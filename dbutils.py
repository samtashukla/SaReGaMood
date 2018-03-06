import sys
import psycopg2
import utils
from defs import SpotipyClient
import pandas as pd
import pandas.io.sql as psql
from utils import stodq
import re
import time

# Get handle on the database using psycopg
# Arguments: dbname is database name and rolename is rolename of a user
# Note that it needs a password entered manually
def get_db_handle(dbname="testdb", rolename="spotify"):
    con = None
    password = passwd
    constr = "host='localhost' dbname='"+dbname+"'  user='"+rolename+"' password='"+passwd+"'"
    try:
        con = psycopg2.connect(constr)
    except Exception as e:
        if con:
            con.rollback()  # rollback the connection before throwing an exception
        print('Error creating or connecting handle', str(e))
        sys.exit(1)
    if con is None: # make sure that con is not None, exit if it is None
        print('Error creating handle', str(e))
        sys.exit(1)
    return con


# Close database handle
def close_db(handle=None):
    if handle:
        handle.close()

# Function to query a database and convert the answer to pandas dataframe
# Takes arguments as database handle and query string
def query_db_translate_to_pandas(con, querystring):
    df = None
    try:
        cur = con.cursor()
        df = pd.read_sql(querystring, con)
    except Exception as e:
        con.rollback() # rollback handle if failed
        print("Error in printing table: ", str(e))
    return df

### WARNING: Do not call delete_table unless you know what you're doing
# Function to delete table. Takes arguments of database handle and table name
# We put it isolated here to underscore that it should be used sparingly.
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

# Demo: mail executes only if this file is executed standalone
# *** Note that you will need to enter your spotify credentials in defs.py ***
if __name__ == "__main__":

    print("Note that this file won't execute successfully until you enter your")
    print("spotify/gracenote credentials in defs and database password in get_db_handle")
    con = get_db_handle() # default arguments handle database name and rolename
    sp = SpotipyClient()
    pid = "4Q9SbpQm3REK3Ey3tZha3N" # Sample public playlist id

    try_sql_query(sp, con)
    close_db(con)
