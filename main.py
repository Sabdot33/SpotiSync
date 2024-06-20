import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

# Spotify API credentials from environment variables
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

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