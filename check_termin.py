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
    }
}


def log(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n")


def check_hamburg():
    city_key = "hamburg"
    log(f"🔍 Checking appointments for {city_key}")
    url = city_config[city_key]["url"]
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"❌ Failed to fetch {url} – Status code: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Exception during request to {url}: {e}")
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
    url = "https://service.berlin.de/terminvereinbarung/termin/day/"
    payload = {
        "dienstleister": "122210",  # VHS Berlin
        "anliegen[]": "120686",     # Einbürgerungstest
        "termin": "1"
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
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


def notify_all_subscribers(city, office, link):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, email FROM subscribers
                WHERE city=? AND office=?
            """, (city, office))
            subscribers = cursor.fetchall()

        for name, email in subscribers:
            send_notification_email(name, email, city, office, link)

    except Exception as e:
        log(f"❌ Error notifying subscribers: {e}")


def send_notification_email(name, to_email, city, office, link):
    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')

    subject = f"✅ New {office} appointment available in {city.capitalize()}!"
    body = f"""
Hi {name},

A new appointment for {office} in {city.capitalize()} is now available!

<a href="{link}">Click here to register</a>

Please act quickly – slots can fill up fast.

Best regards,  
Terminotify Team
"""

    message = MIMEText(body, "html")
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        log(f"📧 Email sent to {to_email}")
    except Exception as e:
        log(f"❌ Error sending email to {to_email}: {str(e)}")


if __name__ == "__main__":
    log("🚀 --- Cron run started ---")

    hamburg_link = check_hamburg()
    if hamburg_link:
        for office in city_config["hamburg"]["offices"]:
            notify_all_subscribers("hamburg", office, hamburg_link)

    berlin_link = check_berlin()
    if berlin_link:
        for office in city_config["berlin"]["offices"]:
            notify_all_subscribers("berlin", office, berlin_link)

    log("✅ --- Cron run finished ---\n")