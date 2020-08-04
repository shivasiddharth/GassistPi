#!/usr/bin/env python

#This is different from AIY Kit's actions
#Copying and Pasting AIY Kit's actions commands will not work

from kodijson import Kodi, PLAYER_VIDEO
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.tools import argparser
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import spotipy.oauth2 as oauth2
from pushbullet import Pushbullet
from mediaplayer import api
from youtube_search_engine import google_cloud_api_key
from googletrans import Translator
from youtube_search_engine import youtube_search
from youtube_search_engine import youtube_stream_link
from google.cloud import texttospeech
from gtts import gTTS
import requests
import mediaplayer
import os
import os.path
try:
    import RPi.GPIO as GPIO
except Exception as e:
    GPIO = None
import time
import re
import subprocess
import aftership
import feedparser
import json
import urllib.request
import pafy
import pychromecast
import spotipy
import pprint
import yaml
import pywemo

ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))


with open('{}/src/config.yaml'.format(ROOT_PATH),'r', encoding='utf8') as conf:
    configuration = yaml.load(conf)

with open('{}/src/lang.yaml'.format(ROOT_PATH),'r', encoding='utf8') as lang:
    langlist = yaml.load(lang)

TTSChoice=''
if configuration['TextToSpeech']['Choice']=="Google Cloud":
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""):
        if configuration['TextToSpeech']['Google_Cloud_TTS_Credentials_Path']!="ENTER THE PATH TO YOUR TTS CREDENTIALS FILE HERE":
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = configuration['TextToSpeech']['Google_Cloud_TTS_Credentials_Path']
            TTSChoice='GoogleCloud'
            # Instantiates a client
            client = texttospeech.TextToSpeechClient()
        else:
            print("Set the path to your Google cloud text to speech credentials in the config.yaml file. Using gTTS for now.....")
            TTSChoice='GTTS'
    else:
        TTSChoice='GoogleCloud'
        # Instantiates a client
        client = texttospeech.TextToSpeechClient()
else:
    TTSChoice='GTTS'


domoticz_devices=''
Domoticz_Device_Control=False
bright=''
hexcolour=''

if 'en' in configuration['Language']['Choice']:
    keywordfile= '{}/src/keywords_en.yaml'.format(ROOT_PATH)
elif 'it' in configuration['Language']['Choice']:
    keywordfile= '{}/src/keywords_it.yaml'.format(ROOT_PATH)
elif 'fr' in configuration['Language']['Choice']:
    keywordfile= '{}/src/keywords_fr.yaml'.format(ROOT_PATH)
elif 'de' in configuration['Language']['Choice']:
    keywordfile= '{}/src/keywords_de.yaml'.format(ROOT_PATH)
elif 'es' in configuration['Language']['Choice']:
    keywordfile= '{}/src/keywords_es.yaml'.format(ROOT_PATH)
elif 'nl' in configuration['Language']['Choice']:
    keywordfile= '{}/src/keywords_nl.yaml'.format(ROOT_PATH)
elif 'sv' in configuration['Language']['Choice']:
    keywordfile= '{}/src/keywords_sv.yaml'.format(ROOT_PATH)
else:
    keywordfile= '{}/src/keywords_en.yaml'.format(ROOT_PATH)
with open(keywordfile,'r' , encoding='utf8') as conf:
    custom_action_keyword = yaml.load(conf)


# Get devices list from domoticz server
if configuration['Domoticz']['Domoticz_Control']=='Enabled':
    Domoticz_Device_Control=True
    try:
        domoticz_response = requests.get("https://" + configuration['Domoticz']['Server_IP'][0] + ":" + configuration['Domoticz']['Server_port'][0] + "/json.htm?type=devices&filter=all&order=Name",verify=False)
        domoticz_devices=json.loads(domoticz_response.text)
        with open('{}/domoticz_device_list.json'.format(USER_PATH), 'w') as devlist:
            json.dump(domoticz_devices, devlist)
    except requests.exceptions.ConnectionError:
        print("Domoticz server not online")
else:
    Domoticz_Device_Control=False

Spotify_credentials=False
Youtube_credentials=False
if configuration['Spotify']['client_id']!= 'ENTER YOUR SPOTIFY CLIENT ID HERE' and configuration['Spotify']['client_secret']!='ENTER YOUR SPOTIFY CLIENT SECRET HERE':
    Spotify_credentials=True
if configuration['Google_cloud_api_key']!='ENTER-YOUR-GOOGLE-CLOUD-API-KEY-HERE':
    Youtube_credentials=True

# Spotify Declarations
# Register with spotify for a developer account to get client-id and client-secret
if Spotify_credentials:
    client_id = configuration['Spotify']['client_id']
    client_secret = configuration['Spotify']['client_secret']
    username=configuration['Spotify']['username']
    credentials = oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    spotify_token = credentials.get_access_token()


#Import VLC player
vlcplayer=mediaplayer.vlcplayer()



#Google Music Declarations
song_ids=[]
track_ids=[]


#Login with default kodi/kodi credentials
#kodi = Kodi("http://localhost:8080/jsonrpc")

#Login with custom credentials
# Kodi("http://IP-ADDRESS-OF-KODI:8080/jsonrpc", "username", "password")
kodiurl=("http://"+str(configuration['Kodi']['ip'])+":"+str(configuration['Kodi']['port'])+"/jsonrpc")
kodi = Kodi(kodiurl, configuration['Kodi']['username'], configuration['Kodi']['password'])
musicdirectory=configuration['Kodi']['musicdirectory']
videodirectory=configuration['Kodi']['videodirectory']
windowcmd=configuration['Kodi']['windowcmd']
window=configuration['Kodi']['window']

if GPIO!=None:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    #Number of entities in 'var' and 'PINS' should be the same
    var = configuration['Raspberrypi_GPIO_Control']['lightnames']
    gpio = configuration['Gpios']['picontrol']
    for pin in gpio:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

    #Servo pin declaration
    servopin=configuration['Gpios']['servo'][0]
    GPIO.setup(servopin, GPIO.OUT)
    pwm=GPIO.PWM(servopin, 50)
    pwm.start(0)

    #Stopbutton
    stoppushbutton=configuration['Gpios']['stopbutton_music_AIY_pushbutton'][0]
    GPIO.setup(stoppushbutton, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIOcontrol=True
else:
    GPIOcontrol=False

#Number of scripts and script names should be the same
scriptname=configuration['Script']['scriptname']
scriptcommand=configuration['Script']['scriptcommand']

#Number of station names and station links should be the same
stnname=configuration['Radio_stations']['stationnames']
stnlink=configuration['Radio_stations']['stationlinks']
stnradio=configuration['Radio_stations']['stationradio']

#IP Address of ESP
ip=configuration['ESP']['IP']

#Declaration of ESP names
devname=configuration['ESP']['devicename']
devid=configuration['ESP']['deviceid']

playshell = None

#Initialize colour list
clrlist=[]
clrlistfullname=[]
clrrgblist=[]
clrhexlist=[]
with open('{}/src/colours.json'.format(ROOT_PATH), 'r') as col:
     colours = json.load(col)
for i in range(0,len(colours)):
    clrname=colours[i]["name"]
    clrnameshort=clrname.replace(" ","",1)
    clrnameshort=clrnameshort.strip()
    clrnameshort=clrnameshort.lower()
    clrlist.append(clrnameshort)
    clrlistfullname.append(clrname)
    clrrgblist.append(colours[i]["rgb"])
    clrhexlist.append(colours[i]["hex"])


#Parcel Tracking declarations
#If you want to use parcel tracking, register for a free account at: https://www.aftership.com
#Add the API number and uncomment next two lines
#parcelapi = aftership.APIv4('YOUR-AFTERSHIP-API-NUMBER')
#couriers = parcelapi.couriers.all.get()
number = ''
slug=''

#RSS feed URLS
worldnews = "http://feeds.bbci.co.uk/news/world/rss.xml"
technews = "http://feeds.bbci.co.uk/news/technology/rss.xml"
topnews = "http://feeds.bbci.co.uk/news/rss.xml"
sportsnews = "http://feeds.feedburner.com/ndtvsports-latest"
quote = "http://feeds.feedburner.com/brainyquote/QUOTEBR"

##Speech and translator declarations
translator = Translator()
femalettsfilename="/tmp/female-say.mp3"
malettsfilename="/tmp/male-say.wav"
ttsfilename="/tmp/gcloud.mp3"
language=configuration['Language']['Choice']
translanguage=language.split('-')[0]
gender=''
if configuration['TextToSpeech']['Voice_Gender']=='Male' and translanguage=='en':
    gender='Male'
elif translanguage=='it':
    gender='Male'
elif configuration['TextToSpeech']['Voice_Gender']=='Male' and translanguage!='en':
    gender='Female'
else:
    gender='Female'

if configuration['Pushbullet']['Pushbullet_API_KEY']!='ENTER YOUR PUSHBULLET KEY HERE':
    pb=Pushbullet(configuration['Pushbullet']['Pushbullet_API_KEY'])
else:
    pb=None

#Function for google KS custom search engine
def kickstrater_search(query):
    service = build("customsearch", "v1",
            developerKey=google_cloud_api_key)
    res = service.cse().list(
        q=query,
        cx = '012926744822728151901:gefufijnci4',
        ).execute()
    return res


#Function for google Gaana custom search engine
def gaana_search(query):
    service = build("customsearch", "v1",
            developerKey=google_cloud_api_key)
    res = service.cse().list(
        q=query,
        cx = '012926744822728151901:jzpzbzih5hi',
        ).execute()
    return res

#gTTS
def gttssay(phrase,saylang,specgender):
    tts = gTTS(text=phrase, lang=saylang)
    tts.save(femalettsfilename)
    if specgender=='Male':
        os.system('sox ' + femalettsfilename + ' ' + malettsfilename + ' pitch -450')
        os.remove(femalettsfilename)
        os.system('aplay ' + malettsfilename)
        os.remove(malettsfilename)
    elif specgender=='Female':
        os.system("mpg123 "+femalettsfilename)
        os.remove(femalettsfilename)

#Google Cloud Text to Speech
def gcloudsay(phrase,lang):
    try:
        if gender=='Male':
            gcloudgender=texttospeech.enums.SsmlVoiceGender.MALE
        else:
            gcloudgender=texttospeech.enums.SsmlVoiceGender.FEMALE

        synthesis_input = texttospeech.types.SynthesisInput(text=phrase)
        voice = texttospeech.types.VoiceSelectionParams(
            language_code=lang,
            ssml_gender=gcloudgender)
        audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3)
        response = client.synthesize_speech(synthesis_input, voice, audio_config)
        with open(ttsfilename, 'wb') as out:
            out.write(response.audio_content)
        if gender=='Male' and lang=='it-IT':
            os.system('sox ' + ttsfilename + ' ' + malettsfilename + ' pitch -450')
            os.remove(ttsfilename)
            os.system('aplay ' + malettsfilename)
            os.remove(malettsfilename)
        else:
            os.system("mpg123 "+ttsfilename)
            os.remove(ttsfilename)
    except google.api_core.exceptions.ResourceExhausted:
        print("Google cloud text to speech quota exhausted. Using GTTS. Make sure to change the choice in config.yaml")
        gttssay(phrase,lang)

