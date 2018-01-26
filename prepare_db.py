import sys
import psycopg2
import utils
from defs import SpotipyClient, pldesc, GracenoteClient, sp_feature_list, gn_feature_list
import dbutils
import pandas as pd
import pandas.io.sql as psql
from utils import stodq
import re
import time

def testword(word):
    if not word:
        return False
    if word.isspace():
        return False
    return True

def get_keywords():
    keywords = []
    with open("ragalist.txt", "r") as fh:
        for line in fh:
            stripline = line.strip()
            splitline = stripline.split('\t')
            if len(splitline) == 0:
                continue
            if len(splitline) == 1:
                if testword(splitline[0]): keywords.append(splitline[0])
            else:
                if testword(splitline[0]):
                    keywords.append(splitline[0])
                    if testword(splitline[1]):
                        keywords.append(splitline[1])
        extras = ['Gat', 'Taan', 'Alap', 'Jor', 'Tillana', 'Thillana', 'Aalap'
                  ,'Raag', 'Khayal', 'Khayaal', 'Tarana', 'Taraana', 'Raga'
                  ,'Drut', 'Khyal', 'Mukhri', 'Thumri', 'Bandish', 'Tappa', 'Vilambit']
        for word in extras:
            keywords.append(word)
    return keywords

#=============== Code begin: Database of playlists: for future ============
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


