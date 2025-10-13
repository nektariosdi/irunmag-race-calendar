import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ics import Calendar, Event

# -----------------------------
# CONFIGURATION
# -----------------------------
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
            ul = header.find_next_sibling("ul")
            if not ul:
                continue

            for li in ul.find_all("li"):
                text = li.get_text(strip=True)

                # -----------------------------
                # 1️⃣ Extract URL and Title
                # -----------------------------
                link = RACE_CALENDAR_URL  # default fallback
                title = None

                # Prefer last non-empty <a> text
                a_tags = li.find_all("a")
                for a in reversed(a_tags):
                    t = a.get_text(strip=True)
                    if t:
                        title = t
                        link = a["href"] if a.has_attr("href") else RACE_CALENDAR_URL
                        break

                # If no <a> or empty, pick the longest <em> or <i> text
                if not title:
                    candidates = li.find_all(["em", "i"])
                    texts = [c.get_text(strip=True) for c in candidates if c.get_text(strip=True)]
                    if texts:
                        title = max(texts, key=len)

                # Fallback: text before parentheses
                if not title:
                    title = text.split("(")[0].strip()

                # -----------------------------
                # 2️⃣ Extract location
                # -----------------------------
                location = "Unknown"
                if "(" in text and ")" in text:
                    inside = text.split("(", 1)[1].split(")")[0]
                    location = inside.split(",")[0].strip()

                # -----------------------------
                # 3️⃣ Parse date(s)
                # -----------------------------
                date = None
                end_date = None
                if "(" in text and ")" in text:
                    date_part = text.split("(", 1)[1].split(")")[0].split(",")[0].strip()
                    # Multi-day check: "25-26/10"
                    if "-" in date_part and "/" in date_part:
                        start_day, rest = date_part.split("-", 1)
                        end_day, month_part = rest.split("/", 1)
                        month_part = month_part.strip()
                        try:
                            month = int(month_part)  # numeric month
                        except ValueError:
                            month = 10  # fallback
                        date = datetime.strptime(f"{start_day}/{month}/2025", "%d/%m/%Y").date()
                        end_date = datetime.strptime(f"{end_day}/{month}/2025", "%d/%m/%Y").date()
                    else:
                        # Single-day: try to parse Greek month
                        for gr, en in GREEK_MONTHS.items():
                            if gr in date_part:
                                day = ''.join([c for c in date_part if c.isdigit()])
                                if day:
                                    try:
                                        date = datetime.strptime(f"{day} {en} 2025", "%d %B %Y").date()
                                    except Exception:
                                        pass

                if not date:
                    continue  # skip if we can't parse a date

                races.append({
                    "title": title,
                    "date": date,
                    "end_date": end_date,
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
        if race.get("end_date"):
            # ICS end date is exclusive, so add 1 day
            event.begin = race["date"]
            event.end = race["end_date"] + timedelta(days=1)
        else:
            event.begin = race["date"]
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
