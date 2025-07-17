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
    try:
        language = request.form.get('language', 'en')
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        city = request.form.get('city', '').strip().lower()
        office = request.form.get('service', '').strip()

        print("▶ Received form data:", name, email, city, office, language)

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

            print("▶ Re-subscribing existing user...")

            try:
                send_confirmation_email(name, email, city, office, language, duplicate=(result[0] == 0))
            except Exception as e:
                log(f"Email failed (duplicate): {e}")
                return jsonify({"status": "error", "message": "Email could not be sent."})

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

            print("▶ Subscribing new user...")

            try:
                send_confirmation_email(name, email, city, office, language, duplicate=False)
            except Exception as e:
                log(f"Email failed (new): {e}")
                return jsonify({"status": "error", "message": "Email could not be sent."})

            return jsonify({
                "status": "success",
                "message": "You’ve been subscribed! We’ll notify you when there's a slot."
            })

    except Exception as e:
        log(f"Global submit error: {e}")
        return jsonify({"status": "error", "message": "Something went wrong on the server."})

email_translations = {
    'en': {
        'subject_new': "You're on the list! 🎉 – Termin Notify",
        'subject_duplicate': "You're already subscribed – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Hi {name},</p>
            <p>Thanks for signing up! You're now subscribed to notifications for <strong>{office}</strong> appointments in <strong>{city}</strong>. 📬<br>
            We'll ping you when something pops up!</p>
            <p>You can support us by checking out our <a href="{wishlist}">wishlist</a>. 🙌</p>
            <p>Changed your mind? You can <a href="{unsubscribe}">unsubscribe here</a>.</p>
            <p>Cheers,<br>Termin Checker Team</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Hi {name},</p>
            <p>You're already on our list for <strong>{office}</strong> appointments in <strong>{city}</strong>. 📝<br>
            We'll keep an eye out and let you know when a spot opens!</p>
            <p>If you'd like to make our day, check out our <a href="{wishlist}">wishlist</a>. 🎁</p>
            <p>Want to unsubscribe? No hard feelings — just <a href="{unsubscribe}">click here</a>.</p>
            <p>Cheers,<br>Termin Checker Team</p>
        """
    },
    'fa': {
        'subject_new': "شما در لیست هستید! 🎉 – ترمین نوتیفای",
        'subject_duplicate': "شما قبلاً عضو شده‌اید – ترمین نوتیفای",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>{name} عزیز،</p>
            <p>ممنون که ثبت‌نام کردید! حالا شما در لیست اطلاع‌رسانی وقت‌های <strong>{office}</strong> در <strong>{city}</strong> هستید. 📬<br>
            به‌محض باز شدن وقت جدید بهتون خبر می‌دیم.</p>
            <p>می‌تونید از ما حمایت کنید با دیدن <a href="{wishlist}">لیست آرزوها</a> 🙌</p>
            <p>نظرتون عوض شده؟ <a href="{unsubscribe}">لغو عضویت</a> رو بزنید.</p>
            <p>با احترام،<br>تیم ترمین نوتیفای</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>{name} عزیز،</p>
            <p>شما قبلاً برای وقت <strong>{office}</strong> در <strong>{city}</strong> عضو شده‌اید. 📝<br>
            ما پیگیر هستیم و به‌محض باز شدن وقت بهتون اطلاع می‌دیم.</p>
            <p>اگه دوست داشتید خوشحالمون کنید، <a href="{wishlist}">لیست آرزوها</a> ما اینجاست. 🎁</p>
            <p>برای لغو عضویت، <a href="{unsubscribe}">اینجا کلیک کنید</a>.</p>
            <p>با احترام،<br>تیم ترمین نوتیفای</p>
        """
    },
    'de': {
        'subject_new': "Du stehst auf der Liste! 🎉 – Termin Notify",
        'subject_duplicate': "Du bist bereits abonniert – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Hallo {name},</p>
            <p>Danke für deine Anmeldung! Du bekommst Benachrichtigungen für <strong>{office}</strong>-Termine in <strong>{city}</strong>. 📬<br>
            Wir informieren dich, sobald ein Termin frei wird!</p>
            <p>Unterstütze uns mit einem Blick auf unsere <a href="{wishlist}">Wunschliste</a>. 🙌</p>
            <p>Möchtest du dich abmelden? <a href="{unsubscribe}">Hier klicken</a>.</p>
            <p>Viele Grüße,<br>Termin Notify Team</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Hallo {name},</p>
            <p>Du bist bereits auf der Liste für <strong>{office}</strong>-Termine in <strong>{city}</strong>. 📝<br>
            Wir benachrichtigen dich, sobald ein Termin frei ist.</p>
            <p>Mach uns eine Freude und schau auf unsere <a href="{wishlist}">Wunschliste</a>. 🎁</p>
            <p>Abmelden? <a href="{unsubscribe}">Hier klicken</a>.</p>
            <p>Viele Grüße,<br>Termin Notify Team</p>
        """
    },
    'tr': {
        'subject_new': "Listeye eklendiniz! 🎉 – Termin Notify",
        'subject_duplicate': "Zaten abonesiniz – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Merhaba {name},</p>
            <p>Kayıt olduğunuz için teşekkürler! Artık <strong>{city}</strong> şehrindeki <strong>{office}</strong> randevuları için bilgilendirileceksiniz. 📬</p>
            <p>Destek olmak isterseniz <a href="{wishlist}">dilek listemize</a> göz atabilirsiniz. 🙌</p>
            <p>Vazgeçtiniz mi? <a href="{unsubscribe}">Buradan ayrılabilirsiniz</a>.</p>
            <p>Sevgiler,<br>Termin Notify Ekibi</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Merhaba {name},</p>
            <p>Zaten <strong>{city}</strong> şehrindeki <strong>{office}</strong> randevuları için kayıtlısınız. 📝<br>
            Bir yer açıldığında sizi bilgilendireceğiz.</p>
            <p>İsterseniz <a href="{wishlist}">dilek listemize</a> göz atabilirsiniz. 🎁</p>
            <p>Aboneliği sonlandırmak için <a href="{unsubscribe}">buraya tıklayın</a>.</p>
            <p>Sevgiler,<br>Termin Notify Ekibi</p>
        """
    },
    'uk': {
        'subject_new': "Вас додано до списку! 🎉 – Termin Notify",
        'subject_duplicate': "Ви вже підписані – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Привіт {name},</p>
            <p>Дякуємо за підписку! Тепер ви отримуватимете сповіщення про <strong>{office}</strong> у <strong>{city}</strong>. 📬</p>
            <p>Підтримайте нас, переглянувши <a href="{wishlist}">наш список побажань</a>. 🙌</p>
            <p>Передумали? <a href="{unsubscribe}">Скасувати підписку</a>.</p>
            <p>З повагою,<br>Команда Termin Notify</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Привіт {name},</p>
            <p>Ви вже підписані на сповіщення про <strong>{office}</strong> у <strong>{city}</strong>. 📝</p>
            <p>Ми повідомимо, коли з’явиться новий час.</p>
            <p><a href="{wishlist}">Список побажань</a> для підтримки. 🎁</p>
            <p><a href="{unsubscribe}">Відписатися</a></p>
            <p>З повагою,<br>Команда Termin Notify</p>
        """
    },
    'ar': {
        'subject_new': "تمت إضافتك للقائمة! 🎉 – Termin Notify",
        'subject_duplicate': "أنت مشترك بالفعل – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>مرحباً {name}،</p>
            <p>شكراً لتسجيلك! سيتم إعلامك بمواعيد <strong>{office}</strong> في <strong>{city}</strong>. 📬</p>
            <p>ادعمنا من خلال <a href="{wishlist}">قائمة الأمنيات</a>. 🙌</p>
            <p>هل غيّرت رأيك؟ <a href="{unsubscribe}">اضغط هنا لإلغاء الاشتراك</a>.</p>
            <p>مع تحياتنا،<br>فريق Termin Notify</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>مرحباً {name}،</p>
            <p>أنت مشترك بالفعل في إشعارات <strong>{office}</strong> في <strong>{city}</strong>. 📝</p>
            <p>سنعلمك عند توفر موعد جديد.</p>
            <p><a href="{wishlist}">قائمة الأمنيات</a> إن أحببت أن تدعمنا. 🎁</p>
            <p><a href="{unsubscribe}">إلغاء الاشتراك</a></p>
            <p>مع تحياتنا،<br>فريق Termin Notify</p>
        """
    }
}

