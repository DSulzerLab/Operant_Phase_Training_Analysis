/*
General info:
Spout position is established with code serialServo

115200 baud both NL & CR

priming code to keep spout open and empty syringe (set to 100ms)

array is where you set the order of the spouts over the number of trials

3 stages
   - phase 0: reward always available, spout entry and available for 30 sec, then 10s ITI
   - phase 1: cue predicts reward delivery, then mult rew
   - phase 2: lever press activates spout entry, then mult rew
   - phase 3: cue predicts lever active, then lever activates spout entry

*/

String programName = "gustoClay_MPR_NAU_leverNeoTone_031023a.ino";
//int trainDay = ?;

int isEthoTrig = 0; // =1 if being triggered by doric (cable must be plugged in or get spurious triggers)
int itiNullPos = 1; // =1 to send servo to null position during ITI
int useCues = 1; // to deliver cues during trial (both light and tone)
int useTone = 1; // to use tone cue (and not only light)

unsigned int iti = 100; // iti in ms
unsigned long trialDur = 10000; // trial duration
int maxNumTrials = 10;
unsigned long sessDur = 300000; // session duration
unsigned long postRewDur = 2000; // duration after reward, before ITI (not used)
long rewAvailDur = 5000; // this should match the tone duration (line 44) and the sync duration (line 125)

int cueDur = 5000; // duration of cue LED/tone in ms
int servoDelay = 100;  // delay from cue start to servo move
int rewTimeout = 100; // timeout for multiple rewards in a trial

int numLicksForRew = 1; //Number of licks to trigger reward (if not using lever)
int maxInterLick = 100; // max inter lick interval for licks in a bout

long forceThresh = 2; // threshold force (g) for lever press

int toneFreq1 = 3000;
int toneDur1 = 5000;
int toneFreq2 = 3000;
int toneDur2 = 5000;

//int isOpto = 0; // whether or not this is opto session
//int percOpto = 50; // percent opto trial (if opto session)

// spout servo positions (determined empirically) - First number is spout 1
int servoPosArr[] = {52, 125, 90}; // for two spout and one null position // increased port3 value by 1 to elim servo hum
int nullPos = 90; // position where no spouts out

int rewDur1 = 100;//90;
int rewDur2 = 100;//320;
int rewDur3 = 100;//70;
int rewDur4 = 100;//90;
int rewDur5 = 100;//120;
int rewDur = 100; // generic solenoid open time in ms (default)

//1 port with servo (if multiple spouts, add numbers)
int trialArray[] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};

// blocks (not using right now?)
//int numTrials = 275; //Set this to the length of the Random Array
//int Blocks = 55; //Blocks are the units to separate out the random order of the 4 ports before repeating, ie. [1,3,2,4] is one block, [4,3,1,2] is another, etc.
//int blockSize = 5;

///PINS//////////////
int buttonPin = 8;  // to start arduino
int doricPin = 4; // to trigger doric
int ledPin = 13; // for sync IR LED
//int optoPin = A0; //4;//12; // TTL for laser trigger (HIGH ON)
int syncPin = 13; //3 sync out from arduino to doric, to attach to interrupt
int servoPin = 7; // servo for spout
int spkPin = 12; // for speaker. Speaker frequency set above, volume is manual on speaker
int neoPin = 11; // pin for Neopixel LED control (visual cue)
int lickPin = 10; // for registering spout touches (licks)

// add here solPin if using more than 2
int solPin1 = 6;
int solPin2 = 5;
int solPin = 6;// for solution delivery after lick (line below specifies that solPin = solPin1)

int irqpin = 2;  // for MPR121 touch sensor interrupt

///////////////////////////

// state/time vars

unsigned long startTime = 0;
int trialNum = 0;
int trialType = 1;
unsigned long trialStartTime = 0;
unsigned long trialEndTime = 0;
unsigned long rewTime = 0;

// lick vars
int prevLick = 0;
//long lickTime = 0;
//long prevLickTime = 0;
int lickState = 0;
int lickStateArr[6];
int numReading = 0;
int lickStateSum = 0;
int justLicked = 0;  // for MPR
int lickThresh = 1;//50; //150; // 5*touch thresh value (for 5 read sum)
int touchVal = 0;
//int hasLicked = 0;

