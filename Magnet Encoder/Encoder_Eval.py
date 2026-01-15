################### Encoder_Eval #############################

import Mag_Encoder as mag
import Motor_Optical_Encoder as motor
from time import sleep

# rotation direction settings (cw for clockwise, ccw for counter-clockwise)
CW = 0x14                       
CCW = 0x04                      

# Test parameters
sleep_time = 0.2
test_angle = 15
test_loop_iterations = 24

def motor_setup():
    # Initialize Motor to 0 position
    motor.configure(CW)
    motor.reset_position()
    # motor.single_move(0)
    sleep(1)
def mag_setup():
    # Initialize Magnet Encoder
    mag.initialize_zero_position()
    sleep(sleep_time)
    mag.test_loop()
    sleep(sleep_time)

def eval_enc():
    # Magnetic Encoder in active mode
    # mag.enable_pin()
    # sleep(sleep_time)
    # Move Motor and Read Magnet Encoder    
    for i in range(test_loop_iterations):    
        motor.single_move(test_angle)
        motor.read_position()
        sleep(sleep_time)
        mag.read_angle()
        sleep(sleep_time)

motor_setup()
mag_setup()
eval_enc()

while True:
    user_input = input("Would you like to run the evaluation again? (y/N): ").strip().lower()
    if user_input == "y":
        eval_enc()
    else:
        print("Exiting evaluation.")
        break