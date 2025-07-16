import paho.mqtt.client as mqtt
import json
import time
import random

# ========== Thông tin cấu hình ==========
THINGSBOARD_HOST = 'thingsboard.cloud'
ACCESS_TOKEN = 'KugsFcIx45iVkWiT95we'  # <-- thay bằng token thiết bị của bạn

# ========== Hàm xử lý kết nối ==========
def on_connect(client, userdata, flags, rc):
    print("✅ Connected with result code " + str(rc))

# ========== Tạo client MQTT ==========
client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)
client.on_connect = on_connect

client.connect(THINGSBOARD_HOST, 1883, 60)
client.loop_start()

# ========== Gửi dữ liệu định kỳ ==========
try:
    while True:
        # Tạo dữ liệu giả lập (thay bằng cảm biến thật nếu cần)
        temperature = round(random.uniform(20, 40), 2)
        humidity = round(random.uniform(30, 90), 2)

        payload = {
            "temperature": temperature,
            "humidity": humidity
        }

        # Gửi dữ liệu lên ThingsBoard
        client.publish("v1/devices/me/telemetry", json.dumps(payload), qos=1)
        print("📤 Sent:", payload)

        time.sleep(5)

except KeyboardInterrupt:
    print("🔌 Stopped by user")
    client.loop_stop()
    client.disconnect()