unsigned long lickTime = 0;
unsigned long prevLickTime = 0;
int numLicksInBout = 0;

int rewReset = 1;
int rewOn = 0;

int isIti = 1;
unsigned long itiStartTime = 0;

int isTrial = 0;
int toStart = 0;

// sync pulse params
int syncDur = 5000;  // duration of pulse
int syncIntv = 10000;  // interval of pulse train

unsigned long syncStartTime = 0; // sync vars
unsigned long prevSyncTime = 0;
int prevSync = 0;
unsigned long lastSyncTime = 0;

//Cue start time
long cueStartTime = 0;
int moveServo = 0;
int cueOn = 0;

int giveCue = 0;
int giveTrial = 1;


///////LIBRARIES///////////
// servo
#include <Servo.h>
Servo spoutServo;  // create servo object to control a servo
int pos = 0;    // variable to store the servo position

// MPR121 touch sensor
//#include "mpr121.h"
#include <Wire.h>
//boolean touchStates[12]; //to keep track of the previous touch states

////#include <Wire.h>
#include <Adafruit_NeoPixel.h>
#define PIN        neoPin
#define NUMPIXELS 1
Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

// // Sparkfun NAU7802 load cell sensor
#include "SparkFun_Qwiic_Scale_NAU7802_Arduino_Library.h" // Click here to get the library: http://librarymanager/All#SparkFun_NAU7802
NAU7802 myScale; //Create instance of the NAU7802 class
float calibrationFactor = 12648.50; // adjust to sensitivity of touch sensor
float zeroOffset = -2437132.00; // adjust to bring baseline value to 0

long forceInt = 0;
float force = 0;
int prevLevPress = 0;
unsigned long levPressTime = 0;

/////SETUP///////////////////////////////
void setup() {

  //  randomSeed(analogRead(A1)); // initialize RNG with floating analog pin
  Serial.begin(115200);//9600);

  //valves
  pinMode(solPin1, OUTPUT);
  pinMode(solPin2, OUTPUT);
  //  pinMode(solPin3, OUTPUT);
  //  pinMode(solPin4, OUTPUT);
  //  pinMode(solPin5, OUTPUT);

  //other pins
  //pinMode(ethoTrigPin, INPUT);
  pinMode(doricPin, OUTPUT);
  pinMode(syncPin, OUTPUT); //INPUT if control is from doric to arduino
  //  pinMode(optoPin, OUTPUT); if optogenetic
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);
  //pinMode(lickOutPin, OUTPUT);

  pinMode(lickPin, INPUT);

  // servo
  spoutServo.attach(servoPin);
  spoutServo.write(nullPos);//(servoPosArr[0]);

  // MPR121 touch sensor setup
  pinMode(irqpin, INPUT);
//  digitalWrite(irqpin, HIGH); //enable pullup resistor
  Wire.begin();
//  mpr121_setup();

  // Sparkfun NAU7802 load cell sensor
  if (myScale.begin() == false)
  {
    Serial.println("Scale not detected. Please check wiring. Freezing...");
    while (1);
  }
  Serial.println("Scale detected!");

  pixels.begin(); // initialize NeoPixel LED
  pixels.show();   // Turn OFF all pixels ASAP
  pixels.setBrightness(50); // Set BRIGHTNESS to about 1/5 (max = 255)

  // print out some header info
  Serial.println(programName);
  //  Serial.print("trainDay="); Serial.println(trainDay);
  //  Serial.print("isOpto="); Serial.println(isOpto);
  Serial.println("END HEADER");

}

//////////////////////
void loop() {
  // check for session start condition
  if (toStart == 0 && ((digitalRead(buttonPin) == 0) )) { //|| (isEthoTrig == 1 && digitalRead(ethoTrigPin) == 1))) {
    toStart = 1;
    startTime = millis();
    digitalWrite(doricPin, HIGH);
    Serial.print("START SESSION, ms=");
    Serial.println(startTime);
    delay(100);
    digitalWrite(doricPin, LOW);
}

  // Session loop
  if (toStart == 1) {
    checkTrial();
    checkCues();
    checkServo();
    checkLever();
    checkLicks();
    checkRew();
//    checkSyncState(); // now sync out at trial
  }
}

