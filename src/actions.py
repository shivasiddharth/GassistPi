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
musicdirectory="/home/pi/Downloads/Music/"
videodirectory="/home/pi/Downloads/Video/"


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

#Function to get Kodi Volume and Mute status
def mutevolstatus():
    status= kodi.Application.GetProperties({"properties": ("volume","muted")})
    mutestatus=(volmutstatus["result"]["muted"])
    volstatus=(volmutstatus["result"]["volume"])
    return mutestatus, volstatus


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


#Function to fetch tracks from an album
def kodialbum(query):
    albumcontents=[]
    kodi.Playlist.Clear(playlistid=0)
    songs=kodi.AudioLibrary.GetSongs({ "limits": { "start" : 0, "end": 200 }, "properties": [ "artist", "duration", "album", "track" ], "sort": { "order": "ascending", "method": "track", "ignorearticle": True } })
    print(songs)
    for root, directories, files in os.walk(musicdirectory):
        musicfiles=kodi.Files.GetDirectory({"directory": root, "media": "music"})
        print(musicfiles)
        nummusicfiles=len(musicfiles["result"]["files"])
        numsongs=len(songs["result"]["songs"])
        i=0
        j=0
        for i in range(0,numsongs):
            if query.lower() in str(songs["result"]["songs"][i]["album"]).lower():
                for j in range(0,nummusicfiles):
                    name=musicfiles["result"]["files"][j]["label"]
                    if str(songs["result"]["songs"][i]["label"]).lower() in str(name).lower():
                        path=musicfiles["result"]["files"][j]["file"]
                        albumcontents.append(songs["result"]["songs"][i]["label"])
                        kodi.Playlist.Add(playlistid=0, item={"file": path})

    if len(albumcontents)!=0:
        print(albumcontents)
        playinginfo=("Playing "+str(len(albumcontents))+" tracks from album")
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
        feedback=("Album, "+reqalbum+"found")
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


#Function to play requested single track or video/movie on kodi
def singleplaykodi(query):
    kodi.Playlist.Clear(playlistid=0)
    i=0
    idx=query.find('play')
    track=query[idx:]
    track=track.replace("'}", "",1)
    track = track.replace('play','',1)
    track = track.replace('on kodi','',1)
    track=track.strip()
    say("Searching for your file")
    if 'song'.lower() in str(track).lower() or 'track'.lower() in str(track).lower() or 'audio'.lower() in str(track).lower():
        track = track.replace('song','',1)
        track=track.strip()
        musicfiles=kodi.Files.GetDirectory({"directory": musicdirectory, "media": "music"})
        nummusicfiles=len(musicfiles["result"]["files"])
        print("Total number of files: "+ str(nummusicfiles))
        for i in range(0,nummusicfiles):
           name=musicfiles["result"]["files"][i]["label"]
           if str(track).lower() in str(name).lower():
               print('Matching file found')
               path=musicfiles["result"]["files"][i]["file"]
               print(path)
               say("Playing "+name+" song")
               kodi.Player.open(item={"file": path})
    elif 'movie'.lower() in str(track).lower() or 'video'.lower() in str(track).lower():
        track = track.replace('movie','',1)
        track=track.strip()
        videofiles=kodi.Files.GetDirectory({"directory": musicdirectory, "media": "video"})
        numvideofiles=len(videofiles["result"]["files"])
        print("Total number of files: "+ str(numvideofiles))
        for i in range(0,numvideofiles):
           name=videofiles["result"]["files"][i]["label"]
           if str(track).lower() in str(name).lower():
               print('Matching file found')
               path=videofiles["result"]["files"][i]["file"]
               print(path)
               say("Playing "+name+" movie")
               kodi.Player.open(item={"file": path})
    else:
        say("Sorry, I am unable to help you with that now")


#Function to check what is currently playing
def whatisplaying():
    players=kodi.Player.GetActivePlayers()
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


