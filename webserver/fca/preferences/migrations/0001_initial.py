from django.conf import settings
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FacultyPreferenceSubmission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("faculty_identifier", models.CharField(blank=True, max_length=255)),
                ("selected_prefixes", models.JSONField(blank=True, default=list)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="faculty_preference_submissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-submitted_at"],
            },
        ),
        migrations.CreateModel(
            name="FacultyCoursePreference",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("crn", models.CharField(max_length=32)),
                ("prefix", models.CharField(max_length=16)),
                ("course_number", models.CharField(max_length=16)),
                ("sequence", models.CharField(blank=True, max_length=16)),
                ("title", models.CharField(max_length=255)),
                ("credits", models.CharField(blank=True, max_length=16)),
                ("faculty", models.CharField(blank=True, max_length=255)),
                ("meeting_days", models.CharField(blank=True, max_length=32)),
                ("meeting_time", models.CharField(blank=True, max_length=32)),
                ("room", models.CharField(blank=True, max_length=64)),
                (
                    "preference",
                    models.CharField(
                        choices=[("X", "X"), ("0", "0"), ("1", "1"), ("2", "2"), ("3", "3")],
                        max_length=1,
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="course_preferences",
                        to="preferences.facultypreferencesubmission",
                    ),
                ),
            ],
            options={
                "ordering": ["prefix", "course_number", "sequence", "crn"],
                "unique_together": {("submission", "crn")},
            },
        ),
    ]
