import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    data = json.loads(payload)
    temp = data['temperature']
    hr = data['heartRate']
    print(f"Nhiệt độ: {temp}°C, Nhịp tim: {hr} bpm")

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.subscribe("patient/data")
client.on_message = on_message

print("Đang lắng nghe dữ liệu từ ESP32...")
client.loop_forever()
