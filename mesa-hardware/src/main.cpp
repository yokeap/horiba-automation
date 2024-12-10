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
//      0x20 open chamber
//      0x21 chamber lamp active, send command to PLC
//      0x22 wait PLC signal (SOR, Sample Off Ready)
//      0x30 success all state


#include <Arduino.h>
#define HOME_ACT_CHAMBER A2
#define PUSH_ACT_CHAMBER A1
#define FULLY_CLOSE_CHAMBER A0
#define FULLY_OPEN_CHAMBER A3
#define SAMPLE_READY 37
#define CHECK_OBJ_SENSOR 23

#define SW_MODE 24            // High = Auto mode, Low = Manual mode
#define SW_OPEN_CHAMBER 25
//#define SW_RESET A4
// #define SW_STOP A2

#define MESA_DEBUG false
#define DEBUG true

// lamp pin out
const int LAMP_MODE = 26;    // 
const int LAMP_CHAMBER = 5;  //
const int LAMP_SAMPLE = 3;   //
const int LAMP_MEASURE = 4;  // 
const int LAMP_ALARM = 2;    // 

// linear motor for activate chamber lid
const int LIN_ACT_CHAMBER_LPWM = 11;
const int LIN_ACT_CHAMBER_RPWM = 12;

//linear motor for chamber lid L
const int LIN_CHAMBER_LID_LPWM_L = 9;
const int LIN_CHAMBER_LID_RPWM_L = 8;

//linear motor for chamber lid R
const int LIN_CHAMBER_LID_LPWM_R = 7;
const int LIN_CHAMBER_LID_RPWM_R = 6;

unsigned char globalState = 0;
unsigned char localState = 0;
unsigned char manualState = 0;

unsigned char uintPwmVal_lin_act_chamber = 0;
unsigned char uintPwmVal_lin_chamber_lid = 0;

unsigned long currentMillis = 0;
unsigned long previousMillis = 0;

bool flagPreviousMillis = false;

String inputString1;         // a String to hold incoming data
bool string1Complete = false;  // whether the string is complete

String inputString2;         // a String to hold incoming data
bool string2Complete = false;  // whether the string is complete

bool flag_mesa_status = false;
bool flag_alarm = false;

void alarm();

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
  return false;
}

bool plc_receive(String strCheck){
  if (string1Complete) {
    // Serial.print("PLC: ");
    // Serial.print(inputString1);
      if(inputString1 == strCheck) {
        // clear the string:
        inputString1 = "";
        string1Complete = false;
        strCheck = "";
        return true;
      }
      // clear the string:
      inputString1 = "";
      string1Complete = false;
      return false;
    }
  return false;
}

bool mesa_receive(char *strCheck){
  if (string2Complete) {
    // Serial.print(inputString2);
    // Serial.print("string check: ");
    // Serial.print(strCheck);
      if(inputString2 == strCheck) {
        // clear the string:
        inputString2 = "";
        string2Complete = false;
        return true;
      }
      // clear the string:
      inputString2 = "";
      string2Complete = false;
      return false;
    }
  return false;
}

void lin_act_chamber_stop(){
  digitalWrite(LIN_ACT_CHAMBER_LPWM, LOW);
  digitalWrite(LIN_ACT_CHAMBER_RPWM, LOW);
  uintPwmVal_lin_act_chamber = 0;
}

unsigned char lin_act_chamber_stroke_in(){
  if(!digitalRead(HOME_ACT_CHAMBER)){
    lin_act_chamber_stop();
    return 1;
  }
  // start stroke
  digitalWrite(LIN_ACT_CHAMBER_LPWM, LOW);
  digitalWrite(LIN_ACT_CHAMBER_RPWM, HIGH);
  if(++uintPwmVal_lin_act_chamber < 120){
    analogWrite(LIN_ACT_CHAMBER_RPWM, uintPwmVal_lin_act_chamber);
  } 
  else{
    uintPwmVal_lin_act_chamber = 120;
    analogWrite(LIN_ACT_CHAMBER_RPWM, uintPwmVal_lin_act_chamber);
  }
  return 0;
}

