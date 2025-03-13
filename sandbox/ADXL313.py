########### ADXL313 Eval Program ###############

from gpiozero import LED
from time import sleep, time
import RPi.GPIO as GPIO
import smbus
from math import sqrt
import matplotlib.pyplot as plt

I2C_BUS = 1
bus=smbus.SMBus(1) #Configure I2C bus
GPIO.setmode(GPIO.BCM) #set pin numbering for GPIOs
duration = 5 #length of data record
run = 0 #initialize

ADXL313 = 0x53 #device address
REG_DATAX0 = 0x32
REG_DATAX1 = 0x33
REG_DATAY0 = 0x34
REG_DATAY1 = 0x35
REG_DATAZ0 = 0x36
REG_DATAZ1 = 0x37

def read_accel_data():
#read acceleration data for X, Y, Z
	x0 = bus.read_byte_data(ADXL313,REG_DATAX0)
	x1 = bus.read_byte_data(ADXL313,REG_DATAX1)
	y0 = bus.read_byte_data(ADXL313,REG_DATAY0)
	y1 = bus.read_byte_data(ADXL313,REG_DATAY1)
	z0 = bus.read_byte_data(ADXL313,REG_DATAZ0)
	z1 = bus.read_byte_data(ADXL313,REG_DATAZ1)
	
	#combinte the two 8-bit values to form a 16 bit value
	x_16 = (x1 << 8) | x0
	y_16 = (y1 << 8) | y0
	z_16 = (z1 << 8) | z0
	
	x_accel = x_16 & 0x1FFF
	y_accel = y_16 & 0x1FFF
	z_accel = z_16 & 0x1FFF
	bits = 13
	
	#convert to signed 16 bit values
	if x_accel & (1 << (bits-1)):
		x_accel -= (1 << bits)
	if y_accel & (1 << (bits-1)):
		y_accel -= (1 << bits)
	if z_accel & (1 << (bits-1)):
		z_accel -= (1 << bits)
	
	scale_factor = 0.00097656
	
	#scale factor is 1024 LSB/g, full resolution set in #DATA_FORMAT, bit D3
	x_g = round(x_accel*scale_factor, 5)
	y_g = round(y_accel*scale_factor, 5)
	z_g = round((z_accel*scale_factor)-1, 5) #remove gravity 
	
	return x_g, y_g, z_g
def vib(run):
	bus.write_byte_data(ADXL313,0x18,0x52) #soft reset, at least 100ms to reboot
	sleep(0.2)

	#rx_data2 =bus.read_byte_data(ADXL313, 0x80) #device check, returns 173 (0xAD)
	#print(rx_data2)

	#ADXL313 configuration
	bus.write_byte_data(ADXL313,0x31,0x0B) #DATA_FORMAT, +/-4g, full resolution. if MSB set to 1, SELF_TEST
	bus.write_byte_data(ADXL313, 0x2E,0x80) #INT_ENABLE, Enable DATA_READY interrupt
	bus.write_byte_data(ADXL313,0x2D,0x08) #POWER_CTL, start measurement
	bus.write_byte_data(ADXL313,0x38,0x00) # FIFO_CTL
	sleep(0.1)

	time_step=0.005
	sample_size = int((duration/time_step) + 1)
	accel_list=[] #list of acceleration values to record
	time_list=[] #list of time values to record
	if run == 1:
		print("Vibration assessment has started")
		for i in range(sample_size):
			x,y,z =read_accel_data()
			print("Time Step:", i, "X value:", x, "Y value:", y, "Z value:", z)
			total_accel = round(sqrt(x**2+y**2+z**2),5)
			accel_list.append(total_accel)
			time_list.append(round(i*time_step,2))
			sleep(time_step)
	
		############## graphs ###################	 
		plt.plot(time_list,accel_list)
		plt.xlabel("Time (s)")
		plt.ylabel("Total Acceleration (g)")
		plt.title("Acceleration vs Time")
		plt.grid(True)
		plt.show()
	else: print("Vibration assessment ready")
