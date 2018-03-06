import spotipy
import pygn
import time
from spotipy.oauth2 import SpotifyClientCredentials
import collections
from collections import namedtuple as nt
import sys

# Global list of spotify feature names
# Ultimately, we will use only some of these features.
sp_feature_list = ['danceability', 'energy', 'key', 'loudness',
        'mode', 'speechiness', 'acousticness', 'instrumentalness',
        'liveness', 'valence', 'tempo']

# Global list of gracenote feature names.
# Ultimately, we will use only some of these features.
gn_feature_list = ['gnid', 'genre_1', 'genre_2', 'genre_3',
        'mood_1', 'mood_2', 'tempo_1', 'tempo_2', 'tempo_3']

class SpotipyClient():
    def __init__(self):
        self.id = None # replace None by your spotify id
        self.secret = None # replace None by your spotify secret
        self.user = None # replace None by your user id
        # token for feature extraction
        # if token expired, get it from here:
        # https://developer.spotify.com/web-api/console/get-audio-features-several-tracks/#complete
        self.auth = None # replace None by spotify authorization
        self.cred_manager = SpotifyClientCredentials(client_id=self.id, client_secret=self.secret)
        self.client = spotipy.Spotify(client_credentials_manager = self.cred_manager)
        self.spotify = spotipy.Spotify(auth=self.auth)
        return

class GracenoteClient():
    def __init__(self):
        self.clientid = None # replace None by your client id
        self.userid = pygn.register(self.clientid)
        return

    def renew(self):
        # Gracenote userid (or authorization) expires but it let us renew with a function call
        # unlike spotify where we have to get get ut from a web-api after selecting categories
        self.userid = pygn.register(self.clientid)
        time.sleep(5)


# Named tuple denoting playlist descriptor (note that nt stands for NamedTuple)
# id, name, uri and url are the feature columns of a playlist that
# we will store (and discard the rest of the columns)
pldesc = nt("pldesc", "id name uri url")
# Named tuple denoting track descriptor.
# Named tuple denoting playlist descriptor (note that nt stands for NamedTuple)
# id, name, uri and url are the feature columns of a track
# that we will store (and discard the rest of the columns)
trdesc = nt("trdesc", "id name uri url duration_ms href artist_id artist_name artist_url album_id album_name album_url")

# The following function takes a spotify track (which is a json-like tree) and constructs
# a named tuple for track descriptor (or trdesc). This makesit easier to access the track features
# instead of hunting a feature down a json tree every time.
def make_trdesc(track):
    try:
        duration_ms = track["duration_ms"]
        url = track["external_urls"]["spotify"]
        href = track["href"]
        tid = track["id"]
        name = track["name"]
        uri = track["uri"]
        artist_id = track["artists"][0]["id"]
        artist_name = track["artists"][0]["name"]
        artist_url = track["artists"][0]["external_urls"]["spotify"]
        album_id = track["album"]["id"]
        album_name = track["album"]["name"]
        album_url = track["album"]["external_urls"]["spotify"]
        td = trdesc(id=tid, name=name, uri=uri, url=url, artist_name=artist_name,
            artist_id=artist_id, artist_url=artist_url, duration_ms=duration_ms, href=href,
            album_id=album_id, album_name=album_name, album_url=album_url)
    except Exception as e:
        print("Error making track descriptor: Not a public track? Reurning None");
        print(str(e))
        td = None
    return td