#Word translator
def trans(words,destlang,srclang):
    transword= translator.translate(words, dest=destlang, src=srclang)
    transword=transword.text
    transword=transword.replace("Text, ",'',1)
    transword=transword.strip()
    print(transword)
    return transword

#Text to speech converter with translation
def say(words,sourcelang=None,destinationlang=None):
    if sourcelang!=None and destinationlang!=None:
        sayword=trans(words,destinationlang,sourcelang)
        gttssay(sayword,destinationlang,'Female')
    else:
        if sourcelang==None:
            sourcelanguage='en'
        else:
            sourcelanguage=sourcelang
        if sourcelanguage!=translanguage:
            sayword=trans(words,translanguage,sourcelanguage)
        else:
            sayword=words
        if TTSChoice=='GoogleCloud':
            gcloudsay(sayword,language)
        elif TTSChoice=='GTTS':
            gttssay(sayword,translanguage,gender)



#Function to get HEX and RGB values for requested colour
def getcolours(phrase):
    usrclridx=idx=phrase.find(custom_action_keyword['Dict']['To'])
    usrclr=query=phrase[usrclridx:]
    usrclr=usrclr.replace(custom_action_keyword['Dict']['To'],"",1)
    usrclr=usrclr.replace("'","",1)
    usrclr=usrclr.replace("}","",1)
    usrclr=usrclr.strip()
    usrclr=usrclr.replace(" ","",1)
    usrclr=usrclr.lower()
    print(usrclr)
    try:
        for colournum, colourname in enumerate(clrlist):
            if usrclr in colourname:
               RGB=clrrgblist[colournum]
               red,blue,green=re.findall('\d+', RGB)
               hexcode=clrhexlist[colournum]
               cname=clrlistfullname[colournum]
               print(cname)
               break
        return red,blue,green,hexcode,cname
    except UnboundLocalError:
        say("Sorry unable to find a matching colour")


#Function to convert FBG to XY for Hue Lights
def convert_rgb_xy(red,green,blue):
    try:
        red = pow((red + 0.055) / (1.0 + 0.055), 2.4) if red > 0.04045 else red / 12.92
        green = pow((green + 0.055) / (1.0 + 0.055), 2.4) if green > 0.04045 else green / 12.92
        blue = pow((blue + 0.055) / (1.0 + 0.055), 2.4) if blue > 0.04045 else blue / 12.92
        X = red * 0.664511 + green * 0.154324 + blue * 0.162028
        Y = red * 0.283881 + green * 0.668433 + blue * 0.047685
        Z = red * 0.000088 + green * 0.072310 + blue * 0.986039
        x = X / (X + Y + Z)
        y = Y / (X + Y + Z)
        return x,y
    except UnboundLocalError:
        say("No RGB values given")

#Custom text to speak notification
def notify_tts(phrase):
    word=(custom_action_keyword['Keywords']['notify_TTS'][0]).lower()
    voice_notify = phrase.replace(word, "")
    voice_notify.strip()
    say(voice_notify)

#Run scripts
def script(phrase):
    for num, name in enumerate(scriptname):
        if name.lower() in phrase:
            conv=scriptname[num]
            command=scriptcommand[num]
            print (command)
            say("Running " +conv)
            os.system(command)

#Radio Station Streaming
def radio(phrase):
    conv = None
    for num, name in reversed(list(enumerate(stnname))):
        if name.lower() in phrase:
            station=stnlink[num]
            conv=stnradio[num]
            print (station)
            break
    if conv is not None:
        say("Tuning into " + conv)
        vlcplayer.media_manager(station,'Radio')
        vlcplayer.media_player(station)
    else:
        say("Station not found")


#ESP6266 Devcies control
def ESP(phrase):
    for num, name in enumerate(devname):
        if name.lower() in phrase:
            dev=devid[num]
            if custom_action_keyword['Dict']['On'] in phrase:
                ctrl='=ON'
                say("Turning On " + name)
            elif custom_action_keyword['Dict']['Off'] in phrase:
                ctrl='=OFF'
                say("Turning Off " + name)
            rq = requests.head("http://"+ip + dev + ctrl)


#Stepper Motor control
def SetAngle(angle):
    if GPIOcontrol:
        duty = angle/18 + 2
        GPIO.output(servopin, True)
        say("Moving motor by " + str(angle) + " degrees")
        pwm.ChangeDutyCycle(duty)
        time.sleep(1)
        pwm.ChangeDutyCycle(0)
        GPIO.output(servopin, False)
    else:
        say("GPIO controls, is not supported for your device.")



def stop():
    vlcplayer.stop_vlc()

#Parcel Tracking
def track():
    text=parcelapi.trackings.get(tracking=dict(slug=slug, tracking_number=number))
    numtrack=len(text['trackings'])
    print("Total Number of Parcels: " + str(numtrack))
    if numtrack==0:
        parcelnotify=("You have no parcel to track")
        say(parcelnotify)
    elif numtrack==1:
        parcelnotify=("You have one parcel to track")
        say(parcelnotify)
    elif numtrack>1:
        parcelnotify=( "You have " + str(numtrack) + " parcels to track")
        say(parcelnotify)
    for x in range(0,numtrack):
        numcheck=len(text[ 'trackings'][x]['checkpoints'])
        description = text['trackings'][x]['checkpoints'][numcheck-1]['message']
        parcelid=text['trackings'][x]['tracking_number']
        trackinfo= ("Parcel Number " + str(x+1)+ " with tracking id " + parcelid + " is "+ description)
        say(trackinfo)
        #time.sleep(10)

#RSS Feed Reader
def feed(phrase):
    if 'world news' in phrase:
        URL=worldnews
    elif 'top news' in phrase:
        URL=topnews
    elif 'sports news' in phrase:
        URL=sportsnews
    elif 'tech news' in phrase:
        URL=technews
    elif (custom_action_keyword['Keywords']['RSS'][1]).lower() in phrase:
        URL=quote
    numfeeds=10
    feed=feedparser.parse(URL)
    feedlength=len(feed['entries'])
    print(feedlength)
    if feedlength<numfeeds:
        numfeeds=feedlength
    title=feed['feed']['title']
    say(title)
    if GPIOcontrol:
        #To stop the feed, press and hold stop button
        while GPIO.input(stoppushbutton):
            for x in range(0,numfeeds):
                content=feed['entries'][x]['title']
                print(content)
                say(content)
                summary=feed['entries'][x]['summary']
                print(summary)
                say(summary)
                if not GPIO.input(stoppushbutton):
                  break
            if x == numfeeds-1:
                break
            else:
                continue
    else:
        print("GPIO controls, is not supported for your device. You need to wait for feeds to automatically stop")


##--------------Start of send clickatell sms----------------------
#Function to send SMS with Clickatell api
recivernum=configuration['Clickatell']['Reciever']
clickatell_api=configuration['Clickatell']['Clickatell_API']

def sendClickatell(number, message):
    response=requests.get('https://platform.clickatell.com/messages/http/send?apiKey=' + clickatell_api + '&to=' + number + '&content=' + message)
    if response.status_code == 202:
        say("SMS message sent")
    else:
        say("Error sending SMS message. Check your settings")

def sendSMS(query):
    if clickatell_api != 'ENTER_YOUR_CLICKATELL_API':
        for num, name in enumerate(configuration['Clickatell']['Name']):
            if name.lower() in query:
                conv=recivernum[num]
                command=(custom_action_keyword['Keywords']['Send_sms_clickatell'][0]).lower()
                msg=query.replace(command, "")
                message=msg.replace(name.lower(), "")
                message=message.strip()
                print(message + " , " + name + " , " + conv)
                say("Sends SMS message " + message + " to " + name)
                sendClickatell(conv, message)
    else:
        say("You need to enter Clickatell API")

##---------------End of send clickatell sms-----------------------

##-------Start of functions defined for Kodi Actions--------------
#Function to get Kodi Volume and Mute status
def mutevolstatus():
    status= kodi.Application.GetProperties({"properties": ("volume","muted")})
    mutestatus=(status["result"]["muted"])
    volstatus=(status["result"]["volume"])
    return mutestatus, volstatus


