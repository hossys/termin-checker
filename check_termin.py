import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
import os

def check_available_termin():
    url = 'https://www.vhs-hamburg.de/deutsch/einbuergerungstest-1058'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'ItemList':
                for item in data.get('itemListElement', []):
                    course = item.get('item', {})
                    availability = course.get('offers', {}).get('availability', [])
                    if "SoldOut" not in str(availability):
                        return course.get('url', 'https://www.vhs-hamburg.de')
        except Exception:
            continue
    return None

def send_email_notification(link):
    msg = MIMEText(f"✅ Einbürgerungstest-Termin verfügbar!\n\nLink: {link}")
    msg['Subject'] = '📬 Neuer Termin verfügbar!'
    msg['From'] = os.getenv('EMAIL')
    msg['To'] = os.getenv('EMAIL')

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(os.getenv('EMAIL'), os.getenv('APP_PASSWORD'))
        server.send_message(msg)

if __name__ == "__main__":
    result = check_available_termin()
    if result:
        send_email_notification(result)
        print("✅ Termin gefunden. E-Mail gesendet.")
    else:
        print("❌ Kein Termin verfügbar.")
