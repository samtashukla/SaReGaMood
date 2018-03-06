import sys
import psycopg2
import utils
from defs import SpotipyClient, pldesc, GracenoteClient, sp_feature_list, gn_feature_list
import dbutils
import pandas as pd
import pandas.io.sql as psql
from utils import stodq, testword, get_keywords
import re
import time

#=============== Code begin: Master database table of tracks ==============
# Notes:
# 1) This database table can contain some tracks which correspond to music categories that
#    we do not desire for our analysis. These tracks will later be filtered to create a new database.
# 2) This database table does not contain "audio features" of tracks but only "administrative info" like
#    track name, artist id, artist name, etc. Audio features of tracks will have a separate database.


# Function to create a table called "alltracks" for storing a track descriptor
def create_tracks_table(con):
    try:
        print("In create tracks table:")
        cur = con.cursor()
        curstr = ("CREATE TABLE ALLTRACKS"
                    + " ("
                    + "ID VARCHAR(32) NOT NULL PRIMARY KEY," # primary key is string for us
                    + " NAME VARCHAR(256) NOT NULL,"
                    + " URI VARCHAR(256) NOT NULL,"
                    + " URL VARCHAR(256) NOT NULL,"
                    + " DURATION_MS INTEGER NOT NULL,"
                    + " HREF VARCHAR(256) NOT NULL,"
                    + " ARTIST_ID VARCHAR(256) NOT NULL,"
                    + " ARTIST_NAME VARCHAR(256) NOT NULL,"
                    + " ARTIST_URL VARCHAR(256) NOT NULL,"
                    + " ALBUM_ID VARCHAR(256) NOT NULL,"
                    + " ALBUM_NAME VARCHAR(256) NOT NULL,"
                    + " ALBUM_URL VARCHAR(256) NOT NULL"
                    + ")")
        print(curstr)
        cur.execute(curstr)
        con.commit()
    except Exception as e:
        con.rollback()
        print("Error creating table: ", str(e))
    return

# Function to add a track descriptor (see namedtuple trdesc in defs.py) to alltracks database
# For inputs, it takes database handle to alltracks and a track descriptor
def add_track_descriptor_to_db(con, td):
    try:
        cur = con.cursor()
        action = "INSERT INTO"
        dbname = "ALLTRACKS"
        # All the column names
        colnames = "(id, name, uri, url, artist_name, artist_id, duration_ms, href)"
        extras = ("VALUES (" # Add values in the order of column names
                  + "\'" + stodq(td.id) + "\',"  # stodq takes care of obnoxious single quotes in string
                  + "\'" + stodq(td.name) + "\',"
                  + "\'" + stodq(td.uri) + "\',"
                  + "\'" + stodq(td.url) + "\',"
                  + str(td.duration_ms) + ","
                  + "\'" + stodq(td.href) + "\',"
                  + "\'" + stodq(td.artist_id) + "\',"
                  + "\'" + stodq(td.artist_name) + "\'," 
                  + "\'" + stodq(td.artist_url) + "\'," 
                  + "\'" + stodq(td.album_id) + "\',"
                  + "\'" + stodq(td.album_name) + "\'," 
                  + "\'" + stodq(td.album_url) + "\'" 
                 ")")
        curstr = action + " " + dbname + " " + extras
        cur.execute(curstr)
        con.commit()
    except Exception as e:
        con.rollback() # rollback database handle if something fails
        print("Error adding track descriptor to db : ", str(e))
    return


# Function to add tracks from a spotify playlist to alltracks database
# For inputs, it takes user's spotify handle, database handle to alltracks and spotify playlist id
def add_tracks_from_playlist_id_to_db(sp, con, pid):
    cur = con.cursor()
    print("in add_tracks_from_playlist_id_to_db")
    tdlist = utils.get_playlist_tracks(sp, pid)
    for td in tdlist:
    	add_track_descriptor_to_db(con, td)
#=============== Code end: Database of tracks ==============


#=============== Code begin: Feature database =====================
# Notes: 
# 1) "featuredb" database table contains "audio features" of tracks (e.g., rhythm, tempo, key, gracenote features, etc.)
# 2) "ragafeaturedb" database table contains audio features of tracks used in our analysis

