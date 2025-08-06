#include <WiFi.h>
#include <PubSubClient.h>

// --- WiFi & MQTT ---
const char* ssid = "SSIoT-02";
const char* password = "SSIoT-02";

const char* mqtt_server = "pi102.local";
const int mqtt_port = 1883;
const char* mqtt_topic_heartbeat = "bachmai/A1/1/102/HEARTBEAT102/bpm";

WiFiClient espClient;
PubSubClient client(espClient);

// --- Heartbeat Sensor ---
#define heartbeat_sensor 34
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

  for(int i=0; i < SAMPLE_SIZE; i++) {
    samples[i] = 0;
  }

  setup_wifi();
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

    if (millis() - lastPrintTime >= printInterval) {
      Serial.println("No finger detected");
      lastPrintTime = millis();
      // Gửi mqtt báo không đo được nhịp tim
      client.publish(mqtt_topic_heartbeat, "No finger detected");
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

        if (millis() - lastPrintTime >= printInterval) {
          Serial.print("Nhịp tim (BPM): ");
          Serial.println(bpm);
          lastPrintTime = millis();

          // Gửi mqtt nhịp tim dưới dạng chuỗi
          char bpmStr[10];
          dtostrf(bpm, 4, 1, bpmStr);
          client.publish(mqtt_topic_heartbeat, bpmStr);
        }
      } else {
        if (millis() - lastPrintTime >= printInterval) {
          Serial.println("Invalid BPM detected");
          lastPrintTime = millis();
          client.publish(mqtt_topic_heartbeat, "Invalid BPM");
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

  readHeartbeatSensor();

  delay(20);  // Tốc độ đọc cảm biến nhịp tim
}
