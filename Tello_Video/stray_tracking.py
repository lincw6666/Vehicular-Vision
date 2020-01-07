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
                time.sleep(7)
                self.state = STATE_PATROL
                
            elif self.state is STATE_PATROL:
                #Do patrol
                isFinish = self.Patrol()
                if isFinish:
                    print "Patrol Finish!!"
                    self.state = STATE_FINISH
                elif self.StrayDection():
                    print "Detect Stray animal!!!"
                    Linebot.SendMessage("Detect stray animal!!!!")
                    self.state = STATE_TRACKING
                    
            elif self.state is STATE_TRACKING:
                #Do tracking
                self.Tracking()
                if not self.StrayDection():
                    print 'Lost object!! Ready to Land.....'
                    self.state = STATE_FINISH
                else :
                    print "Tracking...."
                    Linebot.SendMessage("Tracking....")
                    
            elif self.state is STATE_FINISH:
                if self.Land() == 'ok':
                    print 'Land success!!!!'
                    return
            time.sleep(1.5)
                    
    def Patrol(self):
        #Do partrol and return finish or not. Ture means finish, False mean need continue.
        threashold = 5
        #response = self.vplayer.tello.move_forward(self.vplayer.distance)
        response = 'ok'
        print response
        if response == 'ok':
            self.partrolDistance += self.vplayer.distance
            if self.partrolDistance > threashold:
                return False #need modify
                
        return False
            
    def StrayDection(self):
        #Detect stray animal and return exist stray animal or not. Ture means exist stray animal.
        Threashold = 150
        if self.vplayer.frame is None or self.vplayer.frame.size == 0: return
        self.yolo.predict(self.vplayer.frame)
        if len(self.yolo.boxes)>0:
            ids = np.array(self.yolo.ids)
            animalIndexes = np.concatenate((np.where(ids == 15)[0] , np.where(ids == 16)[0]))#dog
            humanIndexes = np.where(ids == 0)[0]#person
            humanIndexes = [] #need modify
            for animalIndex in animalIndexes:
                x ,y ,w ,h = self.yolo.boxes[animalIndex]
                aniCenter = np.array([x + 0.5*w , y + 0.5*h])
                isStray = True ;
                for humanIndex in humanIndexes:
                    X ,Y ,W ,H = self.yolo.boxes[humanIndex]
                    humanCenter = np.array([X + 0.5*W , Y+0.5*H])
                    dist = np.linalg.norm(aniCenter - humanCenter)
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
        #disFromObj = 10*10 #Area of the bbox
        centerError = 100 #Pixel

        #Distance from the object
        #currentDis = self.bboxWidth * self.bboxLength
        #if currentDis > dis:
        #    self.vplayer.tello.move_backward(self.vplayer.distance)
        #else:
        #    self.vplayer.tello.move_forward(self.vplayer.distance)

        #Move object to center
        height, width= 720 , 1280
        currentBboxCenter = self.bboxCenter

        #x direction
        if currentBboxCenter[0] < width/2 - centerError: #Too left
            self.Rotate_CCW(self.vplayer.degree)
        elif currentBboxCenter[0] > width/2 + centerError: #Too right
            self.Rotate_CW(self.vplayer.degree)

        #y direction
        elif currentBboxCenter[1] < height/2 - centerError: #Too top
            self.vplayer.tello.move_backward(self.vplayer.distance)
        elif currentBboxCenter[1] > height/2 + centerError: #Too bottom
            self.vplayer.tello.move_forward(self.vplayer.distance)
        return
        
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
        


