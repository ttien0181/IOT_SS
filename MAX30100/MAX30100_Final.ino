Bạn đã nói:
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <MAX30100_PulseOximeter.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "SSIoT-02";
const char* password = "SSIoT-02";

// MQTT broker
const char* mqtt_server = "as2.pitunnel.net";
const int mqtt_port = 58395;
const char* topic_spo2 = "A1/1/101/spo2";
const char* topic_heart = "A1/1/101/heart_rate";

// MAX30100
PulseOximeter pox;
uint32_t lastReport = 0;
#define REPORTING_PERIOD_MS 5000

// LED pins
const int LED_GREEN = 16;
const int LED_YELLOW = 17;
const int LED_RED = 18;

// NTP (UTC+7)
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 7 * 3600);

// MQTT
WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  Serial.print("Connecting to WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  unsigned long timeout = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - timeout < 10000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

void reconnect() {
  while (!client.connected() && WiFi.status() == WL_CONNECTED) {
    Serial.print("Connecting to MQTT...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(", retry in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Setup LED pins
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_RED, LOW);

  setup_wifi();
  timeClient.begin();
  timeClient.update();
  client.setServer(mqtt_server, mqtt_port);

  if (!pox.begin()) {
    Serial.println("MAX30100 not found. Check wiring.");
    while (1);
  }

  Serial.println("MAX30100 initialized.");
  pox.setIRLedCurrent(MAX30100_LED_CURR_27_1MA);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  pox.update();

  if (millis() - lastReport > REPORTING_PERIOD_MS) {
    lastReport = millis();

    float heartRate = pox.getHeartRate();
    float spo2 = pox.getSpO2();

    Serial.print("Heart rate: ");
    Serial.print(heartRate);
    Serial.print(" bpm | SpO2: ");
    Serial.print(spo2);
    Serial.println(" %");

  

    // Cập nhật thời gian
    timeClient.update();
    time_t epochTime = timeClient.getEpochTime();
    struct tm* ptm = gmtime(&epochTime);
    char timeString[30];
    strftime(timeString, sizeof(timeString), "%Y-%m-%dT%H:%M:%SZ", ptm);

    // Gửi SpO2
    StaticJsonDocument<128> jsonSpO2;
    jsonSpO2["value"] = spo2;
    jsonSpO2["unit"] = "%";
    jsonSpO2["timestamp"] = timeString;
    char bufferSpO2[128];
    serializeJson(jsonSpO2, bufferSpO2);
    bool success_spo2 = client.publish(topic_spo2, bufferSpO2);

    // Gửi nhịp tim
    StaticJsonDocument<128> jsonHR;
    jsonHR["value"] = heartRate;
    jsonHR["unit"] = "bpm";
    jsonHR["timestamp"] = timeString;
    char bufferHR[128];
    serializeJson(jsonHR, bufferHR);
    bool success_hr = client.publish(topic_heart, bufferHR);

    // Reset LED
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_RED, LOW);

    // Kiểm tra cảnh báo
    bool redAlert = (heartRate < 45 || heartRate > 130 || spo2 < 90 );
    bool yellowAlert = (heartRate < 55 || heartRate > 110 || (spo2 >= 90 && spo2 < 95) );

    if (redAlert) {
      digitalWrite(LED_RED, HIGH);
      Serial.println("Cảnh báo đỏ");
    } else if (yellowAlert) {
      digitalWrite(LED_YELLOW, HIGH);
      Serial.println("Cảnh báo vàng");
    } else {
      digitalWrite(LED_GREEN, HIGH);
      Serial.println("Trạng thái bình thường");
    }

    // Debug MQTT
    Serial.println("Published SpO2:");
    Serial.println(bufferSpO2);
    Serial.println(success_spo2 ? "SpO2 published" : "SpO2 publish failed");

    Serial.println("Published Heart Rate:");
    Serial.println(bufferHR);
    Serial.println(success_hr ? "Heart rate published" : "Heart rate publish failed");

    Serial.println("--------------------------------------");
  }
}