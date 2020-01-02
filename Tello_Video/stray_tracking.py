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

STATE_INIT = 0
STATE_PATROL = 1
STATE_TRACKING = 2
STATE_FINISH = 3

class StrayTracking:
    """Wrapper class to enable the stray animal tracking."""

    def __init__(self,tello,outputpath):
        
        self.vplayer = TelloUI(tello,outputpath) 
        
        self.state = STATE_INIT  #Finite state machine
        self.bbox = None #stray animal bounding box detected.
        self.bboxCoorLeftTop = None
        self.bboxCoorRightBottom = None 
        self.bboxHeight = None 
        self.bboxWidth = None 
        self.partrolDistance = 0.0 #accumulated distance in patrol mode
        
       
        #Active linebot thread, if want to send message , call linebot.SendMassage(message) 
        self.linebotThread = threading.Thread(target = Linebot.Active)
        self.linebotThread.daemon = True
        self.linebotThread.start()
        
        # start the Tkinter mainloop
        self.UIThread = threading.Thread(target = self.vplayer.root.mainloop)
        self.UIThread.daemon = True
        self.UIThread.start()
        
    def MainLoop(self):
        #Main loop to handle the whole finite state machine
        print 'self state: %d' % self.state
        while not self.isEventFinish():
            if self.state is STATE_INIT:
                #Do something init state should do
                #self.Takeoff()
                self.vplayer.tello.takeoff()
                time.sleep(7)
                self.state = STATE_PATROL
                
            elif self.state is STATE_PATROL:
                #Do patrol
                isFinish = self.Patrol()
                if isFinish:
                    self.state = STATE_FINISH
                    
                elif self.StrayDection():
                    Linebot.SendMassage("Detect stray animal!!!!")
                    self.state = STATE_TRACKING
                    
            elif self.state is STATE_TRACKING:
                #Do tracking
                self.Tracking()
                if not self.StrayDection():
                    self.state = STATE_FINISH
                else :
                    Linebot.SendMassage("Tracking....")
                    
            elif self.state is STATE_FINISH:
                if self.Land() == 'ok':
                    return
            time.sleep(2)
                    
    def Patrol(self):
        #Do partrol and return finish or not. Ture means finish, False mean need continue.
        threashold = 5
        response = self.vplayer.tello.move_forward(self.vplayer.distance)
        print 'forward %f' % self.partrolDistance
        if response == 'ok':
            self.partrolDistance += self.vplayer.distance
            if(self.partrolDistance > threashold):
                return True
                
        return False
            
    def StrayDection(self):
        #Detect stray animal and return exist stray animal or not. Ture means exist stray animal.
        return False 
    def Tracking(self):
         #Follow the stray animal.

        #Setting variables
        disFromObj = 10*10 #Area of the bbox
        centerError = 7 #Pixel

        #Distance from the object
        currentDis = self.bboxWidth * self.bboxLength
        if currentDis > dis:
            self.vplayer.tello.move_backward(self.vplayer.distance)
        else:
            self.vplayer.tello.move_forward(self.vplayer.distance)

        #Move object to center
        height, width, _ = self.vplayer.frame.shape
        currentBboxCenter = (self.bboxCoorLeftTop + self.bboxCoorRightBottom) / 2

        #x direction
        if currentBboxCenter[0] < width/2 - centerError: #Too left
            self.Rotate_CCW(self.vplayer.degree)
        elif currentBboxCenter[0] > width/2 + centerError: #Too right
            self.Rotate_CW(self.vplayer.degree)

        #y direction
        if currentBboxCenter[1] < height/2 - centerError: #Too top
            self.vplayer.tello.move_backward(self.vplayer.distance)
        elif currentBboxCenter[1] > height/2 + centerError: #Too bottom
            self.vplayer.tello.move_forward(self.vplayer.distance)
        return
    def Land(self):
        #Drone land. Turn 'OK' or 'FALSE'
        return self.vplayer.tello.land()
        
    def Takeoff(self):
        return self.vplayer.tello.takeoff()
        
    def RotateCW(self , degree):
        return self.vplayer.tello.rotate_cw(degree)
       
    def RotateCCW(self , degree):
        return self.vplayer.tello.rotate_ccw(degree)
    
    def isEventFinish(self): #Return Ture means finish
        return self.vplayer.stopEvent.is_set()
        


