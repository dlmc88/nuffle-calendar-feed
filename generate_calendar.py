import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import uuid

NUFFLE_URL = "https://nuffle.xyz/calendar"

def fetch_events():
    resp = requests.get(NUFFLE_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []

    # This is a placeholder selector — once you show me the HTML structure,
    # I will tailor this to match the real event blocks.
    for ev in soup.find_all("div"):
        text = ev.get_text(" ", strip=True)
        if not text:
            continue

        # Very rough placeholder parsing
        # We will refine this once we see the actual DOM
        if "202" in text:  # crude date detection
            events.append({
                "summary": text,
                "start": datetime.utcnow(),
                "end": datetime.utcnow() + timedelta(hours=1),
                "location": ""
            })

    return events

def format_dt(dt):
    return dt.strftime("%Y%m%dT%H%M%S")

def generate_ics(events):
    lines = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append("PRODID:-//Luke//Nuffle Calendar//EN")
    lines.append("CALSCALE:GREGORIAN")
    lines.append("METHOD:PUBLISH")

    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for ev in events:
        uid = str(uuid.uuid4()) + "@nuffle-feed"
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{now}")
        lines.append(f"DTSTART:{format_dt(ev['start'])}")
        lines.append(f"DTEND:{format_dt(ev['end'])}")
        summary = ev["summary"].replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
        lines.append(f"SUMMARY:{summary}")
        if ev["location"]:
            loc = ev["location"].replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
            lines.append(f"LOCATION:{loc}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

if __name__ == "__main__":
    events = fetch_events()
    ics = generate_ics(events)
    with open("calendar.ics", "w", encoding="utf-8") as f:
        f.write(ics)
