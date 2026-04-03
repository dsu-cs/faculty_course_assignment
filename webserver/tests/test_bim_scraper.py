from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "BIM Scraper" / "bim_scraper.py"
SPEC = importlib.util.spec_from_file_location("bim_scraper", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
BIM_SCRAPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BIM_SCRAPER)


def test_standard_undergraduate_workload_fields():
    row = {
        "Num": "314",
        "Crd": "3",
        "Desc": "Assembly Language",
        "Seats": "7/25",
        "Days": "MWF",
        "Faculty": "Jane Doe",
    }

    result = BIM_SCRAPER._build_workload_fields(row)

    assert result == {
        "workload_if_full": "3",
        "workload_per_student": "0.12",
        "special_workload": "",
    }


def test_graduate_course_uses_equated_multiplier():
    row = {
        "Num": "721",
        "Crd": "3",
        "Desc": "Digital Forensics",
        "Seats": "9/25",
        "Days": "Internet",
        "Faculty": "Jane Doe",
    }

    result = BIM_SCRAPER._build_workload_fields(row)

    assert result == {
        "workload_if_full": "4",
        "workload_per_student": "0.16",
        "special_workload": "",
    }


def test_undergraduate_research_is_capped_at_five_workload_units():
    row = {
        "Num": "498",
        "Crd": "3",
        "Desc": "Research",
        "Seats": "16/25",
        "Days": "Internet",
        "Faculty": "Jane Doe",
    }

    result = BIM_SCRAPER._build_workload_fields(row)

    assert result == {
        "workload_if_full": "5",
        "workload_per_student": "0.2",
        "special_workload": "",
    }


def test_variable_credit_internship_is_capped_at_five_workload_units():
    row = {
        "Num": "494",
        "Crd": "1 TO 12",
        "Desc": "Internship",
        "Seats": "4/5",
        "Days": "Internet",
        "Faculty": "Jane Doe",
    }

    result = BIM_SCRAPER._build_workload_fields(row)

    assert result == {
        "workload_if_full": "5",
        "workload_per_student": "1",
        "special_workload": "",
    }


def test_dissertation_caps_full_workload_at_six_students():
    row = {
        "Num": "898D",
        "Crd": "1 TO 12",
        "Desc": "Dissertation",
        "Seats": "4/10",
        "Days": "Internet",
        "Faculty": "Jane Doe",
    }

    result = BIM_SCRAPER._build_workload_fields(row)

    assert result == {
        "workload_if_full": "3",
        "workload_per_student": "0.3",
        "special_workload": "",
    }


def test_student_teaching_is_capped_at_five_workload_units():
    row = {
        "Num": "489",
        "Crd": "0 TO 18",
        "Desc": "Student Teaching",
        "Seats": "10/10",
        "Days": "MWF",
        "Faculty": "Jane Doe",
    }

    result = BIM_SCRAPER._build_workload_fields(row)

    assert result == {
        "workload_if_full": "5",
        "workload_per_student": "0.5",
        "special_workload": "",
    }


def test_team_taught_sections_split_workload_evenly():
    row = {
        "Num": "314",
        "Crd": "3",
        "Desc": "Assembly Language",
        "Seats": "7/25",
        "Days": "MWF",
        "Faculty": "Jane Doe/John Doe",
    }

    result = BIM_SCRAPER._build_workload_fields(row)

    assert result == {
        "workload_if_full": "1.5",
        "workload_per_student": "0.06",
        "special_workload": "",
    }


def test_independent_study_does_not_count_toward_workload():
    row = {
        "Num": "491",
        "Crd": "3",
        "Desc": "Independent Study",
        "Seats": "1/1",
        "Days": "Internet",
        "Faculty": "Jane Doe",
    }

    result = BIM_SCRAPER._build_workload_fields(row)

    assert result == {
        "workload_if_full": "0",
        "workload_per_student": "0",
        "special_workload": "",
    }


class _FakeOption:
    def __init__(self, text: str):
        self._text = text

    def inner_text(self) -> str:
        return self._text


def test_extract_term_options_filters_to_valid_bim_terms():
    options = [
        _FakeOption("Select..."),
        _FakeOption("2026 Spring"),
        _FakeOption("2026 Fall"),
        _FakeOption("Archive"),
        _FakeOption("2026 Winter"),
    ]

    result = BIM_SCRAPER._extract_term_options(options)

    assert result == ["2026 Spring", "2026 Fall"]