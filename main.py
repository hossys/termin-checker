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
    city = request.form.get('city').strip().lower()
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
    resubscribe_link = f"{DOMAIN}/resubscribe?{urlencode({'email': to_email, 'city': city, 'office': office, 'name': name})}"

    if duplicate:
        subject = "You're already subscribed – Termin Notify"
        body = f"""
        <p>Hi {name},</p>

        <p>You're already on our list for <strong>{office}</strong> appointments in <strong>{city}</strong>. 📝<br>
        We'll keep an eye out and let you know when a spot opens!</p>

        <p>If you'd like to make our day, check out our <a href="{WISHLIST_URL}">wishlist</a>. 🎁</p>

        <p>Want to unsubscribe? No hard feelings — just <a href="{unsubscribe_link}">click here</a>.</p>

        <p>Cheers,<br>Termin Checker Team</p>
        """
    else:
        subject = "You're on the list! 🎉 – Termin Notify"
        body = f"""
        <p>Hi {name},</p>

        <p>Thanks for signing up! You're now subscribed to notifications for <strong>{office}</strong> appointments in <strong>{city}</strong>. 📬<br>
        We'll ping you when something pops up!</p>

        <p>You can support us by checking out our <a href="{WISHLIST_URL}">wishlist</a>. 🙌</p>

        <p>Changed your mind? You can <a href="{unsubscribe_link}">unsubscribe here</a>.</p>

        <p>Cheers,<br>Termin Checker Team</p>
        """

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

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

    return render_template("unsubscribe.html", city=city, office=office, email=email, wishlist_url=WISHLIST_URL)

@app.route('/resubscribe')
def resubscribe():
    email = request.args.get('email', '').strip().lower()
    name = request.args.get('name', '').strip()
    city = request.args.get('city', '').strip()
    office = request.args.get('office', '').strip()

    if not email or not city or not office:
        return "Missing parameters.", 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not name:
        cursor.execute("""
            SELECT name FROM subscribers WHERE email = ? AND city = ? AND office = ?
        """, (email, city, office))
        row = cursor.fetchone()
        name = row[0] if row else "Friend"

    cursor.execute("""
        UPDATE subscribers 
        SET unsubscribed = 0, name = ?
        WHERE email = ? AND city = ? AND office = ?
    """, (name, email, city, office))
    conn.commit()
    conn.close()

    send_confirmation_email(name, email, city, office, duplicate=False)
    return render_template("resubscribed.html", city=city, office=office, email=email, wishlist_url=WISHLIST_URL)

def log(text):
    with open("test_log.txt", "a") as f:
        f.write(text + "\n")