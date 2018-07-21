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
import argparse
import os.path
import os
import json
import subprocess
import re
import psutil
import logging
import imp
import google.auth.transport.requests
import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
DEVICE_API_URL = 'https://embeddedassistant.googleapis.com/v1alpha2'
from actions import Action
from actions import YouTube_No_Autoplay
from actions import YouTube_Autoplay
from actions import radio
from actions import ESP
from actions import track
from actions import feed
import requests
from actions import kodiactions
from actions import mutevolstatus
from actions import gmusic
from actions import chromecast_play_video
from actions import chromecast_control
from actions import kickstarter_tracker
from actions import getrecipe
from actions import hue_control
from actions import misc
from actions import tasmota_control
from actions import load_settings
import snowboydecoder
import sys
import signal
from threading import Thread

ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))

resources = {'fb': '{}/sample-audio-files/Fb.wav'.format(ROOT_PATH), 'startup': '{}/sample-audio-files/Startup.wav'.format(ROOT_PATH)}

logging.basicConfig(filename='/tmp/GassistPi.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logger=logging.getLogger(__name__)

INFO_FILE = os.path.expanduser('~/gassistant-credentials.info')

#Login with default kodi/kodi credentials
#kodi = Kodi("http://localhost:8080/jsonrpc")

#Login with custom credentials
# Kodi("http://IP-ADDRESS-OF-KODI:8080/jsonrpc", "username", "password")
kodi = Kodi("http://192.168.1.15:8080/jsonrpc", "kodi", "kodi")

misc.setup_GPIO()

settings = load_settings()
googleMusic=gmusic()

PRIVACY_ENABLED=True
'''
If PRIVACY_ENABLED is set to True then the assistant mic will be
muted and the assistat will only listen to you when you trigger it by
the custom wake word (snowboy)
If PRIVACY_ENABLED is set to False then snowboy wakewords and the usual
"hi google" and "ok google " hotwords will all work but this comes with
violating your privacy by having google always listening to you

'''

#Add your custom models here
models = ['{}/src/resources/models/smart_mirror.umdl'.format(ROOT_PATH), '{}/src/resources/models/snowboy.umdl'.format(ROOT_PATH)]



#Magic Mirror Remote Control Declarations
mmmip='ENTER_YOUR_MAGIC_MIRROR_IP'


class Myassistant():

    def __init__(self):
        self.interrupted=False
        self.can_start_conversation=False
        self.assistant=None
        self.sensitivity = [0.5]*len(models)
        self.callbacks = [self.detected]*len(models)
        self.detector = snowboydecoder.HotwordDetector(models, sensitivity=self.sensitivity)
        self.t1 = Thread(target=self.start_detector)

    
    def signal_handler(self,signal, frame):
        self.interrupted = True


    def interrupt_callback(self,):
        return self.interrupted
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
    def process_event(self,event, device_id):
        """Pretty prints events.
        Prints all events that occur with two spaces between each new
        conversation and a single space between turns of a conversation.
        Args:
            event(event.Event): The current event to process.
        """
        print(event)
        if event.type == EventType.ON_START_FINISHED:
            self.can_start_conversation = True
            if PRIVACY_ENABLED:
                self.assistant.set_mic_mute(True)
            self.t1.start()
        if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            self.can_start_conversation = False
            misc.pause_vlc()
            misc.play_audio_file(resources['fb'])
            print('listening')
            #Uncomment the following after starting the Kodi
            #status=mutevolstatus()
            #vollevel=status[1]
            #with open(os.path.expanduser('~/.volume.json'), 'w') as f:
                   #json.dump(vollevel, f)
            #kodi.Application.SetVolume({"volume": 0})
            misc.set_GPIO(GPIO5=1,GPIO6=None,duty=100)

        if (event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT 
            or event.type == EventType.ON_NO_RESPONSE):
            self.can_start_conversation = True
            if PRIVACY_ENABLED:
                self.assistant.set_mic_mute(True)
            misc.set_GPIO(GPIO5=0,GPIO6=0,duty=0)
            # Uncomment the following after starting the Kodi
            # with open('/home/pi/.volume.json', 'r') as f:
                   # vollevel = json.load(f)
                   # kodi.Application.SetVolume({"volume": vollevel})
            misc.play_vlc()

        if (event.type == EventType.ON_RESPONDING_STARTED and event.args and not event.args['is_error_response']):
            misc.set_GPIO(GPIO5=0,GPIO6=1,duty=50)
            self.can_start_conversation = True

        if event.type == EventType.ON_RESPONDING_FINISHED:
            misc.set_GPIO(GPIO5=1,GPIO6=0,duty=100)

        if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
            misc.set_GPIO(GPIO5=0,GPIO6=0,duty=0)
            misc.play_vlc()

        

        if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
                event.args and not event.args['with_follow_on_turn']):
            self.can_start_conversation = True
            misc.set_GPIO(GPIO5=0,GPIO6=0,duty=0)
            # Uncomment the following after starting the Kodi
            # with open(os.path.expanduser('~/.volume.json'), 'r') as f:
                   # vollevel = json.load(f)
                   # kodi.Application.SetVolume({"volume": vollevel})
            misc.play_vlc()

        if event.type == EventType.ON_DEVICE_ACTION:
            for command, params in process_device_actions(event, device_id):
                print('Do command', command, 'with params', str(params))

    def detected(self):
        if self.can_start_conversation == True:
            self.assistant.set_mic_mute(False)
            self.assistant.start_conversation()
            print('assistant is listening')
        
    def start_detector(self):
        self.detector.start(detected_callback=self.callbacks,
            interrupt_check=self.interrupt_callback,
            sleep_time=0.03)

    def main(self):
        # capture SIGINT signal, e.g., Ctrl+C
        #signal.signal(signal.SIGINT, signal_handler)
        print('Listening... Press Ctrl+C to exit')

        args = imp.load_source('args',INFO_FILE)
        if not hasattr(args,'credentials'):
            args.credentials = os.path.join(os.path.expanduser('~/.config'),'google-oauthlib-tool','credentials.json')


        with open(args.credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
        with Assistant(credentials, args.device_model_id) as assistant:
            self.assistant = assistant
            misc.play_audio_file(resources['startup'])
            events = assistant.start()
            print('device_model_id:', args.device_model_id + '\n' +
                  'device_id:', assistant.device_id + '\n')
            if args.project_id:
                self.register_device(args.project_id, credentials,
                                args.device_model_id, assistant.device_id)
            for event in events:
                self.process_event(event, assistant.device_id)
                usrcmd=event.args
                try:
                    cmdtext=usrcmd['text'].lower()
                except:
                    cmdtext=''
                with open('{}/src/diyHue/config.json'.format(ROOT_PATH), 'r') as config:
                     hueconfig = json.load(config)
                for i in range(1,len(hueconfig['lights'])+1):
                    try:
                        if str(hueconfig['lights'][str(i)]['name']).lower() in cmdtext:
                            assistant.stop_conversation()
                            hue_control(cmdtext,str(i),str(hueconfig['lights_address'][str(i)]['ip']))
                            break
                    except Keyerror:
                        misc.say('Unable to help, please check your config file')

                for item in settings['tasmota_devicelist']:
                    if item['friendly-name'].lower()  in cmdtext:
                        assistant.stop_conversation()
                        tasmota_control(cmdtext, item)
                        break
                if 'magic mirror'.lower() in cmdtext:
                    assistant.stop_conversation()
                    try:
                        mmmcommand=cmdtext
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
                        misc.say("Magic mirror not online")
                if 'ingredients'.lower() in cmdtext:
                    assistant.stop_conversation()
                    ingrequest=cmdtext
                    ingredientsidx=ingrequest.find('for')
                    ingrequest=ingrequest[ingredientsidx:]
                    ingrequest=ingrequest.replace('for',"",1)
                    ingrequest=ingrequest.replace("'}","",1)
                    ingrequest=ingrequest.strip()
                    ingrequest=ingrequest.replace(" ","%20",1)
                    getrecipe(ingrequest)
                if 'kickstarter'.lower() in cmdtext:
                    assistant.stop_conversation()
                    kickstarter_tracker(cmdtext)
                if 'trigger'.lower() in cmdtext:
                    assistant.stop_conversation()
                    Action(cmdtext)
                if 'stream'.lower() in cmdtext:
                    assistant.stop_conversation()
                    if os.path.isfile("{}/src/trackchange.py".format(ROOT_PATH)):
                        os.system('rm {}/src/trackchange.py'.format(ROOT_PATH))
                        if 'autoplay'.lower() in cmdtext:
                            YouTube_Autoplay(cmdtext)
                        else:
                            YouTube_No_Autoplay(cmdtext)
                    else:
                        if 'autoplay'.lower() in cmdtext:
                            os.system('echo "from actions import youtubeplayer\n\n" >> {}/src/trackchange.py'.format(ROOT_PATH))
                            os.system('echo "youtubeplayer()\n" >> {}/src/trackchange.py'.format(ROOT_PATH))
                            YouTube_Autoplay(cmdtext)
                        else:
                            YouTube_No_Autoplay(cmdtext)

                if 'stop'.lower() in cmdtext:
                    misc.stop_vlc()
                if 'radio' in cmdtext:
                    assistant.stop_conversation()
                    radio(cmdtext)
                if 'wireless'.lower() in cmdtext:
                    assistant.stop_conversation()
                    ESP(cmdtext)
                if 'parcel'.lower() in cmdtext:
                    assistant.stop_conversation()
                    track()
                if 'news'.lower() in cmdtext or 'feed'.lower() in cmdtext or 'quote'.lower() in cmdtext:
                    assistant.stop_conversation()
                    feed(cmdtext)
                if 'on kodi'.lower() in cmdtext:
                    assistant.stop_conversation()
                    kodiactions(cmdtext)
                if 'chromecast'.lower() in cmdtext:
                    assistant.stop_conversation()
                    if 'play'.lower() in cmdtext:
                        chromecast_play_video(cmdtext)
                    else:
                        chromecast_control(usrcmd)
                if 'pause music'.lower() in cmdtext or 'resume music'.lower() in cmdtext:
                    assistant.stop_conversation()
                    if misc.is_vlc_playing():
                        if 'pause music' in cmdtext:
                            misc.pause_vlc()
                        elif 'resume music' in cmdtext:
                            misc.play_vlc()
                    else:
                        misc.say("Sorry nothing is playing right now")
                if 'music volume'.lower() in cmdtext:
                    if misc.is_vlc_playing():
                        if 'set'.lower() in cmdtext or 'change'.lower() in cmdtext:
                            if 'hundred'.lower() in cmdtext or 'maximum' in cmdtext:
                                settingvollevel=100
                                with open(os.path.expanduser('~/.mediavolume.json'), 'w') as vol:
                                    json.dump(settingvollevel, vol)
                                misc.set_vlc_volume(settingvollevel)
                            elif 'zero'.lower() in cmdtext or 'minimum' in cmdtext:
                                settingvollevel=0
                                with open(os.path.expanduser('~/.mediavolume.json'), 'w') as vol:
                                    json.dump(settingvollevel, vol)
                                misc.set_vlc_volume(settingvollevel)
                            else:
                                for settingvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(usrcmd)):
                                    with open(os.path.expanduser('~/.mediavolume.json'), 'w') as vol:
                                        json.dump(settingvollevel, vol)
                                misc.set_vlc_volume(settingvollevel)
                        elif 'increase'.lower() in cmdtext or 'decrease'.lower() in cmdtext or 'reduce'.lower() in cmdtext:
                            if os.path.isfile(os.path.expanduser("~/.mediavolume.json")):
                                with open(os.path.expanduser('~/.mediavolume.json'), 'r') as vol:
                                    oldvollevel = json.load(vol)
                                    for oldvollevel in re.findall(r'\b\d+\b', str(oldvollevel)):
                                        oldvollevel=int(oldvollevel)
                            else:
                                oldvollevel=misc.get_vlc_volume()
                            if 'increase'.lower() in cmdtext:
                                if any(char.isdigit() for char in str(usrcmd)):
                                    for changevollevel in re.findall(r'\b\d+\b', str(usrcmd)):
                                        changevollevel=int(changevollevel)
                                else:
                                    changevollevel=10
                                newvollevel= oldvollevel+ changevollevel
                                print(newvollevel)
                                if newvollevel>100:
                                    settingvollevel==100
                                elif newvollevel<0:
                                    settingvollevel==0
                                else:
                                    settingvollevel=newvollevel
                                with open(os.path.expanduser('~/.mediavolume.json'), 'w') as vol:
                                    json.dump(settingvollevel, vol)
                                misc.set_vlc_volume(settingvollevel)
                            if 'decrease'.lower() in cmdtext or 'reduce'.lower() in cmdtext:
                                if any(char.isdigit() for char in str(usrcmd)):
                                    for changevollevel in re.findall(r'\b\d+\b', str(usrcmd)):
                                        changevollevel=int(changevollevel)
                                else:
                                    changevollevel=10
                                newvollevel= oldvollevel - changevollevel
                                print(newvollevel)
                                if newvollevel>100:
                                    settingvollevel==100
                                elif newvollevel<0:
                                    settingvollevel==0
                                else:
                                    settingvollevel=newvollevel
                                with open(os.path.expanduser('~/.mediavolume.json'), 'w') as vol:
                                    json.dump(settingvollevel, vol)
                                misc.set_vlc_volume(settingvollevel)
                        else:
                            misc.say("Sorry I could not help you")
                    else:
                        misc.say("Sorry nothing is playing right now")

                if 'refresh'.lower() in cmdtext and 'music'.lower() in cmdtext:
                    assistant.stop_conversation()
                    googleMusic.refreshlists()
                if 'google music'.lower() in cmdtext:
                    assistant.stop_conversation()
                    googleMusic.gmusicselect(cmdtext)
        self.detector.terminate()
if __name__ == '__main__':
    try:
        Myassistant().main()
    except Exception as error:
        logger.exception(error)
