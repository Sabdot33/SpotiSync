import spotipy
import os
from spotipy import SpotifyOAuth
import json
from threading import Thread
from .download import download_and_save_mp3

def login_spotify(debug=False):
    
    # Get environment variables
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope="user-library-read"))
    return sp

def search_artist(artist_name, debug=False):
    
    if artist_name is None:
        raise ValueError("Artist name cannot be None")
    
    sp = login_spotify(debug)
    
    results = sp.search(q='artist:' + artist_name, type='artist', limit=4)
    items = results['artists']['items']

    if len(items) == 0:
        if debug: print("No artist found")
        return False
    
    artist_data = []
    for item in items:
        artist = item
        if artist['images']:
            artist_data.append({
                'name': artist['name'],
                'image': artist['images'][0]['url'],
                'id': artist['id']
            })
    
    with open('artist_data.json', 'w') as f:
        json.dump(artist_data, f, indent=4)
        
    return True

def get_and_download_artist_albums_and_respective_tracks(artist_id, path='./', debug=False):
    
    if artist_id is None:
        raise ValueError("Artist id cannot be None")
    
    sp = login_spotify(debug)
    
    results = sp.artist_albums(artist_id)
    
    artist_name = results['items'][0]['artists'][0]['name']
    print(artist_name)
    
    items = results['items']

    album_data = []
    for item in items:
        album = item
        if album['images']:
            album_name = album['name']
            album_data.append({
                'album_name': album_name,
            })
            tracks = sp.album_tracks(album['id'])
            track_data = []
            for track in tracks['items']:
                track_data.append({
                    'track_name': track['name'],
                    'track_id': track['id']
                })
            album_data[-1]['tracks'] = track_data

    with open('albums_and_tracks.json', 'w') as f:
        json.dump(album_data, f, indent=4)
        
    for album in album_data:
        album_name = album['album_name']
        tracks = album['tracks']
        album_path = path + artist_name + '/' + album_name
        os.makedirs(album_path, exist_ok=True)
        for track in tracks:
            track_name = track['track_name']
            track_id = track['track_id']
            try:
                download_and_save_mp3(track_id, track_name, album_path, debug=debug)
            except Exception as e:
                if debug: print(f"Error downloading {track_name}: {e}")
                
def get_and_download_artist_albums_and_respective_tracks_thread(artist_id, path='./', debug=False):
    
    thread = Thread(target=get_and_download_artist_albums_and_respective_tracks, args=(artist_id, path, debug)) 
    thread.start()

if __name__ == "__main__":
    input1 = input("Enter artist name to search for: ")
    search_artist(input1)
    
    with open('artist.json', 'r') as f:
        print(f.read())
    
    input2 = input("Artist ID to download: ")
    path = input("Download path (optional, defaults to current directory): ") or "."
    if not path.endswith("/"):
        path += "/"
    
    get_and_download_artist_albums_and_respective_tracks(input2, path)
    