# Create a table for audio features named "featuredb"
# For inputs, it needs a handle to the database
def create_features_table(con):
    try:
        cur = con.cursor()
        spstr = ""
        for key in sp_feature_list: # sp_feature_list is a global variable defined in defs.py
            spstr = spstr + ", " + "sp_" + key + " VARCHAR(256) NOT NULL"
        gnstr = ""
        for key in gn_feature_list: # gn_feature_list is a global variable defined in defs.py
            gnstr = gnstr + ", " + "gn_" + key + " VARCHAR(256) NOT NULL"
        curstr = ("CREATE TABLE FEATUREDB"
                    + " ("
                    + "ID VARCHAR(32) NOT NULL PRIMARY KEY"
                    + ", NAME VARCHAR(256) NOT NULL"
                    + ", URL VARCHAR(256) NOT NULL"
                    + spstr
                    + gnstr
                    + ")")
        cur.execute(curstr)
        con.commit()
    except Exception as e:
        con.rollback()
        print("Error creating table: ", str(e))
    return


# Create a table for audio features named "ragafeaturedb"
# It contains audio features of only those tracks to be used in our analysis later on.
# For inputs, it needs a handle to the database
def create_ragafeaturedb(con):
    # Has exact same columns as featuredb
    try:
        cur = con.cursor()
        spstr = ""
        for key in sp_feature_list: # sp_feature_list is a global variable defined in defs.py
            spstr = spstr + ", " + "sp_" + key + " VARCHAR(256) NOT NULL"
        gnstr = ""
        for key in gn_feature_list: # gn_feature_list is a global variable defined in defs.py
            gnstr = gnstr + ", " + "gn_" + key + " VARCHAR(256) NOT NULL"
        curstr = ("CREATE TABLE RAGAFEATUREDB"
                    + " ("
                    + "ID VARCHAR(32) NOT NULL PRIMARY KEY"
                    + ", NAME VARCHAR(256) NOT NULL"
                    + ", URL VARCHAR(256) NOT NULL"
                    + spstr
                    + gnstr
                    + ")")
        cur.execute(curstr)
        con.commit()
    except Exception as e:
        con.rollback()
        print("Error creating table: ", str(e))
    return


# Utility to add a track and its audio features to featuredb database
# Inputs:
#   con: database handle
#   tid, tname, turl: spotify track id, track name, track url
#   spfeat: dictionary of spotify audio features
#   gnfeat: dictionary of gracenote audio features
def add_features_sp_gn_to_db(con, tid, tname, turl, spfeat, gnfeat):
    try:
        cur = con.cursor()
        spfeatvals = {"sp_"+k : v for k, v in spfeat[0].items()}
        gnfeatvals = {"gn_"+k : v for k, v in gnfeat.items()}
        action = "INSERT INTO"
        dbname = "FEATUREDB"
        extras = ("VALUES ("
                  + "\'" + stodq(tid) + "\',"
                  + "\'" + stodq(tname) + "\',"
                  + "\'" + stodq(turl) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_danceability'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_energy'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_key'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_loudness'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_mode'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_speechiness'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_acousticness'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_instrumentalness'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_liveness'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_valence'])) + "\',"
                  + "\'" + stodq(str(spfeatvals['sp_tempo'])) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_gnid']) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_genre_1']) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_genre_2']) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_genre_3']) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_mood_1']) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_mood_2']) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_tempo_1']) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_tempo_2']) + "\',"
                  + "\'" + stodq(gnfeatvals['gn_tempo_3']) + "\'"
                 ")")
        curstr = action + " " + dbname + " " + extras
        cur.execute(curstr)
        con.commit()
    except Exception as e:
        con.rollback()
        print("Error adding track descriptor to db : ", str(e))
    return


