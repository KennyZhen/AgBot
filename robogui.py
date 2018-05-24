from Tkinter import *
import threading, time
import SensorComm
import RoboComm
import Camera
from picamera.array import PiRGBArray
from picamera import PiCamera
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages')
from PIL import Image, ImageTk
import numpy as np
import datetime
import csv
camera = Camera.Camera()
sc = SensorComm.SensorComm()
rc = None


def connectBot():
    """ Activates the robot base and robot arm."""
    global rc
    rc = RoboComm.RoboComm(mobilePortEntry.get(), armPortEntry.get(), brEntry.get())


d = datetime.datetime.now()
datestr = d.strftime("%Y%m%d%H%M%S")

########### Root Frame ###########
root = Tk()
root.wm_title("Robot Control Console")
# root.config(background="#000000")
camera.resolution = (1024, 768)
rawCapture = PiRGBArray(camera)
# Exit Handler
exit = False
def on_closing():
    global exit
    exit = True
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
camera.startPreview()

########### Robot Config Frame ###########
configFrame = Frame(root, width=1500, height=95)
configFrame.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
mobilePortLabel = Label(configFrame, text="MOBILE PORT")
mobilePortLabel.grid(row=0, column=0, padx=6, pady=8)
mobilePortEntry = Entry(configFrame, width=11)
mobilePortEntry.grid(row=0, column=1)
mobilePortEntry.insert(END, '/dev/ttyUSB0') ###### Board 328 (5V, 16), port 1
armPortLabel = Label(configFrame, text="ARM PORT")
armPortLabel.grid(row=0, column=2, padx=6, pady=8)
armPortEntry = Entry(configFrame, width=11)
armPortEntry.grid(row=0, column=3)
armPortEntry.insert(END, '/dev/ttyUSB1') ###### Board 328 (5V, 16), port 1
brLabel = Label(configFrame, text="BAUDRATE")
brLabel.grid(row=0, column=4, padx=6, pady=8)
brEntry = Entry(configFrame, width=6)
brEntry.grid(row=0, column=5, padx=6)
brEntry.insert(END, 9600)
cnxButton = Button(configFrame, text="CONNECT", command=connectBot)
cnxButton.grid(row=0, column=6, padx=6)

########### Sensor Information Variables #####
defaultSensor = "Vapor Pressure Deficit"
sensorMsgDict = {}
collectBool = False
collectMsg = "START DATA COLLECTION"
selectedSensor = defaultSensor

########### Sensor Reading Frame ###########
def updateSensorMsgDict():
    """Update the sensor messages with the current sensor readings and the corresponding analyses.
    This function runs every time new data is collected or a new sensor is chosen from the dropdown menu.
    """
    global sensorMsgDict
    tempMsg = str(round(sc.read_temp_hum()[0],2))
    humMsg = str(round(sc.read_temp_hum()[1],2))
    moistureMsg = sc.read_moisture()
    vpdVal = sc.read_VPD()
    if vpdVal < 0.4:
        vpdMsg = "Danger: Low VPD. Remove excess moisture in the air"
    elif vpdVal < 0.8:
        vpdMsg = "Low Transpiration Rate:Sign of Early Vegetative Growth"
    elif vpdVal < 1.2:
        vpdMsg = "Healthy Transpiration Rate: Sign of Ending Growth Phase & Early Flowering"
    elif vpdVal < 1.6:
        vpdMsg = "High Transpiration Rate: Sign of Mid or Late Flowering"
    elif vpdVal < 2.0:
        vpdMsg = "Danger: High VPD. Increase moisture in the air"
    else:
        vpdMsg = "Error"
    sensorMsgDict = {
    "Temperature/Humidity": "Above are the temperature and relative humidity readings, respectively. Temperature is in Celsius and humidity is relative to equilibrium water vapor pressure. The temperature is "+tempMsg+"C and the humidity is "+humMsg,
    "Vapor Pressure Deficit": "Vapor Pressure Deficit, or VPD, is a metric that examines how a plant is reacting to the humidity in the air. Current VPD status ->"+vpdMsg,
    #"Ultrasonic": "Tracks distance",
    #"Sunlight": "Sunlight levels",
    "Moisture": "The moisture sensor reading identifies the existence of moisture. The sensor displays 0 to indicate dry soil and 1023 to indicate wet soil. Current moisture status ->"+moistureMsg,
    #"GPS": "GPS coordinates"
    }

