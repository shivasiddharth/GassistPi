import urllib.request
import pafy
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.tools import argparser
import yaml
import random
import os

ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))

with open('{}/src/config.yaml'.format(ROOT_PATH), 'r') as conf:
    configuration = yaml.load(conf)

# API Key for YouTube and KS Search Engine
google_cloud_api_key = configuration['Google_cloud_api_key']

# YouTube API Constants
DEVELOPER_KEY = google_cloud_api_key
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


# Function to search YouTube and get videoid
def youtube_search(query, maximum=1):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    req = query
    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(
        q=query,
        part='id,snippet'
    ).execute()
    # print(search_response)

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

    # Results of YouTube search. If you wish to see the results, uncomment them
    # print ('Videos\n', '\n'.join(videos), '\n')
    # print ('Channels:\n', '\n'.join(channels), '\n')
    # print ('Playlists:\n', '\n'.join(playlists), '\n')

    # Checks if your query is for a channel, playlist or a video and changes the URL accordingly
    if 'channel' in str(req).lower() and len(channels) != 0:
        urlid = channelids[0]
        channel_response = youtube.channels().list(
            id=urlid,
            part='contentDetails'
        ).execute()
        # print(channel_response)
        urlid = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        list_response = youtube.playlistItems().list(
            playlistId=urlid,
            part='contentDetails'
        ).execute()
        if maximum == 1:
            list_result = random.choice(list_response.get('items', []))
            return list_result['contentDetails']['videoId']
        else:
            ids = []
            for list_result in list_response.get('items', []):
                ids.append(list_result['contentDetails']['videoId'])
                if len(ids) >= maximum:
                    return ids
            return ids
    elif 'playlist' in str(req).lower() and len(playlists) != 0:
        urlid = playlistids[0]
        list_response = youtube.playlistItems().list(
            playlistId=urlid,
            part='contentDetails'
        ).execute()
        if maximum == 1:
            list_result = random.choice(list_response.get('items', []))
            return list_result['contentDetails']['videoId']
        else:
            ids = []
            for list_result in list_response.get('items', []):
                ids.append(list_result['contentDetails']['videoId'])
                if len(ids) >= maximum:
                    return ids
            return ids
    elif len(videoids) != 0:
        if maximum == 1:
            return videoids[0]
        else:
            ids = []
            for id in videoids:
                ids.append(id)
                if len(ids) >= maximum:
                    return ids
            return ids
    elif maximum == 1:
        return []


# Function to get streaming links for YouTube URLs
def youtube_stream_link(video_url):
    video = pafy.new(video_url)
    best_video = video.getbest()
    best_audio = video.getbestaudio()
    audio_streaming_link = best_audio.url
    video_streaming_link = best_video.url
    return audio_streaming_link, video_streaming_link
