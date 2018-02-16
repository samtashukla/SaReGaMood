import sys
import spotipy
import spotipy.util as sputil
from defs import SpotipyClient
import dbutils
import pandas as pd
import time
import utils

def download_survey_playlist(sp, plid):
    tlist = utils.get_playlist_tracks(sp, plid)
    print(len(tlist))


if __name__ == "__main__":

    con = dbutils.get_db_handle()
    sp = SpotipyClient()

    d = {
            "0NmhjttM0NDEWX5D9Amars": "surveys/A.csv",
            "5IwUT6ukJXyeC56lFtbBA8": "surveys/B.csv",
            "61hghH10mCLzpovcvShfwq": "surveys/C.csv",
            "22JkzaRN04pKzPHR0xWicy": "surveys/D.csv",
            "4LlXTpIKiD7fMdAlXpOpRm": "surveys/E.csv",
            "38tYOrFu2SsfevbvRkPTrO": "surveys/F.csv",
            "3AmjqOlzEZoafaXO8PQwAo": "surveys/G.csv",
            "10FpcmqqJD0P9WUdhgP78T": "surveys/H.csv"
        }

    # Select all songs
    querystring = "select id, name, url from ragafeaturedb"
    df = dbutils.query_db_translate_to_pandas(con, querystring)
    df = df.sample(frac=1.0).reset_index(drop=True)

    #def sample_playlist(sp, con, ntracks, plid):
    #    querystring = "select id, name, url from ragafeaturedb"
    #    df = dbutils.query_db_translate_to_pandas(con, querystring)
    #    fr = (ntracks * 1.0)/(df.shape[0])
    #    df = df.sample(frac=fr).reset_index(drop=True)
    #    tracklist = df['id'].tolist()
    #    utils.add_tracks_to_playlist_id(sp, plid, tracklist)
    #    df.to_csv(filename)

    #sample_playlist(sp, con, ntracks, plid)

    base = 0
    ntracks = 300
    for plid, fname in d.items():
        print(plid, fname, base)
        tempdf = df[base:base+ntracks]
        tracklist = tempdf['id'].tolist()
        utils.add_tracks_to_playlist_id(sp, plid, tracklist)
        tempdf.to_csv(fname)
        base += ntracks
        print(plid, fname, "... Done")


    dbutils.close_db(con)
