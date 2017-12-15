#!/usr/bin/env python

#This is different from AIY Kit's actions
#Copying and Pasting AIY Kit's actions commands will not work

from kodijson import Kodi, PLAYER_VIDEO
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import os.path
import RPi.GPIO as GPIO
import time
import re
import subprocess
import aftership
import feedparser

#YouTube API Constants
DEVELOPER_KEY = 'AIzaSyALGk9d83bEHg_Nnn5VP-AH53aI0D3Crbc'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

#Login with default kodi/kodi credentials
#kodi = Kodi("http://localhost:8080/jsonrpc")

#Login with custom credentials
# Kodi("http://IP-ADDRESS-OF-KODI:8080/jsonrpc", "username", "password")
kodi = Kodi("http://localhost:8080/jsonrpc", "kodi", "kodi")

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#Number of entities in 'var' and 'PINS' should be the same
var = ('kitchen lights', 'bathroom lights', 'bedroom lights')#Add whatever names you want. This is case is insensitive
gpio = (12,13,24)#GPIOS for 'var'. Add other GPIOs that you want

#Number of station names and station links should be the same
stnname=('Radio One', 'Radio 2', 'Radio 3', 'Radio 5')#Add more stations if you want
stnlink=('http://www.radiofeeds.co.uk/bbcradio2.pls', 'http://www.radiofeeds.co.uk/bbc6music.pls', 'http://c5icy.prod.playlists.ihrhls.com/1469_icy', 'http://playerservices.streamtheworld.com/api/livestream-redirect/ARNCITY.mp3')

#IP Address of ESP
ip='xxxxxxxxxxxx'

#Declaration of ESP names
devname=('Device 1', 'Device 2', 'Device 3')
devid=('/Device1', '/Device2', '/Device3')

for pin in gpio:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

#Servo pin declaration
GPIO.setup(27, GPIO.OUT)
pwm=GPIO.PWM(27, 50)
pwm.start(0)

#Stopbutton
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#Led Indicator
GPIO.setup(25, GPIO.OUT)
led=GPIO.PWM(25,1)
led.start(0)

playshell = None

#Parcel Tracking declarations
#If you want to use parcel tracking, register for a free account at: https://www.aftership.com
#Add the API number and uncomment next two lines
#api = aftership.APIv4('YOUR-AFTERSHIP-API-NUMBER')
#couriers = api.couriers.all.get()
number = ''
slug=''

#RSS feed URLS
worldnews = "http://feeds.bbci.co.uk/news/world/rss.xml"
technews = "http://feeds.bbci.co.uk/news/technology/rss.xml"
topnews = "http://feeds.bbci.co.uk/news/rss.xml"
sportsnews = "http://feeds.feedburner.com/ndtvsports-latest"
quote = "http://feeds.feedburner.com/brainyquote/QUOTEBR"


#Text to speech converter
def say(words):
    tempfile = "temp.wav"
    devnull = open("/dev/null","w")
    lang = "en-GB" #Other languages: en-US: US English, en-GB: UK English, de-DE: German, es-ES: Spanish, fr-FR: French, it-IT: Italian
    subprocess.call(["pico2wave", "-w", tempfile, "-l", lang,  words],stderr=devnull)
    subprocess.call(["aplay", tempfile],stderr=devnull)
    os.remove(tempfile)

#Radio Station Streaming
def radio(phrase):
    for num, name in enumerate(stnname):
        if name.lower() in phrase:
            station=stnlink[num]
            say("Tuning into " + name)
            p = subprocess.Popen(["/usr/bin/vlc",station],stdin=subprocess.PIPE,stdout=subprocess.PIPE)

