/************************state explanation ***************************/
// global state: 00
//    local state : 00 (Push sample)
//      0x00 pushSampleHome
//      0x01 activate button to open lid 
//      0x02 delay 1000ms
//      0x03 pull lid 
//      0x04 Lamp chamber on and send command to PLC (tell that the lid is opened!)
//      0x10 change to global state 10
// global state: 10 (Measurement state)
//    local state:
//      0x10 wait PLC command (Sample ready)
//      0x11 Sample lamp active 
//      0x12 lid chamber homing
//      0x13 Chamber lamp active and send measure command to PC
//      0x14 wait for Measure ready command from PC
//      0x15 Measure lamp active
//      0x16 wait form Measure done command from PC
//      0x17 Measure lamp deactive
//      0x20 change to global state 20
// global state: 20 (takeoff sample)


#include <Arduino.h>
#define HOME_ACT_CHAMBER A0
#define PUSH_ACT_CHAMBER A4
#define FULLY_CLOSE_CHAMBER A1
#define FULLY_OPEN_CHAMBER A2

#define SW_AUTO A8
#define SW_OPEN_CHAMBER A9
#define SW_RESET A6
// #define SW_STOP A2

// lamp pin out
const int LAMP_CHAMBER = 3;  //
const int LAMP_MEASURE = 4;  // Open-Close Door
const int LAMP_SAMPLE = 5;   //
const int LAMP_ALARM = 6;    // 

// linear motor for activate chamber lid
const int LIN_ACT_CHAMBER_PWM = 8;
const int LIN_ACT_CHAMBER_INA = 9;
const int LIN_ACT_CHAMBER_INB = 10;

//linear motor for chamber lid
const int LIN_CHAMBER_LID_PWM = 11;
const int LIN_CHAMBER_LID_INA = 12;
const int LIN_CHAMBER_LID_INB = 13;


unsigned char globalState = 0;
unsigned char localState = 0;

unsigned char uintPwmVal_lin_act_chamber = 0;
unsigned char uintPwmVal_lin_chamber_lid = 0;

unsigned long currentMillis = 0;
unsigned long previousMillis = 0;

bool flagPreviousMillis = false;

String inputString1 = "";         // a String to hold incoming data
bool string1Complete = false;  // whether the string is complete

String inputString2 = "";         // a String to hold incoming data
bool string2Complete = false;  // whether the string is complete

bool delayC(unsigned long delayT){
  if(!flagPreviousMillis) {
    previousMillis = millis();
    flagPreviousMillis = true;
    return false;
  }
  else{
    currentMillis = millis() - previousMillis;
    if(currentMillis < delayT) {
      flagPreviousMillis = false;
      return true;
    }
  }
}

void lin_act_chamber_stop(){
  analogWrite(LIN_ACT_CHAMBER_PWM, 0);
}

unsigned int lin_act_chamber_stroke_in(){
  if(!digitalRead(HOME_ACT_CHAMBER)){
    lin_act_chamber_stop();
    return 1;
  }
  // start stroke
  digitalWrite(LIN_ACT_CHAMBER_INA, HIGH);
  digitalWrite(LIN_ACT_CHAMBER_INB, LOW);
  if(++uintPwmVal_lin_act_chamber < 255){
    analogWrite(LIN_ACT_CHAMBER_PWM, uintPwmVal_lin_act_chamber);
  } 
  else
    uintPwmVal_lin_act_chamber = 255;
    analogWrite(LIN_ACT_CHAMBER_PWM, uintPwmVal_lin_act_chamber);
  return 0;
}

unsigned int lin_act_chamber_stroke_out(){
  if(!digitalRead(PUSH_ACT_CHAMBER)){
    lin_act_chamber_stop();
    return 1;
  }
  // start stroke
  digitalWrite(LIN_ACT_CHAMBER_INA, LOW);
  digitalWrite(LIN_ACT_CHAMBER_INB, HIGH);
  if(++uintPwmVal_lin_act_chamber < 255){
    analogWrite(LIN_ACT_CHAMBER_PWM, uintPwmVal_lin_act_chamber);
  } 
  else
    uintPwmVal_lin_act_chamber = 255;
    analogWrite(LIN_ACT_CHAMBER_PWM, uintPwmVal_lin_act_chamber);
  return 0;
}

void lin_chamber_lid_stop(){
  analogWrite(LIN_CHAMBER_LID_PWM, 0);
}


unsigned int lin_chamber_lid_stroke_in(){
  // start stroke
  if(!digitalRead(FULLY_OPEN_CHAMBER)){
    lin_chamber_lid_stop();
    return 1;
  }
  digitalWrite(LIN_CHAMBER_LID_INA, HIGH);
  digitalWrite(LIN_CHAMBER_LID_INB, LOW);
  if(++uintPwmVal_lin_chamber_lid < 255){
    analogWrite(LIN_CHAMBER_LID_PWM, uintPwmVal_lin_chamber_lid);
  } 
  else
    uintPwmVal_lin_act_chamber = 255;
    analogWrite(LIN_CHAMBER_LID_PWM, uintPwmVal_lin_chamber_lid);
  return 0;
}

