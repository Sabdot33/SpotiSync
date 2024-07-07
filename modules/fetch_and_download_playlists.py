import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import json
import requests
import zipfile
from threading import Thread

def fetch_playlists(debug=False):
    """
    Fetches the user's saved playlists from Spotify and saves the playlist data to a JSON file.

    Args:
        debug (bool, optional): If True, prints debug information. Defaults to False.

    Returns:
        None
    """

    dbg = debug
    
    load_dotenv()

    # Get environment variables
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

    # Set up Spotify API authentication
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope="user-library-read"))

    # Fetch user's saved playlists
    results = sp.current_user_playlists(limit=50)
    playlists = results['items']

    # Fetch all pages of results
    while results['next']:
        results = sp.next(results)
        playlists.extend(results['items'])

    # Extract playlist names and URLs
    playlist_data = []
    playlists = playlists#[::-1]
    for playlist in playlists:
        images = playlist['images']
        if images:
            playlist_data.append({
                'name': playlist['name'],
                'url': playlist['external_urls']['spotify'],
                'id': playlist['id'],
                'image': images[0]['url']
            })
        else:
            playlist_data.append({
                'name': playlist['name'],
                'url': playlist['external_urls']['spotify'],
                'id': playlist['id'],
                'image': None
            })

    with open('playlist_data.json', 'w') as f:
        json.dump(playlist_data, f, indent=4)
        
def download_playlist(playlist_id, playlist_name, path, debug=False):
    """
    Downloads a playlist from a given URL and saves it to a specified path.

    Args:
        playlist_id (str): The ID of the playlist to download.
        playlist_name (str): The name of the playlist to download.
        path (str): The path where the playlist will be saved.
        debug (bool, optional): If True, prints debug information. Defaults to False.

    Raises:
        ValueError: If there is an error downloading the playlist or if the downloaded data is not a ZIP file.

    Returns:
        None
    """
    
    if not os.path.exists(path):
        os.makedirs(path)
        
    # Create the full path including filename and check if it already exists
    full_path = os.path.join(path, playlist_name) + "/"
    if os.path.exists(full_path):
        print("playlist already exists: " + full_path)
        print("Updating playlist")   
    if debug: print("DEBUG: Downloading playlist to " + full_path)
        
    url = f"https://yank.g3v.co.uk/playlist/{playlist_id}"
    hasfailed=False
    
    # download the playlist with requests and save the downloaded file to temp.zip
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-200 status codes
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error downloading zip file: {e}")
    # Check content type before saving
    if response.headers.get('content-type', '').lower == 'application/zip':
        raise ValueError("Downloaded data is not a ZIP file")

    # Save the file
    with open("temp.zip", "wb") as f:
        for chunk in response.iter_content(1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                
    # unzip temp.zip to DW_PATH + playlist_name
    if not hasfailed:
        if debug: print("DEBUG: Unzipping playlist")
        with zipfile.ZipFile("temp.zip", 'r') as zip_ref:
            zip_ref.extractall(full_path)
    
    # remove temp.zip
    if debug: print("DEBUG: Removing temp.zip")
    os.remove("temp.zip")
    if debug: print("DEBUG: Playlist downloaded to " + full_path)

def download_all_playlists(path, debug=False):
    """
    Downloads all playlists from a JSON file containing playlist data.

    Args:
        path (str): The path where the playlists will be downloaded.
        debug (bool, optional): If True, prints debug information. Defaults to False.

    Returns:
        None

    Raises:
        FileNotFoundError: If the playlist data file does not exist.
        ValueError: If there is an error downloading a playlist.

    This function reads playlist data from a JSON file named 'playlist_data.json' and downloads each playlist to the specified path.
    If the specified path does not exist, it is created.
    If there is an error downloading a playlist, an exception is raised and a message is printed.
    """
    
    dbg = debug
    
    if not os.path.exists(path):
        os.makedirs(path)
        if debug: print("DEBUG: Created download path " + path)
        
    with open('playlist_data.json', 'r') as f:
        playlist_data = json.load(f)
        
    for playlist in playlist_data:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        try:
            download_playlist(playlist_id, playlist_name, path, debug=dbg)
        except Exception as e:
            print(f"Error downloading playlist {playlist_name}: {e}")

if __name__ == "__main__":
    fetch_playlists()
    
    download_all = input("Download all playlists? (y/n): ")
    if download_all == "n":
        playlist_id = input("Enter the playlist ID: ")
        playlist_name = input("Enter the playlist name: ")
        path = input("Enter the download path: ") or "."
        download_playlist(playlist_id, playlist_name, path)
    elif download_all == "y":
        path = input("Enter the download path: ") or "."
        download_all_playlists(path)