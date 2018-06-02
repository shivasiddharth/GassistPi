#!/usr/bin/env python

#This is different from AIY Kit's actions
#Copying and Pasting AIY Kit's actions commands will not work

from kodijson import Kodi, PLAYER_VIDEO
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from gmusicapi import Mobileclient
from googletrans import Translator
from pushbullet import Pushbullet
from vlc import EventType, Instance
from gtts import gTTS
import requests
import os
import os.path
import RPi.GPIO as GPIO
import time
import re
import subprocess
import aftership
import feedparser
import json
import urllib.request
import pafy
import pychromecast


vlc = Instance()

#API Key for YouTube and KS Search Engine
google_cloud_api_key='ENTER-YOUR-GOOGLE-CLOUD-API-KEY-HERE'

#Google Music Declarations
song_ids=[]
track_ids=[]
api = Mobileclient()
#If you are using two-step authentication, use app specific password. For guidelines, go through README
logged_in = api.login('ENTER_YOUR_EMAIL_HERE', 'ENETER_YOUR_PASSWORD', Mobileclient.FROM_MAC_ADDRESS)


#YouTube API Constants
DEVELOPER_KEY = google_cloud_api_key
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

#Login with default kodi/kodi credentials
#kodi = Kodi("http://localhost:8080/jsonrpc")

#Login with custom credentials
# Kodi("http://IP-ADDRESS-OF-KODI:8080/jsonrpc", "username", "password")
kodi = Kodi("http://192.168.1.15:8080/jsonrpc", "kodi", "kodi")
musicdirectory="/home/osmc/Music/"
videodirectory="/home/osmc/Movies/"
windowcmd=["Home","Settings","Weather","Videos","Music","Player"]
window=["home","settings","weather","videos","music","playercontrols"]


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#Number of entities in 'var' and 'PINS' should be the same
var = ('kitchen lights', 'bathroom lights', 'bedroom lights')#Add whatever names you want. This is case is insensitive
gpio = (12,13,24)#GPIOS for 'var'. Add other GPIOs that you want

#Number of station names and station links should be the same
stnname=('Radio 1', 'Radio 2', 'Radio 3', 'Radio 5')#Add more stations if you want
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

#Initialize colour list
clrlist=[]
clrlistfullname=[]
clrrgblist=[]
clrhexlist=[]
with open('/home/pi/GassistPi/src/colours.json', 'r') as col:
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
ttsfilename="/tmp/say.mp3"
translator = Translator()
language='en'
## Other language options:
##'af'    : 'Afrikaans'         'sq' : 'Albanian'           'ar' : 'Arabic'      'hy'    : 'Armenian'
##'bn'    : 'Bengali'           'ca' : 'Catalan'            'zh' : 'Chinese'     'zh-cn' : 'Chinese (China)'
##'zh-tw' : 'Chinese (Taiwan)'  'hr' : 'Croatian'           'cs' : 'Czech'       'da'    : 'Danish'
##'nl'    : 'Dutch'             'en' : 'English'            'eo' : 'Esperanto'   'fi'    : 'Finnish'
##'fr'    : 'French'            'de' : 'German'             'el' : 'Greek'       'hi'    : 'Hindi'
##'hu'    : 'Hungarian'         'is' : 'Icelandic'          'id' : 'Indonesian'  'it'    : 'Italian'
##'ja'    : 'Japanese'          'km' : 'Khmer (Cambodian)'  'ko' : 'Korean'      'la'    : 'Latin'
##'lv'    : 'Latvian'           'mk' : 'Macedonian'         'no' : 'Norwegian'   'pl'    : 'Polish'
##'pt'    : 'Portuguese'        'ro' : 'Romanian'           'ru' : 'Russian'     'sr'    : 'Serbian'
##'si'    : 'Sinhala'           'sk' : 'Slovak'             'es' : 'Spanish'     'sw'    : 'Swahili'
##'sv'    : 'Swedish'           'ta' : 'Tamil'              'th' : 'Thai'        'tr'    : 'Turkish'
##'uk'    : 'Ukrainian'         'vi' : 'Vietnamese'         'cy' : 'Welsh'




def check_delete(file):
    if os.path.isfile(file):
        os.system(file)