def kodi_youtube(query):
    urlid = youtube_search(query)
    if urlid is not None:
        fullurl = "https://www.youtube.com/watch?v=" + urlid

 #If you want to see the URL, uncomment the following line
 #print(YouTubeURL)

 #Instead of sending it to Kodi, if you want to play locally, uncomment the following two lines and comment the next two lines
 #vlcplayer.media_player(YouTubeURL)
 #say("Playing YouTube video")

    kodi.Player.open(item={"file":"plugin://plugin.video.youtube/?action=play_video&videoid=" + urlid})
    say("Playing YouTube video on Kodi")


#Function to fetch tracks from an album
def kodialbum(query):
    albumcontents=[]
    directories=[]
    kodi.Playlist.Clear(playlistid=0)
    songs=kodi.AudioLibrary.GetSongs({ "limits": { "start" : 0, "end": 200 }, "properties": [ "artist", "duration", "album", "track" ], "sort": { "order": "ascending", "method": "track", "ignorearticle": True } })
    numsongs=len(songs["result"]["songs"])
    print(songs)
    files=kodi.Files.GetDirectory({"directory": musicdirectory, "media": "music"})
    print(files)
    numfiles=len(files["result"]["files"])
    for a in range(0,numfiles):
        if (files["result"]["files"][a]["filetype"])=="directory":
            folder=files["result"]["files"][a]["file"]
            musicfiles=kodi.Files.GetDirectory({"directory": folder, "media": "music"})
            print(musicfiles)
            nummusicfiles=len(musicfiles["result"]["files"])
            numsongs=len(songs["result"]["songs"])
            for i in range(0,numsongs):
                if query.lower() in str(songs["result"]["songs"][i]["album"]).lower():
                    for j in range(0,nummusicfiles):
                        name=musicfiles["result"]["files"][j]["label"]
                        if str(songs["result"]["songs"][i]["label"]).lower() in str(name).lower():
                            path=musicfiles["result"]["files"][j]["file"]
                            albumcontents.append(songs["result"]["songs"][i]["label"])
                            kodi.Playlist.Add(playlistid=0, item={"file": path})

        elif (files["result"]["files"][a]["filetype"])=="file":
            for i in range(0,numsongs):
                if query.lower() in str(songs["result"]["songs"][i]["album"]).lower():
                    name=files["result"]["files"][a]["label"]
                    if str(songs["result"]["songs"][i]["label"]).lower() in str(name).lower():
                        path=files["result"]["files"][a]["file"]
                        albumcontents.append(songs["result"]["songs"][i]["label"])
                        kodi.Playlist.Add(playlistid=0, item={"file": path})

    if len(albumcontents)!=0:
        print(albumcontents)
        playinginfo=("Playing "+str(len(albumcontents))+" tracks from album "+query)
        print(playinginfo)
        say(playinginfo)
        kodi.Player.open(item={"playlistid": 0},options={"repeat": "all"})
    else:
        print("Sorry, I could not find tracks from that album")
        say("Sorry, I could not find tracks from that album")


#Function to retrieve the name of requested album from the user command
def albumretrieve(query):
    i=0
    Albumnames=[]
    Albums=kodi.AudioLibrary.GetAlbums({ "limits": { "start" : 0, "end": 200 }, "properties": ["playcount", "artist", "genre", "rating", "thumbnail", "year", "mood", "style"], "sort": { "order": "ascending", "method": "album", "ignorearticle": True } })
    numalbums=len(Albums["result"]["albums"])
    for i in range(0,numalbums):
        Albumnames.append(Albums["result"]["albums"][i]["label"])
        if str(Albums["result"]["albums"][i]["label"]).lower() in str(query).lower():
            reqalbum=(Albums["result"]["albums"][i]["label"])
            break
        else:
            reqalbum=""
    if reqalbum!="":
        print(Albumnames)
        print(reqalbum)
        feedback=("Album, "+reqalbum+" found")
        print(feedback)
        say(feedback)
        kodialbum(reqalbum)#Calling the function to fetch tracks from the album
    else:
        print('Sorry, I could not find that album. But, here is a list of other vailable albums')
        say("Sorry, I could not find that album. But, here is a list of other vailable albums")
        for i in range(0,numalbums):
            Albumname=str(Albums["result"]["albums"][i]["label"])
            print(Albumname)
            say(Albumname)


#Function to fetch songs rendered by an artist
def kodiartist(query):
    artistcontents=[]
    directories=[]
    kodi.Playlist.Clear(playlistid=0)
    songs=kodi.AudioLibrary.GetSongs({ "limits": { "start" : 0, "end": 200 }, "properties": [ "artist", "duration", "album", "track" ], "sort": { "order": "ascending", "method": "track", "ignorearticle": True } })
    numsongs=len(songs["result"]["songs"])
    print(songs)
    files=kodi.Files.GetDirectory({"directory": musicdirectory, "media": "music"})
    print(files)
    numfiles=len(files["result"]["files"])
    for a in range(0,numfiles):
        if (files["result"]["files"][a]["filetype"])=="directory":
            folder=files["result"]["files"][a]["file"]
            musicfiles=kodi.Files.GetDirectory({"directory": folder, "media": "music"})
            print(musicfiles)
            nummusicfiles=len(musicfiles["result"]["files"])
            numsongs=len(songs["result"]["songs"])
            for i in range(0,numsongs):
                if query.lower() in str(songs["result"]["songs"][i]["artist"]).lower():
                    for j in range(0,nummusicfiles):
                        name=musicfiles["result"]["files"][j]["label"]
                        if str(songs["result"]["songs"][i]["label"]).lower() in str(name).lower():
                            path=musicfiles["result"]["files"][j]["file"]
                            artistcontents.append(songs["result"]["songs"][i]["label"])
                            kodi.Playlist.Add(playlistid=0, item={"file": path})

        elif (files["result"]["files"][a]["filetype"])=="file":
            for i in range(0,numsongs):
                if query.lower() in str(songs["result"]["songs"][i]["artist"]).lower():
                    name=files["result"]["files"][a]["label"]
                    if str(songs["result"]["songs"][i]["label"]).lower() in str(name).lower():
                        path=files["result"]["files"][a]["file"]
                        artistcontents.append(songs["result"]["songs"][i]["label"])
                        kodi.Playlist.Add(playlistid=0, item={"file": path})

    if len(artistcontents)!=0:
        print(artistcontents)
        if len(artistcontents)==1:
            playinginfo=("Playing "+str(len(artistcontents))+" track rendered by "+query)
        else:
            playinginfo=("Playing "+str(len(artistcontents))+" tracks rendered by "+query)
        print(playinginfo)
        say(playinginfo)
        kodi.Player.open(item={"playlistid": 0},options={"repeat": "all"})
    else:
        print("Sorry, I could not find tracks rendered by that artist")
        say("Sorry, I could not find tracks rendered by that artist")


#Function to play requested single track or video/movie on kodi
def singleplaykodi(query):
    kodi.Playlist.Clear(playlistid=0)
    i=0
    idx=query.find(custom_action_keyword['Dict']['Play'])
    track=query[idx:]
    track=track.replace("}", "",1)
    track=track.replace("'", "",1)
    track = track.replace(custom_action_keyword['Dict']['Play'],'',1)
    track = track.replace((custom_action_keyword['Keywords']['Kodi_actions'][0]),'',1)
    track=track.strip()
    say("Searching for your file")
    if 'song'.lower() in str(track).lower() or 'track'.lower() in str(track).lower() or 'audio'.lower() in str(track).lower():
        if 'song'.lower() in str(track).lower():
            track = track.replace('song','',1)
        elif 'track'.lower() in str(track).lower():
            track = track.replace('track','',1)
        elif 'audio'.lower() in str(track).lower():
            track = track.replace('audio','',1)
        track=track.strip()
        musicfiles=kodi.Files.GetDirectory({"directory": musicdirectory, "media": "music"})
        nummusicfiles=len(musicfiles["result"]["files"])
        print("Total number of files: "+ str(nummusicfiles))
        for a in range(0,nummusicfiles):
            if (musicfiles["result"]["files"][a]["filetype"])=="directory":
                folder=musicfiles["result"]["files"][a]["file"]
                files=kodi.Files.GetDirectory({"directory": folder, "media": "music"})
                numfiles=len(files["result"]["files"])
                for i in range(0,numfiles):
                   name=files["result"]["files"][i]["label"]
                   if str(track).lower() in str(name).lower():
                       print('Matching file found')
                       path=files["result"]["files"][i]["file"]
                       print(path)
                       say("Playing "+name+" song")
                       kodi.Player.open(item={"file": path})
            elif (musicfiles["result"]["files"][a]["filetype"])=="file":
                name=musicfiles["result"]["files"][a]["label"]
                if str(track).lower() in str(name).lower():
                    print('Matching file found')
                    path=musicfiles["result"]["files"][a]["file"]
                    print(path)
                    say("Playing "+name+" song")
                    kodi.Player.open(item={"file": path})

    elif 'movie'.lower() in str(track).lower() or 'video'.lower() in str(track).lower():
        track = track.replace('movie','',1)
        track=track.strip()
        videofiles=kodi.Files.GetDirectory({"directory": videodirectory, "media": "video"})
        numvideofiles=len(videofiles["result"]["files"])
        print(videofiles)
        print("Total number of files: "+ str(numvideofiles))
        for a in range(0,numvideofiles):
            if (videofiles["result"]["files"][a]["filetype"])=="directory":
                folder=videofiles["result"]["files"][a]["file"]
                files=kodi.Files.GetDirectory({"directory": folder, "media": "video"})
                print(files)
                numfiles=len(files["result"]["files"])
                for i in range(0,numfiles):
                   name=files["result"]["files"][i]["label"]
                   if str(track).lower() in str(name).lower():
                       print('Matching file found')
                       path=files["result"]["files"][i]["file"]
                       print(path)
                       say("Playing "+name+" movie")
                       kodi.Player.open(item={"file": path})
            elif (videofiles["result"]["files"][a]["filetype"])=="file":
                name=videofiles["result"]["files"][a]["label"]
                if str(track).lower() in str(name).lower():
                    print('Matching file found')
                    path=videofiles["result"]["files"][a]["file"]
                    print(path)
                    say("Playing "+name+" movie")
                    kodi.Player.open(item={"file": path})
    else:
        say("Sorry, I am unable to help you with that now")


