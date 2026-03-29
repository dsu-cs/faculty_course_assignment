from django.contrib import messages
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import View

from fca.preferences.exporters import build_dean_download_artifacts
from fca.preferences.exporters import get_available_bim_terms
from fca.preferences.exporters import get_default_bim_term
from fca.preferences.models import FacultyCoursePreference
from fca.preferences.models import FacultyPreferenceSubmission
from fca.preferences.services import group_sections_for_preferences
from fca.preferences.services import get_prefixes
from fca.preferences.services import load_sections_tab_data


VALID_PREFERENCE_VALUES = {
    choice for choice, _label in FacultyCoursePreference.PreferenceValue.choices
}


def _normalize_preference_value(value: str) -> str:
    normalized = value.strip().upper()
    return normalized if normalized in VALID_PREFERENCE_VALUES else ""


class DeanDownloadView(View):
    template_name = "pages/dean_download.html"

    def _get_context_data(
        self,
        *,
        selected_term: str | None = None,
        message: str | None = None,
    ) -> dict[str, object]:
        available_terms: list[str] = []
        term_load_error = None

        try:
            available_terms = get_available_bim_terms()
        except Exception as exc:
            term_load_error = f"Unable to load BIM terms right now: {exc}"

        resolved_selected_term = selected_term
        if available_terms and selected_term not in available_terms:
            resolved_selected_term = get_default_bim_term(available_terms)

        return {
            "available_terms": available_terms,
            "selected_term": resolved_selected_term,
            "message": message,
            "term_load_error": term_load_error,
        }

    def get(self, request):
        return render(request, self.template_name, self._get_context_data())

    def post(self, request):
        selected_term = request.POST.get("bim_term", "").strip() or None
        try:
            artifacts = build_dean_download_artifacts(term=selected_term)
        except (FileNotFoundError, ImportError, RuntimeError, ValueError) as exc:
            return render(
                request,
                self.template_name,
                self._get_context_data(selected_term=selected_term, message=str(exc)),
            )

        return FileResponse(
            artifacts.workbook_path.open("rb"),
            as_attachment=True,
            filename=artifacts.workbook_path.name,
        )


class FacultyPreferenceView(View):
    template_name = "pages/faculty_preference.html"

    def get_context_data(self, selected_prefixes: list[str] | None = None):
        sections = load_sections_tab_data()
        courses = group_sections_for_preferences(sections)
        prefixes = get_prefixes(sections)
        return {
            "prefixes": prefixes,
            "courses": courses,
            "selected_prefixes": selected_prefixes or [],
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request):
        sections = load_sections_tab_data()
        courses = group_sections_for_preferences(sections)
        if not courses:
            messages.error(request, "No course data was found in sections_tab.csv.")
            return render(request, self.template_name, self.get_context_data())

        selected_prefixes = sorted(
            {
                prefix.strip().upper()
                for prefix in request.POST.getlist("prefixes")
                if prefix.strip()
            },
        )

        submitted_preferences: dict[str, str] = {}
        for key, value in request.POST.items():
            if not key.startswith("pref_"):
                continue
            normalized_value = _normalize_preference_value(value)
            if not normalized_value:
                continue
            submitted_preferences[key.removeprefix("pref_")] = normalized_value

        saved_preferences: list[FacultyCoursePreference] = []
        for course in courses:
            course_id = str(course["id"])
            preference = submitted_preferences.get(course_id, "X")
            saved_preferences.append(
                FacultyCoursePreference(
                    crn=course_id,
                    prefix=str(course["prefix"]),
                    course_number=str(course["number"]),
                    sequence="",
                    title=str(course["title"]),
                    credits=str(course["credits"]),
                    faculty="",
                    meeting_days="",
                    meeting_time="",
                    room=f"{course['section_count']} section(s)",
                    preference=preference,
                ),
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


