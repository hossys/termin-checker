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
    email = request.form.get('email')
    city = request.form.get('city')

    if not (name and email and city):
        return redirect(url_for('index'))

    log(f"Submit route reached for {name}, {email}, {city}")

    # ایجاد فایل CSV اگه وجود نداره
    if not os.path.exists("subscribers.csv"):
        with open("subscribers.csv", "w") as f:
            f.write("name,email,city\n")

    # بررسی تکراری بودن ایمیل
    with open("subscribers.csv", "r") as f:
        if any(email in line for line in f.readlines()):
            return render_template('thanks.html', name=name, email=email, city=city, duplicate=True)

    # ذخیره اطلاعات
    with open("subscribers.csv", "a") as f:
        f.write(f"{name},{email},{city}\n")

    send_confirmation_email(name, email, city)
    return render_template('thanks.html', name=name, email=email, city=city, duplicate=False)

def send_confirmation_email(name, to_email, city):
    log(f"Sending confirmation to {name} ({to_email}) for city {city}")

    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASS')  

    subject = "You're subscribed – We'll notify you when an appointment opens"
    body = f"""
Hi {name},

Thank you for signing up!

We’ve successfully added your email to the notification list for available Einbürgerungstest appointments in {city}.

As soon as a slot becomes available, we will notify you right away.

In the meantime, feel free to relax — we’ll take care of the checking.

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