import csv
import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SEASON_ORDER = {"Spring": 1, "Summer": 2, "Fall": 3}
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "sections_tab.csv"


def term_key(term: str) -> tuple[int, int]:
    year, season = term.split()
    return (int(year), SEASON_ORDER[season])


def get_next_term(term: str) -> str:
    year, season = term.split()
    year = int(year)

    if season == "Spring":
        return f"{year} Summer"
    if season == "Summer":
        return f"{year} Fall"
    return f"{year + 1} Spring"


def get_current_term() -> str:
    now = datetime.now()
    month = now.month
    year = now.year

    if month <= 5:
        season = "Spring"
    elif month <= 7:
        season = "Summer"
    else:
        season = "Fall"

    return f"{year} {season}"


def select_term(cli_term: str | None, available_terms: list[str]) -> tuple[str, str | None]:
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


def scrape_sections(term: str | None = None) -> list[dict[str, str]]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        print("Loading page... this may take a moment for the full table.")
        page.goto("https://bim.inclass.today/", wait_until="networkidle")

        select = page.query_selector("select")
        if select is None:
            browser.close()
            raise RuntimeError("Could not find term dropdown on page.")

        options = select.query_selector_all("option")
        all_terms = [
            opt.inner_text().strip()
            for opt in options
            if opt.inner_text().strip()
            and opt.inner_text().strip() != "Select..."
            and len(opt.inner_text().strip().split()) == 2
            and opt.inner_text().strip().split()[1] in SEASON_ORDER
        ]

        chosen_term, warning = select_term(term, all_terms)
        if warning:
            print(warning)

        page.select_option("select", label=chosen_term)
        print(f"Using term: {chosen_term}")

        page.click('th:has-text("CRN")')

        page.wait_for_load_state("networkidle")
        page.wait_for_selector("td a")

        soup = BeautifulSoup(page.content(), "html.parser")
        scraped_rows: list[dict[str, str]] = []

        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if not cells or not cells[0].get_text(strip=True).isdigit():
                continue

            meeting_cell = cells[8]
            day_table = meeting_cell.find("table", class_="tblDOW")
            days_text = ""
            time_text = ""
            room_text = ""

            if day_table:
                active_days = day_table.find_all("td", class_="active")
                days_text = "".join(day.get_text(strip=True) for day in active_days)

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
            else:
                cell_text = meeting_cell.get_text(strip=True)

                if "Internet" in cell_text:
                    days_text = "Internet"
                else:
                    day_abbrevs = {"Su", "M", "Tu", "W", "Th", "F", "Sa"}
                    days_text = "".join(s for s in meeting_cell.stripped_strings if s in day_abbrevs)

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

            faculty_cell = cells[-2]
            faculty_links = faculty_cell.find_all("a")
            faculty_names = [link.get_text(strip=True) for link in faculty_links]

            scraped_rows.append(
                {
                    "CRN": cells[0].get_text(strip=True),
                    "Sub": cells[1].get_text(strip=True),
                    "Num": cells[2].get_text(strip=True),
                    "Seq": cells[3].get_text(strip=True),
                    "Crd": cells[4].get_text(strip=True),
                    "Desc": cells[5].get_text(strip=True),
                    "Seats": cells[6].get_text(strip=True).replace(" ", ""),
                    "Waitlist": cells[7].get_text(strip=True),
                    "Days": days_text,
                    "Time": time_text,
                    "Room": room_text,
                    "Faculty": "/".join(faculty_names),
                }
            )

        browser.close()
        return scraped_rows


def write_sections_csv(
    rows: list[dict[str, str]],
    output_path: Path | str = DEFAULT_OUTPUT_PATH,
) -> Path:
    resolved_output_path = Path(output_path)
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = ["CRN", "Sub", "Num", "Seq", "Crd", "Desc", "Seats", "Waitlist", "Days", "Time", "Room", "Faculty"]

    with resolved_output_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return resolved_output_path


def run(term: str | None = None, output_path: Path | str = DEFAULT_OUTPUT_PATH) -> Path:
    scraped_rows = scrape_sections(term=term)
    saved_path = write_sections_csv(scraped_rows, output_path)
    print(f"Success! Saved {len(scraped_rows)} rows to {saved_path}")
    return saved_path


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else None
    run(term=term)
