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

# gửi mail
def send_email(temperature):
    msg = EmailMessage()
    msg.set_content(f"High tempurature warning at {datetime.datetime.now()}: {temperature}°C")

    msg['Subject'] = 'High tempurature warning from email!'
    msg['From'] = 'ttien0181@gmail.com'     # Gmail bạn dùng để gửi
    msg['To'] = 'tu.ha220055@sis.hust.edu.vn'       # Người nhận email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('ttien0181@gmail.com', 'xabd kwye qrej upct')  # App password tại đây
        smtp.send_message(msg)

# đẩy dữ liệu lên thingspeak, nếu nhiệt độ cao thì gửi mail cảnh báo
def post_data(temperature, pressure):
    # tạo json
    data = {
        "api_key" : API_KEY,
        "field1" : temperature,
        "field2" : pressure
    }
    # đẩy lên thingspeak
    response= requests.post(URl, data = data)
    print(f"Send: {response.status_code} - {response.text}")
    # response.text: số thứ tự bản ghi mà thingspeak đã lưu

    # nếu nhiệt độ cao, gửi mail
    if temperature>15:
        send_email(temperature)
        quit()


# bắt đầu chạy
while True:
    # nhiet do binh thuong: 25, ap suat binh thuong: 101325
    post_data(random.randint(0,30), round(random.uniform(101300,101330),2))
    time.sleep(16)
    
