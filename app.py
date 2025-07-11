from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

app = Flask(__name__)
DB_PATH = "subscribers.db"

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
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email').strip().lower()
    city = request.form.get('city')
    office = request.form.get('service')

    if not (name and email and city and office):
        return redirect(url_for('index'))

    log(f"Submit route reached for {name}, {email}, {city}, {office}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM subscribers WHERE email=? AND city=? AND office=?
    """, (email, city, office))
    result = cursor.fetchone()
    is_duplicate = result is not None

    if not is_duplicate:
        cursor.execute("""
            INSERT INTO subscribers (name, email, city, office)
            VALUES (?, ?, ?, ?)
        """, (name, email, city, office))
        conn.commit()

    conn.close()

    send_confirmation_email(name, email, city, office, duplicate=is_duplicate)
    return render_template('thanks.html', name=name, email=email, city=city, office=office, duplicate=is_duplicate)

def send_confirmation_email(name, to_email, city, office, duplicate):
    log(f"Sending email to {name} ({to_email}) for city {city}, office {office}, duplicate={duplicate}")

    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')

    if duplicate:
        subject = "You’re already subscribed"
        body = f"""
Hi {name},

You're already on our notification list for {office} appointments in {city}.

No need to register again — we will notify you as soon as a slot opens.

Cheers,  
Termin Checker Team
"""
    else:
        subject = "You're subscribed – We'll notify you when an appointment opens"
        body = f"""
Hi {name},

Thank you for signing up!

We’ve successfully added your email to the notification list for {office} appointments in {city}.

As soon as a slot becomes available, we will notify you right away.

In the meantime, relax — we’ll handle the checking.

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
        log(f"Error sending email: {str(e)}")

def log(text):
    with open("test_log.txt", "a") as f:
        f.write(text + "\n")