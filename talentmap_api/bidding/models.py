from django.utils import timezone
from django.db import models

from djchoices import DjangoChoices, ChoiceItem

from talentmap_api.common.common_helpers import safe_navigation


class Bid(models.Model):
    '''
    The bid object represents an individual bid, user, and process status
    '''

    class Status(DjangoChoices):
        draft = ChoiceItem("draft")
        submitted = ChoiceItem("submitted")
        handshake_offered = ChoiceItem("handshake_offered", "handshake_offered")
        handshake_accepted = ChoiceItem("handshake_accepted", "handshake_accepted")
        handshake_declined = ChoiceItem("handshake_declined", "handshake_declined")
        in_panel = ChoiceItem("in_panel", "in_panel")
        approved = ChoiceItem("approved")
        declined = ChoiceItem("declined")
        closed = ChoiceItem("closed")
        handshake_needs_registered = ChoiceItem("handshake_needs_registered", "handshake_needs_registered")

    class Meta:
        managed = False


class BidHandshake(models.Model):
    '''
    The bid handshake object represents a handshake offered to a bidder
    '''

    STATUS_CHOICES = [
        ('O', 'Handshake offered'),
        ('R', 'Handshake revoked'),
        ('A', 'Handshake accepted'),
        ('D', 'Handshake declined'),
    ]

    bidder_perdet = models.CharField(max_length=255, null=False, help_text="The bidder being offered a handshake")
    cp_id = models.CharField(max_length=255, null=False, help_text="The cycle position ID")
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default='O',
    )
    date_created = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now_add=True)
    is_cdo_update = models.BooleanField(default=False)
    last_editing_user = models.ForeignKey('user_profile.UserProfile', related_name='bureau_user', null=False, on_delete=models.DO_NOTHING, help_text="The last offerer user to edit")
    last_editing_bidder = models.ForeignKey('user_profile.UserProfile', related_name='bidder', null=True, on_delete=models.DO_NOTHING, help_text="The last acceptee/cdo to edit")

    class Meta:
        managed = True
        unique_together = ('cp_id', 'bidder_perdet',)