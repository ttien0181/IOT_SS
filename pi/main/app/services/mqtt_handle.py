import paho.mqtt.client as mqtt
import queue
import threading
import time
from datetime import datetime
from app.database.connection import get_connection

# Cấu hình MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
# topic: bachmai/A1/1/101/TEMP101/temperature
MQTT_TOPICS = [("bachmai/#", 0)]

# Biến kiểm soát thời gian ghi CSDL
last_db_write_time = 0
DB_WRITE_INTERVAL = 5  # 5 giây để test (có thể đổi thành 300)

# Hàng đợi để xử lý dữ liệu ghi vào DB
data_queue = queue.Queue()

# Biến toàn cục để lưu instance của SocketIO
_socketio_instance = None

# ------------------------
# Xử lý chuỗi topic
def parse_topic(topic):
    parts = topic.split("/")
    if len(parts) >= 6:
        _, building, floor, room, sensor_id, data_type = parts
        return building, floor, room, sensor_id, data_type
    else:
        return None, None, None, None, None

# ------------------------
# Thread ghi DB
def db_worker():
    while True:
        try:
            sensor_id, value, data_type = data_queue.get()
            conn = get_connection()
            with conn.cursor() as cur:
                sql = """
                    INSERT INTO sensor_data (sensor_id, data_value, data_type, timestamp)
                    VALUES (%s, %s, %s, NOW())
                """
                cur.execute(sql, (sensor_id, value, data_type))
                conn.commit()
                print(f"[DB Worker] ✅ Lưu {data_type}={value} từ {sensor_id} vào DB lúc {datetime.now()}")
        except Exception as e:
            print(f"[DB Worker] ❌ Lỗi: {e}")
        finally:
            if conn:
                conn.close()
            data_queue.task_done()

# ------------------------
# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] ✅ Kết nối thành công tới Broker")
        for topic, qos in MQTT_TOPICS:
            client.subscribe(topic, qos)
            print(f"[MQTT] Đăng ký topic: {topic}")
    else:
        print(f"[MQTT] ❌ Kết nối thất bại, mã lỗi: {rc}")

def on_message(client, userdata, msg):
    global last_db_write_time
    try:
        payload = msg.payload.decode()
        building, floor, room, sensor_id, data_type = parse_topic(msg.topic)

        if not all([building, floor, room, sensor_id, data_type]):
            print(f"[MQTT] Bỏ qua topic không hợp lệ: {msg.topic}")
            return

        print(f"[MQTT] 📩 Nhận dữ liệu: {building}/{floor}/{room}/{data_type} = {payload}")

        # 1️⃣ Đẩy dữ liệu ngay qua Socket.IO
        if _socketio_instance:
            _socketio_instance.emit("sensor_update", {data_type: payload})
            print("[SocketIO] ✅ Đã phát dữ liệu tới client")
        else:
            print("[SocketIO] ⚠️ Chưa có instance SocketIO")

        # 2️⃣ Thêm vào queue để ghi DB (theo chu kỳ)
        current_time = time.time()
        if current_time - last_db_write_time >= DB_WRITE_INTERVAL:
            data_queue.put((sensor_id, payload, data_type))
            last_db_write_time = current_time
            print("[DB] ⏳ Thêm dữ liệu vào hàng đợi")
    except ValueError:
        print(f"[MQTT] ❌ Lỗi chuyển đổi payload: {msg.payload.decode()}")
    except Exception as e:
        print(f"[MQTT] ❌ Lỗi xử lý tin nhắn: {e}")

# ------------------------
# Khởi động MQTT listener
def start_mqtt_listener(socketio_instance):
    global _socketio_instance
    _socketio_instance = socketio_instance

    threading.Thread(target=db_worker, daemon=True).start()
    print("[MQTT Handler] ✅ DB worker thread đã khởi động")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"[MQTT Handler] 🔌 Kết nối tới {MQTT_BROKER}:{MQTT_PORT}")
        client.loop_forever()
    except Exception as e:
        print(f"[MQTT Handler] ❌ Lỗi kết nối MQTT: {e}")
