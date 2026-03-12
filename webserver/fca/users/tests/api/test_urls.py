from django.urls import resolve
from django.urls import reverse

from fca.users.models import User


def test_user_detail(user: User):
    assert (
        reverse("api:retrieve_user", kwargs={"username": user.username})
        == f"/api/users/{user.username}/"
    )
    assert resolve(f"/api/users/{user.username}/").view_name == "api:retrieve_user"


def test_user_list():
    assert reverse("api:list_users") == "/api/users/"
    assert resolve("/api/users/").view_name == "api:list_users"


def test_current_user():
    assert reverse("api:retrieve_current_user") == "/api/users/me/"
    assert resolve("/api/users/me/").view_name == "api:retrieve_current_user"


def test_update_user():
    assert reverse("api:update_user", kwargs={"username": "john"}) == "/api/users/john/"
    assert resolve("/api/users/john/").view_name == "api:retrieve_user"
