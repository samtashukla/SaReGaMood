import sys
import pygn
from defs import pldesc, trdesc, SpotipyClient
from defs import make_trdesc
import time
from collections import defaultdict

# Spotify I/O: Convert all the playlists of a user to a list of playlist descriptors
# (pldesc stands for playlist descriptor which is a namedtuple in defs)
# It takes the user's spotify handle as input
def get_user_playlist_descriptor_list(sp):
    playlists = sp.client.user_playlists(sp.user)
    plist = []
    while playlists: # loop to parse the list of playlists
        for i, playlist in enumerate(playlists['items']):
            plid = playlist['id']
            plname = playlist['name']
            pluri = playlist['uri']
            plurl = playlist['external_urls']['spotify']
            pl = pldesc(name=plname, uri=pluri, id=plid, url=plurl) 
            plist.append(pl)
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    return plist



# Spotify I/O: Function to get all tracks containing in a playlist.
# Inputs are user's spotify handle, playlist id and maximum number of tracks to be fetched
# It returns the list of track descriptors.
# This function processes data in chunks since spotify does not allow all the tracks to
# be fetched in one go. Between the chunks, we sleep for five seconds to avoid sending a huge
# burst to spotify (which may result in the request getting denied).
def get_playlist_tracks(sp, pid, maxitems=200000):
    offset = 0
    step = 100
    tracklist = []
    counter = 0
    goahead = True

    while goahead:

        # get the next chunk of tracks, starting from offset. Break if something goes wrong
        # in fetching the next chunk
        try: 
            newtracks = sp.client.user_playlist_tracks(sp.user, playlist_id=pid, limit=step, offset=offset)
        except Exception as e: 
            print("user_playlist_tracks stopped at offset = ", offset);
            print("Exception = ", str(e));
            break

        # Continue processing if the new chunk does not contain any tracks under expected key
        if not newtracks['items']:
            goahead = False
            continue

        # Now process each record in the newly fetched chunk and obtain track descriptor from each record.
        # Keep appending each track descriptor to tracklist. Throw an exception if something fails.
        try:
            for item in newtracks['items']: # look over each record in newly fetched chunk
                td = get_track_descriptor(item["track"]) # make a track descriptor from record
                if td is None:
                    continue
                tracklist.append(td) # append track descriptor to tracklist
                print(str(td).encode('utf-8')) # tell the user we have processed the record
                counter += 1
                if counter > maxitems: # stop processing if we are done with max number of tracks asked for
                    goahead = False
                    break
        except Exception as e:
            print("get_playlist_tracks stopped at offset = ", offset);
            print("Exception = ", str(e));
            goahead = False

        offset += step # increase offset for the nre chunk
        time.sleep(5) # this is so that we don't send a huge burst to spotify

    return tracklist


# Spotify I/O: Function to get "audio features" for a list of track ids.
# These features are like tempo, instrumentalness, etc.
# Note that these features are different from informative features in a track descriptor,
# (which mainly corresponds to track name, track id, artist name, etc.)
# It takes user's spotify handle and a row of pandas dataframe as input.
def get_spotify_feature_info(sp, row):
    time.sleep(0.1)
    sp_features = sp.sotify.audio_features(row['id'])
    return sp_features


# Spotify I/O: Utility to create a private playlist in spotify on a user's behalf
# It takes as input user's spotify handle and playlist name
def add_playlist(sp, plname):
    sp.spotify.user_playlist_create(sp.user, plname, public=False)


# Spotify I/O: Utility to add tracks to a playlist (specified by id).
# tracks are specified in the form of a list of track ids
# For input, sp denotes a user's spotify handle
def add_tracks_to_playlist_id(sp, playlist_id, tracklist):
    chunksize = 50
    numtracks = len(tracklist)
    for offset in [i for i in range(0, numtracks, chunksize)]:
        listslice = tracklist[offset:offset+chunksize]
        results = sp.spotify.user_playlist_add_tracks(sp.user, playlist_id, listslice)
        print(results)
        time.sleep(5)


# Gracenote I/O: Function to get multiple items within Gracenote record
def get_gn_multiple(search, dictionary, item):
    for k, v in search[item].items():
        dictionary[item + '_' + k] = v['TEXT']


# Gracenote I/O: gets artist and track info from gracenote
# It takes input as gracenote client id, gracenote user id, track name and artist name
def get_gn(clientid, userid, track, artist):
    time.sleep(0.1) # sleep so that we don't send a huge burst to gracenote
    gn_dict = defaultdict(list)
    gn_info = pygn.search(clientid, userid, artist=artist, track=track)
    if gn_info is None:
        print("Error: got gn_info = None")
        return None
    gn_dict['gnid'] = gn_info['track_gnid']
    # track specific info
    for s in ['genre', 'mood', 'tempo']:
        get_gn_multiple(gn_info, gn_dict, s)      
    return dict(gn_dict)


# Greacenote I/O: Function which calls get_gn above
# It needs user's gracenote client, track name and artist name as input
# (We don't need sp_id as input any more, needs to be eliminated).
def get_gracenote_feature_info(gn, sp_id, sp_name, sp_artist):
    clientid = gn.clientid
    userid = gn.userid
    gn_features = get_gn(clientid, userid, sp_name, sp_artist)
    return gn_features


# Utility to test whether a word is composed of whitespaces.
# Useful when we are parsing the file of list of ragas (or scales in Indian Classical Music)
def testword(word):
    if not word:
        return False
    if word.isspace():
        return False
    return True

# Get keywords from the file of "ragas"
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


# Quotes in tracknames causes issues in getting/storing in database
# The following function converts single quotes to double quotes in a given string
def stodq(s):
    return s.replace("'", "''")


# Convert a dictionary of key, val pairs of a track (where features are keys)
# to a track descriptor (which is a namedtuple in defs.py)
def get_track_descriptor(trackdict):
    return make_trdesc(trackdict) # defined in defs

