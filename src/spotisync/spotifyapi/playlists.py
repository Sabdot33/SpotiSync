import io
import json
import logging
import os
import zipfile
from io import BytesIO

import requests
from PIL import Image

from .spotipy import login_spotify


def fetch_playlists():
    """
    Fetches the user's saved playlists from Spotify and saves the playlist data to a JSON file.

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
    playlists = playlists  # [::-1]

    if not os.path.exists(os.path.join("cache")):
        os.makedirs(os.path.join("cache"))

    for playlist in playlists:
        images = playlist['images']

        if images:# save image in cache folder
            if os.path.exists(os.path.join("cache", playlist["id"] + ".jpg")):
                logging.debug("Image already exists in cache")
                pass
            else:
                image_url = images[0]['url']
                response = requests.get(image_url)
                pi_limage = Image.open(BytesIO(response.content))
                pi_limage = pi_limage.resize((128, 128))
                pi_limage.save(os.path.join("cache", playlist["id"] + ".jpg"))
                logging.debug("Image saved in cache")

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

    try:
        w = io.StringIO()

        json.dump(playlist_data, w)
        content = w.getvalue()

        with open("playlist_data.json", "w") as f:
            f.write(content)

        w.close()
    except (IOError, OSError) as e:
        logging.error(f"An error occurred while writing to the file: {e}")
    except TypeError as e:
        logging.error(f"An error occurred: The playlist_data is not JSON serializable: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def download_playlist(playlist_id: str, path: str = "."):
    # get playlist name with ID:
    def get_playlist_name(playlist_id_to_lookup):
        sp = login_spotify()
        return sp.playlist(str(playlist_id_to_lookup))['name']

    playlist_name = get_playlist_name(playlist_id)

    path = os.path.join(path, "Playlists")

    logging.debug(f"debug: path: {path} playlist_id: {playlist_id} playlist_name: {playlist_name}")

    if not os.path.exists(path):
        os.makedirs(path)

    # Create the full path including filename and check if it already exists
    full_path = os.path.join(path, playlist_name)
    if os.path.exists(full_path):
        logging.debug("playlist already exists: " + full_path)
        logging.info("Updating playlist")
    logging.debug("Downloading playlist to " + full_path)

    url = f"https://yank.g3v.co.uk/playlist/{playlist_id}"
    hasfailed = False

    # download the playlist with requests and save the downloaded file to temp.zip
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-200 status codes
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error downloading zip file: {e}")
    if response.headers.get('Content-Type', '').lower == 'application/zip':
        raise ValueError("Downloaded data is not a ZIP file")

    # Save the file
    with open("temp.zip", "wb") as f:
        for chunk in response.iter_content(1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

    # unzip temp.zip to DW_PATH + playlist_name
    if not hasfailed:
        logging.debug("debug: Unzipping playlist")
        with zipfile.ZipFile("temp.zip", 'r') as zip_ref:
            zip_ref.extractall(full_path)

    # remove temp.zip
    logging.debug("debug: Removing temp.zip")
    os.remove("temp.zip")
    logging.debug("debug: Playlist downloaded to " + full_path)


def download_all_playlists(path):
    """
    Downloads all playlists from a JSON file containing playlist data.

    Args:
        path (str): The path where the playlists will be downloaded.

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
        logging.debug("debug: Created download path " + path)

    with open('playlist_data.json', 'r') as f:
        playlist_data = json.load(f)

    for playlist in playlist_data:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        try:
            download_playlist(playlist_id, path + playlist_name + "/")
        except Exception as e:
            logging.error(f"Error downloading playlist {playlist_name}: {e}")
