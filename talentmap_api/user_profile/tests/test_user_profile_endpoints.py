import json
import pytest

from unittest.mock import Mock, patch

from model_mommy import mommy
from rest_framework import status

from rest_framework_expiring_authtoken.models import ExpiringToken

from talentmap_api.user_profile.models import UserProfile


@pytest.mark.django_db(transaction=True)
def test_user_token_endpoint(authorized_client, authorized_user):
    resp = authorized_client.get('/api/v1/accounts/token/view/')

    assert resp.status_code == status.HTTP_200_OK

