from django.conf import settings
from django.db import models


class FacultyPreferenceSubmission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="faculty_preference_submissions",
    )
    faculty_identifier = models.CharField(max_length=255, blank=True)
    selected_prefixes = models.JSONField(default=list, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        identifier = self.faculty_identifier or "Anonymous faculty"
        return f"{identifier} preference submission on {self.submitted_at:%Y-%m-%d %H:%M}"


class FacultyCoursePreference(models.Model):
    class PreferenceValue(models.TextChoices):
        UNWILLING = "X", "X"
        ZERO = "0", "0"
        ONE = "1", "1"
        TWO = "2", "2"
        THREE = "3", "3"

    submission = models.ForeignKey(
        FacultyPreferenceSubmission,
        on_delete=models.CASCADE,
        related_name="course_preferences",
    )
    crn = models.CharField(max_length=32)
    prefix = models.CharField(max_length=16)
    course_number = models.CharField(max_length=16)
    sequence = models.CharField(max_length=16, blank=True)
    title = models.CharField(max_length=255)
    credits = models.CharField(max_length=16, blank=True)
    faculty = models.CharField(max_length=255, blank=True)
    meeting_days = models.CharField(max_length=32, blank=True)
    meeting_time = models.CharField(max_length=32, blank=True)
    room = models.CharField(max_length=64, blank=True)
    preference = models.CharField(max_length=1, choices=PreferenceValue.choices)

    class Meta:
        ordering = ["prefix", "course_number", "sequence", "crn"]
        unique_together = [("submission", "crn")]

    def __str__(self) -> str:
        return f"{self.prefix} {self.course_number} {self.sequence} ({self.preference})"
