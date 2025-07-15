from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlencode

load_dotenv()

app = Flask(__name__)
DB_PATH = "subscribers.db"
WISHLIST_URL = "https://www.amazon.de/hz/wishlist/ls/214QLWQZ9B9DR?ref_=wl_share"
DOMAIN = "https://terminotify.de"

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            city TEXT NOT NULL,
            office TEXT NOT NULL,
            unsubscribed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

initialize_db()

@app.route('/')
def index():
    return render_template('index.html', wishlist_url=WISHLIST_URL)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email').strip().lower()
    city = request.form.get('city')
    office = request.form.get('service')

    if not (name and email and city and office):
        return jsonify({"status": "error", "message": "All fields are required."})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT unsubscribed FROM subscribers WHERE email=? AND city=? AND office=?", (email, city, office))
    result = cursor.fetchone()

    if result:
        if result[0] == 1:
            cursor.execute("""
                UPDATE subscribers 
                SET unsubscribed = 0, name = ?, city = ?, office = ?
                WHERE email = ? AND city = ? AND office = ?
            """, (name, city, office, email, city, office))
            conn.commit()
            conn.close()
            send_confirmation_email(name, email, city, office, duplicate=False)
            return jsonify({
                "status": "resubscribed",
                "message": "You’ve been re-subscribed! We’ll notify you when there's a slot."
            })
        else:
            conn.close()
            send_confirmation_email(name, email, city, office, duplicate=True)
            return jsonify({
                "status": "duplicate",
                "message": "You're already on the list. We’ll notify you when there's a slot."
            })
    else:
        cursor.execute("""
            INSERT INTO subscribers (name, email, city, office) VALUES (?, ?, ?, ?)
        """, (name, email, city, office))
        conn.commit()
        conn.close()

        send_confirmation_email(name, email, city, office, duplicate=False)
        return jsonify({
            "status": "success",
            "message": "You’ve been subscribed! We’ll notify you when there's a slot."
        })

def send_confirmation_email(name, to_email, city, office, duplicate):
    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')

    unsubscribe_link = f"{DOMAIN}/unsubscribe?{urlencode({'email': to_email, 'city': city, 'office': office})}"

    if duplicate:
        subject = "You’re already subscribed"
        body = f"""Hi {name},

You're already on our notification list for {office} appointments in {city}.
We’ll notify you as soon as something opens up.

If you'd like to support the project, here’s the wishlist: {WISHLIST_URL}

To unsubscribe from this service, click here: {unsubscribe_link}

Cheers,  
Termin Checker Team
"""
    else:
        subject = "You're subscribed – We'll notify you"
        body = f"""Hi {name},

Thanks for signing up!

We’ve added you to the list for {office} appointments in {city}.
We’ll notify you when there’s an available slot.

You can support the project by checking out the wishlist: {WISHLIST_URL}

To unsubscribe from this service, click here: {unsubscribe_link}

Cheers,  
Termin Checker Team
"""

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
    except Exception as e:
        log(f"Email failed: {e}")

@app.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email', '').strip().lower()
    city = request.args.get('city', '').strip()
    office = request.args.get('office', '').strip()

    if not email or not city or not office:
        return "Missing parameters.", 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE subscribers SET unsubscribed = 1 WHERE email = ? AND city = ? AND office = ?
    """, (email, city, office))
    conn.commit()
    conn.close()

    return render_template("unsubscribe.html", city=city, office=office, wishlist_url=WISHLIST_URL)

def log(text):
    with open("test_log.txt", "a") as f:
        f.write(text + "\n")