#Function to check what is currently playing
def whatisplaying():
    players=kodi.Player.GetActivePlayers()
    print(players)
    if players["result"]==[]:
        say("Stop kidding, will you?")
    else:
        playid=players["result"][0]["playerid"]
        typeplaying=players["result"][0]["type"]
        if typeplaying=="video" and playid==1:
            currentvid=kodi.Player.GetItem({ "properties": ["title", "album", "artist", "season", "episode", "duration", "showtitle", "tvshowid", "thumbnail", "file", "fanart", "streamdetails"], "playerid": 1 })
            print(currentvid["result"]["item"]["title"])
            playingcontent=("Movie titled, "+(currentvid["result"]["item"]["title"])+", is currently playing")
            print(playingcontent)
            say(playingcontent)
        elif typeplaying=="audio" and playid==0:
            currentaud=kodi.Player.GetItem({ "properties": ["title", "album", "artist", "duration", "thumbnail", "file", "fanart", "streamdetails"], "playerid": 0 })
            print(currentaud["result"]["item"]["title"])
            print(currentaud["result"]["item"]["album"])
            if (currentaud["result"]["item"]["album"]) !=[] and (currentaud["result"]["item"]["album"]) !=str("") and (currentaud["result"]["item"]["artist"])!=[] and (currentaud["result"]["item"]["artist"])!=str(""):
                playingcontent=("Song titled, '"+(currentaud["result"]["item"]["title"])+"', from the album "+(currentaud["result"]["item"]["album"])+", by "+str((currentaud["result"]["item"]["artist"][0]))+", is currently playing")
                print(playingcontent)
                say(playingcontent)
            else:
                playingcontent=("Song titled, "+(currentaud["result"]["item"]["title"])+", is currently playing")
                print(playingcontent)
                say(playingcontent)
        else:
            print("Is anything even playing")
            say("Is anything even playing ?")


#Function to shuffle Kodi tracks
def shufflekodi():
    directories=[]
    kodi.Playlist.Clear(playlistid=0)
    files=kodi.Files.GetDirectory({"directory": musicdirectory, "media": "music"})
    numfiles=len(files["result"]["files"])
    for a in range(0,numfiles):
        if (files["result"]["files"][a]["filetype"])=="directory":
            directories.append(files["result"]["files"][a]["file"])
        elif (files["result"]["files"][a]["filetype"])=="file":
            path=files["result"]["files"][a]["file"]
            kodi.Playlist.Add(playlistid=0, item={"file": path})
    for i in range(0,len(directories)):
        folder=directories[i]
        songs=kodi.Files.GetDirectory({"directory": folder, "media": "music"})
        numsongs=len(songs["result"]["files"])
        for j in range(0,numsongs):
            path=songs["result"]["files"][j]["file"]
            kodi.Playlist.Add(playlistid=0, item={"file": path})
    kodi.Player.open(item={"playlistid": 0},options={"repeat": "all"})
    players=kodi.Player.GetActivePlayers()
    playid=players["result"][0]["playerid"]
    kodi.Player.SetShuffle({"playerid":playid,"shuffle":True})
    say("Shuffling your music")


#Functions for actions on KODI
def kodiactions(phrase):
    if 'youtube'.lower() in str(phrase).lower():
        query=str(phrase).lower()
        idx=query.find(custom_action_keyword['Dict']['Play'])
        track=query[idx:]
        track=track.replace("}", "",1)
        track=track.replace("'", "",1)
        track = track.replace(custom_action_keyword['Dict']['Play'],'',1)
        track = track.replace((custom_action_keyword['Keywords']['Kodi_actions'][0]),'',1)
        if 'youtube'.lower() in track:
            track=track.replace('youtube','',1)
        elif 'video'.lower() in track:
            track=track.replace('video','',1)
        else:
            track=track.strip()
        print(track)
        say("Fetching YouTube links for, "+track)
        kodi_youtube(track)
    elif 'what'.lower() in str(phrase).lower() and 'playing'.lower() in str(phrase).lower():
        whatisplaying()
    elif custom_action_keyword['Dict']['Play'].lower() in str(phrase).lower() and (custom_action_keyword['Dict']['Album']).lower() in str(phrase).lower():
        albumretrieve(phrase)
    elif custom_action_keyword['Dict']['Play'].lower() in str(phrase).lower() and (custom_action_keyword['Dict']['Artist']).lower() in str(phrase).lower():
        query=str(phrase).lower()
        idx = query.find(custom_action_keyword['Dict']['Artist'])
        artist = query[idx:]
        artist = artist.replace("'", "",1)
        artist = artist.replace("}", "",1)
        artist = artist.replace(custom_action_keyword['Dict']['Artist'],'',1)
        artist = artist.replace((custom_action_keyword['Keywords']['Kodi_actions'][0]),'',1)
        artist = artist.strip()
        say("Searching for renditions")
        kodiartist(artist)
    elif custom_action_keyword['Dict']['Play'].lower() in str(phrase).lower() and ('audio'.lower() in str(phrase).lower() or 'movie'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'video'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower()):
        singleplaykodi(phrase)
    elif 'shuffle'.lower() in str(phrase).lower() and ('audio'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower() or 'music'.lower() in str(phrase).lower()):
        shufflekodi()
    elif 'repeat'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        if 'this'.lower() in str(phrase).lower() or 'one'.lower() in str(phrase).lower() or str(1).lower() in str(phrase).lower():
            kodi.Player.SetRepeat({"playerid": playid,"repeat": "one"})
        elif 'all'.lower() in str(phrase).lower():
            kodi.Player.SetRepeat({"playerid": playid,"repeat": "all"})
        elif (custom_action_keyword['Dict']['Off']).lower() in str(phrase).lower() or 'disable'.lower() in str(phrase).lower() or 'none'.lower() in str(phrase).lower():
            kodi.Player.SetRepeat({"playerid": playid,"repeat": "off"})
    elif 'turn'.lower() in str(phrase).lower() and 'shuffle'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        cmd=str(phrase).lower()
        cmd=cmd.replace((custom_action_keyword['Keywords']['Kodi_actions'][0]),'',1)
        cmd=cmd.strip()
        if (custom_action_keyword['Dict']['On']).lower() in str(cmd).lower():
            kodi.Player.SetShuffle({"playerid": playid,"shuffle":True})
            print('Turning on shuffle')
        elif (custom_action_keyword['Dict']['Off']).lower() in str(cmd).lower():
            kodi.Player.SetShuffle({"playerid": playid,"shuffle":False})
            print('Turning off shuffle')
    elif custom_action_keyword['Dict']['Play'].lower() in str(phrase).lower() and 'next'.lower() in str(phrase).lower() or ('audio'.lower() in str(phrase).lower() or 'video'.lower() in str(phrase).lower() or 'movie'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower()):
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        kodi.Player.GoTo({"playerid":playid,"to":"next"})
    elif custom_action_keyword['Dict']['Play'].lower() in str(phrase).lower() and 'previous'.lower() in str(phrase).lower() or ('audio'.lower() in str(phrase).lower() or 'video'.lower() in str(phrase).lower() or 'movie'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower()):
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        kodi.Player.GoTo({"playerid":playid,"to":"previous"})
    elif 'scroll'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        if 'back'.lower() in str(phrase).lower() or 'backward'.lower() in str(phrase).lower():
            if 'a bit'.lower() in str(phrase).lower() or 'little'.lower() in str(phrase).lower():
                kodi.Player.Seek({ "playerid": playid, "value": "smallbackward" })
            else:
                kodi.Player.Seek({ "playerid": playid, "value": "bigbackward" })
        elif 'front'.lower() in str(phrase).lower() or 'forward'.lower() in str(phrase).lower():
            if 'a bit'.lower() in str(phrase).lower() or 'little'.lower() in str(phrase).lower():
                kodi.Player.Seek({ "playerid": playid, "value": "smallforward" })
            else:
                kodi.Player.Seek({ "playerid": playid, "value": "bigforward" })
    elif (custom_action_keyword['Dict']['Set']).lower() in str(phrase).lower() and 'volume'.lower() in str(phrase).lower():
        for s in re.findall(r'\b\d+\b', phrase):
            kodi.Application.SetVolume({"volume": int(s)})
            with open('{}/.volume.json'.format(USER_PATH), 'w') as f:
                   json.dump(int(s), f)
    elif 'toggle mute'.lower() in str(phrase).lower():
        status=mutevolstatus()
        if status[0]==False:
            kodi.Application.SetMute({"mute": True})
            say("Muting Kodi")
        elif status[0]==True:
            kodi.Application.SetMute({"mute": False})
            say("Disabling mute on Kodi")
    elif 'get'.lower() in str(phrase).lower() and 'volume'.lower() in str(phrase).lower():
        status=mutevolstatus()
        vollevel=status[1]
        say("Currently, Kodi's volume is set at: "+str(vollevel))
    elif 'go to'.lower() in str(phrase).lower() or 'open'.lower() in str(phrase).lower():
        for num, name in enumerate(windowcmd):
            if name.lower() in str(phrase).lower():
                activwindow=window[num]
                kodi.GUI.ActivateWindow({"window": activwindow})
    elif 'pause'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        if players["result"]==[]:
            say("There is nothing playing")
        else:
            playid=players["result"][0]["playerid"]
            kodi.Player.PlayPause({"playerid": playid,"play": False})
    elif 'resume'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        if players["result"]==[]:
            say("There is nothing playing")
        else:
            playid=players["result"][0]["playerid"]
            kodi.Player.PlayPause({"playerid": playid,"play": True})
    elif 'stop'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        if players["result"]==[]:
            say("There is nothing playing")
        else:
            playid=players["result"][0]["playerid"]
            kodi.Player.Stop({"playerid": playid})
    elif 'move'.lower() in str(phrase).lower() or 'show'.lower():
        if 'left'.lower() in str(phrase).lower():
            kodi.Input.Left()
        elif 'right'.lower() in str(phrase).lower():
            kodi.Input.Right()
        elif 'up'.lower() in str(phrase).lower():
            kodi.Input.Up()
        elif 'down'.lower() in str(phrase).lower():
            kodi.Input.Down()
        elif 'back'.lower() in str(phrase).lower():
            kodi.Input.Back()
        elif 'select'.lower() in str(phrase).lower():
            kodi.Input.Select()
        elif 'info'.lower() in str(phrase).lower():
            kodi.Input.Info()
        elif 'player'.lower() in str(phrase).lower():
            kodi.Input.ShowOSD

