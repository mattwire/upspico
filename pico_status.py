#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# improved and completed by PiModules Version 1.0 29.08.2015
# picoStatus-v3.py by KTB is based on upisStatus.py by Kyriakos Naziris
# Kyriakos Naziris / University of Portsmouth / kyriakos@naziris.co.uk

import sys
import smbus
import time
import datetime

# You can install psutil using: sudo pip install psutil
#import psutil

i2c = smbus.SMBus(1)

def pwr_mode():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69, 0x00)
   data = data & ~(1 << 7)
   if (data == 1):
      return "ONLINE"
   elif (data == 2):
      return "ONBATT"
   else:
      return "ERR"

def bat_level():
   time.sleep(0.1)
   data = i2c.read_word_data(0x69, 0x01)
   data = format(data,"02x")
   return (float(data) / 100)

def rpi_level():
   time.sleep(0.1)
   data = i2c.read_word_data(0x69, 0x03)
   data = format(data,"02x")
   return (float(data) / 100)

def watchdog_val():
   time.sleep(0.1)
   data = i2c.read_word_data(0x69, 0x0e)
   data = format(data,"02x")
   return data

def charger_state():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69, 0x10)
   data = data & ~(1 << 7)
   if (data == 1):
      return "CHARGING"
   elif (data == 0):
      return "NOT CHARGING"
   else:
      return "ERR"

def fw_version():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x6b, 0x00)
   data = format(data,"02x")
   return data

def sot23_temp():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69, 0x0C)
   data = format(data,"02x")
   return data

def to92_temp():
   time.sleep(0.1)
   data = i2c.read_byte_data(0x69, 0x0d)
   data = format(data,"02x")
   return data

def ad1_read():
   time.sleep(0.1)
   data = i2c.read_word_data(0x69, 0x05)
   data = format(data,"02x")
   return (float(data) / 100)

def ad2_read():
   time.sleep(0.1)
   data = i2c.read_word_data(0x69, 0x07)
   data = format(data,"02x")
   return (float(data) / 100)

def status():
    status = "TIME     : %s" % datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S') \
    + "\nFIRMWARE : %s" % fw_version() \
    + "\nSTATUS   : %s " % pwr_mode() \
    + "\nSTATE    : %s " % charger_state() \
    + "\nBATTV    : %.02f Volts" % bat_level() \
    + "\nRPIV     : %.02f Volts" % rpi_level() \
    + "\nITEMP    : %s C" % sot23_temp() \
    + "\nA/D1 Voltage : %.02f V" % ad1_read() \
    + "\nA/D2 Voltage : %.02f V" % ad2_read() \
    + "\nWatchdog : %s" % watchdog_val()
    return status

if __name__ == '__main__':
    print status()
