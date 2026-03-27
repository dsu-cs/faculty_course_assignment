from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings


SECTION_CSV_CANDIDATES = (
    Path(settings.BASE_DIR) / "BIM Scraper" / "sections_tab.csv",
    Path(settings.BASE_DIR).parent / "Reference Workbook" / "sections_tab.csv",
)


def get_sections_tab_path() -> Path:
    for candidate in SECTION_CSV_CANDIDATES:
        if candidate.exists():
            return candidate
    searched_paths = ", ".join(str(path) for path in SECTION_CSV_CANDIDATES)
    msg = f"Could not find sections_tab.csv. Looked in: {searched_paths}"
    raise FileNotFoundError(msg)


def load_sections_tab_data() -> list[dict[str, str]]:
    sections_path = get_sections_tab_path()

    with sections_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        sections: list[dict[str, str]] = []
        for row in reader:
            prefix = (row.get("Sub") or "").strip().upper()
            crn = (row.get("CRN") or "").strip()
            number = (row.get("Num") or "").strip()
            sequence = (row.get("Seq") or "").strip()

            if not prefix or not crn or not number:
                continue

            sections.append(
                {
                    "id": crn,
                    "crn": crn,
                    "prefix": prefix,
                    "number": number,
                    "sequence": sequence,
                    "title": (row.get("Desc") or "").strip(),
                    "credits": (row.get("Crd") or "").strip(),
                    "faculty": (row.get("Faculty") or "").strip(),
                    "days": (row.get("Days") or "").strip(),
                    "time": (row.get("Time") or "").strip(),
                    "room": (row.get("Room") or "").strip(),
                },
            )

    sections.sort(
        key=lambda section: (
            section["prefix"],
            section["number"],
            section["sequence"],
            section["crn"],
        ),
    )
    return sections


def build_course_group_id(prefix: str, number: str) -> str:
    return f"{prefix}-{number}"


def group_sections_for_preferences(sections: list[dict[str, str]]) -> list[dict[str, str | int | list[str]]]:
    grouped: dict[tuple[str, str], dict[str, str | int | list[str]]] = {}

    for section in sections:
        key = (section["prefix"], section["number"])
        course = grouped.setdefault(
            key,
            {
                "id": build_course_group_id(section["prefix"], section["number"]),
                "prefix": section["prefix"],
                "number": section["number"],
                "title": section["title"],
                "credits": section["credits"],
                "section_count": 0,
                "section_crns": [],
            },
        )

        course["section_count"] = int(course["section_count"]) + 1
        section_crns = course["section_crns"]
        if isinstance(section_crns, list):
            section_crns.append(section["crn"])

        if not course["title"] and section["title"]:
            course["title"] = section["title"]
        if not course["credits"] and section["credits"]:
            course["credits"] = section["credits"]

    courses = list(grouped.values())
    courses.sort(key=lambda course: (str(course["prefix"]), str(course["number"])))
    return courses


def get_prefixes(sections: list[dict[str, str]]) -> list[str]:
    return sorted({section["prefix"] for section in sections})
