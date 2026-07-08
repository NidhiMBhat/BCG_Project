#include <Wire.h>
#include <MPU6050.h>
#include <DHT.h>
#include <math.h>
#include <WiFi.h>

// ===================== Wi-Fi Credentials =====================
const char* ssid = "ShashDELL";
const char* password = "hotspot123";

// ===================== Static IP Configuration =====================
// WARNING: Change these to match your specific router's subnet!
IPAddress local_IP(192, 168, 137, 150);
IPAddress gateway(192, 168, 137, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);

// ===================== Network Objects =======================
// Start TCP Server on port 5000
WiFiServer server(5000);
WiFiClient client;

MPU6050 mpu;
DHT dht(26, DHT11);

// ===================== Hardware Pins =====================
const int BUZZER_PIN = 25;
const int IR_PIN = 27;

unsigned long lastSample = 0;
const unsigned long SAMPLE_PERIOD_US = 10000; // 100 Hz

enum SystemMode { MODE_LIVE, MODE_BRADYCARDIA, MODE_TACHYCARDIA };
SystemMode currentMode = MODE_LIVE;
unsigned long simStartTime = 0;

float temperature = NAN;
float humidity = NAN;
unsigned long lastDHTRead = 0;

int16_t getSyntheticBCG(unsigned long t_ms, float bpm) {
  float period_ms = (60.0 / bpm) * 1000.0;
  float phase = fmod((float)t_ms, period_ms);
  float wave = 0.0;
  wave += 800.0 * exp(-pow((phase - 150.0) / 30.0, 2));  
  wave -= 400.0 * exp(-pow((phase - 100.0) / 20.0, 2));  
  wave -= 500.0 * exp(-pow((phase - 210.0) / 35.0, 2));  
  wave += random(-50, 50);
  return (int16_t)wave;
}

void handleBuzzer(unsigned long t_ms, float bpm) {
  float period_ms = (60.0 / bpm) * 1000.0;
  float phase = fmod((float)t_ms, period_ms);
  if (phase > 130.0 && phase < 180.0) { tone(BUZZER_PIN, 1000); } 
  else { noTone(BUZZER_PIN); }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  mpu.initialize();
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
  mpu.setDLPFMode(MPU6050_DLPF_BW_10);
  
  pinMode(BUZZER_PIN, OUTPUT); digitalWrite(BUZZER_PIN, LOW);
  pinMode(IR_PIN, INPUT);
  dht.begin();
  randomSeed(analogRead(0));

  // ===================== Wi-Fi Setup =====================
  Serial.print("Connecting to Wi-Fi");
  
  // Explicitly configure Wi-Fi to automatically reconnect if the signal drops
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true); 

  // Apply Static IP Configuration before connecting
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS)) {
    Serial.println("\nFailed to configure Static IP!");
  }

  WiFi.begin(ssid, password);

  // Wait for initial connection before starting the server
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWi-Fi Connected!");
  Serial.print("ESP32 Static IP Address: ");
  Serial.println(WiFi.localIP());

  // Start the TCP server
  server.begin();
  Serial.println("TCP Server started on port 5000. Waiting for laptop client...");
}

void loop() {
  // ===================== Network Handling =====================
  // Check if a new client is trying to connect
  if (server.hasClient()) {
    // If we don't have an active client, accept the new one
    if (!client || !client.connected()) {
      if (client) client.stop(); // Clean up old client state
      client = server.available();
      Serial.println("New laptop client connected!");
    } else {
      // If we already have a client connected, cleanly reject the new connection
      WiFiClient newClient = server.available();
      newClient.stop();
    }
  }

  // Check for incoming simulation commands from the active TCP connection
  if (client && client.connected() && client.available() > 0) {
    char cmd = client.read();
    if (cmd == 'N') { currentMode = MODE_LIVE; noTone(BUZZER_PIN); } 
    else if (cmd == 'B') { currentMode = MODE_BRADYCARDIA; simStartTime = millis(); } 
    else if (cmd == 'T') { currentMode = MODE_TACHYCARDIA; simStartTime = millis(); }
  }

  // ===================== Main Sampling Loop =====================
  unsigned long now = micros();

  // Maintain strict 100Hz timing (10,000 us)
  if (now - lastSample >= SAMPLE_PERIOD_US) {
    lastSample += SAMPLE_PERIOD_US;
    unsigned long currentMillis = millis();
    int16_t ax = 0, ay = 0, az = 0;

    if (currentMode == MODE_LIVE) {
      int16_t gx, gy, gz;
      mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    } 
    else if (currentMode == MODE_BRADYCARDIA) {
      float targetBPM = 42.0;
      int16_t baseWave = getSyntheticBCG(currentMillis - simStartTime, targetBPM);
      az = baseWave; ax = (int16_t)(baseWave * 0.85); ay = (int16_t)(baseWave * 0.90);
      handleBuzzer(currentMillis - simStartTime, targetBPM);
    } 
    else if (currentMode == MODE_TACHYCARDIA) {
      float targetBPM = 145.0;
      int16_t baseWave = getSyntheticBCG(currentMillis - simStartTime, targetBPM);
      az = baseWave; ax = (int16_t)(baseWave * 0.80); ay = (int16_t)(baseWave * 0.85);
      handleBuzzer(currentMillis - simStartTime, targetBPM);
    }

    // Active-low IR logic
    int occupancy = (digitalRead(IR_PIN) == LOW) ? 1 : 0;

    // Maintain original DHT timing
    if (millis() - lastDHTRead > 2000) {
      lastDHTRead = millis();
      float t = dht.readTemperature(); float h = dht.readHumidity();
      if (!isnan(t)) temperature = t;
      if (!isnan(h)) humidity = h;
    }

    // ===================== Data Transmission =====================
    // Only attempt to transmit if the Wi-Fi client is actively connected.
    // If disconnected, this block is skipped, but sampling logic continues unaffected.
    if (client && client.connected()) {
      client.print(currentMillis); client.print(",");
      client.print(ax); client.print(",");
      client.print(ay); client.print(",");
      client.print(az); client.print(",");
      client.print(occupancy); client.print(",");
      client.print(temperature); client.print(",");
      client.println(humidity);
    }
  }
}