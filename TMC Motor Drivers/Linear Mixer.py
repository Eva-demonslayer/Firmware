###################### Linear Mixer REV02 UPDATED 8/29/24 ############################
################################ TMC5130 #############################################
import spidev
import tkinter as tk #GUI
from gpiozero import LED
from time import sleep, time
import RPi.GPIO as GPIO
import multiprocessing
import ADXL313 #vibration assessment program

GPIO.setmode(GPIO.BCM) #set pin numbering for GPIOs
GPIO.setup(16, GPIO.OUT)
spi = spidev.SpiDev()
spi.open(0,0) # specify the SPI bus and device
spi.max_speed_hz = 5000000	#set SPI speed, 5MHz
position_bit = 5 #position reached
home_bit = 6 #left home reached
frequency = 10 #default freqency
duration = 10 #default duration of mixing
move_type = 0 #starting move type is a single mve
displacement = 15 #starting single move dispacement
spi.mode = 0 #SPI configuration
move_direction = 0 #initial move away from motor
home_direction = 0 #always move to home away from motor
encode = 0 #Encoder value

######### Main Functions ###########
def configure (move_type,move_direction):
    if move_type == 1:
        spi.xfer2([0x80,0x00,0x00,0x00,0x00]) #gconf, general configuration write, all 0.
        sleep(0.05) 
        spi.xfer2([0xEC,0x04,0x01,0x00,0xC2]) #chopconf, 32 bit register. first byte is address.
        sleep(0.05)
        #toff set to 2 (range is 2-15). delay beyween transactions on SPI bus
        #PWM sync clock set to 1
        #bit 19, high velocity mode
        #MRES (microstep resolution) set to 2 (range is 256,128,64,32,16,8,4,2,FULLSTEP). 200 steps per rotation
        #spi.xfer2([0xED,0x00,0x00,0x00,0x00]) #Coolconf, only in combination with spread cycle, not stealthchop
    else:
        if move_direction == 0:
            direction_bit = 0x14 #left move
        else: direction_bit = 0x04 #right move
        sleep(0.05)
        spi.xfer2([0x80,0x00,0x00,0x00,direction_bit]) #EN_PWM_MODE=1 enables StealthChop (with default PWMCONF = 0x00050480)
        sleep(0.05) 
        spi.xfer2([0x93,0x00,0x00,0x01,0xF4]) #TPWM_THRS=500 yields a switch velocity of about 35000, 30 RPM
        sleep(0.05) 
        spi.xfer2([0xF0,0x00,0x04,0x01,0x80]) #PWMCONF. first byte set to autoscale, minimum setting 0x40. second byte is user defined PWM Grad (1 to 15), third byte is automatic current control
        sleep(0.05) 
        spi.xfer2([0xEC,0x04,0x01,0x00,0x05]) #Chopconf, toff set to 5. MRES (microstep resolution) set to 16 (range is 128,64,32,16,8,4,2,FULLSTEP). 200*16=3200 steps per rotation.
        sleep(0.05)
        
    spi.xfer2([0xA0,0x00,0x00,0x00,0x00]) #RAMPMODE (target position move)  
    sleep(0.05)
    spi.xfer2([0x90,0x00,0x01,0x1F,0x00]) #ihold_irun. Bits 0-4 hold current, 8-12 motor current. 16-19 IHOLDDELAY
    sleep(0.05)                           #Run Current Scaling Factor set to 31, no hold current, minimal delay. 
    spi.xfer2([0x91,0x00,0x00,0x00,0x0A]) #TPOWERDOWN=10, delay before power down at standstill
    sleep(0.05)
    if move_type == 1: #mix
        #AMAX and DMAX shoud be roughly have of A1 and D1
        #V1 should be roughly have of VMAX
        spi.xfer2([0xA5,0x00,0x00,0x3A,0x98]) #V1, Threshold velocity, 15000
        sleep(0.05)
        spi.xfer2([0xA7,0x00,0x00,0x75,0x30]) #VMAX, 30000
        sleep(0.05)
        spi.xfer2([0xA3,0x00,0x00,0x00,0x00]) #VSTART, not used
        sleep(0.05)
        spi.xfer2([0xAB,0x00,0x00,0x00,0x10]) #VSTOP, 10 is mininimum recommended
        sleep(0.05)
        spi.xfer2([0xAA,0x00,0x00,0x9C,0x40]) #D1, deceleration between V1 and VSTOP. 40,000
        sleep(0.05)
        spi.xfer2([0xA4,0x00,0x00,0x9C,0x40]) #A1, first acceleration between VSTART and V1, 40,000
        sleep(0.05)
        spi.xfer2([0xA6,0x00,0x00,0x4E,0x20]) #AMAX, 20000
        sleep(0.05)
        spi.xfer2([0xA8,0x00,0x00,0x4E,0x20]) #DMAX, 20000
        sleep(0.05)
    else: #single move
        spi.xfer2([0xA5,0x00,0x00,0x00,0xFA]) #V1, Threshold velocity, 250 
        sleep(0.05)
        spi.xfer2([0xA7,0x00,0x00,0x03,0xE8]) #VMAX, 1000
        sleep(0.05)
        spi.xfer2([0xA3,0x00,0x00,0x00,0x00]) #VSTART, not used
        sleep(0.05)
        spi.xfer2([0xAB,0x00,0x00,0x00,0x10]) #VSTOP, 10 is mininimum recommended
        sleep(0.05)
        spi.xfer2([0xAA,0x00,0x00,0x00,0x64]) #D1, deceleration between V1 and VSTOP, 100
        sleep(0.05)
        spi.xfer2([0xA4,0x00,0x00,0x00,0x64]) #A1, first acceleration between VSTART and V1, 100
        sleep(0.05)
        spi.xfer2([0xA6,0x00,0x00,0x00,0x32]) #AMAX, 50
        sleep(0.05)
        spi.xfer2([0xA8,0x00,0x00,0x00,0x32]) #DMAX, 50
        sleep(0.05)