#Functions for actions on KODI
def kodiactions(phrase):
    if 'youtube'.lower() in str(phrase).lower():
        query=str(phrase).lower()
        idx=query.find('play')
        track=query[idx:]
        track=track.replace("'}", "",1)
        track = track.replace('play','',1)
        track = track.replace('on kodi','',1)
        if 'youtube'.lower() in track:
            track=track.replace('youtube','',1)
        elif 'video'.lower() in track:
            track=track.replace('video','',1)
        else:
            track=track.strip()
        print(track)
        say("Fetching YouTube links for, "+track)
        youtube_search(track)
    elif 'what'.lower() in str(phrase).lower() and 'playing'.lower() in str(phrase).lower():
        whatisplaying()
    elif 'play'.lower() in str(phrase).lower() and 'album'.lower() in str(phrase).lower():
        albumretrieve(phrase)
    elif 'play'.lower() in str(phrase).lower() and ('audio'.lower() in str(phrase).lower() or 'movie'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'video'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower()):
        singleplaykodi(phrase)
    elif 'shuffle'.lower() in str(phrase).lower() and ('audio'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower() or 'music'.lower() in str(phrase).lower()):
        kodi.Playlist.Clear(playlistid=0)
        musicfiles=kodi.Files.GetDirectory({"directory": musicdirectory, "media": "music"})
        nummusicfiles=len(musicfiles["result"]["files"])
        for i in range(0,nummusicfiles):
           path=musicfiles["result"]["files"][i]["file"]
           kodi.Playlist.Add(playlistid=0, item={"file": path})
        kodi.Player.open(item={"playlistid": 0},options={"repeat": "all"})
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        kodi.Player.SetShuffle({"playerid":0,"shuffle":True})
    elif 'repeat'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        if 'this'.lower() in str(phrase).lower() or 'one'.lower() in str(phrase).lower() or str(1).lower() in str(phrase).lower():
            kodi.Player.SetRepeat({"playerid": playid,"repeat": "one"})
        elif 'all'.lower() in str(phrase).lower():
            kodi.Player.SetRepeat({"playerid": playid,"repeat": "all"})
        elif 'off'.lower() in str(phrase).lower() or 'disable'.lower() in str(phrase).lower() or 'none'.lower() in str(phrase).lower():
            kodi.Player.SetRepeat({"playerid": playid,"repeat": "one"})
    elif 'shuffle'.lower() in str(phrase).lower() and 'turn'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        if 'on'.lower() in str(phrase).lower():
            kodi.Player.SetShuffle({"playerid": playid,"shuffle":True})
        elif 'off'.lower() in str(phrase).lower():
            kodi.Player.SetShuffle({"playerid": playid,"shuffle":False})
    elif 'play'.lower() in str(phrase).lower() and 'next'.lower() in str(phrase).lower() or ('audio'.lower() in str(phrase).lower() or 'video'.lower() in str(phrase).lower() or 'movie'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower()):
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        kodi.Player.GoTo({"playerid":playid,"to":"next"})
    elif 'play'.lower() in str(phrase).lower() and 'previous'.lower() in str(phrase).lower() or ('audio'.lower() in str(phrase).lower() or 'video'.lower() in str(phrase).lower() or 'movie'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower()):
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
    elif 'set'.lower() in str(phrase).lower() and 'volume'.lower() in str(phrase).lower():
        for s in re.findall(r'\b\d+\b', phrase):
            kodi.Application.SetVolume({"volume": int(s)})
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
    elif 'home'.lower() in str(phrase).lower() and 'go'.lower() in str(phrase).lower():
        kodi.GUI.ActivateWindow({"window":"home"})
    elif 'player'.lower() in str(phrase).lower() and ('go'.lower() in str(phrase).lower() or 'open'.lower() in str(phrase).lower()):
        kodi.GUI.ActivateWindow({"window":"playercontrols"})
    elif 'videos'.lower() in str(phrase).lower() and ('go'.lower() in str(phrase).lower() or 'open'.lower() in str(phrase).lower()):
        kodi.GUI.ActivateWindow({"window":"videos"})
    elif 'music'.lower() in str(phrase).lower() and ('go'.lower() in str(phrase).lower() or 'open'.lower() in str(phrase).lower()):
        kodi.GUI.ActivateWindow({"window":"music"})
    elif 'settings'.lower() in str(phrase).lower() and ('go'.lower() in str(phrase).lower() or 'open'.lower() in str(phrase).lower()):
        kodi.GUI.ActivateWindow({"window":"settings"})


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
