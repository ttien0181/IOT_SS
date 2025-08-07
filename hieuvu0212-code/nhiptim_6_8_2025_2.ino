#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <ArduinoJson.h>

// --- WiFi & MQTT ---
const char* ssid = "SSIoT-02";
const char* password = "SSIoT-02";

const char* mqtt_server = "pi102.local";
const int mqtt_port = 1883;
const char* mqtt_topic_heartbeat = "A1/1/101/heart_rate";

WiFiClient espClient;
PubSubClient client(espClient);

// --- NTP ---
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 0, 60000);  // UTC, cập nhật mỗi 60s

// --- Heartbeat Sensor ---
#define heartbeat_sensor 34
#define buzzer 33
#define SAMPLE_SIZE 15
#define MIN_BEAT_INTERVAL 300  // ms

float samples[SAMPLE_SIZE];
int sampleIndex = 0;
float sampleSum = 0;

unsigned long lastBeatTime = 0;
float bpm = 0;
float bpmSmooth = 0;

bool beatDetected = false;
float prevAvgValue = 0;

unsigned long lastPrintTime = 0;
const unsigned long printInterval = 2000;  // 2 giây

const char* sensorID = "ESP32-HEART01";

// --- Hàm lấy timestamp dạng ISO 8601 ---
String getCurrentTimestamp() {
  timeClient.update();
  time_t epochTime = timeClient.getEpochTime();
  struct tm *ptm = gmtime(&epochTime);
  char timeString[30];
  strftime(timeString, sizeof(timeString), "%Y-%m-%dT%H:%M:%SZ", ptm);
  return String(timeString);
}

// --- Hàm setup WiFi ---
void setup_wifi() {
  Serial.print("🔌 Đang kết nối WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Đã kết nối WiFi!");
  Serial.print("📡 IP: ");
  Serial.println(WiFi.localIP());
}

// --- Kết nối MQTT ---
void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("🔌 Kết nối MQTT...");
    if (client.connect("ESP32Client")) {
      Serial.println("✅ Thành công!");
    } else {
      Serial.print("❌ Lỗi kết nối MQTT. Mã: ");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// --- Setup ---
void setup() {
  Serial.begin(115200);

  for (int i = 0; i < SAMPLE_SIZE; i++) {
    samples[i] = 0;
  }

  pinMode(buzzer, OUTPUT);
  digitalWrite(buzzer, LOW);  // Tắt buzzer ban đầu

  setup_wifi();
  timeClient.begin();
  timeClient.update();
  client.setServer(mqtt_server, mqtt_port);
  reconnect_mqtt();
}

// --- Đọc và xử lý cảm biến nhịp tim ---
void readHeartbeatSensor() {
  int rawValue = analogRead(heartbeat_sensor);
  if (rawValue < 50) rawValue = 0;

  sampleSum -= samples[sampleIndex];
  samples[sampleIndex] = rawValue;
  sampleSum += rawValue;
  sampleIndex = (sampleIndex + 1) % SAMPLE_SIZE;
  float avgValue = sampleSum / SAMPLE_SIZE;

  if (avgValue < 100) {
    bpm = 0;
    beatDetected = false;
    prevAvgValue = avgValue;
    digitalWrite(buzzer, LOW);  // Tắt buzzer nếu không phát hiện ngón tay

    if (millis() - lastPrintTime >= printInterval) {
      Serial.println("No finger detected");

      StaticJsonDocument<200> jsonNF;
      jsonNF["value"] = -1;
      jsonNF["unit"] = "bpm";
      jsonNF["sensor_id"] = sensorID;
      jsonNF["timestamp"] = getCurrentTimestamp();

      char bufferNF[200];
      serializeJson(jsonNF, bufferNF);
      client.publish(mqtt_topic_heartbeat, bufferNF);

      lastPrintTime = millis();
    }
    return;
  }

  static float threshold = 0;
  threshold = 0.6 * threshold + 0.4 * avgValue;

  unsigned long now = millis();

  if (avgValue > threshold && avgValue > prevAvgValue && !beatDetected) {
    if (now - lastBeatTime > MIN_BEAT_INTERVAL) {
      unsigned long beatInterval = now - lastBeatTime;
      lastBeatTime = now;

      float currentBpm = 60000.0 / beatInterval;

      if (currentBpm >= 40 && currentBpm <= 140) {
        bpmSmooth = 0.8 * bpmSmooth + 0.2 * currentBpm;
        bpm = bpmSmooth;

        // Điều khiển buzzer theo mức độ BPM
        if (bpm < 45 || bpm > 130) {
          digitalWrite(buzzer, HIGH);  // Nguy hiểm
        } else {
          digitalWrite(buzzer, LOW);   // Bình thường hoặc chỉ bất thường nhẹ
        }

        if (millis() - lastPrintTime >= printInterval) {
          Serial.print("Nhịp tim (BPM): ");
          Serial.println(bpm);

          StaticJsonDocument<200> jsonBPM;
          jsonBPM["value"] = String(bpm, 1);
          jsonBPM["unit"] = "bpm";
          jsonBPM["sensor_id"] = sensorID;
          jsonBPM["timestamp"] = getCurrentTimestamp();

          char bufferBPM[200];
          serializeJson(jsonBPM, bufferBPM);
          bool success = client.publish(mqtt_topic_heartbeat, bufferBPM);

          Serial.println("Published BPM JSON:");
          Serial.println(bufferBPM);
          Serial.println(success ? "✅ BPM published" : "❌ Failed to publish BPM");

          lastPrintTime = millis();
        }
      } else {
        digitalWrite(buzzer, LOW);  // Không hợp lệ → tắt buzzer

        if (millis() - lastPrintTime >= printInterval) {
          Serial.println("Invalid BPM detected");

          StaticJsonDocument<200> jsonInv;
          jsonInv["value"] = 0;
          jsonInv["unit"] = "bpm";
          jsonInv["sensor_id"] = sensorID;
          jsonInv["timestamp"] = getCurrentTimestamp();

          char bufferInv[200];
          serializeJson(jsonInv, bufferInv);
          client.publish(mqtt_topic_heartbeat, bufferInv);

          lastPrintTime = millis();
        }
      }
      beatDetected = true;
    }
  }

  if (avgValue < threshold) {
    beatDetected = false;
  }

  prevAvgValue = avgValue;
}

// --- Main loop ---
void loop() {
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();

  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  readHeartbeatSensor();
  delay(20);  // Đọc cảm biến mỗi 20ms
}
