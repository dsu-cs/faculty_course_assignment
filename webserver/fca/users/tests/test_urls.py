from django.urls import resolve
from django.urls import reverse

from fca.users.models import User


def test_detail(user: User):
    assert (
        reverse("users:detail", kwargs={"username": user.username})
        == f"/users/{user.username}/"
    )
    assert resolve(f"/users/{user.username}/").view_name == "users:detail"


def test_update():
    assert reverse("users:update") == "/users/~update/"
    assert resolve("/users/~update/").view_name == "users:update"


def test_redirect():
    assert reverse("users:redirect") == "/users/~redirect/"
    assert resolve("/users/~redirect/").view_name == "users:redirect"


def test_magic_login():
    assert reverse("users:magic_login") == "/users/auth/login/"
    assert resolve("/users/auth/login/").view_name == "users:magic_login"


def test_magic_check_email():
    assert reverse("users:magic_check_email") == "/users/auth/check-email/"
    assert resolve("/users/auth/check-email/").view_name == "users:magic_check_email"


def test_onboarding():
    assert reverse("users:onboarding") == "/users/auth/onboarding/"
    assert resolve("/users/auth/onboarding/").view_name == "users:onboarding"
