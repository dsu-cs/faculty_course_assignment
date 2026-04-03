from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings


SECTION_CSV_CANDIDATES = (
    Path(settings.BASE_DIR) / "BIM Scraper" / "sections_tab.csv",
    Path(settings.BASE_DIR).parent / "Reference Workbook" / "sections_tab.csv",
)
SECTION_HISTORY_DIR_CANDIDATES = (
    Path(settings.BASE_DIR) / "BIM Scraper" / "previous_semesters",
    Path(settings.BASE_DIR).parent / "BIM Scraper" / "previous_semesters",
)
SECTION_HISTORY_FILENAMES = ("section_data.csv", "sections_tab.csv")
RAW_SECTION_HEADERS = [
    "CRN",
    "Sub",
    "Num",
    "Seq",
    "Crd",
    "Desc",
    "Seats",
    "Waitlist",
    "Days",
    "Time",
    "Room",
    "Faculty",
    "workload_if_full",
    "workload_per_student",
    "special_workload",
]


def build_course_key(prefix: str, number: str) -> str:
    return f"{prefix.strip().upper()}-{number.strip().upper()}"


def get_sections_tab_path() -> Path:
    for candidate in SECTION_CSV_CANDIDATES:
        if candidate.exists():
            return candidate
    searched_paths = ", ".join(str(path) for path in SECTION_CSV_CANDIDATES)
    msg = f"Could not find sections_tab.csv. Looked in: {searched_paths}"
    raise FileNotFoundError(msg)


def load_raw_sections_tab_data(path: Path | None = None) -> list[dict[str, str]]:
    sections_path = path or get_sections_tab_path()

    with sections_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        rows: list[dict[str, str]] = []
        for row in reader:
            normalized_row = {header: (row.get(header) or "").strip() for header in RAW_SECTION_HEADERS}
            if normalized_row["CRN"]:
                rows.append(normalized_row)

    rows.sort(key=lambda row: (row["Sub"], row["Num"], row["Seq"], row["CRN"]))
    return rows


def load_sections_tab_data(path: Path | None = None) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for row in load_raw_sections_tab_data(path):
        prefix = row["Sub"].upper()
        crn = row["CRN"]
        number = row["Num"].upper()
        sequence = row["Seq"]

        if not prefix or not crn or not number:
            continue

        course_key = build_course_key(prefix, number)
        sections.append(
            {
                "id": course_key,
                "course_key": course_key,
                "crn": crn,
                "prefix": prefix,
                "number": number,
                "sequence": sequence,
                "title": row["Desc"],
                "credits": row["Crd"],
                "faculty": row["Faculty"],
                "days": row["Days"],
                "time": row["Time"],
                "room": row["Room"],
            },
        )

    return sections


def group_sections_for_preferences(sections: list[dict[str, str]]) -> list[dict[str, str | int | list[str]]]:
    grouped: dict[tuple[str, str], dict[str, str | int | list[str]]] = {}

    for section in sections:
        key = (section["prefix"], section["number"])
        course = grouped.setdefault(
            key,
            {
                "id": build_course_key(section["prefix"], section["number"]),
                "course_key": build_course_key(section["prefix"], section["number"]),
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


def get_section_history_dir() -> Path:
    for candidate in SECTION_HISTORY_DIR_CANDIDATES:
        if candidate.exists():
            return candidate
    return SECTION_HISTORY_DIR_CANDIDATES[0]


def iter_historical_section_paths() -> list[Path]:
    history_dir = get_section_history_dir()
    if not history_dir.exists():
        return []

    paths: list[Path] = []
    for term_dir in sorted(path for path in history_dir.iterdir() if path.is_dir()):
        for filename in SECTION_HISTORY_FILENAMES:
            candidate = term_dir / filename
            if candidate.exists():
                paths.append(candidate)
                break
    return paths


def _faculty_matches(row_faculty: str, faculty_identifier: str) -> bool:
    normalized_identifier = faculty_identifier.strip().casefold()
    if not normalized_identifier:
        return False

    faculty_names = [name.strip() for name in row_faculty.split("/") if name.strip()]
    return any(name.casefold() == normalized_identifier for name in faculty_names)


def get_previously_taught_course_keys(faculty_identifier: str) -> set[str]:
    if not faculty_identifier.strip():
        return set()

    taught_course_keys: set[str] = set()
    for history_path in iter_historical_section_paths():
        for row in load_raw_sections_tab_data(history_path):
            if _faculty_matches(row.get("Faculty", ""), faculty_identifier):
                taught_course_keys.add(build_course_key(row.get("Sub", ""), row.get("Num", "")))

    return taught_course_keys