#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <ArduinoJson.h>

// --- WiFi ---
const char* ssid = "SSIoT-01";
const char* password = "SSIoT-01";

// --- MQTT ---
const char* mqtt_server = "172.20.10.14";
const int mqtt_port = 1883;
const char* mqtt_topic = "A1/1/102/motion";

WiFiClient espClient;
PubSubClient client(espClient);

WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "129.6.15.28", 0, 60000);

const int motionSensor = 27;
const int ledPin = 25;

const char* sensorID = "ESP32-MOTION01";

String getCurrentTimestamp() {
  time_t epochTime = timeClient.getEpochTime();
  struct tm *ptm = gmtime(&epochTime);
  char timeString[30];
  strftime(timeString, sizeof(timeString), "%Y-%m-%dT%H:%M:%SZ", ptm);
  return String(timeString);
}

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

void reconnect_mqtt() {
  while (!client.connected() && WiFi.status() == WL_CONNECTED) {
    String clientId = "ESP32Client-" + String(WiFi.macAddress());
    Serial.print("🔄 Đang kết nối MQTT...");
    if (client.connect(clientId.c_str())) {
      Serial.println("✅ MQTT connected");
    } else {
      Serial.println("❌ MQTT reconnect failed. Retrying...");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(motionSensor, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  setup_wifi();

  timeClient.begin();
  // Đợi NTP cập nhật thành công
  Serial.println("⏳ Đang đồng bộ thời gian NTP...");
  while (!timeClient.update()) {
    timeClient.forceUpdate();
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Thời gian NTP đồng bộ xong.");

  client.setServer(mqtt_server, mqtt_port);
  reconnect_mqtt();
}
bool lastMotionDetected = false;

void loop() {
  if (!client.connected()) {
    reconnect_mqtt();
  }
  client.loop();

  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  int motionState = digitalRead(motionSensor);
  bool motionDetected = (motionState == HIGH);
 // hoặc HIGH tùy cảm biến

  // In liên tục trạng thái lên Serial
  if (motionDetected) {
    Serial.println("🚨 Có chuyển động!");
    digitalWrite(ledPin, HIGH);
  } else {
    Serial.println("✅ Không có chuyển động.");
    digitalWrite(ledPin, LOW);
  }

  // Gửi MQTT chỉ khi trạng thái thay đổi
  if (motionDetected != lastMotionDetected) {
    lastMotionDetected = motionDetected;

    StaticJsonDocument<200> jsonMotion;
    jsonMotion["value"] = motionDetected ? "1" : "0";
    jsonMotion["unit"] = "state";
    jsonMotion["sensor_id"] = sensorID;
    jsonMotion["timestamp"] = getCurrentTimestamp();

    char buffer[200];
    serializeJson(jsonMotion, buffer);

    bool success = client.publish(mqtt_topic, buffer);

    Serial.println("Published Motion JSON:");
    Serial.println(buffer);
    Serial.println(success ? "✅ MQTT published" : "❌ MQTT publish failed");
  }

  delay(500); // delay nhỏ cho dễ đọc Serial và tránh quá tải CPU
}

