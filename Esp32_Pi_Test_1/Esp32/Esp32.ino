#include <WiFi.h>
#include <PubSubClient.h>

// Thông tin WiFi
const char* ssid = "SSIoT-02";
const char* password = "SSIoT-02";

// Địa chỉ MQTT Broker (IP của Raspberry Pi)
const char* mqtt_server = "172.20.10.5"; // <-- Thay đúng IP Pi bạn đang dùng

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println("Kết nối WiFi...");

  WiFi.mode(WIFI_STA);               // RẤT QUAN TRỌNG: Đặt ESP32 ở chế độ station
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi đã kết nối");
  Serial.print("Địa chỉ IP ESP32: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Kết nối MQTT đến ");
    Serial.print(mqtt_server);
    Serial.print(" ... ");

    // Cố gắng kết nối
    if (client.connect("ESP32Client")) {
      Serial.println("thành công!");
    } else {
      Serial.print("Thất bại, mã lỗi = ");
      Serial.println(client.state());
      delay(2000);  // Chờ rồi thử lại
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);  // Kết nối tới MQTT broker trên Pi
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Giả lập dữ liệu
  float temperature = random(360, 380) / 10.0;
  int heartRate = random(60, 100);

  String payload = "{\"temperature\":" + String(temperature) + ",\"heartRate\":" + String(heartRate) + "}";
  client.publish("patient/data", payload.c_str());

  Serial.println("Đã gửi: " + payload);
  delay(5000);
}