############################ EM3080-W and EM3088-W ############################

import serial

# Replace '/dev/ttyUSB0' with your actual COM port
port = '/dev/ttyACM0'

baud_rate = 9600  # Adjust the baud rate as needed

ser = serial.Serial(
    port, baud_rate,
    bytesize=serial.EIGHTBITS, 
    stopbits = serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE,
    timeout=1)
print("program started\n")
while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').rstrip()
        print(data)
