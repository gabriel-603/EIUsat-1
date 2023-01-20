#include <SoftwareSerial.h>

// Set up a software serial port for communication with the H-12 radio chip
SoftwareSerial h12Serial(2, 3); // RX, TX

void setup() {
  // Set the baud rate for the software serial port
  h12Serial.begin(9600);

  // Initialize serial communication at 9600 baud rate
  Serial.begin(9600);

}
  String group_data;

void loop() {
  // Check if there is data available to read from the H-12 radio chip
  
  if (group_data.length()==260){
      group_data="";
  }
   
  if (h12Serial.available()) {
    // Read a byte of data from the H-12 radio chip
    char data = h12Serial.read();

  

    // Print the data to the serial monitor as an ASCII character

    group_data=group_data+data;
    Serial.println(group_data);
  }
}
