###################### Magnetic Encoder MA780 from MPS ############################

import spidev
from time import sleep, time
import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio" 
# import gpiozero

spi = spidev.SpiDev()
spi.open(0,0)                   # specify the SPI bus and device (chip select)
spi.mode = 0                    # spi mode 0 start. CPOL=0, CPHA=0.
spi.max_speed_hz = 5000000      # assign SPI frequency

Read_Angle = 0x00               # returns angle value (16 bits)
Read_Register = 0x40            # 8-bit angle + register value
Write_Register = 0x80           # 8-bit angle + register value
Store_Single_Register = 0xE0    # 16 bit value
Store_All_Registers = 0xC0      # 16 bit value
Restore_All_Registers = 0xA0    # 16 bit value
Clear_Error_Flag = 0x20         # 16 bit value

# register map
Zero_Setting_LSB = 0x00
Zero_Setting_MSB = 0x01
Bias_Trimming_Current = 0x02
Enable_Trimming_Current = 0x03
Cycle_Time_LSB = 0x04
Cycle_Time_MSB = 0x05
On_Time = 0x07
Threshold = 0x08
Rotation_Direction = 0x09
Reference = 0xA
ASC_ASCR_FW = 0xB
Multi_turns = 0x16
Eeprom = 0x1A

# write register operation is two 16 bit frames
# first frame is 3 bit write command, followed by 5 bit register address
# and lastly register value to write
Write_Command = 0x04
Read_Command = 0x02
Store_Single_Register = 0x07
Store_All_Registers = 0x06
Restore_All_Registers = 0x05
Clear_Error_Flag = 0x01

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
    resp1 = spi.xfer2([msb, lsb])
    sleep(0.001)
    resp2 = spi.xfer2([0x00, 0x00])
    return resp1, resp2

def read_register(addr):
    frame = build_frame(Read_Command, addr, 0x00)
    msb = (frame >> 8) & 0xFF
    lsb = frame & 0xFF
    spi.xfer2([msb, lsb])
    sleep(0.001)
    resp = spi.xfer2([0x00, 0x00])
    return resp[1]

# test for continuous angle measurement
while True:
    raw_bytes = spi.xfer2([Read_Angle, 0x00])       # returns [MSB, LSB]
    msb, lsb = raw_bytes[0], raw_bytes[1]           # retrieve MSB and LSB
    raw16 = (msb << 8) | lsb                        # 16-bit integer from sensor
    angle_deg = raw16 * (359.995 / 65535)           # map 16-bit 
    
    print(f"raw16: {raw16} bytes: {raw_bytes}  angle_deg: {angle_deg:.3f}°")
    sleep(0.5)
