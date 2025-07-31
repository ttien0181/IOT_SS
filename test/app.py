# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import pymysql.cursors
from db import get_connection
from auth import auth_bp
from mqtt_handle import start_mqtt_listener
import threading
import pymysql




# khởi tạo app
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Dùng để quản lý session người dùng



# khởi tạo 1 instance SocketIO, truyền instance 'app' vào   
# Biến ứng dụng Flask thành một máy chủ có khả năng xử lý giao tiếp thời gian thực bằng Socket.IO
socketio = SocketIO(app) 

# Đăng ký Blueprint 'auth_bp' để sử dụng các route của 'auth_bp' (VD: @auth_bp.login)
app.register_blueprint(auth_bp)




# Trang chủ (nếu đã login thì hiển thị dashboard, không thì chuyển hướng login)
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Trang cho từng tầng
@app.route('/floor/<int:floor_id>')
@login_required
def floor_page(floor_id):
    return render_template('floor.html', floot_id = floor_id)


# WebSocket: Khi client kết nối
@socketio.on('connect')
def handle_connect():
    print("[SocketIO] Client connected")
    # emit dữ liệu ban đầu (lấy từ csdl)
    try:
        conn = get_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT temperature, humidity FROM dht_data ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if row:                
                print(f"[SocketIO] gửi dữ liệu ban đầu cho client mới kết nối")
                push_data_to_client(row["temperature"], row["humidity"])
    except Exception as e:
        print(f"[ERROR] lỗi gửi dữ liệu ban đầu cho client mới kết nối: {e}")
    finally :
        if conn:
            conn.close()

# WebSocket: Server đẩy dữ liệu tới client
def push_data_to_client(temp, humid):
    socketio.emit('sensor_update', {'temperature': temp, 'humidity': humid})
    print(f"[SocketIO] đã cập nhật dữ liệu dhtdata")

if __name__ == '__main__':
    print("[FLASK] Web server is running...")
    # Khởi động MQTT listener trong một luồng riêng chạy hàm 'start_mqtt_listener' từ mqtt_handle
    # Truyền đối tượng 'socketio' vào để mqtt_handler có thể phát sự kiện
    mqtt_thread = threading.Thread(target=start_mqtt_listener, args=(socketio,))
    mqtt_thread.daemon = True # Đảm bảo luồng MQTT thoát khi ứng dụng chính thoát
    mqtt_thread.start()
    print("[FLASK] MQTT listener thread đã khởi động.")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