# Following is a utility function to take a row from "featuredb" and insert it into "ragafeaturedb"
# This will be called when we filter "featuredb" for the tracks we desire to include in our analysis
def insert_row_into_ragafeaturedb(con, row):
        # Must have all the elements in the same order as columns of raafeaturedb
        # Now try inserting each row into featuredb
        try:
            cur = con.cursor()
            #"id name uri url artist_name artist_id duration_ms href"
            # (id, name, url, sp_danceability, sp_energy, sp_key, sp_loudness, sp_mode,
            # sp_speechiness, sp_acousticness, sp_instrumentalness, sp_liveness, sp_valence,
            # sp_tempo, sp_analysis_url, sp_duration_ms, sp_time_signature, gn_gnid, gn_genre_1,
            #gn_genre_2, gn_genre_3, gn_mood_1, gn_mood_2, gn_tempo_1, gn_tempo_2, gn_tempo_3)
            action = "INSERT INTO"
            dbname = "RAGAFEATUREDB"
            extras = ("VALUES ("
                  + "\'" + row[0] + "\',"
                  + "\'" + row[1] + "\',"
                  + "\'" + row[2] + "\',"
                  + "\'" + row[3] + "\',"
                  + "\'" + row[4] + "\',"
                  + "\'" + row[5] + "\',"
                  + "\'" + row[6] + "\',"
                  + "\'" + row[7] + "\',"
                  + "\'" + row[8] + "\',"
                  + "\'" + row[9] + "\',"
                  + "\'" + row[10] + "\',"
                  + "\'" + row[11] + "\',"
                  + "\'" + row[12] + "\',"
                  + "\'" + row[13] + "\',"
                  + "\'" + row[14] + "\',"
                  + "\'" + row[15] + "\',"
                  + "\'" + row[16] + "\',"
                  + "\'" + row[17] + "\',"
                  + "\'" + row[18] + "\',"
                  + "\'" + row[19] + "\',"
                  + "\'" + row[20] + "\',"
                  + "\'" + row[21] + "\',"
                  + "\'" + row[22] + "\'"
                 ")")
            curstr = action + " " + dbname + " " + extras
            cur.execute(curstr)
            con.commit()
        except Exception as e:
            cur.close()
            print("Error adding track descriptor to ragafeatuedb : ", str(e))


# Following utility function filters "featuredb" database to select the tracks we
# desire to be included in our analysis. This filtering is keywords-based (i.e., the tracks
# which contain any of the keywords will be included in a new database called ragafeaturedb)
# For input, it needs a database connection handle
def filter_db(con): 

        # Step 1: get all the songs from alltracks which have keyword in name
        action = 'SELECT * from alltracks WHERE '
        keywords = get_keywords()
        for word in keywords:
            tempstr = " name like \'%" + word + "%\' OR"
            action = action + tempstr
        for word in keywords:
            tempstr = " album_name like \'%" + word + "%\' OR"
            action = action + tempstr
        action = action + " name like \'%Raaga%\'"
        df = pd.read_sql(action, con)

        # Step 2: For each of the songs, see whether trackid exists in featuredb
        # Because that means both spotify and gracenote features exist for that song
        for idx, row in df.iterrows():
            # Make a query to filterdb to see whether song exists in featuredb
            trackid = row['id']
            tempaction = "SELECT * from featuredb WHERE id like \'%" + trackid +"%\'"
            try:
                cur = con.cursor()
                cur.execute(tempaction)
                data = cur.fetchall()
                cur.close()
                for row in data: # We found a track that we want. Insert it into the new database
                    insert_row_into_ragafeaturedb(con, row)
            except Exception as e:
                print("Issue with trackid in filter_db = ", trackid)
                print("issue ", str(e))
        


# Utility which:
#  For each tracks in a given dataframe
#   gets its "audio features" from spotify
#   gets its "audio features" from gracenote
#   inserts it into "featuredb"
# For inputs, it needs database handle, spotify handle, gracenote handle and dataframe
# The dataframe df must be selected as a slice from the master database "alltracks"
def add_tracks_to_featuredb(con, sp, gn, df):

    counter = 0
    cur = con.cursor()
    spfeat, gnfeat = None, None

    for idx, row in df.iterrows():
        # Go over each row (or track) in the given dataframe and fetch its "audio features"

        try:
            if(counter % 700 == 0): # Renew gracenote authorization after a certain number of requests
                gn.renew()  
                time.sleep(5)
            counter += 1
            sp_id = row['id']
            sp_name = row['name']
            sp_artist = row['artist_name']
            sp_url = row['url']
            cur.execute("select * from featuredb where id like \'" + str(sp_id) + "\'")
            if cur.fetchone() is not None: # do not send request if we already have info in target databse
                continue # skip rest of the loop
            gnfeat = utils.get_gracenote_feature_info(gn, sp_id, sp_name, sp_artist) # get gracenote features
            spfeat = utils.get_spotify_feature_info(sp, row) # get spotify audio feaures
            if gnfeat is None: # skip if we don't find gracenote info
                print('gnfeat is None for current track: id, name', row['id'], row['name'])
                continue
            if spfeat is None: # skip if we don't find spotify info 
                print('spfeat is None for current track: id, name', row['id'], row['name'])
                continue
            if 'NaN' not in gnfeat.values() and 'NaN' not in spfeat[0].values(): # add tracks without 'NaN'
                add_features_sp_gn_to_db(con, sp_id, sp_name, sp_url, spfeat, gnfeat)
                print("Added track = ", sp_id, sp_name)
            else:
                print("NaN found: ", spfeat, gnfeat)

        except Exception as e:
            print('Issue adding features in add_tracks_to_gracenote_db' )
            print('current track: id, name', row['id'], row['name'])
            print('Exception = ', str(e))
            print(gnfeat)
        sys.stdout.flush()
