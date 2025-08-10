# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from app.routes.auth_routes import auth_bp
from app.routes.main_routes import main_bp
from app.routes.api_route import api_bp
from app.sockets.sensor_events import register_socket_events
from app.services.mqtt_handle import start_mqtt_listener

import threading

socketio = SocketIO()  # create Global socketIO object

# tạo ứng dụng
def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key'

    # Đăng ký Blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Khởi tạo SocketIO
    socketio.init_app(app)

    # Đăng ký các sự kiện socketio
    register_socket_events(socketio)

    # Chạy luồng MQTT
    mqtt_thread = threading.Thread(target=start_mqtt_listener, args=(socketio,))
    # Đặt luồng này thành luồng nền (daemon thread) (tức là sẽ tự động kết thúc khi luồng main kết thúc)
    mqtt_thread.daemon = True 
    # bắt đầu thực thi luồng
    mqtt_thread.start()
    print("[FLASK] MQTT listener thread đã khởi động.")

    return app
