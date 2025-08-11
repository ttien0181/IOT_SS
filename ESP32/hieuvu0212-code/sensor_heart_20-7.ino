#include <WiFi.h>
#include <PubSubClient.h>

#define heartbeat_sensor 34
#define samp_siz 4
#define rise_threshold 5

const char* ssid = "SSIoT-02";
const char* password = "SSIoT-02";
const char* mqtt_server = "192.168.72.94";

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println("Kết nối WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print("...");
  }
  Serial.println("\nWiFi đã kết nối");
  Serial.print("Địa chỉ IP ESP32: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // Kiểm tra và tái kết nối MQTT khi bị ngắt kết nối
  while (!client.connected()) {
    Serial.print("Kết nối MQTT đến ");
    Serial.print(mqtt_server);
    Serial.print(" ... ");
    if (client.connect("ESP32Client")) {
      Serial.println("thành công!");
    } else {
      Serial.print("Thất bại, mã lỗi = ");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);  // Thiết lập server MQTT
}

void loop() {
  if (!client.connected()) {
    reconnect();  // Kiểm tra và kết nối lại nếu mất kết nối
  }

  client.loop();  // Đảm bảo client.loop() được gọi liên tục để duy trì kết nối MQTT
  
  // Gọi hàm đo nhịp tim và gửi dữ liệu qua MQTT
  hearbeat_reading();
}

void hearbeat_reading() {
  static float reads[samp_siz], sum;
  static long int now, ptr;
  static float last, reader, start;
  static float first = 0, second = 0, third = 0, before = 0, print_value = 0;
  static bool rising = false;
  static int rise_count = 0;
  static int n;
  static long int last_beat = 0;

  static unsigned long last_sent_time = 0; // Lưu thời gian gửi dữ liệu cuối cùng
  static unsigned long interval = 1000;    // Gửi mỗi 1 giây

  // Cập nhật mảng giá trị reads
  for (int i = 0; i < samp_siz; i++) {
    reads[i] = 0;
  }

  sum = 0;
  ptr = 0;

  // Đọc trực tiếp từ cảm biến
  reader = analogRead(heartbeat_sensor);  // Đọc tín hiệu từ cảm biến

  // Kiểm tra nếu giá trị đọc hợp lệ, tránh giá trị 0 hoặc nhiễu quá cao
  if (reader < 50) {  // Thay đổi ngưỡng nếu cần thiết
    reader = 0; // Nếu giá trị đọc quá nhỏ, coi như không có tín hiệu
  }

  sum -= reads[ptr];
  sum += reader;
  reads[ptr]   = reader;
  last = sum / samp_siz;

  // Kiểm tra sự thay đổi của tín hiệu để phát hiện nhịp tim
  if (last > before) {
    rise_count++;
    if (!rising && rise_count > rise_threshold) {
      rising = true;
      first = millis() - last_beat;
      last_beat = millis();
      print_value = 60000. / (0.4 * first + 0.3 * second + 0.3 * third);

      // Đảm bảo không tính nhịp tim quá thấp hoặc quá cao
      if (print_value < 60 || print_value > 200) {
        Serial.println("Heart rate abnormal");
        print_value = 0; // Xử lý khi nhịp tim không hợp lý
      }

      third = second;
      second = first;
    }
  } else {
    rising = false;
    rise_count = 0;
  }

  before = last;
  ptr++;
  ptr %= samp_siz;

  // Gửi dữ liệu MQTT mỗi 1 giây
  if (millis() - last_sent_time >= interval) {
    last_sent_time = millis();  // Cập nhật thời gian gửi dữ liệu lần cuối

    if (print_value < 60) {
      Serial.println("Heart rate low");
      client.publish("sensor/heartbeat", "Heart rate low");
    } else {
      Serial.print("Nhịp tim: ");
      Serial.println(print_value);

      // Chuyển giá trị float thành chuỗi để gửi qua MQTT
      char msg[10];
      dtostrf(print_value, 4, 1, msg);  // Chuyển float thành chuỗi
      client.publish("sensor/heartbeat", msg);
    }
  }

  // Cho phép MQTT xử lý (gửi và nhận dữ liệu)
  client.loop();
}
