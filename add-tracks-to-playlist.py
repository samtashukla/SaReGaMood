import sys
import spotipy
import spotipy.util as sputil
#from spotipy.oauth2 import SpotifyClientCredentials

client_id="eaf61ee280c745fa919ec70c278c56bd"
client_secret="b3a7c3030e534a6399da0b2f6461d3a0"
#client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
#sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

username = 'onkarbhardwaj'

scope = 'playlist-modify-private'
#token = sputil.prompt_for_user_token(username, scope)

#token = sputil.prompt_for_user_token(username = username, 
#                                   scope = scope, 
#                                   client_id = client_id, 
#                                   client_secret = client_secret)

#if token:
token="BQD8ATZE49WlXQp43Socz_NYTD8tbzbMB1QFEVhdjjm0GfxFPExzglfKt9YO8-5Py6wFmpauGNaMMm6bOCsHX8LK7pVuCM8o7oq49_uhomz-57ULjhYdjUqnRQ4vn9bTcZonjl_lcbLlCHz6tbRjf8E1pstex3qDK0r_pIZrZWe7IMpz0fu0EjPs5DfJ6Xgex8UTa7b7XBFTiwRt"
sp = spotipy.Spotify(auth=token)
sp.trace = False
playlist_id = "1m3x5wUepl5nj3Oxzc0rvT"
with open("track-ids.txt", "r") as fh:
    track_ids=[]
    for line in fh:
        tid=line.rstrip()
        track_ids.append(tid)
    numtracks = len(track_ids)
    chunksize = 50
    for offset in [i for i in range(0, numtracks, chunksize)]:
        listslice = track_ids[offset:offset+chunksize]
        results = sp.user_playlist_add_tracks(username, playlist_id, listslice)
        #results = sp.user_playlist_add_tracks(username, playlist_id, track_ids)
        print(results)