def end_callback(event):
    if os.path.isfile("/home/pi/.player.json"):
        with open('/home/pi/.player.json','r') as input_file:
              playerinfo= json.load(input_file)
        currenttrackid=playerinfo[0]
        loopstatus=playerinfo[2]
        numtracks=playerinfo[1]
        musictype=playerinfo[3]
        nexttrackid=currenttrackid+1
        playerinfo=[nexttrackid,numtracks,loopstatus,musictype]
        with open('/home/pi/.player.json', 'w') as output_file:
            json.dump(playerinfo, output_file)
        if currenttrackid<numtracks:
            if musictype=='Google Music':
                googlemusic_player(currenttrackid)
            if musictype=='YouTube':
                youtube_player(currenttrackid)

def media_manager(tracks,type):
    check_delete("/home/pi/.player.json")
    check_delete("/home/pi/.trackqueue.json")
    with open('/home/pi/.trackqueue.json', 'w') as output_file:
        json.dump(tracks, output_file)
    nexttrackid=currenttrackid+1
    loopstatus='on'
    musictype=type
    playerinfo=[nexttrackid,numtracks,loopstatus,musictype]
    with open('/home/pi/.player.json', 'w') as output_file:
        json.dump(playerinfo, output_file)


def media_player(track):
    player = vlc.media_player_new()
    media = vlc.media_new(track)
    player.set_media(media)
    player.play()
    event_manager = player.event_manager()
    event_manager.event_attach(EventType.MediaPlayerEndReached, end_callback)


#Function for google KS custom search engine
def kickstrater_search(query):
    service = build("customsearch", "v1",
            developerKey=google_cloud_api_key)
    res = service.cse().list(
        q=query,
        cx = '012926744822728151901:gefufijnci4',
        ).execute()
    return res


#Function to manage mpv start volume
def mpvvolmgr():
    if os.path.isfile("/home/pi/.mediavolume.json"):
        with open('/home/pi/.mediavolume.json', 'r') as vol:
            oldvollevel = json.load(vol)
        print(oldvollevel)
        startvol=oldvollevel
    else:
        startvol=50
    return startvol



#Text to speech converter with translation
def say(words):
    words= translator.translate(words, dest=language)
    words=words.text
    words=words.replace("Text, ",'',1)
    words=words.strip()
    print(words)
    tts = gTTS(text=words, lang=language)
    tts.save(ttsfilename)
    os.system("mpg123 "+ttsfilename)
    os.remove(ttsfilename)


#Function to get HEX and RGB values for requested colour
def getcolours(phrase):
    usrclridx=idx=phrase.find("to")
    usrclr=query=phrase[usrclridx:]
    usrclr=usrclr.replace("to","",1)
    usrclr=usrclr.replace("'}","",1)
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


#Radio Station Streaming
def radio(phrase):
    for num, name in enumerate(stnname):
        if name.lower() in phrase:
            startingvol=mpvvolmgr()
            station=stnlink[num]
            print (station)
            say("Tuning into " + name)
            os.system('mpv --really-quiet --volume='+str(startingvol)+' '+station+' &')

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
            rq = requests.head("https://"+ip + dev + ctrl)


#Stepper Motor control
def SetAngle(angle):
    duty = angle/18 + 2
    GPIO.output(27, True)
    say("Moving motor by " + str(angle) + " degrees")
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    pwm.ChangeDutyCycle(0)
    GPIO.output(27, False)


def stop():
    pkill = subprocess.Popen(["/usr/bin/pkill","mpv"],stdin=subprocess.PIPE)

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

  return YouTubeURL,urlid


#Function to get streaming links for YouTube URLs
def youtube_stream_link(videourl):
    url=videourl
    video = pafy.new(url)
    bestvideo = video.getbest()
    bestaudio = video.getbestaudio()
    audiostreaminglink=bestaudio.url
    videostreaminglink=bestvideo.url
    return audiostreaminglink,videostreaminglink


##-------Start of functions defined for Kodi Actions--------------
#Function to get Kodi Volume and Mute status
def mutevolstatus():
    status= kodi.Application.GetProperties({"properties": ("volume","muted")})
    mutestatus=(status["result"]["muted"])
    volstatus=(status["result"]["volume"])
    return mutestatus, volstatus


