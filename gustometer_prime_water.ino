/*
 * gustoPrimeWater
 * open serial monitor at top right (select NL and CR line
 * endings), type in port to prime and press enter.
 * Servo will move to correct port, then press and hold button
 * til solution starts to come out (and no bubbles in line)
 */


int servoPosArr[]= {7, 19, 26}; //{0, 85, 160}; //{40,124,75};//,90,45,21};//{170,132,93,56,20}; //{20,55,92,132,170};
long drainDur = 100; // valve open duration in ms

/////////// pins
int buttonPin = 8; //A4;  // 
int servoPin = 7; //11;

int solPin1 = 6; //12; //4;
int solPin2 = 5; //8; //5;
//int solPin3 = 6;
//int solPin4 = 9; //8;
//int solPin5 = 5; //7;
int solPin = 6; //7;

int port = 0;

// servo
#include <Servo.h>
Servo spoutServo;  // create servo object to control a servo
int pos = 0;    // variable to store the servo position


String inputString = "";
boolean stringComplete = false;  // whether the string is complete


void setup() {
   Serial.begin(115200);

   //valves
   pinMode(solPin1,OUTPUT);
   pinMode(solPin2,OUTPUT);
//   pinMode(solPin3,OUTPUT);
//   pinMode(solPin4,OUTPUT);
//   pinMode(solPin5,OUTPUT);
  
   pinMode(buttonPin, INPUT_PULLUP);

  // servo4
   
  spoutServo.attach(servoPin);


}

void loop() {
  if (digitalRead(buttonPin)==LOW) {
    digitalWrite(solPin, HIGH);
    Serial.print(port);
    Serial.println(" valveOPEN");
    delay(drainDur);
  }
  else {digitalWrite(solPin, LOW);}
}


void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;

    //fadeVal = inputString.toInt();
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      stringComplete = true;
      Serial.println(inputString);
      port = inputString.toInt()-1;
      pos = servoPosArr[port];
      //fadeVal = map(fadeVal, 0, 100, 0, 255);
      inputString = "";
      spoutServo.write(pos);

      if (port==0) {
        solPin = solPin1;
      }
      else if (port==1) {
        solPin = solPin2;
      }
//      else if (port==2) {
//        solPin = solPin3;
//      }
//      else if (port==3) {
//        solPin = solPin4;
//      }
//      else if (port==4) {
//        solPin = solPin5;
//      }
      
    }
  }
}
