import coreapi
import maya
import logging

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import QueryDict
from django.db.models.functions import Concat
from django.db.models import TextField
from django.conf import settings

from rest_framework.viewsets import GenericViewSet
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins
from rest_framework.schemas import AutoSchema

from rest_framework_bulk import (
    ListBulkCreateUpdateDestroyAPIView,
)

from rest_condition import Or

from talentmap_api.common.common_helpers import in_group_or_403, get_prefetched_filtered_queryset
from talentmap_api.common.permissions import isDjangoGroupMember
from talentmap_api.common.mixins import FieldLimitableSerializerMixin
from talentmap_api.available_positions.models import AvailablePositionFavorite, AvailablePositionDesignation, AvailablePositionRanking, AvailablePositionRankingLock
from talentmap_api.available_positions.serializers.serializers import AvailablePositionDesignationSerializer, AvailablePositionRankingSerializer, AvailablePositionRankingLockSerializer
from talentmap_api.available_positions.filters import AvailablePositionRankingFilter, AvailablePositionRankingLockFilter
from talentmap_api.user_profile.models import UserProfile
from talentmap_api.projected_vacancies.models import ProjectedVacancyFavorite

import talentmap_api.fsbid.services.available_positions as services
import talentmap_api.fsbid.services.projected_vacancies as pvservices
import talentmap_api.fsbid.services.common as comservices
import talentmap_api.fsbid.services.employee as empservices

logger = logging.getLogger(__name__)

FAVORITES_LIMIT = settings.FAVORITES_LIMIT


class AvailablePositionsFilter():
    declared_filters = [
        "exclude_available",
        "exclude_projected",
    ]

    use_api = True

    class Meta:
        fields = "__all__"


class AvailablePositionFavoriteListView(APIView):

    permission_classes = (IsAuthenticated,)

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field("page", location='query', type='integer', description='A page number within the paginated result set.'),
            coreapi.Field("limit", location='query', type='integer', description='Number of results to return per page.'),
        ]
    )

    def get(self, request, *args, **kwargs):
        """
        get:
        Return a list of all of the user's favorite available positions.
        """
        user = UserProfile.objects.get(user=self.request.user)
        aps = AvailablePositionFavorite.objects.filter(user=user, archived=False).values_list("cp_id", flat=True)
        limit = request.query_params.get('limit', 15)
        page = request.query_params.get('page', 1)
        ordering = request.query_params.get('ordering', None)
        if len(aps) > 0:
            comservices.archive_favorites(aps, request)
            pos_nums = ','.join(aps)
            return Response(services.get_available_positions(QueryDict(f"id={pos_nums}&limit={limit}&page={page}&ordering={ordering}"),
                                                             request.META['HTTP_JWT'],
                                                             f"{request.scheme}://{request.get_host()}"))
        else:
            return Response({"count": 0, "next": None, "previous": None, "results": []})


