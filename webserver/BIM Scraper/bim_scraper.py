import csv
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SEASON_ORDER = {"Spring": 1, "Summer": 2, "Fall": 3}
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "sections_tab.csv"

WORKLOAD_DECIMAL_PLACES = Decimal("0.01")
GRADUATE_WORKLOAD_MULTIPLIER = Decimal("4") / Decimal("3")
SMALL_SECTION_MULTIPLIER = Decimal("0.10")
PRIVATE_INSTRUCTION_MULTIPLIER = Decimal("0.33")  # Reserved for future workload policy support
DISSERTATION_PER_STUDENT = Decimal("0.5")
STUDENT_TEACHING_PER_STUDENT = Decimal("0.67")
MAX_DISSERTATION_CHAIR_STUDENTS = 6
MAX_SECTION_WORKLOAD = Decimal("5")

TERM_SELECTORS = ("select#selTerm", "select[name='selTerm']", "select")

UNDERGRADUATE_RESEARCH_COURSE = 498
DOCTORAL_DISSERTATION_CODE = "898D"
INDEPENDENT_STUDY_SUFFIX = 91


def _split_term(term: str) -> tuple[int, str]:
    """Split a term like '2026 Fall' into (2026, 'Fall')."""
    year_text, season = term.split(maxsplit=1)
    season = season.strip().title()
    return int(year_text), season


def _format_decimal(value: Decimal) -> str:
    """Format a Decimal to two places, then normalize trailing zeros cleanly."""
    normalized = value.quantize(
        WORKLOAD_DECIMAL_PLACES,
        rounding=ROUND_HALF_UP,
    ).normalize()
    return format(normalized, "f")


def _extract_term_options(options) -> list[str]:
    """Extract valid academic terms from the BIM term dropdown options."""
    terms: list[str] = []
    for option in options:
        text = option.inner_text().strip()
        if (
            text
            and text != "Select..."
            and len(text.split()) == 2
            and text.split()[1] in SEASON_ORDER
        ):
            terms.append(text)
    return terms


def _find_term_select(page):
    """Find the BIM term dropdown using a list of possible selectors."""
    for selector in TERM_SELECTORS:
        select = page.query_selector(selector)
        if select is not None:
            return select, selector
    raise RuntimeError("Could not find term dropdown on page.")


def _wait_for_term_results(page) -> None:
    """Wait until BIM finishes loading data for the selected term."""
    page.wait_for_function(
        """
        () => {
            const update = document.getElementById("txtUpdate");
            const rows = document.querySelectorAll("tr.trSearch");
            return update && update.textContent.trim() !== "Select a Term" && rows.length > 0;
        }
        """,
        timeout=60000,
    )
    page.wait_for_timeout(1000)


def _parse_credit_hours(credit_text: str) -> Decimal:
    """Parse credit text and return the largest numeric value found."""
    parts: list[Decimal] = []
    for token in str(credit_text).replace("-", " ").split():
        try:
            parts.append(Decimal(token))
        except InvalidOperation:
            continue

    if not parts:
        return Decimal("0")
    return max(parts)


def _parse_seat_counts(seat_text: str) -> tuple[int, int]:
    """Parse a seat string like '12/25' into (current_seats, max_seats)."""
    current_seats = 0
    max_seats = 0
    current_text, _, max_text = str(seat_text).partition("/")

    try:
        current_seats = int(current_text.strip()) if current_text.strip() else 0
    except ValueError:
        current_seats = 0

    try:
        max_seats = int(max_text.strip()) if max_text.strip() else 0
    except ValueError:
        max_seats = 0

    return current_seats, max_seats


def _parse_course_level(number_text: str) -> int | None:
    """Extract the first 3-digit course level from a course number string."""
    match = re.search(r"(\d{3})", str(number_text))
    if match is None:
        return None
    return int(match.group(1))


def _faculty_count(faculty_text: str) -> int:
    """Count faculty names separated by '/' and return at least 1."""
    names = [name.strip() for name in str(faculty_text).split("/") if name.strip()]
    return max(1, len(names))


def _is_independent_study(course_level: int | None) -> bool:
    """Return True if the course level indicates independent study."""
    return course_level is not None and course_level % 100 == INDEPENDENT_STUDY_SUFFIX


def _is_undergraduate_research(course_level: int | None) -> bool:
    """Return True if the course is the undergraduate research course."""
    return course_level == UNDERGRADUATE_RESEARCH_COURSE


def _is_doctoral_dissertation(number_text: str) -> bool:
    """Return True if the course number matches the doctoral dissertation code."""
    return str(number_text).strip().upper() == DOCTORAL_DISSERTATION_CODE


def _is_student_teaching(description: str) -> bool:
    """Return True if the course description indicates student teaching."""
    return "student teaching" in str(description).strip().lower()