def pollSensor():
    """processes the current sensor readings. Displays the sensor reading for the selected sensor.
    If currently collecting data, then all current sensor readings are appended to the opened CSV file.
    This function is rerun every 1 second: time.sleep(1)
    """
    global sensorText
    global sensorMsgEntry
    global sensorMsgDict
    global collectBool
    sensorDict = {
        "Temperature/Humidity": sc.read_temp_hum,
        "Vapor Pressure Deficit": sc.read_VPD,
        #"Ultrasonic": sc.read_rear_sonar,
        #"Sunlight": sc.read_IR,
        "Moisture": sc.read_moisture,
        #"GPS": sc.read_gps_data,
        }
    updateSensorMsgDict()
    sensorMsgEntry.insert(1.0, sensorMsgDict[selectedSensor])
    while not exit:
        sensorText.delete(1.0, END)
        sensorText.insert(END, sensorDict[selectedSensor]())
        if collectBool:
            with open('Data/data_'+datestr+'.csv', 'a') as csvfile:
                filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                filewriter.writerow([sensorDict["Temperature/Humidity"]()[0], sensorDict["Temperature/Humidity"]()[1], sensorDict["Vapor Pressure Deficit"](),
                                 sensorDict["Moisture"]()])
        time.sleep(1)

def callBack(x):
    """Updates the selected sensor. Runs updateSensorMsgDict(). Updates the sensor message textbox."""
    global selectedSensor
    global sensorMsgEntry
    global sensorMsgDict
    selectedSensor = x
    # print ("changed to " + x)
    updateSensorMsgDict()
    sensorMsgEntry.delete(1.0, END)
    sensorMsgEntry.insert(1.0, sensorMsgDict[selectedSensor])

def collect():
    """Boolean toggle to start or stop data collection."""
    global collectBool
    global collectMsg
    collectBool = not collectBool
    if collectBool:
        collectButton["text"] = "STOP DATA COLLECTION"
    else:
        collectButton["text"] = "START DATA COLLECTION"

# Start the CSV file
with open('Data/data_'+datestr+'.csv', 'w') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['Temperature', 'Humidity', 'Vapor Pressure Deficit', 'Moisture'])

sensorFrame = Frame(root, width=1000, height=950)
sensorFrame.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
sensorText = Text(sensorFrame, width=40, height=1)
sensorText.grid(row=0, column=2, padx=6, pady=2)
sensorMsgEntry = Text(root, width=120, height=3, wrap="word")
sensorMsgEntry.grid(row=2, column=0, columnspan=3, padx=15)
t = threading.Thread(target=pollSensor)
t.start()
sensorLabel = Label(sensorFrame, text="SENSOR")
sensorLabel.grid(row=0, column=0, padx=6, pady=2)
tkvar = StringVar(root)
sensors = {"Temperature/Humidity", "Vapor Pressure Deficit", "Moisture"}
tkvar.set(defaultSensor)
popupMenu = OptionMenu(sensorFrame, tkvar, *sensors, command=callBack)
popupMenu.config(width=20)
popupMenu.grid(row=0, column=1, padx=6, pady=2)
collectButton = Button(sensorFrame, text=collectMsg, command=collect)
collectButton.grid(row=0, column=3, padx=25, pady=15)

