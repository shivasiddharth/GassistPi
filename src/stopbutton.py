#!/usr/bin/env python
import time
import os
import os.path
import RPi.GPIO as GPIO
import subprocess
from actions import stop

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP)

while GPIO.input(23):
    time.sleep(0.01)
    if not GPIO.input(23):
       print('Stopped')
       stop() 