def read_position():
    home_check = 0
    position_check = 0
    sleep(.05)
    while bool(position_check) == False and bool(home_check) == False:
        spi.xfer2([0x00,0x00,0x00,0x00,0x00]) #throw out 1st read
        sleep(.05)
        read_data = spi.xfer2([0x00,0x00,0x00,0x00,0x00]) #SPI_STATUS
        sleep(.05)
        hex_data = int(read_data[0])
        position_check=(hex_data >> position_bit) & 1 #bitwise AND operation with a mask of 1
        home_check=(hex_data >> home_bit) & 1 #bitwise AND operation with a mask of 1
def reset_position():
    spi.xfer2([0xA1,0x00,0x00,0x00,0x00]) #XACTUAL reset
    sleep(0.05)
def detection_well():
    print("Mixing has started")
    start_time = time() #time initialized
    while (time()-start_time) < duration:
        try:
            spi.xfer2([0xAD,0x00,0x00,0x05,0xDC]) #XTARGET (7mm)
            #read_position(bit)
            sleep((1/(2*frequency)))
            spi.xfer2([0xAD,0x00,0x00,0x00,0x00]) #XTARGET (7mm)
            #read_position(bit)
            sleep((1/(2*frequency)))
        except: StopIteration
def single_move():
    reset_position()
    print("Single move in mm:", displacement)
    disp = displacement * (16 * 20)/2 #microstepping * lead... and divide by 2
    disp = int(disp)
    #print("actual position as decimal", disp)
    read_data = spi.xfer2([0x2D,0x00,0x00,0x00,0x00]) #throw out 1st read
    sleep (0.05)
    read_data = spi.xfer2([0x2D,0x00,0x00,0x00,0x00]) #second read, actual position
    #print("actual position", read_data)
    if disp < 255:
        my_list = [0xAD,0x00,0x00,0x00]
        my_list.append(disp)
    elif displacement < 65535:  #It was "displacement", changed it to disp
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
def get_frequency(): # button response for frequency
    try:
        global frequency
        frequency = int(entry0.get())
        print(frequency)
        label0.config(text=frequency, bg="light green")
    except ValueError:
        label0.config(text="Error", bg="red")
def get_duration(): # button response for duration
    try:
        global duration
        duration = float(entry1.get())
        label1.config(text=duration, bg="light green")
    except ValueError:
        label1.config(text="Error", bg="red")
