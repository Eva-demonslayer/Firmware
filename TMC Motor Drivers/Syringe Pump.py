############################## Syringe Pump ###################################
################################# TMC5240 #####################################

import spidev
from time import sleep, time
import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio" 
import gpiozero

spi = spidev.SpiDev()
spi.open(0,0) # specify the SPI bus and device (chip select)
spi.mode = 3 #double check if it works in mode 3, pg 25 of data sheet
Fclk = 12500000  #Internal clock frequency of the TMC5240 when pin is pulled to ground, 12.5MHz
spi.max_speed_hz = 5000000  #assign SPI frequency
M_step = 16 #microstep variabe, needs update if the register is changed

######################### FUNCTIONS ###################################

def configure(direction_bit, velocity): #configures all registers of motor
    spi.xfer2([0x80,0x00,0x00,0x00,direction_bit]) #EN_PWM_MODE=1 enables StealthChop2
    sleep(0.05) 
    T_step = spi.xfer2([0x12,0x00,0x00,0x00,0x00]) #T_STEP = Actual measured time between two 1/256 microsteps derived from the step input frequency in units of 1/fCLK. 
    sleep(0.05) 
    #Read out TSTEP when moving at the desired velocity and program the resulting value to TPWMTHRS. Use a low transfer velocity to avoid a jerk at the switching point.
    spi.xfer2([0x93,0x00,0x00,0x00,0x30]) #TPWM_THRS=250, change for switching velocity between spreadcycle and stealthchop 
    sleep(0.05) 
    spi.xfer2([0xF0,0x00,0x00,0x01,0x80]) #PWMCONF. first byte set to autoscale, minimum setting 0x40. second byte is user defined PWM Grad (1 to 15), third byte is automatic current control
    sleep(0.05) 
    spi.xfer2([0xEC,0x04,0x01,0x00,0x05]) #Chopconf, toff set to 5. MRES (microstep resolution) set to 256 (range is 128,64,32,16,8,4,2,FULLSTEP). 256*200=51200 steps per rotation.
    sleep(0.05)
    #toff or "Slow decay time" in a motor refers to the time it takes for the current flowing through the motor windings to decrease to zero at a slow rate after power is removed
    spi.xfer2([0x8A,0x00,0x00,0x00,0x01]) #DRV_Conf, 2 amp motor current
    sleep(0.05)
    spi.xfer2([0xA0,0x00,0x00,0x00,0x00]) #RAMPMODE (target position move)  
    sleep(0.05)
    spi.xfer2([0x90,0x00,0x01,0x1F,0x00]) #ihold_irun. Bits 0-4 hold current, 8-12 motor current. 16-19 IHOLDDELAY
    sleep(0.05)                           #Run Current Scaling Factor set to 31, no hold current, minimal delay. 
    spi.xfer2([0x91,0x00,0x00,0x00,0x0A]) #TPOWERDOWN=10, delay before power down at standstill
    sleep(0.05)
    SW_mode = spi.xfer2([0x34,0x00,0x00,0x00,0x00]) #read Switch Mode Configuration, no automatic motor stops at home flags
    #print("SW bits: ", SW_mode)
    #print("motor configured", direction_bit)
 
#################### time step calculations ########################

    #page 50 of tech data sheet shows ramp parameters vs real world unit calculations
    T_step = spi.xfer2([0x12,0x00,0x00,0x00,0x00])
    #print("T_step: ", T_step) #Actual measured time between two 1/256 microsteps derived from the step input frequency in units of 1/fCLK
    tstep_list= [0x00,0x00,0x00] #creat new array for hex values
    for i in range (0,3):
        tstep_list[i]= hex(T_step[i])[2:] #populate new array with hex values
        #print("T_step array position ", i, ": ",tstep_list[i])
    T_step_hex = tstep_list[2]+tstep_list[1]+tstep_list[0] #combine all 3 bytes into one hex value
    T_step_int = int(T_step_hex,16) #change the combination of all 3 bytes to an integer
    #print("T_step as single integer: ", T_step_int)
    
    TPWM_THRS = spi.xfer2([0x13,0x00,0x00,0x00,0x00])
    #print("TPWM_THRS: ", TPWM_THRS)
    tpwm_list= [0x00,0x00,0x00] #creat new array for hex values
    for i in range (0,3):
        tpwm_list[i]= hex(TPWM_THRS[i])[2:] #populate new array with hex values
        #print("T_step array position ", i, ": ",tpwm_list[i])
    tpwm_hex = tpwm_list[2]+tpwm_list[1]+tpwm_list[0] #combine all 3 bytes into one hex value
    tpwm_int = int(tpwm_hex,16) #change the combination of all 3 bytes to an integer
    #print("TPWM_THRS as single integer: ", tpwm_int)

