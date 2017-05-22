from threading import Thread
import serialComm
import json
import time
from firebase import firebase

firebase = firebase.FirebaseApplication('https://runestone-d1faf.firebaseio.com/', None)
packageBeingHandled = False;
packageInFront = 3; #Time until package is recognised as a package (seconds)
temperatureUpdateTimer = 5; #Time between temperature updates (seconds)
packageIncrement = 0; #Used to give packages seperate package names.

#Handles a package once it enters the system. Gives the package a name -> finds slot for package in warehouse -> stores package in database -> sends instruction to robot
def packageHandler():
    emptySlot = findEmptySlot()
    global packageIncrement
    packageName = "Package "+str(packageIncrement)
    packageIncrement += 1
    firebase.patch('/warehouse/'+str(packageName), {'row': ''+str(emptySlot[0]), 'shelf':''+str(emptySlot[1]),'temperature':''}) #Store pakcage in database
    global packageBeingHandled
    packageBeingHandled = False #Tell system it is ready for another package


#Find the first empty slot in the warehouse
def findEmptySlot():
    warehouse = firebase.get("/maps/test_map", None)
    rows = warehouse['rows']
    shelves = warehouse['shelves']
    wares = firebase.get("/warehouse", None)
    slotOccupied = False
    for row in range(1, rows+1):
        for shelf in range(1, shelves+1):
            for item in wares:
                if(int(wares[item]['row']) == row and int(wares[item]['shelf']) == shelf):
                    slotOccupied = True
            if(not slotOccupied):
                return (row,shelf)
            else:
                slotOccupied = False

    return None

#Updates the temperature value of items in database
def updateTemperature(temp):
    wares = firebase.get("/warehouse", None)
    global temperatureUpdateTimer
    if(temperatureUpdateTimer <= 0): #Update when timer reaches 0
        for item in wares:
            if(wares[item]['row'] == 1): #Update all items in row 1
                firebase.patch("/warehouse/"+item,{'temperature':''+str(temp)})
                temperatureUpdateTimer = 5 #Time between temperature updates
    temperatureUpdateTimer = temperatureUpdateTimer-1

#Reads JSON data and executes the appropriate actions according to the values found in the data.
def handleArduinoValues(jsonData):
    global packageInFront
    global packageBeingHandled
    json_object = json.loads(jsonData)
    updateTemperature(json_object['Temperature'])
    #The value 265 is hardcoded and might need to be calibrated according to the lighting
    #in the room.
    if(json_object['Light'] < 265 and not packageBeingHandled):
        packageInFront = packageInFront-1
    else:
        packageInFront = 3 #Package is recognized as package if sensor is shaded for 3 or more seconds.

    #Check if package is in front of light sensor and calls packageHandler if it is.
    if(packageInFront <= 0 and not packageBeingHandled):
        print "New package has arrived!"
        packageBeingHandled = True
        thread = Thread(target = packageHandler, args = ()) #Start a packageHandler for the package
        thread.start()

#Finds and returns the package with name packageName in the database
def findPackage(packageName):
    searchString = '/warehouse/'+packageName
    result = firebase.get(searchString, None)
    return result

if __name__ == "__main__":
    packageHandler();
#    serialComm.readCommValues("COM4", handleArduinoValues);