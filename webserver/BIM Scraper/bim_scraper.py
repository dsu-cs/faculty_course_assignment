import csv
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "sections_tab.csv"


def scrape_sections() -> list[dict[str, str]]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        print("Loading page... this may take a moment for the full table.")
        page.goto("https://bim.inclass.today/", wait_until="networkidle")
        page.select_option("select", label="2026 Fall")
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
                        time_text = text.replace(" in", "").replace(" ", "").strip()
                        break

                room_link = meeting_cell.find("a", href=lambda href: href and "room.html" in href)
                if room_link:
                    room_text = room_link.get_text(strip=True)

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
                },
            )

        browser.close()
        return scraped_rows


def write_sections_csv(rows: list[dict[str, str]], output_path: Path | str = DEFAULT_OUTPUT_PATH) -> Path:
    resolved_output_path = Path(output_path)
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = ["CRN", "Sub", "Num", "Seq", "Crd", "Desc", "Seats", "Waitlist", "Days", "Time", "Room", "Faculty"]
    with resolved_output_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return resolved_output_path


def run(output_path: Path | str = DEFAULT_OUTPUT_PATH) -> Path:
    scraped_rows = scrape_sections()
    saved_path = write_sections_csv(scraped_rows, output_path)
    print(f"Success! Saved {len(scraped_rows)} rows to {saved_path}")
    return saved_path


if __name__ == "__main__":
    run()