unsigned char lin_act_chamber_stroke_out(){
  if(!digitalRead(PUSH_ACT_CHAMBER)){
    lin_act_chamber_stop();
    return 1;
  }
  // start stroke
  digitalWrite(LIN_ACT_CHAMBER_LPWM, HIGH);
  digitalWrite(LIN_ACT_CHAMBER_RPWM, LOW);
  if(++uintPwmVal_lin_act_chamber < 120){
    analogWrite(LIN_ACT_CHAMBER_LPWM, uintPwmVal_lin_act_chamber);
    Serial.println(uintPwmVal_lin_act_chamber);
  } 
  else{
    uintPwmVal_lin_act_chamber = 120;
    analogWrite(LIN_ACT_CHAMBER_LPWM, uintPwmVal_lin_act_chamber);
  }
  return 0;
}

void lin_chamber_lid_stop(){
  analogWrite(LIN_CHAMBER_LID_LPWM_L, 0);
  analogWrite(LIN_CHAMBER_LID_RPWM_L, 0);
  analogWrite(LIN_CHAMBER_LID_LPWM_R, 0);
  analogWrite(LIN_CHAMBER_LID_RPWM_R, 0);
  uintPwmVal_lin_chamber_lid = 0;
}

unsigned char lin_chamber_lid_stroke_in(){
  // start stroke
  if(!digitalRead(FULLY_OPEN_CHAMBER)){
    lin_chamber_lid_stop();
    return 1;
  }

 if(uintPwmVal_lin_chamber_lid < 150) uintPwmVal_lin_chamber_lid = uintPwmVal_lin_chamber_lid + 1;

  analogWrite(LIN_CHAMBER_LID_LPWM_L, uintPwmVal_lin_chamber_lid);
  analogWrite(LIN_CHAMBER_LID_RPWM_L, 0);
  analogWrite(LIN_CHAMBER_LID_LPWM_R, uintPwmVal_lin_chamber_lid + 10);
  analogWrite(LIN_CHAMBER_LID_RPWM_R, 0);
  return 0;
}

unsigned char lin_chamber_lid_stroke_out(){
  if(!digitalRead(FULLY_CLOSE_CHAMBER)){
    lin_chamber_lid_stop();
    return 1;
  }
  // start stroke
  if(uintPwmVal_lin_chamber_lid < 150) uintPwmVal_lin_chamber_lid = uintPwmVal_lin_chamber_lid + 1;
  analogWrite(LIN_CHAMBER_LID_LPWM_L, 0);
  analogWrite(LIN_CHAMBER_LID_RPWM_L, uintPwmVal_lin_chamber_lid);
  analogWrite(LIN_CHAMBER_LID_LPWM_R, 0);
  analogWrite(LIN_CHAMBER_LID_RPWM_R, uintPwmVal_lin_chamber_lid + 10);
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
  if(lin_act_chamber_home() && lin_chamber_lid_home()) return state + 1;
  return state;
}

unsigned char lin_act_chamber_activate(unsigned char state){
  if(lin_act_chamber_stroke_out()) return state + 1;
  return state;
}

unsigned char lin_chamber_lid_pull(unsigned char state){
  // if(lin_act_chamber_stroke_out() && lin_chamber_lid_stroke_in()) return state + 1;
  if(lin_chamber_lid_stroke_in()) return state + 1;
  // if( lin_chamber_lid_stroke_in()) return 0x04;
  return state;
}

unsigned char lin_chamber_lid_close(unsigned char state){
  if(lin_act_chamber_stroke_in() && lin_chamber_lid_home()) return state + 1;
  // if( lin_chamber_lid_stroke_in()) return 0x04;
  return state;
}

