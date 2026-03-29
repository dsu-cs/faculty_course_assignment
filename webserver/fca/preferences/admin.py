from django.contrib import admin

from fca.preferences.models import FacultyCoursePreference
from fca.preferences.models import FacultyPreferenceSubmission


class FacultyCoursePreferenceInline(admin.TabularInline):
    model = FacultyCoursePreference
    extra = 0
    readonly_fields = (
        "crn",
        "prefix",
        "course_number",
        "sequence",
        "title",
        "credits",
        "faculty",
        "meeting_days",
        "meeting_time",
        "room",
        "preference",
    )
    can_delete = False


@admin.register(FacultyPreferenceSubmission)
class FacultyPreferenceSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "faculty_identifier", "user", "submitted_at")
    search_fields = ("faculty_identifier", "user__username", "user__email")
    readonly_fields = ("submitted_at",)
    inlines = [FacultyCoursePreferenceInline]


@admin.register(FacultyCoursePreference)
class FacultyCoursePreferenceAdmin(admin.ModelAdmin):
    list_display = ("submission", "prefix", "course_number", "sequence", "preference")
    list_filter = ("prefix", "preference")
    search_fields = ("crn", "title", "faculty")