##--------End of functions defined for Kodi Actions--------------------



#----------Getting urls for YouTube autoplay-----------------------------------
def fetchautoplaylist(url,numvideos):
    videourl=url
    autonum=numvideos
    autoplay_urls=[]
    autoplay_urls.append(videourl)
    for i in range(0,autonum):
        response=urllib.request.urlopen(videourl)
        webContent = response.read()
        webContent = webContent.decode('utf-8')
        idx=webContent.find("Up next")
        getid=webContent[idx:]
        idx=getid.find('<a href="/watch?v=')
        getid=getid[idx:]
        getid=getid.replace('<a href="/watch?v=',"",1)
        getid=getid.strip()
        idx=getid.find('"')
        videoid=getid[:idx]
        videourl=('https://www.youtube.com/watch?v='+videoid)
        if not videourl in autoplay_urls:
            i=i+1
            autoplay_urls.append(videourl)
        else:
            i=i-1
            continue
##    print(autoplay_urls)
    return autoplay_urls




##-------Start of functions defined for Google Music-------------------

def loadsonglist():
    song_ids=[]
    if os.path.isfile("{}/songs.json".format(USER_PATH)):
        with open('{}/songs.json'.format(USER_PATH),'r') as input_file:
            songs_list= json.load(input_file)
##            print(songs_list)
    else:
        songs_list= api.get_all_songs()
        with open('{}/songs.json'.format(USER_PATH), 'w') as output_file:
            json.dump(songs_list, output_file)
    for i in range(0,len(songs_list)):
        song_ids.append(songs_list[i]['id'])
    songsnum=len(songs_list)
    return song_ids, songsnum

def loadartist(artistname):
    song_ids=[]
    artist=str(artistname)
    if os.path.isfile("{}/songs.json".format(USER_PATH)):
        with open('{}/songs.json'.format(USER_PATH),'r') as input_file:
            songs_list= json.load(input_file)
##            print(songs_list)
    else:
        songs_list= api.get_all_songs()
        with open('{}/songs.json'.format(USER_PATH), 'w') as output_file:
            json.dump(songs_list, output_file)
    for i in range(0,len(songs_list)):
        if artist.lower() in (songs_list[i]['albumArtist']).lower():
            song_ids.append(songs_list[i]['id'])
        else:
            print("Artist not found")
    songsnum=len(song_ids)
    return song_ids, songsnum

def loadalbum(albumname):
    song_ids=[]
    album=str(albumname)
    if os.path.isfile("{}/songs.json".format(USER_PATH)):
        with open('{}/songs.json'.format(USER_PATH),'r') as input_file:
            songs_list= json.load(input_file)
##            print(songs_list)
    else:
        songs_list= api.get_all_songs()
        with open('{}/songs.json'.format(USER_PATH), 'w') as output_file:
            json.dump(songs_list, output_file)
    for i in range(0,len(songs_list)):
        if album.lower() in (songs_list[i]['album']).lower():
            song_ids.append(songs_list[i]['id'])
        else:
            print("Album not found")
    songsnum=len(song_ids)
    return song_ids, songsnum

def loadplaylist(playlistnum):
    track_ids=[]
    if os.path.isfile("{}/playlist.json".format(USER_PATH)):
        with open('{}/playlist.json'.format(USER_PATH),'r') as input_file:
            playlistcontents= json.load(input_file)
    else:
        playlistcontents=api.get_all_user_playlist_contents()
        with open('{}/playlist.json'.format(USER_PATH), 'w') as output_file:
            json.dump(playlistcontents, output_file)
##        print(playlistcontents[0]['tracks'])

    for k in range(0,len(playlistcontents[playlistnum]['tracks'])):
        track_ids.append(playlistcontents[playlistnum]['tracks'][k]['trackId'])
##        print(track_ids)
    tracksnum=len(playlistcontents[playlistnum]['tracks'])
    return track_ids, tracksnum

def refreshlists():
    playlist_list=api.get_all_user_playlist_contents()
    songs_list=api.get_all_songs()
    with open('{}/songs.json'.format(USER_PATH), 'w') as output_file:
        json.dump(songs_list, output_file)
    with open('{}/playlist.json'.format(USER_PATH), 'w') as output_file:
        json.dump(playlist_list, output_file)
    say("Music list synchronised")



def gmusicselect(phrase):
    currenttrackid=0
    if 'all the songs'.lower() in phrase:
        say("Looking for your songs")
        tracks,numtracks=loadsonglist()
        if not tracks==[]:
            vlcplayer.media_manager(tracks,'Google Music')
            vlcplayer.googlemusic_player(currenttrackid)
        else:
            say("Unable to find songs matching your request")


    if 'playlist'.lower() in phrase:
        if 'first'.lower() in phrase or 'one'.lower() in phrase  or '1'.lower() in phrase:
            say("Playing songs from your playlist")
            tracks,numtracks=loadplaylist(0)
            if not tracks==[]:
                vlcplayer.media_manager(tracks,'Google Music')
                vlcplayer.googlemusic_player(currenttrackid)
            else:
                say("Unable to find songs matching your request")


    if (custom_action_keyword['Dict']['Album']).lower() in phrase:
        req=phrase
        idx1=req.find(custom_action_keyword['Dict']['Album'])
        idx2=req.find(custom_action_keyword['Dict']['From_google_music'])
        album=req[idx1:idx2]
        album = album.replace(custom_action_keyword['Dict']['Album'],'',1)
        album = album.replace(custom_action_keyword['Dict']['From_google_music'],'',1)
        album=album.strip()
        print(album)
        say("Looking for songs from the album")
        tracks,numtracks=loadalbum(album)
        if not tracks==[]:
            vlcplayer.media_manager(tracks,'Google Music')
            vlcplayer.googlemusic_player(currenttrackid)
        else:
            say("Unable to find songs matching your request")

    if (custom_action_keyword['Dict']['Artist']).lower() in phrase:
        req=phrase
        idx1=req.find(custom_action_keyword['Dict']['Artist'])
        idx2=req.find(custom_action_keyword['Dict']['From_google_music'])
        artist=req[idx1:idx2]
        artist = artist.replace(custom_action_keyword['Dict']['Artist'],'',1)
        artist = artist.replace(custom_action_keyword['Dict']['From_google_music'],'',1)
        artist=artist.strip()
        print(artist)
        say("Looking for songs rendered by the artist")
        tracks,numtracks=loadartist(artist)
        if not tracks==[]:
            vlcplayer.media_manager(tracks,'Google Music')
            vlcplayer.googlemusic_player(currenttrackid)
        else:
            say("Unable to find songs matching your request")


#----------End of functions defined for Google Music---------------------------


#-----------------Start of Functions for YouTube Streaming---------------------

def YouTube_Autoplay(phrase):
    try:
        urllist=[]
        currenttrackid=0
        idx1=phrase.find('autoplay')
        idx2=phrase.find(custom_action_keyword['Dict']['From_youtube'])
        track=phrase[idx1:idx2]
        track = track.replace('autoplay','',1)
        track = track.replace(custom_action_keyword['Dict']['From_youtube'],'',1)
        track=track.strip()
        say("Getting autoplay links")
        print(track)
        autourls=youtube_search(track,10) # Maximum of 10 URLS
        print(autourls)
        say("Adding autoplay links to the playlist")
        for i in range(0,len(autourls)):
            audiostream,videostream=youtube_stream_link(autourls[i])
            streamurl=audiostream
            urllist.append(streamurl)
        if not urllist==[]:
                vlcplayer.media_manager(urllist,'YouTube')
                vlcplayer.youtube_player(currenttrackid)
        else:
            say("Unable to find songs matching your request")

    except Exception as e:
        print(e)
        say('Encountered an exception please check the logs.')

