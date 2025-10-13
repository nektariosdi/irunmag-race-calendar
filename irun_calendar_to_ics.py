import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event

# -----------------------------
# CONFIGURATION
# -----------------------------
# Change this URL for 2026 when available
RACE_CALENDAR_URL = "https://irunmag.gr/race-calendar-2025"
ICS_FILENAME = "irun_2025_calendar.ics"

# Greek month mapping to English for parsing
GREEK_MONTHS = {
    "Ιανουαρίου": "January", "Φεβρουαρίου": "February", "Μαρτίου": "March",
    "Απριλίου": "April", "Μαΐου": "May", "Ιουνίου": "June",
    "Ιουλίου": "July", "Αυγούστου": "August", "Σεπτεμβρίου": "September",
    "Οκτωβρίου": "October", "Νοεμβρίου": "November", "Δεκεμβρίου": "December"
}

# -----------------------------
# SCRAPER
# -----------------------------
def scrape_irun_calendar(url=RACE_CALENDAR_URL):
    """Scrape iRunMag race calendar and return a list of race dicts."""
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    races = []

    for month_block in soup.select("div.month-block"):
        headers = month_block.find_all("h4")
        for header in headers:
            date_text = header.get_text(strip=True)
            parts = date_text.split()
            date = None

            if len(parts) >= 3:
                for gr, en in GREEK_MONTHS.items():
                    if gr in parts:
                        day = ''.join([c for c in parts[1] if c.isdigit()])
                        if day:
                            try:
                                date = datetime.strptime(f"{day} {en} 2025", "%d %B %Y")
                            except Exception:
                                pass
                        break

            ul = header.find_next_sibling("ul")
            if not ul or not date:
                continue

            for li in ul.find_all("li"):
                title_tag = li.find("a") or li.find("em") or li.find("i")
                title = title_tag.get_text(strip=True) if title_tag else li.get_text(strip=True)
                link = title_tag["href"] if title_tag and title_tag.has_attr("href") else url

                # Extract location from parentheses
                text = li.get_text(strip=True)
                location = "Unknown"
                if "(" in text and ")" in text:
                    inside = text.split("(", 1)[1].split(")")[0]
                    location = inside.split(",")[0].strip()

                races.append({
                    "title": title,
                    "date": date,
                    "location": location,
                    "url": link
                })

    print(f"✅ Found {len(races)} races.")
    return races

# -----------------------------
# ICS GENERATOR
# -----------------------------
def create_ics(races, filename=ICS_FILENAME):
    """Create ICS calendar file from race list (all-day events)."""
    calendar = Calendar()
    for race in races:
        event = Event()
        event.name = race["title"]
        event.begin = race["date"].date()  # All-day event
        event.make_all_day()
        event.location = race["location"]
        event.url = race["url"]
        event.description = f"{race['title']}\nLocation: {race['location']}\nMore info: {race['url']}"
        calendar.events.add(event)

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(calendar)
    print(f"📅 Saved {len(races)} all-day races to {filename}")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    races = scrape_irun_calendar()
    create_ics(races)
