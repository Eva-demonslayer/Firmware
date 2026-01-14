################# Motor_Optical_Encoder ###################
####################### TMC5130 ###########################

import signal
import sys
import spidev
from time import sleep, time
import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio" 
from gpiozero import DigitalOutputDevice
import atexit

spi0 = spidev.SpiDev()
spi0.open(0,1)                   # specify the SPI bus and device (chip select)
spi0.mode = 0                    # spi mode 0 start. CPOL=0, CPHA=0.
spi0.max_speed_hz = 5000000      # assign SPI frequency, max clock rate 25 MHz

position_bit = 5                # position reached
CW = 0x14                       # CW
CCW = 0x04                      # CCW
N_event = 26                    # GPIO of N channel for encoder
microsteps = 16                 # microstepping value

def enable_pin():
    en_pin.on()
    return en_pin.value
def disable_pin():
    en_pin.off()
    return en_pin.value
try:
    en_pin = DigitalOutputDevice(N_event, active_high=True, initial_value=False)  # high = sensor active, starting low = disabled
except Exception as e:
    # If claiming the pin fails, do nothing (leave en_pin as None)
    en_pin = None
    print(f"Warning: could not claim GPIO26: {e}")

 # cleanup function to release resources
def clean_up():
    """cleanup for en_pin and spi"""
    for name in ("en_pin", "spi"):
        obj = globals().get(name)
        if obj is None:
            continue
        try:
            # turn off if available (safe no-op if not)
            getattr(obj, "off", lambda: None)()
        except Exception:
            pass
        try:
            # close if available
            getattr(obj, "close", lambda: None)()
        except Exception:
            pass
atexit.register(clean_up)

# ensure cleanup on SIGINT / SIGTERM and on normal exit
def signal_handler(*_):
    try:
        clean_up()
    finally:
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)            # Ctrl-C
signal.signal(signal.SIGTERM, signal_handler)           # kill/terminate   

def configure(direction_bit):                           # configures all registers of motor
    spi0.xfer2([0x80,0x00,0x00,0x00,direction_bit])      # EN_PWM_MODE=1 enables StealthChop (with default PWMCONF = 0x00050480)
    sleep(0.05) 
    spi0.xfer2([0x93,0x00,0x00,0x01,0xF4])               # TPWM_THRS=500 yields a switch velocity of about 35000, 30 RPM
    sleep(0.05) 
    spi0.xfer2([0xF0,0x00,0x04,0x01,0x80])               # PWMCONF. first byte set to autoscale, minimum setting 0x40. second byte is user defined PWM Grad (1 to 15), third byte is automatic current control
    sleep(0.05) 
    spi0.xfer2([0xEC,0x04,0x01,0x00,0x04])               # Chopconf, toff set to 5. MRES (microstep resolution) set to 16 (range is 128,64,32,16,8,4,2,FULLSTEP). 200*16=3200 steps per rotation.
    sleep(0.05)
    spi0.xfer2([0xA0,0x00,0x00,0x00,0x00])               # RAMPMODE (target position move)  
    sleep(0.05)
    spi0.xfer2([0x90,0x00,0x01,0x1F,0x00])               # ihold_irun. Bits 0-4 hold current, 8-12 motor current. 16-19 IHOLDDELAY
    sleep(0.05)                                         # Run Current Scaling Factor set to 31, no hold current, minimal delay. 
    spi0.xfer2([0x91,0x00,0x00,0x00,0x0A])               # TPOWERDOWN=10, delay before power down at standstill
    sleep(0.05)
    spi0.xfer2([0xA5,0x00,0x00,0x00,0xFA])               # V1, Threshold velocity, 250 
    sleep(0.05)
    spi0.xfer2([0xA7,0x00,0x00,0x03,0xE8])               # VMAX, 1000
    sleep(0.05)
    spi0.xfer2([0xA3,0x00,0x00,0x00,0x00])               # VSTART, not used
    sleep(0.05)
    spi0.xfer2([0xAB,0x00,0x00,0x00,0x10])               # VSTOP, 10 is mininimum recommended
    sleep(0.05)
    spi0.xfer2([0xAA,0x00,0x00,0x00,0x64])               # D1, deceleration between V1 and VSTOP, 100
    sleep(0.05)
    spi0.xfer2([0xA4,0x00,0x00,0x00,0x64])               # A1, first acceleration between VSTART and V1, 100
    sleep(0.05)
    spi0.xfer2([0xA6,0x00,0x00,0x00,0x32])               # AMAX, 50
    sleep(0.05)
    spi0.xfer2([0xA8,0x00,0x00,0x00,0x32])               # DMAX, 50
    sleep(0.05)
