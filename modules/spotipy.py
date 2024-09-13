from modules.config import read_create_config
import spotipy
from spotipy.oauth2 import SpotifyOAuth

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