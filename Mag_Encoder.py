###################### Magnetic Encoder MA780 fro MPS ############################
from ast import While
import spidev
from time import sleep, time
import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio" 
import gpiozero

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

while True:
    raw_bytes = spi.xfer2([Read_Angle, 0x00])       # returns [MSB, LSB]
    msb, lsb = raw_bytes[0], raw_bytes[1]           # retrieve MSB and LSB
    raw16 = (msb << 8) | lsb                        # 16-bit integer from sensor
    angle_deg = raw16 * (359.995 / 65535)           # map 16-bit 
    
    print(f"raw16: {raw16} bytes: {raw_bytes}  angle_deg: {angle_deg:.3f}°")
    sleep(0.5)