def set_move_type():
    #single move = 0, mixing = 1
    try:
        global move_type
        move_type= int(entry2.get())
        label2.config(text=move_type, bg="light green")
    except ValueError:
        label2.config(text="Error", bg="red")
def get_displacement(): # button response for single move displacement
    try:
        global displacement
        displacement = float(entry3.get())
        label3.config(text=displacement, bg="light green")
    except ValueError:
        label3.config(text="Error", bg="red")
def go_home():
    spi.xfer2([0xB4,0x00,0x00,0x00,0xA3]) #SWMODE automatic motor stop at right and left home switches
    sleep(.05)
    move_direction = 1
    configure(move_type, move_direction)
    reset_position()
    spi.xfer2([0xAD,0x00,0x00,0xFF,0xFF]) #large move to get home
    print("Going home....")
    read_position()
    reset_position()
    spi.xfer2([0x80,0x00,0x00,0x00,0x14]) #configure move towards motor
    sleep(0.05)
    spi.xfer2([0xB4,0x00,0x00,0x00,0x00]) #disable home sensor
    sleep(0.05)
    spi.xfer2([0xAD,0x00,0x00,0x00,0x64]) #detach from home sensor interrupt
    read_position()
    print("move away from home sensor")
    home_direction = 0
    print("Homing comlete")
    reset_encoder()
def encoder_config():
    sleep(0.05)
    spi.xfer2([0xB8,0x00,0x00,0x01,0x5C]) #ENCMODE Encoder config and use of N channel
    sleep(0.05)
    enc_mode = spi.xfer2([0x38,0x00,0x00,0x00,0x00]) #ENCMODE read back
    sleep(0.05)
    print("enc_mode =", enc_mode)
    #pol_A and pol_B  at neg. pol_N = high active
    #ignore AB polarity for N event, manual event trigger from pi
    #pos_edge =  01, N channel is valid upon active going N event
    #clr_cont =  Always latch or latch and clear X_ENC upon an N event
    #encoder prescaler divisor binary mode
    #clr_enc_x = 1, latch and additionally clear encoder counter X_ENC at N-event
    spi.xfer2([0xBA,0x00,0x01,0x1C,0x71]) #Accumulation constant, current microstepping. X_ENC accumulates +/- ENC_CONST / (2^16*X_ENC) (binary)
def reset_encoder():
    encoder_config()
    sleep(0.05)
    N=16
    GPIO.output(N, GPIO.HIGH) #triggers N event and clears X_ENC
    sleep(0.1)
    GPIO.output(N, GPIO.LOW)
    sleep(0.1)
    status = spi.xfer2([0x3B,0x00,0x00,0x00,0x00]) #throw out 1st read
    sleep(0.3)
    status = spi.xfer2([0x3B,0x00,0x00,0x00,0x00]) #ENC_Status, Read and Clear
    print("Encoder Position Cleared")
    sleep(0.3)
    print("N Status after low polarity. Bit1=N event detected", status)
    enc_latch = spi.xfer2([0x3C,0x00,0x00,0x00,0x00]) #throw out 1st read
    sleep(1.5)
    enc_latch = spi.xfer2([0x3C,0x00,0x00,0x00,0x00]) #Encoder position X_ENC latched on N event
def read_encoder():
    x_enc = spi.xfer2([0x39,0x00,0x00,0x00,0x00]) #throw out 1st read
    sleep(0.05)
    x_enc = spi.xfer2([0x39,0x00,0x00,0x00,0x00]) #X_ENC actual encoder position read 
    print("x_enc read register:",x_enc)
    position_2 = hex(x_enc[4]) #store data from bytes in separate variables
    position_1 = hex(x_enc[3]) 
    hex_value_2 = position_2[2:] #trim the 0x from the hex values
    hex_value_1 = position_1[2:]
    combine_str = str(hex_value_1) + str(hex_value_2) #combine the trimmed values into one string
    combine_str = combine_str.zfill(4) #fill in any missing values for 4 digits
    enc_cycles = int(combine_str,16) #change to hex, and then back to integer
    if enc_cycles >= 32768: #Check to see if this number is a negative number
        enc_cycles -= 65536 #If so, compensate it with 65536
    linear_distance = enc_cycles/((16*20/2)) #current micro step and 20 mm lead, divided by 2 same as position command
    print("x_enc in mm:", linear_distance)
