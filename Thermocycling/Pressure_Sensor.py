############################## HONEYWELL MPR PRESSURE SENSOR ###########################

from time import sleep, time
import os
import fcntl
import struct

I2C_SLAVE = 0x0703 # The hex value 0x0703 assigned to the I2C_SLAVE variable is a constant defined in the Linux I2C subsystem.
MUX_ADDRESS =  0x70 # Configurable address of the MIKROE-4048
DEVICE_ADDRESS = 0X18 # M P
COMMAND = 0xAA

######################### READ/WRITE FUNCTIONS ###################################

def I2C_dev_read(address, number_of_bytes):
    i2c_bus = os.open('/dev/i2c-2', os.O_RDWR) # Open I2C bus
    fcntl.ioctl(i2c_bus, I2C_SLAVE, address) # Set the I2C slave address
    # os.write(i2c_bus, bytes([register])) # Write the register address to the device (no stop bit)
    data = os.read(i2c_bus, number_of_bytes)  # Read bytes
    os.close(i2c_bus)
    byte_list = list(data)
    return byte_list
def I2C_dev_write(address, register, data_1, data_2):
    i2c_bus = os.open('/dev/i2c-2', os.O_RDWR) # Open the I2C device file
    fcntl.ioctl(i2c_bus, I2C_SLAVE, address)  # Set the I2C slave address
    os.write(i2c_bus, struct.pack('BBB', register, data_1, data_2))   # Write data to the I2C device
    sleep(0.01)
    os.close(i2c_bus)
def Mux_write(address, control):
    i2c_bus = os.open('/dev/i2c-2', os.O_RDWR) # Open the I2C device file
    fcntl.ioctl(i2c_bus, I2C_SLAVE, address)  # Set the I2C slave address
    os.write(i2c_bus, struct.pack('B', control))   # Write data to the I2C device
    sleep(0.01)
    os.close(i2c_bus)

########################### EXECUTION #################################

p_max = 25; # maximum value of pressure range [bar, psi, kPa, etc.]
p_min = 0; # minimum value of pressure range [bar, psi, kPa, etc.]
output_max = 15099494 # output at maximum pressure [counts]
output_min = 1677722 # output at minimum pressure [counts]
conversion_rate = 68.948 #psi to mbar
atmosphere = 1006.9 #atmospheric pressure in mbar (estimated based on setting the pressure to zero when open to air)
delay = 0.05

def pressure_calc(sensor):
    I2C_dev_write(DEVICE_ADDRESS,COMMAND,0x00,0x00) # This command will cause the device to exit Standby Mode and enter Operating Mode
    data = I2C_dev_read(DEVICE_ADDRESS, 4)
    print("status and pressure data", data)
    press_counts = data[3] + (data[2] * 256) + (data[1] * 65536) # calculate digital pressure counts
    pressure = ((((press_counts - output_min) * (p_max - p_min)) / (output_max - output_min)) + p_min)*conversion_rate - atmosphere
    print("Sensor: ", sensor, "  Calculated pressure: ", pressure)

while(True):
    Mux_write(MUX_ADDRESS,0x01) # set MUX to channel 0
    sleep(delay)
    pressure_calc(1) # run pressure measurement and calc
    sleep(delay)
    Mux_write(MUX_ADDRESS,0x02) # set MUX to channel 1
    sleep(delay)
    pressure_calc(2) # run pressure measurement and calc
    sleep(delay)
