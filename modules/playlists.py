from modules.spotipy import login_spotify
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image
from io import BytesIO
import logging
import zipfile
import requests
import os
import json

def fetch_playlists(DEBUG=False):
    """
    Fetches the user's saved playlists from Spotify and saves the playlist data to a JSON file.

    Args:
        DEBUG (bool, optional): If True, prints DEBUG information. Defaults to False.

    Returns:
        None
    """
    
    sp = login_spotify()
    
    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results['items']:
        playlists.extend(results['items'])
        if results['next']:
            results = sp.next(results)
        else:
            break

    # Extract playlist names and URLs
    playlist_data = []
    playlists = playlists#[::-1]
    for playlist in playlists:
        images = playlist['images']
        
        # save image in cache folder
        if os.path.exists(f"assets/cache/" + playlist["id"] + ".jpg"):
            logging.debug("Image already exists in cache")
            pass
        else:
            if images:
                image_url = images[0]['url']
                response = requests.get(image_url)
                PILimage = Image.open(BytesIO(response.content))
                PILimage = PILimage.resize((128, 128))
                if not os.path.exists('./assets/cache/'):
                    os.makedirs('./assets/cache/')
                PILimage.save(f'./assets/cache/{playlist["id"]}.jpg')
                if DEBUG: print("Image saved in cache")
        
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
        
def download_playlist(playlist_id, path=os.getenv('DOWNLOAD_PATH_MUSIC'), DEBUG=False):
    
    # get playlist name with ID:
    def get_playlist_name(playlist_id, DEBUG=False):
        sp = login_spotify(DEBUG)
        return sp.playlist(str(playlist_id))['name']
    
    playlist_name = get_playlist_name(playlist_id, DEBUG)
    
    if DEBUG: print(f"DEBUG: path: {path} playlist_id: {playlist_id} playlist_name: {playlist_name}")
    
    if not path.endswith("/"):
        path += "/"
        if DEBUG: print("DEBUG: Added '/' to path: " + path)
    
    if not os.path.exists(path):
        os.makedirs(path)
        
    # Create the full path including filename and check if it already exists
    full_path = path + playlist_name + "/"
    if os.path.exists(full_path):
        print("playlist already exists: " + full_path)
        print("Updating playlist")   
    if DEBUG: print("DEBUG: Downloading playlist to " + full_path)
        
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
        if DEBUG: print("DEBUG: Unzipping playlist")
        with zipfile.ZipFile("temp.zip", 'r') as zip_ref:
            zip_ref.extractall(full_path)
    
    # remove temp.zip
    if DEBUG: print("DEBUG: Removing temp.zip")
    os.remove("temp.zip")
    if DEBUG: print("DEBUG: Playlist downloaded to " + full_path)

def download_all_playlists(path, DEBUG=False):
    """
    Downloads all playlists from a JSON file containing playlist data.

    Args:
        path (str): The path where the playlists will be downloaded.
        DEBUG (bool, optional): If True, prints DEBUG information. Defaults to False.

    Returns:
        None

    Raises:
        FileNotFoundError: If the playlist data file does not exist.
        ValueError: If there is an error downloading a playlist.

    This function reads playlist data from a JSON file named 'playlist_data.json' and downloads each playlist to the specified path.
    If the specified path does not exist, it is created.
    If there is an error downloading a playlist, an exception is raised and a message is printed.
    """
    
    if not os.path.exists(path):
        os.makedirs(path)
        if DEBUG: print("DEBUG: Created download path " + path)
        
    with open('playlist_data.json', 'r') as f:
        playlist_data = json.load(f)
        
    for playlist in playlist_data:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        try:
            download_playlist(playlist_id, path + playlist_name + "/", DEBUG)
        except Exception as e:
            print(f"Error downloading playlist {playlist_name}: {e}")