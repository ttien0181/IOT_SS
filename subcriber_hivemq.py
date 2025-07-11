import paho.mqtt.client as mqtt
import ssl

# === Thông tin HiveMQ Cloud ===
broker = "c55d02d9fd4d4b4f812d0e68dc8b3ef6.s1.eu.hivemq.cloud"
port = 8883
username = "tuhoang"
password = "Samsungiot02"
topic = "capstone/temperature"

# === Hàm gọi khi kết nối thành công ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Đã kết nối tới HiveMQ Cloud")
        client.subscribe(topic)  # Đăng ký nhận lệnh
    else:
        print("Lỗi kết nối, mã lỗi:", rc)

# === Hàm gọi khi  nhận được tin nhắn ===
def on_message(client, userdata, msg):
    print(f"Nhận lệnh dữ liệu trên topic '{msg.topic}': {msg.payload.decode()}") 
    # in dữ liệu nhận được

# === Cấu hình và chạy client MQTT ===
client = mqtt.Client()
client.username_pw_set(username, password)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

client.on_connect = on_connect # gán callback cho on_connect
client.on_message = on_message # gán callback cho on_message

client.connect(broker, port)
client.loop_forever()