def motor_move(move_type,move_direction):
    configure(move_type, move_direction)
    if move_type == 0:
        single_move()
        read_position()
    elif move_type == 1:
        reset_position()
        run = 1 #not sure why needed but changes break the code, keep for now
        p1 = multiprocessing.Process(target=ADXL313.vib, args = (run,)) #processing for vibration assessment
        p2 = multiprocessing.Process(target=detection_well) #processing for mixing
        p1.start()
        p2.start()
        p1.join()
        p2.join()

###################### GUI Code ###########################
window = tk.Tk() 	
select_direction=tk.IntVar()
select_direction.set(0)
def direction_update():
    global move_direction
    move_direction = select_direction.get()
    print("Direction updated")
label_list = ["Frequency of detection well mixing (Hz)", "Duration of detection well mixing (seconds)", "Mix =1, Single Move or Home = 0", "Single Move Displacement (mm)", "Single Move Direction (mm)"]
for i in range(4): #Label windows
    label = tk.Label(
            master=window,
            width=35,
            height=5,
            bg="light blue", 
            text=label_list[i])
    label.grid(row=i, column=0, sticky="nsew")
for i in range(4,5): #Label windows
    label = tk.Label(
            master=window,
            width=35,
            height=5,
            bg="light blue", 
            text=label_list[i])
    label.grid(row=i, rowspan=2, column=0, sticky="nsew")
label_list2 = {}
default_variables = [frequency, duration, move_type, displacement, move_direction]
for i in range(4): # status labels
    label_list2[f'label{i}']= tk.Label(
            master=window,
            width=15,
            height=5,
            bg="light yellow",
            text=default_variables[i])
    label_list2[f'label{i}'].grid(row=i, column=2, sticky="nsew")
    globals().update(label_list2)
entry_list = {}
for i in range(4): # Entry windows
    entry_list[f'entry{i}'] = tk.Entry(master=window)
    entry_list[f'entry{i}'].grid(row=i, column=3, sticky="nsew")
    globals().update(entry_list)

#button 1 command
btn1=tk.Button(master=window, text="Update Frequency", command=get_frequency)
btn1.grid(row=0, column=1, sticky="nsew")

#button 2 command
btn2=tk.Button(master=window, text="Update Duration", command=get_duration)
btn2.grid(row=1, column=1, sticky="nsew")

#button 3 command
btn3=tk.Button(master=window, text="Update Move Type", command=set_move_type)
btn3.grid(row=2, column=1, sticky="nsew")

#button 4 command
btn4=tk.Button(master=window, text="Update Move Displacement", command=get_displacement)
btn4.grid(row=3, column=1, sticky="nsew")

#button 5 command
btn5=tk.Button(master=window, text="Go Home", fg="blue", height = 1, font="20", command=go_home)
btn5.grid(row=4, column=3, sticky="nsew")

#button 6 command
btn6=tk.Button(master=window, text="Read Encoder", fg="blue", height = 1, font="20", command=read_encoder)
btn6.grid(row=4, column=2, sticky="nsew")

#button 6 command
btn7=tk.Button(master=window, text="Reset Encoder", fg="red", height = 1, font="20", command=reset_encoder)
btn7.grid(row=5, column=2, sticky="nsew")

#button 7 command
btn8=tk.Button(master=window, text="Start Program", fg="green", height = 1, font="20", command=lambda:motor_move(move_type,move_direction))
btn8.grid(row=5, column=3, sticky="nsew")

#Radio direction buttons
rbtn1=tk.Radiobutton(master=window, text="Left", variable=select_direction, value=0, command = direction_update)
rbtn1.grid(row=4, column=1, sticky="nsew")
rbtn2=tk.Radiobutton(master=window, text="Right", variable=select_direction, value=1, command = direction_update)
rbtn2.grid(row=5, column=1, sticky="nsew")

window.mainloop()
GPIO.cleanup()