///////////////////////Sparkfun NAU7802 load cell sensor
void checkLever() {
  if (myScale.available()) {
    force = myScale.getReading();//scale.getWeight();
    force = (force-zeroOffset)/calibrationFactor;
    Serial.print("g=");
    Serial.print(force);
    Serial.print(", ms=");
    Serial.println(millis());

    if (prevLevPress==0 && force>forceThresh) {
      prevLevPress = 1;
      levPressTime = millis();
      Serial.print("levPress, ms=");
      Serial.println(levPressTime);
    }
    
  }
}

//////////////////////
void checkServo() { // to move spout servo (moves back to null at ITI)
  if (isTrial == 1 && millis() - trialStartTime >= servoDelay && moveServo == 1 && prevLevPress==1) {
    moveServo = 0;

    // move servo to correct position for this trialType
    spoutServo.write(servoPosArr[trialType - 1]);

    Serial.print("moveServo, ");//
    Serial.print("trialNum="); Serial.print(trialNum);
    Serial.print(", port="); Serial.print(trialType);
    Serial.print(", ms=");   //Print  this to the serial port
    Serial.println(millis());

    //delay(500); // give time for servo to move
  }
}

////////////////////
void checkCues() {
  if (isTrial == 1 && useCues == 1 && cueOn == 0 && giveCue == 1) {
    cueOn = 1;
    giveCue = 0;
    cueStartTime = millis();
    if (trialType == 1) {
      pixels.setPixelColor(0, pixels.Color(0, 50, 0));
      if (useTone==1) {
        tone(spkPin, toneFreq1); //, toneDur1);
      }
    }
    else {
      pixels.setPixelColor(0, pixels.Color(0, 0, 50));
      if (useTone==1) {
        tone(spkPin, toneFreq2); //, toneDur1);
      }
    }
    pixels.show();   // Send the updated pixel color to the LED.

    digitalWrite(syncPin, HIGH);
    
    Serial.print("cueOn");
    Serial.print(", port="); Serial.print(trialType);
    Serial.print(", ms=");   //Print  this to the serial port
    Serial.println(cueStartTime);
  }

  else if (cueOn == 1 && millis() - cueStartTime >= cueDur) {
    cueOn = 0;
    if (useTone==1) {
      noTone(spkPin);
    }
    pixels.setPixelColor(0, pixels.Color(0, 0, 0)); // turn neopixel off
    pixels.show();   // Send the updated pixel color to the LED.

    digitalWrite(syncPin, LOW);

    Serial.print("cueOff");//"trialNum="); Serial.print(trialNum);
    Serial.print(", port="); Serial.print(trialType);
    Serial.print(", ms=");   //Print  this to the serial port
    Serial.println(millis());
  }
}


