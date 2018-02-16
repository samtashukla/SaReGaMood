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

moodlist = ["contemplative", "easygoing", "happy", "lively", "other", "peaceful",
        "pining", "romantic", "sad", "sentimental", "serious", "transcendental"]


def process_file(moodlist, tracktolabel, tracktoname, tracktourl, filename):
    with open(filename, "r") as fh:
        for line in fh:
            strip = line.strip()
            sl = strip.split('\t')
            if (len(sl) <= 4):
                continue
            url = sl[1]
            trackid = sl[2]
            trackname = sl[3]
            tempmood = sl[4]
            if "/" in tempmood:
                mood = tempmood.rpartition('/')[0] # pining/longing => pining
            else:
                mood  = tempmood
            if mood not in moodlist:
                continue
            tracktolabel[trackid] = mood
            tracktoname[trackid] = trackname
            tracktourl[trackid] = url


def get_trackfeat(con, tracktofeat, trackidlist, excludeset):
    for tid in trackidlist:
        querystr = ("SELECT sp_danceability, sp_energy, sp_loudness, sp_speechiness, "
            + "sp_acousticness, sp_instrumentalness, sp_liveness, sp_valence, sp_tempo "
             + "from featuredb WHERE id like \'%" + tid + "%\' OR url like \'%" + tid + "%\'")
        adf = dbutils.query_db_translate_to_pandas(con, querystr)
        if adf.shape[0] != 1:
            print("Error gn_trackfeat: track not found or multiple copies found")
            print("Trackid = " + tid + " will be excluded later on in the analysis")
            excludeset.add(tid)
        for idx, row in adf.iterrows():
            tracktofeat[tid] = row.values.tolist()


def get_trackgn(con, tracktogn, trackidlist, excludeset):
    for tid in trackidlist:
        querystr = ("SELECT gn_mood_1 "
             + "from featuredb WHERE id like \'%" + tid + "%\' OR url like \'%" + tid + "%\'")
        adf = dbutils.query_db_translate_to_pandas(con, querystr)
        if adf.shape[0] != 1:
            print("Error get_trackgn: track not found or multiple copies found")
            print("Trackid = " + tid + " will be excluded later on in the analysis")
            excludeset.add(tid)
        for idx, row in adf.iterrows():
            tracktogn[tid] = row['gn_mood_1']



def prune(tracktolabel, tracktoname, tracktourl, tracktofeat, tracktogn, excludeset):
    for k in excludeset:
        print("Removing trackid = " + k + " from the analysis")
        del tracktolabel[k]
        del tracktoname[k]
        del tracktourl[k]
        del tracktofeat[k]
        del tracktogn[k]


def reorganize(tracktofeat, tracktolabel):
    labellist = list(sorted(set(tracktolabel.values()))) # Basically, again you will get moodlist
    orderedtracklist = []
    temp = []
    offset = 0
    offsetlist = []
    for label in labellist:
        tracks_for_this_mood = [tid for tid in tracktolabel if tracktolabel[tid] == label]
        print(label, len(tracks_for_this_mood))
        if tracks_for_this_mood: # i.e., not empty
            orderedtracklist.extend(tracks_for_this_mood)
            for tid in tracks_for_this_mood:
                temp.append(tracktofeat[tid])
            offsetlist.append(offset)
            offset += len(tracks_for_this_mood)
    xfeat = np.asarray(temp, dtype=np.float32)
    xlabel = [tracktolabel[tid] for tid in orderedtracklist]
    return xfeat, xlabel, orderedtracklist, offsetlist, labellist


def compute_normalization_coefficients(con):
    querystr = ("SELECT sp_danceability, sp_energy, sp_loudness, sp_speechiness, "
            + "sp_acousticness, sp_instrumentalness, sp_liveness, sp_valence, sp_tempo "
             + "from featuredb")
    df = dbutils.query_db_translate_to_pandas(con, querystr)
    featval = df.values.astype(np.float32)
    normalize_coeffs = []
    for i in range(featval.shape[1]): # Normalize columns in this loop
        normalize_coeffs.append(max(featval[:,i], key=abs))
    return normalize_coeffs


def normalize_columns(featmat, nc):
    for i in range(len(nc)):
        featmat[:,i] = featmat[:,i] / nc[i]


def compute_nearest_neighbors(moodlist, centroidmat, testmat, tracknamelist, trackurllist):
    # Do not use
    tree = scipy.spatial.KDTree(centroidmat)
    for i, row in enumerate(testmat):
        dist, idx = tree.query(row, 3)
        print("Track = ", tracknamelist[i])
        print("URL = ", trackurllist[i])
        print("Moods : " + moodlist[idx[0]] + ", " + moodlist[idx[1]] + ", " + moodlist[idx[2]])


