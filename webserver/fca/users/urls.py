from django.urls import path

from .views import magic_check_email_view
from .views import magic_login_view
from .views import magic_verify_view
from .views import onboarding_view
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view

app_name = "users"
urlpatterns = [
    path("auth/login/", view=magic_login_view, name="magic_login"),
    path("auth/check-email/", view=magic_check_email_view, name="magic_check_email"),
    path("auth/magic/<str:token>/", view=magic_verify_view, name="magic_verify"),
    path("auth/onboarding/", view=onboarding_view, name="onboarding"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
