
import time
import csv
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from lee_ventus_disc_pump import *

PressureGraph=[]
Power=[] 
xs = []
ys = []
starttime=time.time()
myPump = LVDiscPump()
bp=LVDiscPump()
# plt.ion()
pumpOn=False

def configure_valves(disc_pump_instance: LVDiscPump):
    """
    This function configures both valve output on the GP driver. It should be run once to set the values, then the
    board should be power cycled and the rest of the program can resume.
    GPIO B (Valve 1) needs to be set to "slow mode default off" (default pin mode is in "fast mode default off").
    GPIO C (Valve 2) needs to be set to "slow mode default off" (default pin mode is in "slow mode default off").
    "Slow mode" allows for longer pulses (up to 30s) to be generated, however it has a lower time resolution of 1ms.
    "Fast mode" allows for more accurate pulses to be generated (resolution of 10us), however they are limited to 300ms.
    For more information check the Development Kit User Manual.
    """

    # set both valve outputs to be slow mode default off
    disc_pump_instance.write_reg(LVRegister.GPIO_B_PIN_MODE, LVGpioPinMode.OUTPUT_SLOW_MODE_DEF_LOW)    # Valve 1
    disc_pump_instance.write_reg(LVRegister.GPIO_C_PIN_MODE, LVGpioPinMode.OUTPUT_SLOW_MODE_DEF_LOW)    # Valve 2

    # store settings to the board
    disc_pump_instance.store_current_settings_to_board()

    # close serial port
    disc_pump_instance.disconnect_pump()

    while True:
        print("Valves have been configured. Power cycle the board and restart the program.")
        time.sleep(60)

def script():
    # Open script file and parse
    newlist=[]
    with open('2024-06-13 QSDK Reversible Manifold Testing on Plan B rig.txt') as fp:
        contents = fp.read()
        splitcontent = contents.splitlines()
        for entry in splitcontent:
            if "/" in entry or len(entry)<=1:
                pass
            else:
                newlist.append(entry)

    for entry in newlist:
        RunPump(entry)

def RunPump(Command):

    #Default Values
    Valve1_Value=0
    Valve2_Value=0
    Pump_Registry="W0"
    Registry_Value = 0

    #More text parsing
    Command=Command.replace(" ","")
    string=Command.split(',')

    #Send to right command (add more Registry as needed)
    if "Pump" in Command:
        Pump_Registry = string[2]
        Registry_Value = (int(string[3]))
    if "Valve" in Command:
        Valve1_Value=int(string[1])
        Valve2_Value=int(string[2])
        bp.write_reg(LVRegister.GPIO_B_STATE, Valve1_Value, sleep_after=0)     # Valve 1
        bp.write_reg(LVRegister.GPIO_C_STATE, Valve2_Value, sleep_after=0)   # Valve 2
    if "Wait" in Command:
        wait_time=int(string[1])
        for t in range(wait_time):
            drive_power = myPump.read_register(LVRegister.MEAS_DRIVE_MILLIWATTS)
            pressure = myPump.read_register(LVRegister.MEAS_DIGITAL_PRESSURE)
            PressureGraph.append(pressure)
            Power.append(drive_power)
            print(pressure,drive_power)
            # graphing(pressure)   
            time.sleep(1)

    #Lee Pump Registry
    if Pump_Registry == "#W23":
        # set pressure
        myPump.write_reg(LVRegister.SET_VAL, Registry_Value)

    if Pump_Registry == "#W0":
        # turn the pump on
        myPump.write_reg(LVRegister.PUMP_ENABLE, Registry_Value)
    
    if Pump_Registry == "#W14":
        myPump.set_pid_digital_pressure_control_with_set_val(p_term=Registry_Value, i_term=0.1)

def ReadPump():
    # drive_power = myPump.read_register(LVRegister.MEAS_DRIVE_MILLIWATTS)
    pressure = myPump.read_register(LVRegister.MEAS_DIGITAL_PRESSURE)
    PressureGraph.append(pressure)
    # Power.append(drive_power)
    return pressure

