import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from .download import download_and_save_mp3
import os
import json
import time

def fetch_user_lib_and_save_all(DEBUG=False):
    """
    Fetches the user's saved tracks from Spotify and saves the song data to a JSON file.
    Then, it downloads the audio files for each song and saves them to a specified path.
    
    Args:
        DEBUG (bool, optional): If True, prints DEBUG information. Defaults to False.
    
    Returns:
        bool: True if all songs were downloaded successfully, False otherwise.
    """
    
    dbg = DEBUG
    
    load_dotenv()

    # Get environment variables
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
    DW_PATH = os.getenv('DOWNLOAD_PATH_MUSIC') + "Favorites/"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope="user-library-read"))

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

    with open('song_data.json', 'w') as f:
        json.dump(song_data, f, indent=4)

    if DEBUG: print("DEBUG: Song data extracted and saved to song_data.json")

    with open('song_data.json', 'r') as f:
        data = json.load(f)

    failed_items = []

    for item in data:
        try:
            download_and_save_mp3(item['id'], f"{item['name']}.mp3", path=DW_PATH, DEBUG=dbg)
        except Exception as e:
            if os.name == 'nt':
                pass
            else:
                if DEBUG: print(f"DEBUG: {item['name']}.mp3 (Error: {e})")
            if not str(e).startswith("File already exists"):
                failed_items.append(f"{item['name']}.mp3:  {e})")
                
    failed_items = failed_items[::-1] # Reverse order for most recent track to be at the top

    try:
        os.remove('errors.log')
    except Exception as e:
        if DEBUG: print(f"DEBUG: {e}")
    with open('errors.log', 'w') as log:
        if len(failed_items) > 0:
            print(f"Failed to download {len(failed_items)} items")
            log.write(f"Failed to download {len(failed_items)} items:\n\nSong Name:  Error                                                                                      This log is from " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n-------------------------------------------------------------------------------------------------------------------------------------------\n")
            # ^First 4 lines of errors.log^
            for item in failed_items:
                try:
                    if DEBUG: print(f"- {item}")
                    log.write(f"- {item}\n")
                except Exception as e:
                    log.write(f"Cloud not log error; python raised an exception: {e}\nSee https://github.com/ZSabiudj/SpotiSync/blob/main/README.md#bugs for more Information\n")
            if DEBUG: print("DEBUG: Logged errors to errors.log")
        else:
            print("All songs downloaded successfully! Enjoy :3")
            return True
        
if __name__ == "__main__":
    fetch_user_lib_and_save_all()