def YouTube_No_Autoplay(phrase):
    try:
        urllist=[]
        currenttrackid=0
        idx1=phrase.find(custom_action_keyword['Dict']['Play'])
        idx2=phrase.find(custom_action_keyword['Dict']['From_youtube'])
        track=phrase[idx1:idx2]
        track = track.replace(custom_action_keyword['Dict']['Play'],'',1)
        track = track.replace(custom_action_keyword['Dict']['From_youtube'],'',1)
        track=track.strip()
        say("Getting youtube link")
        print(track)
        urlid=youtube_search(track)
        if urlid is not None:
            fullurl="https://www.youtube.com/watch?v="+urlid
            audiostream,videostream=youtube_stream_link(fullurl)
            streamurl=audiostream
            urllist.append(streamurl)
            vlcplayer.media_manager(urllist,'YouTube')
            vlcplayer.youtube_player(currenttrackid)
        else:
            say("Unable to find songs matching your request")

    except Exception as e:
        print(e)
        say('Encountered an exception please check the logs.')

#-----------------End of Functions for YouTube Streaming---------------------



#--------------Start of Chromecast functions-----------------------------------

def chromecast_play_video(phrase):
    # Chromecast declarations
    # Do not rename/change "TV" its a variable
    TV = pychromecast.Chromecast("192.168.1.13") #Change ip to match the ip-address of your Chromecast
    mc = TV.media_controller
    idx1=phrase.find(custom_action_keyword['Dict']['Play'])
    idx2=phrase.find('on chromecast')
    query=phrase[idx1:idx2]
    query=query.replace(custom_action_keyword['Dict']['Play'],'',1)
    query=query.replace('on chromecast','',1)
    query=query.strip()
    youtubelinks=youtube_search(query)
    youtubeurl=youtubelinks[0]
    streams=youtube_stream_link(youtubeurl)
    videostream=streams[1]
    TV.wait()
    time.sleep(1)
    mc.play_media(videostream,'video/mp4')

def chromecast_control(action):
    # Chromecast declarations
    # Do not rename/change "TV" its a variable
    TV = pychromecast.Chromecast("192.168.1.13") #Change ip to match the ip-address of your Chromecast
    mc = TV.media_controller
    if 'pause'.lower() in str(action).lower():
        TV.wait()
        time.sleep(1)
        mc.pause()
    if 'resume'.lower() in str(action).lower():
        TV.wait()
        time.sleep(1)
        mc.play()
    if 'end'.lower() in str(action).lower():
        TV.wait()
        time.sleep(1)
        mc.stop()
    if 'volume'.lower() in str(action).lower():
        if 'up'.lower() in str(action).lower():
            TV.wait()
            time.sleep(1)
            TV.volume_up(0.2)
        if 'down'.lower() in str(action).lower():
            TV.wait()
            time.sleep(1)
            TV.volume_down(0.2)

#-------------------End of Chromecast Functions---------------------------------

#-------------------Start of Kickstarter Search functions-----------------------
def campaign_page_parser(campaignname):
    page_link=kickstrater_search(campaignname)
    kicktrackurl=page_link['items'][0]['link']
    response=urllib.request.urlopen(kicktrackurl)
    webContent = response.read()
    webContent = webContent.decode('utf-8')
    return webContent

def kickstarter_get_data(page_source,parameter):
    idx=page_source.find(parameter)
    info=page_source[idx:]
    info=info.replace(parameter,"",1)
    idx=info.find('"')
    info=info[:idx]
    info=info.replace('"',"",1)
    info=info.strip()
    result=info
    return result

def get_campaign_title(campaign):
    campaigntitle=campaign
    campaigntitleidx1=campaigntitle.find('<title>')
    campaigntitleidx2=campaigntitle.find('&mdash;')
    campaigntitle=campaigntitle[campaigntitleidx1:campaigntitleidx2]
    campaigntitle=campaigntitle.replace('<title>',"",1)
    campaigntitle=campaigntitle.replace('&mdash;',"",1)
    campaigntitle=campaigntitle.strip()
    return campaigntitle

def get_pledges_offered(campaign):
    pledgesoffered=campaign
    pledgenum=0
    for num in re.finditer('pledge__reward-description pledge__reward-description--expanded',pledgesoffered):
        pledgenum=pledgenum+1
    return pledgenum

def get_funding_period(campaign):
    period=campaign
    periodidx=period.find('Funding period')
    period=period[periodidx:]
    periodidx=period.find('</p>')
    period=period[:periodidx]
    startperiodidx1=period.find('class="invisible-if-js js-adjust-time">')
    startperiodidx2=period.find('</time>')
    startperiod=period[startperiodidx1:startperiodidx2]
    startperiod=startperiod.replace('class="invisible-if-js js-adjust-time">','',1)
    startperiod=startperiod.replace('</time>','',1)
    startperiod=startperiod.strip()
    period2=period[startperiodidx2+5:]
    endperiodidx1=period2.find('class="invisible-if-js js-adjust-time">')
    endperiodidx2=period2.find('</time>')
    endperiod=period2[endperiodidx1:endperiodidx2]
    endperiod=endperiod.replace('class="invisible-if-js js-adjust-time">','',1)
    endperiod=endperiod.replace('</time>','',1)
    endperiod=endperiod.strip()
    duration=period2[endperiodidx2:]
    duration=duration.replace('</time>','',1)
    duration=duration.replace('(','',1)
    duration=duration.replace(')','',1)
    duration=duration.replace('days','day',1)
    duration=duration.strip()
    return startperiod,endperiod,duration

def kickstarter_tracker(phrase):
    idx=phrase.find('of')
    campaign_name=phrase[idx:]
    campaign_name=campaign_name.replace("kickstarter campaign", "",1)
    campaign_name = campaign_name.replace('of','',1)
    campaign_name=campaign_name.strip()
    campaign_source=campaign_page_parser(campaign_name)
    campaign_title=get_campaign_title(campaign_source)
    campaign_num_rewards=get_pledges_offered(campaign_source)
    successidx=campaign_source.find('to help bring this project to life.')
    if str(successidx)==str(-1):
        backers=kickstarter_get_data(campaign_source,'data-backers-count="')
        totalpledged=kickstarter_get_data(campaign_source,'data-pledged="')
        totaltimerem=kickstarter_get_data(campaign_source,'data-hours-remaining="')
        totaldur=kickstarter_get_data(campaign_source,'data-duration="')
        endtime=kickstarter_get_data(campaign_source,'data-end_time="')
        goal=kickstarter_get_data(campaign_source,'data-goal="')
        percentraised=kickstarter_get_data(campaign_source,'data-percent-raised="')
        percentraised=round(float(percentraised),2)
        if int(totaltimerem)>0:
            #print(campaign_title+" is an ongoing campaign with "+str(totaltimerem)+" hours of fundraising still left." )
            say(campaign_title+" is an ongoing campaign with "+str(totaltimerem)+" hours of fundraising still left." )
            #print("Till now, "+str(backers)+ " backers have pledged for "+str(campaign_num_rewards)+" diferent rewards raising $"+str(totalpledged)+" , which is "+str(percentraised)+" times the requested amount of $"+str(goal))
            say("Till now, "+str(backers)+ " backers have pledged for "+str(campaign_num_rewards)+" diferent rewards raising $"+str(totalpledged)+" , which is "+str(percentraised)+" times the requested amount of $"+str(goal))
        if float(percentraised)<1 and int(totaltimerem)<=0:
            #print(campaign_title+" has already ended")
            say(campaign_title+" has already ended")
            #print(str(backers)+ " backers raised $"+str(totalpledged)+" , which was "+str(percentraised)+" times the requested amount of $"+str(goal))
            say(str(backers)+ " backers raised $"+str(totalpledged)+" , which was "+str(percentraised)+" times the requested amount of $"+str(goal))
            #print(campaign_title+" was unseccessful in raising the requested amount of $"+str(goal)+" ." )
            say(campaign_title+" was unseccessful in raising the requested amount of $"+str(goal)+" ." )
        if float(percentraised)>1 and int(totaltimerem)<=0:
            #print(campaign_title+" has already ended")
            say(campaign_title+" has already ended")
            #print(str(backers)+ " backers raised $"+str(totalpledged)+" , which was "+str(percentraised)+" times the requested amount of $"+str(goal))
            say(str(backers)+ " backers raised $"+str(totalpledged)+" , which was "+str(percentraised)+" times the requested amount of $"+str(goal))
            #print("Though the funding goal was reached, due to reasons undisclosed, the campaign was either cancelled by the creator or Kickstarter.")
            say("Though the funding goal was reached, due to reasons undisclosed, the campaign was either cancelled by the creator or Kickstarter.")
    else:
        [start_day,end_day,numdays]=get_funding_period(campaign_source)
        campaigninfo=campaign_source[(successidx-100):(successidx+35)]
        campaignidx=campaigninfo.find('<b>')
        campaigninfo=campaigninfo[campaignidx:]
        campaigninfo=campaigninfo.replace('<b>',"",1)
        campaigninfo=campaigninfo.replace('</b>',"",1)
        campaigninfo=campaigninfo.replace('<span class="money">',"",1)
        campaigninfo=campaigninfo.replace('</span>',"",1)
        campaigninfo=campaigninfo.strip()
        #print(campaign_title+" was a "+str(numdays)+" campaign launched on "+str(start_day))
        #print(campaigninfo)
        say(campaign_title+" was a "+str(numdays)+" campaign launched on "+str(start_day))
        say(campaigninfo)

#------------------------------End of Kickstarter Search functions---------------------------------------


#----------------------------------Start of Push Message function-----------------------------------------
def pushmessage(title,body):
    if pb!=None:
        push = pb.push_note(title,body)
    else:
        say("Pushbullet API key has not been entered.")
#----------------------------------End of Push Message Function-------------------------------------------