def test(con, orderedmoodlist, centroidlist, nc):

    querystr = "select id, name, url from ragafeaturedb "
    df = dbutils.query_db_translate_to_pandas(con, querystr)
    testdf = df.sample(frac=0.01).reset_index(drop=True)

    tracktolabel = {}
    tracktoname = {}
    tracktourl = {}
    tracktofeat = {}
    tracktogn = {}
    excludeset = set()

    tlist = df['id'].tolist()
    get_trackfeat(con, tracktofeat, tlist, excludeset)
    get_trackgn(con, tracktogn, tlist, excludeset)
    prune(tracktolabel, tracktoname, tracktourl, tracktofeat, tracktogn, excludeset)

    # Incomplete: classify using nearest neighbors


def compute_centroids(xfeat, offsetlist):
    ol = offsetlist[:]  # creates a deep copy for a simple list 
    ol.append(xfeat.shape[0])
    centroidlist = []
    for i in range(len(ol) - 1):
        start, end = ol[i], ol[i+1]
        newcentroid = np.mean(xfeat[start:end], axis = 0)
        centroidlist.append(newcentroid)
    return centroidlist
    

if __name__ == "__main__":
    con = dbutils.get_db_handle()

    moodlist = ["contemplative", "easygoing", "happy", "lively", "peaceful",
        "pining", "romantic", "sad", "serious", "transcendental",
        "sentimental"]

    tracktolabel = {}
    tracktoname = {}
    tracktourl = {}
    tracktofeat = {}
    tracktogn = {}
    excludeset = set()

    process_file(moodlist, tracktolabel, tracktoname, tracktourl, "surveys/bhardo-1.tsv")
    process_file(moodlist, tracktolabel, tracktoname, tracktourl, "surveys/survey-ananthu.tsv")
    process_file(moodlist, tracktolabel, tracktoname, tracktourl, "surveys/survey-uma.tsv")

    if len(tracktolabel) != len(tracktoname) or len(tracktolabel) != len(tracktourl):
        print("Error: length mismatch")
        sys.exit(1)

    tlist = list(tracktolabel.keys())
    get_trackfeat(con, tracktofeat, tlist, excludeset)
    get_trackgn(con, tracktogn, tlist, excludeset)
    prune(tracktolabel, tracktoname, tracktourl, tracktofeat, tracktogn, excludeset)
    print(len(tracktolabel)) # get no. of keys

    nc = compute_normalization_coefficients(con)
    print(nc)

    # In the following: xlabel is ~300x9 numpy matrix, xlabel is the mood label of each row
    # xtrackids is the trackid of each row, offsetlist is like at which position a new mood
    # starts, and orderedmoodlist is the order in which different moods appear in xlabel
    xfeat, xlabel, xtrackids, offsetlist, orderedmoodlist = reorganize(tracktofeat, tracktolabel)
    normalize_columns(xfeat, nc)

    #----------------
    # tracktolabel, tracktoname, tracktourl, tracktofeat, tracktogn
    surveydf = pd.DataFrame(columns=['trackid', 'name', 'url', "nsp_danceability", "nsp_energy", "nsp_loudness", "nsp_speechiness",
                "nsp_acousticness", "nsp_instrumentalness", "nsp_liveness", "nsp_valence", "nsp_tempo", "gn_mood_1", "label"])
    nsp_cols=["nsp_danceability", "nsp_energy", "nsp_loudness", "nsp_speechiness",
                "nsp_acousticness", "nsp_instrumentalness", "nsp_liveness", "nsp_valence", "nsp_tempo"]
    for i, myid in enumerate(xtrackids):
        d = {}
        d["trackid"] = myid
        d["label"]= tracktolabel[myid]
        d["name"] = tracktoname[myid]
        d["url"] = tracktourl[myid]
        d["gn_mood_1"] = tracktogn[myid]
        myfeat = xfeat[i]
        for j, col in enumerate(nsp_cols):
            d[col] = myfeat[j]
        new_df = pd.DataFrame(d, index=[i])
        surveydf = surveydf.append(new_df)
    #surveydf.to_csv("playlists/test.csv")
    surveydf.to_pickle("playlists/allsurveys.pkl")
    #----------------
    
    centroidlist = compute_centroids(xfeat, offsetlist)

    ol = offsetlist[:]
    ol.append(xfeat.shape[0])
    for i in range(len(ol)-1):
        start, end = ol[i], ol[i+1]
        currmood = orderedmoodlist[i]
        with open("playlists/"+currmood+".txt", "w") as fh:
            for tid in xtrackids[start:end]:
                tname = tracktoname[tid]
                turl = tracktourl[tid]
                templist = [tid, turl, tname]
                writestr = "###".join(templist)
                fh.write(writestr + "\n")




    #test(con, orderedmoodlist, centroids, nc):

    dbutils.close_db(con)