#=============== Code begin: Database of tracks ==============
def create_tracks_table(con):
    try:
        print("In create tracks table:")
        cur = con.cursor()
        #"id name uri url artist_name artist_id duration_ms href"
        #"id name uri url duration_ms href artist_id artist_name artist_url album_id album_name album_url"
        curstr = ("CREATE TABLE ALLTRACKS"
                    + " ("
                    + "ID VARCHAR(32) NOT NULL PRIMARY KEY,"
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


def add_track_descriptor_to_db(con, td):
    try:
        cur = con.cursor()
        #"id name uri url artist_name artist_id duration_ms href"
        action = "INSERT INTO"
        dbname = "ALLTRACKS"
        colnames = "(id, name, uri, url, artist_name, artist_id, duration_ms, href)"
        extras = ("VALUES ("
                  + "\'" + stodq(td.id) + "\'," 
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
        #curstr = action + " " + dbname + " " + colnames + " " + extras
        curstr = action + " " + dbname + " " + extras
        #print(curstr)
        cur.execute(curstr)
        con.commit()
    except Exception as e:
        con.rollback()
        print("Error adding track descriptor to db : ", str(e))
    return


def add_tracks_from_playlist_id_to_db(sp, con, pid):
    cur = con.cursor()
    print("in add_tracks_from_playlist_id_to_db")
    tdlist = utils.get_playlist_tracks(sp, pid)
    for td in tdlist:
    	add_track_descriptor_to_db(con, td)
#=============== Code end: Database of tracks ==============


#=============== Code begin: Feature database =====================
def create_features_table(con):
    try:
        cur = con.cursor()
        spstr = ""
        for key in sp_feature_list:
            spstr = spstr + ", " + "sp_" + key + " VARCHAR(256) NOT NULL"
        gnstr = ""
        for key in gn_feature_list:
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


def add_features_sp_gn_to_db(con, tid, tname, turl, spfeat, gnfeat):
    try:
        cur = con.cursor()
        #"id name uri url artist_name artist_id duration_ms href"
        spstr, gnstr = "",""
        for key in sp_feature_list:
            spstr = spstr + ", " + "sp_" + key
        for key in gn_feature_list:
            gnstr = gnstr + ", " + "gn_" + key
        colnames = ("(id, name, url"
                    + spstr + gnstr
                    + ")")
        # (id, name, url, sp_danceability, sp_energy, sp_key, sp_loudness, sp_mode, sp_speechiness, sp_acousticness, sp_instrumentalness, sp_liveness, sp_valence, sp_tempo, sp_analysis_url, sp_duration_ms, sp_time_signature, gn_gnid, gn_genre_1, gn_genre_2, gn_genre_3, gn_mood_1, gn_mood_2, gn_tempo_1, gn_tempo_2, gn_tempo_3)
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


def add_tracks_to_gracenote_db(con, sp, gn, df):
    counter = 0
    cur = con.cursor()
    spfeat, gnfeat = None, None
    for idx, row in df.iterrows():
        try:
            if(counter % 700 == 0):
                gn.renew()
                time.sleep(5)
            counter += 1
            sp_id = row['id']
            sp_name = row['name']
            sp_artist = row['artist_name']
            sp_url = row['url']
            print(sp_id, sp_name, sp_artist, sp_url)
            cur.execute("select * from featuredb where id like \'" + str(sp_id) + "\'")
            if cur.fetchone() is not None:
                print("Track features already in database. Skipping id = sp_id", sp_id);
                continue # skip rest of the loop
            gnfeat = utils.get_gracenote_feature_info(gn, sp_id, sp_name, sp_artist)
            spfeat = utils.get_spotify_feature_info(sp, row)
            if gnfeat is None:
                print('gnfeat is None for current track: id, name', row['id'], row['name'])
                continue
            if spfeat is None:
                print('spfeat is None for current track: id, name', row['id'], row['name'])
                continue
            if 'NaN' not in gnfeat.values() and 'NaN' not in spfeat[0].values():
                add_features_sp_gn_to_db(con, sp_id, sp_name, sp_url, spfeat, gnfeat)
                print("Added track = ", sp_id, sp_name)
                print("Total tracks seen in this trip = ", counter)
            else:
                print("NaN found: ", spfeat, gnfeat)
        except Exception as e:
            print('Issue adding features in add_tracks_to_gracenote_db' )
            print('current track: id, name', row['id'], row['name'])
            print('Exception = ', str(e))
            print(gnfeat)
        sys.stdout.flush()


def try_sql_query(sp, con):
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
        #df = pd.read_sql('SELECT * from alltracks WHERE name like \'%Raga%\' OR name like \'%Rag%\' OR name like \'%Alap%\' OR name like \'Gat\'', con)
        print(df.shape)
        action = action + tempstr
        action = action + " name like \'%Raaga%\'"
        df = pd.read_sql(action, con)
        #df = pd.read_sql('SELECT * from alltracks WHERE name like \'%Raga%\' OR name like \'%Rag%\' OR name like \'%Alap%\' OR name like \'Gat\'', con)
        print(df.shape)
    except Exception as e:
        con.rollback()
        print("Error in printing table: ", str(e))
    return

#================== Code end: Feature database ====================

if __name__ == "__main__":
    con = dbutils.get_db_handle()
    sp = SpotipyClient()
    gn = GracenoteClient()
    #pid = "4Q9SbpQm3REK3Ey3tZha3N" #Database_SaReGaMood
    pid = "4o3WqxqqrNRd6u16TVj5K6" #Database_Newragas

    # This function can potentially be useful in future.
    def do_the_due_playlist_table(sp, con):
        create_playlist_table(con)
        pl = utils.get_user_playlist_descriptor_list(sp)
        for desc in pl:
           add_playlist_descriptor_to_db(con, desc)
        print_playlist_table(con)

    def do_the_due_tracks_table(sp, con):
        create_tracks_table(con)
        add_tracks_from_playlist_id_to_db(sp, con, pid)

    def do_the_due_featuredb(sp, gn, con):
        create_features_table(con)
        querystring = "select * from alltracks"
        df = dbutils.query_db_translate_to_pandas(con, querystring)
        df = df.sample(frac=1).reset_index(drop=True)
        add_tracks_to_gracenote_db(con, sp, gn, df)

    print("doing the query")
    #do_the_due_featuredb(sp, gn, con)
    #querystring = "select * from featuredb"
    #df = dbutils.query_db_translate_to_pandas(con, querystring)
    print(df.shape)
    #do_the_due_tracks_table(sp, con)
    #try_sql_query(sp, con)
    dbutils.close_db(con)
