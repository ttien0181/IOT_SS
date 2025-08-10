import paho.mqtt.client as mqtt
import queue
import json
import threading
import time
from datetime import datetime
from app.database.connection import get_mobiusdb_connection

# Cấu hình MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
# topic: A1/1/101/TEMP101/temperature
MQTT_TOPICS = [("#", 0)]

# Biến kiểm soát thời gian ghi CSDL
last_db_write_time = 0
DB_WRITE_INTERVAL = 5  # 5 giây để test (có thể đổi thành 300)

# Hàng đợi để xử lý dữ liệu ghi vào DB
data_queue = queue.Queue()

# Biến toàn cục để lưu instance của SocketIO
_socketio_instance = None

# Xử lý chuỗi topic
def parse_topic(topic):
    parts = topic.split("/")
    if len(parts) >=4:
        building, floor, room, data_type = parts
        return building, floor, room,  data_type
    else:
        return None, None, None, None



# Thread ghi DB
def db_worker():
    while True:
        try:
            sensor_id, value, data_type = data_queue.get()
            conn = get_mobiusdb_connection()
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


# MQTT Callbacks khi bắt đầu kết nối
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] ✅ Kết nối thành công tới Broker")
        for topic, qos in MQTT_TOPICS:
            client.subscribe(topic, qos)
            print(f"[MQTT] Đăng ký topic: {topic}")
    else:
        print(f"[MQTT] ❌ Kết nối thất bại, mã lỗi: {rc}")


# khi nhận message MQTT
def on_message(client, userdata, msg):
    global last_db_write_time
    try:
        # xử lý topic
        building, floor, room, data_type = parse_topic(msg.topic)

        # xử lý payload
        payload_str = msg.payload.decode()
        payload_data = json.loads(payload_str)
        value = payload_data.get("value") # lấy giá trị
        unit = payload_data.get("unit") # lấy đơn vị
        sensor_id = payload_data.get("sensor_id") # Lấy sensor_id từ payload
        timestamp = payload_data.get("timestamp") # Lấy timestamp từ payload
        # topic = f"{building}/{floor}/{room}/{data_type}"

        if not all([building, floor, room, data_type]):
            print(f"[MQTT] Bỏ qua topic không hợp lệ: {msg.topic}")
            return

        print(f"[MQTT] 📩 Nhận dữ liệu: {building}/{floor}/{room}/{data_type} = {payload_str}")

        # 1️⃣ Đẩy dữ liệu ngay qua Socket.IO
        if _socketio_instance:
            _socketio_instance.emit("sensor_update", {"topic": msg.topic, "value": value, "unit": unit})
            print("[SocketIO] ✅ Đã phát dữ liệu tới client")
        else:
            print("[SocketIO] ⚠️ Chưa có instance SocketIO")

        # 2️⃣ Thêm vào queue để ghi DB (theo chu kỳ)
        # current_time = time.time()
        # if current_time - last_db_write_time >= DB_WRITE_INTERVAL:
        #     data_queue.put((sensor_id, payload, data_type))
        #     last_db_write_time = current_time
        #     print("[DB] ⏳ Thêm dữ liệu vào hàng đợi")
        
    except json.JSONDecodeError: # Bắt lỗi khi payload không phải là JSON hợp lệ
        print(f"[MQTT] ❌ Lỗi phân tích JSON từ payload: {payload_str}")
    except Exception as e:
        print(f"[MQTT] ❌ Lỗi xử lý tin nhắn: {e}")


# Khởi động MQTT listener (hàm này dùng để truyền vào Thread để tạo luồng mới)
def start_mqtt_listener(socketio_instance):
    global _socketio_instance
    _socketio_instance = socketio_instance

    # threading.Thread(target=db_worker, daemon=True).start()
    # print("[MQTT Handler] ✅ DB worker thread đã khởi động")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"[MQTT Handler] 🔌 Kết nối tới {MQTT_BROKER}:{MQTT_PORT}")
        client.loop_forever()
    except Exception as e:
        print(f"[MQTT Handler] ❌ Lỗi kết nối MQTT: {e}")
