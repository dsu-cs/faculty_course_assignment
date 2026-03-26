from __future__ import annotations

import pytest
from django.urls import reverse

from fca.preferences.models import FacultyCoursePreference
from fca.preferences.models import FacultyPreferenceSubmission


pytestmark = pytest.mark.django_db


@pytest.fixture
def sample_sections(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    sections = [
        {
            "id": "10001",
            "crn": "10001",
            "prefix": "CSC",
            "number": "150",
            "sequence": "D01",
            "title": "Intro to Computer Science",
            "credits": "3",
            "faculty": "Ada Lovelace",
            "days": "MWF",
            "time": "0900-0950",
            "room": "EH 101",
        },
        {
            "id": "10002",
            "crn": "10002",
            "prefix": "CSC",
            "number": "250",
            "sequence": "D01",
            "title": "Data Structures",
            "credits": "3",
            "faculty": "Grace Hopper",
            "days": "TuTh",
            "time": "1100-1215",
            "room": "EH 102",
        },
        {
            "id": "10003",
            "crn": "10003",
            "prefix": "MATH",
            "number": "201",
            "sequence": "D01",
            "title": "Calculus I",
            "credits": "4",
            "faculty": "Katherine Johnson",
            "days": "MWF",
            "time": "1000-1050",
            "room": "SC 201",
        },
    ]
    monkeypatch.setattr("fca.views.load_sections_tab_data", lambda: sections)
    monkeypatch.setattr("fca.views.get_prefixes", lambda loaded_sections: ["CSC", "MATH"])
    return sections


def test_faculty_preference_get_renders_prefixes(client, sample_sections: list[dict[str, str]]):
    response = client.get(reverse("faculty_preference"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "CSC" in content
    assert "MATH" in content
    assert "Intro to Computer Science" in content


def test_faculty_preference_post_saves_submission(client, sample_sections: list[dict[str, str]]):
    response = client.post(
        reverse("faculty_preference"),
        data={
            "prefixes": ["CSC"],
            "pref_10001": "3",
            "pref_10002": "1",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert FacultyPreferenceSubmission.objects.count() == 1

    submission = FacultyPreferenceSubmission.objects.get()
    assert submission.selected_prefixes == ["CSC"]
    assert submission.faculty_identifier == "anonymous"

    saved_preferences = list(
        FacultyCoursePreference.objects.order_by("crn").values_list(
            "crn",
            "prefix",
            "course_number",
            "preference",
        ),
    )
    assert saved_preferences == [
        ("10001", "CSC", "150", "3"),
        ("10002", "CSC", "250", "1"),
    ]
    assert b"Preferences submitted successfully." in response.content
