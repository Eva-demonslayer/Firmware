####################### THERMOCYCLING WITH BUCK BOOST AND TEMP SENSOR ####################

from time import sleep, time
import smbus2
import os
import fcntl
import struct
import threading

BUCK_BOOST_ADDRESS_1 = 0x75 # Default address of Buck-Boost!
BUCK_BOOST_ADDRESS_2 = 0x74 # Secondary address of Buck-Boost!
I2C_SLAVE = 0x0703 # The hex value 0x0703 assigned to the I2C_SLAVE variable is a constant defined in the Linux I2C subsystem.
TMP_ADDRESS_1 = 0x48 # GND 48h
TMP_ADDRESS_2 = 0x49 # V+ 1001001 49h
TMP_ADDRESS_3 = 0x4A # SDA 1001010 4Ah
TMP_ADDRESS_4 = 0x4B # SCL 1001011 4Bh

####################### TPS55288 REGISTER VALUES ######################

REF_1 = 0x00 # Reference Voltage 
REF_2 = 0x01 # Reference Voltage
IOUT_LIMIT = 0x02 # Current Limit Setting
VOUT_SR = 0x03 # Slew Rate
VOUT_FS = 0x04 # Feedback Selection
CDC = 0x05 # Cable Compensation
MODE = 0x06 # Mode Control
STATUS = 0x07 # Operating Status

####################### TMP112A REGISTER VALUES #######################

TEMP = 0x00 # Temperature Register (Read Only)
CONFIG = 0x01 # Configuration Register (Read/Write)
T_LOW = 0x02 # TLOW Register (Read/Write)
T_HIGH = 0x03 # THIGH Register (Read/Write)

###################### READ/WRITE FUNCTIONS ###########################

def smbus_read_byte(address, register): #reads values from any register
    bus=smbus2.SMBus(1) #Configure I2C bus
    data = bus.read_byte_data(address, register) 
    bus.close
    return data
def smbus_read_word(address, register): #reads values from any register
    bus=smbus2.SMBus(1) #Configure I2C bus
    data = bus.read_word_data(address, register) 
    bus.close
    return data
def smbus_write_register(address, register, data): #reads values from any register
    bus=smbus2.SMBus(1) #Configure I2C bus
    data = bus.write_byte_data(address, register, data) 
    bus.close
    return data
def I2C_dev_read(address, register, number_of_bytes):
    i2c_bus = os.open('/dev/i2c-1', os.O_RDWR) # Open I2C bus
    fcntl.ioctl(i2c_bus, I2C_SLAVE, address) # Set the I2C slave address
    os.write(i2c_bus, bytes([register])) # Write the register address to the device (no stop bit)
    #fcntl.ioctl(i2c_bus, I2C_SLAVE, address | 0x01) # Repeated start condition and resend the address with read bit
    fcntl.ioctl(i2c_bus, I2C_SLAVE, address) # Repeated start condition
    if number_of_bytes == 1:
        data = os.read(i2c_bus, 1)  # Read 1 bytes
        os.close(i2c_bus)
        result = struct.unpack('B', data)[0]  # Convert the data to a usable format (e.g., integer)
        return result
    elif number_of_bytes == 2:
        data = os.read(i2c_bus, 2)  # Read 2 bytes
        os.close(i2c_bus)
        byte_list = list(data)
        # print("read data", byte_list)
        Temp_lsb = byte_list[1] >> 4
        bin_data_1 = format(byte_list[0], '08b')
        bin_data_2 = format(Temp_lsb, '04b')
        # print("binary data 1 ", bin_data_1)
        # print("binary data 2 ", bin_data_2)
        total_temp_bin = bin_data_1 + bin_data_2
        # print("binary data 1 ", total_temp_bin)
        total_temp_int = int(total_temp_bin, 2)
        # print("temp check", total_temp_int)
        # result = struct.unpack('>H', data)[0]  # Convert the data to a usable format (e.g., integer)
        # print("read data", result)
        return total_temp_int
def I2C_dev_write(address, register, data):
    i2c_file = os.open('/dev/i2c-1', os.O_RDWR) # Open the I2C device file
    fcntl.ioctl(i2c_file, I2C_SLAVE, address)  # Set the I2C slave address
    os.write(i2c_file, struct.pack('BB', register, data))   # Write data to the I2C device
    sleep(0.01)
    os.close(i2c_file)

######################## CONFIGURATION ################################

