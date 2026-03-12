import csv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def run():
    with sync_playwright() as p:
        # Launch browser and open a new page
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        
        print("Loading page... this may take a moment for the full table.")
        page.goto("https://bim.inclass.today/", wait_until="networkidle")

        # 1. Select the correct Term and sort by CRN
        page.select_option("select", label="2026 Fall")
        page.click('th:has-text("CRN")')
        
        # 2. Wait for the data table to load content
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("td a")

        # 3. Parse the page HTML with BeautifulSoup
        soup = BeautifulSoup(page.content(), 'html.parser')
        scraped_data = []
        
        headers = ['CRN', 'Sub', 'Num', 'Seq', 'Crd', 'Desc', 'Seats', 'Waitlist', 'Days', 'Time', 'Room', 'Faculty']
        
        # Find all table rows
        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            
            # Process only valid data rows (where CRN is a number)
            if cells and cells[0].get_text(strip=True).isdigit():
                crn = cells[0].get_text(strip=True)
                sub = cells[1].get_text(strip=True)
                num = cells[2].get_text(strip=True)
                seq = cells[3].get_text(strip=True)
                crd = cells[4].get_text(strip=True)
                desc = cells[5].get_text(strip=True)
                seats = cells[6].get_text(strip=True).replace(" ", "")
                wait = cells[7].get_text(strip=True)
                
                # --- Day and Time Logic ---
                meeting_cell = cells[8]
                day_table = meeting_cell.find('table', class_='tblDOW')
                days_text, time_text, room_text = "", "", ""

                if day_table:
                    # 1. Get Days
                    active_days = day_table.find_all('td', class_='active')
                    days_text = "".join([day.get_text(strip=True) for day in active_days])

                    # 2. Get Time (skipping dates)
                    for string in meeting_cell.stripped_strings:
                        if "-" in string and any(char.isdigit() for char in string) and "/" not in string:
                            time_text = string.replace(" in", "").replace(" ", "").strip()
                            break
                    # 3. Get Room (Looks for the link containing 'room.html')
                    room_link = meeting_cell.find('a', href=lambda x: x and 'room.html' in x)
                    if room_link:
                        room_text = room_link.get_text(strip=True)
                    

                # --- Faculty Logic ---
                # Targets specifically the Faculty column (2nd from right)
                faculty_cell = cells[-2]
                faculty_links = faculty_cell.find_all('a')
                
                # Grab text from all instructor links and join with a slash
                names = [link.get_text(strip=True) for link in faculty_links]
                faculty = "/".join(names) # for multiple instructors

                # Add the cleaned row to our list
                scraped_data.append([crn, sub, num, seq, crd, desc, seats, wait, days_text, time_text, room_text, faculty])

        # 4. Save results to CSV file
        with open('sections_tab.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(scraped_data)

        print(f"Success! Saved {len(scraped_data)} rows to sections_tab.csv")
        browser.close()

if __name__ == "__main__":
    run()