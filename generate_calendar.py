import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import uuid

NAF_URL = "https://member.thenaf.net/index.php?module=NAF&type=tournaments"

def find_tournament_table(soup):
    # Find all tables on the page
    tables = soup.find_all("table")

    for table in tables:
        # Look for a header row containing "Tournament"
        header = table.find("tr")
        if not header:
            continue

        header_cells = [c.get_text(strip=True).lower() for c in header.find_all(["th", "td"])]
        if "tournament" in header_cells:
            return table

    return None


def fetch_events():
    resp = requests.get(NAF_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []

    # Find the correct tournaments table
    table = find_tournament_table(soup)
    if not table:
        print("No tournament table found")
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
            continue

        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except:
            end = start

        # Build location string
        location_parts = [p for p in [city, region, country] if p]
        location = ", ".join(location_parts)

        # Build summary
        summary = name
        if format_type:
            summary += f" ({format_type})"

        events.append({
            "summary": summary,
            "start": start,
            "end": end,
            "location": location,
            "url": link
        })

    return events


def format_dt(dt):
    return dt.strftime("%Y%m%d")


def escape(text):
    return (
        text.replace("\\", "\\\\")
            .replace(",", "\\,")
            .replace(";", "\\;")
            .replace("\n", "\\n")
    )


def generate_ics(events):
    lines = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append("PRODID:-//Luke//NAF Tournament Calendar//EN")
    lines.append("CALSCALE:GREGORIAN")
    lines.append("METHOD:PUBLISH")

    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for ev in events:
        uid = str(uuid.uuid4()) + "@naf-calendar"
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{now}")

        # All-day events
        lines.append(f"DTSTART;VALUE=DATE:{format_dt(ev['start'])}")
        lines.append(f"DTEND;VALUE=DATE:{format_dt(ev['end'] + timedelta(days=1))}")

        lines.append(f"SUMMARY:{escape(ev['summary'])}")

        if ev["location"]:
            lines.append(f"LOCATION:{escape(ev['location'])}")

        if ev["url"]:
            lines.append(f"URL:{escape(ev['url'])}")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


if __name__ == "__main__":
    events = fetch_events()
    ics = generate_ics(events)
    with open("calendar.ics", "w", encoding="utf-8") as f:
        f.write(ics)