################## velocity and acceleration parameters #####################

    V_MAX = int(velocity) #VMAX, usteps/t
    print("V_MAX ", V_MAX)
    V1 = int(V_MAX * 0.1) #threshold for starting acceleration
    V2 = int(V_MAX * 0.9) #threshld right before achieving maximum velocity
    A1 = V_MAX #gentle stop to acceleration
    A2 = V_MAX * 2 # main acceleration, change to increase acceleration slope
    A_MAX = V_MAX #gentle stop to acceleration
    Motion = [V1, V2, A1, A2, A_MAX, V_MAX] #list of velocity and acceleration variables
    print("Motion Array ", Motion)
    Motion_Hex = [] #initialize list of hex values for velocity and acceleration
    for i in range(len(Motion)):
        hex_str = hex(Motion[i])[2:] #brackets remove 0x from string
        hex_str = hex_str.zfill(6) #fills in zeros up to 4 digits on the left side
        first_part = hex_str[:2] #removes 4 digits from the right
        second_part = hex_str[2:] #removes 2 digits from the left and right
        second_part = second_part[:2] 
        third_part = hex_str[4:] #removes 4 digits from the left
        first_part_hex = (int(first_part, 16))
        second_part_hex = (int(second_part, 16))
        third_part_hex = (int(third_part, 16))
        Motion_Hex.append(first_part_hex) #bits 16-23
        Motion_Hex.append(second_part_hex) #bits 8-15
        Motion_Hex.append(third_part_hex) #bits 0-7

    spi.xfer2([0xA5,0x00,Motion_Hex[0],Motion_Hex[1],Motion_Hex[2]]) #V1, 100
    sleep(0.05)
    spi.xfer2([0xAE,0x00,Motion_Hex[3],Motion_Hex[4],Motion_Hex[5]]) #V2, 400
    sleep(0.05)
    spi.xfer2([0xA7,0x00,Motion_Hex[15],Motion_Hex[16],Motion_Hex[17]]) #VMAX, Motion ramp target velocity
    sleep(0.05)
    spi.xfer2([0xA3,0x00,0x00,0x00,0x00]) #VSTART, not used
    sleep(0.05)
    spi.xfer2([0xAB,0x00,0x00,0x00,0x10]) #VSTOP, 10 is mininimum recommended
    sleep(0.05)
    spi.xfer2([0xA4,0x00,Motion_Hex[6],Motion_Hex[7],Motion_Hex[8]]) #A1, 400, first acceleration between VSTART and V1
    sleep(0.05)
    spi.xfer2([0xAF,0x00,Motion_Hex[9],Motion_Hex[10],Motion_Hex[11]]) #A2, 800, second acceleration betwee V1 and V2
    sleep(0.05)
    spi.xfer2([0xA6,0x00,Motion_Hex[12],Motion_Hex[13],Motion_Hex[14]]) #AMAX, 400, think acceleration between V2 and V_MAC
    sleep(0.05)
    spi.xfer2([0xAA,0x00,Motion_Hex[6],Motion_Hex[7],Motion_Hex[8]]) #D1, same as A1
    sleep(0.05)
    spi.xfer2([0xA4,0x00,Motion_Hex[9],Motion_Hex[10],Motion_Hex[11]]) #D2, same as A2
    sleep(0.05)
    spi.xfer2([0xA8,0x00,Motion_Hex[12],Motion_Hex[13],Motion_Hex[14]]) #DMAX, same as AMAX
    sleep(0.05)
