import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import uuid

NAF_URL = "https://member.thenaf.net/index.php?module=NAF&type=tournaments"

EXPECTED_HEADERS = [
    "tournament",
    "country",
    "state",
    "city",
    "start date",
    "end date",
    "variant",
    "major"
]

def find_tournament_table(soup):
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        header_cells = rows[0].find_all(["th", "td"])
        header_texts = [c.get_text(strip=True).lower() for c in header_cells]

        # Check if this table matches the expected header structure
        if len(header_texts) >= 8 and all(
            h in header_texts[i] for i, h in enumerate(EXPECTED_HEADERS)
        ):
            return table

    return None


def fetch_events():
    resp = requests.get(NAF_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []

    table = find_tournament_table(soup)
    if not table:
        print("Tournament table not found")
        return events

    rows = table.find_all("tr")[1:]  # skip header row

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue

        # Extract fields
        name_cell = cols[0].find("a")
        name = name_cell.get_text(strip=True) if name_cell else "NAF Tournament"
        link = name_cell["href"] if name_cell and name_cell.has_attr("href") else ""

        country = cols[1].get_text(strip=True)
        state = cols[2].get_text(strip=True)
        city = cols[3].get_text(strip=True)
        start_date = cols[4].get_text(strip=True)
        end_date = cols[5].get_text(strip=True)
        variant = cols[6].get_text(strip=True)
        major = cols[7].get_text(strip=True)

        # Parse dates
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except:
            continue

        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except:
            end = start

        # Build location
        location_parts = [city, state, country]
        location = ", ".join([p for p in location_parts if p])

        # Build summary
        summary = name
        if variant:
            summary += f" ({variant})"
        if major.lower() == "yes":
            summary += " [MAJOR]"

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
