import sys
import spotipy
import spotipy.util as sputil
from defs import SpotipyClient
import dbutils
import pandas as pd
import time
import utils


def add_mood_tracks_to_mood_playlists(sp, con):
    mooddict = {
            "Peaceful": "0AqPGT2UOtlnTfr0dPtwwD", "Romantic": "76oMVdvVaEQJMx6PpmpLAF",
            "Sentimental":"7HPD7jNAjvzgE0qB7UvCZX", "Tender": "1qMVuZvXTjCifhUsRrO6SZ",
            "Easygoing": "3fetVyO0ez8UNRRPXyWFfV", "Yearning": "37NGlcT5IFKBEohRV7JKbo",
            "Sophisticated": "0fzoJwJ3aRUF6gEAJPzPYU", "Sensual": "1nVMTMWQkngR6X9IlBLeCB", "Cool": "15llrn1mLCeV0NO3qh4Btg",
            "Gritty": "3GsKdN5Mmj43pixuoNMXfE", "Somber":"3JzqINleWYbQZVZ9H4w7t2",
            "Melancholy":"7BuPDRmPYF9Z7Q25DonbMn", "Serious":"39YsYl7NLkprJ8NPbKkZmS",
            "Brooding":"0fo7iTdERRmvJRLEMW737h", "Fiery":"7dHlxRExo3dNtkwu2UMEPZ",
            "Urgent":"1zgL8fh9YipChpUKhMndwm", "Defiant":"5Fi5DesfV5j0rtvL5TpHNu",
            "Aggressive":"3rCFT0DPdApQgo93sVKndj", "Rowdy":"3iTmAvGPfuLWiHxQDHpTLY",
            "Excited":"5q3S544x7amHfTWF1ZvDpd", "Energizing":"3I66czUY5Fa80V4PubxFd3",
            "Empowering":"6uhdhSIEhHCkAS3Y1P3o6n", "Stirring":"3g5O2RpkTUl9Zf6ai4aOnW",
            "Lively":"0HWMXqh4VuHnb9nFS8El5j", "Upbeat":"4NYh5KcBrbw8LSJDVGduc1", "Other":"6xAXePNCYBID238rNPKxrp"}

    mooddict = {"Aggressive":"3rCFT0DPdApQgo93sVKndj"}

    for mood in mooddict.keys():
        playlist_id = mooddict[mood]
        querystring = "select id from ragafeaturedb WHERE gn_mood_1 like \'" + mood + "\'"
        df = dbutils.query_db_translate_to_pandas(con, querystring)
        print("Number of tracks to be added to " + mood + " = ", df.shape)
        tracklist = df['id'].tolist()
        utils.add_tracks_to_playlist_id(sp, playlist_id, tracklist)


if __name__ == "__main__":

    con = dbutils.get_db_handle()
    sp = SpotipyClient()
    print(sp.auth)

    add_mood_tracks_to_mood_playlists(sp, con)

    dbutils.close_db(con)
