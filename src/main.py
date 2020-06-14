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

needstatuschange=False

def check_volumio_status():
    try:
        output = subprocess.check_output("volumio status", shell=True)
        decodeoutput=output.decode("UTF-8")
        outputjs=json.loads(dd)
        status=outputjs["status"]
        if status=="stop" or status=="pause":
            needstatuschange=False
        elif status=="play":
            needstatuschange=True
        return needstatuschange
    except KeyError:
        needstatuschange=False
        return needstatuschange

def custom_command(command):
    if "play" in command:
        assistant.stop_conversation()
        requests.get("http://localhost:3000/api/v1/commands/?cmd=play")
    if "pause" in command:
        assistant.stop_conversation()
        requests.get("http://localhost:3000/api/v1/commands/?cmd=pause")
    if "next" in command:
        if needstatuschange:
            assistant.stop_conversation()
            requests.get("http://localhost:3000/api/v1/commands/?cmd=play")
            time.sleep(1000)
            requests.get("http://localhost:3000/api/v1/commands/?cmd=next")
        else:
            print("Unable to help")
    if "previous" in command:
        if needstatuschange:
            assistant.stop_conversation()
            requests.get("http://localhost:3000/api/v1/commands/?cmd=play")
            time.sleep(1000)
            requests.get("http://localhost:3000/api/v1/commands/?cmd=prev")
        else:
            print("Unable to help")
    if "speaker volume" in command:
        if "hundred" in command or "maximum" in command:
            settingvollevel=100
            requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume=100")
        elif "zero" in command or "minimum" in command:
            settingvollevel=0
            requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume=0")
        else:
            for vollevel in re.findall(r"[-+]?\d*\.\d+|\d+", command):
                settingvollevel=vollevel
            requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume="+str(settingvollevel))



def process_event(event):
    """Pretty prints events.

    Prints all events that occur with two spaces between each new
    conversation and a single space between turns of a conversation.

    Args:
        event(event.Event): The current event to process.
    """
    print(event)
    if event.type == EventType.ON_MUTED_CHANGED:
        print("Mic mute is set to: " + str(event.args["is_muted"]))

    if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        if needstatuschange:
            requests.get("http://localhost:3000/api/v1/commands/?cmd=pause")
        subprocess.Popen(["aplay", "{}/sample-audio-files/Fb.wav".format(ROOT_PATH)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print()

    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and not event.args['with_follow_on_turn']):
        if needstatuschange:
            requests.get("http://localhost:3000/api/v1/commands/?cmd=play")
        print()

    if (event.type == EventType.ON_RESPONDING_STARTED and event.args and not event.args['is_error_response']):
        print(event.args)

    if event.type == EventType.ON_RESPONDING_FINISHED:
        print(event.args)

    if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
        usrcmd=event.args["text"]
        usrcmd=str(usrcmd).lower()
        custom_command(usrcmd)

    if event.type == EventType.ON_DEVICE_ACTION:
        for command, params in event.actions:
            print('Do command', command, 'with params', str(params))


def main():
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
            process_event(event)



if __name__ == '__main__':
    main()
