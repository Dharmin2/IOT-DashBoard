/*
 * This ESP32 code is created by esp32io.com
 *
 * This ESP32 code is released in the public domain
 *
 * For more detail (instruction and wiring diagram), visit https://esp32io.com/tutorials/esp32-light-sensor
 */

// The below are constants, which cannot be changed
#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

#define LIGHT_SENSOR_PIN  36  // ESP32 pin GIOP36 (ADC0) connected to light sensor
#define DHT11PIN 16

DHT dht(DHT11PIN, DHT11);
const char* ssid = "VideotronWifi800";
const char* password = "18021885";

const char* mqtt_server = "10.0.0.103";
const char* mqttUser = "Dharmin";
const char* mqttPassword = "1234";
String lightVal;
char light[50];
String tempVal;
char tempchar[50];
String humiVal;
char humichar[50];

WiFiClient vanieriot;
PubSubClient client(vanieriot);

unsigned long previousMillis = 0;
unsigned long interval = 30000;
void setup() {
  Serial.begin(115200);
  initWiFi();
  dht.begin();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
    delay(5000);
  }
    unsigned long currentMillis = millis();
  // if WiFi is down, try reconnecting every CHECK_WIFI_TIME seconds
  if ((WiFi.status() != WL_CONNECTED) && (currentMillis - previousMillis >=interval)) {
    Serial.print(millis());
    Serial.println("Reconnecting to WiFi...");
    WiFi.disconnect();
    WiFi.reconnect();
    previousMillis = currentMillis;
  }
  else {
      int analogValue = analogRead(LIGHT_SENSOR_PIN);
      lightVal = String(analogValue);
      lightVal.toCharArray(light, lightVal.length() + 1);
      //Serial.println("Analog Value = ");
      Serial.println(analogValue);
      float humi = dht.readHumidity();
      float temp = dht.readTemperature();
      char tempArr [8];
      char humArr [8];
      dtostrf(temp, 6, 2, tempArr);
      dtostrf(humi, 6, 2, humArr);
      Serial.print("Temperature: ");
      Serial.print(temp);
      Serial.print("ºC ");
      Serial.print("Humidity: ");
      Serial.println(humi);
    if (client.connect("vanieriot", mqttUser, mqttPassword)) {  
      delay(5000);
      client.publish("IoTLab/light",light);
      client.publish("IoTLab/humi",humArr);
      client.publish("IoTLab/temp",tempArr);
    }
  }
}

void initWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi ..");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(1000);
  }
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
      if (client.connect("vanieriot", mqttUser, mqttPassword)) {
      Serial.println("connected");  
    } else {
      delay(5000);
    }
  }
}
