from PIL import Image
from PIL import ImageTk
import Tkinter as tki
from Tkinter import Toplevel, Scale
import threading
import datetime
import cv2
import os
import time
import platform
import Linebot
from tello_control_ui import TelloUI
from yolov3 import Yolov3
import numpy as np

STATE_INIT = 0
STATE_PATROL = 1
STATE_TRACKING = 2
STATE_FINISH = 3

class StrayTracking:
    """Wrapper class to enable the stray animal tracking."""

    def __init__(self,tello,outputpath):
        
        self.vplayer = TelloUI(tello,outputpath) 
        self.yolo = Yolov3(config='yolov3.cfg', weights='yolov3.weights')
        
        self.FailDectionTimes = 0
        self.PatrolTimes = 0
        
        self.state = STATE_INIT  #Finite state machine
        self.bboxCenter = None
        self.bboxHeight = None 
        self.bboxWidth = None 
        self.partrolDistance = 0.0 #accumulated distance in patrol mode
        
       
        #Active linebot thread, if want to send message , call linebot.SendMassage(message) 
        self.linebotThread = threading.Thread(target = Linebot.Active)
        self.linebotThread.daemon = True
        self.linebotThread.start()
        
        # start the Tkinter mainloop
        self.UIThread = threading.Thread(target = self.MainLoop)
        self.UIThread.daemon = True
        self.UIThread.start()
        
    def MainLoop(self):
        #Main loop to handle the whole finite state machine
        #print 'self state: %d' % self.
        #print self.vplayer.tello.send_command('battery?')
        while not self.isEventFinish():
            if self.state is STATE_INIT:
                #Do something init state should do
                self.Takeoff()
                time.sleep(5)
                self.state = STATE_PATROL
                
            elif self.state is STATE_PATROL:
                #Do patrol
                isFinish = self.Patrol()
                if isFinish:
                    print "Patrol Finish!!"
                    self.state = STATE_FINISH
                elif self.StrayDection():
                    print "Detect Stray animal!!!"
                    #Linebot.SendMessage("Detect stray animal!!!!")
                    self.state = STATE_TRACKING
                    
            elif self.state is STATE_TRACKING:
                #Do tracking
                if not self.StrayDection():
                    self.FailDectionTimes = self.FailDectionTimes + 1
                    print 'Lost object!! '
                    if self.FailDectionTimes <= 3:
                        self.vplayer.tello.move_forward(self.vplayer.distance/2)
                    elif self.FailDectionTimes == 4:
                        self.Rotate_CCW(self.vplayer.degree)
                    elif self.FailDectionTimes == 5:
                        self.Rotate_CW(self.vplayer.degree*2)
                    else:
                        print "Ready to Land...."
                        self.state = STATE_FINISH
                else :
                    self.Tracking()
                    self.FailDectionTimes = 0
                    print "Tracking...."
                    #Linebot.SendMessage("Tracking....")
                    
            elif self.state is STATE_FINISH:
                if self.Land() == 'ok':
                    print 'Land success!!!!'
                    return
            time.sleep(1.)
                    
    def Patrol(self):
        #Do partrol and return finish or not. Ture means finish, False mean need continue.
        threashold = 4.9
        if self.PatrolTimes == 0 :
            response = self.vplayer.tello.move_forward(self.vplayer.distance)
        elif self.PatrolTimes ==1 :
            response = self.Rotate_CCW(self.vplayer.degree)
        elif self.PatrolTimes ==2 :
            response = self.Rotate_CW(2*self.vplayer.degree)
        elif self.PatrolTimes ==3 :
            response = self.Rotate_CCW(self.vplayer.degree)
        #response = 'ok'
        #print response
        if response == 'ok':
            self.PatrolTimes += 1
            self.PatrolTimes %= 4
            if self.PatrolTimes == 1:
                self.partrolDistance += self.vplayer.distance
                if self.partrolDistance > threashold:
                    return True
                
        return False
            
    def StrayDection(self):
        #Detect stray animal and return exist stray animal or not. Ture means exist stray animal.
        Threashold = 300 #smaller means that it is easily consider as stray animal
        if self.vplayer.frame is None or self.vplayer.frame.size == 0: return
        self.yolo.predict(self.vplayer.frame)
        if len(self.yolo.boxes)>0:
            ids = np.array(self.yolo.ids)
            animalIndexes = np.where(ids == 56)[0]#dog
            humanIndexes = np.where(ids == 0)[0]#person
            #humanIndexes = [] #need modify
            for animalIndex in animalIndexes:
                x ,y ,w ,h = self.yolo.boxes[animalIndex]
                aniCenter = np.array([x + 0.5*w , y + 0.5*h])
                isStray = True ;
                for humanIndex in humanIndexes:
                    X ,Y ,W ,H = self.yolo.boxes[humanIndex]
                    humanCenter = np.array([X + 0.5*W , Y+0.5*H])
                    dist = np.linalg.norm(aniCenter - humanCenter) #consider the distance of box center
                    dist += 0.6*(abs((Y+H) - (y+h)))# consider the distance of forward/backward
                    print "Distance: " + str(dist)
                    if dist < Threashold : 
                        isStray = False
                        break
                if isStray == True:
                    self.bboxCenter = aniCenter
                    self.bboxHeight = h
                    self.bboxWidth = w
                    #print "Stray detected!"
                    return True
        return False 
        
    def Tracking(self):
         #Follow the stray animal.

        #Setting variables
        disFromObj = 100*100 #Area of the bbox
        centerError = 160 #Pixel


        #Move object to center
        height, width= 720 , 960
        currentBboxCenter = self.bboxCenter
        currentDis = self.bboxWidth * self.bboxHeight
       
        print currentBboxCenter
        print currentDis

        #x direction
        if currentBboxCenter[0] < width/2 - centerError: #Too left
            self.Rotate_CCW(self.vplayer.degree)
            print 'CCW'
        elif currentBboxCenter[0] > width/2 + centerError: #Too right
            self.Rotate_CW(self.vplayer.degree)
            print 'CW'
        
        #Distance from the object
        
        elif currentDis/disFromObj > 5:
            self.vplayer.tello.move_backward(self.vplayer.distance)
            print 'move backward'
        elif currentDis/disFromObj < 4:
            self.vplayer.tello.move_forward(self.vplayer.distance)
            print 'move forward'

        #y direction
        #elif currentBboxCenter[1]= < height/2 - ccurrentBboxCenter[1]: #Too top
        #    self.vplayer.tello.move_backward(self.vplayer.distance)
        #elif currentBboxCenter[1] > height/2 + centerError: #Too bottom
        #    self.vplayer.tello.move_forward(self.vplayer.distance)
        #return
        
    def Land(self):
        #Drone land. Turn 'OK' or 'FALSE'
        return self.vplayer.tello.land()
        
    def Takeoff(self):
        return self.vplayer.tello.takeoff()
        
    def Rotate_CW(self , degree):
        return self.vplayer.tello.rotate_cw(degree)
       
    def Rotate_CCW(self , degree):
        return self.vplayer.tello.rotate_ccw(degree)
    
    def isEventFinish(self): #Return Ture means finish
        return self.vplayer.stopEvent.is_set()
        