//////////////////////
void checkTrial() {

  //  if (isTrial==0 && isIti==0 && force>=forceThresh) {
  //    giveTrial = 1;
  //  }

  // start new trial (if ITI over)
  if (isTrial == 0 && isIti == 0 && giveTrial == 1) { //millis() - trialEndTime >= ITI) { // NEW TRIAL
    isTrial = 1;
    giveTrial = 0;
    trialNum = trialNum + 1;

    trialType = trialArray[trialNum - 1];

    trialStartTime = millis();

    // set correct solenoid pin (and reward duration) for this port this trial
    if (trialType == 1) { //This resets our generic pins to ones for this trial type
      solPin = solPin1;
      rewDur = rewDur1;
    }
    else if (trialType == 2) {
      solPin = solPin2;
      rewDur = rewDur2;
    }

    if (useCues == 1) {
      giveCue = 1;
    }

    Serial.print("trialNum="); Serial.print(trialNum);
    Serial.print(", port="); Serial.print(trialType);
    Serial.print(", ms=");   //Print  this to the serial port
    Serial.println(trialStartTime);

//    hasLicked = 0;
    numLicksInBout = 0;
    rewReset = 1; // reset rew and lick bouts for new trial
    moveServo = 1; // reset trial servo move
  }
  // start ITI if got rew or by time
  else if (isTrial == 1 && millis() - trialStartTime >= trialDur) { // rewReset==0 && millis() - rewTime >= postRewDur

    //trialEndTime = millis();
    itiStartTime = millis();
    isTrial = 0;
    isIti = 1;
    Serial.print("iti="); Serial.print(iti);
    Serial.print(", trialNum="); Serial.print(trialNum);
    Serial.print(", port="); Serial.print(trialType);
    Serial.print(", ms=");   //Print  this to the serial port
    Serial.println(itiStartTime); //trialEndTime);

    if (itiNullPos == 1) { // to move servo to null position during ITI
      spoutServo.write(nullPos);
      delay(500);
    }

  }
  // to end ITI
  else if (isIti == 1 && millis() - itiStartTime >= iti) {
    isIti = 0;
    giveTrial = 1;
    prevLevPress = 0;
  }
  //  else if (showCue==1 && isITI==1 && millis()-itiStartTime) {
  //    //
  //  }

  // to end session
  if (isTrial == 0 && isIti == 0 && (trialNum >= maxNumTrials || millis() - startTime >= sessDur)) {
    // end session
    toStart = 0;
    Serial.print("END SESSION, numTrials=");
    Serial.print(trialNum);
    Serial.print(", ms=");
    Serial.println(millis());
  }
}


/////////////////////
void checkRew() {
  if (isTrial == 1 && rewOn == 0 && prevLevPress==1 && millis()-levPressTime<rewAvailDur) { //&& millis()-trialStartTime<5000) {
    if ((numLicksInBout >= numLicksForRew) && (millis() - rewTime >= rewTimeout)) { //(rewReset == 1 && force >= forceThresh) { //numLicksInBout >= numLicksForRew) { // && hasLicked==1 // || levForce>=forceThresh
      giveRew();
    }
  }
  // turn reward off (but don't reset until new trial)
  else if (rewOn == 1 && (millis() - rewTime >= rewDur || millis()-trialStartTime>=5000)) {
    digitalWrite(solPin, LOW);
    //digitalWrite(ledPin, LOW);
    rewOn = 0;
  }
}

void giveRew() {

  digitalWrite(solPin, HIGH);
  //digitalWrite(ledPin, HIGH);
  rewTime = millis(); //
  rewOn = 1;
  numLicksInBout = 0;
  rewReset = 0; // rewReset is set to 0 when reward started, then reset to 1 when lick =0 (thus another reward shouldn't be triggered if port still touched)

  Serial.print("REWARD"); //Print text output
  Serial.print(", trialNum="); Serial.print(trialNum);
  Serial.print(", port="); Serial.print(trialType);
  Serial.print(", ms="); Serial.println(millis());

}


///////////////////////
//void checkButton() { // for button start
//  if (digitalRead(buttonPin) == 0) {
//    if (millis() - prevButtonTime > 2000) {
//      prevButtonTime = millis();
//      giveReward();
//      prevRew = 1;
//      //      if (startSession == 0) {
//      //        startSession = 1;
//      //        startTime = millis();
//      //        digitalWrite(trigPin, HIGH); // trig stays HIGH whole session after button start
//      //        Serial.print("START SESSION button, ms = ");
//      //        Serial.println(startTime);
//      //        Serial.print("trigTime, ms=");
//      //        Serial.println(startTime);
//      //        prevButtonTime = startTime;
//      //
//      //      }
//      //      else {
//      //        startSession = 0;
//      //        endTime = millis();
//      //        digitalWrite(trigPin, LOW);
//      //        digitalWrite(syncPin, LOW);
//      //        digitalWrite(syncPin2, LOW);
//      //        Serial.print("END session button, ms=");
//      //        Serial.println(endTime);
//      //        prevButtonTime = endTime;
//      //      }
//    }
//  }
//}


