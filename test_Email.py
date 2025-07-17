import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

sender_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASS")
to_email = "hsnsbrnsn@gmail.com"  # ← ایمیل مقصد را اینجا بذار

# خط اصلاح‌شده اینه 👇
msg = MIMEText("Test email from Terminotify", "plain", "utf-8")

msg["Subject"] = "Test Email"
msg["From"] = sender_email
msg["To"] = to_email

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)
    print("✅ Email sent")
except Exception as e:
    print(f"❌ Error: {e}")
