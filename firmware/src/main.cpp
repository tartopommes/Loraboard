#include <Arduino.h>
#include <MKRWAN.h>
#include <ArduinoLowPower.h>
#include "arduino_secrets.h"

LoRaModem modem;
String appEui = SECRET_APP_EUI;
String appKey = SECRET_APP_KEY;

#define MAX_EVENT 50
#define MIN_DELAY_BTW_INTERRUPT 500
#define DELAY_BTW_TRANSMIT 10*1000

unsigned long last_packet_time;

volatile int counter = 0;

//interruption
void button_pressed() {
  static unsigned long last_time = 0; //declare var for last time button has been pressed (static declaration)
  unsigned long current_time = millis(); //take current time to prevent multiples click due to bounce
  if (last_time < current_time - MIN_DELAY_BTW_INTERRUPT) { //if last press was more than MIN_DELAY_BTW_INTERRUPT seconds ago
    counter++;
    last_time = current_time;//actualize last press
  }
}


void setup() {
  Serial.begin(115200);

  while (!Serial);
  Serial.println("Starting MKR1310");
  pinMode(PIN_A1, INPUT_PULLUP);
  
  //attachInterrupt(digitalPinToInterrupt(PIN_A1), button_pressed, RISING);//set interrupt
  LowPower.attachInterruptWakeup(digitalPinToInterrupt(PIN_A1), button_pressed, RISING);

  // setup regional band (eg. US915, AS923, ...)
  if (!modem.begin(US915)) {
    Serial.println("Failed to start module");
    while (1) {}
  };

  Serial.println("Connexion to LoRa network");

  int connected = 0;

  do {
    connected = modem.joinOTAA(appEui, appKey);
    if (!connected)
      Serial.println("Something went wrong; are you indoor? Move near a window and retry");
  } while (!connected);
  
  Serial.println("Sucessfully Connected");
  modem.minPollInterval(60);

  while(millis()<DELAY_BTW_TRANSMIT);
  return;
}


void loop() {
  
  while (counter == 0) {  ////wait for event
    LowPower.deepSleep(); //deep sleep mode for energy saving -> exited after first interrupt
  }

  unsigned long eventTime = millis();
  while (eventTime > millis() - DELAY_BTW_TRANSMIT);//wait delay to transmit

  Serial.print("Sending :");
  Serial.println(counter);
  
  modem.beginPacket();
  modem.write(counter);
  int err = modem.endPacket(true);

  Serial.println(err > 0 ? "Message sent correctly :)":"Error sending message  :(");

  counter=0;//reset counter
  return;
}