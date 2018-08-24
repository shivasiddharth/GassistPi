import RPi.GPIO as GPIO
import time
import os
from time import sleep

sw_in = 26
LED = 18
file = open('/home/pi/PiraCast/status','r+w')
f = file.read()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(sw_in,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(sw_in,GPIO.FALLING)
GPIO.setup(LED,GPIO.OUT)
GPIO.setwarnings(False)

def flashLED(speed, time):
        for x in range(0, time):
                GPIO.output(LED, GPIO.LOW)
                sleep(speed)
                GPIO.output(LED, GPIO.HIGH)
                sleep(speed)

def triplePress():
        print ("Pressed Thrice So! Switching to Piracast!")
	if f[0] == "1":
	   os.system("sh /home/pi/runme_piracast.sh")
	elif f[0] == "0":
	   os.system("echo 1 > /home/pi/PiraCast/status")
	   os.system("sh /home/pi/PiraCast/switch_to_piracast")
        flashLED(0.5, 3)

def doublePress():
        print ("Pressed Twice So! Kodi! Here We come! :D")
        if f[0] == "1":
	   os.system("echo 0 > /home/pi/PiraCast/status")
	   os.system("sh /home/pi/PiraCast/switch_to_normal")
        elif f[0] == "0" :
	   os.system("kodi-standalone")
        flashLED(0.5, 2)

def singlePress():
        print ("Pressed Once So! Home Automation!")
        if f[0] == "1":
          os.system("echo 0 > /home/pi/PiraCast/status")
          os.system("sh /home/pi/PiraCast/switch_to_normal")
	  print("Changing file and rebooting")
        elif f[0] == "0" :
	  print("Suitable situation found ! so starting")
	  os.system("./usr/local/bin/node /home/pi/HomeAutomation/pi-node-relay/app.js | ./home/pi/HomeAutomation/pi-node-relay/ngrok 3700")
        flashLED(0.5, 1)


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

file.close()
