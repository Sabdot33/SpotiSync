import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from download import download_and_save_mp3
import os
import json

def fetch_user_lib_and_save_all(debug=False):
    

    # Load environment variables from .env file
    load_dotenv()

    # Get environment variables
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
    DW_PATH = "./downloads"

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

    failed_items = []  # Use a list to store failed items

    for item in data:
        try:
            # Call the download function with the song data
            download_and_save_mp3(item['id'], f"{item['name']}.mp3", path=DW_PATH)
        except Exception as e:  # Catch any exception from the download function
            print(f"{item['name']}.mp3 (Error: {e})")
            failed_items.append(f"{item['name']}.mp3 (Error: {e})")  # Log failed item with error details

    if len(failed_items) > 0:
        print(f"Failed to download {len(failed_items)} items:")
        for item in failed_items:
            print(f"\t- {item}")
    else:
        print("All songs downloaded successfully! Enjoy :3")
        return True
        
if __name__ == "__main__":
    fetch_user_lib_and_save_all()