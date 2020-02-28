#!/usr/bin/env python

#This is different from AIY Kit's actions
#Copying and Pasting AIY Kit's actions commands will not work

from kodijson import Kodi, PLAYER_VIDEO
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.tools import argparser
from youtube_search_engine import google_cloud_api_key
from youtube_search_engine import youtube_search
from gtts import gTTS
import requests
import os
import os.path
import time
import re
import subprocess
import json
import urllib.request
import yaml

ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))


with open('{}/src/config.yaml'.format(ROOT_PATH),'r', encoding='utf8') as conf:
    configuration = yaml.load(conf)

TTSChoice='GTTS'

keywordfile= '{}/src/keywords_en.yaml'.format(ROOT_PATH)
with open(keywordfile,'r' , encoding='utf8') as conf:
    custom_action_keyword = yaml.load(conf)

Youtube_credentials=False
if configuration['Google_cloud_api_key']!='ENTER-YOUR-GOOGLE-CLOUD-API-KEY-HERE':
    Youtube_credentials=True


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


##Speech declarations
femalettsfilename="/tmp/female-say.mp3"
malettsfilename="/tmp/male-say.wav"

#gTTS
def gttssay(phrase):
    tts = gTTS(text=phrase, 'en-US')
    tts.save(femalettsfilename)
    if specgender=='Male':
        os.system('sox ' + femalettsfilename + ' ' + malettsfilename + ' pitch -450')
        os.remove(femalettsfilename)
        os.system('aplay ' + malettsfilename)
        os.remove(malettsfilename)
    elif specgender=='Female':
        os.system("mpg123 "+femalettsfilename)
        os.remove(femalettsfilename)


#Text to speech converter with translation
def say(words):
    gttssay(words)


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
