import tello
from tello_control_ui import TelloUI
from stray_tracking import StrayTracking

def main():

    drone = tello.Tello('', 8889)  
    #vplayer = TelloUI(drone,"./img/")
    tracker = StrayTracking(drone , "./img/")
    
	# start the Tkinter mainloop
    #vplayer.root.mainloop() 
    tracker.MainLoop()

if __name__ == "__main__":
    main()
