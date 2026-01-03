import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import uuid

NAF_URL = "https://member.thenaf.net/index.php?module=NAF&type=tournaments"

def fetch_events():
    resp = requests.get(NAF_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []

    # Find the tournaments table
    table = soup.find("table")
    if not table:
        return events

    rows = table.find_all("tr")

    # Skip header row
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        # Extract fields
        name_cell = cols[0].find("a")
        name = name_cell.get_text(strip=True) if name_cell else "NAF Tournament"
        link = name_cell["href"] if name_cell and name_cell.has_attr("href") else ""

        format_type = cols[1].get_text(strip=True)
        city = cols[2].get_text(strip=True)
        region = cols[3].get_text(strip=True)
        start_date = cols[4].get_text(strip=True)
        end_date = cols[5].get_text(strip=True)
        country = cols[6].get_text(strip=True)

        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except:
