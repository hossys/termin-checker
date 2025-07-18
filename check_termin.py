import requests
from bs4 import BeautifulSoup
import json
import smtplib
import sqlite3
import os
import pytz
from email_translations import email_translations, WISHLIST_URL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urlencode

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "subscribers.db")
LOG_PATH = os.path.join(BASE_DIR, "check_log.txt")
DOMAIN = "https://terminotify.de"
WISHLIST_URL = "https://www.amazon.de/hz/wishlist/ls/214QLWQZ9B9DR?ref_=wl_share"

city_config = {
    "hamburg": {
        "url": "https://www.vhs-hamburg.de/deutsch/einbuergerungstest-1058",
        "offices": ["Einbürgerungstest"]
    },
    "berlin": {
        "url": "https://service.berlin.de/terminvereinbarung/termin/taken/",
        "offices": ["Einbürgerungstest"]
    },
    "munich": {
        "url": "https://www.mvhs.de/kurse/460-CAT-KAT7869",
        "offices": ["Einbürgerungstest"]
    },
    "frankfurt": {
        "url": "https://tevis.ekom21.de/vhsfra/select2?md=1",
        "offices": ["Einbürgerungstest"]
    },
    "cologne": {
        "url": "https://vhs-koeln.de/Artikel/cmx54859f23489f6.html",
        "offices": ["Einbürgerungstest"]
    },
    "hannover": {
        "url": "https://www.vhs-hannover.de/vhs-programm/deutsch-integration/einbuergerungstest",
        "offices": ["Einbürgerungstest"]
    }
}

def log(text):
    from_zone = pytz.utc
    to_zone = pytz.timezone('Europe/Berlin')
    utc_time = datetime.utcnow().replace(tzinfo=from_zone)
    berlin_time = utc_time.astimezone(to_zone)
    timestamp = berlin_time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n")

def check_hamburg():
    log("🔍 Checking appointments for hamburg")
    url = city_config["hamburg"]["url"]
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"❌ Hamburg: Failed to fetch URL – Status code: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Hamburg: Exception during request: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    page_text = soup.get_text().lower()
    if "voll" in page_text:
        log("ℹ️ Hamburg: Page contains 'voll' – no appointments.")
        return None

    for script in soup.find_all('script', type='application/ld+json'):
        try:
            if not script.string:
                continue
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'ItemList':
                for item in data.get('itemListElement', []):
                    course = item.get('item', {})
                    availability = course.get('offers', {}).get('availability', "")
                    if "SoldOut" not in str(availability):
                        link = course.get('url', url)
                        log(f"✅ Hamburg: Available appointment found: {link}")
                        return link
        except Exception as e:
            log(f"⚠️ Hamburg: JSON parse error: {e}")
            continue
    log("❌ Hamburg: No available courses found.")
    return None


def check_berlin():
    log("🔍 Checking appointments for berlin")
    url = "https://service.berlin.de/terminvereinbarung/termin/taken/"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code != 200:
            log(f"❌ Berlin: Failed request – Status code {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title").get_text(strip=True).lower()

        if "keine termine" in title or "entschuldigung" in title:
            log("ℹ️ Berlin: No appointments available according to title.")
            return None

        log(f"✅ Berlin: Appointment available – page title: {title}")
        return url

    except Exception as e:
        log(f"❌ Berlin: Exception during request – {e}")
        return None

