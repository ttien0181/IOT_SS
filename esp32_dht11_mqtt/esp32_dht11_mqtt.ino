#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <DHT.h>

// WiFi credentials
const char* ssid = "SSIoT-02";
const char* password = "SSIoT-02";

// MQTT Broker settings
// const char* mqtt_server = "5c5eba53f92a499ca18b75d10b64c1b8.s1.eu.hivemq.cloud";
const char* mqtt_server = "192.168.72.94";
const int mqtt_port = 1883;
// const char* mqtt_user = "dht11_user";
// const char* mqtt_password = "K6_RR9@M2yr2X4w";
// const char* mqtt_client_id = "ESP32_DHT11_Client";

// MQTT topics
const char* temperature_topic = "sensor/temperature";
const char* humidity_topic = "sensor/humidity";


// DHT11 settings
#define DHTPIN 14
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// Create WiFiClientSecure and PubSubClient
WiFiClientSecure espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;

void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi...");
  WiFi.mode(WIFI_STA); 
  WiFi.begin(ssid, password);
  unsigned long wifiTimeout = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiTimeout < 10000) {  // Timeout 10 giây
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected");
    Serial.println("IP address: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (unsigned int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

void reconnect() {
  while (!client.connected() && WiFi.status() == WL_CONNECTED) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);  // Đợi DHT11 ổn định
  dht.begin();
  setup_wifi();

  // Skip CA from HiveMQ (for testing only)
  // espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  // client.setCallback(callback);

}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, attempting to reconnect...");
    setup_wifi();
  }

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 5000) {  // Gửi dữ liệu mỗi 5 giây
    lastMsg = now;

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    // Publish temperature
    char temp_str[10];
    dtostrf(temperature, 6, 2, temp_str);
    bool temp_success = client.publish(temperature_topic, temp_str);

    // Publish humidity
    char hum_str[10];
    dtostrf(humidity, 6, 2, hum_str);
    bool hum_success = client.publish(humidity_topic, hum_str);

    Serial.printf("Temperature: %s °C, Humidity: %s %%\n", temp_str, hum_str);
    Serial.println(temp_success ? "Temperature published" : "Failed to publish temperature");
    Serial.println(hum_success ? "Humidity published" : "Failed to publish humidity");

  }
}