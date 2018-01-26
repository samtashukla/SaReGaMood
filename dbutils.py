import sys
import psycopg2
import utils
from defs import SpotipyClient, pldesc
import pandas as pd
import pandas.io.sql as psql
from utils import stodq
import re
import time

def get_db_handle(dbname="testdb", rolename="spotify"):
    con = None
    constr = "host='localhost' dbname='"+dbname+"'  user='"+rolename+"' password='ics'"
    try:
        con = psycopg2.connect(constr)
    except Exception as e:
        if con:
            con.rollback()
        print('Error creating or connecting handle', str(e))
        sys.exit(1)
    if con is None:
        print('Error creating handle', str(e))
        sys.exit(1)
    return con


def close_db(handle=None):
    if handle:
        handle.close()


def query_db_translate_to_pandas(con, querystring):
    df = None
    try:
        cur = con.cursor()
        df = pd.read_sql(querystring, con)
    except Exception as e:
        con.rollback()
        print("Error in printing table: ", str(e))
    return df

### ------------- WARNING: Do not call unless you know what you're doing -------
def delete_table(con, tablename):
    try:
        cur = con.cursor()
        constr = "DROP TABLE "+tablename
        cur.execute(constr)
        con.commit()
    except Exception as e:
        con.rollback()
        print("Error deleting table: ", str(e))
    return

if __name__ == "__main__":
    con = get_db_handle()
    sp = SpotipyClient()
    pid = "4Q9SbpQm3REK3Ey3tZha3N"

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

    #do_the_due_tracks_table(sp, con)
    try_sql_query(sp, con)

    close_db(con)
