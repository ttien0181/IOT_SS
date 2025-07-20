import paho.mqtt.client as mqtt
import pymysql
import queue
import threading
from datetime import datetime

# MQTT config
MQTT_BROKER = "192.168.72.94"
MQTT_PORT = 1883
MQTT_TOPICS = [("sensor/temperature", 0), ("sensor/humidity", 0)] # chất lượng ("0" tức là chỉ gửi 1 lần, ko gửi lại)

# MySQL config
DB_CONFIG = {
    "host": "localhost",
    "user": "ttien",
    "password": "0181",
    "database": "iot02",
    "charset":"utf8mb4"
}

# Queue để xử lý dữ liệu, thread ghi DB sẽ liên tục xử lý dữ liệu trong queue này
data_queue = queue.Queue()

# Hàm ghi vào DB từ queue 
def db_worker():
    while True:
        temperature, humidity  = data_queue.get() # Lấy dữ liệu từ queue (blocking)
        try:
            conn = pymysql.connect(**DB_CONFIG) # dùng ** để giải nén dictionary thành các tham số đặt tên (named parameters).
            with conn.cursor() as cur: # "with" để đảm bảo cursor tự đóng
                sql = "INSERT INTO temp_humid_data (datetime, temp, humid) VALUES (NOW(), %s, %s)"
                cur.execute(sql, (temperature,humidity))
                conn.commit()
                print(f"Đã lưu nhiệt độ {temperature} độ C, độ ẩm{humidity} % vào lúc {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
            conn.close()
        except Exception as e:
            print("DB Error:", e)
        data_queue.task_done()

# Callback khi kết nối MQTT
def on_connect(client, userdata, flags, rc):
    print("Connected with code", rc)
    client.subscribe(MQTT_TOPICS)


latest_data = {"temperature": None, "humidity": None} # lưu data mới nhất

# Callback khi nhận tin nhắn 
def on_message(client, userdata, msg):
    global latest_data

    try:
        payload = float(msg.payload.decode())           # giải mã byte thành string

        if msg.topic == "sensor/temperature":
            latest_data["temperature"] = float(payload) # chuyển thành số thưucj
        elif msg.topic == "sensor/humidity":
            latest_data["humidity"] = payload

        # Khi có đủ cả 2 dữ liệu
        if latest_data["temperature"] is not None and latest_data["humidity"] is not None:
            data_queue.put((latest_data["temperature"], latest_data["humidity"]))   # đưa vào queue
            latest_data = {"temperature": None, "humidity": None}  # reset data mới nhất

    except Exception as e:
        print("Message error:", e)

# Khởi tạo thread ghi DB
# target: hàm chạy trong thread (db_worker: ko có "()" nên chỉ là địa chỉ hàm, chứ chưa gọi hàm)
# daemon = true: khi thread chính kết thúc, thread này tự dừng
# daemon = false: luồng chính chỉ kết thúc khi thread phụ dừng (nhưng thread phụ này ko dừng) 
# start: bắt đầu thực hiện luồng
threading.Thread(target=db_worker, daemon=True).start()

# MQTT client setup
client = mqtt.Client()                      # tạo client
client.on_connect = on_connect              # gán callback khi on_connect
client.on_message = on_message              # gán callback khi on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)  # kết nối tới broker
client.loop_forever()                       # chạy vòng lặp
