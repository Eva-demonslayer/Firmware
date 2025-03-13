#################### MLX90614 Test Script #########################

from time import sleep, time
import smbus2
import libscrc
import os
# os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio" 
# from gpiozero import OutputDevice
import fcntl
import struct
SDA_PIN = 2 
SCL_PIN = 3
delay = .0001

bus=smbus2.SMBus(1) #Configure I2C bus
DEVICE_ADDRESS=0x00 #all sensors respond to 0x00 value, default is usually 0x5A. will need to remove this from hard code when testing multiple sensors
bus.enable_pec = False #PEC byte on smbus2 protocol, however, there is no equation in class to calculate it... included manually in the code instead
bus.close() #ends bus test, will re-enable as needed in main program

#led = LED(17) #change gpio value to the sensor power
#led.on() #turn on power to the sensor, will likely be needed for a reset after changes. 

#Test change parameters
TEST_EMISSIVITY = [0x00, 0xFF] #change the emissivity to this value
TEST_ADDRESS = [0x5A, 0x5A] #Most significant byte doesn't matter, but doesn't hurt to populate both

####################### REGISTER VALUES ##############################

AMBIENT_TEMP = 0x06 #RAM access, binary 000xxxxx
OBJECT_TEMP = 0x07 #RAM access, binary 000xxxxx
OBJECT_TEMP_2  = 0x08
TOMAX = 0x20
TOMIN = 0x21
PWMCTRL = 0X22
TARANGE = 0X23
EEPROM_EMISSIVITY = 0x24 #eeprom access 001xxxxx, register value is 0x04
CONFIG = 0x25
ADDRESS_CHANGE = 0x2E
SLEEP = 0xFF
FLAGS = 0xF0

######################### FUNCIONS ###################################

def read_register(REGISTER): #reads values from any register
    if REGISTER != ADDRESS_CHANGE:
        # data = bus.read_i2c_block_data(DEVICE_ADDRESS,REGISTER, 3) #for checking PEC data
        # print(data) #for checking PEC data
        data = bus.read_word_data(DEVICE_ADDRESS,REGISTER) 
    else:
        data = bus.read_byte_data(DEVICE_ADDRESS,REGISTER) 
    return data
def convert_to_celsius(temp_data): #simple function for converting to celsisu from raw data
    temp_C = temp_data * 0.02
    temp_C = temp_C - 273.15
    return temp_C
def write_register(REGISTER, VALUE): #writes to any register and includes PEC byte
    print("confirm register for write: ", REGISTER)
    ZERO_VALUES = [0x00, 0x00]
    all_bytes_clear = [REGISTER, ZERO_VALUES[0], ZERO_VALUES[1]]
    all_bytes = [REGISTER, VALUE[0], VALUE[1]]
    print("list of values for PEC calculation, clear: ", all_bytes_clear)
    print("list of values for PEC calculation, write: ", all_bytes)
    CRC_CLEAR = libscrc.crc8(bytes(all_bytes_clear))
    CRC = libscrc.crc8(bytes(all_bytes))
    print("CRC write clear byte", CRC_CLEAR)
    print("CRC write byte", CRC)
    #bus.write_i2c_block_data(DEVICE_ADDRESS,REGISTER,ZERO_VALUES,CRC_CLEAR) #old methodology for writing data, but failed due to repeated device address
    I2C_dev_write(DEVICE_ADDRESS, REGISTER, ZERO_VALUES[0], ZERO_VALUES[1], CRC_CLEAR)
    sleep(0.01) #recommended delay between clearing data and sending new data
    #bus.write_i2c_block_data(DEVICE_ADDRESS,REGISTER,VALUE,CRC) #old methodology for writing data, but failed due to repeated device address
    # write_i2c_command(DEVICE_ADDRESS, REGISTER, VALUE[0], VALUE[1], CRC) #bit bang methodology
    I2C_dev_write(DEVICE_ADDRESS, REGISTER, VALUE[0], VALUE[1], CRC)
    # sleep(0.005)
    # led.off() #power cycle the sensor, turning it off, and then back on again after a sleep
    # sleep(0.05)
    # led.on()