#================== Code end: Feature database ====================


#=============== Code begin: Database of playlists: for future analysis ============
def create_playlist_table(con):
    try:
        cur = con.cursor()
        cur.execute("CREATE TABLE TEST_USER_PLAYLISTS(ID VARCHAR(32) NOT NULL PRIMARY KEY, Name VARCHAR(256) NOT NULL, Uri VARCHAR(256) NOT NULL, Url VARCHAR(256) NOT NULL)")
        con.commit()
    except Exception as e:
        con.rollback()
        print("Error creating table: ", str(e))
    return


def add_playlist_descriptor_to_db(con, pd):
    try:
        cur = con.cursor()
        action = "INSERT INTO"
        dbname = "TEST_USER_PLAYLISTS"
        colnames = "(id, name, uri, url)"
        extras = ("VALUES ("
                  + "\'" + stodq(pd.id) + "\'," 
                  + "\'" + stodq(pd.name) + "\',"
                  + "\'" + stodq(pd.uri) + "\',"
                  + "\'" + stodq(pd.url) + "\'"
                 ")")
        #curstr = action + " " + dbname + " " + colnames + " " + extras
        curstr = action + " " + dbname + " " + extras
        print(curstr)
        cur.execute(curstr)
        con.commit()
    except Exception as e:
        con.rollback()
        print("Error adding playlist descriptor to db : ", str(e))
    return


def print_playlist_table(con):
    try:
        cur = con.cursor()
        cur.execute('SELECT * FROM test_user_playlists')
        for pl in map(pldesc._make, cur.fetchall()): # column names must have same order like pldesc
            print(pl)
    except Exception as e:
        con.rollback()
        print("Error in printing table: ", str(e))
    return

#=============== Code end: Database of playlists: for future ============


# Utility which gets the tracks from database which has "raga-related" keywords
def get_raga_tracks(con):
    try:
        cur = con.cursor()
        action = 'SELECT * from alltracks WHERE '
        keywords = get_keywords()
        for word in keywords:
            tempstr = " name like \'%" + word + "%\' OR"
            action = action + tempstr
        for word in keywords:
            tempstr = " album_name like \'%" + word + "%\' OR"
            action = action + tempstr
        action = action + " name like \'%Raaga%\'"
        df = pd.read_sql(action, con)
        print(df.shape)
        return df
    except Exception as e:
        con.rollback()
        print("Error in printing table: ", str(e))
    return None


if __name__ == "__main__":
    con = dbutils.get_db_handle()
    sp = SpotipyClient()
    gn = GracenoteClient()
    pid = "4o3WqxqqrNRd6u16TVj5K6" # insert your playlist id here

    # Create master table of all tracks if it does not exist already
    # insert songs from a given playlist into this database
    def do_the_due_tracks_table(sp, con):
        create_tracks_table(con)
        add_tracks_from_playlist_id_to_db(sp, con, pid)

    # Select tracks which have keywords corresponding to ragas and
    # insert them into featuredb. Note that ideally we would have wanted
    # featuredb to contain only such tracks. But we made a mistake at some
    # point to include spurious tracks into featuredb, thus we had to create
    # ragafeaturedb which gets filtered based on keywords from featuredb.
    # At some point, we should clean-up featuredb and merge the roles
    # of ragafeaturedb and featuredb
    def do_the_due_featuredb(sp, gn, con):
        create_features_table(con)
        df = get_raga_tracks(con)
        df = df.sample(frac=1).reset_index(drop=True)
        add_tracks_to_featuredb(con, sp, gn, df)

    # Creates ragafeaturedb if it does not exist and filters tracks from featuredb
    # into ragafeaturedb which have desired keywords in their name
    def do_the_due_ragafeaturedb(sp, gn, con):
        create_ragafeaturedb(con)
        filter_db(con)

    #do_the_due_tracks_table(sp, con)
    #do_the_due_featuredb(sp, gn, con)
    #do_the_due_ragafeaturedb(sp, gn, con)
