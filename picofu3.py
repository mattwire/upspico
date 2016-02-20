

#!/usr/bin/python
# -*- coding: iso8859_2 -*-
#===============================================================================
#
# USAGE:        picofu.py -f <fw_file> [ -v | -h | -s | -p serial | --force ] 
#
# DESCRIPTION:
#               This script uploads firmware to UPS PIco. Only mandatory input is new UPS PIco firmware.   
#
# RETURN CODES:
#               0 - Sucessfull update   
#               1 - Failed to parse command line arguments   
#               2 - Failed to establish communication with the UPS PIco   
#               3 - Incompatible UPS PIco powering mode (DISABLED FOR NOW)   
#               4 - Failed to validate firmware file   
#               5 - Failed during the FW upload   
#
# OPTIONS:      ---
# REQUIREMENTS: 
#               python-serial
#               python-smbus
#               Propoer HW setup and setup of Pi to enable Serial/I2C communication based on the UPS PIco manual
# BUGS:         ---
# NOTES:        Updated for the UPS PIco by www.pimodules.com
# AUTHOR:       Vit SAFAR <PIco@safar.info> 
# VERSION:      1.4 adopted for UPS PIco December 2014 by PiModules
# CREATED:      2.6.2014
# REVISION: 
#	              v1.0  16.4.2014 - Vit SAFAR
#                 - Initial release
#	              v1.1  17.4.2014 - Vit SAFAR
#                 - Added code documentation
#                 - Some speed-up optimisations    
#	              v1.2  19.4.2014 - Vit SAFAR
#                 - Disabled the power detection, until automatic switch to bootloader mode is enabled
#	              v1.3  2.6.2014 - Vit SAFAR
#                 - Fixed communication issue by adding dummy ';HELLO' command 
#
# TODO:         - Detect FW version
#               - Automatic switch to bootloader mode using @command when available
#               - Automatically enable of the I2C sw components in Pi (load kernel modules) if not done 
#               - Perform optimisation of the FW file to speed up the upload process     
#               - Make the switch to bootloader mode interactive for users who does not have the I2C interface available.
#               - Show UPS PIco @status after firmware update 
#               - Detect progress of the factory reset, not just wait :)
#               - Set UPS PIco RTC clock after factory reset to the system time
#
#===============================================================================
import sys
import time
import datetime
import os
import re     
import getopt

import smbus
import time
import datetime

# You can install psutil using: sudo pip install psutil
#import psutil

