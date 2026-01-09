################# Motor_Optical_Encoder ###################
####################### TMC5130 ###########################

import spidev
from time import sleep
spi = spidev.SpiDev()
spi.open(0,1)                   # specify the SPI bus and device (chip select)
spi.mode = 0                    # spi mode 0 start. CPOL=0, CPHA=0.
spi.max_speed_hz = 5000000      # assign SPI frequency, max clock rate 25 MHz

position_bit = 5        # position reached
home_bit = 6            # left home reached
encode = 0              # Encoder value

def configure(direction_bit):                           # configures all registers of motor
    spi.xfer2([0x80,0x00,0x00,0x00,direction_bit])      # EN_PWM_MODE=1 enables StealthChop2
    sleep(0.05) 
    # T_step = spi.xfer2([0x12,0x00,0x00,0x00,0x00])    # T_STEP = Actual measured time between two 1/256 microsteps derived from the step input frequency in units of 1/fCLK. 
    # sleep(0.05) 
    # Read out TSTEP when moving at the desired velocity and program the resulting value to TPWMTHRS. Use a low transfer velocity to avoid a jerk at the switching point.
    spi.xfer2([0x93,0x00,0x00,0x00,0x30])               # TPWM_THRS=250, change for switching velocity between spreadcycle and stealthchop 
    sleep(0.05) 
    spi.xfer2([0xF0,0x00,0x00,0x01,0x80])               # PWMCONF. first byte set to autoscale, minimum setting 0x40. second byte is user defined PWM Grad (1 to 15), third byte is automatic current control
    sleep(0.05) 
    spi.xfer2([0xEC,0x04,0x01,0x00,0x05])               # Chopconf, toff set to 5. MRES (microstep resolution) set to 256 (range is 128,64,32,16,8,4,2,FULLSTEP). 256*200=51200 steps per rotation.
    sleep(0.05)
    # toff or "Slow decay time" in a motor refers to the time it takes for the current flowing through the motor windings to decrease to zero at a slow rate after power is removed
    spi.xfer2([0x8A,0x00,0x00,0x00,0x01])               # DRV_Conf, 2 amp motor current
    sleep(0.05)
    spi.xfer2([0xA0,0x00,0x00,0x00,0x00])               # RAMPMODE (target position move)  
    sleep(0.05)
    spi.xfer2([0x90,0x00,0x01,0x1F,0x00])               # ihold_irun. Bits 0-4 hold current, 8-12 motor current. 16-19 IHOLDDELAY
    sleep(0.05)                                         # Run Current Scaling Factor set to 31, no hold current, minimal delay. 
    spi.xfer2([0x91,0x00,0x00,0x00,0x0A])               # TPOWERDOWN=10, delay before power down at standstill
    sleep(0.05)
    #SW_mode = spi.xfer2([0x34,0x00,0x00,0x00,0x00])     # read Switch Mode Configuration, no automatic motor stops at home flags
    # print("SW bits: ", SW_mode)
    # print("motor configured", direction_bit)
def read_position():                                    # reads actual position from motor
    home_check = 0
    position_check = 0
    sleep(.05)
    while bool(position_check) == False and bool(home_check) == False:
        spi.xfer2([0x00,0x00,0x00,0x00,0x00])                           # throw out 1st read
        sleep(.05)
        read_data = spi.xfer2([0x00,0x00,0x00,0x00,0x00])               # SPI_STATUS
        sleep(.05)
        hex_data = int(read_data[0])
        position_check=(hex_data >> position_bit) & 1                   # bitwise AND operation with a mask of 1
        home_check=(hex_data >> home_bit) & 1                           # bitwise AND operation with a mask of 1
def reset_position():                                   # resets actual position to 0        
    spi.xfer2([0xA1,0x00,0x00,0x00,0x00])               # XACTUAL reset
    sleep(0.05)