////////////////////////
//void checkSyncState() {
//  if (prevSync == 1 && millis() - syncStartTime >= syncDur) {
//    digitalWrite(syncPin, LOW);
//    //digitalWrite(syncPin2, LOW);
//    prevSync = 0;
//  }
//  else if (millis() - lastSyncTime >= syncIntv) {
//    digitalWrite(syncPin, HIGH);
//    //digitalWrite(syncPin2, HIGH);
//    syncStartTime = millis();
//    Serial.print("syncOut, ms = ");
//    Serial.println(syncStartTime);
//    lastSyncTime = syncStartTime;
//    prevSync = 1;
//  }
//}

//////////////////////
void checkLicks() {

  touchVal = digitalRead(lickPin);
  numReading++;

  lickStateSum = lickStateSum + touchVal;

  if (numReading == 5) {  // every 5 readings
    if (lickStateSum > lickThresh) { // if all readings were lick ON (to debounce)
      if (prevLick == 0) { // if new lick
        //digitalWrite(ledPin, HIGH);
        prevLick = 1;

          lickTime = millis();

          Serial.print("lick, ");
          Serial.print("trialNum="); Serial.print(trialNum);
          Serial.print(", port="); Serial.print(trialType + 1);
          Serial.print(", ms=");   //Print  this to the serial port
          Serial.println(lickTime);

          // check lick bout (if in trial and no prev rew)
          if (isTrial == 1) { // && rewReset == 1) {
            if (lickTime - prevLickTime <= maxInterLick) {
              numLicksInBout = numLicksInBout + 1;
              Serial.print(numLicksInBout);
              Serial.println(" licks in bout");
            }
            else {
              numLicksInBout = 1;
            }
          }

          //Serial.println(numLicksInBout);
          //hasLicked = 1;  // set this for lick choice in this trial

          prevLickTime = lickTime;

      }
    }
    else if (lickStateSum == 0) {  //if (prevLick == 1 && lickState == 0 && millis()-lickTime>50) {
      prevLick = 0;
      //digitalWrite(ledPin, LOW);
    }
    numReading = 0;
    lickStateSum = 0;
  }

}  // END checkLicks();

//////////////////////////////
//void readTouchInputs() {
//  if (!checkInterrupt()) {
//
//    //read the touch state from the MPR121
//    Wire.requestFrom(0x5A, 2);
//
//    byte LSB = Wire.read();
//    byte MSB = Wire.read();
//
//    uint16_t touched = ((MSB << 8) | LSB); //16bits that make up the touch states
//
//
//    for (int i = 0; i < 12; i++) { // Check what electrodes were pressed
//      if (touched & (1 << i)) {
//
//        if (touchStates[i] == 0) {
//          if (i==trialType-1) { // 031023 if lick is on current port
//          //pin i was just touched
//          //          Serial.print("pin ");
//          //          Serial.print(i);
//          //          Serial.println(" was just touched");
//
//          lickTime = millis();
//
//          Serial.print("lick, ");
//          Serial.print("trialNum="); Serial.print(trialNum);
//          Serial.print(", port="); Serial.print(i + 1);
//          Serial.print(", ms=");   //Print  this to the serial port
//          Serial.println(lickTime);
//
//
//          // check lick bout (if in trial and no prev rew)
//          if (isTrial == 1) { // && rewReset == 1) {
//            //Serial.println("good");
//            if (lickTime - prevLickTime <= maxInterLick) {
//              numLicksInBout = numLicksInBout + 1;
//              Serial.print(numLicksInBout);
//              Serial.println(" licks in bout");
//            }
//            else {
//              numLicksInBout = 1;
//            }
//          }
//
//          //Serial.println(numLicksInBout);
//
//          //hasLicked = 1;  // set this for lick choice in this trial
//
//          prevLickTime = lickTime;
//        }
//
//        }
//        else if (touchStates[i] == 1) {
//          //pin i is still being touched
//        }
//
//        touchStates[i] = 1;
//      }
//      else { // if not touched
////        if (touchStates[i] == 1) { // if previously touched
////          Serial.print("pin ");
////          Serial.print(i);
////          Serial.println(" is no longer being touched");
////
////          //pin i is no longer being touched
////        }
//
//        touchStates[i] = 0;
//      }
//
//    }
//
//  }
//}
//
