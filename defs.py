import spotipy
import pygn
import time
from spotipy.oauth2 import SpotifyClientCredentials
import collections
from collections import namedtuple as nt
import sys

sp_feature_list = ['danceability', 'energy', 'key', 'loudness',
        'mode', 'speechiness', 'acousticness', 'instrumentalness',
        'liveness', 'valence', 'tempo']

gn_feature_list = ['gnid', 'genre_1', 'genre_2', 'genre_3',
        'mood_1', 'mood_2', 'tempo_1', 'tempo_2', 'tempo_3']

class SpotipyClient():
    def __init__(self):
        self.id = "e643f7df10314258ad94a7f1778995f0"
        self.secret = "b72131ac34604679880abe5d9801e677"
        self.user = "shukls"
        self.cred_manager = SpotifyClientCredentials(client_id=self.id, client_secret=self.secret)
        self.client = spotipy.Spotify(client_credentials_manager = self.cred_manager)
        # token for feature extraction
        # if token expired, get it from here: https://developer.spotify.com/web-api/console/get-audio-features-several-tracks/#complete
        self.spotify = spotipy.Spotify(auth='BQBZ3JKBmqBu-Bkav6fMt6d3i2P-4ULzUubFJD9Hvy5XjPQ1M3-gDnvXy-no0RAC1lYU_L27GJtcv8P3kZFz_iE07ujQlOCeCgl_EQVRibfinvspojqN9qL2io3ZKs8sjA7Ke5g7GwEySKKoXY__8mxv1wnzlbQ')
        return

class GracenoteClient():
    def __init__(self):
        self.clientid = '18404282-D215A8393036073C7D4008B567ADB278'
        #self.userid = pygn.register(self.clientid)
        #self.userid = '40350305677161399-FBEEF011A5EE5144578CE45E3A2EC94D'
        self.userid = '50483412008758138-7A27D3EEAD745D53BE95957201EF3C4C'
        return

    def renew(self):
        print("Renewing gracenote authorization")
        self.userid = pygn.register(self.clientid)
        time.sleep(5)


pldesc = nt("pldesc", "id name uri url")
trdesc = nt("trdesc", "id name uri url duration_ms href artist_id artist_name artist_url album_id album_name album_url")
#trdesc = nt("trdesc", "album artists available_markets disc_number duration_ms explicit external_ids external_urls href id name popularity preview_url track_number type uri")

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
