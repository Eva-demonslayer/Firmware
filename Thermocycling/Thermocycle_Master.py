############################## Thermocycle Master ###########################

import multiprocessing
from time import sleep, time
import os
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio" 
import gpiozero
import Buck_Boost_and_Temp_Sensor
import Pressure_Sensor
import Syringe_Pump_and_Infrared_Sensor

Temp_High = 95 # temperature setting for hot well
Temp_Low = 65 # temperature setting for cold well
well_to_well_move = 1000 # step count to move fluid between wells
dwell_time = 1 # dwell time at set temperatures
run = 1 # passed to scripts to initial main programs

if __name__ == '__main__': # only execute this function if the program is run directly
    p1 = multiprocessing.Process(target=Buck_Boost_and_Temp_Sensor,args= (Temp_High,Temp_Low)) # begin heater loop with set temps
    p2 = multiprocessing.Process(target=Syringe_Pump_and_Infrared_Sensor.main,args=(well_to_well_move, dwell_time)) # need to include syringe pump movement and infrared sensor into one script
    p3 = multiprocessing.Process(target=Pressure_Sensor.main)
    p1.start() # Start the processes
    sleep(15) # wait for heating to enter steady state cycle
    p2.start()
    sleep(1)
    p3.start()
# p1.join() # Wait for both processes to finish
# p2.join()
# p3.join()