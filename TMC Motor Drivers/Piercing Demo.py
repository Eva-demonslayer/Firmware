################ Application to Test Pierce, November 2024 demo ################
################################# TMC5240 #####################################
import spidev
from gpiozero import LED
from time import sleep, time
import RPi.GPIO as GPIO
import sys
from lee_ventus_disc_pump import *

#set spi mode 3, double check pi
spi = spidev.SpiDev()
spi.open(0,0) # specify the SPI bus and device (chip select)
Fclk = 5000000  #SPI bus frequency, 5MHz (16MHz doesn't work correctly although advised by tech data sheet as typical)
spi.max_speed_hz = Fclk  #assign SPI frequency
M_step = 256 #microstep variabe, needs update if the register is changed
GPIO.setmode(GPIO.BCM) #set pin numbering for GPIOs

#Pump Variables
# myPump = LVDiscPump()
# bp=LVDiscPump()

def configure(direction_bit): #configures all registers of motor
    spi.xfer2([0x80,0x00,0x00,0x00,direction_bit]) #EN_PWM_MODE=1 enables StealthChop2
    sleep(0.05) 
    signal_check = spi.xfer2([0x00,0x00,0x00,0x00, 0x00]) #signal check
    #print("spi bus communication: ", signal_check)
    spi.xfer2([0x93,0x00,0x00,0x00,0xC8]) #TPWM_THRS=250 yields a switch velocity of about 35000, 30 RPM
    sleep(0.05) 
    spi.xfer2([0xF0,0x00,0x00,0x01,0x80]) #PWMCONF. first byte set to autoscale, minimum setting 0x40. second byte is user defined PWM Grad (1 to 15), third byte is automatic current control
    sleep(0.05) 
    spi.xfer2([0xEC,0x00,0x01,0x00,0x05]) #Chopconf, toff set to 5. MRES (microstep resolution) set to 16 (range is 128,64,32,16,8,4,2,FULLSTEP). 256*200=51200 steps per rotation.
    sleep(0.05)
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

    V_MAX = int(200*M_step) #VMAX, usteps/t
    hex_str = hex(V_MAX)[2:]
    hex_str = hex_str.zfill(4)
    first_part = hex_str[:2]
    second_part = hex_str[2:]
    first_part_hex = (int(first_part, 16))
    second_part_hex = (int(second_part, 16))
    
    spi.xfer2([0xA5,0x00,0x00,0x00,0xFA]) #V1, Threshold velocity, 500 
    sleep(0.05)
    spi.xfer2([0xA7,0x00,0x00,first_part_hex,second_part_hex]) #VMAX, Motion ramp target velocity
    sleep(0.05)
    spi.xfer2([0xA3,0x00,0x00,0x00,0x00]) #VSTART, not used
    sleep(0.05)
    spi.xfer2([0xAB,0x00,0x00,0x00,0x10]) #VSTOP, 10 is mininimum recommended
    sleep(0.05)
    spi.xfer2([0xAA,0x00,0x00,0x00,0xC8]) #D1, deceleration between V1 and VSTOP, 100
    sleep(0.05)
    spi.xfer2([0xA4,0x00,0x00,0x00,0x64]) #A1, first acceleration between VSTART and V1, 100
    sleep(0.05)
    spi.xfer2([0xAF,0x00,0x00,0x01,0x90]) #A2,
    sleep(0.05)
    spi.xfer2([0xA6,0x00,0x00,0x00,0xC8]) #AMAX
    sleep(0.05)
    spi.xfer2([0xAA,0x00,0x00,0x00,0xC8]) #D1, deceleration between V1 and VSTOP, 100
    sleep(0.05)
    spi.xfer2([0xA4,0x00,0x00,0x01,0x90]) #D2,
    sleep(0.05)
    spi.xfer2([0xA8,0x00,0x00,0x00,0xC8]) #DMAX
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
        hex_str = hex_str.zfill(6) #fills in zeros up to 4 digits on the left side
        first_part = hex_str[:2] #removes 4 digits from the right
        second_part = hex_str[2:] #removes 2 digits from the left and right
        second_part = second_part[:2] 
        third_part = hex_str[4:] #removes 4 digits from the left
        first_part_hex = (int(first_part, 16))
        second_part_hex = (int(second_part, 16))
        third_part_hex = (int(third_part, 16))
        my_list.append(first_part_hex) #bits 8-15
        my_list.append(second_part_hex) #bits 0-7
        my_list.append(third_part_hex) #bits 16-23
    elif micro_steps <= 255:
        my_list = [0xAD,0x00,0x00,0x00]
        my_list.append(micro_steps)
        #print("Check step count:", my_list)
    else:
        print("Move Error")
    spi.xfer2(my_list) #send commant to start move
    position_check = 0 #starts as false
    position_bit = 5 #position reached
    while bool(position_check) == False:
        spi.xfer2([0x00,0x00,0x00,0x00,0x00]) #throw out 1st read
        sleep(.05)
        read_data = spi.xfer2([0x00,0x00,0x00,0x00,0x00]) #SPI_STATUS
        #print("status bits: ",read_data)
        sleep(1)
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
def check_in(): # a quick function to check in with the user during the main loop
    all_good = str(input("Press any key to keep going, or X to exit program"))
    if all_good == "x" or all_good == "X":
        sys.exit()
