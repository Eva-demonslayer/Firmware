import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import csv
from Pressure_test import pressure_check

if __name__ == '__main__':

    # Generator function with a while loop
    def infinite_data_generator():
        i = 0
        while True:
            yield i, i*2
            i += 1
            time.sleep(0.1)

    # Initialize figure and axes
    fig, ax = plt.subplots()
    xdata, ydata = [], []
    ln, = plt.plot([], [])

    # Animation function
    def animate(frame):
        x, y = frame
        print(f"Frame: {frame}, X: {x}, Y: {y}")  # Debugging print statement
        xdata.append(x)
        ydata.append(y)
        ln.set_data(xdata, ydata)
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()  # Force a redraw of the figure canvas
        return ln,

    # duration of test 
    FRAME_INTERVAL = 100   # interval 100 milliseconds = 10 frames per second
    TEST_DURATION = 10     # duration of the test in seconds
    MAX_FRAMES = int(TEST_DURATION * 1000 / FRAME_INTERVAL)  # calculate the number of frames

    # Set up animation
    # ani = animation.FuncAnimation(fig, animate, frames=infinite_data_generator, save_count=MAX_FRAMES, interval=FRAME_INTERVAL, blit=True)
    ani = animation.FuncAnimation(fig, animate, frames=pressure_check, save_count=MAX_FRAMES, interval=FRAME_INTERVAL, blit=True)

    # Add labels and title
    ax.set_xlabel('Time')
    ax.set_ylabel('Pressure (Mbar)')
    ax.set_title('Pressure Monitor')

    # Function to stop the animation
    def stop_animation():
        ani.event_source.stop()

    # Create and start the timer
    timer = fig.canvas.new_timer(interval=TEST_DURATION * 1000) #times a 1000 to convert to seconds
    timer.add_callback(stop_animation)
    timer.start()

    plt.show()

    # print(xdata, ydata)  # Debugging print statement
    combined = zip(xdata, ydata)
    time_stamp = time.strftime("%Y-%m-%d %H:%M:%S", time
    .localtime())
    with open('pressure_data.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time', 'Pressure', time_stamp])
        writer.writerows(combined)
    print("Data written to pressure_data.csv")