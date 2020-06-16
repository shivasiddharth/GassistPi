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
import argparse
import json
import os.path
import pathlib2 as pathlib
import os
import subprocess
import requests
import time
import re
import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from google.assistant.library.device_helpers import register_device
import faulthandler
faulthandler.enable()

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

ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))

class Myassistant():

    def __init__(self):
        self.isplaying=False
        self.trackchange=False
        self.can_start_conversation=False
        self.assistant=None

    def check_volumio_status(self):
        try:
            output = subprocess.check_output("volumio status", shell=True)
            decodeoutput=output.decode("UTF-8")
            outputjs=json.loads(decodeoutput)
            status=outputjs["status"]
            if status=="stop" or status=="pause":
                self.isplaying=False
            elif status=="play":
                self.isplaying=True
        except KeyError:
            self.isplaying=False

    def volumiocontrol(self,volumiocommand):
        if "play music" in volumiocommand:
            self.assistant.stop_conversation()
            requests.get("http://localhost:3000/api/v1/commands/?cmd=play")
        if "pause music" in volumiocommand:
            self.isplaying=False
            self.assistant.stop_conversation()
            requests.get("http://localhost:3000/api/v1/commands/?cmd=pause")
        if "stop music" in volumiocommand:
            self.isplaying=False
            self.assistant.stop_conversation()
            requests.get("http://localhost:3000/api/v1/commands/?cmd=stop")
        if "next track" in volumiocommand or "next song" in volumiocommand:
            if self.isplaying:
                self.trackchange=True
                self.assistant.stop_conversation()
                requests.get("http://localhost:3000/api/v1/commands/?cmd=play")
                time.sleep(5)
                requests.get("http://localhost:3000/api/v1/commands/?cmd=next")
            else:
                print("Nothing is playing")
        if "previous track" in volumiocommand or "previous song" in volumiocommand:
            if self.isplaying:
                self.trackchange=True
                self.assistant.stop_conversation()
                requests.get("http://localhost:3000/api/v1/commands/?cmd=play")
                time.sleep(5)
                requests.get("http://localhost:3000/api/v1/commands/?cmd=prev")
            else:
                print("Nothing is playing")
        if "speaker volume" in volumiocommand:
            self.assistant.stop_conversation()
            if "hundred" in volumiocommand or "maximum" in volumiocommand:
                settingvollevel=100
                requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume=100")
            elif "zero" in volumiocommand or "minimum" in volumiocommand:
                settingvollevel=0
                requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume=0")
            else:
                for vollevel in re.findall(r"[-+]?\d*\.\d+|\d+", volumiocommand):
                    settingvollevel=vollevel
                requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume="+str(settingvollevel))

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

        if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            self.check_volumio_status()
            if self.isplaying:
                requests.get("http://localhost:3000/api/v1/commands/?cmd=pause")
            subprocess.Popen(["aplay", "{}/sample-audio-files/Fb.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.can_start_conversation = False

        if (event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT or event.type == EventType.ON_NO_RESPONSE):
            self.can_start_conversation = True

        if (event.type == EventType.ON_RESPONDING_STARTED and event.args and not event.args['is_error_response']):
            print(event.args)

        if event.type == EventType.ON_RESPONDING_FINISHED:
            print(event.args)

        if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
            usrcmd=event.args["text"]
            self.volumiocontrol(str(usrcmd).lower())

        if event.type == EventType.ON_RENDER_RESPONSE:
            print(event.args)

        if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
                event.args and not event.args['with_follow_on_turn']):
            if self.isplaying==True and self.trackchange==False:
                requests.get("http://localhost:3000/api/v1/commands/?cmd=play")
            self.can_start_conversation = True
            self.trackchange=False

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
            events = assistant.start()
            subprocess.Popen(["aplay", "{}/sample-audio-files/Startup-Female.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

if __name__ == '__main__':
    try:
        Myassistant().main()
    except Exception as error:
        print(error)