unsigned char pushSample(unsigned char state){
  switch (state)
  {
    case 0x00:

      Serial1.write("PLC,CHK\n");                   // check PLC
      state = 0x01;
      Serial.println(inputString1);
      break;
    case 0x01:
      
      if(plc_receive("PLC,RDY\n")) state++;    //RDY = Ready
      break;
    case 0x02:

      state = pushSampleHome(state);
      break;
    case 0x03:
      state = lin_act_chamber_activate(state);
      break;
    case 0x04:

      if(delayC(1000)) state++;
      break;
    case 0x05:

      state = lin_chamber_lid_pull(state);
      break;
    case 0x06:

      digitalWrite(LAMP_CHAMBER, LOW);
      Serial1.write("PLC,LO1\n");                   // LO = LID close;
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
    if(plc_receive("PLC,SIR\n"))state++;    //SIR = Sample IN Ready
    break;
  case 0x11:
    if(!digitalRead(CHECK_OBJ_SENSOR)){
      digitalWrite(LAMP_SAMPLE, LOW);
      state++;
      break;
    }
    if(digitalRead(SAMPLE_READY)){
      digitalWrite(LAMP_SAMPLE, LOW);
      state++;
      break;
    } 
       else{
      alarm();
    }
    break;
  case 0x12:
    state = lin_chamber_lid_close(state);
    break;
  case 0x13:
     digitalWrite(LAMP_CHAMBER, HIGH);
     Serial2.write("MESA,MSS\n");                   // MS = Measure Start
     state++;
    break;
  case 0x14:
    digitalWrite(LAMP_MEASURE, LOW);
    state++;
    break;
  case 0x15:  
    if(MESA_DEBUG) {
        state++;
        break;
    }
    if(mesa_receive("MESA,MSR\n")) state++;    //MSR = Measure Ready
    break;
  case 0x16:
    if(MESA_DEBUG) {
        state++;
        break;
    }
    if(mesa_receive("MESA,MSD\n")) state++;    //MSD = Measure Done
    break;
  case 0x17:
    digitalWrite(LAMP_MEASURE, HIGH);
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
  case 0x20:
      state = lin_act_chamber_activate(state);
      break;
  case 0x21:
      if(delayC(1000)) state++;
      break;  
  case 0x22:
    state = lin_chamber_lid_pull(state);
    break;
  case 0x23:
    digitalWrite(LAMP_CHAMBER, HIGH);
    Serial1.write("PLC,LO2\n");                   // L = LID open;
    state++;
    break;
  case 0x24:
    if(plc_receive("PLC,SOR\n")) state++;    //SR = Sample Ready
    break;
  case 0x25:
      if(!digitalRead(SAMPLE_READY)){
      digitalWrite(LAMP_SAMPLE, HIGH);
      state++;
      break;
    }
    else{
      alarm();
    }
    break;
  case 0x26:
    // if(lin_chamber_lid_home()) state++;
    
    state = pushSampleHome(state);
    break;
  case 0x27:
     digitalWrite(LAMP_CHAMBER, HIGH);
     state = 0x30;
    break;

  default:
    break;
  }
  return state;
}

void alarm(){
  Serial.print("ALARM\n");
  Serial1.print("PLC,ALM\n");
  flag_mesa_status = false;
  lin_act_chamber_stop();
  lin_chamber_lid_stop();
  flag_alarm = true;
}

