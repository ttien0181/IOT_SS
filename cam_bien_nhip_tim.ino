#define heartbeat_sensor 33
#define samp_siz 4
#define rise_threshold 5

float reads[samp_siz];
float sum = 0;
int ptr = 0;

float first = 0, second = 0, third = 0;
float before = 0;
long int last_beat = 0;

bool rising = false;
int rise_count = 0;

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < samp_siz; i++) {
    reads[i] = 0;
  }
}

void loop() {
  static unsigned long last_check = 0;
  if (millis() - last_check >= 30000) {
    last_check = millis();
    hearbeat_reading();  // gọi mỗi 30s
  }
}

void hearbeat_reading() {
  int n = 0;
  float reader = 0;
  unsigned long start = millis();
  unsigned long now;

  do {
    reader += analogRead(heartbeat_sensor);
    n++;
    now = millis();
  } while (now < start + 20);

  reader /= n;

  sum -= reads[ptr];
  sum += reader;
  reads[ptr] = reader;

  float last = sum / samp_siz;

  if (last > before) {
    rise_count++;
    if (!rising && rise_count > rise_threshold) {
      rising = true;
      float interval = millis() - last_beat;
      last_beat = millis();

      first = interval;
      float bpm = 60000. / (0.4 * first + 0.3 * second + 0.3 * third);

      if (bpm < 60) {
        Serial.println("Heart rate low");
      } else {
        Serial.print("BPM: ");
        Serial.println(bpm);
        third = second;
        second = first;
      }
    }
  } else {
    rising = false;
    rise_count = 0;
  }

  before = last;
  ptr = (ptr + 1) % samp_siz;
}
