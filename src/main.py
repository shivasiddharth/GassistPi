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
try:
    import RPi.GPIO as GPIO
except Exception as e:
    if str(e) == 'No module named \'RPi\'':
        GPIO = None
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
import io
import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from google.assistant.library.device_helpers import register_device
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types     
import paho.mqtt.client as mqtt
from actions import say
from actions import trans
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
if GPIO!=None:
    from indicator import assistantindicator
    from indicator import stoppushbutton
    from indicator import irreceiver
    GPIOcontrol=True
else:
    irreceiver=None
    GPIOcontrol=False
from pathlib import Path
from Adafruit_IO import MQTTClient
from actions import Domoticz_Device_Control
from actions import domoticz_control
from actions import domoticz_devices
from actions import gaana_playlist_select
from actions import deezer_playlist_select
from actions import gender
from actions import on_ir_receive
from actions import Youtube_credentials
from actions import Spotify_credentials
from actions import notify_tts
from actions import sendSMS
from actions import translanguage
from actions import language
from actions import voicenote
from actions import langlist
from audiorecorder import record_to_file

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

logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG , filename='/tmp/GassistPi.log')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))

#Login with default kodi/kodi credentials
#kodi = Kodi("http://localhost:8080/jsonrpc")

#Login with custom credentials
# Kodi("http://IP-ADDRESS-OF-KODI:8080/jsonrpc", "username", "password")
kodiurl=("http://"+str(configuration['Kodi']['ip'])+":"+str(configuration['Kodi']['port'])+"/jsonrpc")
kodi = Kodi(kodiurl, configuration['Kodi']['username'], configuration['Kodi']['password'])
if configuration['Kodi']['Kodi_Control']=='Enabled':
    kodicontrol=True
