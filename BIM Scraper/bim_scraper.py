import csv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        
        print("Loading page... this may take a moment for the full table.")
        page.goto("https://bim.inclass.today/", wait_until="networkidle")

        # 1. Select the Term
        page.select_option("select", label="2026 Fall")
        page.click('th:has-text("CRN")')
        
        # 2. Wait for the data to load completely
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("td a")

        # 3. Parse the full page content
        soup = BeautifulSoup(page.content(), 'html.parser')
        scraped_data = []
        
        headers = ['CRN', 'Sub', 'Num', 'Seq', 'Crd', 'Desc', 'Seats Available', 'Waitlist Size', 'Faculty']
        
        # Find all rows in the table body
        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            
            # Check if it's a valid data row (CRN must be a number)
            if cells and cells[0].get_text(strip=True).isdigit():
                crn = cells[0].get_text(strip=True)
                sub = cells[1].get_text(strip=True)
                num = cells[2].get_text(strip=True)
                seq = cells[3].get_text(strip=True)
                crd = cells[4].get_text(strip=True)
                desc = cells[5].get_text(strip=True)
                seats = cells[6].get_text(strip=True)
                wait = cells[7].get_text(strip=True)

                # Use the negative index trick to get Faculty reliably
                faculty = cells[-2].get_text(strip=True)
                
                # Double-check: if we accidentally grabbed a day-of-week icon
                if any(day in faculty for day in ['Su', 'M', 'Tu', 'W', 'Th', 'F', 'Sa']):
                    links = row.find_all('a')
                    if len(links) >= 3:
                        faculty = links[-1].get_text(strip=True)

                scraped_data.append([crn, sub, num, seq, crd, desc, seats, wait, faculty])

        # 4. Save everything to CSV
        with open('sections_tab.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(scraped_data)

        print(f"Success! Saved {len(scraped_data)} rows to sections_tab.csv")
        browser.close()

if __name__ == "__main__":
    run()