unsigned int lin_chamber_lid_stroke_out(){
  if(!digitalRead(FULLY_CLOSE_CHAMBER)){
    lin_chamber_lid_stop();
    return 1;
  }
  // start stroke
  digitalWrite(LIN_CHAMBER_LID_INA, LOW);
  digitalWrite(LIN_CHAMBER_LID_INB, HIGH);
  if(++uintPwmVal_lin_chamber_lid < 255){
    analogWrite(LIN_CHAMBER_LID_PWM, uintPwmVal_lin_chamber_lid);
  } 
  else
    uintPwmVal_lin_chamber_lid = 255;
    analogWrite(LIN_CHAMBER_LID_PWM, uintPwmVal_lin_chamber_lid);
    return 0;
}

unsigned char lin_act_chamber_home(){
  if(!digitalRead(HOME_ACT_CHAMBER)){
    lin_act_chamber_stop();
    return 1;
  }
  lin_act_chamber_stroke_in();
  return 0;
}

unsigned char lin_chamber_lid_home(){
  if(!digitalRead(FULLY_CLOSE_CHAMBER)){
    lin_chamber_lid_stop();
    return 1;
  }
  lin_chamber_lid_stroke_out();
  return 0;
}

unsigned char pushSampleHome(unsigned char state){
  if(lin_act_chamber_home() && lin_chamber_lid_home()) return 0x01;
}

unsigned char lin_act_chamber_activate(unsigned char state){
  if(lin_act_chamber_stroke_out()) return 0x02;
}

unsigned char lin_chamber_lid_pull(unsigned char state){
  if(lin_act_chamber_stroke_in() && lin_chamber_lid_stroke_in()) return 0x04;
}

unsigned char pushSample(unsigned char state){
  switch (state)
  {
    case 0x00:
      state = pushSampleHome(0x00);
      break;
    case 0x01:
      state = lin_act_chamber_activate(0x01);
      break;
    case 0x02:
      if(delayC(1000)) state = 0x03;
      break;
    case 0x03:
      state = lin_chamber_lid_pull(0x03);
      break;
    case 0x04:
      digitalWrite(LAMP_CHAMBER, HIGH);
      Serial.write("S,PLC,LC\r");                   // LC = LID close;
      state = 0x10;
      // return 0x10;
      break;
    
    default:
      break;
  }
  
  return state;
}

unsigned char measure(unsigned char state){
  switch (state)
  {
  case 0x10:
    if (string1Complete) {
      Serial.println(inputString1);
      if(inputString1 == "R,PLC,SR") state = 0x11;    //SR = Sample Ready
      // clear the string:
      inputString1 = "";
      string1Complete = false;
    }
    break;
  case 0x11:
    digitalWrite(LAMP_SAMPLE, HIGH);
    state = 0x12;
    break;
  case 0x12:
    if(lin_chamber_lid_home()) state = 0x13;
    break;
  case 0x13:
     digitalWrite(LAMP_CHAMBER, LOW);
     Serial.write("S,MESA,MS\r");                   // MS = Measure
     state = 0x14;
    break;
  case 0x14:
    if (string2Complete) {
        Serial.println(inputString2);
        if(inputString1 == "R,MESA,MSA") state = 0x15;    //MSA = Measure Ready
        // clear the string:
        inputString2 = "";
        string2Complete = false;
      }
    break;
  case 0x15:
    digitalWrite(LAMP_MEASURE, HIGH);
    state = 0x16;
    break;
  case 0x16:
    if (string2Complete) {
        Serial.println(inputString2);
        if(inputString1 == "R,MESA,MSD") state = 0x17;    //MSD = Measure Done
        // clear the string:
        inputString2 = "";
        string2Complete = false;
      }
    break;
  case 0x17:
    digitalWrite(LAMP_MEASURE, LOW);
    state = 0x20;
    break;

  
  default:
    break;
  }
  return state;
}

unsigned char takeoffSample(unsigned char state){
  switch (state)
  {
  case /* constant-expression */:
    /* code */
    break;
  
  default:
    break;
  }
  return state;
}

// void lamp_state_check(){
//   if(!digitalRead(HOME_ACT_CHAMBER)){
//     digitalWrite()
//   }
//   if(!digitalRead(PUSH_ACT_CHAMBER)){

//   }
//   if(!digitalRead(FULLY_CLOSE_CHAMBER)){

//   }
//   if(!digitalRead(FULLY_OPEN_CHAMBER)){

//   }
// }

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  inputString1.reserve(200);
  Serial2.begin(9600);
  inputString2.reserve(200);
  pinMode(LAMP_CHAMBER, OUTPUT);
  pinMode(LAMP_MEASURE, OUTPUT);
  pinMode(LAMP_SAMPLE, OUTPUT);
  pinMode(LAMP_ALARM, OUTPUT);
  digitalWrite(LAMP_CHAMBER, LOW);
  digitalWrite(LAMP_MEASURE, LOW);
  digitalWrite(LAMP_SAMPLE, LOW);
  digitalWrite(LAMP_ALARM, LOW);
  
}

void loop() {
  
  switch (globalState)
  {
  case 0x00:
    localState = pushSample(localState);
    globalState = localState & 0xF0;
    break;
  case 0x10:
    localState = measure(0x10);
    globalState = localState & 0xF0;
    break;
  case 0x20:
    localState = takeoffSample(0x20);
    globalState = localState & 0xF0;
    break;
  case 0x30:
    localState = 0;
    break;

  default:
    break;
  }
}

void serial1Event() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial1.read();
    // add it to the inputString:
    inputString1 += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\r') {
      string1Complete = true;
    }
  }
}

void serial2Event() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial2.read();
    // add it to the inputString:
    inputString2 += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\r') {
      string2Complete = true;
    }
  }
}