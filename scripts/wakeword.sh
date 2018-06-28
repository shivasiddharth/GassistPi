#!/bin/bash
cd GassistPi/Snowboy/
sleep 150
aplay /home/pi/GassistPi/Snowboy/resources/ding.wav
sudo python trigger.py
