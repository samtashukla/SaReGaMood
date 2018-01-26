import sys
import pygn
from defs import pldesc, trdesc, SpotipyClient
from defs import make_trdesc
import time
from collections import defaultdict

def stodq(s):
    return s.replace("'", "''")


def add_playlist_tracks_to_db(plid, plname):
    print("Processing playlist = plname (", plid, ")")
    return


def get_user_playlist_descriptor_list(sp):
    playlists = sp.client.user_playlists(sp.user)
    plist = []
    while playlists:
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


def get_track_descriptor(trackdict):
    return make_trdesc(trackdict)


def get_playlist_tracks(sp, pid, maxitems=200000):
    offset = 0
    step = 100
    tracklist = []
    counter = 0
    goahead = True
    while goahead:
        try:
            newtracks = sp.client.user_playlist_tracks(sp.user, playlist_id=pid, limit=step, offset=offset)
        except Exception as e:
            print("user_playlist_tracks stopped at offset = ", offset);
            print("Exception = ", str(e));
            break
        if not newtracks['items']:
            goahead = False
            continue
        try:
            for item in newtracks['items']:
                td = get_track_descriptor(item["track"])
                if td is None:
                    continue
                tracklist.append(td)
                print(str(td).encode('utf-8'))
                counter += 1
                if counter > maxitems:
                    goahead = False
                    break
        except Exception as e:
            print("get_playlist_tracks stopped at offset = ", offset);
            print("Exception = ", str(e));
            goahead = False
        offset += step
        time.sleep(5)
    return tracklist

# =======Get features from spotify============

def complete_sp_audio_features(sp, stuff):
    features_list = []
    features_add = sp.spotify.audio_features(tracks=stuff)
    features_list.extend(features_add)
    return features_list

def get_spotify_feature_info(sp, row):
    time.sleep(0.1)
    sp_features = complete_sp_audio_features(sp, row['id'])
    return sp_features

#============================================


# =======Get features from gracenote=========

def get_gn_multiple(search, dictionary, item):
    '''
    Helper function to get multiple items within Gracenote record
    '''
    for k, v in search[item].items():
        dictionary[item + '_' + k] = v['TEXT']

def get_gn(clientid, userid, track, artist):
    '''
    Gets artist and track information from Gracenote
    '''
    time.sleep(0.1)
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

def get_gracenote_feature_info(gn, sp_id, sp_name, sp_artist):
    clientid = gn.clientid
    userid = gn.userid
    gn_features = get_gn(clientid, userid, sp_name, sp_artist)
    return gn_features

#===========================================


if __name__ == "__main__":
    #sp = SpotipyClient()
    #pl = get_user_playlist_descriptor_list(sp)
    #for desc in pl:
    #    print(desc)
    #    get_playlist_tracks(sp, desc.id)
    #    break
    #pid="4Q9SbpQm3REK3Ey3tZha3N"
    #tl = get_playlist_tracks(sp, pid)
    sys.exit()
