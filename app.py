from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email').strip().lower()
    city = request.form.get('city')
    office = request.form.get('office')

    if not (name and email and city and office):
        return redirect(url_for('index'))

    log(f"Submit route reached for {name}, {email}, {city}, {office}")

    # اگه فایل نبود، بساز
    if not os.path.exists("subscribers.csv"):
        with open("subscribers.csv", "w") as f:
            f.write("name,email,city,office\n")

    is_duplicate = False
    with open("subscribers.csv", "r") as f:
        for line in f.readlines():
            if f"{email},{city},{office}" in line:
                is_duplicate = True
                break

    if is_duplicate:
        send_confirmation_email(name, email, city, office, duplicate=True)
        return render_template('thanks.html', name=name, email=email, city=city, office=office, duplicate=True)

    # ذخیره اطلاعات
    with open("subscribers.csv", "a") as f:
        f.write(f"{name},{email},{city},{office}\n")

    send_confirmation_email(name, email, city, office, duplicate=False)
    return render_template('thanks.html', name=name, email=email, city=city, office=office, duplicate=False)

def send_confirmation_email(name, to_email, city, office, duplicate):
    log(f"Sending email to {name} ({to_email}) for city {city}, office {office}, duplicate={duplicate}")

    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')

    if duplicate:
        subject = "You’re already subscribed"
        body = f"""
Hi {name},

You're already on our notification list for **{office}** appointments in {city}.

No need to register again — we will notify you as soon as a slot opens.

Cheers,  
Termin Checker Team
"""
    else:
        subject = "You're subscribed – We'll notify you when an appointment opens"
        body = f"""
Hi {name},

Thank you for signing up!

We’ve successfully added your email to the notification list for **{office}** appointments in {city}.

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