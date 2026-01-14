###################### Mag_Encoder ############################
##################### MA780 from MPS ##########################

import signal
import sys
import spidev
from time import sleep, time
import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio" 
from gpiozero import DigitalOutputDevice
import atexit

spi1 = spidev.SpiDev()
spi1.open(0,0)                   # specify the SPI bus and device (chip select)
spi1.mode = 0                    # spi mode 0 start. CPOL=0, CPHA=0.
spi1.max_speed_hz = 5000000      # assign SPI frequency, max clock rate 25 MHz for MA780

# command set
Read_Angle = 0x00               # returns angle value (16 bits)
Read_Register = 0x02            # returns 8-bit angle + register value
Write_Register = 0x04           
Store_Single_Register = 0xE0    
Store_All_Registers = 0xC0      
Restore_All_Registers = 0xA0    
Clear_Error_Flag = 0x20         

# registry for address->name lookup
REGISTER_NAMES = {}

def reg(name: str, value: int) -> int:
    """Create a global constant named `name` with `value` and record its name."""
    globals()[name] = value
    REGISTER_NAMES[value] = name
    return value

# register map addresses
Zero_Setting_LSB = reg("Zero_Setting_LSB", 0x00)
Zero_Setting_MSB = reg("Zero_Setting_MSB", 0x01)
Bias_Trimming_Current = reg("Bias_Trimming_Current", 0x02)
Enable_Trimming_Current = reg("Enable_Trimming_Current", 0x03)
Cycle_Time_LSB = reg("Cycle_Time_LSB", 0x04)
Cycle_Time_MSB = reg("Cycle_Time_MSB", 0x05)
Filter_Settings = reg("Filter_Settings", 0x06)
On_Time = reg("On_Time", 0x07)
Threshold = reg("Threshold", 0x08)
Rotation_Direction = reg("Rotation_Direction", 0x09)
Reference = reg("Reference", 0x0A)
ASC_ASCR_FW = reg("ASC_ASCR_FW", 0x0B)
Multi_turns = reg("Multi_turns", 0x16)
Eeprom = reg("Eeprom", 0x1A)

# write register operation is two 16 bit frames
# first frame is 3 bit write command, followed by 5 bit register address
# and lastly register value to write
Write_Command = 0x04
Read_Command = 0x02
Store_Single_Register = 0x07
Store_All_Registers = 0x06
Restore_All_Registers = 0x05
Clear_Error_Flag = 0x01

# GPIO17 for enable pin
Enable_GPIO =  17
# enable and disable pin control
def enable_pin():
    en_pin.on()
    return en_pin.value
def disable_pin():
    en_pin.off()
    return en_pin.value
try:
    en_pin = DigitalOutputDevice(Enable_GPIO, active_high=True, initial_value=True)  # high = sensor active
    pin_state = enable_pin()
    print("Enable Pin State:", pin_state)
except Exception as e:
    # If claiming the pin fails, do nothing (leave en_pin as None)
    en_pin = None
    print(f"Warning: could not claim GPIO17: {e}")

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
signal.signal(signal.SIGINT, signal_handler)   # Ctrl-C
signal.signal(signal.SIGTERM, signal_handler)  # kill/terminate

# build 16-bit frame for read/write operations
def build_frame(cmd, addr, value):
    
    # bits 15-13 : cmd (3 bits)
    # bits 12-8  : addr (5 bits)
    # bits 7-0   : value (8 bits)
    
    cmd &= 0x07
    addr &= 0x1F
    value &= 0xFF
    return (cmd << 13) | (addr << 8) | value
def write_register(addr, value):
    frame = build_frame(Write_Command, addr, value)
    msb = (frame >> 8) & 0xFF
    lsb = frame & 0xFF
    spi1.xfer2([msb, lsb])
    sleep(0.05)
    resp2 = spi1.xfer2([0x00, 0x00])                      # dumby write to read response
    sleep(0.05)
    if resp2[1] != value:
        print("Error in write response: ", resp2)        # check that value is returned after write
def read_register(addr):
    frame = build_frame(Read_Command, addr, 0x00)
    msb = (frame >> 8) & 0xFF
    msb_check = (msb & 0xE0) >> 5                        # extract command bits for verification
    print("Read Command: ", msb_check)                   # should be 0b010 for read
    lsb = frame & 0xFF
    spi1.xfer2([msb, lsb])
    sleep(0.05)
    resp = spi1.xfer2([0x00, 0x00])                       # dumby write to read response
    sleep(0.05)
    # print("Current Angle Value: ", resp[0])          
    print("Values stored in register: ", resp[1])        # values stored in register
    return resp[1]

# set magnet ratio adjustment
def set_magnet_ratio(enable, bias_value):
    # set bias trimming current to adjust magnet ratio
    write_register(Bias_Trimming_Current, bias_value) 
    sleep(0.05)
    # enable trimming current for X and Y axis
    write_register(Enable_Trimming_Current, enable)
    sleep(0.05)

# set zero position to current angle
def set_zero_position():
    raw_bytes = spi1.xfer2([Read_Angle, 0x00])       # returns [MSB, LSB]
    msb, lsb = raw_bytes[0], raw_bytes[1]           # retrieve MSB and LSB
    raw16 = (msb << 8) | lsb                        # 16-bit integer from sensor
    zero_lsb = raw16 & 0xFF                         # LSB for zero setting
    zero_msb = (raw16 >> 8) & 0xFF                  # MSB for zero setting

    print(f"Setting zero position to raw16: {raw16} bytes: {raw_bytes}")
    resp1, resp2 = write_register(Zero_Setting_LSB, zero_lsb)
    print(f"Write Zero Setting LSB Response: {resp1}, {resp2}")
    resp1, resp2 = write_register(Zero_Setting_MSB, zero_msb)
    print(f"Write Zero Setting MSB Response: {resp1}, {resp2}")

# check to ensure read operation works for registers
read_register(Filter_Settings)   
sleep(0.05)

# Adjust magnet ratio as needed for accurate
# set_magnet_ratio(0x00, 0x00)

# set zero position to current angle
# set_zero_position()

##################### TEST LOOP OR ANGULAR READING #############################

def read_angle():
    # ask user for how long to run (seconds). 0 = infinite
    duration_s = int(input("Run duration in seconds (0 for infinite): ") or 0)
    end_time = (time() + duration_s) if duration_s > 0 else None

    # run until time expires (or forever if end_time is None)
    while end_time is None or time() < end_time:
        raw_bytes = spi1.xfer2([Read_Angle, 0x00])              # returns [MSB, LSB]
        msb, lsb = raw_bytes[0], raw_bytes[1]                  # retrieve MSB and LSB
        raw16 = (msb << 8) | lsb                               # 16-bit integer from sensor
        angle_deg = raw16 * (359.995 / 65535)                  # map 16-bit 
    
        print(f"raw16: {raw16} bytes: {raw_bytes}  angle_deg: {angle_deg:.3f}°")
        sleep(0.5)

    clean_up()

# run test loop if executed as main script
if __name__ == "__main__":
    read_angle()