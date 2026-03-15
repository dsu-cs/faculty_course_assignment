from django.urls import path
from fca.views import DeanDownloadView
from fca.views import FacultyPreferenceView

app_name = "fca"

urlpatterns = [
    path("dean-download/", DeanDownloadView.as_view(), name="dean_download"),
    path("faculty-preference", FacultyPreferenceView.as_view(), name="faculty_preference"),
]