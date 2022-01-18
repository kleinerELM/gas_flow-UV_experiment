#include <Arduino.h>

#define MAX_BUFF_LEN 255
#define relais_pin   D1

String str;
uint8_t idx = 0;

void setup() {
  pinMode(relais_pin, OUTPUT);
  Serial.begin(115200);
  delay(500);
  Serial.println("Hi Torbi!");
  Serial.println("On");
  digitalWrite(relais_pin, HIGH);
  delay(1000);
  Serial.println("Off");
  digitalWrite(relais_pin, LOW);
  delay(1000);
}

void loop() {
  if (Serial.available() > 0) {
    str = Serial.readString();
    str.trim();
    Serial.print( "Received: [" );
    Serial.print(str);
    Serial.println("]");
    if (str == "On") {
      Serial.println("Turning relais on");
      digitalWrite(relais_pin, HIGH);
    } else if (str == "Off") {
      Serial.println("Turning relais off");
      digitalWrite(relais_pin, LOW);
    }
  }
}