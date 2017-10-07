#!/usr/bin/env python
#This is different from AIY Kit's actions
#Copying and Pasting AIY Kit's actions commands will not work

import os
import os.path
import RPi.GPIO as GPIO
import time
import re
import subprocess

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#Number of entities in 'var' and 'PINS' should be the same
var = ('kitchen lights', 'bathroom lights', 'bedroom lights')#Add whatever names you want. This is case is insensitive
gpio = (23,24,25)#GPIOS for 'var'. Add other GPIOs that you want

for pin in gpio:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

#Servo pin declaration
GPIO.setup(27, GPIO.OUT)
pwm=GPIO.PWM(27, 50)
pwm.start(0)


def SetAngle(angle):
    duty = angle/18 + 2
    GPIO.output(27, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    pwm.ChangeDutyCycle(0)
    GPIO.output(27, False)

def Action(phrase):
    if 'shut down' in phrase:
        subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Pi-Close.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(10)
        os.system("sudo shutdown -h now")
        #subprocess.call(["shutdown -h now"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    if 'servo' in phrase:
        for s in re.findall(r'\b\d+\b', str(usr)):
            SetAngle(int(s))
    if 'zero' in phrase:
        SetAngle(0)

    #****Create your own actions***********
    #if 'çustom-keyword' in phrase:
    #Custom actions here for the detected custom-keyword
    #**************************************

    else:
        for num, name in enumerate(var):
            if name.lower() in phrase:
                pinout=gpio[num]
                if 'on' in phrase:
                    GPIO.output(pinout, 1)
                    subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Device-On.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif 'off' in phrase:
                    GPIO.output(pinout, 0)
                    subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Device-Off.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
