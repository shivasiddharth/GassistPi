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

"""Sample that implements a gRPC client for the Google Assistant API."""

import concurrent.futures
import json
import logging
import os
import os.path
import pathlib2 as pathlib
import sys
import time
import uuid
try:
    import RPi.GPIO as GPIO
except Exception as e:
    GPIO = None
import argparse
import subprocess
import click
import grpc
import psutil
import logging
import re
import requests
import random
from actions import say
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials
from kodijson import Kodi, PLAYER_VIDEO
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
import snowboydecoder
import signal
from threading import Thread
if GPIO!=None:
    from indicator import assistantindicator
    from indicator import stoppushbutton
    GPIOcontrol=True
else:
    GPIOcontrol=False
from actions import Domoticz_Device_Control
from actions import domoticz_control
from actions import domoticz_devices
from actions import gaana_playlist_select
from actions import deezer_playlist_select
from actions import gender

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)
from tenacity import retry, stop_after_attempt, retry_if_exception

try:
    from googlesamples.assistant.grpc import (
        assistant_helpers,
        audio_helpers,
        browser_helpers,
        device_helpers
    )
except (SystemError, ImportError):
    import assistant_helpers
    import audio_helpers
    import browser_helpers
    import device_helpers

# logging.basicConfig(filename='/tmp/GassistPi.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s %(name)s %(message)s')
# logger=logging.getLogger(__name__)

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

ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))

if GPIOcontrol:
    #GPIO Declarations
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    pushbuttontrigger=configuration['Gpios']['pushbutton_trigger'][0]
    GPIO.setup(pushbuttontrigger, GPIO.IN, pull_up_down = GPIO.PUD_UP)


#Sonoff-Tasmota Declarations
#Make sure that the device name assigned here does not overlap any of your smart device names in the google home app
tasmota_devicelist=configuration['Tasmota_devicelist']['friendly-names']
tasmota_deviceip=configuration['Tasmota_devicelist']['ipaddresses']

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


ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE
PLAYING = embedded_assistant_pb2.ScreenOutConfig.PLAYING
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5



#Function to control Sonoff Tasmota Devices
def tasmota_control(phrase,devname,devip):
    if custom_action_keyword['Dict']['On'] in phrase:
        try:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power%20on")
            say("Tunring on "+devname)
        except requests.exceptions.ConnectionError:
            say("Device not online")
    elif custom_action_keyword['Dict']['Off'] in phrase:
        try:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power%20off")
            say("Tunring off "+devname)
        except requests.exceptions.ConnectionError:
            say("Device not online")

#Check if custom wakeword has been enabled
if configuration['Wakewords']['Custom_Wakeword']=='Enabled':
    custom_wakeword=True
elif GPIOcontrol==False:
    print("Pushbutton trigger is not configured. So forcing custom wakeword ON.")
    custom_wakeword=True
else:
    custom_wakeword=False

models=configuration['Wakewords']['Custom_wakeword_models']
interrupted=False
def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted


mediastopbutton=True

#Custom Conversation
numques=len(configuration['Conversation']['question'])
numans=len(configuration['Conversation']['answer'])

