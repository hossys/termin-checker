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

    with open("test_log.txt", "a") as f:
        f.write(f"Submit route reached for {name}, {email}, {city}\n")

    print(f"Submit route reached for {name}, {email}, {city}")

    if name and email and city:
        send_confirmation_email(name, email, city)
        return render_template('thanks.html', name=name, email=email, city=city)

    return redirect(url_for('index'))

def send_confirmation_email(name, to_email, city):
    with open("test_log.txt", "a") as f:
        f.write(f"Sending confirmation to {name} ({to_email}) for city {city}\n")

    print(f"Sending confirmation to {name} ({to_email}) for city {city}")

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
        with open("test_log.txt", "a") as f:
            f.write("Email sent successfully\n")
    except Exception as e:
        with open("test_log.txt", "a") as f:
            f.write(f"Error sending email: {str(e)}\n")