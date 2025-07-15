from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

app = Flask(__name__)
DB_PATH = "subscribers.db"
WISHLIST_URL = "https://www.amazon.de/hz/wishlist/ls/214QLWQZ9B9DR?ref_=wl_share"

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            city TEXT NOT NULL,
            office TEXT NOT NULL
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

    log(f"Form submitted: {name}, {email}, {city}, {office}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM subscribers WHERE email=? AND city=? AND office=?", (email, city, office))
    result = cursor.fetchone()
    is_duplicate = result is not None

    if not is_duplicate:
        cursor.execute("INSERT INTO subscribers (name, email, city, office) VALUES (?, ?, ?, ?)", (name, email, city, office))
        conn.commit()

    conn.close()

    send_confirmation_email(name, email, city, office, duplicate=is_duplicate)

    return jsonify({
        "status": "duplicate" if is_duplicate else "success",
        "message": "You're already on the list. We’ll notify you when there's a slot." if is_duplicate else "You’ve been subscribed! We’ll notify you when there's a slot."
    })

def send_confirmation_email(name, to_email, city, office, duplicate):
    log(f"Sending email to {to_email} | duplicate: {duplicate}")

    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')

    if duplicate:
        subject = "You’re already subscribed"
        body = f"""Hi {name},

You're already on our notification list for {office} appointments in {city}.
We’ll notify you as soon as something opens up.

If you'd like to support the project, here’s the wishlist: {WISHLIST_URL}

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
        log("Email sent successfully")
    except Exception as e:
        log(f"Email failed: {e}")

def log(text):
    with open("test_log.txt", "a") as f:
        f.write(text + "\n")