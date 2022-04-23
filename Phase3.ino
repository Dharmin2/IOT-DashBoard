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
#include <SPI.h>
#include <MFRC522.h>
#include "DHT.h"

#define LIGHT_SENSOR_PIN  36  // ESP32 pin GIOP36 (ADC0) connected to light sensor
#define DHT11PIN 16
#define SS_PIN  5  // ESP32 pin GIOP5 
#define RST_PIN 27 // ESP32 pin GIOP27 

MFRC522 rfid(SS_PIN, RST_PIN);
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
unsigned long uid;
String rfidVal;
char rfidChar[50];
WiFiClient vanieriot;
PubSubClient client(vanieriot);
unsigned long previousMillis = 0;
unsigned long interval = 30000;
boolean scanned = false;
void setup() {
  Serial.begin(115200);
  initWiFi();
  SPI.begin(); // init SPI bus
  rfid.PCD_Init(); // init MFRC522
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
    if(rfid.PICC_IsNewCardPresent()) {
   uid = getID();
  if(uid != -1 && scanned == false){
    Serial.print("Card detected, UID: "); Serial.println(uid);
    if (client.connect("vanieriot", mqttUser, mqttPassword)) {  
      rfidVal = String(uid);
      rfidVal.toCharArray(rfidChar, rfidVal.length() + 1);
      client.publish("IoTLab/rfid",rfidChar);
      scanned = true;
    }
  }
}
  }
  if (scanned == true) {
      int analogValue = analogRead(LIGHT_SENSOR_PIN);
      lightVal = String(analogValue);
      lightVal.toCharArray(light, lightVal.length() + 1);
      Serial.print(rfidChar);
      //Serial.println("Analog Value = ");
      Serial.println(analogValue);
      float humi = dht.readHumidity();
      float temp = dht.readTemperature();
      char tempArr [8];
      char humArr [8];
      dtostrf(temp, 6, 2, tempArr);
      dtostrf(humi, 6, 2, humArr);
      Serial.print(temp);
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

unsigned long getID(){
  if ( !rfid.PICC_ReadCardSerial()) { //Since a PICC placed get Serial and continue
    return -1;
  }
  unsigned long hex_num = 0;
  hex_num =  rfid.uid.uidByte[0] << 24;
  hex_num += rfid.uid.uidByte[1] << 16;
  hex_num += rfid.uid.uidByte[2] <<  8;
  hex_num += rfid.uid.uidByte[3];
  rfid.PICC_HaltA(); // Stop reading
  return hex_num;
}