def send_confirmation_email(name, to_email, city, office, language=None, duplicate=False):
    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')

    if not sender_email or not sender_password:
        raise Exception("Missing email credentials in environment variables.")

    if not language:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM subscribers WHERE email = ? AND city = ? AND office = ?", (to_email, city, office))
            result = cursor.fetchone()
            conn.close()
            language = result[0] if result and result[0] in email_translations else 'en'
        except Exception as e:
            log(f"Failed to get language from DB: {e}")
            language = 'en'

    unsubscribe_link = f"{DOMAIN}/unsubscribe?{urlencode({'email': to_email, 'city': city, 'office': office})}"
    t = email_translations.get(language, email_translations['en'])

    subject = t['subject_duplicate'] if duplicate else t['subject_new']
    body = t['body_duplicate'](name, city, office, WISHLIST_URL, unsubscribe_link) if duplicate else t['body_new'](name, city, office, WISHLIST_URL, unsubscribe_link)

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = subject
    if language in ["fa", "ar"]:
        body = f'<div dir="rtl" style="text-align: right;">{body}</div>'
    else:
        body = f'<div dir="ltr">{body}</div>'

    message.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        log(f"📧 Confirmation email sent to {to_email}")
    except Exception as e:
        log(f"❌ Failed to send confirmation email to {to_email}: {str(e)}")
        raise

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


    cursor.execute("""
        SELECT name, language FROM subscribers WHERE email = ? AND city = ? AND office = ?
    """, (email, city, office))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "User not found.", 404

    name_from_db = row[0] if row[0] else "Friend"
    language = row[1] if row[1] else "en"

    name = name or name_from_db

    cursor.execute("""
        UPDATE subscribers 
        SET unsubscribed = 0, name = ?
        WHERE email = ? AND city = ? AND office = ?
    """, (name, email, city, office))
    conn.commit()
    conn.close()

    send_confirmation_email(name, email, city, office, language, duplicate=False)

    return render_template("resubscribed.html", city=city, office=office, email=email, wishlist_url=WISHLIST_URL, language=language)
def log(text):
    with open("test_log.txt", "a") as f:
        f.write(text + "\n")