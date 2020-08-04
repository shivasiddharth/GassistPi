#!/usr/bin/env python

try:
    import RPi.GPIO as GPIO
except Exception as e:
    GPIO = None
import time
import os
from actions import configuration
import apa102
import time
import threading
import numpy
from gpiozero import LED
try:
    import queue as Queue
except ImportError:
    import Queue as Queue


audiosetup=''

USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))

if os.path.isfile("{}/audiosetup".format(USER_PATH)):
    with open('{}/audiosetup'.format(USER_PATH)) as f:
        detected_audio_setup = f.readline().rstrip()
        print(detected_audio_setup)
        if (detected_audio_setup=='AIY-HAT' or detected_audio_setup=='CUSTOM-VOICE-HAT'):
            audiosetup='AIY'
        elif (detected_audio_setup=='USB-DAC' or detected_audio_setup=='USB-MIC-HDMI' or detected_audio_setup=='USB-MIC-JACK'):
            audiosetup='GEN'
        elif (detected_audio_setup=='Respeaker-4-Mic'):
            audiosetup='R4M'
        elif (detected_audio_setup=='Respeaker-2-Mic'):
            audiosetup='R2M'
        else:
            audiosetup='GEN'
else:
    audiosetup='GEN'

if configuration['IR']['IR_Control']=='Enabled':
    ircontrol=True
else:
    ircontrol=False

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Indicators
aiyindicator=configuration['Gpios']['AIY_indicator'][0]
listeningindicator=configuration['Gpios']['assistant_indicators'][0]
speakingindicator=configuration['Gpios']['assistant_indicators'][1]

