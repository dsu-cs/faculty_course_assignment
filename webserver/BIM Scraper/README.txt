Create venv
 - python -m venv venv

Activate venv
 - .\venv\Scripts\activate

Install Dependencies
 - pip install -r requirements.txt

Install Playwright Browsers
 - playwright install chromium

Run (default: auto-select next available term)
 - python bim_scraper.py

Run with a specific term
 - python bim_scraper.py "2026 Fall"
 
Notes
 - If an invalid term is provided, the scraper will fallback to the next available term based on the current date.
 - Term format must be: "YYYY Season" (e.g., "2026 Fall", "2025 Spring", "2026 Summer")