def init():
    myPump.connect_pump(com_port="/dev/ttyUSB3")  # Pump control
    bp.connect_pump(com_port="/dev/ttyACM1")    # Valve control


    # turn off data streaming mode
    myPump.streaming_mode_disable()
    bp.streaming_mode_disable()

    # This function configures both valve output on the GP driver if not set correctly. It should be run once to set
    # the values, then the board should be power cycled (as these settings take effect on startup).
    # The function will automatically be skipped once the valves are configured.
    if bp.read_register(LVRegister.GPIO_B_PIN_MODE) != LVGpioPinMode.OUTPUT_SLOW_MODE_DEF_LOW or \
            bp.read_register(LVRegister.GPIO_C_PIN_MODE) != LVGpioPinMode.OUTPUT_SLOW_MODE_DEF_LOW:
        configure_valves(bp)

    # turn the pump off whilst configuring system
    myPump.write_reg(LVRegister.PUMP_ENABLE, 0)
    pumpOn=False


    # set the pump to PID pressure control with target pressure to the SetVal register (to negative value)
    myPump.set_pid_digital_pressure_control_with_set_val(p_term=-80, i_term=0.1)

    print("Pump is Ready!")
def configure_valves(disc_pump_instance: LVDiscPump):
    """
    This function configures both valve output on the GP driver. It should be run once to set the values, then the
    board should be power cycled and the rest of the program can resume.
    GPIO B (Valve 1) needs to be set to "slow mode default off" (default pin mode is in "fast mode default off").
    GPIO C (Valve 2) needs to be set to "slow mode default off" (default pin mode is in "slow mode default off").
    "Slow mode" allows for longer pulses (up to 30s) to be generated, however it has a lower time resolution of 1ms.
    "Fast mode" allows for more accurate pulses to be generated (resolution of 10us), however they are limited to 300ms.
    For more information check the Development Kit User Manual.
    """

    # set both valve outputs to be slow mode default off
    disc_pump_instance.write_reg(LVRegister.GPIO_B_PIN_MODE, LVGpioPinMode.OUTPUT_SLOW_MODE_DEF_LOW)    # Valve 1
    disc_pump_instance.write_reg(LVRegister.GPIO_C_PIN_MODE, LVGpioPinMode.OUTPUT_SLOW_MODE_DEF_LOW)    # Valve 2

    # store settings to the board
    disc_pump_instance.store_current_settings_to_board()

    # close serial port
    disc_pump_instance.disconnect_pump()

    while True:
        print("Valves have been configured. Power cycle the board and restart the program.")
        time.sleep(60)
def exit_pump():
    # turn the pump off
    bp.write_reg(LVRegister.GPIO_B_STATE, 0, sleep_after=0)     # Valve 2
    bp.write_reg(LVRegister.GPIO_C_STATE, 0, sleep_after=0)
    myPump.write_reg(LVRegister.PUMP_ENABLE, 0)
    bp.write_reg(LVRegister.PUMP_ENABLE, 0)
    # close serial port / I2C connection
    myPump.disconnect_pump()
    bp.disconnect_pump()
    print("Pump is Closed")
def main(): #main program
    program = 0
    gear_ratio = 7.75
    direction = 0x14 #CW
    configure(direction)
    sleep(0.05)
    while program != 4:
        program = int(input("Enter 1 for test revolution, 2 to jog the motor home, or 3 to begin piercing sequence, or 4 to exit ")) #user input for which program to use
        if program == 1:
            print("Test revolution has begun")
            reset_position()
            sleep(0.05)
            move(200*gear_ratio) #1.5:1 gear reduction, 5:1 gear box. 7.5:1 total ratio
        elif program == 2:
            reset_position()
            move(gear_ratio)
            command = 2
            while command == 2:
                reset_position()
                sleep(0.05)
                move(10*gear_ratio)
                command = int(input("Home yet? Enter 2 to get closer and or any other number key to terminate program "))
            reset_position()
        elif program == 3:
            print("Piercing sequence has begun")
            reset_position()
            sleep(0.05)
            move(200*gear_ratio)
            # negative pressure @-200
            # myPump.write_reg(LVRegister.SET_VAL, -300) #Set to -200
            # bp.write_reg(LVRegister.GPIO_B_STATE, -1, sleep_after=0)     # Valve 1
            # bp.write_reg(LVRegister.GPIO_C_STATE, -1, sleep_after=0)     # Valve 2
            # myPump.write_reg(LVRegister.PUMP_ENABLE, 1) #Turn on pump
            # drain lysis, wash1, and wash2
            # sleep for 10
            # sleep(15)
            # check_in()
            # move((200)*gear_ratio)
            # negative pressure and hold
            # n=30
            # sleep(40)
            # for i in range(n):
                # print(myPump.read_register(LVRegister.MEAS_DIGITAL_PRESSURE))
                # sleep(1)
            # vent
            # bp.write_reg(LVRegister.GPIO_B_STATE, 0, sleep_after=0)     # Valve 1
            # bp.write_reg(LVRegister.GPIO_C_STATE, 0, sleep_after=0)     # Valve 2
            # myPump.write_reg(LVRegister.PUMP_ENABLE, 0) #Turn off pump
            # drain elution and CAM shaft is back at home
        else:
            print("Invalid Command. Enter 1 for test revolution, 2 to jog the motor home, or 3 to begin piercing sequence ")
# init()
main() #run the main program
# exit_pump()