#----------------------------------Start of recipe Function----------------------------------------------
def getrecipe(item):
    appid='ENTER-YOUR-APPID-HERE'
    appkey='ENTER-YOUR-APP-KEY-HERE'
    recipeurl = 'https://api.edamam.com/search?q='+item+'&app_id='+appid+'&app_key='+appkey
    print(recipeurl)
    recipedetails = urllib.request.urlopen(recipeurl)
    recipedetails=recipedetails.read()
    recipedetails = recipedetails.decode('utf-8')
    recipedetails=json.loads(recipedetails)
    recipe_ingredients=str(recipedetails['hits'][0]['recipe']['ingredientLines'])
    recipe_url=recipedetails['hits'][0]['recipe']['url']
    recipe_name=recipedetails['hits'][0]['recipe']['label']
    recipe_ingredients=recipe_ingredients.replace('[','',1)
    recipe_ingredients=recipe_ingredients.replace(']','',1)
    recipe_ingredients=recipe_ingredients.replace('"','',1)
    recipe_ingredients=recipe_ingredients.strip()
    print(recipe_name)
    print("")
    print(recipe_url)
    print("")
    print(recipe_ingredients)
    compiled_recipe_info="\nRecipe Source URL:\n"+recipe_url+"\n\nRecipe Ingredients:\n"+recipe_ingredients
    pushmessage(str(recipe_name),str(compiled_recipe_info))

#---------------------------------End of recipe Function------------------------------------------------


#--------------------------------Start of Hue Control Functions------------------------------------------

def hue_control(phrase,lightindex,lightaddress):
    with open('/opt/hue-emulator/config.json', 'r') as config:
         hueconfig = json.load(config)
    currentxval=hueconfig['lights'][lightindex]['state']['xy'][0]
    currentyval=hueconfig['lights'][lightindex]['state']['xy'][1]
    currentbri=hueconfig['lights'][lightindex]['state']['bri']
    currentct=hueconfig['lights'][lightindex]['state']['ct']
    huelightname=str(hueconfig['lights'][lightindex]['name'])
    try:
        if custom_action_keyword['Dict']['On'] in phrase:
            huereq=requests.head("http://"+lightaddress+"/set?light="+lightindex+"&on=true")
            say("Turning on "+huelightname)
        if custom_action_keyword['Dict']['Off'] in phrase:
            huereq=requests.head("http://"+lightaddress+"/set?light="+lightindex+"&on=false")
            say("Turning off "+huelightname)
        if 'çolor' in phrase:
            rcolour,gcolour,bcolour,hexcolour,colour=getcolours(phrase)
            print(str([rcolour,gcolour,bcolour,hexcolour,colour]))
            xval,yval=convert_rgb_xy(int(rcolour),int(gcolour),int(bcolour))
            print(str([xval,yval]))
            huereq=requests.head("http://"+lightaddress+"/set?light="+lightindex+"&x="+str(xval)+"&y="+str(yval)+"&on=true")
            print("http://"+lightaddress+"/set?light="+lightindex+"&x="+str(xval)+"&y="+str(yval)+"&on=true")
            say("Setting "+huelightname+" to "+colour)
        if (custom_action_keyword['Dict']['Brightness']).lower() in phrase:
            if 'hundred'.lower() in phrase or custom_action_keyword['Dict']['Maximum'] in phrase:
                bright=100
            elif 'zero'.lower() in phrase or custom_action_keyword['Dict']['Minimum'] in phrase:
                bright=0
            else:
                bright=re.findall('\d+', phrase)
            brightval= (bright/100)*255
            huereq=requests.head("http://"+lightaddress+"/set?light="+lightindex+"&on=true&bri="+str(brightval))
            say("Changing "+huelightname+" brightness to "+bright+" percent")
    except (requests.exceptions.ConnectionError,TypeError) as errors:
        if str(errors)=="'NoneType' object is not iterable":
            print("Type Error")
        else:
            say("Device not online")

#------------------------------End of Hue Control Functions---------------------------------------------

#------------------------------Start of Spotify Functions-----------------------------------------------

def show_spotify_track_names(tracks):
    spotify_tracks=[]
    for i, item in enumerate(tracks['items']):
        track = item['track']
##        print ("%d %32.32s %s" % (i, track['artists'][0]['name'],track['name']))
        # print ("%s %s" % (track['artists'][0]['name'],track['name']))
        spotify_tracks.append("%s %s" % (track['artists'][0]['name'],track['name']))
    return spotify_tracks

def scan_spotify_playlists():
    if spotify_token:
        i=0
        playlistdetails=[]
        spotify_tracks_list=[]
        sp = spotipy.Spotify(auth=spotify_token)
        # print(sp.user(username))
        # print("")
        # print("")
        playlists = sp.user_playlists(username)
        print(len(playlists['items']))
        num_playlists=len(playlists['items'])
        spotify_playlists={"Playlists":[0]*(len(playlists['items']))}
        # print(spotify_playlists)
        # print("")
        # print("")
        for playlist in playlists['items']:
            # print (playlist['name'])
            playlist_name=playlist['name']
            # print("")
            # print("")
##            print ('  total tracks', playlist['tracks']['total'])
##            print("")
##            print("")
            results = sp.user_playlist(playlist['owner']['id'], playlist['id'],fields="tracks,next")
            tracks = results['tracks']
            spotify_tracks_list=show_spotify_track_names(tracks)
            playlistdetails.append(i)
            playlistdetails.append(playlist_name)
            playlistdetails.append(spotify_tracks_list)
            spotify_playlists['Playlists'][i]=playlistdetails
            playlistdetails=[]
            i=i+1
        # print("")
        # print("")
        # print(spotify_playlists['Playlists'])
        return spotify_playlists, num_playlists
    else:
        say("Can't get token for, " + username)
        print("Can't get token for ", username)

def spotify_playlist_select(phrase):
    trackslist=[]
    currenttrackid=0
    idx1=phrase.find(custom_action_keyword['Dict']['Play'])
    idx2=phrase.find(custom_action_keyword['Dict']['From_spotify'])
    track=phrase[idx1:idx2]
    track = track.replace(custom_action_keyword['Dict']['Play'],'',1)
    track = track.replace(custom_action_keyword['Dict']['From_spotify'],'',1)
    track=track.strip()
    say("Getting music links")
    print(track)
    playlists,num=scan_spotify_playlists()
    if not num==[]:
        for i in range(0,num):
            print(str(playlists['Playlists'][i][1]).lower())
            if track in str(playlists['Playlists'][i][1]).lower():
                trackslist=playlists['Playlists'][i][2]
                break
        if not trackslist==[]:
            vlcplayer.media_manager(trackslist,'Spotify')
            vlcplayer.spotify_player(currenttrackid)
    else:
        say("Unable to find matching playlist")

#----------------------End of Spotify functions---------------------------------

#----------------------Start of Domoticz Control Functions----------------------
def domoticz_control(query,index,devicename):
    global hexcolour,bright,devorder
    try:
        for j in range(0,len(domoticz_devices['result'])):
            if domoticz_devices['result'][j]['idx']==index:
                devorder=j
                break

        if (' ' + custom_action_keyword['Dict']['On'] + ' ') in query or (' ' + custom_action_keyword['Dict']['On']) in query or (custom_action_keyword['Dict']['On'] + ' ') in query:
            devreq=requests.head("https://" + configuration['Domoticz']['Server_IP'][0] + ":" + configuration['Domoticz']['Server_port'][0] + "/json.htm?type=command&param=switchlight&idx=" + index + "&switchcmd=On",verify=False)
            say('Turning on ' + devicename )
        if custom_action_keyword['Dict']['Off'] in query:
            devreq=requests.head("https://" + configuration['Domoticz']['Server_IP'][0] + ":" + configuration['Domoticz']['Server_port'][0] + "/json.htm?type=command&param=switchlight&idx=" + index + "&switchcmd=Off",verify=False)
            say('Turning off ' + devicename )
        if 'toggle' in query:
            devreq=requests.head("https://" + configuration['Domoticz']['Server_IP'][0] + ":" + configuration['Domoticz']['Server_port'][0] + "/json.htm?type=command&param=switchlight&idx=" + index + "&switchcmd=Toggle",verify=False)
            say('Toggling ' + devicename )
        if custom_action_keyword['Dict']['Colour'] in query:
            if 'RGB' in domoticz_devices['result'][devorder]['SubType']:
                rcolour,gcolour,bcolour,hexcolour,colour=getcolours(query)
                hexcolour=hexcolour.replace("#","",1)
                hexcolour=hexcolour.strip()
                print(hexcolour)
                if bright=='':
                    bright=str(domoticz_devices['result'][devorder]['Level'])
                devreq=requests.head("https://" + configuration['Domoticz']['Server_IP'][0] + ":" + configuration['Domoticz']['Server_port'][0] + "/json.htm?type=command&param=setcolbrightnessvalue&idx=" + index + "&hex=" + hexcolour + "&brightness=" + bright + "&iswhite=false",verify=False)
                say('Setting ' + devicename + ' to ' + colour )
            else:
                say('The requested light is not a colour bulb')
        if custom_action_keyword['Dict']['Brightness'] in query:
            if domoticz_devices['result'][devorder]['HaveDimmer']:
                if 'hundred' in query or 'hundred'.lower() in query or custom_action_keyword['Dict']['Maximum'] in query:
                    bright=str(100)
                elif 'zero' in query or custom_action_keyword['Dict']['Minimum'] in query:
                    bright=str(0)
                else:
                    bright=re.findall('\d+', query)
                    bright=bright[0]
                devreq=requests.head("https://" + configuration['Domoticz']['Server_IP'][0] + ":" + configuration['Domoticz']['Server_port'][0] + "/json.htm?type=command&param=switchlight&idx=" + index + "&switchcmd=Set%20Level&level=" + bright ,verify=False)
                say('Setting ' + devicename + ' brightness to ' + str(bright) + ' percent.')
            else:
                say('The requested light does not have a dimer')

    except (requests.exceptions.ConnectionError,TypeError) as errors:
        if str(errors)=="'NoneType' object is not iterable":
            print("Type Error")
        else:
            say("Device or Domoticz server is not online")
