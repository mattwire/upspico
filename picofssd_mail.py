#!/usr/bin/env python2
# Import the libraries to use time delays, send os commands and access GPIO pins
import RPi.GPIO as GPIO
import time
import os
import socket
import smtplib
import smbus
import pico_status

fqdn = socket.getfqdn()

sendmail = "/usr/sbin/sendmail"
sender = "root@" + fqdn
receivers = ["root"]

#--------------------------------------------------------
# msgid=1 started
# msgid=2 onbatt
# msgid=3 shutdown
def mailMessage(msgid):
  if(msgid==1):
    subject = fqdn + " UPS system started"
    text = fqdn + " UPS system started"
  elif(msgid==2):
    subject = fqdn + " UPS Power Failure !!!"
    text = fqdn + " UPS power failure.  Now running on Battery"
  elif (msgid==3):
    subject = fqdn + " UPS Power Critical. Shutting down !!!"
    text = fqdn + " UPS Power Critical. System will shutdown and restart when power is restored"
  elif (msgid==4):
    subject = fqdn + " UPS Power Restored."
    text = fqdn + " UPS Power Restored. Now running on line"

  message = """\
From: %s
To: %s
Subject: %s

%s

%s
  """ % (sender,  ", ".join(receivers), subject, text, pico_status.status())
  
  p = os.popen("%s -t -i" % sendmail, "w")
  p.write(message)
  status = p.close()
  if status:
    print "Sendmail exit status", status
# mailMessage()
#--------------------------------------------------------
 
def pwr_mode():
   data = i2c.read_byte_data(0x69, 0x00)
   data = data & ~(1 << 7)
   return data

mailMessage(1)

GPIO.setmode(GPIO.BCM) # Set pin numbering to board numbering
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Setup pin 27 as an input
GPIO.setup(22, GPIO.OUT) # Setup pin 22 as an output
i2c = smbus.SMBus(1)
onbatt=False
online=True

while True: # Setup a while loop to wait for a button press
    GPIO.output(22,True)
    time.sleep(0.25) # Allow a sleep time of 0.25 second to reduce CPU usage
    GPIO.output(22,False)
    pwrmode=pwr_mode()
    if(pwrmode==2):
      if (onbatt!=True):
        print "ONBATT"
        mailMessage(2)
      onbatt=True
      online=False
    elif(pwrmode==1):
      if (online!=True):
        print "ONLINE"
        mailMessage(4)
      online=True
      onbatt=False
    if(GPIO.input(27)==0): # Setup an if loop to run a shutdown command when button press sensed
        mailMessage(3)
        sleep(5)
    	os.system("shutdown -h now Shutdown by UPS") # Send shutdown command to os
    	break

    time.sleep(0.25) # Allow a sleep time of 0.25 second to reduce CPU usage