########### Robot Arm Frame ###########
duration = 5
currentAngles = [90, 165, 45]
poseExtended  = [90, 60, 105]
poseIntoSoil1 = [90, 15, 180]
poseIntoSoil2 = [90, 15, 150]
poseRetracted = [90, 165, 0]
increment = 15
pressedTime = 10
pressed = None
def rBase():
    """Activate Base servo with positive movement (i.e. moves to the right).
        Holding down the "Base Right" button will continuously execute this function. """
    global pressed
    currentAngles[0] = currentAngles[0] + increment
    if currentAngles[0] > 180:
        currentAngles[0] = 180
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])
    pressed = root.after(pressedTime,rBase)

def rBaseOn(event):
    """Turns on continuous Base positive movement"""
    #print("base right")
    rBase()

def rBaseOff(event):
    """Turns off continuous Base positive movement"""
    global pressed
    root.after_cancel(pressed)

def lBase():
    """Activate Base servo with negative movement (i.e. moves to the left).
        Holding down the "Base Left" button will continuously execute this function. """

    global pressed
    currentAngles[0] = currentAngles[0]-increment
    if currentAngles[0] < 0:
        currentAngles[0] = 0
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])
    pressed = root.after(pressedTime,lBase)

def lBaseOn(event):
    """Turns on continuous Base negative movement"""
    #print("base left")
    lBase()

def lBaseOff(event):
    """Turns off continuous Base negative movement"""
    global pressed
    root.after_cancel(pressed)

def upSh():
    """Activate Shoulder servo with positive movement (i.e. moves upwards).
        Holding down the "Shoulder Up" button will continuously execute this function. """

    global pressed
    currentAngles[1] = currentAngles[1]+increment
    if currentAngles[1] > 180:
        currentAngles[1] = 180
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])
    pressed = root.after(pressedTime,upSh)
    
def upShOn(event):
    """Turns on continuous Shoulder positive movement"""
    #print("shoulder up")
    upSh()
    
def upShOff(event):
    """Turns off continuous Shoulder positive movement"""
    global pressed
    root.after_cancel(pressed)

def downSh():
    """Activate Shoulder servo with negative movement (i.e. moves downwards).
        Holding down the "Shoulder Down" button will continuously execute this function. """
    global pressed
    currentAngles[1] = currentAngles[1]-increment
    if currentAngles[1] < 0:
        currentAngles[1] = 0
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])
    pressed = root.after(pressedTime,downSh)
    
def downShOn(event):
    """Turns on continuous Shoulder negative movement"""
    #print("shoulder down")
    downSh()
    
def downShOff(event):
    """Turns off continuous Shoulder negative movement"""
    global pressed
    root.after_cancel(pressed)
    
def upEl():
    """Activate Elbow servo with negative movement (i.e. moves upwards).
        Holding down the "Elbow Down" button will continuously execute this function. """
    global pressed
    currentAngles[2] = currentAngles[2]+increment
    if currentAngles[2] > 180:
        currentAngles[2] = 180
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])
    pressed = root.after(pressedTime,upEl)
    
def upElOn(event):
    """Turns on continuous Elbow positive movement"""
    #print("elbow up")
    upEl()
    
def upElOff(event):
    """Turns off continuous Elbow positive movement"""
    global pressed
    root.after_cancel(pressed)

def downEl():
    """Activate Elbow servo with negative movement (i.e. moves downwards).
        Holding down the "Elbow Down" button will continuously execute this function. """
    global pressed
    currentAngles[2] = currentAngles[2]-increment
    if currentAngles[2] < 0:
        currentAngles[2] = 0
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])
    pressed = root.after(pressedTime,downEl)
    
def downElOn(event):
    """Turns on continuous Elbow negative movement"""
    #print("elbow down")
    downEl()
    
def downElOff(event):
    """Turns off continuous Elbow negative movement"""
    global pressed
    root.after_cancel(pressed)


# Poses
def retract():
    """Moves the arm into a retracted position by bringing it close to the base and pointing upwards"""
    global currentAngles
    currentAngles = poseRetracted
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])

def extend():
    """Moves the arm into a fully outward extended position"""
    global currentAngles
    currentAngles = poseExtended
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])

