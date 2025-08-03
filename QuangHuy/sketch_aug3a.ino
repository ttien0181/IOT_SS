#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "SSIoT-02";
const char* password = "SSIoT-02";

const char* mqtt_server = "pi102.local";
const int mqtt_port = 1883;
const char* mqtt_topic = "bachmai/A1/1/102/MOTION102/motion";

WiFiClient espClient;
PubSubClient client(espClient);

const int motionSensor = 27;
const int ledPin = 25;

int lastMotionState = LOW;

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

void setup() {
  Serial.begin(115200);

  pinMode(motionSensor, INPUT);  // Sửa lỗi tại đây
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  reconnect_mqtt();
}

void loop() {
  if (!client.connected()) {
    reconnect_mqtt();
  }

  client.loop();

  int motionState = digitalRead(motionSensor);

  Serial.print("📡 Trạng thái cảm biến PIR: ");
  Serial.println(motionState);

  if (motionState != lastMotionState) {
    lastMotionState = motionState;

    if (motionState == HIGH) {
      Serial.println("🚨 Có chuyển động!");
      client.publish(mqtt_topic, "chuyen dong");
      digitalWrite(ledPin, HIGH);
    } else {
      Serial.println("✅ Không có chuyển động.");
      client.publish(mqtt_topic, "Khong chuyen dong");
      digitalWrite(ledPin, LOW);
    }
  }

  delay(200);
}
