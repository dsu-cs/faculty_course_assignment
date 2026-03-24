from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from http import HTTPStatus

import jwt
import pytest
from django.conf import settings
from django.core import mail
from django.urls import reverse

from fca.users.magic_links import build_magic_link_token
from fca.users.models import User
from fca.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_magic_login_rejects_non_dsu_email(client):
    response = client.post(
        reverse("users:magic_login"),
        data={"email": "someone@example.com"},
    )

    assert response.status_code == HTTPStatus.OK
    assert "Only @dsu.edu addresses are allowed." in response.content.decode()
    assert len(mail.outbox) == 0


def test_magic_login_send_link_happy_path(client):
    response = client.post(
        reverse("users:magic_login"),
        data={"email": "professor@dsu.edu"},
    )

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("users:magic_check_email")
    assert len(mail.outbox) == 1


def test_magic_verify_invalid_token(client):
    response = client.get(reverse("users:magic_verify", kwargs={"token": "broken.token"}))

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_magic_verify_expired_token_auto_resends(client):
    payload = {
        "eml": "staff@dsu.edu",
        "iat": int((datetime.now(tz=UTC) - timedelta(hours=1)).timestamp()),
        "exp": int((datetime.now(tz=UTC) - timedelta(minutes=1)).timestamp()),
        "jti": "expired-token-id",
    }
    token = jwt.encode(
        payload,
        settings.MAGIC_LINK_JWT_SECRET or settings.SECRET_KEY,
        algorithm=settings.MAGIC_LINK_JWT_ALGORITHM,
    )

    response = client.get(reverse("users:magic_verify", kwargs={"token": token}))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("users:magic_check_email")
    assert len(mail.outbox) == 1


def test_magic_verify_new_user_onboarding_flow(client):
    token = build_magic_link_token("newfaculty@dsu.edu")
    verify_response = client.get(reverse("users:magic_verify", kwargs={"token": token}))

    assert verify_response.status_code == HTTPStatus.FOUND
    assert verify_response.url == reverse("users:onboarding")

    redirect_response = client.get(reverse("home"))
    assert redirect_response.status_code == HTTPStatus.FOUND
    assert redirect_response.url == reverse("users:onboarding")

    onboarding_response = client.post(
        reverse("users:onboarding"),
        data={"name": "New Faculty"},
    )
    assert onboarding_response.status_code == HTTPStatus.FOUND
    assert onboarding_response.url == reverse("home")

    user = User.objects.get(email="newfaculty@dsu.edu")
    assert user.name == "New Faculty"


def test_magic_verify_replayed_token_denied(client):
    user = UserFactory.create(email="repeat@dsu.edu")
    token = build_magic_link_token(user.email)

    first_response = client.get(reverse("users:magic_verify", kwargs={"token": token}))
    assert first_response.status_code == HTTPStatus.FOUND
    assert first_response.url == reverse("home")

    second_response = client.get(reverse("users:magic_verify", kwargs={"token": token}))
    assert second_response.status_code == HTTPStatus.FORBIDDEN
