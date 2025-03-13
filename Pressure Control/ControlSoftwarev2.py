# import PumpControl
import PumpControlMultipValve
import sys
import tkinter as tk
import csv
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# sys.path.append("PythonArduinoGUI")
# import HeaterSensor
import matplotlib.pyplot as plt
import time
from tkinter import filedialog

starttime=time.time()

PGraph=[]
TGraph=[]
graphtime=[]

stop = False
datasave = False
filename="nothing"
currentV = "0"

# -----------------------
# XXXXX Functions XXXXXXX
# -----------------------
     
def browseFiles():
    global filename
    file = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
    filename = file
    print(filename)

# submit data on pressing "enter"
def print_contents(events):
    setPValue()
    # setTValue()
    
# Startup connections with hardware
def init():
    PumpControlMultipValve.init()
    PumpControlMultipValve.SetPumpValue(0)
    # HeaterSensor.init()
    # HeaterSensor.runTest()
    graphing()

# Close connections
def closeProgram():
    stop = True
    PumpControlMultipValve.exit()
    # HeaterSensor.exit()
    writeToCSV()
    sys.exit()

# Export if save data button is checked   
def writeToCSV():
    if datasave == True:
        with open('graphdata.csv', 'w', newline = 
                  '') as f:
            writer = csv.writer(f)
            writer.writerows(zip(graphtime, PGraph,TGraph))

# Operates Button toggle
def on_button_toggle():
    global datasave
    if datasaver.get() == 1:
        datasave = True
    else:
        datasave = False

def ActivateValve(n):
    PumpControlMultipValve.ChangeValve(n)
    currentV = n
    vvalue=tk.Label(root, text = currentV).grid(row = 1, column = 4)


# Set new values
def setPValue():
    P = Pressure.get()
    PumpControlMultipValve.main(P)
    tk.Label(root, text = P ).grid(row = 0, column= 4)

# def setTValue(): 
#     T = Temp.get()
#     # HeaterSensor.main(T)
#     tk.Label(root, text = T).grid(row = 1, column= 4)


# Graphing function
def graphing():
    Pline = []
    Tline = []
    global PGraph, TGraph

    # get data points and add to list
    # t=round(float(HeaterSensor.recvFromArduino()),2)
    p=round(PumpControlMultipValve.ReadPump(),2)
    # TGraph.append(t)
    PGraph.append(p)
    graphtime.append(time.time()-starttime)

    #Update current value
    tk.Label(root, text = p).grid(row = 0, column= 5) 
    # tk.Label(root, text = t).grid(row = 1, column= 5)

    # Graph new lines
    # xs = xs[-500:]
    # timetime=graphtime[-100:]

    Pax.clear()
    Pline = PGraph[-100:]
    Pax.plot(Pline, color = "blue")
    Pax.set_xlabel("Time")
    Pax.set_ylabel("Pressure [mBar]")
    PChart.draw_idle()

    # Tax.clear()
    # Tline = TGraph[-100:]
    # Tax.plot(Tline, color = "green")
    # Tax.set_xlabel("Time")
    # Tax.set_ylabel("Temperature [C]")
    # TChart.draw_idle()
    
    # Wait x time, then repeat
    root.after(50, graphing)

def RunScript():  
    PumpControlMultipValve.script(filename)



# --------------
# Main Function
# --------------

