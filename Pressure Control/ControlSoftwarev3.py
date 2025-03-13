# import PumpControl
import PumpControl4Valve
import sys
import tkinter as tk
import csv
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.pyplot as plt
import time
from tkinter import filedialog
import threading

starttime=time.time()

PGraph=[]
graphtime=[]

stop = False
datasave = False
filename=r"C:\Users\CHENCX127\Documents\Python\20250115 Python Sample Script.txt"
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
    
# Startup connections with hardware
def init():
    global stop
    stop = True
    # PumpControl4Valve.init()
    # PumpControl4Valve.SetPumpValue(0)
    graphing()
    setPValue()

# Close connections
def closeProgram():
    if stop == True:
        PumpControl4Valve.exit()
    writeToCSV()
    sys.exit()

# Export if save data button is checked   
def writeToCSV():
    if datasave == True:
    # if checkbutton.cget('variable')==1:
        print('saving data!')
        with open('graphdata.csv', 'w', newline = 
                  '') as f:
            writer = csv.writer(f)
            writer.writerows(zip(graphtime, PGraph))

# Operates Button toggle
def on_button_toggle():
    global datasave
    if datasaver.get() == 1:
        datasave = True
    else:
        datasave = False

def ActivateValve(n, button):
    if button.cget('bg')=='white':
        button.config(bg="pink")
    elif button.cget('bg')=='pink':
        button.config(bg = 'white')

    if button.cget('text') == " Positive ":
        button.config(text = 'Negative')
    elif button.cget('text')=='Negative':
        button.config(text= " Positive ")

    if button.cget('text') == 'All Off':
        for i in range(len(ValveList)):
            ValveList[i].config(bg='white')
            if ValveList[i].cget('text')=='Negative':
                ValveList[i].config(text = ' Positive ')
        
    PumpControl4Valve.ChangeValve(n)
    # if n==0:
    #     currentV = 0
    # elif n%2 == 1:
    #     currentV=n//2+1
    # elif n%2 == 0:



# Set new values
def setPValue():
    P = Pressure.get()
    print(P)
    tk.Label(root, text ="  "+P+"  " ).grid(row = 0, column= 5)
#     uploadThread = threading.Thread(target=setPValueT,args=(P,root))
#     uploadThread.start()

# def setPValueT(P,root):
    P=float(P)
    PumpControl4Valve.SetPumpValue(P)
    

# Graphing function



def graphing():
    Pline = []
    global PGraph
    global starttime

    # get data points and add to list
    p=round(PumpControl4Valve.ReadPump(),2)
    PGraph.append(p)
    graphtime.append(time.time()-starttime)

    #Update current value
    text = str(p)
    tk.Label(root, text = " "+text+" " ).grid(row = 0, column= 6) 

    Pax.clear()
    Pline = PGraph[-100:]
    Pax.plot(Pline, color = "blue")
    Pax.set_xlabel("Time")
    Pax.set_ylabel("Pressure [mBar]")
    PChart.draw_idle()
   
    # Wait x time, then repeat
    root.after(50, graphing)


def RunScript(): 
    global filename
    uploadThread = threading.Thread(target=RunningScript,args=(filename,root))
    uploadThread.start()

def RunningScript(filename,root):
    i=0
    file = filename
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

    while i<len(newlist):
        entry = newlist[i]
        #More text parsing
        Command=entry.replace(" ","")
        print(Command)
        string=Command.split(',')
        if "Pump" in Command:
            Pump_Registry = string[2]
            Registry_Value = (float(string[3]))
        if "Valve" in Command:
            Pump_Registry = string[0]
            Registry_Value = string[1]
            # Valve[0]=int(string[1])
            # Valve[1]=int(string[2])
            # Valve[2]=int(string[3])
            # Valve[3]=int(string[4])
            # Valve[4]=int(string[5])
            # Valve[5]=int(string[6])
            # Valve[6]=int(string[7])
            # Valve[7]=int(string[8])
        if "Wait" in Command:
            wait_time=int(string[1])
            for t in range(wait_time):
                time.sleep(1)
            i=i+1
            continue
        PumpControl4Valve.RunPump(Pump_Registry,Registry_Value)
        if i+1 == len(newlist):
            print('Script Complete')
        i=i+1
        





# --------------
# Main Function
# --------------