void setup() {
  pinMode(18, OUTPUT);
  pinMode(19, INPUT_PULLUP);
  Serial.begin(9600);
  delay(1000);
  Serial1.begin(9600);
  delay(1000);
  inputString1.reserve(20);
  Serial2.begin(9600);
  delay(1000);
  inputString2.reserve(20);



  // lamp 
  pinMode(LAMP_CHAMBER, OUTPUT);
  pinMode(LAMP_MEASURE, OUTPUT);
  pinMode(LAMP_SAMPLE, OUTPUT);
  pinMode(LAMP_ALARM, OUTPUT);
  pinMode(LAMP_MODE, OUTPUT);
  digitalWrite(LAMP_CHAMBER, HIGH); // Low to open lamp
  digitalWrite(LAMP_MEASURE, HIGH);
  digitalWrite(LAMP_SAMPLE, HIGH);
  digitalWrite(LAMP_ALARM, HIGH);
  digitalWrite(LAMP_MODE, HIGH);
  // limit switch
  pinMode(HOME_ACT_CHAMBER, INPUT);
  pinMode(PUSH_ACT_CHAMBER, INPUT);
  pinMode(FULLY_CLOSE_CHAMBER, INPUT);
  pinMode(FULLY_OPEN_CHAMBER, INPUT);
  pinMode(SAMPLE_READY, INPUT);
  pinMode(CHECK_OBJ_SENSOR, INPUT);
  pinMode(SW_MODE, INPUT);
  pinMode(SW_OPEN_CHAMBER, INPUT);
  // linear motor for activate chamber lid
  pinMode(LIN_ACT_CHAMBER_LPWM, OUTPUT);
  pinMode(LIN_ACT_CHAMBER_RPWM, OUTPUT);
  
  // linear motor for chamber lid L
  pinMode(LIN_CHAMBER_LID_LPWM_L, OUTPUT);
  pinMode(LIN_CHAMBER_LID_RPWM_L, OUTPUT);

  // linear motor for chamber lid R
  pinMode(LIN_CHAMBER_LID_LPWM_R, OUTPUT);
  pinMode(LIN_CHAMBER_LID_RPWM_R, OUTPUT);


  delay(1000);
  Serial.println("Ready");
}

unsigned char auto_mode(){
  digitalWrite(LAMP_MODE, LOW);
  if(DEBUG) Serial.println(localState, HEX);
  
  if(!flag_mesa_status){
  if(mesa_receive("MESA,CHK\n")){
    Serial2.write("MESA,RDY\n");
    Serial.println("Ready");
    flag_mesa_status = true;
  }
 }

  //  flag_mesa_status = true;
  if(flag_mesa_status){
    switch (globalState)
    {
    case 0x00:
      localState = pushSample(localState);
      globalState = localState & 0xF0;
      break;
    case 0x10:
      localState = measure(localState);
      globalState = localState & 0xF0;
      break;
    case 0x20:
      localState = takeoffSample(localState);
      globalState = localState & 0xF0;
      break;
    case 0x30:
      localState = 0;
      globalState = 0;
      break;

    default:
      break;
    }
    return 0;
  }
}

unsigned char manual_mode(){
  globalState = 0;
  localState = 0;

  Serial.println("Manual_Mode");
  digitalWrite(LAMP_MODE, HIGH);
  if(!digitalRead(SW_OPEN_CHAMBER)){
    switch (manualState)
    {
    case 0x00:
      manualState = lin_act_chamber_activate(manualState);
      break;
    case 0x01:
      manualState = lin_chamber_lid_pull(manualState);
      break;

    default:
      break;
    }
    
    digitalWrite(LAMP_CHAMBER, LOW);
  }
  else{
    manualState = 0;
    pushSampleHome(0);
    digitalWrite(LAMP_CHAMBER, HIGH);
  }
  return 0;
}

void loop() {

//for arduino debug
  if(flag_alarm){
    digitalWrite(LAMP_ALARM, LOW);
    delay(500);
    digitalWrite(LAMP_ALARM, HIGH);
    delay(500);
  }
  else{
    if(!digitalRead(SW_MODE)) auto_mode();
     else manual_mode();
  }
  

  // if(mesa_receive("MESA,ALM")) {
  //   flag_mesa_status = false;
  //   digitalWrite(LAMP_ALARM, HIGH);
  // }
}

void serialEvent1() {
  while (Serial1.available()) {
    // get the new byte:
    char inChar1 = (char)Serial1.read();
    // Serial.print(inChar1);
    // add it to the inputString:
    inputString1 += inChar1;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    // Serial.print(inputString1);
    if (inChar1 == '\n') {
      string1Complete = true;
    }
  }
}

void serialEvent2() {
  while (Serial2.available()) {
    // get the new byte:
    char inChar2 = (char)Serial2.read();
    // add it to the inputString:
    inputString2 += inChar2;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:*-*-*
    if (inChar2 == '\n') {
        string2Complete = true;
        if (inputString2 == "MESA,ALM\n"){
          alarm();
          inputString2 = "";
          string2Complete = false;
        }
    }
  }
}