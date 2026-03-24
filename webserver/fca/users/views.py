from __future__ import annotations

import jwt
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from fca.users.magic_links import MagicLinkExpiredError
from fca.users.magic_links import MagicLinkInvalidError
from fca.users.magic_links import build_magic_link_token
from fca.users.magic_links import consume_magic_link_jti
from fca.users.magic_links import is_allowed_email_domain
from fca.users.magic_links import normalize_email
from fca.users.magic_links import parse_magic_link_token
from fca.users.models import User


class MagicLinkEmailForm(forms.Form):
    email = forms.EmailField(max_length=254)

    def clean_email(self):
        email = normalize_email(self.cleaned_data["email"])
        if not is_allowed_email_domain(email):
            raise forms.ValidationError("Only @dsu.edu addresses are allowed.")
        return email


class OnboardingForm(forms.Form):
    name = forms.CharField(max_length=255)


def _build_magic_login_url(request, token: str) -> str:
    return request.build_absolute_uri(
        reverse(settings.MAGIC_LINK_URL_NAME, kwargs={"token": token}),
    )


def _send_magic_link_email(request, email: str):
    token = build_magic_link_token(email)
    login_url = _build_magic_login_url(request, token)
    body_text = (
        "Use this one-time magic link to sign in.\n\n"
        f"{login_url}\n\n"
        f"This link expires in {settings.MAGIC_LINK_TTL_MINUTES} minutes."
    )
    body_html = (
        "<p>Use this one-time magic link to sign in.</p>"
        f'<p><a href="{login_url}">Click Here To Login</a></p>'
        "<p>If the button does not work, copy this URL:</p>"
        f"<p>{login_url}</p>"
    )
    from django.core.mail import EmailMultiAlternatives

    message = EmailMultiAlternatives(
        subject="Your FCA magic sign-in link",
        body=body_text,
        to=[email],
    )
    message.attach_alternative(body_html, "text/html")
    message.send()


def _extract_email_from_expired_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.MAGIC_LINK_JWT_SECRET or settings.SECRET_KEY,
            algorithms=[settings.MAGIC_LINK_JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        return None
    email = normalize_email(payload.get("eml", ""))
    return email if is_allowed_email_domain(email) else None


def magic_login_view(request):
    if request.user.is_authenticated and not request.session.get(
        settings.ONBOARDING_REQUIRED_SESSION_KEY,
    ):
        return redirect("home")

    form = MagicLinkEmailForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        _send_magic_link_email(request, form.cleaned_data["email"])
        messages.success(
            request,
            "If that address is eligible, a login link has been sent.",
        )
        return redirect("users:magic_check_email")
    return render(request, "users/magic_login.html", {"form": form})


def magic_check_email_view(request):
    return render(request, "users/magic_check_email.html")


def magic_verify_view(request, token: str):
    try:
        claims = parse_magic_link_token(token)
    except MagicLinkExpiredError:
        if settings.MAGIC_LINK_RESEND_ON_EXPIRED:
            email = _extract_email_from_expired_token(token)
            if email:
                _send_magic_link_email(request, email)
        messages.info(
            request,
            "Your link expired. A new link has been sent to your email.",
        )
        return redirect("users:magic_check_email")
    except MagicLinkInvalidError:
        return render(request, "users/magic_invalid.html", status=403)

    if not consume_magic_link_jti(claims.jti, claims.email):
        return render(request, "users/magic_invalid.html", status=403)

    user = User.objects.filter(email__iexact=claims.email).first()
    if user:
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.pop(settings.ONBOARDING_REQUIRED_SESSION_KEY, None)
        request.session.pop(settings.MAGIC_LINK_SESSION_EMAIL_KEY, None)
        return redirect("home")

    request.session[settings.MAGIC_LINK_SESSION_EMAIL_KEY] = claims.email
    request.session[settings.ONBOARDING_REQUIRED_SESSION_KEY] = True
    return redirect("users:onboarding")


def onboarding_view(request):
    email = request.session.get(settings.MAGIC_LINK_SESSION_EMAIL_KEY)
    if not email:
        return redirect("users:magic_login")

    form = OnboardingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        base_username = email.split("@", 1)[0]
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username}{suffix}"

        user = User.objects.create_user(
            username=username,
            email=email,
            name=form.cleaned_data["name"],
            password=None,
        )
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.pop(settings.ONBOARDING_REQUIRED_SESSION_KEY, None)
        request.session.pop(settings.MAGIC_LINK_SESSION_EMAIL_KEY, None)
        return redirect("home")
    return render(request, "users/onboarding.html", {"form": form, "email": email})


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()
