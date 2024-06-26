import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from download import download_and_save_mp3
import os
import sys
import json

def fetch_user_lib_and_save_all(debug=False):
    
    dbg = debug
    
    # Load environment variables from .env file
    load_dotenv()

    # Get environment variables
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
    DW_PATH = os.getenv('DOWNLOAD_PATH')

    # Set up Spotify API authentication
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope="user-library-read"))

    # Fetch user's saved tracks
    results = sp.current_user_saved_tracks(limit=50)
    tracks = results['items']

    # Fetch all pages of results
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Extract song names and URLs
    song_data = []
    for item in tracks:
        track = item['track']
        song_data.append({
            'name': track['name'],
            'url': track['external_urls']['spotify'],
            'id': track['id']
        })

    # Save song data to a JSON file
    with open('song_data.json', 'w') as f:
        json.dump(song_data, f, indent=4)

    print("Song data extracted and saved to song_data.json")

    with open('song_data.json', 'r') as f:
        data = json.load(f)

    failed_items = []

    for item in data:
        try:
            download_and_save_mp3(item['id'], f"{item['name']}.mp3", path=DW_PATH, debug=dbg)
        except Exception as e:
            # dont print if os is windows
            if os.name == 'nt':
                pass
            else:
                print(f"{item['name']}.mp3 (Error: {e})")
            # log every error except "file already exists"
            if not str(e).startswith("File already exists"):
                failed_items.append(f"{item['name']}.mp3:  {e})")

    if os.path.exists('errors.log'):
        os.remove('errors.log')
    with open('errors.log', 'w') as log:
        if len(failed_items) > 0:
            print(f"Failed to download {len(failed_items)} items")
            log.write(f"Failed to download {len(failed_items)} items:\n\nSong Name:  Error\n------------------------------------------------------------------------------------------------------------------------------------------\n")
            # ^First 4 lines of errors.log^
            for item in failed_items:
                try:
                    if debug: print(f"\t- {item}")
                    log.write(f"- {item}\n")
                except Exception as e:
                    log.write(f"Cloud not log error; python raised an exception: {e}\nSee https://github.com/ZSabiudj/SpotiSync/blob/main/README.md#bugs for more Information\n")
            if debug: print("DEBUG: Logged errors to errors.log")
        else:
            print("All songs downloaded successfully! Enjoy :3")
            return True
        
if __name__ == "__main__":
    fetch_user_lib_and_save_all()