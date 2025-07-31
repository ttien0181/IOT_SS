# mqtt_handler.py
import paho.mqtt.client as mqtt
import pymysql
import queue
import threading
import time
from datetime import datetime
from db import get_connection

# Cấu hình MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = [("hospital/floor1/room101/temperature", 0), ("hospital/floor1/room101/humidity", 0)] # chất lượng ("0" tức là chỉ gửi 1 lần, ko gửi lại)

# Biến kiểm soát thời gian ghi CSDL
last_db_write_time = 0
DB_WRITE_INTERVAL = 300  

# Hàng đợi để xử lý dữ liệu ghi vào DB
data_queue = queue.Queue()

# Biến toàn cục để lưu instance của SocketIO
# Sẽ được gán khi khởi tạo MQTTHandler
_socketio_instance = None

# Dữ liệu mới nhất từ MQTT (để ghép cặp nhiệt độ và độ ẩm)
latest_mqtt_data = {"lastest_temperature": None, "lastest_humidity": None}
latest_mqtt_data_lock = threading.Lock() # để đảm bảo chỉ có 1 luồng tại 1 thời điểm có, tránh race condition

# Hàm ghi vào DB từ queue (sẽ được chạy trong thread phụ)
def db_worker():
    while True:
        # Lấy dữ liệu từ queue (blocking call - sẽ chờ nếu queue rỗng)
        temp, humid = data_queue.get()
        conn = None
        try:
            conn = get_connection() # Sử dụng hàm get_connection của bạn
            with conn.cursor() as cur:
                # Đảm bảo tên bảng và cột khớp với CSDL của bạn
                # Dựa trên app.py của bạn, tôi dùng dht_data, temperature, humidity
                sql = "INSERT INTO dht_data (datetime, temperature, humidity) VALUES (NOW(), %s, %s)"
                cur.execute(sql, (temp, humid))
                conn.commit()
                print(f"[DB Worker] Đã lưu Nhiệt độ {temp}°C, Độ ẩm {humid}% vào lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"[DB Worker] Lỗi DB: {e}")
        finally:
            if conn:
                conn.close()
        data_queue.task_done() # Báo hiệu đã xử lý xong một item trong queue

# Callback khi kết nối MQTT thành công
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Đã kết nối thành công tới Broker!")
        for topic, qos in MQTT_TOPICS:
            client.subscribe(topic, qos)
            print(f"[MQTT] Đã đăng ký topic: {topic}")
    else:
        print(f"[MQTT] Kết nối thất bại với mã: {rc}")

# Callback khi nhận tin nhắn MQTT
def on_message(client, userdata, msg):
    global latest_mqtt_data, _socketio_instance, last_db_write_time

    try:
        payload = float(msg.payload.decode())

        with latest_mqtt_data_lock: # Sử dụng khóa để bảo vệ latest_mqtt_data
            if msg.topic == "sensor/temperature":
                latest_mqtt_data["lastest_temperature"] = payload
            elif msg.topic == "sensor/humidity":
                latest_mqtt_data["lastest_humidity"] = payload

            # Khi có đủ cả nhiệt độ và độ ẩm
            if latest_mqtt_data["lastest_temperature"] is not None and latest_mqtt_data["lastest_humidity"] is not None:
                temp = latest_mqtt_data["lastest_temperature"]
                humid = latest_mqtt_data["lastest_humidity"]

                print(f"[MQTT] Nhận dữ liệu: Nhiệt độ={temp}°C, Độ ẩm={humid}%")

                # 1. Đẩy dữ liệu ngay lập tức qua Socket.IO tới client với sự kiện 'sensor_data'
                if _socketio_instance:
                    _socketio_instance.emit('sensor_update', {'temperature': temp, 'humidity': humid})
                    print(f"[SocketIO] Đã phát dữ liệu tới client.")
                else:
                    print("[SocketIO] Lỗi: SocketIO instance chưa được gán.")

                # 2. Đưa dữ liệu vào queue để ghi vào CSDL bất đồng bộ
                current_time = time.time()
                # Nếu đã đủ thời gian, ghi vào db
                if current_time - last_db_write_time >= DB_WRITE_INTERVAL:
                    data_queue.put((temp, humid))
                    last_db_write_time = current_time
                    print(f"[DB] ⏳ Đã đủ thời gian, thêm vào queue")

                # Reset dữ liệu mới nhất để chờ cặp dữ liệu tiếp theo
                latest_mqtt_data = {"lastest_temperature": None, "lastest_humidity": None}

    except ValueError:
        print(f"[MQTT] Lỗi chuyển đổi payload thành số: {msg.payload.decode()}")
    except Exception as e:
        print(f"[MQTT] Lỗi xử lý tin nhắn: {e}")

# Hàm khởi tạo và chạy MQTT client
def start_mqtt_listener(socketio_instance):
    global _socketio_instance
    _socketio_instance = socketio_instance # Gán instance SocketIO

    # Khởi tạo thread ghi DB, thread này chạy hàm 'db_worker'
    threading.Thread(target=db_worker, daemon=True).start()
    print("[MQTT Handler] DB worker thread đã khởi động.")

    # Cấu hình MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"[MQTT Handler] Đang kết nối tới MQTT Broker tại {MQTT_BROKER}:{MQTT_PORT}...")
        client.loop_forever() # Chạy vòng lặp xử lý tin nhắn MQTT
    except Exception as e: # nếu lỗi
        print(f"[MQTT Handler] Lỗi kết nối hoặc vòng lặp MQTT: {e}")