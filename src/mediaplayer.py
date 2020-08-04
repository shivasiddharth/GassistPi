#!/usr/bin/env python


import vlc
import os
import json
from gmusicapi import Mobileclient
import os.path
from youtube_search_engine import youtube_search
from youtube_search_engine import youtube_stream_link
import yaml

ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))

with open('{}/src/config.yaml'.format(ROOT_PATH),'r') as conf:
    configuration = yaml.load(conf)

api = Mobileclient()
deviceid=[]
logged_in=api.oauth_login(Mobileclient.FROM_MAC_ADDRESS)
if logged_in:
    for device in api.get_registered_devices():
        if device['type']=='ANDROID':
            deviceid=device['id'][2:]
            print(deviceid)
            break
    if deviceid!=[]:
        api.logout()
        logged_in=api.oauth_login(deviceid)



class vlcplayer():

    def __init__(self):
        self.libvlc_Instance=vlc.Instance('--verbose 0')
        self.libvlc_player = self.libvlc_Instance.media_player_new()
        # self.libvlc_list_player = self.libvlc_Instance.media_list_player_new()
        # self.libvlc_Media_list = self.libvlc_Instance.media_list_new()
        # self.libvlc_list_player.set_media_player(self.libvlc_player)
        # self.libvlc_list_player.set_media_list(self.libvlc_Media_list)
        # self.libvlc_player_event_manager= self.libvlc_player.event_manager()

    def play_audio_file(self,fname):
        Instance=vlc.Instance()
        player=Instance.media_player_new()
        player.set_mrl(fname)
        player.play()

    def end_callback(self,event):
        if os.path.isfile("{}/.player.json".format(USER_PATH)):
            with open('{}/.player.json'.format(USER_PATH),'r') as input_file:
                  playerinfo= json.load(input_file)
            currenttrackid=playerinfo[0]
            loopstatus=playerinfo[2]
            numtracks=playerinfo[1]
            musictype=playerinfo[3]
            nexttrackid=currenttrackid+1
            playerinfo=[nexttrackid,numtracks,loopstatus,musictype]
            with open('{}/.player.json'.format(USER_PATH), 'w') as output_file:
                json.dump(playerinfo, output_file)
            if currenttrackid<numtracks:
                if musictype=='Google Music':
                    self.googlemusic_player(currenttrackid)
                if musictype=='YouTube':
                    self.youtube_player(currenttrackid)
                if musictype=='Spotify':
                    self.spotify_player(currenttrackid)
                if musictype=='Gaana':
                    self.gaana_player(currenttrackid)
                if musictype=='Deezer':
                    self.deezer_player(currenttrackid)

    def change_media_next(self):
        if os.path.isfile("{}/.player.json".format(USER_PATH)):
            with open('{}/.player.json'.format(USER_PATH),'r') as input_file:
                  playerinfo= json.load(input_file)
            currenttrackid=playerinfo[0]
            loopstatus=playerinfo[2]
            numtracks=playerinfo[1]
            musictype=playerinfo[3]
            nexttrackid=currenttrackid+1
            playerinfo=[nexttrackid,numtracks,loopstatus,musictype]
            with open('{}/.player.json'.format(USER_PATH), 'w') as output_file:
                json.dump(playerinfo, output_file)
            if currenttrackid<numtracks:
                if musictype=='Google Music':
                    self.googlemusic_player(currenttrackid)
                if musictype=='YouTube':
                    self.youtube_player(currenttrackid)
                if musictype=='Spotify':
                    self.spotify_player(currenttrackid)
                if musictype=='Gaana':
                    self.gaana_player(currenttrackid)
                if musictype=='Deezer':
                    self.deezer_player(currenttrackid)

    def change_media_previous(self):
        if os.path.isfile("{}/.player.json".format(USER_PATH)):
            with open('{}/.player.json'.format(USER_PATH),'r') as input_file:
                  playerinfo= json.load(input_file)
            currenttrackid=playerinfo[0]
            loopstatus=playerinfo[2]
            numtracks=playerinfo[1]
            musictype=playerinfo[3]
            nexttrackid=currenttrackid-1
            prevtrackid=currenttrackid-2
            if prevtrackid<0:
                currenttrackid=0
            else:
                currenttrackid=prevtrackid
            playerinfo=[nexttrackid,numtracks,loopstatus,musictype]
            with open('{}/.player.json'.format(USER_PATH), 'w') as output_file:
                json.dump(playerinfo, output_file)
            if currenttrackid<numtracks:
                if musictype=='Google Music':
                    self.googlemusic_player(currenttrackid)
                if musictype=='YouTube':
                    self.youtube_player(currenttrackid)
                if musictype=='Spotify':
                    self.spotify_player(currenttrackid)
                if musictype=='Gaana':
                    self.gaana_player(currenttrackid)
                if musictype=='Deezer':
                    self.deezer_player(currenttrackid)

    def media_player(self,mrl):
        self.libvlc_player = self.libvlc_Instance.media_player_new()
        media=self.libvlc_Instance.media_new(mrl)
        self.libvlc_player.set_media(media)
        self.libvlc_player.play()
        if os.path.isfile("{}/.mediavolume.json".format(USER_PATH)):
            with open('{}/.mediavolume.json'.format(USER_PATH), 'r') as vol:
                setvollevel = json.load(vol)
            self.set_vlc_volume(int(setvollevel))
        else:
            self.set_vlc_volume(90)
        event_manager = self.libvlc_player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached,self.end_callback)
        #self.libvlc_Media_list.add_media(media)
        #self.libvlc_list_player.play_item(media)

    def set_vlc_volume(self,level):
        self.libvlc_player.audio_set_volume(level)

    def get_vlc_volume(self):
        return self.libvlc_player.audio_get_volume()

    def mute_vlc(self,status=True):
        return self.libvlc_player.audio_set_mute(status)

    def stop_vlc(self):
        print('stopping vlc')
        self.libvlc_player.stop()

    def pause_vlc(self):
        print('pausing vlc')
        self.libvlc_player.pause()

    def play_vlc(self):
        if self.libvlc_player.get_state()==vlc.State.Paused:
            print('playing/resuming vlc')
            self.libvlc_player.play()

    def is_vlc_playing(self):
        return self.libvlc_player.is_playing()

    def state(self):
        return self.libvlc_player.get_state()

    def media_manager(self,tracks,type):
        self.check_delete("{}/.player.json".format(USER_PATH))
        self.check_delete("{}/.trackqueue.json".format(USER_PATH))
        with open('{}/.trackqueue.json'.format(USER_PATH), 'w') as output_file:
            json.dump(tracks, output_file)
        currenttrackid=0
        nexttrackid=currenttrackid+1
        loopstatus='on'
        musictype=type
        numtracks=len(tracks)
        playerinfo=[nexttrackid,numtracks,loopstatus,musictype]
        with open('{}/.player.json'.format(USER_PATH), 'w') as output_file:
            json.dump(playerinfo, output_file)

    def googlemusic_player(self,trackid):
        with open('{}/.trackqueue.json'.format(USER_PATH),'r') as input_file:
            tracks= json.load(input_file)
        streamurl=api.get_stream_url(tracks[trackid])
        self.media_player(streamurl)

    def youtube_player(self,trackid):
        with open('{}/.trackqueue.json'.format(USER_PATH),'r') as input_file:
            tracks= json.load(input_file)
        print(tracks[trackid])
        self.media_player(tracks[trackid])

    def spotify_player(self,trackid):
        with open('{}/.trackqueue.json'.format(USER_PATH),'r') as input_file:
            tracks= json.load(input_file)
        print(tracks[trackid])
        urlid = youtube_search(tracks[trackid])
        if urlid is not None:
            fullurl = "https://www.youtube.com/watch?v=" + urlid
            audiostream, videostream = youtube_stream_link(fullurl)
            streamurl = audiostream
            self.media_player(streamurl)

    def gaana_player(self,trackid):
        with open('{}/.trackqueue.json'.format(USER_PATH),'r') as input_file:
            tracks= json.load(input_file)
        print(tracks[trackid])
        urlid = youtube_search(tracks[trackid])
        if urlid is not None:
            fullurl = "https://www.youtube.com/watch?v=" + urlid
            audiostream, videostream = youtube_stream_link(fullurl)
            streamurl = audiostream
            self.media_player(streamurl)

    def deezer_player(self,trackid):
        with open('{}/.trackqueue.json'.format(USER_PATH),'r') as input_file:
            tracks= json.load(input_file)
        print(tracks[trackid])
        urlid = youtube_search(tracks[trackid])
        if urlid is not None:
            fullurl = "https://www.youtube.com/watch?v=" + urlid
            audiostream, videostream = youtube_stream_link(fullurl)
            streamurl = audiostream
            self.media_player(streamurl)

    def check_delete(self,file):
        if os.path.isfile(file):
            os.system("sudo rm "+file)
