from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import time
import threading
import json

app = Flask(__name__)

# Mobius Configuration
MOBIUS_BASE_URL = "http://172.27.162.58:7579"
CSE_BASE = "/Mobius"
ORIGIN = "HealthCareIoT"
CONTAINER_NAME = "SensorDataContainer"

# Global data store with thread lock
from threading import Lock
data_lock = Lock()
latest_data = {
    "status": "waiting",
    "timestamp": datetime.now().isoformat(),
    "patient_data": None,
    "error": None
}

def fetch_mobius_data():
    global latest_data
    url = f"{MOBIUS_BASE_URL}{CSE_BASE}/{ORIGIN}/{CONTAINER_NAME}/la"
    
    try:
        response = requests.get(url, headers={
            "Accept": "application/json",
            "X-M2M-RI": "12345",
            "X-M2M-Origin": ORIGIN
        }, timeout=3)

        if response.status_code == 200:
            cin = response.json().get("m2m:cin", {})
            content = cin.get("con", {})
            
            # Parse content (handles both string and dict)
            try:
                data = json.loads(content) if isinstance(content, str) else content
            except json.JSONDecodeError:
                data = {}

            with data_lock:
                latest_data = {
                    "status": "success",
                    "timestamp": datetime.fromisoformat(cin.get("lt", datetime.now().isoformat())).strftime("%Y-%m-%d %H:%M:%S"),
                    "patient_data": data,
                    "error": None
                }
        else:
            with data_lock:
                latest_data["error"] = f"HTTP {response.status_code}"

    except Exception as e:
        with data_lock:
            latest_data["error"] = str(e)

def background_updater():
    while True:
        fetch_mobius_data()
        time.sleep(2)  # Update more frequently

@app.route('/')
def dashboard():
    with data_lock:
        return render_template('dashboard.html', data=latest_data)

@app.route('/api/data')
def api_data():
    with data_lock:
        return jsonify(latest_data)

if __name__ == '__main__':
    threading.Thread(target=background_updater, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)