#Stopbutton
stoppushbutton=configuration['Gpios']['stopbutton_music_AIY_pushbutton'][0]
GPIO.setup(stoppushbutton, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(stoppushbutton,GPIO.FALLING)

#IR receiver
if ircontrol:
    irreceiver=configuration['Gpios']['ir'][0]
    GPIO.setup(irreceiver, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
else:
    irreceiver=None

if (audiosetup=='AIY'):
    GPIO.setup(aiyindicator, GPIO.OUT)
    led=GPIO.PWM(aiyindicator,1)
    led.start(0)
    print('Initializing GPIO '+str(aiyindicator)+' for assistant activity indication')
elif (audiosetup=='GEN'):
    GPIO.setup(listeningindicator, GPIO.OUT)
    GPIO.setup(speakingindicator, GPIO.OUT)
    GPIO.output(listeningindicator, GPIO.LOW)
    GPIO.output(speakingindicator, GPIO.LOW)
    print('Initializing GPIOs '+str(listeningindicator)+' and '+str(speakingindicator)+' for assistant activity indication')

class GoogleHomeLedPattern(object):
    def __init__(self, show=None):
        self.basis = numpy.array([0] * 4 * 12)
        self.basis[0 * 4 + 1] = 2
        self.basis[3 * 4 + 1] = 1
        self.basis[3 * 4 + 2] = 1
        self.basis[6 * 4 + 2] = 2
        self.basis[9 * 4 + 3] = 2
        self.pixels = self.basis * 24

        if not show or not callable(show):
            def dummy(data):
                pass
            show = dummy
        self.show = show
        self.stop = False

    def wakeup(self, direction=0):
        position = int((direction + 15) / 30) % 12

        basis = numpy.roll(self.basis, position * 4)
        for i in range(1, 25):
            pixels = basis * i
            self.show(pixels)
            time.sleep(0.005)
        pixels =  numpy.roll(pixels, 4)
        self.show(pixels)
        time.sleep(0.1)
        for i in range(2):
            new_pixels = numpy.roll(pixels, 4)
            self.show(new_pixels * 0.5 + pixels)
            pixels = new_pixels
            time.sleep(0.1)
        self.show(pixels)
        self.pixels = pixels

    def listen(self):
        pixels = self.pixels
        for i in range(1, 25):
            self.show(pixels * i / 24)
            time.sleep(0.01)

    def think(self):
        pixels = self.pixels
        while not self.stop:
            pixels = numpy.roll(pixels, 4)
            self.show(pixels)
            time.sleep(0.2)
        t = 0.1
        for i in range(0, 5):
            pixels = numpy.roll(pixels, 4)
            self.show(pixels * (4 - i) / 4)
            time.sleep(t)
            t /= 2
        self.pixels = pixels

    def speak(self):
        pixels = self.pixels
        step = 1
        brightness = 5
        while not self.stop:
            self.show(pixels * brightness / 24)
            time.sleep(0.02)
            if brightness <= 5:
                step = 1
                time.sleep(0.4)
            elif brightness >= 24:
                step = -1
                time.sleep(0.4)
            brightness += step

    def off(self):
        self.show([0] * 4 * 12)

    def red(self):
        self.show([0,1,0,0] * 12)


class Pixels4mic:
    PIXELS_N = 12
    def __init__(self, pattern=GoogleHomeLedPattern):
        self.pattern = pattern(show=self.show)
        self.dev = apa102.APA102(num_led=self.PIXELS_N)
        self.power = LED(5)
        self.power.on()
        self.queue = Queue.Queue()
        self.t4 = threading.Thread(target=self._run)
        self.t4.daemon = True
        self.t4.start()
        self.last_direction = None

    def wakeup(self, direction=0):
        self.last_direction = direction
        def f():
            self.pattern.wakeup(direction)
        self.put(f)

    def listen(self):
        if self.last_direction:
            def f():
                self.pattern.wakeup(self.last_direction)
            self.put(f)
        else:
            self.put(self.pattern.listen)

    def think(self):
        self.put(self.pattern.think)

    def speak(self):
        self.put(self.pattern.speak)

    def off(self):
        self.put(self.pattern.off)

    def put(self, func):
        self.pattern.stop = True
        self.queue.put(func)

    def _run(self):
        while True:
            func = self.queue.get()
            self.pattern.stop = False
            func()

    def show(self, data):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(i, int(data[4*i + 1]), int(data[4*i + 2]), int(data[4*i + 3]))
        self.dev.show()

    def mute(self):
        self.put(self.pattern.red)

class Pixels2mic:
    PIXELS_N = 3
    def __init__(self):
        self.basis = [0] * 3 * self.PIXELS_N
        self.basis[0] = 1
        self.basis[4] = 1
        self.basis[8] = 2
        self.colors = [0] * 3 * self.PIXELS_N
        self.dev = apa102.APA102(num_led=self.PIXELS_N)
        self.next = threading.Event()
        self.queue = Queue.Queue()
        self.t5 = threading.Thread(target=self._run)
        self.t5.daemon = True
        self.t5.start()

    def wakeup(self, direction=0):
        def f():
            self._wakeup(direction)
        self.next.set()
        self.queue.put(f)

    def listen(self):
        self.next.set()
        self.queue.put(self._listen)

    def think(self):
        self.next.set()
        self.queue.put(self._think)

    def speak(self):
        self.next.set()
        self.queue.put(self._speak)

    def off(self):
        self.next.set()
        self.queue.put(self._off)

    def _run(self):
        while True:
            func = self.queue.get()
            func()

    def _wakeup(self, direction=0):
        for i in range(1, 25):
            colors = [i * v for v in self.basis]
            self.write(colors)
            time.sleep(0.01)
        self.colors = colors

    def _listen(self):
        for i in range(1, 25):
            colors = [i * v for v in self.basis]
            self.write(colors)
            time.sleep(0.01)
        self.colors = colors

    def _think(self):
        colors = self.colors
        self.next.clear()
        while not self.next.is_set():
            colors = colors[3:] + colors[:3]
            self.write(colors)
            time.sleep(0.2)
        t = 0.1
        for i in range(0, 5):
            colors = colors[3:] + colors[:3]
            self.write([(v * (4 - i) / 4) for v in colors])
            time.sleep(t)
            t /= 2
        # time.sleep(0.5)
        self.colors = colors

    def _speak(self):
        colors = self.colors
        self.next.clear()
        while not self.next.is_set():
            for i in range(5, 25):
                self.write([(v * i / 24) for v in colors])
                time.sleep(0.01)
            time.sleep(0.3)
            for i in range(24, 4, -1):
                self.write([(v * i / 24) for v in colors])
                time.sleep(0.01)
            time.sleep(0.3)
        self._off()

    def _off(self):
        self.write([0] * 3 * self.PIXELS_N)

    def write(self, colors):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(i, int(colors[3*i]), int(colors[3*i + 1]), int(colors[3*i + 2]))
        self.dev.show()

    def mute(self):
        self.write([1,0,0] * self.PIXELS_N)

if audiosetup=='R2M':
    pixels=Pixels2mic()
elif audiosetup=='R4M':
    pixels=Pixels4mic()

def assistantindicator(activity):
    activity=activity.lower()
    if activity=='listening':
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.LOW)
            GPIO.output(listeningindicator,GPIO.HIGH)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.listen()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(75)
    elif activity=='speaking':
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.HIGH)
            GPIO.output(listeningindicator,GPIO.LOW)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.speak()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(50)
    elif (activity=='off' or activity=='unmute'):
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.LOW)
            GPIO.output(listeningindicator,GPIO.LOW)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.off()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(0)
    elif (activity=='on' or activity=='mute'):
        if (audiosetup=='GEN'):
            GPIO.output(speakingindicator,GPIO.HIGH)
            GPIO.output(listeningindicator,GPIO.HIGH)
        elif (audiosetup=='R2M' or audiosetup=='R4M'):
            pixels.mute()
        elif (audiosetup=='AIY'):
            led.ChangeDutyCycle(100)
