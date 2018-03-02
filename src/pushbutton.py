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
import sys
import uuid
import RPi.GPIO as GPIO
import argparse
import subprocess
import click
import grpc
import time
import psutil
import logging
import re
import requests
import pathlib2 as pathlib
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

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)
from tenacity import retry, stop_after_attempt, retry_if_exception

try:
    from googlesamples.assistant.grpc import (
        assistant_helpers,
        audio_helpers,
        device_helpers
    )
except SystemError:
    import assistant_helpers
    import audio_helpers
    import device_helpers

logging.basicConfig(filename='/tmp/GassistPi.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

#Login with default kodi/kodi credentials
#kodi = Kodi("http://localhost:8080/jsonrpc")

#Login with custom credentials
# Kodi("http://IP-ADDRESS-OF-KODI:8080/jsonrpc", "username", "password")
kodi = Kodi("http://192.168.1.15:8080/jsonrpc", "kodi", "kodi")

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Trigger Pin
GPIO.setup(22, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#Indicator Pins
GPIO.setup(25, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.setup(6, GPIO.OUT)
GPIO.output(5, GPIO.LOW)
GPIO.output(6, GPIO.LOW)
led=GPIO.PWM(25,1)
led.start(0)

mpvactive=False

#Sonoff-Tasmota Declarations
#Make sure that the device name assigned here does not overlap any of your smart device names in the google home app
tasmota_devicelist=['Desk Lamp','Table Lamp']
tasmota_deviceip=['192.168.1.35','192.168.1.36']

#Magic Mirror Remote Control Declarations
mmmip='ENTER_YOUR_MAGIC_MIRROR_IP'

ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5

#Function to check if mpv is playing
def ismpvplaying():
    for pid in psutil.pids():
        p=psutil.Process(pid)
        if 'mpv'in p.name():
            mpvactive=True
            break
        else:
            mpvactive=False
    return mpvactive


#Function to control Sonoff Tasmota Devices
def tasmota_control(phrase,devname,devip):
    if 'on' in phrase:
        try:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power%20on")
            say("Tunring on "+devname)
        except requests.exceptions.ConnectionError:
            say("Device not online")
    elif 'off' in phrase:
        try:
            rq=requests.head("http://"+devip+"/cm?cmnd=Power%20off")
            say("Tunring off "+devname)
        except requests.exceptions.ConnectionError:
            say("Device not online")


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
                 conversation_stream,
                 channel, deadline_sec, device_handler):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.conversation_stream = conversation_stream

        # Opaque blob provided in AssistResponse that,
        # when provided in a follow-up AssistRequest,
        # gives the Assistant a context marker within the current state
        # of the multi-Assist()-RPC "conversation".
        # This value, along with MicrophoneMode, supports a more natural
        # "conversation" with the Assistant.
        self.conversation_state = None

        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
            channel
        )
        self.deadline = deadline_sec

        self.device_handler = device_handler

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
        subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Fb.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.conversation_stream.start_recording()
        #Uncomment the following after starting the Kodi
        #status=mutevolstatus()
        #vollevel=status[1]
        #with open('/home/pi/.volume.json', 'w') as f:
               #json.dump(vollevel, f)
        #kodi.Application.SetVolume({"volume": 0})
        GPIO.output(5,GPIO.HIGH)
        led.ChangeDutyCycle(100)
        if ismpvplaying():
            if os.path.isfile("/home/pi/.mediavolume.json"):
                mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume","10"]})+"' | socat - /tmp/mpvsocket")
            else:
                mpvgetvol=subprocess.Popen([("echo '"+json.dumps({ "command": ["get_property", "volume"]})+"' | socat - /tmp/mpvsocket")],shell=True, stdout=subprocess.PIPE)
                output=mpvgetvol.communicate()[0]
                for currntvol in re.findall(r"[-+]?\d*\.\d+|\d+", str(output)):
                    with open('/home/pi/.mediavolume.json', 'w') as vol:
                        json.dump(currntvol, vol)
                mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume","10"]})+"' | socat - /tmp/mpvsocket")

        logging.info('Recording audio request.')

        def iter_assist_requests():
            for c in self.gen_assist_requests():
                assistant_helpers.log_assist_request_without_audio(c)
                yield c
            self.conversation_stream.start_playback()

        # This generator yields AssistResponse proto messages
        # received from the gRPC Google Assistant API.
        for resp in self.assistant.Assist(iter_assist_requests(),
                                          self.deadline):
            assistant_helpers.log_assist_response_without_audio(resp)
            if resp.event_type == END_OF_UTTERANCE:
                logging.info('End of audio request detected')
                GPIO.output(5,GPIO.LOW)
                led.ChangeDutyCycle(0)
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
                    for num, name in enumerate(tasmota_devicelist):
                        if name.lower() in str(usrcmd).lower():
                            tasmota_control(str(usrcmd).lower(), name.lower(),tasmota_deviceip[num])
                            return continue_conversation
                            break
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

                    if 'magic mirror'.lower() in str(usrcmd).lower():
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
                    if 'ingredients'.lower() in str(usrcmd).lower():
                        assistant.stop_conversation()
                        ingrequest=str(usrcmd).lower()
                        ingredientsidx=ingrequest.find('for')
                        ingrequest=ingrequest[ingredientsidx:]
                        ingrequest=ingrequest.replace('for',"",1)
                        ingrequest=ingrequest.replace("'}","",1)
                        ingrequest=ingrequest.strip()
                        ingrequest=ingrequest.replace(" ","%20",1)
                        getrecipe(ingrequest)
                    if 'kickstarter'.lower() in str(usrcmd).lower():
                        assistant.stop_conversation()
                        kickstarter_tracker(str(usrcmd).lower())
                    if 'trigger'.lower() in str(usrcmd).lower():
                        Action(str(usrcmd).lower())
                        return continue_conversation
                    if 'stream'.lower() in str(usrcmd).lower():
                        os.system('pkill mpv')
                        if os.path.isfile("/home/pi/GassistPi/src/trackchange.py"):
                            os.system('rm /home/pi/GassistPi/src/trackchange.py')
                            os.system('echo "from actions import youtubeplayer\n\n" >> /home/pi/GassistPi/src/trackchange.py')
                            os.system('echo "youtubeplayer()\n" >> /home/pi/GassistPi/src/trackchange.py')
                            if 'autoplay'.lower() in str(usrcmd).lower():
                                YouTube_Autoplay(str(usrcmd).lower())
                            else:
                                YouTube_No_Autoplay(str(usrcmd).lower())
                        else:
                            os.system('echo "from actions import youtubeplayer\n\n" >> /home/pi/GassistPi/src/trackchange.py')
                            os.system('echo "youtubeplayer()\n" >> /home/pi/GassistPi/src/trackchange.py')
                            if 'autoplay'.lower() in str(usrcmd).lower():
                                YouTube_Autoplay(str(usrcmd).lower())
                            else:
                                YouTube_No_Autoplay(str(usrcmd).lower())
                        return continue_conversation
                    if 'stop'.lower() in str(usrcmd).lower():
                        stop()
                        return continue_conversation
                    if 'radio'.lower() in str(usrcmd).lower():
                        radio(str(usrcmd).lower())
                        return continue_conversation
                    if 'wireless'.lower() in str(usrcmd).lower():
                        ESP(str(usrcmd).lower())
                        return continue_conversation
                    if 'parcel'.lower() in str(usrcmd).lower():
                        track()
                        return continue_conversation
                    if 'news'.lower() in str(usrcmd).lower() or 'feed'.lower() in str(usrcmd).lower() or 'quote'.lower() in str(usrcmd).lower():
                        feed(str(usrcmd).lower())
                        return continue_conversation
                    if 'on kodi'.lower() in str(usrcmd).lower():
                        kodiactions(str(usrcmd).lower())
                        return continue_conversation
                    if 'chromecast'.lower() in str(usrcmd).lower():
                        if 'play'.lower() in str(usrcmd).lower():
                            chromecast_play_video(str(usrcmd).lower())
                        else:
                            chromecast_control(usrcmd)
                        return continue_conversation
                    if 'pause music'.lower() in str(usrcmd).lower() or 'resume music'.lower() in str(usrcmd).lower():
                        if ismpvplaying():
                            if 'pause music'.lower() in str(usrcmd).lower():
                                playstatus=os.system("echo '"+json.dumps({ "command": ["set_property", "pause", True]})+"' | socat - /tmp/mpvsocket")
                            elif 'resume music'.lower() in str(usrcmd).lower():
                                playstatus=os.system("echo '"+json.dumps({ "command": ["set_property", "pause", False]})+"' | socat - /tmp/mpvsocket")
                        else:
                            say("Sorry nothing is playing right now")
                        return continue_conversation
                    if 'music volume'.lower() in str(usrcmd).lower():
                        if ismpvplaying():
                            if 'set'.lower() in str(usrcmd).lower() or 'change'.lower() in str(usrcmd).lower():
                                if 'hundred'.lower() in str(usrcmd).lower() or 'maximum' in str(usrcmd).lower():
                                    settingvollevel=100
                                    with open('/home/pi/.mediavolume.json', 'w') as vol:
                                        json.dump(settingvollevel, vol)
                                    mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume",str(settingvollevel)]})+"' | socat - /tmp/mpvsocket")
                                elif 'zero'.lower() in str(usrcmd).lower() or 'minimum' in str(usrcmd).lower():
                                    settingvollevel=0
                                    with open('/home/pi/.mediavolume.json', 'w') as vol:
                                        json.dump(settingvollevel, vol)
                                    mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume",str(settingvollevel)]})+"' | socat - /tmp/mpvsocket")
                                else:
                                    for settingvollevel in re.findall(r"[-+]?\d*\.\d+|\d+", str(usrcmd)):
                                        with open('/home/pi/.mediavolume.json', 'w') as vol:
                                            json.dump(settingvollevel, vol)
                                    mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume",str(settingvollevel)]})+"' | socat - /tmp/mpvsocket")
                            elif 'increase'.lower() in str(usrcmd).lower() or 'decrease'.lower() in str(usrcmd).lower() or 'reduce'.lower() in str(usrcmd).lower():
                                if os.path.isfile("/home/pi/.mediavolume.json"):
                                    with open('/home/pi/.mediavolume.json', 'r') as vol:
                                        oldvollevel = json.load(vol)
                                        for oldvollevel in re.findall(r'\b\d+\b', str(oldvollevel)):
                                            oldvollevel=int(oldvollevel)
                                else:
                                    mpvgetvol=subprocess.Popen([("echo '"+json.dumps({ "command": ["get_property", "volume"]})+"' | socat - /tmp/mpvsocket")],shell=True, stdout=subprocess.PIPE)
                                    output=mpvgetvol.communicate()[0]
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
                                    if newvollevel>100:
                                        settingvollevel==100
                                    elif newvollevel<0:
                                        settingvollevel==0
                                    else:
                                        settingvollevel=newvollevel
                                    with open('/home/pi/.mediavolume.json', 'w') as vol:
                                        json.dump(settingvollevel, vol)
                                    mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume",str(settingvollevel)]})+"' | socat - /tmp/mpvsocket")
                                if 'decrease'.lower() in str(usrcmd).lower() or 'reduce'.lower() in str(usrcmd).lower():
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
                                    with open('/home/pi/.mediavolume.json', 'w') as vol:
                                        json.dump(settingvollevel, vol)
                                    mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume",str(settingvollevel)]})+"' | socat - /tmp/mpvsocket")
                            else:
                                say("Sorry I could not help you")
                        else:
                            say("Sorry nothing is playing right now")
                        return continue_conversation

                    if 'refresh'.lower() in str(usrcmd).lower() and 'music'.lower() in str(usrcmd).lower():
                        refreshlists()
                        return continue_conversation
                    if 'google music'.lower() in str(usrcmd).lower():
                        os.system('pkill mpv')
                        if os.path.isfile("/home/pi/GassistPi/src/trackchange.py"):
                            os.system('rm /home/pi/GassistPi/src/trackchange.py')
                            gmusicselect(str(usrcmd).lower())
                        else:
                            gmusicselect(str(usrcmd).lower())
                        return continue_conversation

                    else:
                        continue
                GPIO.output(5,GPIO.LOW)
                GPIO.output(6,GPIO.HIGH)
                led.ChangeDutyCycle(50)
                logging.info('Playing assistant response.')
            if len(resp.audio_out.audio_data) > 0:
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
                GPIO.output(6,GPIO.LOW)
                GPIO.output(5,GPIO.HIGH)
                led.ChangeDutyCycle(100)
                logging.info('Expecting follow-on query from user.')
            elif resp.dialog_state_out.microphone_mode == CLOSE_MICROPHONE:
                GPIO.output(6,GPIO.LOW)
                GPIO.output(5,GPIO.LOW)
                led.ChangeDutyCycle(0)
                if ismpvplaying():
                    if os.path.isfile("/home/pi/.mediavolume.json"):
                        with open('/home/pi/.mediavolume.json', 'r') as vol:
                            oldvollevel = json.load(vol)
                            print(oldvollevel)
                        mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume",str(oldvollevel)]})+"' | socat - /tmp/mpvsocket")

                #Uncomment the following, after starting Kodi
                #with open('/home/pi/.volume.json', 'r') as f:
                    #vollevel = json.load(f)
                    #kodi.Application.SetVolume({"volume": vollevel})
                continue_conversation = False
            if resp.device_action.device_request_json:
                device_request = json.loads(
                    resp.device_action.device_request_json
                )
                fs = self.device_handler(device_request)
                if fs:
                    device_actions_futures.extend(fs)

        if len(device_actions_futures):
            logging.info('Waiting for device executions to complete.')
            concurrent.futures.wait(device_actions_futures)

        logging.info('Finished playing assistant response.')
        self.conversation_stream.stop_playback()
        return continue_conversation

    def gen_assist_requests(self):
        """Yields: AssistRequest messages to send to the API."""

        dialog_state_in = embedded_assistant_pb2.DialogStateIn(
                language_code=self.language_code,
                conversation_state=b''
            )
        if self.conversation_state:
            logging.debug('Sending conversation state.')
            dialog_state_in.conversation_state = self.conversation_state
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
            dialog_state_in=dialog_state_in,
            device_config=embedded_assistant_pb2.DeviceConfig(
                device_id=self.device_id,
                device_model_id=self.device_model_id,
            )
        )
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
         device_model_id, device_id, device_config, lang, verbose,
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
    subprocess.Popen(["aplay", "/home/pi/GassistPi/sample-audio-files/Startup.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

    device_handler = device_helpers.DeviceRequestHandler(device_id)

    @device_handler.command('action.devices.commands.OnOff')
    def onoff(on):
        if on:
            logging.info('Turning device on')
        else:
            logging.info('Turning device off')

    if not device_id or not device_model_id:
        try:
            with open(device_config) as f:
                device = json.load(f)
                device_id = device['id']
                device_model_id = device['model_id']
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

    with SampleAssistant(lang, device_model_id, device_id,
                         conversation_stream,
                         grpc_channel, grpc_deadline,
                         device_handler) as assistant:
        # If file arguments are supplied:
        # exit after the first turn of the conversation.
        if input_audio_file or output_audio_file:
            assistant.assist()
            return

        # If no file arguments supplied:
        # keep recording voice requests using the microphone
        # and playing back assistant response using the speaker.
        # When the once flag is set, don't wait for a trigger. Otherwise, wait.
        wait_for_user_trigger = not once
        while True:
            if wait_for_user_trigger:
                button_state=GPIO.input(22)
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


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        logger.exception(error)
