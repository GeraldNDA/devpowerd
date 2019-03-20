// CI Relay Controller Script
#include "Arduino.h"
#include "string.h"

// define relay module pins ...
#define RELAYMODULE_PIN_IN_START  2
#define RELAYMODULE_PIN_IN_END    9
#define NUM_RELAYMODULE_PINS      (RELAYMODULE_PIN_IN_END - RELAYMODULE_PIN_IN_START + 1)
// Get array length (by Google) which errors with misuse.
#define COUNT_OF(x) ((sizeof(x)/sizeof(0[x])) / ((size_t)(!(sizeof(x) % sizeof(0[x])))))
#define NUM_DEVICES COUNT_OF(device_list)

// Send EOT to inform scripts that that's it.
// NOTE: No longer necessary since conserver+expect is used.
#define EOT "\x04"

const String device_list[] = {
  "slot_0", //pinea64
  "slot_1", //beaglebone
  "slot_2",
  "slot_3",
  "slot_4",
  "slot_5",
  "slot_6",
  "slot_7"
};

const String operations[] = {
  "?", "help",
  "toggle",
  "turn_on",
  "turn_off"
};

bool pin_state[NUM_RELAYMODULE_PINS];

String command_line;
char command_buffer[100];

String operation = "";
int device = 0;

bool get_line();
bool parse_line();
bool parse_serial();
void print_help();

void setup() {
  for (size_t i = 0; i < NUM_RELAYMODULE_PINS; ++i) {
    int relay_pin = RELAYMODULE_PIN_IN_START + i;
    pinMode(relay_pin, OUTPUT); // Configure GPIO as output
    digitalWrite(relay_pin, HIGH); // Initialize relay to off (active low)  
    pin_state[i] = false;
  }
  
  Serial.begin(115200);
  // Necessary for Leonardo since it doesn't have separate Serial chip
  while(!Serial); 
  print_help();
}
void print_help() {
  // Usage instructions for when working with controller directly.
  Serial.println("=== CI Relay Controller ===");
  Serial.println("Available Operations: ");
  Serial.println("    ?, help - Print out this help text.");
  Serial.println("   toggle <device_num> - Toggle the power to this device.");
  Serial.println("   turn_on <device_num> - Provide power to this device.");
  Serial.println("   turn_off <device_num> - Remove power to this the device.");
  // Device listing can be updated using `device_list` 
  // to make this more helpful
  Serial.println("Available Devices: ");
  for (size_t i = 1; i <= NUM_DEVICES; ++i) {
    Serial.println(String("    ") + i + " - " + device_list[i - 1]);
  }
  Serial.println();
  Serial.print(EOT);
}

/** The following lines are for parsing the serial "commandline"
 ** Whenever a new line is sent, the buffer is read and parsed.
 ** Basic validation of operands and device numbers is done too.
 **/ 
bool get_line() {
  while(Serial.available()) {
    char curr_char = Serial.read();
    switch (curr_char) {
      case '\n':
      case '\r':
        Serial.println(String("> ") + command_line);
        Serial.print(EOT);
        command_line.toCharArray(command_buffer, 100);
        command_line = "";
        command_line.reserve(100);
        return true;
      default:
        command_line += curr_char;
    }
 
  }
  return false;
}

bool parse_line() {
    bool got_error;
    char * str = strtok(command_buffer, " \t\r\n");
    if (str == NULL) {
      Serial.println("Error: Bad line.");
      return false;
    }
  
    operation = String(str);
    got_error = true;
  
    for(size_t i = 0; i < COUNT_OF(operations); ++i) {
        if (operations[i] == operation) got_error = false;
    }
    if (got_error) {
      Serial.println("Error: Invalid operation.");
      return false;
    }
    
    if (operation == "?" || operation == "help")
      return false;
  
    str = strtok(NULL, " \t\r\n");
    if (str == NULL) {
      Serial.println("Error: Missing device number");
      return false;
    }
  
    device = String(str).toInt() - 1;
    
    if(device < 0 || device >= (int)NUM_DEVICES){
        Serial.println("Error: Invalid device number.");
        return false;
    }
  
    return true;
}

bool parse_serial() {
  if (get_line()) {
    if (parse_line()) {
      return true;
    } else {
      print_help();
      return false;
    }
  }
  return false; // Got no line
}


void loop() {
  if(parse_serial()) {
    // only modify the GPIOs if the operation will change the state
    // Inform caller that the operation went was successful 
    // (and was not an illegal operation/device)
    bool device_state_changed = (operation == "toggle") || 
      (operation == "turn_on" && !pin_state[device]) ||
      (operation == "turn_off" && pin_state[device]);
    
    if(device_state_changed) {
      int relay_pin = RELAYMODULE_PIN_IN_START + device;
      // invert state
      pin_state[device] = !pin_state[device];
      // write level (HIGH to turn off relay (state = false), and LOW to turn on relay (state = true))
      digitalWrite(relay_pin, !pin_state[device]); 
    }
    Serial.println("Did: " + operation + " for device '" + device_list[device] + "'");
    Serial.print(EOT); 
  }
}
