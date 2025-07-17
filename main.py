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
            language TEXT DEFAULT 'en',
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
    language = request.form.get('language', 'en')
    name = request.form.get('name')
    email = request.form.get('email').strip().lower()
    city = request.form.get('city').strip().lower()
    office = request.form.get('service')

    if not (name and email and city and office):
        return jsonify({"status": "error", "message": "All fields are required."})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT unsubscribed FROM subscribers WHERE email=? AND city=? AND office=?
    """, (email, city, office))
    result = cursor.fetchone()

    if result:
        cursor.execute("""
            UPDATE subscribers 
            SET unsubscribed = 0, name = ?, city = ?, office = ?, language = ?
            WHERE email = ? AND city = ? AND office = ?
        """, (name, city, office, language, email, city, office))
        conn.commit()
        conn.close()
        send_confirmation_email(name, email, city, office, language, duplicate=(result[0] == 0))
        return jsonify({
            "status": "resubscribed" if result[0] == 1 else "duplicate",
            "message": "Updated successfully."
        })
    else:
        cursor.execute("""
            INSERT INTO subscribers (name, email, city, office, language) VALUES (?, ?, ?, ?, ?)
        """, (name, email, city, office, language))
        conn.commit()
        conn.close()
        send_confirmation_email(name, email, city, office, language, duplicate=False)
        return jsonify({
            "status": "success",
            "message": "You’ve been subscribed! We’ll notify you when there's a slot."
        })

def send_confirmation_email(name, to_email, city, office, language, duplicate):
    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')

    unsubscribe_link = f"{DOMAIN}/unsubscribe?{urlencode({'email': to_email, 'city': city, 'office': office})}"
    resubscribe_link = f"{DOMAIN}/resubscribe?{urlencode({'email': to_email, 'city': city, 'office': office, 'name': name})}"

    subjects = {
        "en": {
            "duplicate": "You're already subscribed – Termin Notify",
            "new": "You're on the list! 🎉 – Termin Notify"
        },
        "fa": {
            "duplicate": "شما قبلاً عضو شده‌اید – ترمین نوتیفای",
            "new": "شما در لیست هستید! 🎉 – ترمین نوتیفای"
        },
        "de": {
            "duplicate": "Du bist bereits angemeldet – Termin Notify",
            "new": "Du stehst auf der Liste! 🎉 – Termin Notify"
        }
        # سایر زبان‌ها در صورت نیاز اضافه شود
    }

    bodies = {
        "en": {
            "duplicate": f"""
                <p>Hi {name},</p>
                <p>You're already on our list for <strong>{office}</strong> appointments in <strong>{city}</strong>. 📝</p>
                <p>Check out our <a href="{WISHLIST_URL}">wishlist</a>. 🎁</p>
                <p><a href="{unsubscribe_link}">Unsubscribe</a> anytime.</p>
                <p>Cheers,<br>Termin Notify</p>
            """,
            "new": f"""
                <p>Hi {name},</p>
                <p>You’re subscribed to notifications for <strong>{office}</strong> in <strong>{city}</strong>. 📬</p>
                <p><a href="{WISHLIST_URL}">Support us</a> if you like.</p>
                <p>To unsubscribe, <a href="{unsubscribe_link}">click here</a>.</p>
                <p>Cheers,<br>Termin Notify</p>
            """
        },
        "fa": {
            "duplicate": f"""
                <p>سلام {name}،</p>
                <p>شما قبلاً برای نوتیفیکیشن‌های <strong>{office}</strong> در <strong>{city}</strong> ثبت‌نام کرده‌اید. 📝</p>
                <p>از <a href="{WISHLIST_URL}">لیست آرزوهای ما</a> دیدن کنید. 🎁</p>
                <p><a href="{unsubscribe_link}">لغو عضویت</a></p>
                <p>با احترام،<br>تیم ترمین نوتیفای</p>
            """,
            "new": f"""
                <p>سلام {name}،</p>
                <p>ثبت‌نام شما برای نوتیفیکیشن‌های <strong>{office}</strong> در <strong>{city}</strong> موفقیت‌آمیز بود. 📬</p>
                <p><a href="{WISHLIST_URL}">ما را حمایت کنید</a> اگر خواستید.</p>
                <p><a href="{unsubscribe_link}">لغو عضویت</a></p>
                <p>با احترام،<br>تیم ترمین نوتیفای</p>
            """
        },
        "de": {
            "duplicate": f"""
                <p>Hallo {name},</p>
                <p>Du bist bereits für <strong>{office}</strong> in <strong>{city}</strong> registriert. 📝</p>
                <p>Schaue auf unsere <a href="{WISHLIST_URL}">Wunschliste</a>. 🎁</p>
                <p><a href="{unsubscribe_link}">Abmelden</a></p>
                <p>Grüße,<br>Termin Notify Team</p>
            """,
            "new": f"""
                <p>Hallo {name},</p>
                <p>Du bist jetzt für <strong>{office}</strong> in <strong>{city}</strong> registriert. 📬</p>
                <p><a href="{WISHLIST_URL}">Unterstütze uns</a>, wenn du möchtest.</p>
                <p><a href="{unsubscribe_link}">Abmelden</a></p>
                <p>Grüße,<br>Termin Notify Team</p>
            """
        }
    }

    lang = language if language in subjects else "en"
    status_key = "duplicate" if duplicate else "new"
    subject = subjects[lang][status_key]
    body = bodies[lang][status_key]

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

    send_confirmation_email(name, email, city, office, "en", duplicate=False)
    return render_template("resubscribed.html", city=city, office=office, email=email, wishlist_url=WISHLIST_URL)

def log(text):
    with open("test_log.txt", "a") as f:
        f.write(text + "\n")