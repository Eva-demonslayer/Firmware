
import time
import serial
from lee_ventus_disc_pump import *
from pySerialTransfer import pySerialTransfer as txfer

PressureGraph=[]
xs = []
ys = []
starttime=time.time()
myPump = LVDiscPump()
pumpOn=False
PosP=True
Valve=[0,0,0,0,0,0,0,0,0,0,0,0,0,0]

#Set COM port for pump
myPump.connect_pump(com_port='COM24')  # Pump control

#Arduino for Valves
serPort = "COM29"
baudRate = 9600
ser = serial.Serial(serPort, baudRate)
# link = txfer.SerialTransfer('COM29')

Pump_Registry="W0"
Registry_Value = 0

def script(file):
    # Open script file and parse
    newlist=[]
    with open(file) as fp:
        contents = fp.read()
        splitcontent = contents.splitlines()
        for entry in splitcontent:
            if "/" in entry or len(entry)<=1:
                pass
            else:
                newlist.append(entry)

    for entry in newlist:
        RunPump(entry)

def RunPump(Pump_Registry,Registry_Value):

    #Send to right command (add more Registry as needed)
    if Pump_Registry == "Valve":
        Msg = int(Registry_Value)
        sendToArduino(Msg)

    #Lee Pump Registry
    if Pump_Registry == "#W23":
        # set pressure
        myPump.write_reg(LVRegister.SET_VAL, Registry_Value)

    if Pump_Registry == "#W0":
        # turn the pump on
        myPump.write_reg(LVRegister.PUMP_ENABLE, Registry_Value)
    
    if Pump_Registry == "#W14":
        # set P value (generally 80 or -80)
        myPump.set_pid_digital_pressure_control_with_set_val(p_term=Registry_Value, i_term=0.1)

def ReadPump():
    pressure = myPump.read_register(LVRegister.MEAS_DIGITAL_PRESSURE)
    PressureGraph.append(pressure)
    return pressure

def sendToArduino(sendInt):
    global Valve
    # print(sendInt)
    t=sendInt-1
    CurrentV = (Valve[t])
    if CurrentV == 0:
        Valve[t] == 1
    elif CurrentV == 1:
        Valve[t] == 0
    ser.write((str(sendInt) + '\n').encode()) # change for Python3

def ChangeValve(n):
    # boardpositions = [LVRegister.GPIO_B_STATE, LVRegister.GPIO_C_STATE]
    # if n==0:
    #     sendToArduino(string)
    #     # for i in boardList:
    #     #     for j in range(2):
    #     #         i.write_reg(boardpositions[j],0,sleep_after = 0)

    # else:
    print("Changing Valve" + str(n))
    sendToArduino(n)
        # value = -1
        # boardn = ((n+1)//2)-1
        # board = boardList[boardn]
        # boardpos = abs(n%2-1)

        # board.write_reg(boardpositions[boardpos], value, sleep_after=0) 
        # print("Valve"+ str(n))
        
        # for i in boardList:
        #     for j in range(2):
        #         if i == board and j == boardpos:
        #             continue
        #         else:
        #             i.write_reg(boardpositions[j],0,sleep_after = 0)
            

def SetPumpValue(P):
    n=float(P)
    global pumpOn
    global PosP
    
    # wait for 1s and print the pressure reached
    if n<0 and PosP == True:
        PosP = False
        myPump.write_reg(LVRegister.PUMP_ENABLE, 0)
        pumpOn = False
        myPump.set_pid_digital_pressure_control_with_set_val(p_term=-80, i_term=0.1)
        sendToArduino(13)
        sendToArduino(14)
    elif n>=0 and PosP == False:
        PosP = True
        myPump.write_reg(LVRegister.PUMP_ENABLE, 0)
        pumpOn = False
        myPump.set_pid_digital_pressure_control_with_set_val(p_term=80, i_term=0.1)
        sendToArduino(13)
        sendToArduino(14)
    
    myPump.write_reg(LVRegister.SET_VAL, n)
    if pumpOn==False:
        myPump.write_reg(LVRegister.PUMP_ENABLE, 1)
        pumpOn = True
    time.sleep(1)
    pressure = myPump.read_register(LVRegister.MEAS_DIGITAL_PRESSURE)
    PressureGraph.append(pressure)
    print(pressure)

# if __name__ == '__main__':
# #     # create a Disc Pump instance
def main(P):
    SetPumpValue(P)
    print(P)
# # connect the pump

def init():
    
    # turn off data streaming mode
    myPump.streaming_mode_disable()
    
    # turn the pump off whilst configuring system
    myPump.write_reg(LVRegister.PUMP_ENABLE, 0)

    # set the pump to PID pressure control with target pressure to the SetVal register
    myPump.set_pid_digital_pressure_control_with_set_val(p_term=80, i_term=0.1)

    print("Pump is Ready!")

    # script()


def exit():
    # turn the pump off
    myPump.write_reg(LVRegister.PUMP_ENABLE, 0)

    # close serial port / I2C connection
    myPump.disconnect_pump()

    # for i in range(len(Valve)):
    #     print(Valve[i])
    #     if Valve[i]==1:
    #         sendToArduino(i)
    sendToArduino(12)
    sendToArduino(13)
    sendToArduino(0)

    ser.close

    print("Pump is Closed")
 