def _standard_workload(credit_hours: Decimal, course_level: int | None) -> Decimal:
    """Return standard workload based on credit hours and graduate multiplier rules."""
    if course_level is not None and course_level >= 700:
        return credit_hours * GRADUATE_WORKLOAD_MULTIPLIER
    return credit_hours


def _per_student_workload(
    credit_hours: Decimal,
    course_level: int | None,
    number_text: str,
    description: str,
) -> Decimal:
    """Return workload added per student based on course type rules."""
    if _is_independent_study(course_level):
        return Decimal("0")
    if _is_doctoral_dissertation(number_text):
        return DISSERTATION_PER_STUDENT
    if _is_student_teaching(description):
        return STUDENT_TEACHING_PER_STUDENT
    if _is_undergraduate_research(course_level):
        return SMALL_SECTION_MULTIPLIER * credit_hours
    if course_level is not None and course_level >= 700:
        return SMALL_SECTION_MULTIPLIER * credit_hours * GRADUATE_WORKLOAD_MULTIPLIER
    return SMALL_SECTION_MULTIPLIER * credit_hours


def _workload_if_full(
    credit_hours: Decimal,
    course_level: int | None,
    number_text: str,
    description: str,
    max_seats: int,
) -> Decimal:
    """Return the total workload for a section if it reaches full enrollment."""
    if _is_independent_study(course_level):
        return Decimal("0")
    if _is_doctoral_dissertation(number_text):
        return DISSERTATION_PER_STUDENT * min(max_seats, MAX_DISSERTATION_CHAIR_STUDENTS)
    if _is_student_teaching(description):
        return STUDENT_TEACHING_PER_STUDENT * max_seats
    if _is_undergraduate_research(course_level):
        return SMALL_SECTION_MULTIPLIER * credit_hours * max_seats
    return _standard_workload(credit_hours, course_level)


def _cap_workload_values(
    workload_if_full: Decimal,
    workload_per_student: Decimal,
    max_seats: int,
) -> tuple[Decimal, Decimal]:
    """Cap workload fields so section workload does not exceed policy limits."""
    capped_if_full = min(workload_if_full, MAX_SECTION_WORKLOAD)

    if max_seats <= 0:
        return capped_if_full, min(workload_per_student, capped_if_full)

    capped_per_student = min(workload_per_student, capped_if_full / Decimal(max_seats))
    return capped_if_full, capped_per_student


def _build_workload_fields(row: dict[str, str]) -> dict[str, str]:
    """Build workload fields for one BIM row using current policy rules."""
    credit_hours = _parse_credit_hours(row.get("Crd", ""))
    current_seats, max_seats = _parse_seat_counts(row.get("Seats", ""))

    if max_seats <= 0:
        max_seats = current_seats

    course_level = _parse_course_level(row.get("Num", ""))
    faculty_divisor = Decimal(_faculty_count(row.get("Faculty", "")))

    workload_if_full = _workload_if_full(
        credit_hours,
        course_level,
        row.get("Num", ""),
        row.get("Desc", ""),
        max_seats,
    )
    workload_per_student = _per_student_workload(
        credit_hours,
        course_level,
        row.get("Num", ""),
        row.get("Desc", ""),
    )

    # Policy IIA.13: split section workload evenly when more than one faculty member teaches the section.
    workload_if_full /= faculty_divisor
    workload_per_student /= faculty_divisor

    # Safety guard: BIM-derived workload values should never exceed 5 workload units.
    workload_if_full, workload_per_student = _cap_workload_values(
        workload_if_full,
        workload_per_student,
        max_seats,
    )

    return {
        "workload_if_full": _format_decimal(workload_if_full),
        "workload_per_student": _format_decimal(workload_per_student),
        "special_workload": "",
    }


def term_key(term: str) -> tuple[int, int]:
    """Return a sortable key for terms."""
    year, season = _split_term(term)
    return int(year), SEASON_ORDER[season]


def get_next_term(term: str) -> str:
    """Return the next academic term after the given term."""
    year, season = _split_term(term)

    if season == "Spring":
        return f"{year} Summer"
    if season == "Summer":
        return f"{year} Fall"
    return f"{year + 1} Spring"


def get_current_term() -> str:
    """Infer the current academic term from the current date."""
    now = datetime.now()
    month = now.month
    year = now.year

    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}")

    if month <= 5:
        season = "Spring"
    elif month <= 7:
        season = "Summer"
    else:
        season = "Fall"

    return f"{year} {season}"


def select_term(cli_term: str | None, available_terms: list[str]) -> tuple[str, str | None]:
    """Choose the term to scrape, with fallback to next/current/latest available term."""
    if cli_term:
        if cli_term in available_terms:
            return cli_term, None

        next_term = get_next_term(get_current_term())
        if next_term in available_terms:
            return next_term, f"Invalid semester: {cli_term}, defaulting to next available term: {next_term}"

        current_term = get_current_term()
        if current_term in available_terms:
            return current_term, f"Invalid semester: {cli_term}, defaulting to current term: {current_term}"

        raise ValueError("No valid term found (input, next, or current)")

    current_term = get_current_term()
    if current_term in available_terms:
        return current_term, None

    sorted_terms = sorted(available_terms, key=term_key)
    return sorted_terms[-1], None


