#include <Arduino.h>
/*
 * MASAISAI Phase-1 sensing node (Wokwi simulation)
 * ------------------------------------------------
 * Simulates one RF sensing node from the MASAISAI proposal:
 *   - The slide potentiometer stands in for received RF energy on the
 *     monitored UHF DTT channel (i.e. the licensed broadcaster's TX power
 *     as seen by this node). Slide up = broadcaster transmitting.
 *   - The node computes RSSI (dBm), occupancy and sensing confidence and
 *     publishes a JSON reading over MQTT to the MASAISAI ingestion service,
 *     exactly like a real RTL-SDR node would in the Phase 1 pilot.
 *   - OLED shows live channel state; red LED = occupied, green = idle.
 *
 * MQTT topic:  masaisai/sensing/<node_id>
 * Publish period: every 3 seconds.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ---------- Config ----------
const char* WIFI_SSID  = "Wokwi-GUEST";
const char* WIFI_PASS  = "";

const char* MQTT_HOST  = "38.247.146.172";   // MASAISAI VPS
const int   MQTT_PORT  = 1883;
const char* MQTT_USER  = "masaisai_node";
const char* MQTT_PASSW = "CHANGE_ME_NODE_PASSWORD";   // set after VPS setup

const char* NODE_ID    = "wokwi-node-01";
const int   CHANNEL    = 23;                 // simulated UHF DTT channel

const int PIN_RF_POT   = 34;   // slide pot = RF energy on channel
const int PIN_LED_OCC  = 25;   // red: channel occupied
const int PIN_LED_IDLE = 26;   // green: channel idle

// Energy-detection threshold, mirroring sensing_sim.py's model:
// idle floor around -95 dBm, active broadcast around -55 dBm.
const float OCCUPIED_THRESHOLD_DBM = -75.0;

Adafruit_SSD1306 display(128, 64, &Wire, -1);
WiFiClient espClient;
PubSubClient mqtt(espClient);

unsigned long lastPublish = 0;
int readingId = 0;

float readRssiDbm() {
  // Map pot 0..4095 -> -100 dBm .. -40 dBm, plus small Gaussian-ish noise
  int raw = analogRead(PIN_RF_POT);
  float base = -100.0 + (raw / 4095.0) * 60.0;
  float noise = (random(-150, 150)) / 100.0;  // +/-1.5 dB sensor noise
  return base + noise;
}

float sensingConfidence(float rssi) {
  // Confidence drops near the decision threshold (ambiguous zone),
  // mirroring the fail-safe design in constraint_engine.py
  float dist = fabs(rssi - OCCUPIED_THRESHOLD_DBM);
  float conf = 0.55 + (dist / 40.0);
  if (conf > 0.99) conf = 0.99;
  return conf;
}

void connectWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(300); }
}

void connectMqtt() {
  while (!mqtt.connected()) {
    String cid = String(NODE_ID) + "-" + String(random(0xffff), HEX);
    if (!mqtt.connect(cid.c_str(), MQTT_USER, MQTT_PASSW)) delay(1000);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_OCC, OUTPUT);
  pinMode(PIN_LED_IDLE, OUTPUT);
  Wire.begin(21, 22);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("MASAISAI node boot...");
  display.display();

  connectWifi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  connectMqtt();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWifi();
  if (!mqtt.connected()) connectMqtt();
  mqtt.loop();

  if (millis() - lastPublish >= 3000) {
    lastPublish = millis();
    readingId++;

    float rssi = readRssiDbm();
    bool occupied = rssi > OCCUPIED_THRESHOLD_DBM;
    float conf = sensingConfidence(rssi);

    digitalWrite(PIN_LED_OCC, occupied ? HIGH : LOW);
    digitalWrite(PIN_LED_IDLE, occupied ? LOW : HIGH);

    char payload[220];
    snprintf(payload, sizeof(payload),
      "{\"node_id\":\"%s\",\"channel\":%d,\"rssi_dbm\":%.1f,"
      "\"occupied\":%d,\"sensing_confidence\":%.2f,\"seq\":%d}",
      NODE_ID, CHANNEL, rssi, occupied ? 1 : 0, conf, readingId);

    char topic[64];
    snprintf(topic, sizeof(topic), "masaisai/sensing/%s", NODE_ID);
    mqtt.publish(topic, payload);
    Serial.println(payload);

    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("MASAISAI sensing node");
    display.print("CH "); display.print(CHANNEL);
    display.print("  seq "); display.println(readingId);
    display.print("RSSI: "); display.print(rssi, 1); display.println(" dBm");
    display.print("conf: "); display.println(conf, 2);
    display.setTextSize(2);
    display.setCursor(0, 42);
    display.println(occupied ? "OCCUPIED" : "IDLE");
    display.setTextSize(1);
    display.display();
  }
}