def read_position():                                    # reads actual position from motor
    position_check = 0
    sleep(.05)
    while bool(position_check) == False:                # loop until position reached bit is set
        spi0.xfer2([0x00,0x00,0x00,0x00,0x00])           # throw out 1st read
        sleep(.05)
        read_data = spi0.xfer2([0x00,0x00,0x00,0x00,0x00])
        sleep(.05)
        hex_data = int(read_data[0])
        position_check=(hex_data >> position_bit) & 1   # bitwise AND operation with a mask of 1
def reset_position():                                   # resets actual position to 0        
    spi0.xfer2([0xA1,0x00,0x00,0x00,0x00])               # XACTUAL reset
    sleep(0.1)
def single_move(displacement):                          # single move command to motor
    reset_position()
    print("Single move in degrees:", displacement)
    disp = (displacement * microsteps)/1.8              # microstepping and divide by 1.8 to get steps per degree
    disp = int(disp)
    if disp < 255:
        my_list = [0xAD,0x00,0x00,0x00]
        my_list.append(disp)
    elif disp < 65535:                                  
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
    spi0.xfer2(my_list)                                  # send move command to motor
    encoder_disp = read_encoder()                       # read encoder position
    return encoder_disp                                 # return encoder position for comparison
def encoder_config():                                   # configures encoder registers    
    sleep(0.05)
    spi0.xfer2([0xB8,0x00,0x00,0x01,0x5C])               # ENCMODE Encoder config and use of N channel
    sleep(0.05)
    enc_mode = spi0.xfer2([0x38,0x00,0x00,0x00,0x00])    # ENCMODE read back
    sleep(0.05)
    print("enc_mode =", enc_mode)
    #pol_A and pol_B  at neg. pol_N = high active
    #ignore AB polarity for N event, manual event trigger from pi
    #pos_edge =  01, N channel is valid upon active going N event
    #clr_cont =  Always latch or latch and clear X_ENC upon an N event
    #encoder prescaler divisor binary mode
    #clr_enc_x = 1, latch and additionally clear encoder counter X_ENC at N-event
    spi0.xfer2([0xBA,0x00,0x01,0x1C,0x71]) # Accumulation constant, current microstepping. X_ENC accumulates +/- ENC_CONST / (2^16*X_ENC) (binary)
def reset_encoder():                                    # resets encoder position to 0
    try:
        pin_state = enable_pin()
        print("Enable Pin State:", pin_state)
        sleep(0.3)
        pin_state = disable_pin()
        print("Enable Pin State:", pin_state)
        sleep(0.3)
    except Exception as e:
        print(f"Warning: could not claim GPIO26: {e}")
    status = spi0.xfer2([0x3B,0x00,0x00,0x00,0x00])      # throw out 1st read
    sleep(0.3)
    status = spi0.xfer2([0x3B,0x00,0x00,0x00,0x00])      # ENC_Status, Read and Clear
    print("Encoder Position Cleared")
    sleep(0.3)
    print("N Status after low polarity. If LSB is 1, N event detected ", status)
    enc_latch = spi0.xfer2([0x3C,0x00,0x00,0x00,0x00])   # throw out 1st read
    sleep(1.5)
    enc_latch = spi0.xfer2([0x3C,0x00,0x00,0x00,0x00])   # Encoder position X_ENC latched on N event
    print("Encoder latch position after reset:", enc_latch)
def read_encoder():                                     # reads actual encoder position
    x_enc = spi0.xfer2([0x39,0x00,0x00,0x00,0x00])       # throw out 1st read
    sleep(0.05)
    x_enc = spi0.xfer2([0x39,0x00,0x00,0x00,0x00])       # X_ENC actual encoder position read 
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
    distance = enc_cycles/((microsteps/1.8))            # current micro step and divided by full steps per degree
    # print("x_enc in degrees:", distance)
    return distance

################## TEST CODE FOR MOTOR/ENCOER FUNCTION ######################

def test_loop():
    configure(CW)                                            # configure motor with direction and settings
    reset_position()                                         # reset motor position to 0
    single_move(0)
    sleep(0.1)

    encoder_config()                                        # configure encoder settings
    sleep(0.1)
    reset_encoder()                                         # reset encoder position to 0
    sleep(0.1)                        

    for i in range(4):       
        encoder_value = single_move(90)                     # move motor CW 360 degrees
        read_position()                                     # read intended motor position
        print("Encoder position in degrees:", encoder_value)
        sleep(0.2)

    clean_up()                                              # cleanup resources    

#  run test loop if executed as main program
if __name__ == "__main__":              
    test_loop()                                             