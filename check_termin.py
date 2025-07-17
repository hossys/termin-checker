import requests
from bs4 import BeautifulSoup
import json
import smtplib
import sqlite3
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "subscribers.db")
LOG_PATH = os.path.join(BASE_DIR, "check_log.txt")

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
    }
}

def log(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n")

def check_hamburg():
    try:
        log("🔍 Checking appointments for hamburg")
        url = city_config["hamburg"]["url"]
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"❌ Hamburg: Failed to fetch URL – Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        if "voll" in soup.get_text().lower():
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
        log("❌ Hamburg: No available courses found.")
        return None
    except Exception as e:
        log(f"❌ Hamburg: General error – {e}")
        return None

def check_berlin():
    try:
        log("🔍 Checking appointments for berlin")
        url = "https://service.berlin.de/terminvereinbarung/termin/day/"
        payload = {
            "dienstleister": "122210",
            "anliegen[]": "120686",
            "termin": "1"
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest"
        }
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code != 200:
            log(f"❌ Berlin: Failed request – Status code {response.status_code}")
            return None
        if "keine freien termine" in response.text.lower():
            log("ℹ️ Berlin: No available appointments.")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all("a"):
            href = link.get("href", "")
            if "calendar" in href:
                full_link = f"https://service.berlin.de{href}"
                log(f"✅ Berlin: Available appointment found: {full_link}")
                return full_link
        log("❌ Berlin: No appointment links found in HTML.")
        return None
    except Exception as e:
        log(f"❌ Berlin: Exception during check – {e}")
        return None

def check_munich():
    try:
        log("🔍 Checking appointments for munich")
        url = city_config["munich"]["url"]
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"❌ Munich: Failed to fetch URL – Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        all_cards = soup.select("div.card-list-item-info")
        if not all_cards:
            log("❌ Munich: No appointment cards found (empty all_cards).")
            return None

        for i, card in enumerate(all_cards):
            card_text = card.get_text(separator=" ", strip=True).lower()
            log(f"🔎 Munich: card content: {card_text}")
            if any(day in card_text for day in ["termin", "fr.", "mo.", "di.", "mi."]):
                log(f"✅ Munich: Found appointment card: {card_text}")
                return url
        log("❌ Munich: No available appointments found.")
        return None
    except Exception as e:
        log(f"❌ Munich: General error – {e}")
        return None

def check_frankfurt():
    try:
        log("🔍 Checking appointments for frankfurt")
        url = city_config["frankfurt"]["url"]
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"❌ Frankfurt: Failed to fetch URL – Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        dt = soup.find("dt", string="Termin")
        if not dt:
            log("❌ Frankfurt: Termin label not found.")
            return None
        dd = dt.find_next_sibling("dd")
        if not dd:
            log("❌ Frankfurt: Termin value not found.")
            return None
        if dd.text.strip().lower() != "noch nicht gesetzt":
            log(f"✅ Frankfurt: Appointment found – Termin: {dd.text.strip()}")
            return url
        else:
            log("ℹ️ Frankfurt: Termin not set yet.")
            return None
    except Exception as e:
        log(f"❌ Frankfurt: General error – {e}")
        return None

def check_cologne():
    try:
        log("🔍 Checking appointments for cologne")
        url = city_config["cologne"]["url"]
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"❌ Cologne: Failed to fetch URL – Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table")
        if table and "ausgebucht" not in table.get_text().lower():
            log(f"✅ Cologne: Appointment found – check page manually: {url}")
            return url
        else:
            log("ℹ️ Cologne: All listed dates are fully booked.")
            return None
    except Exception as e:
        log(f"❌ Cologne: General error – {e}")
        return None

def notify_all_subscribers(city, office, link):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, email FROM subscribers
                WHERE LOWER(city)=? AND office=? AND unsubscribed=0
            """, (city.lower(), office))
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

    if city.lower() == "cologne":
        subject = f"ℹ️ {office} appointment info – {city.capitalize()}"
        body = f"""
        <p>Hi {name},</p>
        <p>There’s now a new appointment date listed for <strong>{office}</strong> in <strong>{city.capitalize()}</strong>.</p>
        <p><strong>Important:</strong> Registration is only possible <u>in person</u> at the VHS Kundenzentrum in Köln. There is no online booking available.</p>
        <p>Please bring your valid passport and register as soon as possible at the address mentioned on the page below:</p>
        <p><a href="{link}" target="_blank">See appointment details</a></p>
        <p>Best regards,<br>Terminotify Team</p>
        """
    else:
        subject = f"✅ New {office} appointment available in {city.capitalize()}!"
        body = f"""
        <p>Hi {name},</p>
        <p>A new appointment for <strong>{office}</strong> in <strong>{city.capitalize()}</strong> is now available!</p>
        <p><a href="{link}" target="_blank">Click here to register</a></p>
        <p>Please act quickly – slots can fill up fast.</p>
        <p>If you already got your appointment, please <a href="https://terminotify.de/unsubscribe?email={to_email}">unsubscribe here</a>.</p>
        <p>Best regards,<br>Terminotify Team</p>
        """

    message = MIMEText(body, "html", "utf-8")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
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
    ]:
        try:
            link = check_function()
            if link:
                for office in city_config[city]["offices"]:
                    notify_all_subscribers(city, office, link)
        except Exception as e:
            log(f"❌ Error during city check '{city}': {e}")
    log("✅ --- Cron run finished ---\n")