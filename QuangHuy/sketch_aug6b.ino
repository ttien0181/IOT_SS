#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <ArduinoJson.h>


const char* ssid = "SSIoT-02";
const char* password = "SSIoT-02";


const char* mqtt_server = "pi102.local";
const int mqtt_port = 1883;


const int motionSensor = 27;
const int ledPin = 25;
String sensorID = "esp32-PIR102";
String baseTopic = "A1/1/102";  
String topic_motion;


WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 7 * 3600);  
char timeString[30];


WiFiClient espClient;
PubSubClient client(espClient);


int lastMotionState = LOW;

void setup_wifi() {
  Serial.print("🔌 Đang kết nối WiFi");
  WiFi.begin(ssid, password);
  unsigned long wifiTimeout = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiTimeout < 10000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n Đã kết nối WiFi!");
    Serial.print("📡 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n Kết nối WiFi thất bại!");
  }
}

void reconnect_mqtt() {
  while (!client.connected() && WiFi.status() == WL_CONNECTED) {
    Serial.print("🔌 Kết nối MQTT...");
    if (client.connect("ESP32Client_PIR")) {
      Serial.println(" MQTT đã kết nối");
    } else {
      Serial.print(" MQTT thất bại, mã lỗi: ");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void getFormattedTime() {
  timeClient.update();
  time_t epochTime = timeClient.getEpochTime();
  struct tm* ptm = gmtime(&epochTime);
  strftime(timeString, sizeof(timeString), "%Y-%m-%dT%H:%M:%SZ", ptm);
}

void setup() {
  Serial.begin(115200);
  pinMode(motionSensor, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  setup_wifi();

  timeClient.begin();
  timeClient.update();

  client.setServer(mqtt_server, mqtt_port);
  reconnect_mqtt();

  topic_motion = baseTopic + "/motion";
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    setup_wifi();
  }

  if (!client.connected()) {
    reconnect_mqtt();
  }

  client.loop();

  int motionState = digitalRead(motionSensor);

  if (motionState != lastMotionState) {
    lastMotionState = motionState;

    getFormattedTime();


    StaticJsonDocument<200> jsonMotion;
    jsonMotion["value"] = motionState == HIGH ? "1" : "0";  
    jsonMotion["unit"] = "motion";
    jsonMotion["sensor_id"] = sensorID;
    jsonMotion["timestamp"] = timeString;

    char bufferMotion[200];
    serializeJson(jsonMotion, bufferMotion);

    bool success = client.publish(topic_motion.c_str(), bufferMotion);


    digitalWrite(ledPin, motionState);
    Serial.println(success ? " Đã gửi MQTT:" : " Gửi thất bại:");
    Serial.println(bufferMotion);
  }

  delay(200);
}

