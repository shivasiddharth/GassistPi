import RPi.GPIO as GPIO
import time
import os
from time import sleep

sw_in = 26
LED = 18
GPIO.setmode(GPIO.BOARD)
GPIO.setup(sw_in,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(sw_in,GPIO.FALLING)
GPIO.setup(LED,GPIO.OUT)
GPIO.setwarnings(False)


def triplePress():
        print ("Pressed Thrice")	

def doublePress():
        print ("Pressed Twice")        

def singlePress():
        print ("Pressed Once")      


while True:
   if GPIO.event_detected(sw_in):
      GPIO.remove_event_detect(sw_in)
      now = time.time()
      count = 1
      GPIO.add_event_detect(sw_in,GPIO.RISING)
      while time.time() < now + 1: # 1 second period
         if GPIO.event_detected(sw_in):
            count +=1
            time.sleep(.25) # debounce time
      #print count
      #performing required task!
      if count == 2:
	singlePress()
	GPIO.remove_event_detect(sw_in)
        GPIO.add_event_detect(sw_in,GPIO.FALLING)
	#break
      elif count == 3:
	doublePress()
	GPIO.remove_event_detect(sw_in)
	GPIO.add_event_detect(sw_in,GPIO.FALLING)
	#break
      elif count == 4:
	triplePress()
        GPIO.remove_event_detect(sw_in)
        GPIO.add_event_detect(sw_in,GPIO.FALLING)
	#break
