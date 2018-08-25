#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import os
from actions import configuration

audiosetup=''

if os.path.isfile("/home/pi/.GassistPi-Config/audiosetup"):
    with open('/home/pi/.GassistPi-Config/audiosetup') as f:
        detected_audio_setup = f.readline().rstrip()
        print(detected_audio_setup)
        if (detected_audio_setup=='AIY-HAT' or detected_audio_setup=='CUSTOM-VOICE-HAT'):
            audiosetup='AIY'
        elif (detected_audio_setup=='USB-DAC' or detected_audio_setup=='USB-MIC-HDMI' or detected_audio_setup=='USB-MIC-JACK'):
            audiosetup='GEN'
    else:
        audiosetup='GEN'


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Indicators
aiyindicator=configuration['Gpios']['AIY_indicator'][0]
liseningindicator=configuration['Gpios']['assistant_indicators'][0]
speakingindicator=configuration['Gpios']['assistant_indicators'][1]

#Stopbutton
stoppushbutton=configuration['Gpios']['stopbutton_music_AIY_pushbutton'][0]
GPIO.setup(stoppushbutton, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(stoppushbutton,GPIO.FALLING)

if (audiosetup=='AIY'):
    GPIO.setup(aiyindicator, GPIO.OUT)
    led=GPIO.PWM(aiyindicator,1)
    led.start(0)
    print('Initializing GPIO '+str(aiyindicator)+' for assistant activity indication')
elif (audiosetup=='GEN'):
    GPIO.setup(listening, GPIO.OUT)
    GPIO.setup(speaking, GPIO.OUT)
    GPIO.output(listening, GPIO.LOW)
    GPIO.output(speaking, GPIO.LOW)
    print('Initializing GPIOs '+str(liseningindicator)+' and '+str(speakingindicator)+' for assistant activity indication')


def assistantindicator(activity):
    activity=activity.lower()
    if activity=='listening':
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.LOW)
            GPIO.output(listeningindicator,GPIO.HIGH)
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(75)
    elif activity=='speaking':
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.HIGH)
            GPIO.output(listeningindicator,GPIO.LOW)
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(50)
    elif (activity=='off' or activity=='unmute'):
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.LOW)
            GPIO.output(listeningindicator,GPIO.LOW)
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(0)
    elif (activity=='on' or activity=='mute'):
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.HIGH)
            GPIO.output(listeningindicator,GPIO.HIGH)
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(100)