#------------------------End of Domoticz Control Functions----------------------

#------------------------Start of Gaana Functions-------------------------------
def getgaanaplaylistinfo(playlisturl):
    trackstart=[]
    trackend=[]
    playliststart=[]
    playlistend=[]
    trackdetails=[]
    response=urllib.request.urlopen(playlisturl)
    response=response.read().decode('utf-8')
    for a in re.finditer('{"title":',response):
        trackstart.append(a.start())
    for b in re.finditer('"parental_warning":(.*)}',response):
        trackend.append(b.end())
    for c in re.finditer('{"source":',response):
        playliststart=c.start()
    for d in re.finditer('}</span>',response):
        playlistend=int(d.start())+1
    playlistinfo=json.loads(response[playliststart:playlistend])
    playlistname=playlistinfo['title']
    if len(trackstart)==len(trackend) and len(trackstart)>0:
        for i in range(0,len(trackstart)):
            trackdetails.append(json.loads(response[trackstart[i]:trackend[i]]))
    else:
        trackdetails=[]
    numtracks=len(trackdetails)
    return playlistname,numtracks,trackdetails

def gaana_playlist_select(phrase):
    trackslist=[]
    currenttrackid=0
    idx1=phrase.find(custom_action_keyword['Dict']['Play'])
    idx2=phrase.find(custom_action_keyword['Dict']['From_gaana'])
    track=phrase[idx1:idx2]
    track = track.replace(custom_action_keyword['Dict']['Play'],'',1)
    track = track.replace(custom_action_keyword['Dict']['From_gaana'],'',1)
    track=track.strip()
    playlistnumreq=re.findall(r'\b\d+\b', track)
    if playlistnumreq !=[]:
        playlistnumreq=playlistnumreq[0]
    userplaylists=configuration['Gaana']['Playlist']
    numuserplaylists=len(userplaylists)
    if playlistnumreq !=[] and "top" not in track and int(playlistnumreq) <= int(numuserplaylists):
        print("Getting links for playlist number " + playlistnumreq)
        say("Getting links for playlist number " + playlistnumreq)
        reqplaylist=configuration['Gaana']['Playlist'][(int(playlistnumreq)-1)]
    else:
        print("Searching for " + track +  " in gaana.com")
        say("Searching for " + track +  " in gaana.com")
        page_link=gaana_search(track)
        reqplaylist=page_link['items'][0]['link']
    name,numsongs,tracks= getgaanaplaylistinfo(reqplaylist)
    print(numsongs)
    if not numsongs==[]:
        say("Getting the tracks from " + name)
        for i in range(0,numsongs):
            trackslist.append((tracks[i]['title'] + ' ' + tracks[i]['albumtitle']))
        if not trackslist==[]:
            vlcplayer.media_manager(trackslist,'Gaana')
            vlcplayer.gaana_player(currenttrackid)
    else:
        say("Unable to find matching playlist")

#------------------------End of Gaana Functions-------------------------------

#------------------------Start of Deezer Functions-------------------------------
def deezer_playlist_select(phrase):
    trackslist=[]
    deezer_user_playlists=[]
    currenttrackid=0
    idx1=phrase.find(custom_action_keyword['Dict']['Play'])
    idx2=phrase.find(custom_action_keyword['Dict']['From_deezer'])
    track=phrase[idx1:idx2]
    track = track.replace(custom_action_keyword['Dict']['Play'],'',1)
    track = track.replace(custom_action_keyword['Dict']['From_deezer'],'',1)
    track=track.strip()
    playlistnumreq=re.findall(r'\b\d+\b', track)
    if playlistnumreq !=[]:
        playlistnumreq=playlistnumreq[0]
    deezer_response = requests.get("https://api.deezer.com/user/" + configuration['Deezer']['User_id'] + "/playlists",verify=False)
    deezer_user_playlist_info=json.loads(deezer_response.text)
    if deezer_user_playlist_info['data'] != []:
        for i in range(0,len(deezer_user_playlist_info['data'])):
            deezer_user_playlists.append(deezer_user_playlist_info['data'][i]['tracklist'])
    else:
        say("No playlists found for the user")
    numuserplaylists=len(deezer_user_playlists)
    if playlistnumreq !=[] and "top" not in track and int(playlistnumreq) <= int(numuserplaylists):
        print("Getting links for playlist number " + playlistnumreq)
        say("Getting links for playlist number " + playlistnumreq)
        tracklisturl=deezer_user_playlists[(int(playlistnumreq)-1)]
    else:
        say("No matching playlists found")
    deezer_tracks_response = requests.get(tracklisturl,verify=False)
    deezer_user_playlist_tracks_info=json.loads(deezer_tracks_response.text)
    numsongs=len(deezer_user_playlist_tracks_info['data'])
    if not numsongs==[]:
        say("Getting the tracks from " + deezer_user_playlist_info['data'][int(playlistnumreq)-1]['title'])
        for i in range(0,numsongs):
            trackslist.append((deezer_user_playlist_tracks_info['data'][i]['title'] + ' by ' + deezer_user_playlist_tracks_info['data'][i]['artist']['name'] + ' from ' + deezer_user_playlist_tracks_info['data'][i]['album']['title']))
        if not trackslist==[]:
            vlcplayer.media_manager(trackslist,'Deezer')
            vlcplayer.gaana_player(currenttrackid)
    else:
        say("Unable to find matching tracks")

#------------------------End of Deezer Functions-------------------------------

#-----------------------Start of functions for IR code--------------------------

def binary_aquire(pin, duration):
    t0 = time.time()
    results = []
    while (time.time() - t0) < duration:
        results.append(GPIO.input(pin))
    return results

def on_ir_receive(pinNo, bouncetime=150):
    data = binary_aquire(pinNo, bouncetime/1000.0)
    if len(data) < bouncetime:
        return
    rate = len(data) / (bouncetime / 1000.0)
    pulses = []
    i_break = 0
    for i in range(1, len(data)):
        if (data[i] != data[i-1]) or (i == len(data)-1):
            pulses.append((data[i-1], int((i-i_break)/rate*1e6)))
            i_break = i
    outbin = ""
    for val, us in pulses:
        if val != 1:
            continue
        if outbin and us > 2000:
            break
        elif us < 1000:
            outbin += "0"
        elif 1000 < us < 2000:
            outbin += "1"
    try:
        return int(outbin, 2)
    except ValueError:
        return None

#-----------------------End of functions for IR code--------------------------

#-----------------------Start of functions for Wemo/Emulated Wemo-------------

def wemodiscovery():
    devices = pywemo.discover_devices()
    if devices!=[]:
        with open('{}/wemodevicelist.json'.format(USER_PATH), 'w') as devicelist:
               json.dump(devices, devicelist)
        if len(devices)>1:
            say("Found "+str(len(devices))+" devices.")
        else:
            say("Found "+str(len(devices))+" device.")
    else:
        say("Unable to find any active device.")

def wemocontrol(command):
    if os.path.isfile("{}/wemodevicelist.json".format(USER_PATH)):
        with open('{}/wemodevicelist.json'.format(USER_PATH), 'r') as devicelist:
            wemodevices = json.load(devicelist)
        if wemodevices!=[]:
            for i in range(0,len(wemodevices)):
                if wemodevices[i] in command:
                    if (' ' + custom_action_keyword['Dict']['On'] + ' ') in command or (' ' + custom_action_keyword['Dict']['On']) in query or (custom_action_keyword['Dict']['On'] + ' ') in command:
                        wemodevices[i].on()
                        say("Turning on "+wemodevices[i])
                    elif custom_action_keyword['Dict']['Off'] in command:
                        wemodevices[i].on()
                        say("Turning off "+wemodevices[i])
                    break
        else:
            say("Device list is empty. Try running the device discovery.")
    else:
        say("Unable to find device registry. Try running the device discovery.")

#-----------------------End of functions for Wemo/Emulated Wemo-------------

#Send voicenote to phone
def voicenote(audiofile):
    if pb!=None:
        say("Sending your voicenote")
        with open(audiofile, "rb") as recordedvoicenote:
            file_data = pb.upload_file(recordedvoicenote, 'Voicenote.wav')
        push = pb.push_file(**file_data)
    else:
        say("Pushbullet API key has not been entered.")

#GPIO Device Control
def Action(phrase):
    if 'shutdown' in phrase:
        say('Shutting down Raspberry Pi')
        time.sleep(10)
        os.system("sudo shutdown -h now")
        #subprocess.call(["shutdown -h now"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if 'servo' in phrase:
        for s in re.findall(r'\b\d+\b', phrase):
            SetAngle(int(s))
        if 'zero' in phrase:
            SetAngle(0)
    else:
        if GPIOcontrol:
            for num, name in enumerate(var):
                if name.lower() in phrase:
                    pinout=gpio[num]
                    if custom_action_keyword['Dict']['On'] in phrase:
                        GPIO.output(pinout, 1)
                        say("Turning On " + name)
                    elif custom_action_keyword['Dict']['Off'] in phrase:
                        GPIO.output(pinout, 0)
                        say("Turning Off " + name)
        else:
            say("GPIO controls, is not supported for your device.")