if __name__ == '__main__':

    root = tk.Tk()
    root.title("Control Software")
    # root.geometry("500x400")
    plt.ion

    # Entry buttons and labels
    Plabel=tk.Label(root, text = "Pressure").grid(row = 0, column= 0)
    # Tlabel=tk.Label(root, text = "Temperature").grid(row = 1, column= 0)
    tk.Label(root, text = "Current Set P").grid(row = 0, column= 3)
    # tk.Label(root, text = "Current Set T").grid(row = 1, column= 3)
    PEntry = tk.Entry()
    # TEntry = tk.Entry()
    PEntry.grid(row = 0, column= 1)
    # TEntry.grid(row = 1, column= 1)

    # Create the application variable.
    Pressure = tk.StringVar()
    # Temp = tk.StringVar()

    # Submit buttons
    Pbutton = tk.Button(root, text = "submit", command = setPValue).grid(row = 0, column= 2)
    # Tbutton = tk.Button(root, text = "submit", command = setTValue).grid(row = 1, column= 2)

    # Set defualt value.
    Pressure.set(0)
    # Temp.set(0)

    # Tell the entry widget to watch this variable.
    PEntry["textvariable"] = Pressure
    # TEntry["textvariable"] = Temp

    # Define a callback for when the user hits return.
    # It prints the current value of the variable.
    PEntry.bind('<Key-Return>', print_contents)
    # TEntry.bind('<Key-Return>',print_contents)

    # Init and Quit buttons
    closeB = tk.Button(root, text = "Quit", command = closeProgram).grid(row = 2, column= 1)
    startB = tk.Button(root, text = "Initialize", command = init).grid(row = 2, column= 0)

    # Save Data
    datasaver = tk.IntVar()
    checkbutton = tk.Checkbutton(root, text = "Save Data?", variable = datasaver, onvalue = 1, offvalue = 0, command = on_button_toggle)
    checkbutton.grid(row = 1, column = 6)

    # Pressure Graph
    Pfigure = plt.figure(figsize=(6, 4), dpi=100)
    Pax = Pfigure.add_subplot(111)
    PChart = FigureCanvasTkAgg(Pfigure, master = root)
    Pax.set_xlabel("Time")
    Pax.set_ylabel("Pressure [mBar]")
    PChart.draw()
    PChart.get_tk_widget().grid(row = 3, column= 0)
    Pax.set_title("Pressure")

    # #Temperature Graph
    # Tfigure = plt.figure(figsize=(6, 4), dpi=100)
    # Tax = Tfigure.add_subplot(111)
    # TChart = FigureCanvasTkAgg(Tfigure, master = root)
    # Tax.set_xlabel("Time")
    # Tax.set_ylabel("Temperature [C]")
    # TChart.draw()
    # TChart.get_tk_widget().grid(row = 3, column= 1)
    # Tax.set_title("Temperature")

    # Display Current and Set Pressures
    tk.Label(root, text = 0 ).grid(row = 0, column= 4)
    # tk.Label(root, text = 56 ).grid(row = 1, column= 4)
    tk.Label(root, text = 0 ).grid(row = 0, column= 5)
    # tk.Label(root, text = 0 ).grid(row = 1, column= 5)

    #state active valve
    tk.Label(root, text = "Current Active Valve").grid(row = 1, column= 3)
    vvalue=tk.Label(root, text = currentV).grid(row = 1, column = 4)

    #Valve control buttons
    valve1b = tk.Button(root, text = "Valve 1", command = lambda: ActivateValve(1), activebackground="blue").grid(row=3, column=1)
    valve2b = tk.Button(root, text = "Valve 2", command = lambda: ActivateValve(2), activebackground="green").grid(row=3, column=2)
    valve3b = tk.Button(root, text = "Valve 3", command = lambda: ActivateValve(3), activebackground="red").grid(row=3, column=3)
    valve4b = tk.Button(root, text = "Valve 4", command = lambda: ActivateValve(4), activebackground="purple").grid(row=3, column=4)
    valve5b = tk.Button(root, text = "Valve 5", command = lambda: ActivateValve(5), activebackground="orange").grid(row=3, column=5)
    valve6b = tk.Button(root, text = "Valve 6", command = lambda: ActivateValve(6), activebackground="brown").grid(row=3, column=6)
    valve7b = tk.Button(root, text = "Valve 7", command = lambda: ActivateValve(7), activebackground="pink").grid(row=3, column=7)
    valve8b = tk.Button(root, text = "Valve 8", command = lambda: ActivateValve(8), activebackground="gray").grid(row=3, column=8)
    valveNob = tk.Button(root, text = "All Off", command = lambda: ActivateValve(0)).grid(row=3, column=9)


    # button_explore = tk.Button(root,text = "Browse Files",command = browseFiles).grid(row = 2, column = 4)
    # scriptStart = tk.Button(root,text = "Start Script",command = RunScript).grid(row = 2, column = 5)

    # Add Graph tool bar
    # PtoolbarFrame = tk.Frame(master=root)
    # PtoolbarFrame.grid(row=4,column=0)
    # Ptoolbar = NavigationToolbar2Tk(Pfigure, PtoolbarFrame)

    # TtoolbarFrame = tk.Frame(master=root)
    # TtoolbarFrame.grid(row=4,column=1)
    # Ttoolbar = NavigationToolbar2Tk(Tfigure, TtoolbarFrame)

    root.mainloop()