############################ MUX TEST - MIKROE-4048 ######################################

from time import sleep, time
import os
import fcntl
import struct

I2C_SLAVE = 0x0703 # The hex value 0x0703 assigned to the I2C_SLAVE variable is a constant defined in the Linux I2C subsystem.
MUX_ADDRESS =  0x70 # Configurable address of the MIKROE-4048

def I2C_dev_read(address, number_of_bytes):
    i2c_bus = os.open('/dev/i2c-2', os.O_RDWR) # Open I2C bus
    fcntl.ioctl(i2c_bus, I2C_SLAVE, address) # Set the I2C slave address
    # os.write(i2c_bus, bytes([register])) # Write the register address to the device (no stop bit)
    data = os.read(i2c_bus, number_of_bytes)  # Read bytes
    os.close(i2c_bus)
    byte_list = list(data)
    return byte_list
def Mux_write(address, control):
    i2c_bus = os.open('/dev/i2c-2', os.O_RDWR) # Open the I2C device file
    fcntl.ioctl(i2c_bus, I2C_SLAVE, address)  # Set the I2C slave address
    os.write(i2c_bus, struct.pack('B', control))   # Write data to the I2C device
    sleep(0.01)
    os.close(i2c_bus)


Mux_write(MUX_ADDRESS,0x01) # set MUX to channel 0
control_value = I2C_dev_read(MUX_ADDRESS, 1)
print("control value: ", control_value)