from flask import Flask, render_template, request, redirect, url_for
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    email = request.form.get('email')
    city = request.form.get('city')

    if email and city:
        send_confirmation_email(email, city)
        return render_template('thanks.html', email=email, city=city)

    return redirect(url_for('index'))

def send_confirmation_email(to_email, city):
    print(f"Sending confirmation to {to_email} for city {city}")
    sender_email = 'terminnotify@gmail.com'
    sender_password = 'cytmec-miRhov-7jutmy'  

    subject = "You're subscribed – We'll notify you when an appointment opens"
    body = f"""
    Hi there,

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
    except Exception as e:
        print(f"Error sending email: {e}")