else:
    kodicontrol=False


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
        if custom_action_keyword['Dict']['On'] in phrase:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power"+devportid+"%20on")
            say("Tunring on "+devname)
        elif custom_action_keyword['Dict']['Off'] in phrase:
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
        self.mutestatus=False
        self.interpreter=False
        self.interpconvcounter=0
        self.interpcloudlang1=language
        self.interpttslang1=translanguage
        self.interpcloudlang2=''
        self.interpttslang2=''
        self.singleresposne=False
        self.singledetectedresponse=''
        self.t1 = Thread(target=self.start_detector)
        if GPIOcontrol:
            self.t2 = Thread(target=self.pushbutton)
        if configuration['MQTT']['MQTT_Control']=='Enabled':
            self.t3 = Thread(target=self.mqtt_start)
        if irreceiver!=None:
            self.t4 = Thread(target=self.ircommands)
        if configuration['ADAFRUIT_IO']['ADAFRUIT_IO_CONTROL']=='Enabled':
            self.t5 = Thread(target=self.adafruit_mqtt_start)

    def signal_handler(self,signal, frame):
        self.interrupted = True

    def interrupt_callback(self,):
        return self.interrupted

    def buttonsinglepress(self):
        if os.path.isfile("{}/.mute".format(USER_PATH)):
            os.system("sudo rm {}/.mute".format(USER_PATH))
            assistantindicator('unmute')
            if configuration['Wakewords']['Ok_Google']=='Disabled':
                self.assistant.set_mic_mute(True)
                print("Mic is open, but Ok-Google is disabled")
            else:
                self.assistant.set_mic_mute(False)
            # if custom_wakeword:
            #     self.t1.start()
                print("Turning on the microphone")
        else:
            open('{}/.mute'.format(USER_PATH), 'a').close()
            assistantindicator('mute')
            self.assistant.set_mic_mute(True)
            # if custom_wakeword:
            #     self.thread_end(t1)
            print("Turning off the microphone")

    def buttondoublepress(self):
        print('Stopped')
        stop()

    def buttontriplepress(self):
        print("Create your own action for button triple press")

    def pushbutton(self):
        if GPIOcontrol:
            while mutestopbutton:
                time.sleep(.1)
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
        print()
        if event.type == EventType.ON_MUTED_CHANGED:
            self.mutestatus=event.args["is_muted"]

        if event.type == EventType.ON_START_FINISHED:
            self.can_start_conversation = True
            if GPIOcontrol:
                self.t2.start()
            if os.path.isfile("{}/.mute".format(USER_PATH)):
                assistantindicator('mute')
            if (configuration['Wakewords']['Ok_Google']=='Disabled' or os.path.isfile("{}/.mute".format(USER_PATH))):
                self.assistant.set_mic_mute(True)
            if custom_wakeword:
                self.t1.start()
            if configuration['MQTT']['MQTT_Control']=='Enabled':
                self.t3.start()
            if irreceiver!=None:
                self.t4.start()
            if configuration['ADAFRUIT_IO']['ADAFRUIT_IO_CONTROL']=='Enabled':
                self.t5.start()

        if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            subprocess.Popen(["aplay", "{}/sample-audio-files/Fb.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.can_start_conversation = False
            if kodicontrol:
                try:
                    status=mutevolstatus()
                    vollevel=status[1]
                    with open('{}/.volume.json'.format(USER_PATH), 'w') as f:
                           json.dump(vollevel, f)
                    kodi.Application.SetVolume({"volume": 0})
                    kodi.GUI.ShowNotification({"title": "", "message": ".....Listening.....", "image": "{}/GoogleAssistantImages/GoogleAssistantBarsTransparent.gif".format(ROOT_PATH)})
                except requests.exceptions.ConnectionError:
                    print("Kodi TV box not online")

            if GPIOcontrol:
                assistantindicator('listening')
            if vlcplayer.is_vlc_playing():
                if os.path.isfile("{}/.mediavolume.json".format(USER_PATH)):
                    try:
                        with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                            volume = json.load(vol)
                        vlcplayer.set_vlc_volume(15)
                    except json.decoder.JSONDecodeError:
                        currentvolume=vlcplayer.get_vlc_volume()
                        print(currentvolume)
                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                           json.dump(currentvolume, vol)
                        vlcplayer.set_vlc_volume(15)
                else:
                    currentvolume=vlcplayer.get_vlc_volume()
                    print(currentvolume)
                    with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                       json.dump(currentvolume, vol)
                    vlcplayer.set_vlc_volume(15)

        if (event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT or event.type == EventType.ON_NO_RESPONSE):
            self.can_start_conversation = True
            if GPIOcontrol:
                assistantindicator('off')
            if kodicontrol:
                try:
                    with open('{}/.volume.json'.format(USER_PATH), 'r') as f:
                           vollevel = json.load(f)
                           kodi.Application.SetVolume({"volume": vollevel})
                except requests.exceptions.ConnectionError:
                    print("Kodi TV box not online")

            if (configuration['Wakewords']['Ok_Google']=='Disabled' or os.path.isfile("{}/.mute".format(USER_PATH))):
                  self.assistant.set_mic_mute(True)
            if os.path.isfile("{}/.mute".format(USER_PATH)):
                if GPIOcontrol:
                    assistantindicator('mute')
            if vlcplayer.is_vlc_playing():
                with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                    oldvolume = json.load(vol)
                vlcplayer.set_vlc_volume(int(oldvolume))

        if (event.type == EventType.ON_RESPONDING_STARTED and event.args and not event.args['is_error_response']):
            if GPIOcontrol:
                assistantindicator('speaking')

        if event.type == EventType.ON_RESPONDING_FINISHED:
            if GPIOcontrol:
                assistantindicator('off')

        if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
            if GPIOcontrol:
                assistantindicator('off')
            if self.singleresposne:
                self.assistant.stop_conversation()
                self.singledetectedresponse= event.args["text"]
            else:
                usrcmd=event.args["text"]
                self.custom_command(usrcmd)
                if kodicontrol:
                    try:
                        kodi.GUI.ShowNotification({"title": "", "message": event.args["text"], "image": "{}/GoogleAssistantImages/GoogleAssistantDotsTransparent.gif".format(ROOT_PATH)})
                    except requests.exceptions.ConnectionError:
                        print("Kodi TV box not online")

        if event.type == EventType.ON_RENDER_RESPONSE:
            if GPIOcontrol:
                assistantindicator('off')
            if kodicontrol:
                try:
                    kodi.GUI.ShowNotification({"title": "", "message": event.args["text"], "image": "{}/GoogleAssistantImages/GoogleAssistantTransparent.gif".format(ROOT_PATH),"displaytime": 20000})
                except requests.exceptions.ConnectionError:
                    print("Kodi TV box not online")

        if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
                event.args and not event.args['with_follow_on_turn']):
            self.can_start_conversation = True
            if GPIOcontrol:
                assistantindicator('off')
            if (configuration['Wakewords']['Ok_Google']=='Disabled' or os.path.isfile("{}/.mute".format(USER_PATH))):
                self.assistant.set_mic_mute(True)
            if os.path.isfile("{}/.mute".format(USER_PATH)):
                if GPIOcontrol:
                    assistantindicator('mute')
            if kodicontrol:
                try:
                    with open('{}/.volume.json'.format(USER_PATH), 'r') as f:
                        vollevel = json.load(f)
                        kodi.Application.SetVolume({"volume": vollevel})
                except requests.exceptions.ConnectionError:
                    print("Kodi TV box not online")

            if vlcplayer.is_vlc_playing():
                with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                    oldvolume= json.load(vol)
                vlcplayer.set_vlc_volume(int(oldvolume))

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
            if self.mutestatus:
                self.assistant.set_mic_mute(False)
                time.sleep(1)
                self.assistant.start_conversation()
            if not self.mutestatus:
                self.assistant.start_conversation()
            print('Assistant is listening....')

    def start_detector(self):
        self.detector.start(detected_callback=self.callbacks,
            interrupt_check=self.interrupt_callback,
            sleep_time=0.03)

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        client.subscribe(configuration['MQTT']['TOPIC'])

    def on_message(self, client, userdata, msg):
        if self.can_start_conversation == True:
            print("Message from MQTT: "+str(msg.payload.decode('utf-8')))
            mqtt_query=str(msg.payload.decode('utf-8'))
            if 'custom' in mqtt_query.lower():
                mqtt_query=mqtt_query.lower()
                mqtt_queryidx=mqtt_query.find('custom')
                mqtt_query=mqtt_query[mqtt_queryidx:]
                mqtt_query=mqtt_query.replace('custom',"",1)
                mqtt_query=mqtt_query.strip()
                self.custom_command(mqtt_query)
            elif mqtt_query.lower() == 'mute':
                self.buttonsinglepress()
            else:
                self.assistant.send_text_query(mqtt_query)

    def mqtt_start(self):
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.username_pw_set(configuration['MQTT']['UNAME'], configuration['MQTT']['PSWRD'])
        client.connect(configuration['MQTT']['IP'], 1883, 60)
        client.loop_forever()

    def adafruit_connected(self,client):
        print('Connected to Adafruit IO!  Listening for {0} changes...'.format(configuration['ADAFRUIT_IO']['FEEDNAME']))
        client.subscribe(configuration['ADAFRUIT_IO']['FEEDNAME'])

    def adafruit_disconnected(self,client):
        print('Disconnected from Adafruit IO!')

    def adafruit_message(self,client, feed_id, payload):
        if self.can_start_conversation == True:
            print("Message from ADAFRUIT MQTT: "+str(payload))
            adafruit_mqtt_query=str(payload)
            self.custom_command(adafruit_mqtt_query)

    def adafruit_mqtt_start(self):
        if configuration['ADAFRUIT_IO']['ADAFRUIT_IO_CONTROL']=='Enabled':
            client = MQTTClient(configuration['ADAFRUIT_IO']['ADAFRUIT_IO_USERNAME'], configuration['ADAFRUIT_IO']['ADAFRUIT_IO_KEY'])
            client.on_connect    = self.adafruit_connected
            client.on_disconnect = self.adafruit_disconnected
            client.on_message    = self.adafruit_message
            client.connect()
            client.loop_blocking()
        else:
            print("Adafruit_io MQTT client not enabled")

    def ircommands(self):
        if irreceiver!=None:
            try:
                print("IR Sensor Started")
                while True:
                    time.sleep(.1)
                    #print("Listening for IR Signal on GPIO "+irreceiver)
                    GPIO.wait_for_edge(irreceiver, GPIO.FALLING)
                    code = on_ir_receive(irreceiver)
                    if code:
                        if self.can_start_conversation == True:
                            for codenum, usercode in enumerate(configuration['IR']['Codes']):
                                if usercode==code:
                                    if 'custom' in (configuration['IR']['Commands'][codenum]).lower():
                                        self.custom_command((configuration['IR']['Commands'][codenum]).lower())
                                    elif 'start conversation' in (configuration['IR']['Commands'][codenum]).lower():
                                        self.assistant.start_conversation()
                                    elif 'mute' in (configuration['IR']['Commands'][codenum]).lower():
                                        self.buttonsinglepress()
                                    else:
                                        self.assistant.send_text_query(configuration['IR']['Commands'][codenum])
                                    break
            except KeyboardInterrupt:
                pass
            except RuntimeError:
                pass
            print("Stopping IR Sensor")

    def cloud_speech_transcribe(self,file,language):
        client = speech.SpeechClient()
        with io.open(speech_file, 'rb') as audio_file:
            content = audio_file.read()
        audio = types.RecognitionAudio(content=content)
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code=language)
        response = client.recognize(config, audio)
        for result in response.results:
            transcribedtext=u'{}'.format(result.alternatives[0].transcript)
        return transcribedtext

    def interpreter_mode_trigger(self,switch):
        if configuration['Speechtotext']['Google_Cloud_Speech']['Cloud_Speech_Control']=='Disabled':
            say("Cloud speech has not been enabled")
        else:
            if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""):
                if configuration['Speechtotext']['Google_Cloud_Speech']['Google_Cloud_Speech_Credentials_Path']!="ENTER THE PATH TO YOUR CLOUD SPEECH CREDENTIALS FILE HERE":
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = configuration['Speechtotext']['Google_Cloud_Speech']['Google_Cloud_Speech_Credentials_Path']
                    if switch=="Start":
                        self.interpreter=True
                        say("Starting interpreter.")
                        self.interpreter_speech_recorder()
                    elif switch=="Stop":
                        self.interpreter=False
                        self.interpconvcounter=0
                        say("Stopping interpreter.")
                    else:
                        self.interpreter=False
            else:
                if switch=="Start":
                    self.interpreter=True
                    say("Starting interpreter.")
                    self.interpreter_speech_recorder()
                elif switch=="Stop":
                    self.interpreter=False
                    self.interpconvcounter=0
                    say("Stopping interpreter.")
                else:
                    self.interpreter=False

    def interpreter_speech_recorder(self):
        if self.interpreter:
            interpreteraudio='/tmp/interpreter.wav'
            subprocess.Popen(["aplay", "{}/sample-audio-files/Fb.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while not record_to_file(interpreteraudio):
                time.sleep(.1)
            if (self.interpconvcounter % 2)==0:
                text=cloud_speech_transcribe(interpreteraudio,self.interpcloudlang1)
                print("Local Speaker: "+text)
            elif (self.interpconvcounter % 2)==1:
                text=cloud_speech_transcribe(interpreteraudio,self.interpcloudlang2)
                print("Foreign Speaker: "+text)
            self.interpreter_mode_tts(text,self.interpconvcounter)
            self.interpconvcounter=self.interpconvcounter+1
        else:
            say("Interpreter not active.")

    def interpreter_mode_tts(self,text,count):
        if (count % 2)==0:
            say(text,self.interpttslang1,self.interpttslang2)
            self.interpreter_speech_recorder()
        else:
            say(text,self.interpttslang2,self.interpttslang1)
            self.interpreter_speech_recorder()

    def voicenote_recording(self):
        recordfilepath='/tmp/audiorecord.wav'
        subprocess.Popen(["aplay", "{}/sample-audio-files/Fb.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while not record_to_file(recordfilepath):
            time.sleep(.1)
        voicenote(recordfilepath)

    def single_user_response(self,prompt):
        self.singledetectedresponse=''
        self.singleresposne=True
        say(prompt)
        self.assistant.start_conversation()
        while self.singledetectedresponse=='':
            time.sleep(.1)
        self.singleresposne=False
        return self.singledetectedresponse

    def custom_command(self,usrcmd):
        if configuration['DIYHUE']['DIYHUE_Control']=='Enabled':
            if os.path.isfile('/opt/hue-emulator/config.json'):
                with open('/opt/hue-emulator/config.json', 'r') as config:
                     hueconfig = json.load(config)
                for i in range(1,len(hueconfig['lights'])+1):
                    try:
                        if str(hueconfig['lights'][str(i)]['name']).lower() in str(usrcmd).lower():
                            self.assistant.stop_conversation()
                            hue_control(str(usrcmd).lower(),str(i),str(hueconfig['lights_address'][str(i)]['ip']))
                            break
                    except Keyerror:
                        say('Unable to help, please check your config file')
        if configuration['Tasmota_devicelist']['Tasmota_Control']=='Enabled':
            for num, name in enumerate(tasmota_devicelist):
                if name.lower() in str(usrcmd).lower():
                    self.assistant.stop_conversation()
                    tasmota_control(str(usrcmd).lower(), name.lower(),tasmota_deviceip[num],tasmota_deviceportid[num])
        if configuration['Conversation']['Conversation_Control']=='Enabled':
            for i in range(1,numques+1):
                try:
                    if str(configuration['Conversation']['question'][i][0]).lower() in str(usrcmd).lower():
                        self.assistant.stop_conversation()
                        selectedans=random.sample(configuration['Conversation']['answer'][i],1)
                        say(selectedans[0])
                        break
                except Keyerror:
                    say('Please check if the number of questions matches the number of answers')

        if Domoticz_Device_Control==True and len(domoticz_devices['result'])>0:
            if len(configuration['Domoticz']['Devices']['Name'])==len(configuration['Domoticz']['Devices']['Id']):
                for i in range(0,len(configuration['Domoticz']['Devices']['Name'])):
                    if str(configuration['Domoticz']['Devices']['Name'][i]).lower() in str(usrcmd).lower():
                        self.assistant.stop_conversation()
                        domoticz_control(str(usrcmd).lower(),configuration['Domoticz']['Devices']['Id'][i],configuration['Domoticz']['Devices']['Name'][i])
                        break
            else:
                say("Number of devices and the number of ids given in config file do not match")

        if (custom_action_keyword['Keywords']['Magic_mirror'][0]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
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
            self.assistant.stop_conversation()
            ingrequest=str(usrcmd).lower()
            ingredientsidx=ingrequest.find('for')
            ingrequest=ingrequest[ingredientsidx:]
            ingrequest=ingrequest.replace('for',"",1)
            ingrequest=ingrequest.replace("'}","",1)
            ingrequest=ingrequest.strip()
            ingrequest=ingrequest.replace(" ","%20",1)
            getrecipe(ingrequest)
        if configuration['Pushbullet']['Pushbullet_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['Send_Message'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                say("What is your message?")
                self.voicenote_recording()
        if (custom_action_keyword['Keywords']['Kickstarter_tracking'][0]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
            kickstarter_tracker(str(usrcmd).lower())
        if configuration['Raspberrypi_GPIO_Control']['GPIO_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['Pi_GPIO_control'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                Action(str(usrcmd).lower())
        if configuration['YouTube']['YouTube_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['YouTube_music_stream'][0]).lower() in str(usrcmd).lower() and 'kodi' not in str(usrcmd).lower() and 'chromecast' not in str(usrcmd).lower():
                self.assistant.stop_conversation()
                vlcplayer.stop_vlc()
                if not Youtube_credentials:
                    say("Hey, you need to enter your google cloud api in the config file first.")
                else:
                    if 'autoplay'.lower() in str(usrcmd).lower():
                        YouTube_Autoplay(str(usrcmd).lower())
                    else:
                        YouTube_No_Autoplay(str(usrcmd).lower())
        if (custom_action_keyword['Keywords']['Stop_music'][0]).lower() in str(usrcmd).lower():
            stop()
        if configuration['Notify_TTS']['Notify_TTS_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['notify_TTS'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                notify_tts(str(usrcmd).lower())
        if configuration['Radio_stations']['Radio_Control']=='Enabled':
            if 'radio'.lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                vlcplayer.stop_vlc()
                radio(str(usrcmd).lower())
        if configuration['ESP']['ESP_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['ESP_control'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                ESP(str(usrcmd).lower())
        if (custom_action_keyword['Keywords']['Parcel_tracking'][0]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
            track()
        if (custom_action_keyword['Keywords']['RSS'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['RSS'][1]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
            feed(str(usrcmd).lower())
        if kodicontrol:
            try:
                if (custom_action_keyword['Keywords']['Kodi_actions'][0]).lower() in str(usrcmd).lower():
                    self.assistant.stop_conversation()
                    kodiactions(str(usrcmd).lower())
            except requests.exceptions.ConnectionError:
                say("Kodi TV box not online")
        # Google Assistant now comes built in with chromecast control, so custom function has been commented
        # if 'chromecast'.lower() in str(usrcmd).lower():
        #     self.assistant.stop_conversation()
        #     if 'play'.lower() in str(usrcmd).lower():
        #         chromecast_play_video(str(usrcmd).lower())
        #     else:
        #         chromecast_control(usrcmd)
        if (custom_action_keyword['Keywords']['Pause_resume'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Pause_resume'][1]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
            if vlcplayer.is_vlc_playing():
                if (custom_action_keyword['Keywords']['Pause_resume'][0]).lower() in str(usrcmd).lower():
                    vlcplayer.pause_vlc()
            if checkvlcpaused():
                if (custom_action_keyword['Keywords']['Pause_resume'][1]).lower() in str(usrcmd).lower():
                    vlcplayer.play_vlc()
            elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                say("Sorry nothing is playing right now")
        if (custom_action_keyword['Keywords']['Track_change']['Next'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Next'][1]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Next'][2]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
            if vlcplayer.is_vlc_playing() or checkvlcpaused()==True:
                vlcplayer.stop_vlc()
                vlcplayer.change_media_next()
            elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                say("Sorry nothing is playing right now")
        if (custom_action_keyword['Keywords']['Track_change']['Previous'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Previous'][1]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Previous'][2]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
            if vlcplayer.is_vlc_playing() or checkvlcpaused()==True:
                vlcplayer.stop_vlc()
                vlcplayer.change_media_previous()
            elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                say("Sorry nothing is playing right now")
        if (custom_action_keyword['Keywords']['VLC_music_volume'][0]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
            if vlcplayer.is_vlc_playing()==True or checkvlcpaused()==True:
                if (custom_action_keyword['Dict']['Set']).lower() in str(usrcmd).lower() or (custom_action_keyword['Dict']['Change']).lower() in str(usrcmd).lower():
                    if 'hundred'.lower() in str(usrcmd).lower() or custom_action_keyword['Dict']['Maximum'] in str(usrcmd).lower():
                        settingvollevel=100
                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                            json.dump(settingvollevel, vol)
                    elif 'zero'.lower() in str(usrcmd).lower() or custom_action_keyword['Dict']['Minimum'] in str(usrcmd).lower():
                        settingvollevel=0
                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                            json.dump(settingvollevel, vol)
                    else:
                        for settingvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(usrcmd)):
                            with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                                json.dump(settingvollevel, vol)
                    print('Setting volume to: '+str(settingvollevel))
                    vlcplayer.set_vlc_volume(int(settingvollevel))
                elif (custom_action_keyword['Dict']['Increase']).lower() in str(usrcmd).lower() or (custom_action_keyword['Dict']['Decrease']).lower() in str(usrcmd).lower() or 'reduce'.lower() in str(usrcmd).lower():
                    if os.path.isfile("{}/.mediavolume.json".format(USER_PATH)):
                        try:
                            with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                                oldvollevel = json.load(vol)
                                for oldvollevel in re.findall(r'\b\d+\b', str(oldvollevel)):
                                    oldvollevel=int(oldvollevel)
                        except json.decoder.JSONDecodeError:
                            oldvollevel=vlcplayer.get_vlc_volume
                            for oldvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(output)):
                                oldvollevel=int(oldvollevel)
                    else:
                        oldvollevel=vlcplayer.get_vlc_volume
                        for oldvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(output)):
                            oldvollevel=int(oldvollevel)
                    if (custom_action_keyword['Dict']['Increase']).lower() in str(usrcmd).lower():
                        if any(char.isdigit() for char in str(usrcmd)):
                            for changevollevel in re.findall(r'\b\d+\b', str(usrcmd)):
                                changevollevel=int(changevollevel)
                        else:
                            changevollevel=10
                        newvollevel= oldvollevel+ changevollevel
                        print(newvollevel)
                        if int(newvollevel)>100:
                            settingvollevel=100
                        elif int(newvollevel)<0:
                            settingvollevel=0
                        else:
                            settingvollevel=newvollevel
                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                            json.dump(settingvollevel, vol)
                        print('Setting volume to: '+str(settingvollevel))
                        vlcplayer.set_vlc_volume(int(settingvollevel))
                    if (custom_action_keyword['Dict']['Decrease']).lower() in str(usrcmd).lower() or 'reduce'.lower() in str(usrcmd).lower():
                        if any(char.isdigit() for char in str(usrcmd)):
                            for changevollevel in re.findall(r'\b\d+\b', str(usrcmd)):
                                changevollevel=int(changevollevel)
                        else:
                            changevollevel=10
                        newvollevel= oldvollevel - changevollevel
                        print(newvollevel)
                        if int(newvollevel)>100:
                            settingvollevel=100
                        elif int(newvollevel)<0:
                            settingvollevel=0
                        else:
                            settingvollevel=newvollevel
                        with open('{}/.mediavolume.json'.format(USER_PATH), 'w') as vol:
                            json.dump(settingvollevel, vol)
                        print('Setting volume to: '+str(settingvollevel))
                        vlcplayer.set_vlc_volume(int(settingvollevel))
                else:
                    say("Sorry I could not help you")
            else:
                say("Sorry nothing is playing right now")
        if (custom_action_keyword['Keywords']['Music_index_refresh'][0]).lower() in str(usrcmd).lower() and (custom_action_keyword['Keywords']['Music_index_refresh'][1]).lower() in str(usrcmd).lower():
            self.assistant.stop_conversation()
            refreshlists()
        if configuration['Gmusicapi']['Gmusic_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['Google_music_streaming'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                vlcplayer.stop_vlc()
                gmusicselect(str(usrcmd).lower())
        if configuration['Spotify']['Spotify_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['Spotify_music_streaming'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                vlcplayer.stop_vlc()
                if not Spotify_credentials:
                    say("Hey, you need to enter your spotify credentials in the config file first.")
                else:
                    spotify_playlist_select(str(usrcmd).lower())
        if configuration['Gaana']['Gaana_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['Gaana_music_streaming'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                vlcplayer.stop_vlc()
                gaana_playlist_select(str(usrcmd).lower())
        if configuration['Deezer']['Deezer_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['Deezer_music_streaming'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                vlcplayer.stop_vlc()
                deezer_playlist_select(str(usrcmd).lower())
        if configuration['Clickatell']['Clickatell_Control']=='Enabled':
            if (custom_action_keyword['Keywords']['Send_sms_clickatell'][0]).lower() in str(usrcmd).lower():
                self.assistant.stop_conversation()
                sendSMS(str(usrcmd).lower())
        if 'interpreter' in str(usrcmd).lower():
            self.assistant.stop_conversation()
            reqlang=str(usrcmd).lower()
            reqlang=reqlang.replace('stop','',1)
            reqlang=reqlang.replace('start','',1)
            reqlang=reqlang.replace('interpreter','',1)
            reqlang=reqlang.strip()
            for i in range(0,len(langlist['Languages'])):
                if str(langlist['Languages'][i]).lower()==reqlang:
                    self.interpcloudlang2=langlist['Languages'][i][0]
                    self.interpttslang2=langlist['Languages'][i][1]
                    if 'start' in str(usrcmd).lower():
                        self.interpreter_mode_trigger(reqlang,'Start')
                    else:
                        self.interpreter_mode_trigger(reqlang,'Stop')
                    break


    def main(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--device-model-id', '--device_model_id', type=str,
                            metavar='DEVICE_MODEL_ID', required=False,
                            help='the device model ID registered with Google')
        parser.add_argument('--project-id', '--project_id', type=str,
                            metavar='PROJECT_ID', required=False,
                            help='the project ID used to register this device')
        parser.add_argument('--nickname', type=str,
                        metavar='NICKNAME', required=False,
                        help='the nickname used to register this device')
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
        parser.add_argument('--query', type=str,
                        metavar='QUERY',
                        help='query to send as soon as the Assistant starts')
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
            if gender=='Male':
                subprocess.Popen(["aplay", "{}/sample-audio-files/Startup-Male.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.Popen(["aplay", "{}/sample-audio-files/Startup-Female.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            events = assistant.start()
            device_id = assistant.device_id
            print('device_model_id:', device_model_id)
            print('device_id:', device_id + '\n')

            # Re-register if "device_id" is different from the last "device_id":
            if should_register or (device_id != last_device_id):
                if args.project_id:
                    register_device(args.project_id, credentials,
                                    device_model_id, device_id, args.nickname)
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
                if event.type == EventType.ON_START_FINISHED and args.query:
                    assistant.send_text_query(args.query)
                self.process_event(event)

        if custom_wakeword:
            self.detector.terminate()


if __name__ == '__main__':
    try:
        Myassistant().main()
    except Exception as error:
        logger.exception(error)
