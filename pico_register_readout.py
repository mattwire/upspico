#!/usr/bin/env python2

# pico_register_readout.py
# Written by Pontus Petersson (pontus.pson@gmail.com)
# Version 1: 2015-10-16

import commands

# RTC data
year =   commands.getstatusoutput("i2cget -y 1 0x6A 6")
month =   commands.getstatusoutput("i2cget -y 1 0x6A 5")
day =    commands.getstatusoutput("i2cget -y 1 0x6A 4")
dow =   commands.getstatusoutput("i2cget -y 1 0x6A 3")
hour =    commands.getstatusoutput("i2cget -y 1 0x6A 2")
min =    commands.getstatusoutput("i2cget -y 1 0x6A 1")
sec =    commands.getstatusoutput("i2cget -y 1 0x6A 0")
ccf =    commands.getstatusoutput("i2cget -y 1 0x6A 7")

days_of_the_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

YEAR =   "20" + year[1][2:]
MONTH = month[1][2:]
DAY =    day[1][2:]
DOW =    days_of_the_week[int(dow[1][3:])-1]
HOUR =    hour[1][2:]
MIN =    min[1][2:]
SEC =   sec[1][2:]
CCF =   ccf[1][2:]

print("--- RTC data ---")
print(YEAR+"-"+MONTH+"-"+DAY+" "+DOW+" "+HOUR+":"+MIN+":"+SEC+" /"+CCF+"\n")

# Status registers
mode =      commands.getstatusoutput("i2cget -y 1 0x69 0")
batlevel_1 =    commands.getstatusoutput("i2cget -y 1 0x69 2")
batlevel_2 =    commands.getstatusoutput("i2cget -y 1 0x69 1")
rpilevel_1 =    commands.getstatusoutput("i2cget -y 1 0x69 4")
rpilevel_2 =    commands.getstatusoutput("i2cget -y 1 0x69 3")
tmpcels =    commands.getstatusoutput("i2cget -y 1 0x69 12")

powering_modes = ['RPi', 'Bat']

MODE =      powering_modes[int(mode[1][2:])-1]
BATLEVEL =   batlevel_1[1][3:]+"."+batlevel_2[1][2:]+" V"
RPILEVEL =   rpilevel_1[1][3:]+"."+rpilevel_2[1][2:]+" V"
TMPCELS =   tmpcels[1][2:]+" "+unichr(176)+"C"

print("--- Status registers ---   ")
print("Mode\t\tBat_lvl\t\tRPi_lvl\t\tTemp")
print(MODE+"\t\t"+BATLEVEL+"\t\t"+RPILEVEL+"\t\t"+TMPCELS+"\n")

# Module commands
version =    commands.getstatusoutput("i2cget -y 1 0x6B 0")
error_code =    commands.getstatusoutput("i2cget -y 1 0x6B 1")
rpi_serror_1 =    commands.getstatusoutput("i2cget -y 1 0x6B 3")
rpi_serror_2 =    commands.getstatusoutput("i2cget -y 1 0x6B 2")
bat_serror_1 =    commands.getstatusoutput("i2cget -y 1 0x6B 5")
bat_serror_2 =    commands.getstatusoutput("i2cget -y 1 0x6B 4")
tmp_serror_1 =    commands.getstatusoutput("i2cget -y 1 0x6B 7")
tmp_serror_2 =    commands.getstatusoutput("i2cget -y 1 0x6B 6")
sta_counter =    commands.getstatusoutput("i2cget -y 1 0x6B 8")
fssd_batime =   commands.getstatusoutput("i2cget -y 1 0x6B 9")
lprsta =    commands.getstatusoutput("i2cget -y 1 0x6B 10")
btto =      commands.getstatusoutput("i2cget -y 1 0x6B 11")
led_blue =   commands.getstatusoutput("i2cget -y 1 0x6B 12")
led_red =   commands.getstatusoutput("i2cget -y 1 0x6B 13")
buzmode =   commands.getstatusoutput("i2cget -y 1 0x6B 14")
fanmode =   commands.getstatusoutput("i2cget -y 1 0x6B 15")
fanspeed =   commands.getstatusoutput("i2cget -y 1 0x6B 16")
xbmc =      commands.getstatusoutput("i2cget -y 1 0x6B 23")
fssd_tout =   commands.getstatusoutput("i2cget -y 1 0x6B 24")

status =   ['OFF', 'ON']
buz_fan_modes =   ['Disabled', 'Enabled', 'Automatic', 'Unknown']
fan_speeds =   ['0', '100', '25', '50', '75']

VERSION =    version[1][2:]
ERROR_CODE =   '{0:08b}'.format(int(error_code[1][2:]))
RPI_SERROR =   rpi_serror_1[1][3:]+"."+rpi_serror_2[1][2:]+" V"
BAT_SERROR =   bat_serror_1[1][3:]+"."+bat_serror_2[1][2:]+" V"
TMP_SERROR =   tmp_serror_1[1][2:]+"."+tmp_serror_2[1][2:]+" "+unichr(176)+"C"
STA_COUNTER =   int(sta_counter[1], 16)
FSSD_BATIME =   int(fssd_batime[1], 16)
LPRSTA =   int(lprsta[1], 16)
BTTO =      int(btto[1], 16)
LED_BLUE =   status[int(led_blue[1][3:])]
LED_RED =   status[int(led_red[1][3:])]
BUZMODE =   buz_fan_modes[int(buzmode[1][3:])]
FANMODE =   buz_fan_modes[int(fanmode[1][3:])]
FANSPEED =   fan_speeds[int(fanspeed[1][3:])]
XBMC =      status[int(xbmc[1][3:])]
FSSD_TOUT =   int(fssd_tout[1], 16)

print("--- Status commands ---")
print("Firmware: %s" % VERSION)
print("Error code: %s" % ERROR_CODE)
print("rpi_serror: %s" % RPI_SERROR)
print("bat_serror: %s" % BAT_SERROR)
print("tmp_serror: %s" % TMP_SERROR)
print("Still Alive Timeout Counter: %d s (255=disabled)" % STA_COUNTER)
print("Battery Running Time: %d s (255=disabled)" % FSSD_BATIME)
print("Low Power Restart Time: %d s" % LPRSTA)
print("Battery Powering Testing Timeout: %d s" % BTTO)
print("led_blue: %s" % LED_BLUE)
print("led_red: %s" % LED_RED)
print("Integrated Buzzer Mode: %s" % BUZMODE)
print("Integrated Fan Mode: %s" % FANMODE)
print("Integrated Fan Speed: %s %%" % FANSPEED)
print("XBMC Mode: %s" % XBMC)
print("FSSD Timeout: %d s" % FSSD_TOUT)
