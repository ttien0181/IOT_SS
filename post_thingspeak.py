# from raspberry pi
import smtplib
import requests
import time
import json
import google.auth
import random
import datetime
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2 import service_account

def send_noti(temperature):
    print("bắt đầu gửi noti")
    # Tải service account credentials
    creds = service_account.Credentials.from_service_account_file(
        "service-account.json", scopes=["https://www.googleapis.com/auth/firebase.messaging"]
    )

    # Lấy access token, refresh nếu hết hạn
    creds.refresh(Request()) 
    access_token = creds.token

    # Gửi đến topic 'family'
    project_id = "iot-02-c0122"  # id trên console firebase 
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send" # url yêu cầu gửi noti

    headers = {
        "Authorization": f"Bearer {access_token}", # token
        "Content-Type": "application/json; UTF-8", # định dạng json
    }

    message = {
        "message": {
            "topic": "livingroom", # topic 
            "notification": { 
                "title": "High temperature warning! ",
                "body": f"The temperature is {temperature}  C"
            }
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(message))

    print(f"đã gửi noti: return {response.status_code} - {response.text}")
    print("đã gửi xong noti")






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
    print(f"đã gửi xong mail cho nhiệt độ {temperature} độ C")

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
    print(f"đã gửi request: {response.status_code} - {response.text} cho {temperature} độ C")
    # response.text: số thứ tự bản ghi mà thingspeak đã lưu

    # nếu nhiệt độ cao, gửi mail
    if temperature>1:
        print("nh độ cao, bắt đầu gửi canhr baos")
        send_email(temperature)
        send_noti(temperature)
        quit()


# bắt đầu chạy
while True:
    # nhiet do binh thuong: 25, ap suat binh thuong: 101325
    post_data(random.randint(0,30), round(random.uniform(101300,101330),2))
    time.sleep(16)
    