def SetPumpValue(P):
    n=int(P)
    global pumpOn
    if n <0:
        Valve1_Value = -1
        Valve2_Value = -1
        myPump.write_reg(LVRegister.PUMP_ENABLE, 0)
        pumpOn=False
        myPump.set_pid_digital_pressure_control_with_set_val(p_term= -80, i_term=0.1)
    else:
        Valve1_Value = 0
        Valve2_Value = 0
        myPump.set_pid_digital_pressure_control_with_set_val(p_term= 80, i_term=0.1)
    bp.write_reg(LVRegister.GPIO_B_STATE, Valve1_Value, sleep_after=0)     # Valve 1
    bp.write_reg(LVRegister.GPIO_C_STATE, Valve2_Value, sleep_after=0)
    myPump.write_reg(LVRegister.SET_VAL, n)
    if pumpOn==False:
        myPump.write_reg(LVRegister.PUMP_ENABLE, 1)
        pumpOn = True
    # wait for 1s and print the pressure reached
    #time.sleep(1)
    # drive_power = myPump.read_register(LVRegister.MEAS_DRIVE_MILLIWATTS)
    # pressure = myPump.read_register(LVRegister.MEAS_DIGITAL_PRESSURE)
    # PressureGraph.append(pressure)
    # Power.append(drive_power)
    # print(pressure,drive_power)

# def graphing():
#     fig = plt.figure()
#     ax = fig.add_subplot(1,1,1)
#     ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys, ax), interval=1000, cache_frame_data=False)
#     plt.show()

# def animate(i, xs, ys, ax):
#     currentPressure = myPump.read_register(LVRegister.MEAS_DIGITAL_PRESSURE)

#     # Add x and y to lists
#     currenttime = time.time()
#     xs.append(currenttime-starttime)
#     ys.append(currentPressure)

#     # Limit x and y lists to 20 items
#     xs = xs[-30:]
#     ys = ys[-30:]

#     # Draw x and y lists
#     ax.clear()
#     ax.plot(xs, ys)

#     # Format plot
#     plt.ylabel('Pressure (mBar)')
    

# def graphing(currentPressure):
#         currenttime = time.time()
#         xs.append(currenttime-starttime)
#         ys.append(currentPressure)

#         #Limit number of data points shown at once

#         if len(xs) > 50:
#             xlim = xs[-49:]
#             ylim = ys[-49:]
#         else:
#             ylim=ys

#         # # plotting graph and update for each data point
#         plt.clf()
#         plt.plot(xs, ys, color = 'g')
#         plt.draw()
#         # plt.ylim(20,40)
#         plt.xlabel("time")
#         plt.ylabel("Pressure (mBar)")
        
#         # calling pause function
#         plt.pause(0.01)



def main(P):
    SetPumpValue(P)
    print(P)
    # connect the pump

def init():
    myPump.connect_pump(i2c_address=37)  # Pump control
    bp.connect_pump(com_port="COM7")    # Valve control

    # turn off data streaming mode
    myPump.streaming_mode_disable()
    bp.streaming_mode_disable()

    # This function configures both valve output on the GP driver if not set correctly. It should be run once to set
    # the values, then the board should be power cycled (as these settings take effect on startup).
    # The function will automatically be skipped once the valves are configured.
    if bp.read_register(LVRegister.GPIO_B_PIN_MODE) != LVGpioPinMode.OUTPUT_SLOW_MODE_DEF_LOW or \
            bp.read_register(LVRegister.GPIO_C_PIN_MODE) != LVGpioPinMode.OUTPUT_SLOW_MODE_DEF_LOW:
        configure_valves(bp)

    # turn the pump off whilst configuring system
    myPump.write_reg(LVRegister.PUMP_ENABLE, 0)
    pumpOn=False


    # set the pump to PID pressure control with target pressure to the SetVal register
    myPump.set_pid_digital_pressure_control_with_set_val(p_term=80, i_term=0.1)

    print("Pump is Ready!")

    # script()


def exit():
    # turn the pump off
    myPump.write_reg(LVRegister.PUMP_ENABLE, 0)
    bp.write_reg(LVRegister.PUMP_ENABLE, 0)

    # close serial port / I2C connection
    myPump.disconnect_pump()
    bp.disconnect_pump()

    # Write data to csv
    # with open('pumpdata.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerows(zip(Power,PressureGraph))

    print("Pump is Closed")
 
if __name__ == '__main__':
    # create a Disc Pump instance
    init()