i2c = smbus.SMBus(1)



  
class FWUpdate(object):
  """ 
    Only class performing the FW update 
    The class performs following tasks
      1) Check the command line arguments and performs validation of the expected/required parameters
      2) Pereform detection of the Pi powering scheme via I2C or Serial interface 
      3) Perform validation of the FW file
      4) Verify the connectivity to UPS PIco bootloader is working
      5) Perform FW update
      6) Perform UPS PIco factory reset
  
  """

  # running in verbose mode
  verbose=False
  # force the FW update by skipping prechecks
  force=False
  # skip validation of the FW
  skip=False
  # firmware file
  filename=False 
  # default serial port
  port='/dev/ttyAMA0'
  # serial connection established on bloader level
  seria_bloader=False
  # status of the i2c serial feature
  i2c=False
  # detected i2c bus  
  i2c_bus=False
  # default I2C port of UPS PIco control interface
  i2c_port=0x69
  # is Pi powered via Pi or not
  power=False
  # if power not via Pi USB and already warned about via Pi powering requirement
  power_warned=False


  def __init__(self):
  
    # check if smbus module is deployed and load it if possible
    try:
      import smbus
      self.i2c=True
      self.smbus=smbus
    except:
      print 'WARNING: I2C support is missing. Please install smbus support for python to enable additional functionality! (sudo apt-get install python-smbus)'
      self.i2c=False

    # check if pyserial module is deployed and load it if possible
    try:
      import serial
      self.serial=serial
    except:
      print 'ERROR: Serial support is missing. Please install pyserial support for python to enable additional functionality! (sudo apt-get install python-serial)'
      sys.exit(2)
      
    # parse command line arguments
    try:
    	opts, args = getopt.getopt(sys.argv[1:], 'vhf:sp:', ['help', 'force' ])
    except getopt.GetoptError, err:
      # print help information and exit:
      print str(err) # will print something like "option -a not recognized"
      self.usage()
      sys.exit(1)
    for o, a in opts:
      # look for verbose argument
      if o =="-v":
        self.verbose = True
      # look for help argument
      elif o in ("-h", "--help"):
        self.usage()
        sys.exit(1)
      # look for fw filename argument
      elif o == "-f":
        self.filename = a
        # Check if fw filename really exists
        if not os.path.isfile(self.filename):
          print 'ERROR: Input file "'+str(self.filename)+'" cannot be found! Make sure file exists and is readable.'
          sys.exit(1)
      # look for force argument
      elif o == "--force":
        self.force = True
      # look for fw validation skip argument
      elif o == "-s":
        self.skip = True
      # look for serial port definition argument
      elif o == "-p":
        self.port = a
        if not os.path.exists(self.port):
          print 'ERROR: Serial port "'+str(self.port)+'" cannot be found! No need to change this value in most of the cases!'
          sys.exit(1)
      # in case of unknown argument
      else:
        assert False, "ERROR: Unknown option"
        sys.exit(1)

    # Check if serial port device exists
    if not os.path.exists(self.port):
      print 'ERROR: Serial port "'+str(self.port)+'" cannot be found!'
      sys.exit(1)
  
    # Check if fw filename is defined 
    if not self.filename:
      print 'ERROR: Firmware filename has to be defined! :)'
      sys.exit(1)
      
    # check the powering option is ok
    ####self.power_detect()
        
    # validsate the provided firmware file
    if not self.skip:
      self.validate()
    else:
      if self.verbose: print 'WARNING: Skipping firmware validation'
    
    # verify bootloader connectivity
    self.serial_check()
    
    # launch FW upload
    self.fw_upload()
    
    # Execute factory reset of UPS PIco
    self.factory_reset()

  """
  2) Detects the powering status of the Pi
    a) Check the power status via I2C bus 0 and 1 (most common way to do it in the future?)
    b) In case that no answer found (yes or no), check via serial port. 
      - We expect to have serial port in the bootloader mode at this time, so @command on serial interface is not available and it will fail in most of the cases
        
  """
  def power_detect(self):
    if self.verbose: print 'INFO: Detecting power setup'

    # check if the system is powered via Pi USB connector  
    if self.i2c:
      # it's I2C we expect somthing to go wrong :)
      try:
        if self.verbose: print 'INFO: Probing I2C bus 0'
        # open connection to the first I2C bus (applicable mainly for the Rev.1 Pi boards)
        bus = self.smbus.SMBus(0)
        # read the powering systus byte (reffer to the manual for the meaning)
        pwr=bus.read_byte_data(0x6a,0)
        # in case we got valid response (0 is not a vlid return value of this interface, so probably not connected :) )
        if pwr>0:
          self.i2c_bus=0
          # if powered via Pi, than ok
          if pwr==3:
            if self.verbose: print 'INFO: (I2C bus 1) System is powered via the Pi USB port.'
            self.power=True
          # otherwise powered using unsupported mode...
          # if forced to skip this check, lets do it :)
          elif self.force:
            print 'WARNING: (I2C-0) System is not powered via Pi USB port. There is a UPS PIco reset after a FW update, that would perform hard reset of Pi! (use --force to disable this check)'
            self.power_warned=True
          else:
            print 'ERROR: (I2C-0) System has to be powered via the Pi USB port. There is a PIco reset after a FW update, that would perform hard reset of Pi! (use --force to disable this check)'
            sys.exit(3)
      except SystemExit as e:
        sys.exit(e)      
      except:
        pass
      if not self.power:
        try:  
          if self.verbose: print 'INFO: Probing I2C bus 1'
          # open connection to the first I2C bus (applicable mainly for the Rev.2 Pi boards)
          bus = self.smbus.SMBus(1)
          # read the powering systus byte (reffer to the manual for the meaning)
          pwr=bus.read_byte_data(0x6a,0)
          # in case we got valid response (0 is not a vlid return value of this interface, so probably not connected :) )
          if pwr>0:
            self.i2c_bus=1
            # if powered via Pi, than ok
            if pwr==3:
              if self.verbose: print 'INFO: (I2C bus 1) System is powered via the Pi USB port.'
              self.power=True
            # otherwise powered using unsupported mode...
            # if forced to skip this check, lets do it :)
            elif self.force:
              print 'WARNING: (I2C-1) System is not powered via Pi USB port. There is a UPS PIco reset after a FW update, that would perform hard reset of Pi! (use --force to disable this check)'
              self.power_warned=True
            else:
              print 'ERROR: (I2C-1) System has to be powered via the Pi USB port. There is a UPS PIco reset after a FW update, that would perform hard reset of Pi! (use --force to disable this check)'
              sys.exit(3)
        except SystemExit as e:
          sys.exit(e)      
        except:
          pass
    
    # in case power status not ok and we have not detected wrong power status already, check via Serial as a failback method (even though it is expected to fail also due to the bootloader mode requirement) 
    if not self.power and not self.power_warned:
      if self.verbose: print 'INFO: Probing serial port'
      # Set up the connection to the UPS PIco
      PIco= self.serial.Serial(port=self.port,baudrate=38400,timeout=0.05,rtscts=0,xonxoff=0)
      # empty the input buffer
      for line in PIco:
        pass
      # get status of power via serial from PIco
      PIco.write('@PM\r')
      # wait for the answer
      time.sleep(0.5)
      # for each line in the output buffer (there are some newlines returned)
      for line in PIco:
        # get rid of the newline characters
        line=line.strip()
        # is it the answer we are looking for? (yep, should be regexp...)
        if line[:16] == 'Powering Source:':    
          # get the power source (yep, should be regexp...)
          ret=line[16:20]
          # in case it is RPI, everything is ok :)
          if ret == 'RPI':
            self.power=True
            if self.verbose: print 'INFO: System is powered via the Pi USB port.'
          # otherwise powered using unsupported mode...
          # if forced to skip this check, lets do it :)
          elif self.force:
            if not self.power_warned:
              print 'WARNING: (Serial) System is not powered via Pi USB port. There is a PIco reset after a FW update, that would perform hard reset of Pi! (use --force to disable this check)'
              self.power_warned=True
          else:
            print 'ERROR: (Serial) System has to be powered via the Pi USB port. There is a PIco reset after a FW update, that would perform hard reset of Pi! (use --force to disable this check)'
            sys.exit(3)
      # close the connection to PIco via serial
      PIco.close()
              
    #print 'pwr:',self.power,' pwrw:',self.power_warned,' pwr',self.power
    # in case no power information gathered
    if not self.power:
      if self.force:
        if not self.power_warned:
          print 'WARNING: System powering mode not detected. There is a PIco reset after a FW update, that would perform hard reset of Pi! Use --force to disable this check.'
      else:
        print 'ERROR: System powering mode not detected. System has to be powered via the Pi USB port since here is a PIco reset after a FW update, that would perform hard reset of Pi! Make a proper HW/Pi setup of Serial interface or PiCo interface(I2C) to enable auto-detection. This can happen also in case that PIco is already in the bootload mode having PIco RED led lid. Use --force to disable this check.'
        sys.exit(3)
       

  """
  3) Check that there is a PIco bootloader connected to the other side of the serial interface :)
    - Send dummy command and get the confirmation from the bootloader
        
  """
  def serial_check(self):
    print "Checking communication with bootloader:",
    status=False
    try:
      # Set up the connection to the PIco
      PIco = self.serial.Serial(port=self.port,baudrate=38400,timeout=0.05,rtscts=0,xonxoff=True)
      # empty the input buffer
      for line in PIco:
        pass
      # send dummy command
      PIco.write(":020000040000FA\r")
    except:
      print "KO\nERROR: Unable to establish communication with PIco bootloader via port:",self.port,'Please verify that the serial port is availble.'
      sys.exit(2)
    try:
      # set the wait iterations for the bootloader response
      rcnt=1000
      # loop and wait for the response
      while rcnt>0:
        # in case there is something waiting on the serial line
        for resp in PIco:
          # get rid of the nwlines
          resp=resp.strip()
          # check if the response is the expected value or not :)
          if ord(resp[0])==6:
            print "OK"
            status=True
            rcnt=1
          else:
            print "KO\nERROR: Invalid response from PIco:",ord(resp[0])," Please retry the FW upload process."
            sys.exit(2)
          break
        rcnt-=1
    except:
      print "KO\nERROR: Something wrong happened during verification of communication channel with PIco bootloader via port:",self.port,'Please verify that the serial port is availble and not used by some other application.'
      sys.exit(2)
      
    # in case communication not verified
    if not status:
      if self.force:
        print "KO\nWARNING: Unable to verify communication with bootloader in PIco. Is the PIco in the bootloader mode? (Red LED lid on PIco)"      
      else:
        print "KO\nERROR: Failed to establish communication with bootloader in PIco. Is the PIco in the bootloader mode? (Red LED lid on PIco)"
        sys.exit(2)
    # close the channel to PIco
    PIco.close()


  """
  4) Verify the content of the provided FW file by:
        a) validating crc
        b) validating format
        c) validating passed data syntax
  """
  def validate(self):
    print "Validating firmware:",
    valid=False
    #count number of lines
    lnum=1
    # open the FW file
    f = open(self.filename)
    # for each file line
    for line in f:
      #static  LEN ADDR1 ADDR2 TYPE  DATA     CKSUM
      #:       04  05    00    00    50EF2EF0 9A
      # parse the line
      target = re.match( r"^:([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]*)([a-fA-F0-9]{2}).$", line, re.M|re.I|re.DOTALL)
      # in case the data field does not have correct size
      if len(target.group(5))%2!=0:
        print "KO\nLine",lnum,': Invalid bytecode message!'
        sys.exit(4)
      # get the CRC valucalculate CRC
      crc1=int(line[-4:-1],16)
      # calculate the CRC value of the data read
      crc2=0    
      for i in range(1, len(line)-5, 2):
        #print line[i:i+2] 
        crc2+=int(line[i:i+2],16)
      # python cannot simulate byte overruns, so ugly math to be done 
      crc2%=256
      crc2=255-crc2+1
      crc2%=256
      # validate the CRC :)
      if crc1!=crc2:
        print "KO\nLine",lnum,': Invalid bytecode checksum! Defined:', crc1,'Calculated:', crc2
        sys.exit(4)
        
      # in case that the done command is detected, than finish
      if target.group(4)=='01':
         valid=True
         break
      lnum+=1
    # close the FW file
    f.close()
    if not valid:
      print "KO\n Termination signature not found in the firmware file."
      sys.exit(4)
    else:
      print 'OK'




  """
  5) Upload the FW to PIco
        
  """
  def fw_upload(self):
    print "Uploading firmware: 0% ",
    # count the number fo lines in the file for the progress bar
    with open(self.filename) as f:
      lnum=len(list(f))

    # open the FW file
    f = open(self.filename)
    # Set up the connection to the PIco
    PIco = self.serial.Serial(port=self.port,baudrate=38400,timeout=0.001,rtscts=0,xonxoff=True)
    # empty the input buffer
    for line in PIco:
      pass
    status=False
    # send the data to PIco
    PIco.write(";HELLO\r")
    rcnt=100
    # loop and wait for the response
    while rcnt>0:
      # in case there is something waiting on the serial line
      for resp in PIco:
        # get rid of the nwlines
        resp=resp.strip()
        # check if the response is the expected value or not :)
        if ord(resp[0])==6:
          #print "Response OK:",ord(resp)
          status=True
          rcnt=1
        else:
          print "KO\nERROR: Invalid status word from PIco (",ord(resp),') when processing initial line! Please retry the FW upload process.'
          sys.exit(5)
        break
      rcnt-=1
    if not status:
      print "KO\nERROR: No status word from PIco revcieved when processing initial line! Please check possible warnings above and retry the FW upload process."
      sys.exit(5)

    # calculate 5% progress bar step
    lnumx=lnum/100*5
    # count the processed lines
    lnum2=1
    # for each line in the FW file
    for line in f:
      status=False
      # strp the \r\n and add only \r 
      line=line.strip()+"\r"
      # send the data to PIco
      PIco.write(line)
      #print "Written:",line
      # set the wait iterations for the bootloader response
      rcnt=100
      lrcnt=0
      # loop and wait for the response
      while rcnt>0:
        # in case there is something waiting on the serial line
        for resp in PIco:
          # get rid of the nwlines
          resp=resp.strip()
          # check if the response is the expected value or not :)
          if ord(resp[0])==6:
            #print "Response OK:",ord(resp)
            #print "Waited:",rcnt
            status=True
            lrcnt=rcnt
            rcnt=1
          else:
            print "KO\nERROR: Invalid status word from PIco (",ord(resp),') when processing line',lnum2,' Please retry the FW upload process.'
            sys.exit(5)
          break
        rcnt-=1
      if not status:
        print "KO\nERROR: No status word from PIco revcieved when processing line",lnum2,' Please check possible warnings above and retry the FW upload process.'
        sys.exit(5)
      # in case that the done command is detected, than finish
      if line[7:9]=='01':
        break
      lnum2+=1
      # show the update progress and show percentages of the process ssometimes
      if lnum2%lnumx==0:
        print ' '+str(round(float(100*lnum2/lnum)))+'% ',
      else:
        if lrcnt>80: 
          sys.stdout.write('.')
        elif lrcnt>60: 
          sys.stdout.write(',')
        elif lrcnt>40: 
          sys.stdout.write('i')
        elif lrcnt>20: 
          sys.stdout.write('|')
        else: 
          sys.stdout.write('!')
          
      sys.stdout.flush()
    print ' Done uploading...'
    # close the FW file 
    f.close()

  """
  6) Perform factory reset of the PIco
        
  """
  def factory_reset(self):
    #time.sleep(1)
    print "Invoking factory reset of PIco..."
    time.sleep(5)
    status=False
    # Set up the connection to the PIco
    PIco = self.serial.Serial(port=self.port,baudrate=38400,timeout=0.05,rtscts=0,xonxoff=True)
    # empty the input buffer
    for line in PIco:
      pass
    # send factory reset command 
    #i2c.write_byte_data(0x6b, 0x00, 0xdd) 
    time.sleep(5)
    i2c.write_byte_data(0x6b, 0x00, 0xdd) 
    #PIco.write('@factory\r')
    time.sleep(5)
    # close the channel to PIco
    PIco.close()
    print 'ALL Done :) Ready to go...'

  
  def usage(self):
    print "\n",sys.argv[0],' -f <fw_file> [ -v | -h | --force | -s | -p serial | -b i2c_bus_number ]',"\n"
    sys.exit(1)


if __name__ == "__main__":
  FWUpdate()	


