#!/usr/bin/env python2
# Import the libraries to use time delays, send os commands and access GPIO pins
import RPi.GPIO as GPIO
import time
import os
 
GPIO.setmode(GPIO.BCM) # Set pin numbering to board numbering
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Setup pin 27 as an input
GPIO.setup(22, GPIO.OUT) # Setup pin 22 as an output

while True: # Setup a while loop to wait for a button press
    GPIO.output(22,True)
    time.sleep(0.25) # Allow a sleep time of 0.25 second to reduce CPU usage
    GPIO.output(22,False)
    if(GPIO.input(27)==0): # Setup an if loop to run a shutdown command when button press sensed
    	os.system("sudo shutdown -h now") # Send shutdown command to os
    	break

    time.sleep(0.25) # Allow a sleep time of 0.25 second to reduce CPU usage