#ESP6266 Devcies control
def ESP(phrase):
    for num, name in enumerate(devname):
        if name.lower() in phrase:
            dev=devid[num]
            if 'on' in phrase:
                ctrl='=ON'
                say("Turning On " + name)
            elif 'off' in phrase:
                ctrl='=OFF'
                say("Turning Off " + name)
            subprocess.Popen(["elinks", ip + dev + ctrl],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            time.sleep(2)
            subprocess.Popen(["/usr/bin/pkill","elinks"],stdin=subprocess.PIPE)

#Stepper Motor control
def SetAngle(angle):
    duty = angle/18 + 2
    GPIO.output(27, True)
    say("Moving motor by " + str(angle) + " degrees")
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    pwm.ChangeDutyCycle(0)
    GPIO.output(27, False)

#Play Youtube Music
def YouTube(phrase):
    idx=phrase.find('play')
    track=phrase[idx:]
    track=track.replace("'}", "",1)
    track = track.replace('play','',1)
    track=track.strip()
    global playshell
    if (playshell == None):
        playshell = subprocess.Popen(["/usr/local/bin/mpsyt",""],stdin=subprocess.PIPE ,stdout=subprocess.PIPE)

    print("Playing: " + track)
    say("Playing " + track)
    playshell.stdin.write(bytes('/' + track + '\n1\n','utf-8'))
    playshell.stdin.flush()

def stop():
    pkill = subprocess.Popen(["/usr/bin/pkill","vlc"],stdin=subprocess.PIPE)

#Parcel Tracking
def track():
    text=api.trackings.get(tracking=dict(slug=slug, tracking_number=number))
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
    elif 'my feed' in phrase:
        URL=quote
    numfeeds=10
    feed=feedparser.parse(URL)
    feedlength=len(feed['entries'])
    print(feedlength)
    if feedlength<numfeeds:
        numfeeds=feedlength
    title=feed['feed']['title']
    say(title)
    #To stop the feed, press and hold stop button
    while GPIO.input(23):
        for x in range(0,numfeeds):
            content=feed['entries'][x]['title']
            print(content)
            say(content)
            summary=feed['entries'][x]['summary']
            print(summary)
            say(summary)
            if not GPIO.input(23):
              break
        if x == numfeeds-1:
            break
        else:
            continue

            
#Function to search YouTube and get videoid
def youtube_search(query):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  req=query
  # Call the search.list method to retrieve results matching the specified
  # query term.
  search_response = youtube.search().list(
    q=query,
    part='id,snippet'
  ).execute()

  videos = []
  channels = []
  playlists = []
  videoids = []
  channelids = []
  playlistids = []

  # Add each result to the appropriate list, and then display the lists of
  # matching videos, channels, and playlists.

  for search_result in search_response.get('items', []):
                  
    if search_result['id']['kind'] == 'youtube#video':
      videos.append('%s (%s)' % (search_result['snippet']['title'],
                                 search_result['id']['videoId']))
      videoids.append(search_result['id']['videoId'])

    elif search_result['id']['kind'] == 'youtube#channel':
      channels.append('%s (%s)' % (search_result['snippet']['title'],
                                   search_result['id']['channelId']))
      channelids.append(search_result['id']['channelId'])

    elif search_result['id']['kind'] == 'youtube#playlist':
      playlists.append('%s (%s)' % (search_result['snippet']['title'],
                                    search_result['id']['playlistId']))
      playlistids.append(search_result['id']['playlistId'])

  #Results of YouTube search. If you wish to see the results, uncomment them
  # print 'Videos:\n', '\n'.join(videos), '\n'
  # print 'Channels:\n', '\n'.join(channels), '\n'
  # print 'Playlists:\n', '\n'.join(playlists), '\n'

  #Checks if your query is for a channel, playlist or a video and changes the URL accordingly
  if 'channel'.lower() in  str(req).lower() and len(channels)!=0:
      urlid=channelids[0]
      YouTubeURL=("https://www.youtube.com/watch?v="+channelids[0])
  elif 'playlist'.lower() in  str(req).lower() and len(playlists)!=0:
      urlid=playlistids[0]
      YouTubeURL=("https://www.youtube.com/watch?v="+playlistids[0])
  else:
      urlid=videoids[0]
      YouTubeURL=("https://www.youtube.com/watch?v="+videoids[0])

 #If you want to see the URL, uncomment the following line
 #print(YouTubeURL)

 #Instead of sending it to Kodi, if you want to locally play in VLC, uncomment the following two lines and comment the next two lines
 #os.system("vlc "+YouTubeURL)
 #say("Playing YouTube video")

  kodi.Player.open(item={"file":"plugin://plugin.video.youtube/?action=play_video&videoid=" + urlid})
  say("Playing YouTube video on Kodi")



#GPIO Device Control
def Action(phrase):
    if 'shut down' in phrase:
        say('Shutting down Raspberry Pi')
        time.sleep(10)
        os.system("sudo shutdown -h now")
        #subprocess.call(["shutdown -h now"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if 'motor' in phrase:
        for s in re.findall(r'\b\d+\b', phrase):
            SetAngle(int(s))
    if 'zero' in phrase:
        SetAngle(0)
    else:
        for num, name in enumerate(var):
            if name.lower() in phrase:
                pinout=gpio[num]
                if 'on' in phrase:
                    GPIO.output(pinout, 1)
                    say("Turning On " + name)
                elif 'off' in phrase:
                    GPIO.output(pinout, 0)
                    say("Turning Off " + name)