def calc_emissivity(emissivity_data):
    #print("EEPROM emissivity data: ", emissivity_data) #raw data print out, only needed for troubleshooting
    emissivity = (emissivity_data/65535)
    return emissivity
def I2C_dev_write(address, register, data, data_2, CRC):
    #address = 0x00 #always works all sensors attached
    I2C_SLAVE = 0x0703 # The hex value 0x0703 assigned to the I2C_SLAVE variable is a constant defined in the Linux I2C subsystem.
    i2c_file = os.open('/dev/i2c-1', os.O_RDWR) # Open the I2C device file
    fcntl.ioctl(i2c_file, I2C_SLAVE, address)  # Set the I2C slave address
    os.write(i2c_file, struct.pack('BBBB', register, data, data_2, CRC))   # Write data to the I2C device
    sleep(0.01)
    os.close(i2c_file)

######################## MAIN PPROGRAM ################################

decision = int(input(f"Enter 1 to sample data continuously, 2 to check values, or 3 to change address to {TEST_ADDRESS} or 4 to change emissivity to {TEST_EMISSIVITY} "))

if decision == 1: #sample data continuously
    bus=smbus2.SMBus(1) #Configure I2C bus
    data_delay = 0.02
    test_duration = 60
    sleep(0.1)
    print("Time betwen samples is ", data_delay)
    sleep(1)
    data_list=[]
    start_time = time()
    elapsed_time = 0
    while elapsed_time < test_duration:
        object_data = round(convert_to_celsius(read_register(OBJECT_TEMP)), 2) #linearized object temperature, RAM
        print("Object Temp: ", object_data)
        sleep(data_delay)
        end_time = time()
        elapsed_time = round(end_time - start_time, 3)
        data_list.append(object_data)
    print("Total test time: ", elapsed_time)
    expected_number_of_values = test_duration / data_delay
    print("Expected number of values: ", expected_number_of_values)
    print("Actual number of values: ", len(data_list))
    bus.close()
elif decision == 2: # check all values
    bus=smbus2.SMBus(1) #Configure I2C bus
    address_check = read_register(ADDRESS_CHANGE) #only use this function when configuring one sensor
    print("Address Check: ",address_check)
    sleep(0.1)
    ambient_data = round(convert_to_celsius(read_register(AMBIENT_TEMP)),2) #linearized ambient temperature, RAM
    print("Ambient Temp: ", ambient_data)
    sleep(0.1)
    object_data = round(convert_to_celsius(read_register(OBJECT_TEMP)), 2) #linearized object temperature, RAM
    print("Object Temp: ", object_data)
    sleep(0.1)
    # object_data_2 = round(read_register(OBJECT_TEMP_2), 2) #linearized object temperature, RAM #current reading zero, not sure why yet
    # print("Sensor Temperature: ", object_data_2)
    # sleep(0.1)
    emissivity_eeprom = round(calc_emissivity(read_register(EEPROM_EMISSIVITY)), 2)
    print("EEPROM Emissivity Check: ",emissivity_eeprom)
    sleep(0.1)
    bus.close()
elif decision == 3: # address change
    bus=smbus2.SMBus(1) #Configure I2C bus
    address_check = read_register(ADDRESS_CHANGE) #only use this function when configuring one sensor
    print("Address Check: ",address_check)
    sleep(0.1)
    bus.close()
    write_register(ADDRESS_CHANGE, TEST_ADDRESS)
    print("New address sent: ", TEST_ADDRESS[1])
    sleep(0.1)
    bus=smbus2.SMBus(1) #Configure I2C bus
    address_check = read_register(ADDRESS_CHANGE) #only use this function when configuring one sensor
    print("Address Check: ",address_check)
    sleep(0.1)
    bus.close()
elif decision == 4:
    write_register(EEPROM_EMISSIVITY, TEST_EMISSIVITY) #test code for changing the eeprom emmissivity
    sleep(0.05)
    bus=smbus2.SMBus(1) #Configure I2C bus
    emissivity_eeprom = round(calc_emissivity(read_register(EEPROM_EMISSIVITY)), 2)
    print("EEPROM Emissivity Check: ",emissivity_eeprom)
    sleep(0.1)
    bus.close()
else:
    print("You have entered an invalid command, run the program again")