def move(pulse): #single motor move
    micro_steps = int((pulse * M_step))
    if micro_steps <= 65535 and micro_steps > 255: 
        my_list = [0xAD,0x00,0x00]
        hex_str = hex(micro_steps)[2:] #brackets remove 0x from string
        hex_str = hex_str.zfill(4) #fills in zeros up to 4 digits on the left side
        first_part = hex_str[:2] #removes 2 digits from the right
        second_part = hex_str[2:] #removes 2 digits from the left
        first_part_hex = (int(first_part, 16))
        second_part_hex = (int(second_part, 16))
        my_list.append(first_part_hex) #bits 8-15
        my_list.append(second_part_hex) #bits 0-7
    elif micro_steps <= 16777215 and micro_steps > 65535:
        my_list = [0xAD,0x00]
        hex_str = hex(micro_steps)[2:] #brackets remove 0x from string
        hex_str = hex_str.zfill(6) #fills in zeroes up to 4 digits on the left side
        first_part = hex_str[:2] #removes 4 digits from the right
        second_part = hex_str[2:] #removes 2 digits from the left and right
        second_part = second_part[:2] 
        third_part = hex_str[4:] #removes 4 digits from the left
        first_part_hex = (int(first_part, 16))
        second_part_hex = (int(second_part, 16))
        third_part_hex = (int(third_part, 16))
        my_list.append(first_part_hex) #bits 16-23
        my_list.append(second_part_hex) #bits 8-15
        my_list.append(third_part_hex) #bits 0-7
    elif micro_steps <= 255:
        my_list = [0xAD,0x00,0x00,0x00]
        my_list.append(micro_steps)
        #print("Check step count:", my_list)
    else:
        print("Move Error")
    spi.xfer2(my_list) #send command to start move
    position_check = 0 #starts as false
    position_bit = 5 #position reached
    while bool(position_check) == False:
        spi.xfer2([0x00,0x00,0x00,0x00,0x00]) #throw out 1st read
        sleep(.05)
        read_data = spi.xfer2([0x00,0x00,0x00,0x00,0x00]) #SPI_STATUS
        #print("status bits: ",read_data)
        sleep(0.05)
        hex_data = int(read_data[0])
        position_check=(hex_data >> position_bit) & 1 #bitwise AND operation with a mask of 1  
        print("position bit: ",position_check)
def reset_position(): #resets position of motor
    spi.xfer2([0xA1,0x00,0x00,0x00,0x00]) #send command to move nowhere, sets 0 position
    sleep(0.05)
    x_actual = spi.xfer2([0x21,0x00,0x00,0x00,0x00]) #throw out first read
    sleep(0.05)
    x_actual = spi.xfer2([0x21,0x00,0x00,0x00,0x00]) #check position X_actual
    sleep(0.05)
    #print("X_actual: ", x_actual) #print position, should be 0
    spi.xfer2([0xB5,0x00,0x00,0x00,0xCC]) #RAMP_STAT clear all flags
    sleep(0.05)
    Ramp_stat = spi.xfer2([0x35,0x00,0x00,0x00,0x00])
    print("Ramp_stat: ", Ramp_stat) #check for cleared flags

########################### MAIN PROGRAM ##############################

program = 0 #initial variable declaration for user options
micro_steps_revolution = 200 * M_step #microsteps per a revolution assuming 1 rotation per a second
t = (2**24)/Fclk
velocity = micro_steps_revolution * t #initial variable declaration for speed, in case user selects a value out of bounds. 1 RPS
CW = 0x14 #CW
CCW = 0x04 #CCW
dwell_time = 1 # dwell time in each well for thermocycling
well_to_well_move = 1000 #default setting for amount of full steps to transfer fluid one well to another
move_adjust = 100 #small adjustments for the fluid position
#configure(CW,velocity) #initial configuration of motor
sleep(0.05)
while program != 4:
    program = int(input("Enter 1 for jog forward, 2 to jog back, or 3 to begin test sequence. ")) #user input for which program to use
    if program == 1:
        configure(CW,velocity) #initial configuration of motor
        sleep(0.1)
        reset_position()
        sleep(0.1)
        move(move_adjust) #Small move to get fluid in correct position
    elif program == 2:
        configure(CCW,velocity) #initial configuration of motor
        sleep(0.1)
        reset_position()
        sleep(0.1)
        move(move_adjust) #Opposive small move to get fluid in correct position
    elif program == 3:
        Linear_speed= float(input("Enter linear distance per a second between 5 inch/s and 15 inch/s (speed not yet correct) ")) #user input for linear distance/sec. assumes 0.1 inches for lead
        well_to_well_move = int(input("Enter full steps per cycle (200 steps is 0.1 inches of travel) ")) 
        if Linear_speed > 4.9 and Linear_speed < 15.1: #speed limits, more testing required
            velocity_lead_screw = velocity * Linear_speed * 10
        else:
            velocity_lead_screw = velocity * 5 * 10
            print("Speed entered is out of range, running at 5 inches/second instead")
        configure(CW, velocity_lead_screw)
        sleep(0.1)
        reset_position()
        sleep(0.1)
        for i in range (40):
            start_time = time()
            move(well_to_well_move) #first move value for 40x cycle
            end_time = time()
            elapsed_time = round(end_time - start_time, 3)
            print("Travel time for fluid in seconds: ", elapsed_time)
            print("Dwell time in seconds: ",dwell_time)
            sleep(dwell_time)
            #can add a detection dwell time here for future iterations
            move(0) #second move value for 40x cycle
            print("Dwell time in seconds: ",dwell_time)
            sleep(dwell_time)
    else:
        print("Invalid Command. Enter 1 for jog forward, 2 to jog back, or 3 to begin test sequence.  ")


