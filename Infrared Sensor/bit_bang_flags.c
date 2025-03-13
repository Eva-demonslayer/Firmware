////////////////////////////// WIP, NOT FINISHED /////////////////////////

#include <stdio.h>
#include <stdint.h>
#define SDA_PIN 2
#define SCL_PIN 3

// Function to set SDA pin as output
void sda_set_output() {
    // Set direction register for SDA pin to output
}

// Function to set SDA pin as input
void sda_set_input() {
    // Set direction register for SDA pin to input
}

// Function to set SCL pin as output
void scl_set_output() {
    // Set direction register for SCL pin to output
}

// Function to set SCL pin as input
void scl_set_input() {
    // Set direction register for SCL pin to input
}

// Function to set SDA pin high
void sda_high() {
    // Set SDA pin to high logic
}

// Function to set SDA pin low
void sda_low() {
    // Set SDA pin to low logic
}

// Function to set SCL pin high
void scl_high() {
    // Set SCL pin to high logic
}

// Function to set SCL pin low
void scl_low() {
    // Set SCL pin to low logic
}

// Function to read SDA pin value
uint8_t sda_read() {
    // Read SDA pin value and return
}

// Function to generate I2C start condition
void i2c_start() {
    sda_high();
    scl_high();
    sda_low();
    scl_low();
}

// Function to generate I2C stop condition
void i2c_stop() {
    sda_low();
    scl_high();
    sda_high();
}

// Function to send a single bit on I2C bus
void i2c_send_bit(uint8_t bit) {
    if (bit) {
        sda_high();
    } else {
        sda_low();
    }
    scl_high();
    scl_low();
}

// Function to send a byte on I2C bus
void i2c_send_byte(uint8_t data) {
    for (int i = 0; i < 8; i++) {
        i2c_send_bit((data >> (7 - i)) & 0x01);
    }
}

// Function to read a byte from I2C bus with acknowledge
uint8_t i2c_read_byte() {
    uint8_t data = 0;
    sda_set_input();
    for (int i = 0; i < 8; i++) {
        scl_high();
        data |= (sda_read() << (7 - i));
        scl_low();
    }
    sda_high(); // Send acknowledge
    scl_high();
    scl_low();
    sda_set_output();
    return data;
}

int main() {
    // Initialize I2C pins
    
    // Set slave address to read from
    uint8_t slave_address = 0x00; // DEvice Address

    i2c_start();
    i2c_send_byte(slave_address | 0x01); // Send address with read bit set
    
    uint8_t received_byte = i2c_read_byte();
    
    i2c_stop();
    
    printf("Read byte: 0x%02X\n", received_byte);
    
    return 0;
}