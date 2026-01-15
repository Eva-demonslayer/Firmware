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
    en_pin = DigitalOutputDevice(Enable_GPIO, active_high=True, initial_value=False)
    # ensure pin is low (sensor inactive) at start
    disable_pin() 
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
signal.signal(signal.SIGINT, signal_handler)        # Ctrl-C
signal.signal(signal.SIGTERM, signal_handler)       # kill/terminate

# build 16-bit frame for read/write operations
def build_frame(cmd, addr, value):
    
    # bits 15-13 : cmd (3 bits)
    # bits 12-8  : addr (5 bits)
    # bits 7-0   : value (8 bits)
    
    cmd &= 0x07
    addr &= 0x1F
    value &= 0xFF
    return (cmd << 13) | (addr << 8) | value
def read_register(addr):
    frame = build_frame(Read_Command, addr, 0x00)
    msb = (frame >> 8) & 0xFF
    lsb = frame & 0xFF
    spi1.xfer2([msb, lsb])                          # send read command
    sleep(0.05)
    resp = spi1.xfer2([0x00, 0x00])                 # dummy read to get register value
    sleep(0.01)
    print(f"{REGISTER_NAMES.get(addr, '')}: {resp[1]}")
    return resp[1]
def write_register(addr, value):
    # Check if en_pin exists and is off (LOW)
    if en_pin is not None and en_pin.value:
        print("Warning: Enable pin is ON (sensor active). Register write should be done with sensor in idle (enable pin OFF).")
        return None
    
    frame = build_frame(Write_Command, addr, value)
    msb = (frame >> 8) & 0xFF
    lsb = frame & 0xFF
    print(f"Frame built: 0x{frame:04X}")                 # print the frame for debugging
    spi1.xfer2([msb, lsb])                               # write command
    sleep(0.05)
    resp2 = spi1.xfer2([0x00, 0x00])                     # dummy read to get write response
    sleep(0.05)
    if resp2[1] != (value & 0xFF):
        print("Error in write response: ", resp2[1])     # check that register value is returned after write
    
    error_flags = read_register(Eeprom) & 0xFF           # Check error flags after every write
    if error_flags != 0x00:
        print(f"Warning: Error flags: 0x{error_flags:02X}")
    
    return resp2[1]

# set magnet ratio adjustment
def set_magnet_ratio(enable, bias_value):
    # set bias trimming current to adjust magnet ratio
    write_register(Bias_Trimming_Current, bias_value) 
    sleep(0.05)
    # enable trimming current for X and Y axis
    write_register(Enable_Trimming_Current, enable)
    sleep(0.05)

# read angle in degrees
def read_angle():
    raw_bytes = spi1.xfer2([Read_Angle, 0x00])             # returns [MSB, LSB]
    msb, lsb = raw_bytes[0], raw_bytes[1]                  # retrieve MSB and LSB
    raw16 = (msb << 8) | lsb                               # 16-bit integer from sensor
    angle_deg = raw16 * (359.995 / 65535)                  # map 16-bit 
    print(f"raw16: {raw16} bytes: {raw_bytes}  angle_deg: {angle_deg:.3f}°")
    sleep(0.5)
    return angle_deg

# set zero position to current angle
def set_zero_position():
    print("Clearing zero position registers")
    write_register(Zero_Setting_LSB,0x00)
    write_register(Zero_Setting_MSB,0x00)
    sleep(0.5)                   
    pin_state = enable_pin()                        # active mode
    print("Enable Pin State:", pin_state)
    sleep(0.5)      
    print("Clearing...")
    for i in range(3):                              # take multiple readings to ensure angle is updated
        read_angle()                          
    raw_bytes = spi1.xfer2([Read_Angle, 0x00])      # returns [MSB, LSB]
    msb, lsb = raw_bytes[0], raw_bytes[1]           # retrieve MSB and LSB
    pin_state = disable_pin()
    print("Disable Pin State:", pin_state)
    sleep(0.5)
    write_register(Zero_Setting_LSB, lsb)
    print("Zero LSB Written:", lsb)
    sleep(0.5)
    write_register(Zero_Setting_MSB, msb)
    print("Zero MSB Written:", msb)
    # Read back both zero registers to verify
    read_register(Zero_Setting_LSB)
    read_register(Zero_Setting_MSB)

# check to ensure read operation works for registers
# read_register(Filter_Settings)   
# sleep(0.05)

# Adjust magnet ratio as needed for accurate
# set_magnet_ratio(0x00, 0x00)

# set zero position to current angle
def initialize_zero_position():
    write_register(ASC_ASCR_FW, 0x00)                   # disable ASC/ASCR firmware control 
    read_register(ASC_ASCR_FW)                          # verify ASC/ASCR firmware control disabled
    read_register(Eeprom)                               # check EEPROM register before zeroing

    # Set rotation direction before zeroing
    write_register(Rotation_Direction, 0x00)            # set rotation direction (0x00 = default direction)
    read_register(Rotation_Direction)                   # verify rotation direction

    # set zero position
    angle = read_angle()
    if abs(angle) < 0.5:                                # threshold for "very close to zero"
        print("Angle is close to zero; skipping zero reset.")
    else:
        set_zero_position()
        print("Zero position set to current angle.")

# Test loop for angular reading from sensor
def test_loop():

    # enable active mode if en_pin is available
    pin_state = enable_pin()
    print("Enable Pin State:", pin_state)
    sleep(0.5)

    # ask user for how long to run (seconds). 0 = infinite
    # duration_s = int(input("Run duration in seconds (0 for infinite): ") or 0)
    duration_s = 2  # default to 2 seconds for testing
    end_time = (time() + duration_s) if duration_s > 0 else None

    # run until time expires (or forever if end_time is None)
    while end_time is None or time() < end_time:
        raw_bytes = spi1.xfer2([Read_Angle, 0x00])             # returns [MSB, LSB]
        msb, lsb = raw_bytes[0], raw_bytes[1]                  # retrieve MSB and LSB
        raw16 = (msb << 8) | lsb                               # 16-bit integer from sensor
        angle_deg = raw16 * (359.995 / 65535)                  # map 16-bit 
        print(f"raw16: {raw16} bytes: {raw_bytes}  angle_deg: {angle_deg:.3f}°")
        sleep(0.5)

# run test loop if executed as main script
if __name__ == "__main__":
    initialize_zero_position()
    test_loop()
    pin_state = disable_pin()                            # idle mode if en_pin is available
    print("Disable Pin State:", pin_state)
    clean_up()