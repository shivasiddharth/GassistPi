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
from kodijson import Kodi, PLAYER_VIDEO
import RPi.GPIO as GPIO
import argparse
import json
import os.path
import pathlib2 as pathlib
import os
import subprocess
import re
import psutil
import logging
import time
import random
import snowboydecoder
import sys
import signal
import requests
import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from google.assistant.library.device_helpers import register_device
from actions import say
from actions import Action
from actions import YouTube_No_Autoplay
from actions import YouTube_Autoplay
from actions import stop
from actions import radio
from actions import ESP
from actions import track
from actions import feed
from actions import kodiactions
from actions import mutevolstatus
from actions import gmusicselect
from actions import refreshlists
from actions import chromecast_play_video
from actions import chromecast_control
from actions import kickstarter_tracker
from actions import getrecipe
from actions import hue_control
from actions import vlcplayer
from actions import spotify_playlist_select
from actions import configuration
from actions import custom_action_keyword
from threading import Thread
from indicator import assistantindicator
from indicator import stoppushbutton
from pathlib import Path
from actions import Domoticz_Device_Control
from actions import domoticz_control
from actions import domoticz_devices

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


WARNING_NOT_REGISTERED = """
    This device is not registered. This means you will not be able to use
    Device Actions or see your device in Assistant Settings. In order to
    register this device follow instructions at:

    https://developers.google.com/assistant/sdk/guides/library/python/embed/register-device
"""

