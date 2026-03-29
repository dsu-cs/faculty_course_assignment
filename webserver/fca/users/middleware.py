from __future__ import annotations

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.urls import Resolver404
from django.urls import resolve
from django.urls import reverse


class AuthenticationFlowMiddleware:
    """
    Controls auth flow redirects:
    - anonymous users are sent to magic link login page
    - users flagged for onboarding are constrained to onboarding routes
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "GET":
            path = request.path
            try:
                match = resolve(path)
            except (Resolver404, Http404):
                return self.get_response(request)
            exempt_paths = (
                settings.STATIC_URL,
                settings.MEDIA_URL,
                "/admin/",
                "/accounts/logout/",
                "/api/",
            )
            exempt_names = {
                "users:magic_login",
                "users:magic_verify",
                "users:magic_check_email",
                "users:onboarding",
            }

            if any(path.startswith(prefix) for prefix in exempt_paths):
                return self.get_response(request)

            if request.session.get(settings.ONBOARDING_REQUIRED_SESSION_KEY):
                if match.view_name not in exempt_names:
                    return redirect("users:onboarding")
            elif not request.user.is_authenticated and match.view_name not in exempt_names:
                return redirect(f"{reverse(settings.LOGIN_URL)}?next={request.path}")

        return self.get_response(request)