def single_move(displacement):                          # single move command to motor
    reset_position()
    print("Single move in degrees:", displacement)
    disp = displacement * (16)                  # microstepping... and divide by 2?
    disp = int(disp)
    #print("actual position as decimal", disp)
    read_data = spi.xfer2([0x2D,0x00,0x00,0x00,0x00])   # throw out 1st read
    sleep (0.05)
    read_data = spi.xfer2([0x2D,0x00,0x00,0x00,0x00])   # second read, actual position
    #print("actual position", read_data)
    if disp < 255:
        my_list = [0xAD,0x00,0x00,0x00]
        my_list.append(disp)
    elif displacement < 65535:                          # was "displacement", changed it to disp
        my_list = [0xAD,0x00,0x00]
        hex_str = hex(disp)[2:]
        hex_str = hex_str.zfill(4)
        first_part = hex_str[:2]
        second_part = hex_str[2:]
        first_part_hex = (int(first_part, 16))
        second_part_hex = (int(second_part, 16))
        my_list.append(first_part_hex)
        my_list.append(second_part_hex)
    else:
        print("move it too large")
    spi.xfer2(my_list)
    print("Single Move Started!")
def encoder_config():                                   # configures encoder registers    
    sleep(0.05)
    spi.xfer2([0xB8,0x00,0x00,0x01,0x5C])               # ENCMODE Encoder config and use of N channel
    sleep(0.05)
    enc_mode = spi.xfer2([0x38,0x00,0x00,0x00,0x00])    # ENCMODE read back
    sleep(0.05)
    print("enc_mode =", enc_mode)
    #pol_A and pol_B  at neg. pol_N = high active
    #ignore AB polarity for N event, manual event trigger from pi
    #pos_edge =  01, N channel is valid upon active going N event
    #clr_cont =  Always latch or latch and clear X_ENC upon an N event
    #encoder prescaler divisor binary mode
    #clr_enc_x = 1, latch and additionally clear encoder counter X_ENC at N-event
    spi.xfer2([0xBA,0x00,0x01,0x1C,0x71]) #Accumulation constant, current microstepping. X_ENC accumulates +/- ENC_CONST / (2^16*X_ENC) (binary)
def reset_encoder():                                    # resets encoder position to 0
    encoder_config()
    sleep(0.05)
    N=16
    GPIO.output(N, GPIO.HIGH)                           # triggers N event and clears X_ENC
    sleep(0.1)
    GPIO.output(N, GPIO.LOW)
    sleep(0.1)
    status = spi.xfer2([0x3B,0x00,0x00,0x00,0x00])      # throw out 1st read
    sleep(0.3)
    status = spi.xfer2([0x3B,0x00,0x00,0x00,0x00])      # ENC_Status, Read and Clear
    print("Encoder Position Cleared")
    sleep(0.3)
    print("N Status after low polarity. Bit1=N event detected", status)
    enc_latch = spi.xfer2([0x3C,0x00,0x00,0x00,0x00])   # throw out 1st read
    sleep(1.5)
    enc_latch = spi.xfer2([0x3C,0x00,0x00,0x00,0x00])   # Encoder position X_ENC latched on N event
def read_encoder():                                     # reads actual encoder position
    x_enc = spi.xfer2([0x39,0x00,0x00,0x00,0x00])       # throw out 1st read
    sleep(0.05)
    x_enc = spi.xfer2([0x39,0x00,0x00,0x00,0x00])       # X_ENC actual encoder position read 
    print("x_enc read register:",x_enc)
    position_2 = hex(x_enc[4])                          # store data from bytes in separate variables
    position_1 = hex(x_enc[3]) 
    hex_value_2 = position_2[2:]                        # trim the 0x from the hex values
    hex_value_1 = position_1[2:]
    combine_str = str(hex_value_1) + str(hex_value_2)   # combine the trimmed values into one string
    combine_str = combine_str.zfill(4)                  # fill in any missing values for 4 digits
    enc_cycles = int(combine_str,16)                    # change to hex, and then back to integer
    if enc_cycles >= 32768:                             # Check to see if this number is a negative number
        enc_cycles -= 65536                             # If so, compensate it with 65536
    distance = enc_cycles/((16))                            # current micro step and divided by 2 same as position command?
    print("x_enc in degrees:", distance)
    return distance

def motor_move(move_direction, revolution):             # main function to move motor
    configure(move_direction)                           # configure motor with direction  
    reset_position()                                    # reset position motor position to 0
    reset_encoder()                                     # reset encoder position to 0
    single_move(revolution)                             # single move command with displacement
    read_position()                                     # read intended motor position
    angular_disp = read_encoder()                       # read encoder position
    print("Encoder position in degrees:", angular_disp)
    return angular_disp                                 # return encoder position for comparison