def configure(BUCK_BOOST_ADDRESS):
    I2C_dev_write(BUCK_BOOST_ADDRESS,IOUT_LIMIT,0xE4) # Current limit, 1 LSB is 0.5 mV. Default value is E4, 50mV or 5 Amps
    sleep(0.05)
    current_limit = I2C_dev_read(BUCK_BOOST_ADDRESS, IOUT_LIMIT, 1)
    print("Current limit: ", current_limit, " ", BUCK_BOOST_ADDRESS)
    sleep(0.5)
    # REF_data1= I2c_dev_read(BUCK_BOOST_ADDRESS, REF_1, 1) # 00 11010010b = 282-mV reference voltage (Default)
    # sleep(20.5)
    REF_data1= I2C_dev_read(BUCK_BOOST_ADDRESS, REF_1, 1) # 00 11010010b = 282-mV reference voltage (Default)
    sleep(0.05)
    # REF_data2= I2c_dev_read(BUCK_BOOST_ADDRESS, REF_2, 1) # 00 11010010b = 282-mV reference voltage (Default)
    # sleep(0.5)
    REF_data1= I2C_dev_read(BUCK_BOOST_ADDRESS, REF_1, 1) # 00 11010010b = 282-mV reference voltage (Default)
    sleep(0.05)
    combined_REF = (REF_2 << 8) | REF_1
    print("Buck-Boost internal reference voltage:", combined_REF, " ", BUCK_BOOST_ADDRESS)
    sleep(0.5)
    I2C_dev_write(BUCK_BOOST_ADDRESS, VOUT_FS, 0x03)
    sleep(0.5)
    I2C_dev_write(BUCK_BOOST_ADDRESS, VOUT_SR, 0x01)
    sleep(0.5)
    # temp_mode_check = I2c_dev_read(TPM_ADDRESS_1, CONFIG, 2)
    # temp_mode_check = smbus_read_register(TPM_ADDRESS_1, CONFIG, 2)
    # print("Temp sensor initial configuraton:", temp_mode_check)
    mode_check = I2C_dev_read(BUCK_BOOST_ADDRESS, MODE, 1)
    status_check = I2C_dev_read(BUCK_BOOST_ADDRESS, STATUS, 1)
    print("mode check: ", mode_check)
    print("status: ", status_check)

configure(BUCK_BOOST_ADDRESS_1)
configure(BUCK_BOOST_ADDRESS_2)

########################### EXECUTION #################################

TEMP_SET_TOLERANCE =  0.25 # symmetric tolerance for temperature
TEMP_SET_HI = 95 # hot temp setting
TEMP_SET_LO = 55 # warm temp setting
sample_delay = 0.01 # delay between temperature readings
HIGH_CURRENT = 0X87 # higher current for raising temperature
LOW_CURRENT =  0X82  #lower current for falling temperature

def warm_up(BUCK_BOOST_ADDRESS):
    I2C_dev_write(BUCK_BOOST_ADDRESS,IOUT_LIMIT,0xE4) # default 50 mV, 2.5 A
    I2C_dev_write(BUCK_BOOST_ADDRESS,MODE,0xB0) # turn output on
    print("Warm up sequence has started ", BUCK_BOOST_ADDRESS)

warm_up(BUCK_BOOST_ADDRESS_1)
warm_up(BUCK_BOOST_ADDRESS_2)

def Heater(BUCK_BOOST_ADDRESS, TPM_ADDRESS, TEMP_SET, ID):
    temp_data = 0 # initialize temp data to start
    while temp_data < (TEMP_SET-2):
        temp_data = (I2C_dev_read(TPM_ADDRESS,0x00, 2)) * .0625 # 1 LSB is 0.625 degrees Celsius.
        sleep(sample_delay)
    while True:
        while temp_data < (TEMP_SET+TEMP_SET_TOLERANCE):
            I2C_dev_write(BUCK_BOOST_ADDRESS,IOUT_LIMIT,HIGH_CURRENT) # higher current for raising temperature
            temp_data = (I2C_dev_read(TPM_ADDRESS,0x00, 2)) * .0625 # 1 LSB is 0.625 degrees Celsius.
            print("Heater", ID," temperature data in C: ", temp_data)
            sleep(sample_delay)
        sleep(sample_delay)
        while temp_data > (TEMP_SET-TEMP_SET_TOLERANCE):
            I2C_dev_write(BUCK_BOOST_ADDRESS,IOUT_LIMIT,LOW_CURRENT)  #lower current for falling temperature
            temp_data = (I2C_dev_read(TPM_ADDRESS,0x00, 2)) * .0625 # 1 LSB is 0.625 degrees Celsius.
            print("Heater ", ID," temperature data in C: ", temp_data)
            sleep(sample_delay)
    
# Create threads
thread1 = threading.Thread(target=Heater, args=(BUCK_BOOST_ADDRESS_1, TMP_ADDRESS_4, TEMP_SET_HI, 1))
thread2 = threading.Thread(target=Heater, args=(BUCK_BOOST_ADDRESS_2, TMP_ADDRESS_2, TEMP_SET_LO, 2))

# Start threads
thread1.start()
thread2.start()

# Wait for threads to complete
thread1.join()
thread2.join()

print("Done!")