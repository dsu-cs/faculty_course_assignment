from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import View

from fca.preferences.models import FacultyCoursePreference
from fca.preferences.models import FacultyPreferenceSubmission
from fca.preferences.services import get_prefixes
from fca.preferences.services import load_sections_tab_data


VALID_PREFERENCE_VALUES = {
    choice for choice, _label in FacultyCoursePreference.PreferenceValue.choices
}


class DeanDownloadView(View):
    template_name = "pages/dean_download.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        faculty_csv = request.FILES.get("faculty_csv")
        bim_csv = request.FILES.get("bim_csv")

        if not faculty_csv or not bim_csv:
            return render(
                request,
                self.template_name,
                {"message": "Both CSV files must be added."},
            )

        # this need to be update by IURI later on
        message = (
            f"Received files: {faculty_csv.name} and {bim_csv.name}. "
            "Workbook generation logic will be connected next."
        )
        return render(request, self.template_name, {"message": message})


class FacultyPreferenceView(View):
    template_name = "pages/faculty_preference.html"

    def get_context_data(self, selected_prefixes: list[str] | None = None):
        sections = load_sections_tab_data()
        prefixes = get_prefixes(sections)
        return {
            "prefixes": prefixes,
            "sections": sections,
            "selected_prefixes": selected_prefixes or [],
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request):
        sections = load_sections_tab_data()
        sections_by_crn = {section["crn"]: section for section in sections}
        selected_prefixes = sorted(
            {
                prefix.strip().upper()
                for prefix in request.POST.getlist("prefixes")
                if prefix.strip()
            },
        )

        saved_preferences: list[FacultyCoursePreference] = []
        for key, value in request.POST.items():
            if not key.startswith("pref_"):
                continue
            if value not in VALID_PREFERENCE_VALUES:
                continue

            crn = key.removeprefix("pref_")
            section = sections_by_crn.get(crn)
            if section is None:
                continue

            saved_preferences.append(
                FacultyCoursePreference(
                    crn=section["crn"],
                    prefix=section["prefix"],
                    course_number=section["number"],
                    sequence=section["sequence"],
                    title=section["title"],
                    credits=section["credits"],
                    faculty=section["faculty"],
                    meeting_days=section["days"],
                    meeting_time=section["time"],
                    room=section["room"],
                    preference=value,
                ),
            )

        if not saved_preferences:
            messages.error(request, "Select at least one course preference before submitting.")
            return render(
                request,
                self.template_name,
                self.get_context_data(selected_prefixes=selected_prefixes),
            )

        faculty_identifier = "anonymous"
        if request.user.is_authenticated:
            faculty_identifier = request.user.name or request.user.username

        with transaction.atomic():
            submission = FacultyPreferenceSubmission.objects.create(
                user=request.user if request.user.is_authenticated else None,
                faculty_identifier=faculty_identifier,
                selected_prefixes=selected_prefixes,
            )
            for saved_preference in saved_preferences:
                saved_preference.submission = submission
            FacultyCoursePreference.objects.bulk_create(saved_preferences)

        messages.success(request, "Preferences submitted successfully.")
        return redirect("faculty_preference")
