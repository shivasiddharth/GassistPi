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
import re
import psutil
import logging
import google.auth.transport.requests
import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
DEVICE_API_URL = 'https://embeddedassistant.googleapis.com/v1alpha2'
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
from actions import play_playlist
from actions import play_songs
from actions import play_album
from actions import play_artist
from actions import refreshlists
from actions import chromecast_play_video
from actions import chromecast_control


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

#Indicator Pins
GPIO.setup(25, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.setup(6, GPIO.OUT)
GPIO.output(5, GPIO.LOW)
GPIO.output(6, GPIO.LOW)
led=GPIO.PWM(25,1)
led.start(0)

mpvactive=False


def ismpvplaying():
    for pid in psutil.pids():
        p=psutil.Process(pid)
        if 'mpv'in p.name():
            mpvactive=True
            break
        else:
            mpvactive=False
    return mpvactive

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
        if ismpvplaying():
            if os.path.isfile("/home/pi/.mediavolume.json"):
                with open('/home/pi/.mediavolume.json', 'r') as vol:
                    oldvollevel = json.load(vol)
                print(oldvollevel)
                mpvsetvol=os.system("echo '"+json.dumps({ "command": ["set_property", "volume",str(oldvollevel)]})+"' | socat - /tmp/mpvsocket")

        print()

    if event.type == EventType.ON_DEVICE_ACTION:
        for command, params in process_device_actions(event, device_id):
            print('Do command', command, 'with params', str(params))


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
            if 'trigger'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                Action(str(usrcmd).lower())
            if 'stream'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
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
                
            if 'stop'.lower() in str(usrcmd).lower():
                stop()
            if 'radio'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                radio(str(usrcmd).lower())
            if 'wireless'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                ESP(str(usrcmd).lower())
            if 'parcel'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                track()
            if 'news'.lower() in str(usrcmd).lower() or 'feed'.lower() in str(usrcmd).lower() or 'quote'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                feed(str(usrcmd).lower())
            if 'on kodi'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                kodiactions(str(usrcmd).lower())
            if 'chromecast'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                if 'play'.lower() in str(usrcmd).lower():
                    chromecast_play_video(str(usrcmd).lower())
                else:
                    chromecast_control(usrcmd)
            if 'pause music'.lower() in str(usrcmd).lower() or 'resume music'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                if ismpvplaying():
                    if 'pause music'.lower() in str(usrcmd).lower():
                        playstatus=os.system("echo '"+json.dumps({ "command": ["set_property", "pause", True]})+"' | socat - /tmp/mpvsocket")
                    elif 'resume music'.lower() in str(usrcmd).lower():
                        playstatus=os.system("echo '"+json.dumps({ "command": ["set_property", "pause", False]})+"' | socat - /tmp/mpvsocket")
                else:
                    say("Sorry nothing is playing right now")
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

            if 'refresh'.lower() in str(usrcmd).lower() and 'music'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                refreshlists()
            if 'google music'.lower() in str(usrcmd).lower():
                assistant.stop_conversation()
                os.system('pkill mpv')
                if os.path.isfile("/home/pi/GassistPi/src/trackchange.py"):
                    os.system('rm /home/pi/GassistPi/src/trackchange.py')
                    os.system('echo "from actions import play_playlist\nfrom actions import play_songs\nfrom actions import play_album\nfrom actions import play_artist\n\n" >> /home/pi/GassistPi/src/trackchange.py')
                    if 'all the songs'.lower() in str(usrcmd).lower():
                        os.system('echo "play_songs()\n" >> /home/pi/GassistPi/src/trackchange.py')
                        say("Playing all your songs")
                        play_songs()

                    if 'playlist'.lower() in str(usrcmd).lower():
                        if 'first'.lower() in str(usrcmd).lower() or 'one'.lower() in str(usrcmd).lower()  or '1'.lower() in str(usrcmd).lower():
                            os.system('echo "play_playlist(0)\n" >> /home/pi/GassistPi/src/trackchange.py')
                            say("Playing songs from your playlist")
                            play_playlist(0)
                        else:
                            say("Sorry I am unable to help")

                    if 'album'.lower() in str(usrcmd).lower():
                        if os.path.isfile("/home/pi/.gmusicalbumplayer.json"):
                            os.system("rm /home/pi/.gmusicalbumplayer.json")

                        req=str(usrcmd).lower()
                        idx=(req).find('album')
                        album=req[idx:]
                        album=album.replace("'}", "",1)
                        album = album.replace('album','',1)
                        if 'from'.lower() in req:
                            album = album.replace('from','',1)
                            album = album.replace('google music','',1)
                        else:
                            album = album.replace('google music','',1)

                        album=album.strip()
                        print(album)
                        albumstr=('"'+album+'"')
                        f = open('/home/pi/GassistPi/src/trackchange.py', 'a+')
                        f.write('play_album('+albumstr+')')
                        f.close()
                        say("Looking for songs from the album")
                        play_album(album)

                    if 'artist'.lower() in str(usrcmd).lower():
                        if os.path.isfile("/home/pi/.gmusicartistplayer.json"):
                            os.system("rm /home/pi/.gmusicartistplayer.json")

                        req=str(usrcmd).lower()
                        idx=(req).find('artist')
                        artist=req[idx:]
                        artist=artist.replace("'}", "",1)
                        artist = artist.replace('artist','',1)
                        if 'from'.lower() in req:
                            artist = artist.replace('from','',1)
                            artist = artist.replace('google music','',1)
                        else:
                            artist = artist.replace('google music','',1)

                        artist=artist.strip()
                        print(artist)
                        artiststr=('"'+artist+'"')
                        f = open('/home/pi/GassistPi/src/trackchange.py', 'a+')
                        f.write('play_artist('+artiststr+')')
                        f.close()
                        say("Looking for songs rendered by the artist")
                        play_artist(artist)
                else:
                    os.system('echo "from actions import play_playlist\nfrom actions import play_songs\nfrom actions import play_album\nfrom actions import play_artist\n\n" >> /home/pi/GassistPi/src/trackchange.py')
                    if 'all the songs'.lower() in str(usrcmd).lower():
                        os.system('echo "play_songs()\n" >> /home/pi/GassistPi/src/trackchange.py')
                        say("Playing all your songs")
                        play_songs()

                    if 'playlist'.lower() in str(usrcmd).lower():
                        if 'first'.lower() in str(usrcmd).lower() or 'one'.lower() in str(usrcmd).lower()  or '1'.lower() in str(usrcmd).lower():
                            os.system('echo "play_playlist(0)\n" >> /home/pi/GassistPi/src/trackchange.py')
                            say("Playing songs from your playlist")
                            play_playlist(0)
                        else:
                            say("Sorry I am unable to help")

                    if 'album'.lower() in str(usrcmd).lower():
                        if os.path.isfile("/home/pi/.gmusicalbumplayer.json"):
                            os.system("rm /home/pi/.gmusicalbumplayer.json")

                        req=str(usrcmd).lower()
                        idx=(req).find('album')
                        album=req[idx:]
                        album=album.replace("'}", "",1)
                        album = album.replace('album','',1)
                        if 'from'.lower() in req:
                            album = album.replace('from','',1)
                            album = album.replace('google music','',1)
                        else:
                            album = album.replace('google music','',1)

                        album=album.strip()
                        print(album)
                        albumstr=('"'+album+'"')
                        f = open('/home/pi/GassistPi/src/trackchange.py', 'a+')
                        f.write('play_album('+albumstr+')')
                        f.close()
                        say("Looking for songs from the album")
                        play_album(album)

                    if 'artist'.lower() in str(usrcmd).lower():
                        if os.path.isfile("/home/pi/.gmusicartistplayer.json"):
                            os.system("rm /home/pi/.gmusicartistplayer.json")

                        req=str(usrcmd).lower()
                        idx=(req).find('artist')
                        artist=req[idx:]
                        artist=artist.replace("'}", "",1)
                        artist = artist.replace('artist','',1)
                        if 'from'.lower() in req:
                            artist = artist.replace('from','',1)
                            artist = artist.replace('google music','',1)
                        else:
                            artist = artist.replace('google music','',1)

                        artist=artist.strip()
                        print(artist)
                        artiststr=('"'+artist+'"')
                        f = open('/home/pi/GassistPi/src/trackchange.py', 'a+')
                        f.write('play_artist('+artiststr+')')
                        f.close()
                        say("Looking for songs rendered by the artist")
                        play_artist(artist)



if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        logger.exception(error)
