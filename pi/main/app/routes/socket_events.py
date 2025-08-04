# app/routes/socket_events.py
from flask_socketio import emit
import pymysql
from app.database.connection import get_connection

def register_socket_events(socketio):
    # Khi client kết nối
    @socketio.on('connect')
    def handle_connect():
        print("[SocketIO] Client connected")

    # Khi client chọn topic (tòa nhà/tầng/phòng/loại dữ liệu)
    @socketio.on('subscribe_topic')
    def handle_subscribe_topic(data):
        building = data.get("building")
        floor = data.get("floor")
        room = data.get("room")
        data_type = data.get("data_type")

        print(f"[SocketIO] Client subscribed: {building}/{floor}/{room}/{data_type}")

        try:
            conn = get_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute("""
                    SELECT sd.data_value, sd.data_type 
                    FROM sensor_data sd
                    JOIN sensor_location sl ON sd.sensor_id = sl.sensor_id
                    WHERE sl.building = %s
                      AND sl.floor = %s
                      AND sl.room = %s
                      AND sd.data_type = %s
                    ORDER BY sd.timestamp DESC
                    LIMIT 1;
                """, (building, floor, room, data_type))
                
                row = cur.fetchone()
                if row:
                    # Gửi dữ liệu ban đầu cho client
                    push_data_to_client(socketio, row["data_type"], row["data_value"])
                else:
                    print("[SocketIO] Không có dữ liệu khớp")
        except Exception as e:
            print(f"[ERROR] Lỗi khi lấy dữ liệu ban đầu: {e}")
        finally:
            if conn:
                conn.close()

# ----
# Hàm phát dữ liệu ra client
def push_data_to_client(socketio, data_type, value):
    socketio.emit('sensor_update', {data_type: value})
    print(f"[SocketIO] Đã phát dữ liệu {data_type}: {value}")
