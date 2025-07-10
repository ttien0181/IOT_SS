import paho.mqtt.client as mqtt
import ssl
import time
import random
import json

# === Cấu hình kết nối HiveMQ Cloud ===
broker = "c55d02d9fd4d4b4f812d0e68dc8b3ef6.s1.eu.hivemq.cloud"  # Địa chỉ broker bạn nhận được
port = 8883                                                   # Port TLS bắt buộc
username = "tuhoang"                                         # Username bạn tạo trong HiveMQ
password = "Samsungiot02"
topic = "capstone/temperature"                                # Password tương ứng

# === Callback khi kết nối thành công ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Kết nối thành công tới HiveMQ Cloud")
    else:
        print("Kết nối thất bại, mã lỗi:", rc)

# === Tạo client MQTT và cấu hình bảo mật ===
client = mqtt.Client()
client.username_pw_set(username, password)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)  # Bắt buộc TLS với HiveMQ Cloud

client.on_connect = on_connect # gán callback cho on_connect
client.connect(broker, port) # kết nối tới broker

client.loop_start()  
# khởi động luồng nền chạy vòng lặp xử lý sự kiện MQTT
# VD:   Kết nối lại nếu bị mất, 
#       Gửi keep-alive ping, 
#       Nhận gói tin từ broker (subscribe),
#       Gọi callback (như on_connect, on_message, ... )


# === Gửi dữ liệu giả lập mỗi 10 giây ===
try:
    while True:
        temperature = round(random.uniform(25.0, 35.0), 2)  # Sinh số ngẫu nhiên từ 25.00 đến 35.00

        data = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"), # thời gian hiện tại VD: "2025-07-10 16:46:00"
            "temperature": round(random.uniform(25.0, 30.0), 2) # nhiệt độ ngẫu nhiên
        }
        payload = json.dumps(data) # chuyển thành json
        result = client.publish(topic, payload) # publish lên topic capstone/temperature
        status = result[0]
        if status == 0:
            print(f"Đã gửi {payload}°C lên topic `{topic}`")
        else:
            print("Gửi thất bại")

        time.sleep(10)  # Chờ 10 giây
except KeyboardInterrupt:
    print("Dừng chương trình")
    client.loop_stop()
