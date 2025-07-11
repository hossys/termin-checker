import requests
from bs4 import BeautifulSoup
import json
import smtplib
import sqlite3
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "subscribers.db"

city_config = {
    "hamburg": {
        "url": "https://www.vhs-hamburg.de/deutsch/einbuergerungstest-1058",
        "offices": ["Einbürgerungstest"]
    }
}

def check_available(city_key):
    city = city_config.get(city_key)
    if not city:
        return None

    url = city["url"]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    if "voll" in soup.get_text().lower():
        return None

    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'ItemList':
                for item in data.get('itemListElement', []):
                    course = item.get('item', {})
                    availability = course.get('offers', {}).get('availability', [])
                    if "SoldOut" not in str(availability):
                        return course.get('url', url)
        except Exception:
            continue
    return None

def notify_all_subscribers(city, office, link):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, email FROM subscribers
        WHERE city=? AND office=?
    """, (city, office))
    subscribers = cursor.fetchall()
    conn.close()

    for name, email in subscribers:
        send_notification_email(name, email, city, office, link)

def send_notification_email(name, to_email, city, office, link):
    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')

    subject = f"✅ New {office} appointment available in {city}!"
    body = f"""
Hi {name},

A new appointment for {office} in {city} is now available!

Here is the registration link:  
{link}

Please act quickly – slots can fill up fast.

Best regards,  
Terminotify Team
"""

    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Error sending email to {to_email}: {str(e)}")

if __name__ == "__main__":
    city_key = "hamburg"
    link = check_available(city_key)
    if link:
        print("✅ Appointment found!")
        for office in city_config[city_key]["offices"]:
            notify_all_subscribers(city_key.capitalize(), office, link)
    else:
        print("❌ No appointments available.")