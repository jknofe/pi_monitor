#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import sys
import time
import socket
import os
import shlex
import RPi.GPIO as GPIO
from subprocess import call, PIPE, STDOUT

from RPLCD import CharLCD
from RPLCD import Alignment, CursorMode, ShiftMode
from RPLCD import cursor, cleared
from RPLCD import BacklightMode

# defines
PIN_GPIO  = 12	 # gpio on pin 12
DSPL_TIME = 5	 # seconds
UI_TICKDL = 0.25 # seconds

try:
    input = raw_input
except NameError:
    pass

try:
    unichr = unichr
except NameError:
    unichr = chr

# get current time
def _get_time():
	act_time_str = time.strftime("%d.%b %H:%M:%S")
	return act_time_str

def _get_cpu_temp():
    tempFile = open("/sys/class/thermal/thermal_zone0/temp")
    cpu_temp = tempFile.read()
    tempFile.close()
    cpu_temp = float(cpu_temp)/1000
    cpu_temp_str = str(str("{0:2.1f}".format(cpu_temp)))
    return cpu_temp_str

# get total rain this day
def _get_disk_space():
	disk_free_val = 12.345
	str_disk_free = str(disk_free_val) + "GB free"
	return str_disk_free

# get total rain this day
def _get_day_rain():
	rain_val = 0
	str_rain_day = "Rain: " + str(rain_val) + "mm"
	return str_rain_day

# get current outside temprature
def _get_temp_curr():
	temp_val = 15.6
	str_temp_curr = "Temp: " + str(temp_val)
	return str_temp_curr

# execute a shell comand an get return value
def _get_shell_ret_code(cmd, stderr=STDOUT):
    args = shlex.split(cmd)
    return call(args, stdout=PIPE, stderr=stderr)

# check if internet is connected, ping google dns, if no reponse no internet
def _is_connected():
    #cmd = "ping -c 1 www.google.com"
    cmd = "ping -c 1 8.8.8.8"
    return _get_shell_ret_code(cmd) == 0


# get ip form dnydns script result
def _get_ip():
	try:
		ip_file = open('/media/ramdisk/log/my_ip.log','r')
		ip_add = ip_file.readline()
		ip_add = ip_add.rstrip(os.linesep)
	except:
		ip_add = "no IP yet..."
	#print ip_add
	return ip_add


# init gpio
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(PIN_GPIO, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# init LCD
lcd = CharLCD(cols=16, rows=2)
# create :) and :(
happy = (0b00000, 0b01010, 0b01010, 0b00000, 0b10001, 0b10001, 0b01110, 0b00000)
sad   = (0b00000, 0b01010, 0b01010, 0b00000, 0b01110, 0b10001, 0b10001, 0b00000)
block = (0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111) 
degr  = (0b01110, 0b01010, 0b01110, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000) # °
lcd.create_char(0, sad)
lcd.create_char(1, happy)
lcd.create_char(2, block)
lcd.create_char(3, degr)

while True:
	count = 0
	lcd.clear()
	lcd.write_string(_get_time())
	lcd.cursor_pos = (1, 0)
	
	# put smiley indicator if connected
	if _is_connected() == True:
		lcd.write_string(_get_ip())
		lcd.cursor_pos = (1, 15)
		lcd.write_string(unichr(1))
	else:
		lcd.write_string("Kein Internet!")
		lcd.cursor_pos = (1, 15)
		lcd.write_string(unichr(0))

	# if buttin is hold, count hold time #############
	if(GPIO.input(PIN_GPIO) ==1):
		# clear lcd
		lcd.clear()
		lcd.cursor_pos = (0, 0)
		lcd.write_string("  1  |  2  |  3 ")
		lcd.cursor_pos = (0, 0)
		
		# as long as button is hold show indicators, if hold reaches 15 end loop
		while (GPIO.input(PIN_GPIO) == 1):
			lcd.write_string(unichr(2))
			count += 1
			time.sleep(UI_TICKDL)
			if count >= 16:
				lcd.cursor_pos = (0, 0)
				lcd.write_string("  1  |  2  |  3 ")
				lcd.cursor_pos = (0, 0)
				count = 0
			pass

	# if button was pressed unti segment 3, initiate reboot
	# sleep, butto was not pressed this loop
	if 	 (count == 0):
		time.sleep( DSPL_TIME )
	elif (count <= 5):
		# show solar and weather data
		lcd.clear()
		lcd.cursor_pos = (0, 0)
		lcd.write_string(_get_temp_curr())
		lcd.write_string(unichr(3))
		lcd.write_string("C")
		lcd.cursor_pos = (1, 0)
		lcd.write_string(_get_day_rain())
		time.sleep(DSPL_TIME)
	elif (count <= 11):
		# cpu temp
		lcd.clear()
		lcd.cursor_pos = (0, 0)
		lcd.write_string("CPU temp: " + _get_cpu_temp())
		lcd.write_string(unichr(3))
		lcd.write_string("C")
		lcd.cursor_pos = (1, 0)
		lcd.write_string(_get_disk_space())
		time.sleep(DSPL_TIME)
		# disk free space
	elif (count <= 16):
		# close lcd connection
		lcd.clear()
		lcd.cursor_pos = (0, 0)
		lcd.write_string("Rebooting")
		lcd.cursor_pos = (1, 0)
		lcd.write_string("please stand by.")
		# set reboot indicator
		if _get_shell_ret_code("touch /media/ramdisk/reboot.ind") != 0:
			print("create reboot file failed!")
		break
	
	# end button #############################

lcd.close()

# close gpio
GPIO.cleanup()

# EOF