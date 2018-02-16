import sys
import psycopg2
import utils
from defs import SpotipyClient, pldesc, GracenoteClient
import pandas as pd
import pandas.io.sql as psql
from utils import stodq
import re
import dbutils
import scipy
import scipy.spatial
import numpy as np
import itertools

globalvars = {}

def preliminary():
    with open("survey_bhardo.tsv", "r") as fh:
        count = 0
        d = dict()
        for line in fh:
            count += 1
            strip = line.strip()
            sl = strip.split('\t')
            if (len(sl) <= 4):
                continue
            mood = sl[4]
            d[mood] = d.get(mood, 0) + 1
        entries = 0
        for k in sorted(d, key=d.get, reverse=True):
            entries += d[k]
        print(entries)
        for k in sorted(d, key=d.get, reverse=True):
            print(k, d[k], "%.2f" % (d[k] * 1.0 / entries * 100))


def newsurvey(filename):
    with open(filename, "r") as fh:
        count = 0
        d = dict()
        trackdict = dict()
        trackurldict = dict()
        tracklist = []
        tracknamedict = dict()
        for line in fh:
            count += 1
            strip = line.strip()
            sl = strip.split('\t')
            if (len(sl) <= 4):
                continue
            mood = sl[4]
            d[mood] = d.get(mood, 0) + 1
            if mood in trackdict:
                trackdict[mood].append(sl[2])
                trackurldict[mood].append(sl[1])
                tracknamedict[mood].append(sl[3])
            else:
                trackdict[mood] = [sl[2]]
                trackurldict[mood] = [sl[1]]
                tracknamedict[mood] = [sl[3]]
            tracklist.append(sl[2])
        entries = 0
        for k in sorted(d, key=d.get, reverse=True):
            entries += d[k]
        print(entries)
        for k in sorted(d, key=d.get, reverse=True):
            print(k, d[k], "%.2f" % (d[k] * 1.0 / entries * 100))

    for mood, moodtracks in trackdict.items():
        if "/" in mood:
            singlename = mood.rpartition('/')[0] # pining/longing => pining
        else:
            singlename = mood
        with open("surveys/playlist-" + singlename + ".txt", "w") as fh:
            for tid, turl, tname in zip(moodtracks, trackurldict[mood], tracknamedict[mood]):
                fh.write(tid + "\n")
        with open("surveys/bhardo-survey-tracks.csv", "a") as fh:
            for tid, turl, tname in zip(moodtracks, trackurldict[mood], tracknamedict[mood]):
                fh.write(tid+ "###" + tname + "###" + turl + "\n")
    # trackdict is a dictionary containing {mood: [trackid list]} mappings
    return d, tracklist, trackdict


def get_training_set_track_features(con, trackdict):
    #querystr = ("SELECT sp_danceability, sp_energy, sp_key, sp_loudness, sp_mode, sp_speechiness, "
    #           + "sp_acousticness, sp_instrumentalness, sp_liveness, sp_valence, sp_tempo "
    #           + "from featuredb WHERE id like \'%" + tid + "%\' OR url like \'%" + tid + "%\'")
    tflist = []
    tempdict = {}
    for mood, mtlist in trackdict.items():
        if mood == "other":
            continue
        tempdict[mood] = []
        for tid in mtlist:
            querystr = ("SELECT sp_danceability, sp_energy, sp_loudness, sp_speechiness, "
               + "sp_acousticness, sp_instrumentalness, sp_liveness, sp_valence, sp_tempo "
               + "from featuredb WHERE id like \'%" + tid + "%\' OR url like \'%" + tid + "%\'")
            adf = dbutils.query_db_translate_to_pandas(con, querystr)
            if adf.shape[0] != 1:
                print("Error: track not found or multiple copies found")
                sys.exit(1)
            querystr = ("SELECT duration_ms "
               + "from alltracks WHERE id like \'%" + tid + "%\' OR url like \'%" + tid + "%\'")
            bdf = dbutils.query_db_translate_to_pandas(con, querystr)
            if bdf.shape[0] != 1:
                print("Error: track not found or multiple copies found")
                sys.exit(1)
            cdf = pd.concat([adf, bdf], axis=1)
            for idx, row in cdf.iterrows():
                tflist.append(row.values.tolist())
                tempdict[mood].append(row.values.tolist())
    return tflist, tempdict



