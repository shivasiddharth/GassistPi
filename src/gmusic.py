from gmusicapi import Mobileclient
import os
import os.path
import json
import subprocess


song_ids=[]
track_ids=[]
api = Mobileclient()
logged_in = api.login('ushivasiddharth@gmail.com', 'uxgmuojgbgmyolze', Mobileclient.FROM_MAC_ADDRESS)



##-------Start of functions defined for Google Music-------------------

def loadsonglist():
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
    playlistcontents=api.get_all_user_playlist_contents()
    songs_list= api.get_all_songs()
    with open('/home/pi/songs.json', 'w') as output_file:
        json.dump(songs_list, output_file)
    with open('/home/pi/playlist.json', 'w') as output_file:
        json.dump(playlist_list, output_file)

def play_playlist(playlistnum):

    if os.path.isfile("/home/pi/.gmusicplaylistplayer.json"):
        with open('/home/pi/.gmusicplaylistplayer.json','r') as input_file:
            playerinfo= json.load(input_file)
        currenttrackid=playerinfo[0]
        loopstatus=playerinfo[1]
        nexttrackid=currenttrackid+1
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicplaylistplayer.json', 'w') as output_file:
            json.dump(playerinfo, output_file)
    else:
        currenttrackid=0
        nexttrackid=1
        loopstatus='on'
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicplaylistplayer.json', 'w') as output_file:
            json.dump(playerinfo, output_file)

    tracks,numtracks=loadplaylist(playlistnum)

    if currenttrackid<numtracks:
        streamurl=api.get_stream_url(tracks[currenttrackid])
        streamurl=("'"+streamurl+"'")
        print(streamurl)
        os.system('mpv --really-quiet '+streamurl+' &')
    elif currenttrackid>numtracks and loopstatus=='on':
        currenttrackid=0
        nexttrackid=1
        loopstatus='on'
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicplaylistplayer.json', 'w') as output_file:
            json.dump(playerinfo,output_file)
        streamurl=api.get_stream_url(tracks[currenttrackid])
        streamurl=("'"+streamurl+"'")
        print(streamurl)
        os.system('"mpv --really-quiet "+streamurl+" &"')
    elif currenttrackid>numtracks and loopstatus=='off':
        print("Error")

def play_songs():

    if os.path.isfile("/home/pi/.gmusicsongsplayer.json"):
        with open('/home/pi/.gmusicsongsplayer.json','r') as input_file:
            playerinfo= json.load(input_file)
        currenttrackid=playerinfo[0]
        loopstatus=playerinfo[1]
        nexttrackid=currenttrackid+1
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicsongsplayer.json', 'w') as output_file:
            json.dump(playerinfo, output_file)
    else:
        currenttrackid=0
        nexttrackid=1
        loopstatus='on'
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicsongsplayer.json', 'w') as output_file:
            json.dump(playerinfo, output_file)

    tracks,numtracks=loadsonglist()

    if currenttrackid<numtracks:
        streamurl=api.get_stream_url(tracks[currenttrackid])
        streamurl=("'"+streamurl+"'")
        print(streamurl)
        os.system('mpv --really-quiet '+streamurl+' &')
    elif currenttrackid>numtracks and loopstatus=='on':
        currenttrackid=0
        nexttrackid=1
        loopstatus='on'
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicsongsplayer.json', 'w') as output_file:
            json.dump(playerinfo,output_file)
        streamurl=api.get_stream_url(tracks[currenttrackid])
        streamurl=("'"+streamurl+"'")
        print(streamurl)
        os.system('mpv --really-quiet '+streamurl+' &')
    elif currenttrackid>numtracks and loopstatus=='off':
        print("Error")

def play_album(albumname):
    if os.path.isfile("/home/pi/.gmusicalbumplayer.json"):
        with open('/home/pi/.gmusicalbumplayer.json','r') as input_file:
            playerinfo= json.load(input_file)
        currenttrackid=playerinfo[0]
        loopstatus=playerinfo[1]
        nexttrackid=currenttrackid+1
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicalbumplayer.json', 'w') as output_file:
            json.dump(playerinfo, output_file)
    else:
        currenttrackid=0
        nexttrackid=1
        loopstatus='on'
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicalbumplayer.json', 'w') as output_file:
            json.dump(playerinfo, output_file)

    tracks,numtracks=loadalbum(albumname)

    if currenttrackid<numtracks:
        streamurl=api.get_stream_url(tracks[currenttrackid])
        streamurl=("'"+streamurl+"'")
        print(streamurl)
        os.system('mpv --really-quiet '+streamurl+' &')
    elif currenttrackid>numtracks and loopstatus=='on':
        currenttrackid=0
        nexttrackid=1
        loopstatus='on'
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicalbumplayer.json', 'w') as output_file:
            json.dump(playerinfo,output_file)
        streamurl=api.get_stream_url(tracks[currenttrackid])
        streamurl=("'"+streamurl+"'")
        print(streamurl)
        os.system('mpv --really-quiet '+streamurl+' &')
    elif currenttrackid>numtracks and loopstatus=='off':
        print("Error")


def play_artist(artistname):
    if os.path.isfile("/home/pi/.gmusicartistplayer.json"):
        with open('/home/pi/.gmusicartistplayer.json','r') as input_file:
            playerinfo= json.load(input_file)
        currenttrackid=playerinfo[0]
        loopstatus=playerinfo[1]
        nexttrackid=currenttrackid+1
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicartistplayer.json', 'w') as output_file:
            json.dump(playerinfo, output_file)
    else:
        currenttrackid=0
        nexttrackid=1
        loopstatus='on'
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicartistplayer.json', 'w') as output_file:
            json.dump(playerinfo, output_file)

    tracks,numtracks=loadartist(artistname)

    if currenttrackid<numtracks:
        streamurl=api.get_stream_url(tracks[currenttrackid])
        streamurl=("'"+streamurl+"'")
        print(streamurl)
        os.system('mpv --really-quiet '+streamurl+' &')
    elif currenttrackid>numtracks and loopstatus=='on':
        currenttrackid=0
        nexttrackid=1
        loopstatus='on'
        playerinfo=[nexttrackid,loopstatus]
        with open('/home/pi/.gmusicartistplayer.json', 'w') as output_file:
            json.dump(playerinfo,output_file)
        streamurl=api.get_stream_url(tracks[currenttrackid])
        streamurl=("'"+streamurl+"'")
        print(streamurl)
        os.system('mpv --really-quiet '+streamurl+' &')
    elif currenttrackid>numtracks and loopstatus=='off':
        print("Error")
#----------End of functions defined for Google Music---------------------------