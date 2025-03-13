################ Application to Initiate Manifold Engagement ################
############################## TMC5130 ######################################
import spidev
from gpiozero import LED
from time import sleep, time
import RPi.GPIO as GPIO
 
spi = spidev.SpiDev()
spi.open(0,0) # specify the SPI bus and device
spi.max_speed_hz = 5000000    #set SPI speed, 5MHz
Fclk = 3.3554432 #(2^24)/spi.max_speed_hz troubleshoot later
 
GPIO.setmode(GPIO.BCM) #set pin numbering for GPIOs
switch = 16 #pin number for switch
GPIO.setup(switch, GPIO.IN)#, pull_up_down=GPIO.PUD_DOWN) #setup pin as an input and pull down resistor
 
#direction_bit = 0x04 #CW move, other direction is 0x14, global
#pulse = 0 # initiation of pulse variable, global

def configure(direction_bit, v_multiplier):
    spi.xfer2([0x80,0x00,0x00,0x00,direction_bit]) #EN_PWM_MODE=1 enables StealthChop
    sleep(0.05) 
    spi.xfer2([0x93,0x00,0x00,0x01,0xF4]) #TPWM_THRS=500 yields a switch velocity of about 35000, 30 RPM
    sleep(0.05) 
    spi.xfer2([0xF0,0x00,0x04,0x01,0x80]) #PWMCONF. first byte set to autoscale, minimum setting 0x40. second byte is user defined PWM Grad (1 to 15), third byte is automatic current control
    sleep(0.05) 
    spi.xfer2([0xEC,0x04,0x01,0x00,0x05]) #Chopconf, toff set to 5. MRES (microstep resolution) set to 16 (range is 128,64,32,16,8,4,2,FULLSTEP). 200*16=3200 steps per rotation.
    sleep(0.05)
    spi.xfer2([0xA0,0x00,0x00,0x00,0x00]) #RAMPMODE (target position move)  
    sleep(0.05)
    spi.xfer2([0x90,0x00,0x01,0x1F,0x00]) #ihold_irun. Bits 0-4 hold current, 8-12 motor current. 16-19 IHOLDDELAY
    sleep(0.05)                           #Run Current Scaling Factor set to 31, no hold current, minimal delay. 
    spi.xfer2([0x91,0x00,0x00,0x00,0x0A]) #TPOWERDOWN=10, delay before power down at standstill
    sleep(0.05)
    print("motor configured", direction_bit, v_multiplier)
 
########### velocity and acceleration parameters ############
 
    V_MAX = int(21.3*16*Fclk * v_multiplier) #VMAX, 1000 or 2000
    hex_str = hex(V_MAX)[2:]
    hex_str = hex_str.zfill(4)
    first_part = hex_str[:2]
    second_part = hex_str[2:]
    first_part_hex = (int(first_part, 16))
    second_part_hex = (int(second_part, 16))
    
    spi.xfer2([0xA5,0x00,0x00,0x00,0xFA]) #V1, Threshold velocity, 500 
    sleep(0.05)
    spi.xfer2([0xA7,0x00,0x00,first_part_hex,second_part_hex]) #VMAX, 1000 or 2000
    #spi.xfer2([0xA7,0x00,0x00,0x03,0xE8]) #VMAX, 1000
    sleep(0.05)
    spi.xfer2([0xA3,0x00,0x00,0x00,0x00]) #VSTART, not used
    sleep(0.05)
    spi.xfer2([0xAB,0x00,0x00,0x00,0x10]) #VSTOP, 10 is mininimum recommended
    sleep(0.05)
    spi.xfer2([0xAA,0x00,0x00,0x00,0x64]) #D1, deceleration between V1 and VSTOP, 100
    sleep(0.05)
    spi.xfer2([0xA4,0x00,0x00,0x00,0x64]) #A1, first acceleration between VSTART and V1, 100
    sleep(0.05)
    spi.xfer2([0xA6,0x00,0x00,0x00,0x32]) #AMAX, 50
    sleep(0.05)
    spi.xfer2([0xA8,0x00,0x00,0x00,0x32]) #DMAX, 50
    sleep(0.05)
def move(pulse):
    micro_step = int((pulse * 16))
    my_list = [0xAD,0x00,0x00]
    hex_str = hex(micro_step)[2:]
    #print(hex_str)
    hex_str = hex_str.zfill(4)
    first_part = hex_str[:2]
    second_part = hex_str[2:]
    #print(first_part)
    #print(second_part)
    first_part_hex = (int(first_part, 16))
    second_part_hex = (int(second_part, 16))
    #print(first_part_hex)
    #print(second_part_hex)
    my_list.append(first_part_hex)
    my_list.append(second_part_hex)
    print("move list", my_list)
    spi.xfer2(my_list)
    sleep(0.05)
 
    position_check = 0 #starts as false
    position_bit = 5 #position reached
    while bool(position_check) == False:
        spi.xfer2([0x00,0x00,0x00,0x00,0x00]) #throw out 1st read
        sleep(.05)
        read_data = spi.xfer2([0x00,0x00,0x00,0x00,0x00]) #SPI_STATUS
        print(read_data)
        sleep(.05)
        hex_data = int(read_data[0])
        position_check=(hex_data >> position_bit) & 1 #bitwise AND operation with a mask of 1  
def reset_position():
    spi.xfer2([0xA1,0x00,0x00,0x00,0x00])
    sleep(0.05)
program = int(input("Enter 1 for manifold engagement, or 2 for consumable return")) #user input for which program to use
if program == 1:
    while GPIO.input(switch) == GPIO.LOW:
        sleep(1)
        print("Waiting for consumable Insertion ")
    sleep(2) #wait 2 seconds before manifold engagement
    print("Manifold Engagement Started")
    direction = 0x14 #CW
    configure(direction, v_multiplier=1)
    reset_position()
    move(70)
    print("Manifold Engagement Complete")
if program == 2:
    print("Consumable Return Started")
    direction = 0x04 #CCW
    configure(direction, v_multiplier=1)
    reset_position()
    move(200)
    direction = 0x14 #CW
    sleep(5.0)
    configure(direction, v_multiplier=1)
    reset_position()
    move(130)
    print("Consumable Return Complete")