if __name__ == '__main__':

    root = tk.Tk()
    root.title("Control Software")
    # root.geometry("500x400")
    plt.ion

    # Entry buttons and labels
    Plabel=tk.Label(root, text = "Pressure").grid(row = 0, column= 1)
    tk.Label(root, text = "Current Set P").grid(row = 0, column= 4)
    PEntry = tk.Entry()
    PEntry.grid(row = 0, column= 2)

    # Create the application variable.
    Pressure = tk.StringVar()

    # Submit buttons
    Pbutton = tk.Button(root, text = "submit", command = setPValue).grid(row = 0, column= 3)

    # Set defualt value.
    Pressure.set(0)

    # Tell the entry widget to watch this variable.
    PEntry["textvariable"] = Pressure

    # Define a callback for when the user hits return.
    # It prints the current value of the variable.
    PEntry.bind('<Key-Return>', print_contents)

    # Init and Quit buttons
    closeB = tk.Button(root, text = "Quit", command = closeProgram).grid(row = 2, column= 2)
    startB = tk.Button(root, text = "Initialize", command = init).grid(row = 2, column= 1)

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
    PChart.get_tk_widget().grid(row = 4, column= 0)
    Pax.set_title("Pressure")

    # Display Current and Set Pressures
    tk.Label(root, text = 0 ).grid(row = 0, column= 5)
    tk.Label(root, text = 0 ).grid(row = 0, column= 6)

    # color_pallette = {"enabled":"blue", 
    #                   "disabled":"red"}

    #Valve control buttons
    valve1b = tk.Button(root, text = "Port 1", command = lambda: ActivateValve(1,valve1b), background='white')
    valve1b.grid(row=3, column=1)
    valve2b = tk.Button(root, text = "Port 2", command = lambda: ActivateValve(3,valve2b), background='white')
    valve2b.grid(row=3, column=2)
    valve3b = tk.Button(root, text = "Port 3", command = lambda: ActivateValve(5,valve3b), background='white')
    valve3b.grid(row=3, column=3)
    valve4b = tk.Button(root, text = "Port 4", command = lambda: ActivateValve(7,valve4b), background='white')
    valve4b.grid(row=3, column=4)
    valve5b = tk.Button(root, text = "Port 5", command = lambda: ActivateValve(9,valve5b), background='white')
    valve5b.grid(row=3, column=5)
    valve6b = tk.Button(root, text = "Port 6", command = lambda: ActivateValve(11,valve6b), background='white')
    valve6b.grid(row=3, column=6)
    valveNob = tk.Button(root, text = "All Off", command = lambda: ActivateValve(0,valveNob), background = 'red')
    valveNob.grid(row=3, column=9)

    valve1ba = tk.Button(root, text = "1 Close", command = lambda: ActivateValve(2,valve1ba), background='white')
    valve1ba.grid(row=4, column=1)
    valve2ba = tk.Button(root, text = "2 Close", command = lambda: ActivateValve(4,valve2ba), background='white')
    valve2ba.grid(row=4, column=2)
    valve3ba = tk.Button(root, text = "3 Close", command = lambda: ActivateValve(6,valve3ba), background='white')
    valve3ba.grid(row=4, column=3)
    valve4ba = tk.Button(root, text = "4 Close", command = lambda: ActivateValve(8,valve4ba), background='white')
    valve4ba.grid(row=4, column=4)
    valve5ba = tk.Button(root, text = "5 Close", command = lambda: ActivateValve(10,valve5ba), background='white')
    valve5ba.grid(row=4, column=5)
    valve6ba = tk.Button(root, text = "6 Close", command = lambda: ActivateValve(12,valve6ba), background='white')
    valve6ba.grid(row=4, column=6)

    valveposneg1 = tk.Button(root, text = " Positive ", command = lambda: ActivateValve(13,valveposneg1), bg = 'white')
    valveposneg1.grid(row=5, column=1)
    valveposneg2 = tk.Button(root, text = "Vent", command = lambda: ActivateValve(14,valveposneg2), background='white')
    valveposneg2.grid(row=5, column=2)

    ValveList = [valve1b, valve2b, valve3b, valve4b, valve5b, valve6b, valve1ba, valve2ba, valve3ba, valve4ba, valve5ba, valve6ba, valveposneg1, valveposneg2]

    #Script Buttons
    button_explore = tk.Button(root,text = "Browse Files",command = browseFiles).grid(row = 2, column = 4)
    scriptStart = tk.Button(root,text = "Start Script",command = RunScript).grid(row = 2, column = 5)

    # Add Graph tool bar
    # PtoolbarFrame = tk.Frame(master=root)
    # PtoolbarFrame.grid(row=4,column=0)
    # Ptoolbar = NavigationToolbar2Tk(Pfigure, PtoolbarFrame)


    root.mainloop()