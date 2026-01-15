################### Encoder_Eval #############################

import Mag_Encoder as mag
import Motor_Optical_Encoder as motor
from time import sleep

# rotation direction settings (cw for clockwise, ccw for counter-clockwise)
CW = 0x14                       
CCW = 0x04                      

# Test parameters
test_loop_iterations = 4
sleep_time = 0.1
test_angle = 90

def eval_enc():

    # Initialize Motor to 0 position
    motor.configure(CW)
    motor.reset_position()
    motor.single_move(0)
    sleep(1)

    # Initialize Magnet Encoder
    mag.initialize_zero_position()
    sleep(sleep_time)
    mag.read_angle()
    sleep(sleep_time)

    # Move Motor and Read Magnet Encoder
    for i in range(test_loop_iterations):    
        motor.single_move(test_angle)
        motor.read_position()
        sleep(sleep_time)
        mag.read_angle()
        sleep(sleep_time)

eval_enc()