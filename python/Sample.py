################################################################################
# Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################
import sys
import time
import OSC
import math
import threading
import Leap

from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture



class SampleListener(Leap.Listener):
    isTimerRunning = False;
    isCircleComplete = True;
    isSwipeComplete = True;

    def startAsyncTimer(self,delay=0.3):
        threading.Thread(target=wait, args=[self,delay], kwargs={}).start()   

    def sendMSG(self,content,route_list):

        oscmsg = OSC.OSCMessage()
        oscmsg.setAddress("/"+route_list[0])
        for i in range(1,len(route_list)):
            oscmsg.append("/"+route_list[i])
        oscmsg.append(content)
        self.client.send(oscmsg)

    def on_init(self, controller):
        print "############################Initalized############################"
        self.client = OSC.OSCClient()
        self.client.connect(('127.0.0.1', 5005))  


    def on_connect(self, controller):
        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);
        controllerSetup(controller)


    def on_disconnect(self, controller):
        print "############################Disconnected############################"

    def on_exit(self, controller):
        print "############################Exited############################"

    def on_frame(self, controller):
        frame = controller.frame()

        # print  "Gestes reconnus : %d" % (len(frame.gestures()))                

        # Get hands

        if len(frame.hands) == 0:
            self.sendMSG(-1,["positionMain"])
        else:
            hand = frame.hands[0]
            self.sendMSG(distance(hand.palm_position,[0,0,0]),["positionMain"])

        # Get gestures

        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_CIRCLE and not self.isTimerRunning:
                circle = CircleGesture(gesture)

                # Determine clock direction using the angle between the pointable and the circle normal
                if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
                    clockwiseness = "trigo"
                else:
                    clockwiseness = "horaire"

                if circle.state is Leap.Gesture.STATE_START and self.isCircleComplete:
                    print "starting circle "+clockwiseness
                    self.isCircleComplete = False
                    self.sendMSG("bang",["events","circle",clockwiseness,"start"])
                if circle.state is Leap.Gesture.STATE_STOP and not self.isCircleComplete:
                    print "stopping circle "+clockwiseness
                    self.isCircleComplete = True
                    self.startAsyncTimer()
                    self.sendMSG("bang",["events","circle",clockwiseness,"stop"])

            if gesture.type == Leap.Gesture.TYPE_SWIPE and not self.isTimerRunning:

                swipe = SwipeGesture(gesture)
                velocity = swipe.speed

                isHorizontal = abs(swipe.direction[0]) > abs(swipe.direction[1])

                if(isHorizontal):
                    if(swipe.direction[0] > 0):
                        swipeDirection = "right"
                    else:
                        swipeDirection = "left"
                
                else:
                    if(swipe.direction[1] > 0):
                        swipeDirection = "up";
                    else:
                        swipeDirection = "down";
                       
                if swipe.state is Leap.Gesture.STATE_START and self.isSwipeComplete:
                    self.isSwipeComplete = False
                    print "swipe "+swipeDirection+" occurred"                
                    self.sendMSG("bang",["events","swipe",swipeDirection])

                if swipe.state is Leap.Gesture.STATE_UPDATE:
                    if self.isSwipeComplete:
                        self.isSwipeComplete = False
                print "swipe speed : %d" % (velocity)
                self.sendMSG(velocity,["events","swipe","speed"])

                if swipe.state is Leap.Gesture.STATE_STOP and not self.isSwipeComplete:
                    print "swipe stopped"
                    self.isSwipeComplete = True
                    self.startAsyncTimer()
                    self.sendMSG("bang",["events","swipe","stop"])


            if gesture.type == Leap.Gesture.TYPE_KEY_TAP and not self.isTimerRunning:
                keytap = KeyTapGesture(gesture)
                self.startAsyncTimer();
                print "keytap occurred"
                self.sendMSG("bang",["events","keytap"])

            if gesture.type == Leap.Gesture.TYPE_SCREEN_TAP and not self.isTimerRunning:
                screentap = ScreenTapGesture(gesture)
                self.startAsyncTimer();
                print "screentap occurred"
                self.sendMSG("bang",["events","screentap"])



def controllerSetup(c):
    #Swipe
    c.config.set("Gesture.Swipe.MinLength", 100.0)
    c.config.set("Gesture.Swipe.MinVelocity", 1000)
    #ScreenTap
    c.config.set("Gesture.ScreenTap.MinForwardVelocity", 20.0)
    c.config.set("Gesture.ScreenTap.HistorySeconds", .1)
    c.config.set("Gesture.ScreenTap.MinDistance", 5.0)
    #KeyTap
    c.config.set("Gesture.KeyTap.MinDownVelocity", 20.0)
    c.config.set("Gesture.KeyTap.HistorySeconds", .1)
    c.config.set("Gesture.KeyTap.MinDistance", 5.0)
    #Circle
    c.config.set("Gesture.Circle.MinRadius", 20.0)
    c.config.set("Gesture.Circle.MinArc", 1.5*Leap.PI)

    c.config.save()

def distance(a,b):
    ans=0
    for i in range(0,2):
        ans += (a[i]-b[i])*(a[i]-b[i])
    return math.sqrt(ans)


def wait(listener,delay):
    listener.isTimerRunning=True;
    time.sleep(delay) 
    listener.isTimerRunning=False;

def main():
    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        # Remove the sample listener when done
        controller.remove_listener(listener)


if __name__ == "__main__":
    main()


