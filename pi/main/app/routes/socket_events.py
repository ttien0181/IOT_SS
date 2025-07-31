# app/routes/socket_events.py
from flask_socketio import emit
import pymysql
from app.database.connection import get_connection

def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print("[SocketIO] Client connected")
        try:
            conn = get_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute("SELECT temperature, humidity FROM dht_data ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                if row:
                    print(f"[SocketIO] gửi dữ liệu ban đầu cho client mới kết nối")
                    push_data_to_client(socketio, row["temperature"], row["humidity"])
        except Exception as e:
            print(f"[ERROR] lỗi gửi dữ liệu ban đầu cho client mới kết nối: {e}")
        finally:
            if conn:
                conn.close()

def push_data_to_client(socketio, temp, humid):
    socketio.emit('sensor_update', {'temperature': temp, 'humidity': humid})
    print(f"[SocketIO] đã cập nhật dữ liệu dhtdata")