def get_matching_tracks_training_set(con, trackdict):
    tflist, tempdict = get_training_set_track_features(con, trackdict)

    moodmatdict = {}
    fullmat = np.asarray(tflist, dtype=np.float32)
    print(fullmat.shape)

    globalvars["maxtempo"] = np.max(fullmat[:,8])
    globalvars["maxduration"] = np.max(fullmat[:,9])
    print(globalvars["maxtempo"], globalvars["maxduration"])

    fullmat[:,8] = fullmat[:,8]/globalvars["maxtempo"]
    fullmat[:,9] = fullmat[:,9]/globalvars["maxduration"]

    for mood, moodtracklist in tempdict.items():
        moodmatdict[mood] = np.asarray(moodtracklist, dtype=np.float32)
        moodmatdict[mood][:,8] = moodmatdict[mood][:,8]/globalvars["maxtempo"]
        moodmatdict[mood][:,9] = moodmatdict[mood][:,9]/globalvars["maxduration"]
        print(moodmatdict[mood].shape)

    return fullmat, moodmatdict


def compute_nearest_neighbors(moodlist, centroidmat, testmat, tracknamelist, trackurllist):
    tree = scipy.spatial.KDTree(centroidmat)
    for i, row in enumerate(testmat):
        dist, idx = tree.query(row, 3)
        print("Track = ", tracknamelist[i])
        print("URL = ", trackurllist[i])
        print("Moods : " + moodlist[idx[0]] + ", " + moodlist[idx[1]] + ", " + moodlist[idx[2]])



def test(con, moods, centroids):

    querystr = "select id, name, url from featuredb "
    df = dbutils.query_db_translate_to_pandas(con, querystr)
    testdf = df.sample(frac=0.01).reset_index(drop=True)
    trackidlist, tracknamelist = [],[]
    trackidlist = testdf['id'].tolist()
    tracknamelist = testdf['name'].tolist()
    trackurllist = testdf['url'].tolist()
    #for idx, row in testdf.iterrows():
    #    trackidlist.append(testdf['id'].tolist())
    #    tracknamelist.append(testdf['name'].tolist())

    tflist = []
    for tid in trackidlist:
        querystr = ("SELECT sp_danceability, sp_energy, sp_loudness, sp_speechiness, "
            + "sp_acousticness, sp_instrumentalness, sp_liveness, sp_valence, sp_tempo "
             + "from featuredb WHERE id like \'%" + tid + "%\' OR url like \'%" + tid + "%\'")
        adf = dbutils.query_db_translate_to_pandas(con, querystr)
        if adf.shape[0] != 1:
            print("Error: track not found or multiple copies found")
            sys.exit(1)
        querystr = ("SELECT duration_ms "
            + "from alltracks WHERE id like \'%" + tid + "%\' OR url like \'%" + tid + "%\'")
        bdf = dbutils.query_db_translate_to_pandas(con, querystr)
        if bdf.shape[0] != 1:
            print("Error: track not found or multiple copies found")
            sys.exit(1)
        cdf = pd.concat([adf, bdf], axis=1)
        for idx, row in cdf.iterrows():
            tflist.append(row.values.tolist())

    testmat = np.asarray(tflist, dtype=np.float32)
    testmat[:,8] = testmat[:,8]/globalvars["maxtempo"]
    testmat[:,9] = testmat[:,9]/globalvars["maxduration"]
    
    centroidmat = np.asarray(centroids, dtype=np.float32)
    compute_nearest_neighbors(moodlist, centroidmat, testmat, tracknamelist, trackurllist)




def compute_centroids(moodmatdict):
    moodcentroiddict = {}
    for mood, moodmat in moodmatdict.items():
        moodcentroiddict[mood] = np.mean(moodmat, axis=0)
        #print(moodcentroiddict[mood])
    return moodcentroiddict
    

if __name__ == "__main__":
    con = dbutils.get_db_handle()
    #querystr = "select * from featuredb "
    #featuredf = dbutils.query_db_translate_to_pandas(con, querystr)

    mooddict, tracklist, trackdict = newsurvey("surveys/bhardo-1.tsv")
#    fullmat, moodmatdict = get_matching_tracks_training_set(con, trackdict)
#    moodcentroiddict = compute_centroids(moodmatdict)
#
#    moodlist, centroidlist = [], []
#    for mood, centroid in moodcentroiddict.items():
#        moodlist.append(mood)
#        centroidlist.append(centroid)
#
#    test(con, moodlist, centroidlist)
#
#
    dbutils.close_db(con)