def intoSoil1():
    """Moves the arm into an extended position and slightly lifted at the elbow"""
    global currentAngles
    currentAngles = poseIntoSoil1
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])

def intoSoil2():
    """Moves the arm into an extended position and slightly lowered at the elbow"""
    global currentAngles
    currentAngles = poseIntoSoil2
    rc.move_arm(duration, (currentAngles[0], currentAngles[1], currentAngles[2]))
    print "move to " + str(currentAngles[0]) + "/" + str(currentAngles[1])+ "/" + str(currentAngles[2])

# Arm GUI
armFrame = Frame(root, width=495, height=395)
armFrame.grid(row=3, column=1, padx=5, pady=5)

elUpButton = Button(armFrame, text="  Elbow Up  ")
elUpButton.pack(side=TOP, padx=15, pady=8)
elUpButton.bind('<ButtonPress-1>', upElOn)
elUpButton.bind('<ButtonRelease-1>', upElOff)

shUpButton = Button(armFrame, text="   Elbow Down   ")
shUpButton.pack(side=TOP, padx=15, pady=8)
shUpButton.bind('<ButtonPress-1>', downElOn)
shUpButton.bind('<ButtonRelease-1>', downElOff)

lBaseButton = Button(armFrame, text="  Base Left   ")
lBaseButton.pack(side=LEFT, padx=15, pady=5)
lBaseButton.bind('<ButtonPress-1>', lBaseOn)
lBaseButton.bind('<ButtonRelease-1>', lBaseOff)

rBaseButton = Button(armFrame, text=" Base Right ")
rBaseButton.pack(side=RIGHT, padx=15, pady=5)
rBaseButton.bind('<ButtonPress-1>', rBaseOn)
rBaseButton.bind('<ButtonRelease-1>', rBaseOff)

shDownButton = Button(armFrame, text="Shoulder Up")
shDownButton.pack(side=TOP, padx=15, pady=8)
shDownButton.bind('<ButtonPress-1>', upShOn)
shDownButton.bind('<ButtonRelease-1>', upShOff)

elDownButton = Button(armFrame, text="  Shoulder Down  ")
elDownButton.pack(side=BOTTOM, padx=15, pady=8)
elDownButton.bind('<ButtonPress-1>', downShOn)
elDownButton.bind('<ButtonRelease-1>', downShOff)
##

posesFrame = Frame(root, width = 200, height=395)
posesFrame.grid(row=3, column=0)

retractButton = Button(posesFrame, text="Retracted Pose", command=retract)
retractButton.pack(side=TOP, padx=15, pady = 5)
extendButton = Button(posesFrame, text="Extended Pose", command=extend)
extendButton.pack(side=TOP, padx=15, pady=5)
soil1Button = Button(posesFrame, text="Reach Plant Pose", command=intoSoil1)
soil1Button.pack(side=TOP, padx=15, pady=5)
soil2Button = Button(posesFrame, text="Into Soil Pose", command=intoSoil2)
soil2Button.pack(side=TOP, padx=15, pady=5)


##def moveClick():
##    base = baseEntry.get()
##    shoulder = shoulderEntry.get()
##    elbow = elbowEntry.get()
##    rc.move_arm(duration, (base, shoulder, elbow))
##    print "move to " + base + "/" + shoulder + "/" + elbow


##baseLabel = Label(armFrame, text="BASE         ")
##baseLabel.grid(row=0, column=0, padx=15, pady=8)
##baseEntry = Entry(armFrame, width=15)
##baseEntry.grid(row=0, column=1, padx=15)
##baseEntry.insert(0, 0)
##shoulderLabel = Label(armFrame, text="SHOULDER")
##shoulderLabel.grid(row=1, column=0, padx=15, pady=8)
##shoulderEntry = Entry(armFrame, width=15)
##shoulderEntry.grid(row=1, column=1, padx=15)
##shoulderEntry.insert(0, 0)
##elbowLabel = Label(armFrame, text="ELBOW      ")
##elbowLabel.grid(row=2, column=0, padx=15, pady=8)
##elbowEntry = Entry(armFrame, width=15)
##elbowEntry.grid(row=2, column=1, padx=15)
##elbowEntry.insert(0, 0)
##moveButton = Button(armFrame, text="MOVE", command=moveClick)
##moveButton.grid(row=3, column=1, padx=15, pady=8)


