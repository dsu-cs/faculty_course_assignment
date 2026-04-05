from __future__ import annotations

import csv
from pathlib import Path

import pytest
from django.urls import reverse

from fca.preferences.exporters import build_preferences_csv
from fca.preferences.models import FacultyCoursePreference
from fca.preferences.models import FacultyPreferenceSubmission
from fca.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def sample_sections() -> list[dict[str, str]]:
    return [
        {
            "id": "CSC-105",
            "course_key": "CSC-105",
            "crn": "10001",
            "prefix": "CSC",
            "number": "105",
            "sequence": "D01",
            "title": "Intro to Computing",
            "credits": "3",
            "faculty": "Ada Lovelace",
            "days": "MWF",
            "time": "0900-0950",
            "room": "EH 101",
        },
        {
            "id": "CSC-105",
            "course_key": "CSC-105",
            "crn": "10002",
            "prefix": "CSC",
            "number": "105",
            "sequence": "D02",
            "title": "Intro to Computing",
            "credits": "3",
            "faculty": "Grace Hopper",
            "days": "TuTh",
            "time": "1100-1215",
            "room": "EH 102",
        },
        {
            "id": "MATH-201",
            "course_key": "MATH-201",
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


@pytest.fixture
def faculty_user() -> object:
    return UserFactory.create(email="faculty@dsu.edu", name="Ada Lovelace")


@pytest.fixture
def patch_sections(monkeypatch: pytest.MonkeyPatch, sample_sections: list[dict[str, str]]):
    monkeypatch.setattr("fca.views.load_sections_tab_data", lambda: sample_sections)
    monkeypatch.setattr("fca.preferences.exporters.load_sections_tab_data", lambda _path=None: sample_sections)
    monkeypatch.setattr("fca.views.get_previously_taught_course_keys", lambda faculty_identifier: set())
    return sample_sections


def test_faculty_preference_get_groups_courses(client, faculty_user, patch_sections: list[dict[str, str]]):
    client.force_login(faculty_user)
    response = client.get(reverse("faculty_preference"))

    assert response.status_code == 200
    courses = response.context["courses"]
    assert len(courses) == 2
    assert courses[0]["id"] == "CSC-105"
    assert courses[0]["section_count"] == 2


def test_faculty_preference_get_defaults_previously_taught_courses_to_h(
    client,
    faculty_user,
    monkeypatch: pytest.MonkeyPatch,
    patch_sections: list[dict[str, str]],
):
    client.force_login(faculty_user)
    monkeypatch.setattr("fca.views.get_previously_taught_course_keys", lambda faculty_identifier: {"CSC-105"})

    response = client.get(reverse("faculty_preference"))

    assert response.status_code == 200
    assert response.context["default_preferences"] == {
        "CSC-105": "H",
        "MATH-201": "X",
    }


def test_faculty_preference_post_defaults_unseen_courses_to_x(client, faculty_user, patch_sections: list[dict[str, str]]):
    client.force_login(faculty_user)
    response = client.post(
        reverse("faculty_preference"),
        data={
            "prefixes": ["CSC"],
            "pref_CSC-105": "3",
        },
        follow=True,
    )

    assert response.status_code == 200
    submission = FacultyPreferenceSubmission.objects.get()
    saved_preferences = list(
        FacultyCoursePreference.objects.order_by("prefix", "course_number").values_list(
            "course_key",
            "prefix",
            "course_number",
            "preference",
        ),
    )
    assert submission.selected_prefixes == ["CSC"]
    assert submission.faculty_identifier == "Ada Lovelace"
    assert saved_preferences == [
        ("CSC-105", "CSC", "105", "3"),
        ("MATH-201", "MATH", "201", "X"),
    ]
    assert b"Preferences submitted successfully." in response.content


def test_build_preferences_csv_maps_h_to_solver_friendly_score(
    tmp_path: Path,
    patch_sections: list[dict[str, str]],
):
    submission_a = FacultyPreferenceSubmission.objects.create(faculty_identifier="Dr A")
    FacultyCoursePreference.objects.create(
        submission=submission_a,
        course_key="CSC-105",
        prefix="CSC",
        course_number="105",
        sequence="",
        title="Intro to Computing",
        credits="3",
        faculty="",
        meeting_days="",
        meeting_time="",
        room="2 section(s)",
        preference="H",
    )
    FacultyCoursePreference.objects.create(
        submission=submission_a,
        course_key="MATH-201",
        prefix="MATH",
        course_number="201",
        sequence="",
        title="Calculus I",
        credits="4",
        faculty="",
        meeting_days="",
        meeting_time="",
        room="1 section(s)",
        preference="X",
    )

    submission_b = FacultyPreferenceSubmission.objects.create(faculty_identifier="Dr B")
    FacultyCoursePreference.objects.create(
        submission=submission_b,
        course_key="CSC-105",
        prefix="CSC",
        course_number="105",
        sequence="",
        title="Intro to Computing",
        credits="3",
        faculty="",
        meeting_days="",
        meeting_time="",
        room="2 section(s)",
        preference="X",
    )
    FacultyCoursePreference.objects.create(
        submission=submission_b,
        course_key="MATH-201",
        prefix="MATH",
        course_number="201",
        sequence="",
        title="Calculus I",
        credits="4",
        faculty="",
        meeting_days="",
        meeting_time="",
        room="1 section(s)",
        preference="1",
    )

    csv_path = build_preferences_csv(tmp_path / "preferences.csv")

    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.reader(csv_file))

    assert rows == [
        ["CRN", "Dr A", "Dr B"],
        ["10001", "3", "x"],
        ["10002", "3", "x"],
        ["10003", "x", "1"],
    ]