#define BLYNK_TEMPLATE_ID "TMPL6jeYP-hE-"
#define BLYNK_TEMPLATE_NAME "cambiennhiptim"
#define BLYNK_AUTH_TOKEN "X4rcNrJtRgD1og8JLiE2it7FqaZLa56i"

#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>

char ssid[] = "Tuan Minh";
char pass[] = "30052008";

#define HEART_SENSOR_PIN 34
#define BUZZER_PIN 27

#define SAMP_SIZ 4
#define RISE_THRESHOLD 5

float reads[SAMP_SIZ];
float sum = 0;
int ptr = 0;

float first = 0, second = 0, third = 0;
float before = 0;
unsigned long last_beat = 0;

bool rising = false;
int rise_count = 0;

bool measureEnabled = false;

BlynkTimer timer;

// Biến dùng cho đọc trung bình tín hiệu trong 20ms không blocking
unsigned long avgStartTime = 0;
int avgSamples = 0;
float avgReader = 0;
bool isAveraging = false;

// Nút bật tắt cảm biến nhịp tim trên app Blynk (V0)
BLYNK_WRITE(V0) {
  int value = param.asInt();
  measureEnabled = (value == 1);

  if (!measureEnabled) {
    digitalWrite(BUZZER_PIN, LOW);
    Blynk.virtualWrite(V1, 0);
    Serial.println("Ngừng đo nhịp tim.");
  } else {
    Serial.println("Bắt đầu đo nhịp tim...");
    // Reset lại các biến khi bắt đầu đo
    for (int i = 0; i < SAMP_SIZ; i++) reads[i] = 0;
    sum = 0;
    ptr = 0;
    first = second = third = 0;
    before = 0;
    last_beat = millis();
    rising = false;
    rise_count = 0;

    avgStartTime = 0;
    avgSamples = 0;
    avgReader = 0;
    isAveraging = false;
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  WiFi.begin(ssid, pass);
  Serial.print("Kết nối WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi kết nối thành công");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  Blynk.config(BLYNK_AUTH_TOKEN);
  Blynk.connect();

  // Gọi hàm đọc nhịp tim mỗi 10ms để thực hiện trung bình 20ms trong nhiều lần gọi
  timer.setInterval(10L, hearbeat_reading);
}

void loop() {
  Blynk.run();
  timer.run();
}

// Hàm đo nhịp tim, chạy từng bước, không block
void hearbeat_reading() {
  if (!measureEnabled) return;

  unsigned long now = millis();

  if (!isAveraging) {
    // Bắt đầu chu kỳ lấy mẫu trung bình 20ms
    avgStartTime = now;
    avgSamples = 0;
    avgReader = 0;
    isAveraging = true;
  }

  if (isAveraging) {
    // Đọc mẫu sensor
    avgReader += analogRead(HEART_SENSOR_PIN);
    avgSamples++;

    // Nếu đủ 20ms, tính trung bình và xử lý nhịp tim
    if (now - avgStartTime >= 20) {
      float readerAvg = avgReader / avgSamples;

      // Cập nhật dãy trượt trung bình
      sum -= reads[ptr];
      sum += readerAvg;
      reads[ptr] = readerAvg;
      ptr = (ptr + 1) % SAMP_SIZ;

      float avg = sum / SAMP_SIZ;

      if (avg > before) {
        rise_count++;
        if (!rising && rise_count > RISE_THRESHOLD) {
          rising = true;
          unsigned long interval = now - last_beat;
          last_beat = now;

          first = interval;
          float bpm = 60000.0 / (0.4 * first + 0.3 * second + 0.3 * third);

          if (bpm < 60 || bpm > 180) {
            Serial.print("BPM: ");
            Serial.println((int)bpm);
            Blynk.virtualWrite(V1, (int)bpm);
          } 
          else {
            Serial.print("BPM: ");
            Serial.println((int)bpm);
            Blynk.virtualWrite(V1, (int)bpm);
            if(bpm>100) digitalWrite(BUZZER_PIN, HIGH);
            else digitalWrite(BUZZER_PIN, LOW);

            third = second;
            second = first;
          }
        }
      } else {
        rising = false;
        rise_count = 0;
      }

      before = avg;

      // Kết thúc chu kỳ trung bình 20ms, chuẩn bị cho lần tiếp theo
      isAveraging = false;
    }
  }
}
