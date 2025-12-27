import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event
import re

URL = "https://irunmag.gr/races/world-race/world-marathons-2026"
ICS_FILENAME = "irun_world_marathons_2026_calendar.ics"

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

def parse_date(text):
    match = DATE_RE.search(text)
    if not match:
        return None

    day, gr_month, year = match.groups()
    en_month = GREEK_MONTHS.get(gr_month)
    if not en_month:
        return None

    return datetime.strptime(f"{day} {en_month} {year}", "%d %B %Y")

def scrape():
    r = requests.get(URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    content = soup.select_one("#penci-post-entry-inner")
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
            a = el.find("a")
            em = el.find("em")

            if a and em:
                title = em.get_text(strip=True)
                url = a.get("href")

                text = el.get_text(" ", strip=True)
                location = "Unknown"
                if "(" in text and ")" in text:
                    location = text.split("(", 1)[1].split(")")[0].strip()

                races.append({
                    "title": title,
                    "date": current_date,
                    "location": location,
                    "url": url,
                })

    print(f"✅ Found {len(races)} races")
    return races

def create_ics(races):
    cal = Calendar()

    for r in races:
        e = Event()
        e.name = r["title"]
        e.begin = r["date"].date()
        e.make_all_day()
        e.location = r["location"]
        e.url = r["url"]
        e.description = f"{r['title']}\n{r['location']()