class SampleAssistant(object):
    """Sample Assistant that supports conversations and device actions.

    Args:
      device_model_id: identifier of the device model.
      device_id: identifier of the registered device instance.
      conversation_stream(ConversationStream): audio stream
        for recording query and playing back assistant answer.
      channel: authorized gRPC channel for connection to the
        Google Assistant API.
      deadline_sec: gRPC deadline in seconds for Google Assistant API call.
      device_handler: callback for device actions.
    """

    def __init__(self, language_code, device_model_id, device_id,
                 conversation_stream, display,
                 channel, deadline_sec, device_handler):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.conversation_stream = conversation_stream
        self.display = display
        if GPIOcontrol:
            self.t3 = Thread(target=self.stopbutton)
            self.t3.start()
        # Opaque blob provided in AssistResponse that,
        # when provided in a follow-up AssistRequest,
        # gives the Assistant a context marker within the current state
        # of the multi-Assist()-RPC "conversation".
        # This value, along with MicrophoneMode, supports a more natural
        # "conversation" with the Assistant.
        self.conversation_state = None
        # Force reset of first conversation.
        self.is_new_conversation = True

        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
            channel
        )
        self.deadline = deadline_sec

        self.device_handler = device_handler

    def stopbutton(self):
        if GPIOcontrol:
            while mediastopbutton:
                time.sleep(0.25)
                if not GPIO.input(stoppushbutton):
                    print('Stopped')
                    stop()

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            return False
        self.conversation_stream.close()

    def is_grpc_error_unavailable(e):
        is_grpc_error = isinstance(e, grpc.RpcError)
        if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
            logging.error('grpc unavailable error: %s', e)
            return True
        return False

    @retry(reraise=True, stop=stop_after_attempt(3),
           retry=retry_if_exception(is_grpc_error_unavailable))
    def assist(self):
        """Send a voice request to the Assistant and playback the response.

        Returns: True if conversation should continue.
        """
        continue_conversation = False
        device_actions_futures = []
        subprocess.Popen(["aplay", "{}/sample-audio-files/Fb.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.conversation_stream.start_recording()
        if kodicontrol:
            try:
                status=mutevolstatus()
                vollevel=status[1]
                with open('{}/.volume.json'.format(USER_PATH), 'w') as f:
                       json.dump(vollevel, f)
                kodi.Application.SetVolume({"volume": 0})
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

        logging.info('Recording audio request.')

        def iter_log_assist_requests():
            for c in self.gen_assist_requests():
                assistant_helpers.log_assist_request_without_audio(c)
                yield c
            logging.debug('Reached end of AssistRequest iteration.')

        # This generator yields AssistResponse proto messages
        # received from the gRPC Google Assistant API.
        for resp in self.assistant.Assist(iter_log_assist_requests(),
                                          self.deadline):
            assistant_helpers.log_assist_response_without_audio(resp)
            if resp.event_type == END_OF_UTTERANCE:
                logging.info('End of audio request detected.')
                logging.info('Stopping recording.')
                self.conversation_stream.stop_recording()
            if resp.speech_results:
                logging.info('Transcript of user request: "%s".',
                             ' '.join(r.transcript
                                      for r in resp.speech_results))
                for r in resp.speech_results:
                    usercommand=str(r)

                if "stability: 1.0" in usercommand.lower():
                    usrcmd=str(usercommand).lower()
                    idx=usrcmd.find('stability')
                    usrcmd=usrcmd[:idx]
                    usrcmd=usrcmd.replace("stability","",1)
                    usrcmd=usrcmd.strip()
                    usrcmd=usrcmd.replace('transcript: "','',1)
                    usrcmd=usrcmd.replace('"','',1)
                    usrcmd=usrcmd.strip()
                    print(str(usrcmd))
                    if configuration['DIYHUE']['DIYHUE_Control']=='Enabled':
                        if os.path.isfile('/opt/hue-emulator/config.json'):
                            with open('/opt/hue-emulator/config.json', 'r') as config:
                                 hueconfig = json.load(config)
                            for i in range(1,len(hueconfig['lights'])+1):
                                try:
                                    if str(hueconfig['lights'][str(i)]['name']).lower() in str(usrcmd).lower():
                                        hue_control(str(usrcmd).lower(),str(i),str(hueconfig['lights_address'][str(i)]['ip']))
                                        return continue_conversation
                                        break
                                except Keyerror:
                                    say('Unable to help, please check your config file')
                    if configuration['Tasmota_devicelist']['Tasmota_Control']=='Enabled':
                        for num, name in enumerate(tasmota_devicelist):
                            if name.lower() in str(usrcmd).lower():
                                tasmota_control(str(usrcmd).lower(), name.lower(),tasmota_deviceip[num])
                                return continue_conversation
                                break
                    if configuration['Conversation']['Conversation_Control']=='Enabled':
                        for i in range(1,numques+1):
                            try:
                                if str(configuration['Conversation']['question'][i][0]).lower() in str(usrcmd).lower():
                                    selectedans=random.sample(configuration['Conversation']['answer'][i],1)
                                    say(selectedans[0])
                                    return continue_conversation
                                    break
                            except Keyerror:
                                say('Please check if the number of questions matches the number of answers')
                    if Domoticz_Device_Control==True and len(domoticz_devices['result'])>0:
                        for i in range(0,len(domoticz_devices['result'])):
                            if str(domoticz_devices['result'][i]['HardwareName']).lower() in str(usrcmd).lower():
                                domoticz_control(i,str(usrcmd).lower(),domoticz_devices['result'][i]['idx'],domoticz_devices['result'][i]['HardwareName'])
                                return continue_conversation
                                break
                    if (custom_action_keyword['Keywords']['Magic_mirror'][0]).lower() in str(usrcmd).lower():
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
                        return continue_conversation
                    if (custom_action_keyword['Keywords']['Recipe_pushbullet'][0]).lower() in str(usrcmd).lower():
                        ingrequest=str(usrcmd).lower()
                        ingredientsidx=ingrequest.find('for')
                        ingrequest=ingrequest[ingredientsidx:]
                        ingrequest=ingrequest.replace('for',"",1)
                        ingrequest=ingrequest.replace("'}","",1)
                        ingrequest=ingrequest.strip()
                        ingrequest=ingrequest.replace(" ","%20",1)
                        getrecipe(ingrequest)
                        return continue_conversation
                    if (custom_action_keyword['Keywords']['Kickstarter_tracking'][0]).lower() in str(usrcmd).lower():
                        kickstarter_tracker(str(usrcmd).lower())
                        return continue_conversation
                    if configuration['Raspberrypi_GPIO_Control']['GPIO_Control']=='Enabled':
                        if (custom_action_keyword['Keywords']['Pi_GPIO_control'][0]).lower() in str(usrcmd).lower():
                            Action(str(usrcmd).lower())
                            return continue_conversation
                    if configuration['YouTube']['YouTube_Control']=='Enabled':
                        if (custom_action_keyword['Keywords']['YouTube_music_stream'][0]).lower() in str(usrcmd).lower():
                            vlcplayer.stop_vlc()
                            if 'autoplay'.lower() in str(usrcmd).lower():
                                YouTube_Autoplay(str(usrcmd).lower())
                            else:
                                YouTube_No_Autoplay(str(usrcmd).lower())
                            return continue_conversation
                    if (custom_action_keyword['Keywords']['Stop_music'][0]).lower() in str(usrcmd).lower():
                        stop()
                    if configuration['Radio_stations']['Radio_Control']=='Enabled':
                        if 'radio'.lower() in str(usrcmd).lower():
                            radio(str(usrcmd).lower())
                            return continue_conversation
                    if configuration['ESP']['ESP_Control']=='Enabled':
                        if (custom_action_keyword['Keywords']['ESP_control'][0]).lower() in str(usrcmd).lower():
                            ESP(str(usrcmd).lower())
                            return continue_conversation

                    if (custom_action_keyword['Keywords']['Parcel_tracking'][0]).lower() in str(usrcmd).lower():
                        track()
                        return continue_conversation
                    if (custom_action_keyword['Keywords']['RSS'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['RSS'][1]).lower() in str(usrcmd).lower():
                        feed(str(usrcmd).lower())
                        return continue_conversation
                    if kodicontrol:
                        try:
                            if (custom_action_keyword['Keywords']['Kodi_actions'][0]).lower() in str(usrcmd).lower():
                                kodiactions(str(usrcmd).lower())
                        except requests.exceptions.ConnectionError:
                            say("Kodi TV box not online")
                        return continue_conversation
                    # Google Assistant now comes built in with chromecast control, so custom function has been commented
                    # if 'chromecast'.lower() in str(usrcmd).lower():
                    #     if 'play'.lower() in str(usrcmd).lower():
                    #         chromecast_play_video(str(usrcmd).lower())
                    #     else:
                    #         chromecast_control(usrcmd)
                    #     return continue_conversation
                    if (custom_action_keyword['Keywords']['Pause_resume'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Pause_resume'][1]).lower() in str(usrcmd).lower():
                        if vlcplayer.is_vlc_playing():
                            if (custom_action_keyword['Keywords']['Pause_resume'][0]).lower() in str(usrcmd).lower():
                                vlcplayer.pause_vlc()
                        if checkvlcpaused():
                            if (custom_action_keyword['Keywords']['Pause_resume'][1]).lower() in str(usrcmd).lower():
                                vlcplayer.play_vlc()
                        elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                            say("Sorry nothing is playing right now")
                        return continue_conversation
                    if (custom_action_keyword['Keywords']['Track_change']['Next'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Next'][1]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Next'][2]).lower() in str(usrcmd).lower():
                        if vlcplayer.is_vlc_playing() or checkvlcpaused()==True:
                            vlcplayer.stop_vlc()
                            vlcplayer.change_media_next()
                        elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                            say("Sorry nothing is playing right now")
                        return continue_conversation
                    if (custom_action_keyword['Keywords']['Track_change']['Previous'][0]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Previous'][1]).lower() in str(usrcmd).lower() or (custom_action_keyword['Keywords']['Track_change']['Previous'][2]).lower() in str(usrcmd).lower():
                        if vlcplayer.is_vlc_playing() or checkvlcpaused()==True:
                            vlcplayer.stop_vlc()
                            vlcplayer.change_media_previous()
                        elif vlcplayer.is_vlc_playing()==False and checkvlcpaused()==False:
                            say("Sorry nothing is playing right now")
                        return continue_conversation
                    if (custom_action_keyword['Keywords']['VLC_music_volume'][0]).lower() in str(usrcmd).lower():
                        if vlcplayer.is_vlc_playing()==True or checkvlcpaused()==True:
                            if (custom_action_keyword['Dict']['Set']).lower() in str(usrcmd).lower() or custom_action_keyword['Dict']['Change'].lower() in str(usrcmd).lower():
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
                            elif custom_action_keyword['Dict']['Increase'].lower() in str(usrcmd).lower() or custom_action_keyword['Dict']['Decrease'].lower() in str(usrcmd).lower() or 'reduce'.lower() in str(usrcmd).lower():
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
                                if custom_action_keyword['Dict']['Increase'].lower() in str(usrcmd).lower():
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
                                if custom_action_keyword['Dict']['Decrease'].lower() in str(usrcmd).lower() or 'reduce'.lower() in str(usrcmd).lower():
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
                        return continue_conversation
                    if (custom_action_keyword['Keywords']['Music_index_refresh'][0]).lower() in str(usrcmd).lower() and (custom_action_keyword['Keywords']['Music_index_refresh'][1]).lower() in str(usrcmd).lower():
                        refreshlists()
                        return continue_conversation
                    if configuration['Gmusicapi']['Gmusic_Control']=='Enabled':
                        if (custom_action_keyword['Keywords']['Google_music_streaming'][0]).lower() in str(usrcmd).lower():
                            vlcplayer.stop_vlc()
                            gmusicselect(str(usrcmd).lower())
                            return continue_conversation
                    if configuration['Spotify']['Spotify_Control']=='Enabled':
                        if (custom_action_keyword['Keywords']['Spotify_music_streaming'][0]).lower() in str(usrcmd).lower():
                            vlcplayer.stop_vlc()
                            spotify_playlist_select(str(usrcmd).lower())
                            return continue_conversation
                    if configuration['Gaana']['Gaana_Control']=='Enabled':
                        if (custom_action_keyword['Keywords']['Gaana_music_streaming'][0]).lower() in str(usrcmd).lower():
                            vlcplayer.stop_vlc()
                            gaana_playlist_select(str(usrcmd).lower())
                            return continue_conversation
                    if configuration['Deezer']['Deezer_Control']=='Enabled':
                        if (custom_action_keyword['Keywords']['Deezer_music_streaming'][0]).lower() in str(usrcmd).lower():
                            vlcplayer.stop_vlc()
                            deezer_playlist_select(str(usrcmd).lower())
                            return continue_conversation
                    else:
                        continue
                if GPIOcontrol:
                    assistantindicator('speaking')

            if len(resp.audio_out.audio_data) > 0:
                if not self.conversation_stream.playing:
                    self.conversation_stream.stop_recording()
                    self.conversation_stream.start_playback()
                    logging.info('Playing assistant response.')
                self.conversation_stream.write(resp.audio_out.audio_data)
            if resp.dialog_state_out.conversation_state:
                conversation_state = resp.dialog_state_out.conversation_state
                logging.debug('Updating conversation state.')
                self.conversation_state = conversation_state
            if resp.dialog_state_out.volume_percentage != 0:
                volume_percentage = resp.dialog_state_out.volume_percentage
                logging.info('Setting volume to %s%%', volume_percentage)
                self.conversation_stream.volume_percentage = volume_percentage
            if resp.dialog_state_out.microphone_mode == DIALOG_FOLLOW_ON:
                continue_conversation = True
                if GPIOcontrol:
                    assistantindicator('listening')
                logging.info('Expecting follow-on query from user.')
            elif resp.dialog_state_out.microphone_mode == CLOSE_MICROPHONE:
                if GPIOcontrol:
                    assistantindicator('off')
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
                continue_conversation = False
            if resp.device_action.device_request_json:
                device_request = json.loads(
                    resp.device_action.device_request_json
                )
                fs = self.device_handler(device_request)
                if fs:
                    device_actions_futures.extend(fs)
            if self.display and resp.screen_out.data:
                system_browser = browser_helpers.system_browser
                system_browser.display(resp.screen_out.data)

        if len(device_actions_futures):
            logging.info('Waiting for device executions to complete.')
            concurrent.futures.wait(device_actions_futures)

        logging.info('Finished playing assistant response.')
        self.conversation_stream.stop_playback()
        return continue_conversation
        if GPIOcontrol:
            assistantindicator('off')
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


    def gen_assist_requests(self):
        """Yields: AssistRequest messages to send to the API."""

        config = embedded_assistant_pb2.AssistConfig(
            audio_in_config=embedded_assistant_pb2.AudioInConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
            ),
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
                volume_percentage=self.conversation_stream.volume_percentage,
            ),
            dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                language_code=self.language_code,
                conversation_state=self.conversation_state,
                is_new_conversation=self.is_new_conversation,
            ),
            device_config=embedded_assistant_pb2.DeviceConfig(
                device_id=self.device_id,
                device_model_id=self.device_model_id,
            )
        )
        if self.display:
            config.screen_out_config.screen_mode = PLAYING
        # Continue current conversation with later requests.
        self.is_new_conversation = False
        # The first AssistRequest must contain the AssistConfig
        # and no audio data.
        yield embedded_assistant_pb2.AssistRequest(config=config)
        for data in self.conversation_stream:
            # Subsequent requests need audio data, but not config.
            yield embedded_assistant_pb2.AssistRequest(audio_in=data)


@click.command()
@click.option('--api-endpoint', default=ASSISTANT_API_ENDPOINT,
              metavar='<api endpoint>', show_default=True,
              help='Address of Google Assistant API service.')
@click.option('--credentials',
              metavar='<credentials>', show_default=True,
              default=os.path.join(click.get_app_dir('google-oauthlib-tool'),
                                   'credentials.json'),
              help='Path to read OAuth2 credentials.')
@click.option('--project-id',
              metavar='<project id>',
              help=('Google Developer Project ID used for registration '
                    'if --device-id is not specified'))
@click.option('--device-model-id',
              metavar='<device model id>',
              help=(('Unique device model identifier, '
                     'if not specifed, it is read from --device-config')))
@click.option('--device-id',
              metavar='<device id>',
              help=(('Unique registered device instance identifier, '
                     'if not specified, it is read from --device-config, '
                     'if no device_config found: a new device is registered '
                     'using a unique id and a new device config is saved')))
@click.option('--device-config', show_default=True,
              metavar='<device config>',
              default=os.path.join(
                  click.get_app_dir('googlesamples-assistant'),
                  'device_config.json'),
              help='Path to save and restore the device configuration')
@click.option('--lang', show_default=True,
              metavar='<language code>',
              default='en-US',
              help='Language code of the Assistant')
@click.option('--display', is_flag=True, default=False,
              help='Enable visual display of Assistant responses in HTML.')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Verbose logging.')
@click.option('--input-audio-file', '-i',
              metavar='<input file>',
              help='Path to input audio file. '
              'If missing, uses audio capture')
@click.option('--output-audio-file', '-o',
              metavar='<output file>',
              help='Path to output audio file. '
              'If missing, uses audio playback')
@click.option('--audio-sample-rate',
              default=audio_helpers.DEFAULT_AUDIO_SAMPLE_RATE,
              metavar='<audio sample rate>', show_default=True,
              help='Audio sample rate in hertz.')
@click.option('--audio-sample-width',
              default=audio_helpers.DEFAULT_AUDIO_SAMPLE_WIDTH,
              metavar='<audio sample width>', show_default=True,
              help='Audio sample width in bytes.')
@click.option('--audio-iter-size',
              default=audio_helpers.DEFAULT_AUDIO_ITER_SIZE,
              metavar='<audio iter size>', show_default=True,
              help='Size of each read during audio stream iteration in bytes.')
@click.option('--audio-block-size',
              default=audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE,
              metavar='<audio block size>', show_default=True,
              help=('Block size in bytes for each audio device '
                    'read and write operation.'))
@click.option('--audio-flush-size',
              default=audio_helpers.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE,
              metavar='<audio flush size>', show_default=True,
              help=('Size of silence data in bytes written '
                    'during flush operation'))
@click.option('--grpc-deadline', default=DEFAULT_GRPC_DEADLINE,
              metavar='<grpc deadline>', show_default=True,
              help='gRPC deadline in seconds')
@click.option('--once', default=False, is_flag=True,
              help='Force termination after a single conversation.')
def main(api_endpoint, credentials, project_id,
         device_model_id, device_id, device_config,
         lang, display, verbose,
         input_audio_file, output_audio_file,
         audio_sample_rate, audio_sample_width,
         audio_iter_size, audio_block_size, audio_flush_size,
         grpc_deadline, once, *args, **kwargs):
    """Samples for the Google Assistant API.

    Examples:
      Run the sample with microphone input and speaker output:

        $ python -m googlesamples.assistant

      Run the sample with file input and speaker output:

        $ python -m googlesamples.assistant -i <input file>

      Run the sample with file input and output:

        $ python -m googlesamples.assistant -i <input file> -o <output file>
    """
    if gender=='Male':
        subprocess.Popen(["aplay", "{}/sample-audio-files/Startup-Male.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        subprocess.Popen(["aplay", "{}/sample-audio-files/Startup-Female.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Setup logging.
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    # Load OAuth 2.0 credentials.
    try:
        with open(credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
    except Exception as e:
        logging.error('Error loading credentials: %s', e)
        logging.error('Run google-oauthlib-tool to initialize '
                      'new OAuth 2.0 credentials.')
        sys.exit(-1)

    # Create an authorized gRPC channel.
    grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
        credentials, http_request, api_endpoint)
    logging.info('Connecting to %s', api_endpoint)

    # Configure audio source and sink.
    audio_device = None
    if input_audio_file:
        audio_source = audio_helpers.WaveSource(
            open(input_audio_file, 'rb'),
            sample_rate=audio_sample_rate,
            sample_width=audio_sample_width
        )
    else:
        audio_source = audio_device = (
            audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=audio_sample_rate,
                sample_width=audio_sample_width,
                block_size=audio_block_size,
                flush_size=audio_flush_size
            )
        )
    if output_audio_file:
        audio_sink = audio_helpers.WaveSink(
            open(output_audio_file, 'wb'),
            sample_rate=audio_sample_rate,
            sample_width=audio_sample_width
        )
    else:
        audio_sink = audio_device = (
            audio_device or audio_helpers.SoundDeviceStream(
                sample_rate=audio_sample_rate,
                sample_width=audio_sample_width,
                block_size=audio_block_size,
                flush_size=audio_flush_size
            )
        )
    # Create conversation stream with the given audio source and sink.
    conversation_stream = audio_helpers.ConversationStream(
        source=audio_source,
        sink=audio_sink,
        iter_size=audio_iter_size,
        sample_width=audio_sample_width,
    )

    if not device_id or not device_model_id:
        try:
            with open(device_config) as f:
                device = json.load(f)
                device_id = device['id']
                device_model_id = device['model_id']
                logging.info("Using device model %s and device id %s",
                             device_model_id,
                             device_id)
        except Exception as e:
            logging.warning('Device config not found: %s' % e)
            logging.info('Registering device')
            if not device_model_id:
                logging.error('Option --device-model-id required '
                              'when registering a device instance.')
                sys.exit(-1)
            if not project_id:
                logging.error('Option --project-id required '
                              'when registering a device instance.')
                sys.exit(-1)
            device_base_url = (
                'https://%s/v1alpha2/projects/%s/devices' % (api_endpoint,
                                                             project_id)
            )
            device_id = str(uuid.uuid1())
            payload = {
                'id': device_id,
                'model_id': device_model_id,
                'client_type': 'SDK_SERVICE'
            }
            session = google.auth.transport.requests.AuthorizedSession(
                credentials
            )
            r = session.post(device_base_url, data=json.dumps(payload))
            if r.status_code != 200:
                logging.error('Failed to register device: %s', r.text)
                sys.exit(-1)
            logging.info('Device registered: %s', device_id)
            pathlib.Path(os.path.dirname(device_config)).mkdir(exist_ok=True)
            with open(device_config, 'w') as f:
                json.dump(payload, f)

    device_handler = device_helpers.DeviceRequestHandler(device_id)

    @device_handler.command('action.devices.commands.OnOff')
    def onoff(on):
        if on:
            logging.info('Turning device on')
        else:
            logging.info('Turning device off')



    @device_handler.command('com.example.commands.BlinkLight')
    def blink(speed, number):
        logging.info('Blinking device %s times.' % number)
        delay = 1
        if speed == "slowly":
            delay = 2
        elif speed == "quickly":
            delay = 0.5
        for i in range(int(number)):
            logging.info('Device is blinking.')
            time.sleep(delay)

    with SampleAssistant(lang, device_model_id, device_id,
                         conversation_stream, display,
                         grpc_channel, grpc_deadline,
                         device_handler) as assistant:
        # If file arguments are supplied:
        # exit after the first turn of the conversation.
        if input_audio_file or output_audio_file:
            assistant.assist()
            return

        def detected():
            continue_conversation=assistant.assist()
            if continue_conversation:
                print('Continuing conversation')
                assistant.assist()

        signal.signal(signal.SIGINT, signal_handler)
        sensitivity = [0.5]*len(models)
        callbacks = [detected]*len(models)
        detector = snowboydecoder.HotwordDetector(models, sensitivity=sensitivity)
        def start_detector():
            detector.start(detected_callback=callbacks,
                                   interrupt_check=interrupt_callback,
                                   sleep_time=0.03)

        # If no file arguments supplied:
        # keep recording voice requests using the microphone
        # and playing back assistant response using the speaker.
        # When the once flag is set, don't wait for a trigger. Otherwise, wait.

        wait_for_user_trigger = not once
        while True:
            if wait_for_user_trigger:
                if custom_wakeword:
                    start_detector()
                else:
                    button_state=GPIO.input(pushbuttontrigger)
                    if button_state==True:
                       continue
                    else:
                       pass
            continue_conversation = assistant.assist()
            # wait for user trigger if there is no follow-up turn in
            # the conversation.
            wait_for_user_trigger = not continue_conversation

            # If we only want one conversation, break.
            if once and (not continue_conversation):
                break



    detector.terminate()

if __name__ == '__main__':
    main()
