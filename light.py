import RPi.GPIO as GPIO
import time

class Light(object):
    def __init__(self, port):
        self.port = port
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.port, GPIO.OUT)
        self.on_state = GPIO.HIGH
        self.off_state = not self.on_state

    def set_on(self):
        GPIO.output(self.port, self.on_state)

    def set_off(self):
        GPIO.output(self.port, self.off_state)

    def is_on(self):
        return GPIO.input(self.port) == self.on_state

    def is_off(self):
        return GPIO.input(self.port) == self.off_state

    def toggle(self):
        if self.is_on():
            self.set_off()
        else:
            self.set_on()

    def blink(self, t=0.3):
        self.set_off()
        self.set_on()
        time.sleep(t)
        self.set_off()

if __name__ == "__main__":
    light = Light(17)
    while True:
        light.blink()
        time.sleep(0.7)
