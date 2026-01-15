################### Encoder_Eval #############################

import Mag_Encoder as mag
import Motor_Optical_Encoder as motor
from time import sleep
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import scrolledtext

# rotation direction settings (cw for clockwise, ccw for counter-clockwise)
CW = 0x14                       
CCW = 0x04                      

# Test parameters
sleep_time = 0.2
test_angle = 15
test_loop_iterations = 24

def motor_setup():                      # Initialize Motor
    motor.configure(CW)
    motor.reset_position()
    sleep(1)
def mag_setup():                        # Initialize Magnet Encoder
    mag.initialize_zero_position()
    sleep(sleep_time)
    mag.test_loop()
    sleep(sleep_time)
def eval_enc(): 
    mag_degrees_list = []
    expected_angles = []
    for i in range(test_loop_iterations): 
        sleep(sleep_time)   
        motor.single_move(test_angle)
        motor.read_position()
        sleep(sleep_time)
        mag_degrees = mag.read_angle()
        mag_degrees_list.append(mag_degrees)
        expected_angles.append((i + 1) * test_angle)
        sleep(sleep_time)
    return mag_degrees_list, expected_angles

# setup motor and magnet encoder
motor_setup()
mag_setup()

while True:
    user_input = input("Would you like to run the evaluation? (y/N): ").strip().lower()
    if user_input == "y":
        expected, measured = eval_enc()
        plt.figure()
        plt.plot(expected, measured, marker='o', label='Mag Encoder')
        plt.plot(expected, expected, '--', label='Ideal')
        plt.xlabel('Expected Angle (deg)')
        plt.ylabel('Measured Angle (deg)')
        plt.title('Mag Encoder vs. Expected Angle')
        plt.legend()
        plt.grid(True)
        plt.show()

        # Calculate deviations
        deviations = [m - e for m, e in zip(measured, expected)]
        deviation_lines = [f"Step {i+1}: {dev:+.2f}" for i, dev in enumerate(deviations)]
        deviation_text = "Deviations from Ideal\n" + "\n".join(deviation_lines)

        # Show deviations in a separate window
        root = tk.Tk()
        root.title("Deviations from Ideal")
        text_area = scrolledtext.ScrolledText(root, width=40, height=20)
        text_area.pack(padx=10, pady=10)
        text_area.insert(tk.END, deviation_text)
        text_area.config(state='disabled')
        root.mainloop()
    else:
        mag.clean_up()
        motor.clean_up()
        print("Exiting evaluation.")
        break