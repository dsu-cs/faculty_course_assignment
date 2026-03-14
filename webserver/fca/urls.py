from django.urls import path

from fca.views import DeanDownloadView

app_name = "fca"

urlpatterns = [
    path("dean-download/", DeanDownloadView.as_view(), name="dean_download"),
]