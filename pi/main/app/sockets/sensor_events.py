# app/routes/socket_events.py
from flask_socketio import emit
import logging
from app.services.sensor_service import get_latest_data

logger = logging.getLogger(__name__)

# hàm đăng ký các callback cho "socketio"
def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print("[SocketIO] Client connected")

    @socketio.on('disconnect')
    def handle_disconnect():
        print("[SocketIO] Client disconnected")

    # callback khi có message 'subscribe_topic'
    @socketio.on('subscribe_topic')
    def handle_subscribe_topic(data):
        building = data.get("building")
        floor = data.get("floor")
        room = data.get("room")
        data_type = data.get("data_type")

        topic = f"{building}/{floor}/{room}/{data_type}"

        print(f"[SocketIO] Client subscribed: {building}/{floor}/{room}/{data_type}")

        try:
            row = get_latest_data(building, floor, room, data_type)
            if row:
                push_data_to_client(socketio, row["value"], row["unit"], topic)
            else:
                emit("sensor_update", {"message": "Không có dữ liệu"})
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu ban đầu: {e}")
            emit("sensor_update", {"error": "Lỗi server, không lấy được dữ liệu"})

def push_data_to_client(socketio,  value, unit ,topic):
    socketio.emit('sensor_update', {
        'topic': topic, 
        'value': value,
        'unit': unit
    })
    print(f"[SocketIO] Đã phát dữ liệu: {topic} : {value} {unit}")
