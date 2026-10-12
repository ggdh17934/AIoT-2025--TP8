// TP8: send a real quantized mock image; Python runs inference and replies.
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>
#include "image_data.h"

const char *WIFI_SSID = "Wokwi-GUEST";
const char *WIFI_PASSWORD = "";
const char *MQTT_HOST = "broker.mqtt.cool"; // classroom demonstration
const int BUTTON_PIN = 4;
WiFiClient network;
PubSubClient mqtt(network);
LiquidCrystal_I2C lcd(0x27, 16, 2);
String deviceId;
bool previousButton = false;
int imageIndex = 0;
unsigned long requestId = 0;
unsigned long sentAt = 0;
unsigned long lastReconnect = 0;
unsigned long reconnectDelay = 1000;

void onMessage(char *topic, byte *payload, unsigned int length) {
  JsonDocument response;
  if (deserializeJson(response, payload, length)) return;
  if (String(response["device_id"].as<const char *>()) != deviceId) return;
  if (response["request_id"].as<unsigned long>() != requestId) return;
  const char *name = response["class_name"];
  if (!name) return;
  lcd.clear(); lcd.print("Prediction:");
  lcd.setCursor(0, 1); lcd.print(name);
  Serial.printf("Class=%s Round-trip_ms=%lu\n", name, millis() - sentAt);
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT);
  Wire.begin(21, 22);
  lcd.init(); lcd.backlight(); lcd.print("Connecting...");
  deviceId = "ghanabzia-tp8-" + String(uint32_t(ESP.getEfuseMac()), HEX);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  mqtt.setServer(MQTT_HOST, 1883);
  mqtt.setCallback(onMessage);
  mqtt.setBufferSize(8192); // 784 JSON pixels are much larger than default 256 bytes.
  mqtt.setSocketTimeout(2);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) { delay(10); return; }
  if (!mqtt.connected()) {
    if (millis() - lastReconnect < reconnectDelay) return;
    lastReconnect = millis();
    if (mqtt.connect(deviceId.c_str())) {
      mqtt.subscribe("esp32/control", 1);
      reconnectDelay = 1000;
      lcd.clear(); lcd.print("Press button");
    } else {
      reconnectDelay = min(reconnectDelay * 2, 30000UL);
      return;
    }
  }
  mqtt.loop();
  const bool pressed = digitalRead(BUTTON_PIN) == HIGH;
  if (pressed && !previousButton) {
    JsonDocument message;
    requestId = millis();
    message["device_id"] = deviceId;
    message["request_id"] = requestId;
    JsonArray pixels = message["encoded_image"].to<JsonArray>();
    for (int i = 0; i < 784; ++i) pixels.add(int(image_data[imageIndex][i]));
    String payload;
    serializeJson(message, payload);
    sentAt = millis();
    if (mqtt.publish("esp32/data", payload.c_str())) {
      Serial.printf("Sent image=%d True=%s JSON bytes=%u\n", imageIndex,
                    class_names[label_list[imageIndex]], payload.length());
      lcd.clear(); lcd.print("Waiting for AI");
      imageIndex = (imageIndex + 1) % NUM_IMAGES;
    } else Serial.println("Publish failed");
    delay(50);
  }
  previousButton = pressed;
  delay(10);
}
