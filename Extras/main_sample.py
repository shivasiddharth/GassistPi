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

from kodijson import Kodi, PLAYER_VIDEO
import RPi.GPIO as GPIO
import argparse
import os.path
import os
import json
import subprocess
import google.auth.transport.requests
import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
DEVICE_API_URL = 'https://embeddedassistant.googleapis.com/v1alpha2'
from actions import Action
from actions import YouTube
from actions import stop
from actions import radio
from actions import ESP
from actions import track
from actions import feed
from actions import kodiactions
from actions import mutevolstatus
import blinkt
import sys
import math
from actions import custom_action_keyword

#Login with default kodi/kodi credentials
#kodi = Kodi("http://localhost:8080/jsonrpc")

#Login with custom credentials
# Kodi("http://IP-ADDRESS-OF-KODI:8080/jsonrpc", "username", "password")
kodi = Kodi("http://192.168.1.15:8080/jsonrpc", "kodi", "kodi")


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Indicator Pins
GPIO.setup(25, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.setup(6, GPIO.OUT)
GPIO.output(5, GPIO.LOW)
GPIO.output(6, GPIO.LOW)
led=GPIO.PWM(25,1)
led.start(0)


def colourconv(x):
    accesscolour=int(x)
    R=math.floor(accesscolour/65536)
    G=math.floor((accesscolour-(R*65536))/256)
    B=accesscolour-(R*65536)-(G*256)

    return R,G,B


def process_device_actions(event, device_id):
    if 'inputs' in event.args:
        for i in event.args['inputs']:
            if i['intent'] == 'action.devices.EXECUTE':
                for c in i['payload']['commands']:
                    for device in c['devices']:
                        if device['id'] == device_id:
                            if 'execution' in c:
                                for e in c['execution']:
                                    if e['params']:
                                        yield e['command'], e['params']
                                    else:
                                        yield e['command'], None


def process_event(event, device_id):
    """Pretty prints events.
    Prints all events that occur with two spaces between each new
    conversation and a single space between turns of a conversation.
    Args:
        event(event.Event): The current event to process.
    """
    if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Fb.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #Uncomment the following after starting the Kodi
        #status=mutevolstatus()
        #vollevel=status[1]
        #with open('/home/pi/.volume.json', 'w') as f:
               #json.dump(vollevel, f)
        #kodi.Application.SetVolume({"volume": 0})
        GPIO.output(5,GPIO.HIGH)
        led.ChangeDutyCycle(100)
        print()
    print(event)

    if (event.type == EventType.ON_RESPONDING_STARTED and event.args and not event.args['is_error_response']):
       GPIO.output(5,GPIO.LOW)
       GPIO.output(6,GPIO.HIGH)
       led.ChangeDutyCycle(50)

    if event.type == EventType.ON_RESPONDING_FINISHED:
       GPIO.output(6,GPIO.LOW)
       GPIO.output(5,GPIO.HIGH)
       led.ChangeDutyCycle(100)

    print(event)

    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and not event.args['with_follow_on_turn']):
        GPIO.output(5,GPIO.LOW)
        led.ChangeDutyCycle(0)
        #Uncomment the following after starting the Kodi
        #with open('/home/pi/.volume.json', 'r') as f:
               #vollevel = json.load(f)
               #kodi.Application.SetVolume({"volume": vollevel})
        print()

    if event.type == EventType.ON_DEVICE_ACTION:
        for command, params in process_device_actions(event, device_id):
            print('Do command', command, 'with params', str(params))
            if command=='action.devices.commands.OnOff':
                if params['on']:
                    blinkt.set_all(255, 255, 255,brightness=0.05)
                    blinkt.show()
                else:
                    blinkt.clear()
                    blinkt.show()
            if command=='action.devices.commands.ColorAbsolute':
                r,g,b=colourconv(params['color']['spectrumRGB'])
                print(r,g,b)
                blinkt.set_all(r,g,b)
                blinkt.show()
            if command=='action.devices.commands.BrightnessAbsolute':
                bright=(params['brightness'])/100
                blinkt.set_brightness(bright)
                blinkt.show()


def register_device(project_id, credentials, device_model_id, device_id):
    """Register the device if needed.
    Registers a new assistant device if an instance with the given id
    does not already exists for this model.
    Args:
       project_id(str): The project ID used to register device instance.
       credentials(google.oauth2.credentials.Credentials): The Google
                OAuth2 credentials of the user to associate the device
                instance with.
       device_model_id: The registered device model ID.
       device_id: The device ID of the new instance.
    """
    base_url = '/'.join([DEVICE_API_URL, 'projects', project_id, 'devices'])
    device_url = '/'.join([base_url, device_id])
    session = google.auth.transport.requests.AuthorizedSession(credentials)
    r = session.get(device_url)
    print(device_url, r.status_code)
    if r.status_code == 404:
        print('Registering....', end='', flush=True)
        r = session.post(base_url, data=json.dumps({
            'id': device_id,
            'model_id': device_model_id,
            'client_type': 'SDK_LIBRARY'
        }))
        if r.status_code != 200:
            raise Exception('failed to register device: ' + r.text)
        print('\rDevice registered.')


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--credentials', type=existing_file,
                        metavar='OAUTH2_CREDENTIALS_FILE',
                        default=os.path.join(
                            os.path.expanduser('~/.config'),
                            'google-oauthlib-tool',
                            'credentials.json'
                        ),
                        help='Path to store and read OAuth2 credentials')
    parser.add_argument('--device_model_id', type=str,
                        metavar='DEVICE_MODEL_ID', required=True,
                        help='The device model ID registered with Google.')
    parser.add_argument('--project_id', type=str,
                        metavar='PROJECT_ID', required=False,
                        help='The project ID used to register device '
                        + 'instances.')
    args = parser.parse_args()
    with open(args.credentials, 'r') as f:
        credentials = google.oauth2.credentials.Credentials(token=None,
                                                            **json.load(f))
    with Assistant(credentials, args.device_model_id) as assistant:
        subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Startup.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        events = assistant.start()
        print('device_model_id:', args.device_model_id + '\n' +
              'device_id:', assistant.device_id + '\n')
        if args.project_id:
            register_device(args.project_id, credentials,
                            args.device_model_id, assistant.device_id)
        for event in events:
            process_event(event, assistant.device_id)
            usrcmd=event.args

            if (custom_action_keyword['Keywords']['Pi_GPIO_control'][0]).lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                Action(str(usrcmd).lower())
            if (custom_action_keyword['Keywords']['YouTube_music_stream'][0]).lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                YouTube(str(usrcmd).lower())
            if (custom_action_keyword['Keywords']['Stop_music'][0]).lower() in str(usrcmd).lower():
                stop()
            if 'tune into'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                radio(str(usrcmd).lower())
            if (custom_action_keyword['Keywords']['ESP_control'][0]).lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                ESP(str(usrcmd).lower())
            if (custom_action_keyword['Keywords']['Parcel_tracking'][0]).lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                track()
            if 'news'.lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['RSS'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['RSS'][1]).lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                feed(str(usrcmd).lower())
            if (custom_action_keyword['Keywords']['Kodi_actions'][0]).lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                kodiactions(str(usrcmd).lower())


if __name__ == '__main__':
    main()