def check_munich():
    log("🔍 Checking appointments for munich")
    url = "https://www.mvhs.de/kurse/deutsch-integration/pruefungen-einbuergerung/einbuergerung/einbuergerungstest/einbuergerungstest/anmeldung-nur-fuer-menschen-mit-wohnort-in-der-landeshauptstadt-muenchen-begrenzte-teilnehmerzahl-10-tage-vor-der-pruefung-bekommen-sie-die-genauen-pruefungszeiten-mit-der-post-zugeschickt-460-C-V674110"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code != 200:
            log(f"❌ Munich: Failed to fetch URL – Status code: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Munich: Exception during request: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    appointment = soup.select_one("li.courseTime")

    if appointment:
        text = appointment.get_text(strip=True).lower()
        log(f"✅ Munich: Appointment found – {text}")
        return url
    else:
        log("❌ Munich: No available appointments found (no courseTime found).")
        return None

def check_frankfurt():
    log("🔍 Checking appointments for frankfurt")
    url = city_config["frankfurt"]["url"]
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code != 200:
            log(f"❌ Frankfurt: Failed to fetch URL – Status code: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Frankfurt: Exception during request: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        dt_termin = soup.find("dt", string=lambda s: s and "Termin" in s)
        if not dt_termin:
            log("❌ Frankfurt: 'Termin' label not found.")
            return None

        dd_termin = dt_termin.find_next_sibling("dd")
        value = dd_termin.get_text(strip=True).lower() if dd_termin else "noch nicht gesetzt"

        if "noch nicht gesetzt" not in value:
            log(f"✅ Frankfurt: Termin is set – value: {value}")
            return url
        else:
            log("ℹ️ Frankfurt: Termin not set yet.")
            return None
    except Exception as e:
        log(f"❌ Frankfurt: Error parsing Termin info – {e}")
        return None

def check_cologne():
    log("🔍 Checking appointments for cologne")
    url = city_config["cologne"]["url"]
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"❌ Cologne: Failed to fetch URL – Status code: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Cologne: Exception during request: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table")
    if not table:
        log("❌ Cologne: No table found on the page.")
        return None

    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            test_date = cells[0].get_text(strip=True)
            status = cells[1].get_text(strip=True).lower()
            if "ausgebucht" not in status and status:
                log(f"✅ Cologne: Available date found – {test_date} (Anmeldeschluss: {status})")
                return url

    log("ℹ️ Cologne: All listed dates are fully booked.")
    return None

def check_hannover():
    log("🔍 Checking appointments for hannover")
    url = "https://www.vhs-hannover.de/vhs-programm/deutsch-integration/einbuergerungstest"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code != 200:
            log(f"❌ Hannover: Failed to fetch URL – Status code: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Hannover: Exception during request: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text(separator=" ", strip=True).lower()

    keywords = [
        "keine termine",
        "keine weiteren termine",
        "alle plätze",
        "ausgebucht",
        "keine anmeldung möglich"
    ]

    if any(kw in page_text for kw in keywords):
        log("ℹ️ Hannover: Page indicates no appointments – match found in keywords.")
        return None
    else:
        log("✅ Hannover: Possible appointment available.")
        return url

def notify_all_subscribers(city, office, link):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, email FROM subscribers
                WHERE city=? AND office=? AND unsubscribed=0
            """, (city, office))
            subscribers = cursor.fetchall()

        log(f"📋 Notifying for city: {city}, office: {office}, found subscribers: {len(subscribers)}")

        for name, email in subscribers:
            log(f"📤 Sending email to {email}")
            send_notification_email(name, email, city, office, link)
    except Exception as e:
        log(f"❌ Error notifying subscribers: {e}")


def send_notification_email(name, to_email, city, office, link):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    unsubscribe_link = f"{DOMAIN}/unsubscribe?{urlencode({'email': to_email, 'city': city, 'office': office})}"

    # Get language from DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM subscribers WHERE email=? AND city=? AND office=?", (to_email, city, office))
    result = cursor.fetchone()
    conn.close()

    language = result[0] if result and result[0] in email_translations else 'en'
    t = email_translations[language]

    subject = t.get('subject_notify', f"✅ New {office} appointment available in {city.capitalize()}!")


    if 'body_notify' in t:
        body = t['body_notify'](name, city, office, link, WISHLIST_URL, unsubscribe_link)
    else:

        body = f"""
        <p>Hi {name},</p>
        <p>A new appointment for <strong>{office}</strong> in <strong>{city.capitalize()}</strong> is now available!</p>
        <p><a href="{link}" target="_blank" style="background-color:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Click here to register</a></p>
        <p>Please act quickly – slots can fill up fast.</p>
        <p>You can support us by checking out our <a href="{WISHLIST_URL}" target="_blank">wishlist</a>. 🎁</p>
        <p>If you're done and want to unsubscribe, <a href="{unsubscribe_link}">click here</a>.</p>
        <p>Cheers,<br>Termin Notify Team</p>
        """

    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = to_email
    message.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        log(f"📧 Email sent to {to_email}")
    except Exception as e:
        log(f"❌ Error sending email to {to_email}: {str(e)}")
if __name__ == "__main__":
    log("🚀 --- Cron run started ---")
    for city, check_function in [
        ("hamburg", check_hamburg),
        ("berlin", check_berlin),
        ("munich", check_munich),
        ("frankfurt", check_frankfurt),
        ("cologne", check_cologne),
        ("hannover", check_hannover),
    ]:
        link = check_function()
        if link:
            for office in city_config[city]["offices"]:
                notify_all_subscribers(city, office, link)
    log("✅ --- Cron run finished ---\n")