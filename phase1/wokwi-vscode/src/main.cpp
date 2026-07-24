#include <Arduino.h>
/*
 * MASAISAI Phase-1 sensing node (Wokwi simulation)
 * ------------------------------------------------
 * One physical Wokwi ESP32 simulates a NETWORK of NUM_NODES independent
 * sensing nodes (matches the proposal's "network of low-cost RF sensing
 * nodes" story without needing NUM_NODES separate simulator instances):
 *   - The slide potentiometer stands in for the licensed broadcaster's TX
 *     power as seen region-wide. Slide up = broadcaster transmitting.
 *   - Each simulated node has its own fixed path-loss ATTEN_DB offset
 *     (0-18 dB), mirroring the per-node attenuation model
 *     src/sensing_sim.py trains the occupancy model on - nodes further
 *     from the broadcaster see weaker RSSI for the same underlying
 *     occupancy state, exactly like real deployment geometry would.
 *   - Each node also scans the UHF DTT channel list independently
 *     (offset starting position), so the dashboard shows a live,
 *     staggered multi-node/multi-channel scan.
 *   - OLED + LEDs reflect the shared underlying broadcaster state read
 *     from the pot (not any one simulated node individually).
 *
 * MQTT topic:  masaisai/sensing/<node_id>  (one publish per node per tick)
 * Publish period: every 3 seconds, all NUM_NODES nodes publish each tick.
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
const char* MQTT_PASSW = "CHANGE_ME_NODE_PASSWORD";   // set after VPS setup - never commit the real one

// ---------- Simulated node network ----------
const int NUM_NODES = 10;
const char* NODE_IDS[NUM_NODES] = {
  "wokwi-node-01", "wokwi-node-02", "wokwi-node-03", "wokwi-node-04", "wokwi-node-05",
  "wokwi-node-06", "wokwi-node-07", "wokwi-node-08", "wokwi-node-09", "wokwi-node-10",
};
// Fixed per-node path-loss offset (dB) - simulates each node sitting at a
// different distance from the broadcaster. Deterministic (not random per
// boot) so the demo is reproducible run to run.
const float NODE_ATTEN_DB[NUM_NODES] = {0, 2, 4, 6, 8, 10, 12, 14, 16, 18};

// Each node scans across these UHF DTT channels in turn (same CH21-CH40
// range the occupancy model was trained on - see src/sensing_sim.py
// CHANNELS), one channel per publish cycle, round-robin. Nodes start at
// staggered offsets so they aren't all reading the same channel at once.
const int CHANNELS[]   = {21, 23, 27, 31, 36, 40};
const int NUM_CHANNELS = sizeof(CHANNELS) / sizeof(CHANNELS[0]);
int channelIdx[NUM_NODES];

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

float readRssiDbm(float attenDb) {
  // Map pot 0..4095 -> -100 dBm .. -40 dBm (region-wide broadcaster signal),
  // then apply this node's fixed path-loss offset, plus small sensor noise.
  int raw = analogRead(PIN_RF_POT);
  float base = -100.0 + (raw / 4095.0) * 60.0;
  float noise = (random(-150, 150)) / 100.0;  // +/-1.5 dB sensor noise
  return base - attenDb + noise;
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
    String cid = String("wokwi-gateway-") + String(random(0xffff), HEX);
    if (!mqtt.connect(cid.c_str(), MQTT_USER, MQTT_PASSW)) delay(1000);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_OCC, OUTPUT);
  pinMode(PIN_LED_IDLE, OUTPUT);
  for (int i = 0; i < NUM_NODES; i++) channelIdx[i] = i % NUM_CHANNELS;
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

    // Region-wide broadcaster state, read once per tick so every node's
    // occupancy call is consistent with the others this cycle.
    int potRaw = analogRead(PIN_RF_POT);
    float baseRssi = -100.0 + (potRaw / 4095.0) * 60.0;
    bool broadcasterActive = baseRssi > OCCUPIED_THRESHOLD_DBM;
    digitalWrite(PIN_LED_OCC, broadcasterActive ? HIGH : LOW);
    digitalWrite(PIN_LED_IDLE, broadcasterActive ? LOW : HIGH);

    int occupiedCount = 0;
    int lastChannel = 0;
    float lastRssi = 0;

    for (int i = 0; i < NUM_NODES; i++) {
      int channel = CHANNELS[channelIdx[i]];
      channelIdx[i] = (channelIdx[i] + 1) % NUM_CHANNELS;

      float rssi = readRssiDbm(NODE_ATTEN_DB[i]);
      bool occupied = rssi > OCCUPIED_THRESHOLD_DBM;
      float conf = sensingConfidence(rssi);
      if (occupied) occupiedCount++;

      char payload[220];
      snprintf(payload, sizeof(payload),
        "{\"node_id\":\"%s\",\"channel\":%d,\"rssi_dbm\":%.1f,"
        "\"occupied\":%d,\"sensing_confidence\":%.2f,\"seq\":%d}",
        NODE_IDS[i], channel, rssi, occupied ? 1 : 0, conf, readingId);

      char topic[64];
      snprintf(topic, sizeof(topic), "masaisai/sensing/%s", NODE_IDS[i]);
      mqtt.publish(topic, payload);
      Serial.println(payload);
      mqtt.loop();

      lastChannel = channel;
      lastRssi = rssi;
    }

    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("MASAISAI sensing network");
    display.print(NUM_NODES); display.print(" nodes  seq "); display.println(readingId);
    display.print("last: CH "); display.print(lastChannel);
    display.print(" "); display.print(lastRssi, 1); display.println(" dBm");
    display.print("occupied: "); display.print(occupiedCount);
    display.print("/"); display.println(NUM_NODES);
    display.setTextSize(2);
    display.setCursor(0, 42);
    display.println(broadcasterActive ? "ACTIVE" : "IDLE");
    display.setTextSize(1);
    display.display();
  }
}
