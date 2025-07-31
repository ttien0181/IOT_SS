# mqtt_subscriber.py
import paho.mqtt.client as mqtt
import pymysql
from db import get_connection
from app import push_data_to_client  # 👈 Import từ app.py

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/capstone/dht11"

def save_to_db(temp, humid):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dht_data (temp, humid) VALUES (%s, %s)", (temp, humid))
        conn.commit()
    conn.close()

# Gọi khi nhận được message từ MQTT
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"[MQTT] Received: {payload}")

    try:
        temp, humid = map(float, payload.split(","))
        save_to_db(temp, humid)

        # 👉 Gửi dữ liệu tới client qua WebSocket (realtime)
        push_data_to_client(temp, humid)

    except Exception as e:
        print(f"[ERROR] {e}")

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT)
client.subscribe(TOPIC)

print("[MQTT] Listening for data...")
client.loop_forever()