class AvailablePositionFavoriteIdsListView(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """
        get:
        Return a list of the ids of the user's favorite available positions.
        """
        user = UserProfile.objects.get(user=self.request.user)
        aps = AvailablePositionFavorite.objects.filter(user=user, archived=False).values_list("cp_id", flat=True)
        return Response(aps)


class AvailablePositionRankingView(FieldLimitableSerializerMixin,
                                   GenericViewSet,
                                   ListBulkCreateUpdateDestroyAPIView,
                                   mixins.ListModelMixin,
                                   mixins.RetrieveModelMixin):

    permission_classes = [Or(isDjangoGroupMember('ao_user'), isDjangoGroupMember('bureau_user')), ]
    serializer_class = AvailablePositionRankingSerializer
    filter_class = AvailablePositionRankingFilter

    # For all requests, if the position is locked, then the user must have the appropriate bureau permission for the cp_id

    def perform_create(self, serializer):
        if AvailablePositionRankingLock.objects.filter(cp_id=self.request.data.get('cp_id')).exists() and not empservices.has_bureau_permissions(self.request.data.get('cp_id'), self.request):
            raise PermissionDenied()
        serializer.save(user=self.request.user.profile)

    def get_queryset(self):
        cp = self.request.GET.get('cp_id')
        if AvailablePositionRankingLock.objects.filter(cp_id=cp).exists() and not empservices.has_bureau_permissions(cp, self.request):
            raise PermissionDenied()
        return get_prefetched_filtered_queryset(AvailablePositionRanking, self.serializer_class, user=self.request.user.profile).order_by('rank')

    def perform_delete(self, request, pk, format=None):
        '''
        Removes the available position rankings by cp_id for the user
        '''
        user = UserProfile.objects.get(user=self.request.user)
        if AvailablePositionRankingLock.objects.filter(cp_id=pk).exists() and not empservices.has_bureau_permissions(pk, request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        get_prefetched_filtered_queryset(AvailablePositionRanking, self.serializer_class, user=self.request.user.profile, cp_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvailablePositionRankingLockView(FieldLimitableSerializerMixin,
                                       GenericViewSet,
                                       mixins.ListModelMixin,
                                       mixins.RetrieveModelMixin):

    permission_classes = (isDjangoGroupMember('bureau_user'),)
    serializer_class = AvailablePositionRankingLockSerializer
    filter_class = AvailablePositionRankingLockFilter


    def put(self, request, pk, format=None):
        # must have bureau permission for the bureau code associated with the position
        if not empservices.has_bureau_permissions(pk, request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # get the bureau code and org code associated with the position
        pos = services.get_available_position(pk, request.META['HTTP_JWT'])
        try:
            bureau = pos.get('position').get('bureau_code')
            org = pos.get('position').get('organization_code')
        # return a 404 if we can't determine the bureau/org code
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if pos is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # if the position is already locked, still update the bureau/org codes
        if AvailablePositionRankingLock.objects.filter(cp_id=pk).exists():
            AvailablePositionRankingLock.objects.filter(cp_id=pk).update(bureau_code=bureau, org_code=org)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # save the cp_id, bureau code and org code
        position, _ = AvailablePositionRankingLock.objects.get_or_create(cp_id=pk, bureau_code=bureau, org_code=org)
        position.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, pk, format=None):
        '''
        Indicates if the available position is a favorite

        Returns 204 if the available position is a favorite, otherwise, 404
        '''
        # must have bureau permission for the bureau code associated with the position
        if not empservices.has_bureau_permissions(pk, request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        if AvailablePositionRankingLock.objects.filter(cp_id=pk).exists():
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk, format=None):
        '''
        Removes the available position ranking by cp_id
        '''
        # must have bureau permission for the bureau code associated with the position
        if not empservices.has_bureau_permissions(pk, request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        get_prefetched_filtered_queryset(AvailablePositionRankingLock, self.serializer_class, cp_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoritesCSVView(APIView):

    permission_classes = (IsAuthenticated,)
    filter_class = AvailablePositionsFilter

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field("exclude_available", type='boolean', location='query', description='Whether to exclude available positions'),
            coreapi.Field("exclude_projected", type='boolean', location='query', description='Whether to exclude projected vacancies'),
        ]
    )

    def get(self, request, *args, **kwargs):
        """
        Return a list of all of the user's favorite positions.
        """
        user = UserProfile.objects.get(user=self.request.user)
        data = []

        aps = AvailablePositionFavorite.objects.filter(user=user, archived=False).values_list("cp_id", flat=True)
        if len(aps) > 0 and request.query_params.get('exclude_available') != 'true':
            pos_nums = ','.join(aps)
            apdata = services.get_available_positions(QueryDict(f"id={pos_nums}&limit={len(aps)}&page=1"), request.META['HTTP_JWT'])
            data = data + apdata.get('results')

        pvs = ProjectedVacancyFavorite.objects.filter(user=user, archived=False).values_list("fv_seq_num", flat=True)
        if len(pvs) > 0 and request.query_params.get('exclude_projected') != 'true':
            pos_nums = ','.join(pvs)
            pvdata = pvservices.get_projected_vacancies(QueryDict(f"id={pos_nums}&limit={len(pvs)}&page=1"), request.META['HTTP_JWT'])
            data = data + pvdata.get('results')

        return comservices.get_ap_and_pv_csv(data, "favorites", True)


class AvailablePositionFavoriteActionView(APIView):
    '''
    Controls the favorite status of a available position

    Responses adapted from Github gist 'stars' https://developer.github.com/v3/gists/#star-a-gist
    '''

    permission_classes = (IsAuthenticated,)

    def get(self, request, pk, format=None):
        '''
        Indicates if the available position is a favorite

        Returns 204 if the available position is a favorite, otherwise, 404
        '''
        user = UserProfile.objects.get(user=self.request.user)
        if AvailablePositionFavorite.objects.filter(user=user, cp_id=pk, archived=False).exists():
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk, format=None):
        '''
        Marks the available position as a favorite
        '''
        user = UserProfile.objects.get(user=self.request.user)
        aps = AvailablePositionFavorite.objects.filter(user=user, archived=False).values_list("cp_id", flat=True)
        comservices.archive_favorites(aps, request)
        aps_after_archive = AvailablePositionFavorite.objects.filter(user=user, archived=False).values_list("cp_id", flat=True)
        if len(aps_after_archive) >= FAVORITES_LIMIT:
            return Response({"limit": FAVORITES_LIMIT}, status=status.HTTP_507_INSUFFICIENT_STORAGE)
        else:
            AvailablePositionFavorite.objects.get_or_create(user=user, cp_id=pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, pk, format=None):
        '''
        Removes the available position from favorites
        '''
        user = UserProfile.objects.get(user=self.request.user)
        AvailablePositionFavorite.objects.filter(user=user, cp_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvailablePositionDesignationView(mixins.UpdateModelMixin,
                                       FieldLimitableSerializerMixin,
                                       GenericViewSet):
    '''
    partial_update:
    Updates an available position designation
    '''
    serializer_class = AvailablePositionDesignationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        queryset = AvailablePositionDesignation.objects.all()
        queryset = self.serializer_class.prefetch_model(AvailablePositionDesignation, queryset)
        return queryset

    def get_object(self):
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk', None)
        obj, _ = queryset.get_or_create(cp_id=pk)
        self.check_object_permissions(self.request, obj)
        return obj


class AvailablePositionHighlightListView(APIView):
    """
    list:
    Return a list of all currently highlighted available positions
    """

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):
        """
        get:
        Return a list of all of the higlighted available positions.
        """
        cp_ids = AvailablePositionDesignation.objects.filter(is_highlighted=True).values_list("cp_id", flat=True)
        if len(cp_ids) > 0:
            pos_nums = ','.join(cp_ids)
            return Response(services.get_available_positions(QueryDict(f"id={pos_nums}"), request.META['HTTP_JWT']))
        else:
            return Response({"count": 0, "next": None, "previous": None, "results": []})


class AvailablePositionHighlightActionView(APIView):
    '''
    Controls the highlighted status of an available position
    '''

    permission_classes = (IsAuthenticated,)

    def get(self, request, pk, format=None):
        '''
        Indicates if the position is highlighted

        Returns 204 if the position is highlighted, otherwise, 404
        '''
        position = get_object_or_404(AvailablePositionDesignation, cp_id=pk)
        if position.is_highlighted is True:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk, format=None):
        '''
        Marks the position as highlighted by the position's bureau
        '''
        position, _ = AvailablePositionDesignation.objects.get_or_create(cp_id=pk)
        in_group_or_403(self.request.user, "superuser")
        position.is_highlighted = True
        position.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, pk, format=None):
        '''
        Removes the position from highlighted positions
        '''
        position, _ = AvailablePositionDesignation.objects.get_or_create(cp_id=pk)
        in_group_or_403(self.request.user, "superuser")
        position.is_highlighted = False
        position.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
