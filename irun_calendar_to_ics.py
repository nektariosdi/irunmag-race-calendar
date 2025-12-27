import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event

# -----------------------------
# CONFIGURATION
# -----------------------------
RACE_CALENDAR_URLS = [
    "https://irunmag.gr/race-calendar-2025",
    "https://irunmag.gr/races/world-race/world-marathons-2026/",
]
#RACE_CALENDAR_URLS.append("https://irunmag.gr/race-calendar-2026")
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
def scrape_irun_calendar(url):
    """Scrape ONE iRunMag calendar page and return races."""
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
                        day = ''.join(c for c in parts[1] if c.isdigit())
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
                link = url  # fallback to page URL
                title = None

                # Prefer last non-empty <a>
                for a in reversed(li.find_all("a")):
                    text = a.get_text(strip=True)
                    if text:
                        title = text
                        if a.has_attr("href"):
                            link = a["href"]
                        break

                # Fallback: longest <em> or <i>
                if not title:
                    texts = [
                        t.get_text(strip=True)
                        for t in li.find_all(["em", "i"])
                        if t.get_text(strip=True)
                    ]
                    if texts:
                        title = max(texts, key=len)

                # Final fallback
                if not title:
                    title = li.get_text(strip=True).split("(")[0].strip()

                # Location
                text = li.get_text(strip=True)
                location = "Unknown"
                if "(" in text and ")" in text:
                    location = text.split("(", 1)[1].split(")")[0].split(",")[0].strip()

                races.append({
                    "title": title,
                    "date": date,
                    "location": location,
                    "url": link
                })

    print(f"✅ {len(races)} races scraped from {url}")
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
    all_races = []

    for url in RACE_CALENDAR_URLS:
        try:
            races = scrape_irun_calendar(url)
            all_races.extend(races)
        except Exception as e:
            print(f"❌ Failed scraping {url}: {e}")

    create_ics(all_races)