########### Mobile Platform Frame ###########
speed = 650
stopped = False
def upClick():
    global stopped
    stopped = False
    rc.move(1, speed)
    print "forward"

def downClick():
    global stopped
    stopped = False
    rc.move(0, speed)
    print "backward"
    
def leftClick():
    global stopped
    stopped = False
    rc.move(2, speed)    
    print "rotate left"

def rightClick():
    global stopped
    stopped = False
    rc.move(3, speed)    
    print "rotate right"

def stopClick():
    global stopped
    stopped = True
    rc.move(4, speed)
    print "slow to stop"


########## Camera and Vision ##########
im = ImageTk.PhotoImage(Image.open("/home/pi/Robot Code/AgriculturalRobotAPI/image.jpg").resize((250,250),Image.ANTIALIAS))

def camClick():
    """Perform the camClick function in the Camera module, which takes a photo and displays it on the GUI"""
    global im
    camera.camClick()
    im = ImageTk.PhotoImage(Image.open("/home/pi/Robot Code/AgriculturalRobotAPI/plantcv/guiimage.jpg").resize((250,250),Image.ANTIALIAS))
    imageLabel.config(image=im)
    print "camclick completed"

def pipeline():
    """Perform the Pipeline function in the Camera module"""
    camera.pipeline()
    print "pipeline completed"

def ndvi():
    """Perform the NDVI function in the Camera module"""
    camera.ndvi()
    print "ndvi completed"

    
mobileFrame = Frame(root, width=495, height=395)
mobileFrame.grid(row=3, column=2, padx=5, pady=5)
camButton = Button(mobileFrame, text="  CAMERA  ", command=camClick)
camButton.pack(side=TOP, padx=15, pady=8)
upButton = Button(mobileFrame, text="   FORWARD   ", command=upClick)
upButton.pack(side=TOP, padx=15, pady=8)
downButton = Button(mobileFrame, text="BACKWARD", command=downClick)
downButton.pack(side=BOTTOM, padx=15, pady=8)
leftButton = Button(mobileFrame, text="  LEFT   ", command=leftClick)
leftButton.pack(side=LEFT, padx=15)
rightButton = Button(mobileFrame, text=" RIGHT ", command=rightClick)
rightButton.pack(side=RIGHT, padx=15, pady=5)
stopButton = Button(mobileFrame, text="  STOP  ", command=stopClick)
stopButton.pack(side=TOP, padx=15, pady=8)

imageLabel = Label(root, image=im)
imageLabel.grid(row=4, column=2, padx=6, pady=8)

vision_text="Pipeline is a function that performs thresholding and center of mass calculations for a plant in a test image. This analysis is important for future autonomous movement innovations. \n\nNormalized Difference Vegitation Index (NDVI) is a graphical indicator that assesses the density of green vegatation in a target image."

visionFrame = Frame(root, width=200, height=300)
visionFrame.grid(row=4, column=0, padx=5, pady=5)
pipelineButton = Button(visionFrame, text="PIPELINE", command=pipeline)
pipelineButton.pack(side=TOP, pady=15)
ndviButton = Button(visionFrame, text="NDVI ANALYSIS", command=ndvi)
ndviButton.pack(side=BOTTOM, pady=5)

visionAnalysisLabel = Text(root, width=75, height= 6, wrap="word")
visionAnalysisLabel.grid(row=4, column=1, padx=10, pady=5)
visionAnalysisLabel.insert(1.0, vision_text)
root.mainloop()
