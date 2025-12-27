import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event
import re

# -----------------------------
# CONFIGURATION
# -----------------------------
WORLD_MARATHONS_URL = "https://irunmag.gr/races/world-race/world-marathons-2026/"
ICS_FILENAME = "irun_world_marathons_2026_calendar.ics"

# -----------------------------
# PARSE WORLD MARATHONS
# -----------------------------
def scrape_world_marathons(url=WORLD_MARATHONS_URL):
    """Scrapes the World Marathons 2026 page and returns a list of race dicts."""
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    races = []

    # The page contains a flat <ul><li> list of races with dates like "05/04/2026"
    for li in soup.select("ul li"):
        text = li.get_text(" ", strip=True)

        # Try to find the date in format DD/MM/YYYY
        date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
        if not date_match:
            continue

        day, month, year = map(int, date_match.groups())
        try:
            race_date = datetime(year, month, day).date()
        except ValueError:
            continue

        # Title: the text before the first "("
        title = text.split("(")[0].strip()

        # Extract location if available in parentheses after the date
        location = "Unknown"
        paren_match = re.search(r"\(([^)]+)\)", text)
        if paren_match:
            parts = [p.strip() for p in paren_match.group(1).split(",")]
            if len(parts) > 1:
                location = parts[1]

        # If there’s a link inside <a>, use that; else fallback to source URL
        a_tag = li.find("a", href=True)
        link = a_tag["href"] if a_tag else url

        races.append({
            "title": title,
            "date": race_date,
            "location": location,
            "url": link,
        })

    print(f"✅ Found {len(races)} world marathons.")
    return races

# -----------------------------
# GENERATE ICS
# -----------------------------
def create_ics(races, filename=ICS_FILENAME):
    """Creates an ICS calendar file for the given races."""
    calendar = Calendar()

    for race in races:
        event = Event()
        event.name = race["title"]
        event.begin = race["date"]
        event.make_all_day()
        event.location = race["location"]
        event.url = race["url"]
        event.description = f"{race['title']}\nLocation: {race['location']}\nMore info: {race['url']}"

        calendar.events.add(event)

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(calendar)

    print(f"📅 Saved {len(races)} world marathon races to {filename}.")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    races = scrape_world_marathons()
    create_ics(races)
