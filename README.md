#  Health Monitoring System
A real-time IoT-based health monitoring system that collects vital signs such as heart rate, SpO₂, body temperature, and motion using biomedical sensors and ESP32, then processes and visualizes the data through a full-stack IoT architecture (MQTT, [Mobius](https://github.com/IoTKETI/Mobius) [oneM2M](https://github.com/IoTKETI/oneM2MBrowser), [nCube Thyme Nodejs](https://github.com/IoTKETI/nCube-Thyme-Nodejs), Flask Web Dashboard).

--- 
## Overview
This project was built as part of the **Samsung Innovation Campus - IoT Capstone Course**. The system aims to enhance hospital and remote patient monitoring by enabling continuous data acquisition, real-time alerting, and historical trend visualization.

--- 

## Requirements
### 1. Operating System
- Linux (Ubuntu 20.04/22.04+ recommended)
- Windows with WSL (Ubuntu) enabled

### 2. System Packages (Linux/WSL)
Install core tools and services:
```bash
sudo apt update
sudo apt install -y git curl build-essential python3 python3-venv python3-pip \
    mariadb-server mosquitto
```

Verify versions:
```bash
python3 --version
node --version || true
npm --version || true
mysql --version
mosquitto -h | head -n1
```

If Node.js is not installed, install LTS:
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

### 3. Clone Repository
```bash
git clone https://github.com/ttien0181/IOT_SS.git
cd IOT_SS
```

### 4. Database Setup (MariaDB/MySQL)
Create required databases and users. Mobius uses `mobiusdb`. Flask auth uses `iot02` by default.

Open MySQL shell and create DBs/users:
```bash
sudo service mysql start
mysql -u root -p -e "\
CREATE DATABASE IF NOT EXISTS mobiusdb CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci; \
CREATE DATABASE IF NOT EXISTS iot02 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci; \
CREATE USER IF NOT EXISTS 'mobius'@'localhost' IDENTIFIED BY 'mobius'; \
GRANT ALL PRIVILEGES ON mobiusdb.* TO 'mobius'@'localhost'; \
CREATE USER IF NOT EXISTS 'ttien'@'localhost' IDENTIFIED BY '0181'; \
GRANT ALL PRIVILEGES ON iot02.* TO 'ttien'@'localhost'; \
FLUSH PRIVILEGES;"
```

Import Mobius schema:
```bash
mysql -u root -p mobiusdb < Mobius/mobius/mobiusdb.sql
```

Create Flask auth tables in `iot02`:
```bash
mysql -u root -p iot02 -e "\
CREATE TABLE IF NOT EXISTS pending_users ( \
  email VARCHAR(255) PRIMARY KEY, \
  password_hash VARCHAR(255) NOT NULL, \
  otp_code VARCHAR(10) NOT NULL, \
  expires_at DATETIME NOT NULL \
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci; \
CREATE TABLE IF NOT EXISTS users ( \
  id INT AUTO_INCREMENT PRIMARY KEY, \
  email VARCHAR(255) NOT NULL UNIQUE, \
  password VARCHAR(255) NOT NULL, \
  create_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP \
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
```

### 5. MQTT Broker (Mosquitto)
Start broker (keep it running while testing):
```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### 3. Hardware
#### Actuators
- **Led** 
![Led](image/led.png)
- **Buzzer** 
![Buzzer](image/buzzer.png)
#### Sensor
- **MAX30100** (HR, SpO₂) 
![MAX30100 (HR, SpO₂)](/image/MAX30100.png)
- **KY-039** (HR)
![KY-039 (HR)](/image/KY039.png) 
- **DHT11** (Temp)
![DHT11 (Temp)](/image/DHT11.png) 
- **HC-SR501** (Motion)
![HC-SR501 (Motion)](/image/HC-SR501.png)

#### Microcontroller 
**ESP32** (sends sensor data via MQTT)
![ESP32](/image/ESP32.png)

---
## System Architecture
![](image/system_architecture.png)

---
## Sensor Thresholds & Alerts
| Sensor     | Normal     | Warning     | Critical    |
|------------| ---------- | ----------- | ----------- |
| Heart Rate | 60–100 bpm | <55 or >110 | <45 or >130 |
| SpO₂       | ≥ 95%      | 90% – 94%   | <90%        |
| Motion     | Detected   | —           | No Motion   |

---
## Demo Screenshots


![login](image/login.png)


![register](image/register.png)


![realtime](image/realtime.png)


![dashboard](image/dashboard.png)


![profile](image/profile.png)


![MAX30100](image/MAX30100_cout.png)


![KY-039](image/KY-039_cout.png)


![HC-SR501](image/HC-SR501_cout.png)


---
## How to Run
### 1. Hardware (optional for simulation)
- To test end-to-end without hardware, you can publish simulated MQTT messages (see step 5). For real hardware, flash ESP32 with code in `ESP32/` and connect sensors.

### 2. Start MQTT Broker (Mosquitto)
```bash
sudo systemctl start mosquitto
```

### 3. Configure and Run Mobius (IoT Platform)
Set database and server ports via `Mobius/conf.json` (already created by code):
```json
{
    "csebaseport": 7579,
    "dbhost": "localhost",
    "dbuser": "mobius",
    "dbpass": "mobius",
    "dbname": "mobiusdb"
}
```
Run Mobius:
```bash
cd Mobius
npm install
node mobius.js
```
Verify Mobius is up:
```bash
curl -s http://localhost:7579/Mobius -H "X-M2M-RI: 12345" -H "X-M2M-Origin: Sorigin" -H "Accept: application/json"
```

### 4. Run nCube-Thyme (Edge App)
Confirm it points to local Mobius in `nCube-Thyme-Nodejs/conf.js`:
```js
cse = { host: 'localhost', port: '7579', name: 'Mobius', id: '/Mobius2', mqttport: '1883', wsport: '7577' };
```
Run:
```bash
cd nCube-Thyme-Nodejs
npm install
node thyme.js
```

### 5. Send Simulated Sensor Data via Mosquitto
Open a new terminal (keep Mobius running). Publish JSON payloads matching Flask and dashboard expectations:
```bash
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

mosquitto_pub -h localhost -p 1883 -t "A1/1/101/spo2" -m "{\"value\": 97, \"unit\": \"%\", \"sensor_id\": \"esp32-01\", \"timestamp\": \"${TS}\"}"

mosquitto_pub -h localhost -p 1883 -t "A1/1/101/heart_rate" -m "{\"value\": 72, \"unit\": \"bpm\", \"sensor_id\": \"esp32-01\", \"timestamp\": \"${TS}\"}"
```

### 6. Run Flask Web Dashboard
```bash
cd Flask-web
python3 -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt
python3 run.py
```
Open the dashboard at:
```
http://127.0.0.1:5000
```

If you use the built-in registration/login, ensure the `iot02` DB and tables exist (see Requirements → Database Setup). If you prefer a single DB, you may point auth to `mobiusdb` in `app/database/connection.py` (both options supported).
---
## Future Improvements
- Add AI anomaly detection (arrhythmia, hypoxia)
- Develop mobile app for doctors/nurses
- Battery support for ESP32 + backup server
- Cloud data storage and remote monitoring

---
## Team members

- [Nguyễn Quang Dũng](https://github.com/Duzngpanda05)
- [Hoàng Anh Tú](https://github.com/ttien0181)
- [Vũ Trung Hiếu](https://github.com/hieuvu0212)
- [Nguyễn Quang Huy](https://github.com/huymtpzz1)
- [Nguyễn Quang Linh](https://github.com/JKunnarter)
- [Nguyễn Quốc Anh](https://github.com/QuanhVipPro)
![](image/member.png)