def kodi_youtube(query):
    fullurl,urlid=youtube_search(query)

 #If you want to see the URL, uncomment the following line
 #print(YouTubeURL)

 #Instead of sending it to Kodi, if you want to play locally, uncomment the following two lines and comment the next two lines
 #os.system("mpv "+YouTubeURL)
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
    idx=query.find('play')
    track=query[idx:]
    track=track.replace("'}", "",1)
    track = track.replace('play','',1)
    track = track.replace('on kodi','',1)
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
        kodi_youtube(track)
    elif 'what'.lower() in str(phrase).lower() and 'playing'.lower() in str(phrase).lower():
        whatisplaying()
    elif 'play'.lower() in str(phrase).lower() and 'album'.lower() in str(phrase).lower():
        albumretrieve(phrase)
    elif 'play'.lower() in str(phrase).lower() and 'artist'.lower() in str(phrase).lower():
        query=str(phrase).lower()
        idx = query.find('artist')
        artist = query[idx:]
        artist = artist.replace("'}", "",1)
        artist = artist.replace('artist','',1)
        artist = artist.replace('on kodi','',1)
        artist = artist.strip()
        say("Searching for renditions")
        kodiartist(artist)
    elif 'play'.lower() in str(phrase).lower() and ('audio'.lower() in str(phrase).lower() or 'movie'.lower() in str(phrase).lower() or 'song'.lower() in str(phrase).lower() or 'video'.lower() in str(phrase).lower() or 'track'.lower() in str(phrase).lower()):
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
        elif 'off'.lower() in str(phrase).lower() or 'disable'.lower() in str(phrase).lower() or 'none'.lower() in str(phrase).lower():
            kodi.Player.SetRepeat({"playerid": playid,"repeat": "off"})
    elif 'turn'.lower() in str(phrase).lower() and 'shuffle'.lower() in str(phrase).lower():
        players=kodi.Player.GetActivePlayers()
        playid=players["result"][0]["playerid"]
        cmd=str(phrase).lower()
        cmd=cmd.replace('on kodi','',1)
        cmd=cmd.strip()
        if 'on'.lower() in str(cmd).lower():
            kodi.Player.SetShuffle({"playerid": playid,"shuffle":True})
            print('Turning on shuffle')
        elif 'off'.lower() in str(cmd).lower():
            kodi.Player.SetShuffle({"playerid": playid,"shuffle":False})
            print('Turning off shuffle')
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
            with open('/home/pi/.volume.json', 'w') as f:
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
    if os.path.isfile("/home/pi/songs.json"):
        with open('/home/pi/songs.json','r') as input_file:
            songs_list= json.load(input_file)
##            print(songs_list)
    else:
        songs_list= api.get_all_songs()
        with open('/home/pi/songs.json', 'w') as output_file:
            json.dump(songs_list, output_file)
    for i in range(0,len(songs_list)):
        song_ids.append(songs_list[i]['id'])
    songsnum=len(songs_list)
    return song_ids, songsnum

def loadartist(artistname):
    song_ids=[]
    artist=str(artistname)
    if os.path.isfile("/home/pi/songs.json"):
        with open('/home/pi/songs.json','r') as input_file:
            songs_list= json.load(input_file)
##            print(songs_list)
    else:
        songs_list= api.get_all_songs()
        with open('/home/pi/songs.json', 'w') as output_file:
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
    if os.path.isfile("/home/pi/songs.json"):
        with open('/home/pi/songs.json','r') as input_file:
            songs_list= json.load(input_file)
##            print(songs_list)
    else:
        songs_list= api.get_all_songs()
        with open('/home/pi/songs.json', 'w') as output_file:
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
    if os.path.isfile("/home/pi/playlist.json"):
        with open('/home/pi/playlist.json','r') as input_file:
            playlistcontents= json.load(input_file)
    else:
        playlistcontents=api.get_all_user_playlist_contents()
        with open('/home/pi/playlist.json', 'w') as output_file:
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
    with open('/home/pi/songs.json', 'w') as output_file:
        json.dump(songs_list, output_file)
    with open('/home/pi/playlist.json', 'w') as output_file:
        json.dump(playlist_list, output_file)
    say("Music list synchronised")

def googlemusic_player(trackid):
    with open('/home/pi/.trackqueue.json','r') as input_file:
            tracks= json.load(input_file)
    streamurl=api.get_stream_url(tracks[trackid])
    media_player(streamurl)