def fetch_available_terms() -> list[str]:
    """Fetch all currently available term options from BIM."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto("https://bim.inclass.today/", wait_until="networkidle")
            select, _selector = _find_term_select(page)
            return _extract_term_options(select.query_selector_all("option"))
        finally:
            browser.close()


def _extract_time_and_room(meeting_cell) -> tuple[str, str]:
    """Extract time and room text from a BIM meeting cell."""
    time_text = ""
    room_text = ""

    for text in meeting_cell.stripped_strings:
        if "-" in text and any(char.isdigit() for char in text) and "/" not in text:
            time_text = text.split(" in ")[0].replace(" ", "").strip()
            if time_text.endswith("in"):
                time_text = time_text[:-2]
            break

    room_link = meeting_cell.find("a", href=lambda href: href and "room.html" in href)
    if room_link:
        room_val = room_link.get_text(strip=True)
        if room_val.upper() != "TBD":
            room_text = room_val

    return time_text, room_text


def _extract_meeting_details(meeting_cell) -> tuple[str, str, str]:
    """Extract days, time, and room from a BIM meeting cell."""
    day_table = meeting_cell.find("table", class_="tblDOW")
    days_text = ""

    if day_table:
        active_days = day_table.find_all("td", class_="active")
        days_text = "".join(day.get_text(strip=True) for day in active_days)
        time_text, room_text = _extract_time_and_room(meeting_cell)
        return days_text, time_text, room_text

    cell_text = meeting_cell.get_text(strip=True)
    if "Internet" in cell_text:
        days_text = "Internet"
        time_text, room_text = _extract_time_and_room(meeting_cell)
        return days_text, time_text, room_text

    day_abbrevs = {"Su", "M", "Tu", "W", "Th", "F", "Sa"}
    days_text = "".join(s for s in meeting_cell.stripped_strings if s in day_abbrevs)
    time_text, room_text = _extract_time_and_room(meeting_cell)
    return days_text, time_text, room_text


def scrape_sections(term: str | None = None) -> list[dict[str, str]]:
    """Scrape BIM sections for one selected term and return rows as dictionaries."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()

            print("Loading page... this may take a moment for the full table.")
            page.goto("https://bim.inclass.today/", wait_until="networkidle")

            select, selector = _find_term_select(page)
            all_terms = _extract_term_options(select.query_selector_all("option"))

            chosen_term, warning = select_term(term, all_terms)
            if warning:
                print(warning)

            page.select_option(selector, label=chosen_term)
            _wait_for_term_results(page)
            print(f"Using term: {chosen_term}")

            soup = BeautifulSoup(page.content(), "html.parser")
            scraped_rows: list[dict[str, str]] = []

            for row in soup.select("tr.trSearch"):
                cells = row.find_all("td")
                if not cells or not cells[0].get_text(strip=True).isdigit():
                    continue

                cell_texts = [cell.get_text(strip=True) for cell in cells]

                meeting_cell = cells[8]
                days_text, time_text, room_text = _extract_meeting_details(meeting_cell)

                faculty_cell = cells[-2]  # Faculty appears in the second-to-last BIM table column
                faculty_links = faculty_cell.find_all("a")
                faculty_names = [link.get_text(strip=True) for link in faculty_links]
                faculty_value = "/".join(faculty_names) if faculty_names else faculty_cell.get_text(" ", strip=True)

                base_row = {
                    "Term": chosen_term,
                    "CRN": cell_texts[0],
                    "Sub": cell_texts[1],
                    "Num": cell_texts[2],
                    "Seq": cell_texts[3],
                    "Crd": cell_texts[4],
                    "Desc": cell_texts[5],
                    "Seats": cell_texts[6].replace(" ", ""),
                    "Waitlist": cell_texts[7],
                    "Days": days_text,
                    "Time": time_text,
                    "Room": room_text,
                    "Faculty": faculty_value,
                }
                base_row.update(_build_workload_fields(base_row))
                scraped_rows.append(base_row)

            return scraped_rows
        finally:
            browser.close()


def write_sections_csv(
    rows: list[dict[str, str]],
    output_path: Path | str = DEFAULT_OUTPUT_PATH,
) -> Path:
    """Write scraped BIM rows to a CSV file."""
    resolved_output_path = Path(output_path)
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "Term",
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

    with resolved_output_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return resolved_output_path


def run(term: str | None = None, output_path: Path | str = DEFAULT_OUTPUT_PATH) -> Path:
    """Run the BIM scraper and save the resulting CSV."""
    scraped_rows = scrape_sections(term=term)
    saved_path = write_sections_csv(scraped_rows, output_path)
    print(f"Success! Saved {len(scraped_rows)} rows to {saved_path}")
    return saved_path


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else None
    run(term=term)