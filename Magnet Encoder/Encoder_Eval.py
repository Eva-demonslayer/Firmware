################### Encoder_Eval #############################

import Mag_Encoder as mag
import Motor_Optical_Encoder as motor
from time import sleep

# rotation direction settings
CW = 0x14                       # CW
CCW = 0x04                      # CCW

def eval_enc():

    # Initialize Motor to 0 position
    motor.configure(CW)
    motor.reset_position()
    motor.single_move(0)
    sleep(1)

    # Initialize Magnet Encoder
    mag.set_zero_position()
    sleep(0.1)
    mag.read_angle()
    sleep(0.1)

    # Move Motor and Read Magnet Encoder
    for i in range(4):    
        motor.single_move(90)
        motor.read_position()
        sleep(0.1)
        mag.read_angle()
        sleep(0.1)

eval_enc()