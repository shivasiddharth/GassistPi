#!/usr/bin/env python

# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import print_function
import RPi.GPIO as GPIO
import argparse
import os.path
import os
import json
import subprocess
import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from actions import Action
from actions import YouTube
from actions import stop

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Indicator Pins
GPIO.setup(05,GPIO.OUT)
GPIO.setup(06,GPIO.OUT)
GPIO.output(05, GPIO.LOW)
GPIO.output(06, GPIO.LOW)


def process_event(event):
    """Pretty prints events.

    Prints all events that occur with two spaces between each new
    conversation and a single space between turns of a conversation.

    Args:
        event(event.Event): The current event to process.
    """
    if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Fb.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        GPIO.output(05,GPIO.HIGH)

    if (event.type == EventType.ON_RESPONDING_STARTED and event.args and not event.args['is_error_response']):
       GPIO.output(05,GPIO.LOW)
       GPIO.output(06,GPIO.HIGH)

    if event.type == EventType.ON_RESPONDING_FINISHED:
       GPIO.output(06,GPIO.LOW)
       GPIO.output(05,GPIO.HIGH)


    print(event)

    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and not event.args['with_follow_on_turn']):
        GPIO.output(05,GPIO.LOW)
        print()


def main():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--credentials', type=existing_file,
                        metavar='OAUTH2_CREDENTIALS_FILE',
                        default=os.path.join(
                            os.path.expanduser('/home/pi/.config'),
                            'google-oauthlib-tool',
                            'credentials.json'
                        ),
                        help='Path to store and read OAuth2 credentials')
    args = parser.parse_args()
    with open(args.credentials, 'r') as f:
        credentials = google.oauth2.credentials.Credentials(token=None,
                                                            **json.load(f))

    with Assistant(credentials) as assistant:
        subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Startup.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for event in assistant.start():
            process_event(event)
            usrcmd=event.args
            if 'trigger'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                Action(str(usrcmd).lower())
            if 'play'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                YouTube(str(usrcmd).lower())
            if 'stop'.lower() in str(usrcmd).lower():
                stop()
            if 'tune into'.lower() in str(usrcmd).lower():
                radio(str(usrcmd).lower())

if __name__ == '__main__':
    main()
