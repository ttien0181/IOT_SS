# mqtt_ws_bridge.py
import asyncio
import json
import websockets
import paho.mqtt.client as mqtt

clients = set()
latest_data = {"temp": 0, "humid": 0}

# Gửi dữ liệu đến tất cả client WebSocket
async def send_data():
    while True:
        if clients:
            data = json.dumps(latest_data)
            await asyncio.wait([client.send(data) for client in clients])
        await asyncio.sleep(1)  # Gửi mỗi giây

# Khi có client kết nối WebSocket
async def handler(websocket, path):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

# MQTT Callback
def on_message(client, userdata, msg):
    global latest_data
    payload = msg.payload.decode()
    if msg.topic == "sensor/temp":
        latest_data["temp"] = float(payload)
    elif msg.topic == "sensor/humid":
        latest_data["humid"] = float(payload)

# Kết nối MQTT
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.connect("localhost", 1883)
mqttc.subscribe("sensor/temp")
mqttc.subscribe("sensor/humid")
mqttc.loop_start()

# Chạy WebSocket server
start_server = websockets.serve(handler, "0.0.0.0", 6789)
loop = asyncio.get_event_loop()
loop.create_task(send_data())
loop.run_until_complete(start_server)
loop.run_forever()
