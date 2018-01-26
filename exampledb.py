import sys
import psycopg2
import utils
from defs import SpotipyClient, pldesc, GracenoteClient
import pandas as pd
import pandas.io.sql as psql
from utils import stodq
import re
import dbutils


if __name__ == "__main__":
    con = dbutils.get_db_handle()
    sp = SpotipyClient()
    querystr = "select id, name, artist_name from alltracks"
    #where name like \'%Shri%\'"
    df = dbutils.query_db_translate_to_pandas(con, querystr)
    print(df.to_string())
    print(df.shape)
    for idx, row in df.iterrows():
        utils.get_spotify_feature_info(sp, row) 
    
#    
#    
#    con = dbutils.get_db_handle()
#    gn = GracenoteClient()
#    df = dbutils.query_db_translate_to_pandas(con, "Select name, id, artist_name from alltracks where name like \'%Shri%\'")
#    print(df.to_string())
#    for idx, row in df.iterrows():
#        sp_name = row['name']
#        sp_id = row['id']
#        sp_artist = row['artist_name']
#        utils.get_gracenote_feature_info(gn,  sp_id, sp_name, sp_artist)
#    #con = dbutils.get_db_handle()
#    #querystr = "select id, name, artist_name from alltracks where name like \'%Khamaj%\'"
#    #df = dbutils.query_db_translate_to_pandas(con, querystr)
#    #print(df.to_string())
    dbutils.close_db(con)
