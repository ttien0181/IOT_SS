# from raspberry pi
import smtplib
import requests
import time
import random
import datetime
from email.message import EmailMessage

#API Key
API_KEY = "QFXS1F2D77UCKYDC"
URl = "https://api.thingspeak.com/update"


def send_email():
    msg = EmailMessage()
    msg.set_content(f"High tempurature warning at {datetime.datetime.now()} !")

    msg['Subject'] = 'High tempurature warning from email!'
    msg['From'] = 'ttien0181@gmail.com'     # Gmail bạn dùng để gửi
    msg['To'] = 'tu.ha220055@sis.hust.edu.vn'       # Người nhận email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('ttien0181@gmail.com', 'xabd kwye qrej upct')  # App password tại đây
        smtp.send_message(msg)


def post_data(temprature, pressure):
    data = {
        "api_key" : API_KEY,
        "field1" : temprature,
        "field2" : pressure
    }
    response= requests.post(URl, data = data)
    print(f"Send: {response.status_code} - {response.text}")
    # response.text: số thứ tự bản ghi mà thingspeak đã lưu

    if temprature>15:
        send_email()
        quit()



while True:
    # nhiet do binh thuong: 25, ap suat binh thuong: 101325
    post_data(random.randint(0,30), round(random.uniform(101300,101330),2))
    time.sleep(16)
    
