from http import HTTPStatus

import pytest
from django.urls import reverse


def test_api_docs_accessible_by_admin(admin_client):
    url = reverse("api:openapi-view")
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_api_docs_not_accessible_by_anonymous_users(client):
    url = reverse("api:openapi-view")
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == "/admin/login/?next=/api/docs"


def test_api_schema_generated_successfully(admin_client):
    url = reverse("api:openapi-json")
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.OK