def gmusicselect(phrase):
    currenttrackid=0
    if 'all the songs'.lower() in phrase:
        say("Looking for your songs")
        tracks,numtracks=loadsonglist()
        if not tracks==[]:
            media_manager(tracks,'Google Music')
            googlemusic_player(currenttrackid)
        else:
            say("Unable to find songs matching your request")
    else:
        say("Sorry I am unable to help")

    if 'playlist'.lower() in phrase:
        if 'first'.lower() in phrase or 'one'.lower() in phrase  or '1'.lower() in phrase:
            say("Playing songs from your playlist")
            tracks,numtracks=loadplaylist(playlistnum)
            if not tracks==[]:
                media_manager(tracks,'Google Music')
                googlemusic_player(currenttrackid)
            else:
                say("Unable to find songs matching your request")
        else:
            say("Sorry I am unable to help")

    if 'album'.lower() in phrase:
        req=phrase
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
        say("Looking for songs from the album")
        tracks,numtracks=loadalbum(albumname)
        if not tracks==[]:
            media_manager(tracks,'Google Music')
            googlemusic_player(currenttrackid)
        else:
            say("Unable to find songs matching your request")

    if 'artist'.lower() in phrase:
        req=phrase
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
        say("Looking for songs rendered by the artist")
        tracks,numtracks=loadartist(artistname)
        if not tracks==[]:
            media_manager(tracks,'Google Music')
            googlemusic_player(currenttrackid)
        else:
            say("Unable to find songs matching your request")


#----------End of functions defined for Google Music---------------------------


#-----------------Start of Functions for YouTube Streaming---------------------
def youtube_player(trackid):
    with open('/home/pi/.trackqueue.json','r') as input_file:
            tracks= json.load(input_file)
    audiostream,videostream=youtube_stream_link(tracks[trackid])
    streamurl=audiostream
    media_player(streamurl)

def YouTube_Autoplay(phrase):
    urllist=[]
    currenttrackid=0
    idx=phrase.find('stream')
    track=phrase[idx:]
    track=track.replace("'}", "",1)
    track = track.replace('stream','',1)
    track=track.strip()
    say("Getting autoplay links")
    fullurl,urlid=youtube_search(track)
    autourls=fetchautoplaylist(fullurl,10)#Maximum of 10 URLS
    print(autourls)
    for i in range(0,len(autourls)):
        urllist.append(autourls[i])
    say("Adding autoplay links to the playlist")
    if not autourls==[]:
        media_manager(autourls,'YouTube')
        youtube_player(currenttrackid)
    else:
        say("Unable to find songs matching your request")

def YouTube_No_Autoplay(phrase):
    urllist=[]
    currenttrackid=0
    idx=phrase.find('stream')
    track=phrase[idx:]
    track=track.replace("'}", "",1)
    track = track.replace('stream','',1)
    track=track.strip()
    say("Getting youtube link")
    fullurl,urlid=youtube_search(track)
    urllist.append(fullurl)
    print(urllist)
    if not urllist==[]:
        media_manager(urllist,'YouTube')
        youtube_player(currenttrackid)
    else:
        say("Unable to find songs matching your request")


#-----------------End of Functions for YouTube Streaming---------------------



#--------------Start of Chromecast functions-----------------------------------

def chromecast_play_video(phrase):
    # Chromecast declarations
    # Do not rename/change "TV" its a variable
    TV = pychromecast.Chromecast("192.168.1.13") #Change ip to match the ip-address of your Chromecast
    mc = TV.media_controller
    idx=phrase.find('play')
    query=phrase[idx:]
    query=query.replace("'}", "",1)
    query=query.replace('play','',1)
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
    pb = Pushbullet('ENTER-YOUR-PUSHBULLET-KEY-HERE')
    push = pb.push_note(title,body)
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
    with open('/home/pi/GassistPi/src/diyHue/config.json', 'r') as config:
         hueconfig = json.load(config)
    currentxval=hueconfig['lights'][lightindex]['state']['xy'][0]
    currentyval=hueconfig['lights'][lightindex]['state']['xy'][1]
    currentbri=hueconfig['lights'][lightindex]['state']['bri']
    currentct=hueconfig['lights'][lightindex]['state']['ct']
    huelightname=str(hueconfig['lights'][lightindex]['name'])
    try:
        if 'on' in phrase:
            huereq=requests.head("http://"+lightaddress+"/set?light="+lightindex+"&on=true")
            say("Turning on "+huelightname)
        if 'off' in phrase:
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
        if 'brightness'.lower() in phrase:
            if 'hundred'.lower() in str(usrcmd).lower() or 'maximum' in str(usrcmd).lower():
                bright=100
            elif 'zero'.lower() in str(usrcmd).lower() or 'minimum' in str(usrcmd).lower():
                bright=100
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



#GPIO Device Control
def Action(phrase):
    if 'shut down' in phrase:
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
        for num, name in enumerate(var):
            if name.lower() in phrase:
                pinout=gpio[num]
                if 'on' in phrase:
                    GPIO.output(pinout, 1)
                    say("Turning On " + name)
                elif 'off' in phrase:
                    GPIO.output(pinout, 0)
                    say("Turning Off " + name)
