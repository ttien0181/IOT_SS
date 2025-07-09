import smtplib
from email.message import EmailMessage

def gui_email():
    msg = EmailMessage()
    msg.set_content("Bạn quên uống thuốc sáng nay!")
    msg["Subject"] = "Cảnh báo quên uống thuốc"
    msg["From"] = "your.email@gmail.com"
    msg["To"] = "nguoinha@example.com"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("your.email@gmail.com", "YOUR_APP_PASSWORD")
        smtp.send_message(msg)