import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event
import re

# -----------------------------
# CONFIG
# -----------------------------
URL = "https://irunmag.gr/races/world-race/world-marathons-2026"
ICS_FILENAME = "docs/irun_world_marathons_2026_calendar.ics"

GREEK_MONTHS = {
    "Ιανουαρίου": "January",
    "Φεβρουαρίου": "February",
    "Μαρτίου": "March",
    "Απριλίου": "April",
    "Μαΐου": "May",
    "Ιουνίου": "June",
    "Ιουλίου": "July",
    "Αυγούστου": "August",
    "Σεπτεμβρίου": "September",
    "Οκτωβρίου": "October",
    "Νοεμβρίου": "November",
    "Δεκεμβρίου": "December",
}

DATE_RE = re.compile(r"(\d{1,2})\s+([Α-Ωα-ωΐάέήίόύώ]+)\s+(\d{4})")

# -----------------------------
# DATE PARSER
# -----------------------------
def parse_date(text):
    match = DATE_RE.search(text)
    if not match:
        return None

    day, gr_month, year = match.groups()
    en_month = GREEK_MONTHS.get(gr_month)
    if not en_month:
        return None

    return datetime.strptime(f"{day} {en_month} {year}", "%d %B %Y")

# -----------------------------
# SCRAPER
# -----------------------------
def scrape():
    response = requests.get(URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.select_one("#penci-post-entry-inner")
    if not content:
        raise RuntimeError("Could not find main content container")

    races = []
    current_date = None

    for el in content.find_all(["h2", "p"], recursive=True):

        # Month header → reset date
        if el.name == "h2":
            current_date = None
            continue

        # Date line
        strong = el.find("strong")
        if strong and "2026" in strong.text:
            parsed = parse_date(strong.text)
            if parsed:
                current_date = parsed
            continue

        # Race line
        if current_date:
            a = el.find("a", href=True)
            em = el.find("em")

            if not (a and em):
                continue

            title = em.get_text(strip=True)
            url = a["href"]

            # text = el.get_text(" ", strip=True)
            # location = "Unknown"
            # if "(" in text and ")" in text:
            #     location = text.split("(", 1)[1].split(")")[0].strip()

            text = el.get_text(strip=True)
            location = "Unknown"
            if "(" in text and ")" in text:
                inside = text.split("(", 1)[1].split(")")[0]
                location = inside.split(",")[0].strip()
            
            races.append({
                "title": title,
                "date": current_date,
                "location": location,
                "url": url,
            })

    print(f"✅ Found {len(races)} world marathon races")
    return races

# -----------------------------
# ICS GENERATOR
# -----------------------------
def create_ics(races):
    calendar = Calendar()

    for r in races:
        e = Event()
        e.name = r["title"]
        e.begin = r["date"].date()
        e.make_all_day()
        e.location = r["location"]
        e.url = r["url"]
        e.description = (
            f"{r['title']}\n"
            f"Location: {r['location']}\n"
            f"More info: {r['url']}"
        )
        calendar.events.add(e)

    with open(ICS_FILENAME, "w", encoding="utf-8") as f:
        f.writelines(calendar)

    print(f"📅 Saved {ICS_FILENAME}")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    races = scrape()
    create_ics(races)
