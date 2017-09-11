import snowboydecoder
import sys
import signal
import RPi.GPIO as GPIO
import time
import os

path = '/home/pi/GassistPi/trigger.txt'
# Demo code for listening two hotwords at the same time
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
interrupted = False
GPIO.setup(22,GPIO.OUT)
GPIO.output(22,GPIO.LOW)
models = ['/home/pi/GassistPi/snowboy/resources/alexa.umdl', '/home/pi/GassistPi/snowboy/resources/snowboy.umdl']

def signal_handler(signal, frame):
    global interrupted
    interrupted = True



def interrupt_callback():
    global interrupted
    return interrupted

##if len(sys.argv) != 3:
##    print("Error: need to specify 2 model names")
##    print("Usage: python demo.py 1st.model 2nd.model")
##    sys.exit(-1)


def detected():


    trig= open(path,'w')
    trig.write('1')
    trig.close()
    GPIO.output(22,GPIO.HIGH)
    time.sleep(.05)
    GPIO.output(22,GPIO.LOW)
##    snowboydecoder.play_audio_file(snowboydecoder.DETECT_DING)



# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

sensitivity = [0.5]*len(models)
detector = snowboydecoder.HotwordDetector(models, sensitivity=sensitivity)
callbacks = [detected, detected]
print('Listening... Press Ctrl+C to exit')

# main loop
# make sure you have the same numbers of callbacks and models
detector.start(detected_callback=callbacks,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()
