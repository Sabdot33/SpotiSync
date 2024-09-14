from modules.config import read_create_config
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import logging
import json

def login_spotify(DEBUG=False):
    
    config = read_create_config()

    # Create Spotify object
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="user-library-read",
            client_id=config.get('spotipy', 'client_id'),
            client_secret=config.get('spotipy', 'client_secret'),
            redirect_uri=config.get('spotipy', 'redirect_uri')
            )
        )
    
    
    return sp

def fetch_user_lib(DEBUG):
    """
    Fetches the user's saved tracks from Spotify and saves the song data to a JSON file.

    Returns:
        None
    """
    sp = login_spotify()
    
    results = sp.current_user_saved_tracks(limit=50)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Extract song names and URLs (oldest first)
    song_data = []
    tracks = tracks[::-1]
    for item in tracks:
        track = item['track']
        song_data.append({
            'name': track['name'],
            'url': track['external_urls']['spotify'],
            'id': track['id']
        })
        
    json.dump(song_data, open('song_data.json', 'w'), indent=4)
    
    logging.debug("DEBUG: Song data extracted and saved to song_data.json")