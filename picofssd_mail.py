#!/usr/bin/env python2
# Manage the UPS pico.
# Send emails, pulse train and trigger shutdown
# Import the libraries to use time delays, send os commands and access GPIO pins
import RPi.GPIO as GPIO
import time
import os
import socket
import smbus
import datetime
import pico_status

# Configurable variables
checkInterval=5 # Interval between checking powering mode in seconds
shutdownDelay=1 # Delay before shutdown in minutes
minBatteryLevel=3.4 # Minimum battery level before shutdown triggers

# Mail configuration
fqdn = socket.getfqdn()
sendmail = "/usr/sbin/sendmail"
sender = "root@" + fqdn
receivers = ["root"]

#--------------------------------------------------------
# msgid=START,ONBATT,CRIT,ONLINE,SHUTDOWN
def mailMessage(msgid):
  if(msgid=="START"):
    subject = fqdn + " UPS system started"
    text = subject
  elif(msgid=="ONBATT"):
    subject = fqdn + " UPS Power Failure !!!"
    text = fqdn + " UPS power failure.  Now running on Battery"
  elif (msgid=="CRIT"):
    subject = fqdn + " UPS Power Critical. Shutting down !!!"
    text = fqdn + " UPS Power Critical. System will shutdown and restart when power is restored"
  elif (msgid=="ONLINE"):
    subject = fqdn + " UPS Power Restored."
    text = fqdn + " UPS Power Restored. Now running on line"
  elif (msgid=="SHUTDOWN"):
    subject = fqdn + " UPS Triggered Shutdown"
    text = subject
  elif (msgid=="BATNOCHARGE"):
    subject = fqdn + " UPS Battery not charging !!!"
    text = subject
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
 
def checkBatteryLevel():
  if (pico_status.bat_level() < minBatteryLevel):
    return "LOW"
  else:
    return "OK"

# Initialise board
GPIO.setmode(GPIO.BCM) # Set pin numbering to board numbering
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Setup pin 27 as an input
GPIO.setup(22, GPIO.OUT) # Setup pin 22 as an output
i2c = smbus.SMBus(1)

# Initialise variables
# onbatt/online flags
# 0=not, 1=first detect, 2=second detect, >2=message sent
onbatt=0
online=2
battV=0
minBattV=battV
maxBattV=battV
lastTime = datetime.datetime.now()
started=False

while True: # Setup a while loop to wait for a button press
    # Send keepalive pulse to ups
    GPIO.output(22,True)
    time.sleep(0.25) # Allow a sleep time of 0.25 second to reduce CPU usage
    GPIO.output(22,False)
    time.sleep(0.25) # Allow a sleep time of 0.25 second to reduce CPU usage
    
    # Every checkInterval seconds check powering mode
    if (datetime.datetime.now() > (lastTime + datetime.timedelta(seconds=checkInterval))):
      if not started:
        started=True
        # Send startup message after initial checkInterval
        mailMessage("START")

      lastTime = datetime.datetime.now()
      pwrmode=pico_status.pwr_mode()
      if(pwrmode=="ONBATT"):
        # Running On battery
        onbatt+=1
        online=0
        if (onbatt == 2):
          # Same state for 5 seconds or more
          print pwrmode
          mailMessage("ONBATT")
        elif (onbatt > 3):
          # No need to count above 3
          onbatt=3
          if (checkBatteryLevel()=="LOW"):
            # Report and shutdown
            mailMessage("CRIT")
    	    os.system("/sbin/shutdown -h +% 'UPS Battery Low. Shutting down.'" % shutdownDelay)

      elif(pwrmode=="ONLINE"):
        # Running On line
        online+=1
        onbatt=0
        if (online == 2):
          # Same state for 5 seconds or more
          print pwrmode
          mailMessage("ONLINE")
        elif (online > 2):
          # Check that battery is charging and UPS is alive
          battV=pico_status.bat_level()
          if (battV < minBattV):
            minBattV=battV
          if (battV > maxBattV):
            maxBattV=battV
          if (online == 102):
            # On the 102th cycle (5mins) maxBattV should be greater than minBattV if charging
            if ((maxBattV <= minBattV) and (minBattV < 4.1)):
              mailMessage("BATNOCHARGE")
          # Count 3 to 102 (100 cycles) to check V over one minute
          if (online > 101):
            online = 3
    
    # Setup an if loop to run a shutdown command when button press sensed
    if(GPIO.input(27)==0): 
      mailMessage("SHUTDOWN")
      time.sleep(5) # Allow to actually send mail
      os.system("/sbin/shutdown -h now") # Send shutdown command to os
      break