logging.basicConfig(filename='/tmp/GassistPi.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)



#Login with default kodi/kodi credentials
#kodi = Kodi("http://localhost:8080/jsonrpc")

#Login with custom credentials
# Kodi("http://IP-ADDRESS-OF-KODI:8080/jsonrpc", "username", "password")
kodiurl=("http://"+str(configuration['Kodi']['ip'])+":"+str(configuration['Kodi']['port'])+"/jsonrpc")
kodi = Kodi(kodiurl, configuration['Kodi']['username'], configuration['Kodi']['password'])



mutestopbutton=True

#Sonoff-Tasmota Declarations
#Make sure that the device name assigned here does not overlap any of your smart device names in the google home app
tasmota_devicelist=configuration['Tasmota_devicelist']['friendly-names']
tasmota_deviceip=configuration['Tasmota_devicelist']['ipaddresses']
tasmota_deviceportid=configuration['Tasmota_devicelist']['portID']

#Magic Mirror Remote Control Declarations
mmmip=configuration['Mmmip']

# Check if VLC is paused
def checkvlcpaused():
    state=vlcplayer.state()
    if str(state)=="State.Paused":
        currentstate=True
    else:
        currentstate=False
    return currentstate



#Function to control Sonoff Tasmota Devices
def tasmota_control(phrase,devname,devip,devportid):
    try:
        if 'on' in phrase:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power"+devportid+"%20on")
            say("Tunring on "+devname)
        elif 'off' in phrase:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power"+devportid+"%20off")
            say("Tunring off "+devname)
    except requests.exceptions.ConnectionError:
        say("Device not online")

#Check if custom wakeword has been enabled
if configuration['Wakewords']['Custom_Wakeword']=='Enabled':
    custom_wakeword=True
else:
    custom_wakeword=False

models=configuration['Wakewords']['Custom_wakeword_models']

#Custom Conversation
numques=len(configuration['Conversation']['question'])
numans=len(configuration['Conversation']['answer'])

class Myassistant():

    def __init__(self):
        self.interrupted=False
        self.can_start_conversation=False
        self.assistant=None
        self.sensitivity = [0.5]*len(models)
        self.callbacks = [self.detected]*len(models)
        self.detector = snowboydecoder.HotwordDetector(models, sensitivity=self.sensitivity)
        self.t1 = Thread(target=self.start_detector)
        self.t2 = Thread(target=self.pushbutton)

    def signal_handler(self,signal, frame):
        self.interrupted = True

    def interrupt_callback(self,):
        return self.interrupted

    def buttonsinglepress(self):
        if os.path.isfile("/home/pi/.mute"):
            os.system("sudo rm /home/pi/.mute")
            assistantindicator('unmute')
            if configuration['Wakewords']['Ok_Google']=='Disabled':
                self.assistant.set_mic_mute(True)
            else:
                self.assistant.set_mic_mute(False)
            # if custom_wakeword:
            #     self.t1.start()
            subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Mic-On.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Turning on the microphone")
        else:
            open('/home/pi/.mute', 'a').close()
            assistantindicator('mute')
            self.assistant.set_mic_mute(True)
            # if custom_wakeword:
            #     self.thread_end(t1)
            subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Mic-Off.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Turning off the microphone")

    def buttondoublepress(self):
        print('Stopped')
        stop()

    def buttontriplepress(self):
        print("Create your own action for button triple press")

    def pushbutton(self):
        while mutestopbutton:
            if GPIO.event_detected(stoppushbutton):
                GPIO.remove_event_detect(stoppushbutton)
                now = time.time()
                count = 1
                GPIO.add_event_detect(stoppushbutton,GPIO.RISING)
                while time.time() < now + 1:
                     if GPIO.event_detected(stoppushbutton):
                         count +=1
                         time.sleep(.25)
                if count == 2:
                    self.buttonsinglepress()
                    GPIO.remove_event_detect(stoppushbutton)
                    GPIO.add_event_detect(stoppushbutton,GPIO.FALLING)
                elif count == 3:
                    self.buttondoublepress()
                    GPIO.remove_event_detect(stoppushbutton)
                    GPIO.add_event_detect(stoppushbutton,GPIO.FALLING)
                elif count == 4:
                    self.buttontriplepress()
                    GPIO.remove_event_detect(stoppushbutton)
                    GPIO.add_event_detect(stoppushbutton,GPIO.FALLING)

    def process_device_actions(self,event, device_id):
        if 'inputs' in event.args:
            for i in event.args['inputs']:
                if i['intent'] == 'action.devices.EXECUTE':
                    for c in i['payload']['commands']:
                        for device in c['devices']:
                            if device['id'] == device_id:
                                if 'execution' in c:
                                    for e in c['execution']:
                                        if 'params' in e:
                                            yield e['command'], e['params']
                                        else:
                                            yield e['command'], None


    def process_event(self,event):
        """Pretty prints events.
        Prints all events that occur with two spaces between each new
        conversation and a single space between turns of a conversation.
        Args:
            event(event.Event): The current event to process.
        """
        print(event)
        if event.type == EventType.ON_START_FINISHED:
            self.can_start_conversation = True
            self.t2.start()
            if os.path.isfile("/home/pi/.mute"):
                assistantindicator('mute')
            if (configuration['Wakewords']['Ok_Google']=='Disabled' or os.path.isfile("/home/pi/.mute")):
                self.assistant.set_mic_mute(True)
            if custom_wakeword:
                self.t1.start()

        if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            self.can_start_conversation = False
            subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Fb.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #Uncomment the following after starting the Kodi
            #status=mutevolstatus()
            #vollevel=status[1]
            #with open('/home/pi/.volume.json', 'w') as f:
                   #json.dump(vollevel, f)
            #kodi.Application.SetVolume({"volume": 0})
            assistantindicator('listening')
            if vlcplayer.is_vlc_playing():
                if os.path.isfile("/home/pi/.mediavolume.json"):
                    vlcplayer.set_vlc_volume(15)
                else:
                    currentvolume=vlcplayer.get_vlc_volume()
                    print(currentvolume)
                    with open('/home/pi/.mediavolume.json', 'w') as vol:
                       json.dump(currentvolume, vol)
                    vlcplayer.set_vlc_volume(15)
            print()

        if (event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT or event.type == EventType.ON_NO_RESPONSE):
            self.can_start_conversation = True
            assistantindicator('off')
            #Uncomment the following after starting the Kodi
            #with open('/home/pi/.volume.json', 'r') as f:
                   #vollevel = json.load(f)
                   #kodi.Application.SetVolume({"volume": vollevel})
            if (configuration['Wakewords']['Ok_Google']=='Disabled' or os.path.isfile("/home/pi/.mute")):
                  self.assistant.set_mic_mute(True)
            if os.path.isfile("/home/pi/.mute"):
                assistantindicator('mute')
            if vlcplayer.is_vlc_playing():
                with open('/home/pi/.mediavolume.json', 'r') as vol:
                    oldvolume = json.load(vol)
                vlcplayer.set_vlc_volume(int(oldvolume))

        if (event.type == EventType.ON_RESPONDING_STARTED and event.args and not event.args['is_error_response']):
            assistantindicator('speaking')

        if event.type == EventType.ON_RESPONDING_FINISHED:
            assistantindicator('off')

        if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
            assistantindicator('off')

        print(event)

        if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
                event.args and not event.args['with_follow_on_turn']):
            self.can_start_conversation = True
            assistantindicator('off')
            if (configuration['Wakewords']['Ok_Google']=='Disabled' or os.path.isfile("/home/pi/.mute")):
                self.assistant.set_mic_mute(True)
            if os.path.isfile("/home/pi/.mute"):
                assistantindicator('mute')
            #Uncomment the following after starting the Kodi
            #with open('/home/pi/.volume.json', 'r') as f:
                   #vollevel = json.load(f)
                   #kodi.Application.SetVolume({"volume": vollevel})
            if vlcplayer.is_vlc_playing():
                with open('/home/pi/.mediavolume.json', 'r') as vol:
                    oldvolume= json.load(vol)
                vlcplayer.set_vlc_volume(int(oldvolume))
            print()

        if event.type == EventType.ON_DEVICE_ACTION:
            for command, params in event.actions:
                print('Do command', command, 'with params', str(params))


    def register_device(self,project_id, credentials, device_model_id, device_id):
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
            print('Registering....')
            r = session.post(base_url, data=json.dumps({
                'id': device_id,
                'model_id': device_model_id,
                'client_type': 'SDK_LIBRARY'
            }))
            if r.status_code != 200:
                raise Exception('failed to register device: ' + r.text)
            print('\rDevice registered.')


    def detected(self):
        if self.can_start_conversation == True:
            self.assistant.set_mic_mute(False)
            self.assistant.start_conversation()
            print('Assistant is listening....')

    def start_detector(self):
        self.detector.start(detected_callback=self.callbacks,
            interrupt_check=self.interrupt_callback,
            sleep_time=0.03)

    def main(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--device-model-id', '--device_model_id', type=str,
                            metavar='DEVICE_MODEL_ID', required=False,
                            help='the device model ID registered with Google')
        parser.add_argument('--project-id', '--project_id', type=str,
                            metavar='PROJECT_ID', required=False,
                            help='the project ID used to register this device')
        parser.add_argument('--device-config', type=str,
                            metavar='DEVICE_CONFIG_FILE',
                            default=os.path.join(
                                os.path.expanduser('~/.config'),
                                'googlesamples-assistant',
                                'device_config_library.json'
                            ),
                            help='path to store and read device configuration')
        parser.add_argument('--credentials', type=existing_file,
                            metavar='OAUTH2_CREDENTIALS_FILE',
                            default=os.path.join(
                                os.path.expanduser('~/.config'),
                                'google-oauthlib-tool',
                                'credentials.json'
                            ),
                            help='path to store and read OAuth2 credentials')
        parser.add_argument('-v', '--version', action='version',
                            version='%(prog)s ' + Assistant.__version_str__())

        args = parser.parse_args()
        with open(args.credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))

        device_model_id = None
        last_device_id = None
        try:
            with open(args.device_config) as f:
                device_config = json.load(f)
                device_model_id = device_config['model_id']
                last_device_id = device_config.get('last_device_id', None)
        except FileNotFoundError:
            pass

        if not args.device_model_id and not device_model_id:
            raise Exception('Missing --device-model-id option')

        # Re-register if "device_model_id" is given by the user and it differs
        # from what we previously registered with.
        should_register = (
            args.device_model_id and args.device_model_id != device_model_id)

        device_model_id = args.device_model_id or device_model_id
        with Assistant(credentials, device_model_id) as assistant:
            self.assistant = assistant
            subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Startup.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            events = assistant.start()
            device_id = assistant.device_id
            print('device_model_id:', device_model_id)
            print('device_id:', device_id + '\n')

            # Re-register if "device_id" is different from the last "device_id":
            if should_register or (device_id != last_device_id):
                if args.project_id:
                    register_device(args.project_id, credentials,
                                    device_model_id, device_id)
                    pathlib.Path(os.path.dirname(args.device_config)).mkdir(
                        exist_ok=True)
                    with open(args.device_config, 'w') as f:
                        json.dump({
                            'last_device_id': device_id,
                            'model_id': device_model_id,
                        }, f)
                else:
                    print(WARNING_NOT_REGISTERED)

            for event in events:
                self.process_event(event)
                usrcmd=event.args
                with open('/home/pi/GassistPi/src/diyHue/config.json', 'r') as config:
                     hueconfig = json.load(config)
                for i in range(1,len(hueconfig['lights'])+1):
                    try:
                        if str(hueconfig['lights'][str(i)]['name']).lower() in str(usrcmd).lower():
                            assistant.stop_conversation()
                            hue_control(str(usrcmd).lower(),str(i),str(hueconfig['lights_address'][str(i)]['ip']))
                            break
                    except Keyerror:
                        say('Unable to help, please check your config file')

                for num, name in enumerate(tasmota_devicelist):
                    if name.lower() in str(usrcmd).lower():
                        assistant.stop_conversation()
                        tasmota_control(str(usrcmd).lower(), name.lower(),tasmota_deviceip[num],tasmota_deviceportid[num])
                        break
                for i in range(1,numques+1):
                    try:
                        if str(configuration['Conversation']['question'][i][0]).lower() in str(usrcmd).lower():
                            assistant.stop_conversation()
                            selectedans=random.sample(configuration['Conversation']['answer'][i],1)
                            say(selectedans[0])
                            break
                    except Keyerror:
                        say('Please check if the number of questions matches the number of answers')

                if Domoticz_Device_Control==True and len(domoticz_devices['result'])>0:
                    for i in range(0,len(domoticz_devices['result'])):
                        if str(domoticz_devices['result'][i]['HardwareName']).lower() in str(usrcmd).lower():
                            assistant.stop_conversation()
                            domoticz_control(i,str(usrcmd).lower(),domoticz_devices['result'][i]['idx'],domoticz_devices['result'][i]['HardwareName'])
                            break

                if (custom_action_keyword['Keywords']['Magic_mirror'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    try:
                        mmmcommand=str(usrcmd).lower()
                        if 'weather'.lower() in mmmcommand:
                            if 'show'.lower() in mmmcommand:
                                mmreq_one=requests.get("http://"+mmmip+":8080/remote?action=SHOW&module=module_2_currentweather")
                                mmreq_two=requests.get("http://"+mmmip+":8080/remote?action=SHOW&module=module_3_currentweather")
                            if 'hide'.lower() in mmmcommand:
                                mmreq_one=requests.get("http://"+mmmip+":8080/remote?action=HIDE&module=module_2_currentweather")
                                mmreq_two=requests.get("http://"+mmmip+":8080/remote?action=HIDE&module=module_3_currentweather")
                        if 'power off'.lower() in mmmcommand:
                            mmreq=requests.get("http://"+mmmip+":8080/remote?action=SHUTDOWN")
                        if 'reboot'.lower() in mmmcommand:
                            mmreq=requests.get("http://"+mmmip+":8080/remote?action=REBOOT")
                        if 'restart'.lower() in mmmcommand:
                            mmreq=requests.get("http://"+mmmip+":8080/remote?action=RESTART")
                        if 'display on'.lower() in mmmcommand:
                            mmreq=requests.get("http://"+mmmip+":8080/remote?action=MONITORON")
                        if 'display off'.lower() in mmmcommand:
                            mmreq=requests.get("http://"+mmmip+":8080/remote?action=MONITOROFF")
                    except requests.exceptions.ConnectionError:
                        say("Magic mirror not online")
                if (custom_action_keyword['Keywords']['Recipe_pushbullet'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    ingrequest=str(usrcmd).lower()
                    ingredientsidx=ingrequest.find('for')
                    ingrequest=ingrequest[ingredientsidx:]
                    ingrequest=ingrequest.replace('for',"",1)
                    ingrequest=ingrequest.replace("'}","",1)
                    ingrequest=ingrequest.strip()
                    ingrequest=ingrequest.replace(" ","%20",1)
                    getrecipe(ingrequest)
                if (custom_action_keyword['Keywords']['Kickstarter_tracking'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    kickstarter_tracker(str(usrcmd).lower())
                if (custom_action_keyword['Keywords']['Pi_GPIO_control'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    Action(str(usrcmd).lower())
                if (custom_action_keyword['Keywords']['YouTube_music_stream'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    vlcplayer.stop_vlc()
                    if 'autoplay'.lower() in str(usrcmd).lower():
                        YouTube_Autoplay(str(usrcmd).lower())
                    else:
                        YouTube_No_Autoplay(str(usrcmd).lower())
                if (custom_action_keyword['Keywords']['Stop_music'][0]).lower() in str(usrcmd).lower():
                    stop()
                if 'radio'.lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    radio(str(usrcmd).lower())
                if (custom_action_keyword['Keywords']['ESP_control'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    ESP(str(usrcmd).lower())
                if (custom_action_keyword['Keywords']['Parcel_tracking'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    track()
                if (custom_action_keyword['Keywords']['RSS'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['RSS'][1]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    feed(str(usrcmd).lower())
                if (custom_action_keyword['Keywords']['Kodi_actions'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    kodiactions(str(usrcmd).lower())
                # Google Assistant now comes built in with chromecast control, so custom function has been commented
                # if 'chromecast'.lower() in str(usrcmd).lower():
                #     assistant.stop_conversation()
                #     if 'play'.lower() in str(usrcmd).lower():
                #         chromecast_play_video(str(usrcmd).lower())
                #     else:
                #         chromecast_control(usrcmd)
                if (custom_action_keyword['Keywords']['Pause_resume'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Pause_resume'][1]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    if vlcplayer.is_vlc_playing():
                        if (custom_action_keyword['Keywords']['Pause_resume'][0]).lower() in str(usrcmd).lower():
                            vlcplayer.pause_vlc()
                    if checkvlcpaused():
                        if (custom_action_keyword['Keywords']['Pause_resume'][1]).lower() in str(usrcmd).lower():
                            vlcplayer.play_vlc()
                    elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                        say("Sorry nothing is playing right now")
                if (custom_action_keyword['Keywords']['Track_change']['Next'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Next'][1]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Next'][2]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    if vlcplayer.is_vlc_playing() or checkvlcpaused()==True:
                        vlcplayer.stop_vlc()
                        vlcplayer.change_media_next()
                    elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                        say("Sorry nothing is playing right now")
                if (custom_action_keyword['Keywords']['Track_change']['Previous'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Previous'][1]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Previous'][2]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    if vlcplayer.is_vlc_playing() or checkvlcpaused()==True:
                        vlcplayer.stop_vlc()
                        vlcplayer.change_media_previous()
                    elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                        say("Sorry nothing is playing right now")
                if (custom_action_keyword['Keywords']['VLC_music_volume'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    if vlcplayer.is_vlc_playing()==True or checkvlcpaused()==True:
                        if 'set'.lower() in str(usrcmd).lower() or 'change'.lower() in str(usrcmd).lower():
                            if 'hundred'.lower() in str(usrcmd).lower() or 'maximum' in str(usrcmd).lower():
                                settingvollevel=100
                                with open('/home/pi/.mediavolume.json', 'w') as vol:
                                    json.dump(settingvollevel, vol)
                            elif 'zero'.lower() in str(usrcmd).lower() or 'minimum' in str(usrcmd).lower():
                                settingvollevel=0
                                with open('/home/pi/.mediavolume.json', 'w') as vol:
                                    json.dump(settingvollevel, vol)
                            else:
                                for settingvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(usrcmd)):
                                    with open('/home/pi/.mediavolume.json', 'w') as vol:
                                        json.dump(settingvollevel, vol)
                            print('Setting volume to: '+str(settingvollevel))
                            vlcplayer.set_vlc_volume(int(settingvollevel))
                        elif 'increase'.lower() in str(usrcmd).lower() or 'decrease'.lower() in str(usrcmd).lower() or 'reduce'.lower() in str(usrcmd).lower():
                            if os.path.isfile("/home/pi/.mediavolume.json"):
                                with open('/home/pi/.mediavolume.json', 'r') as vol:
                                    oldvollevel = json.load(vol)
                                    for oldvollevel in re.findall(r'\b\d+\b', str(oldvollevel)):
                                        oldvollevel=int(oldvollevel)
                            else:
                                oldvollevel=vlcplayer.get_vlc_volume
                                for oldvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(output)):
                                    oldvollevel=int(oldvollevel)
                            if 'increase'.lower() in str(usrcmd).lower():
                                if any(char.isdigit() for char in str(usrcmd)):
                                    for changevollevel in re.findall(r'\b\d+\b', str(usrcmd)):
                                        changevollevel=int(changevollevel)
                                else:
                                    changevollevel=10
                                newvollevel= oldvollevel+ changevollevel
                                print(newvollevel)
                                if int(newvollevel)>100:
                                    settingvollevel==100
                                elif int(newvollevel)<0:
                                    settingvollevel==0
                                else:
                                    settingvollevel=newvollevel
                                with open('/home/pi/.mediavolume.json', 'w') as vol:
                                    json.dump(settingvollevel, vol)
                                print('Setting volume to: '+str(settingvollevel))
                                vlcplayer.set_vlc_volume(int(settingvollevel))
                            if 'decrease'.lower() in str(usrcmd).lower() or 'reduce'.lower() in str(usrcmd).lower():
                                if any(char.isdigit() for char in str(usrcmd)):
                                    for changevollevel in re.findall(r'\b\d+\b', str(usrcmd)):
                                        changevollevel=int(changevollevel)
                                else:
                                    changevollevel=10
                                newvollevel= oldvollevel - changevollevel
                                print(newvollevel)
                                if int(newvollevel)>100:
                                    settingvollevel==100
                                elif int(newvollevel)<0:
                                    settingvollevel==0
                                else:
                                    settingvollevel=newvollevel
                                with open('/home/pi/.mediavolume.json', 'w') as vol:
                                    json.dump(settingvollevel, vol)
                                print('Setting volume to: '+str(settingvollevel))
                                vlcplayer.set_vlc_volume(int(settingvollevel))
                        else:
                            say("Sorry I could not help you")
                    else:
                        say("Sorry nothing is playing right now")
                if (custom_action_keyword['Keywords']['Music_index_refresh'][0]).lower() in str(usrcmd).lower() and (custom_action_keyword['Keywords']['Music_index_refresh'][1]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    refreshlists()
                if (custom_action_keyword['Keywords']['Google_music_streaming'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    vlcplayer.stop_vlc()
                    gmusicselect(str(usrcmd).lower())
                if (custom_action_keyword['Keywords']['Spotify_music_streaming'][0]).lower() in str(usrcmd).lower():
                    assistant.stop_conversation()
                    vlcplayer.stop_vlc()
                    spotify_playlist_select(str(usrcmd).lower())
        if custom_wakeword:
            self.detector.terminate()


if __name__ == '__main__':
    try:
        Myassistant().main()
    except Exception as error:
        logger.exception(error)
