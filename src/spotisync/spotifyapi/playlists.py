import io
import json
import logging
import os
import zipfile
from io import BytesIO
import threading

import requests
from PIL import Image

from .spotipy import login_spotify

# Import logging configuration from core module
from ..core.logger import setup_logging

# Setup logging for this module
logger = setup_logging(__name__)

def fetch_playlists():
    logging.info("Starting to fetch user playlists")
    sp = login_spotify()
    logging.debug("Successfully logged in to Spotify")

    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results['items']:
        playlists.extend(results['items'])
        if results['next']:
            results = sp.next(results)
            logging.debug(f"Fetched next page of playlists, total count: {len(playlists)}")
        else:
            break

    logging.info(f"Found {len(playlists)} playlists")
    playlist_data = []

    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        logging.debug(f"Created cache directory: {cache_dir}")

    for playlist in playlists:
        images = playlist['images']
        playlist_name = playlist['name']
        logging.debug(f"Processing playlist: {playlist_name}")

        if images:
            cache_path = os.path.join(cache_dir, playlist["id"] + ".jpg")
            if os.path.exists(cache_path):
                logging.debug(f"Image already exists in cache for playlist: {playlist_name}")
            else:
                try:
                    image_url = images[0]['url']
                    response = requests.get(image_url)
                    response.raise_for_status()
                    pi_limage = Image.open(BytesIO(response.content))
                    pi_limage = pi_limage.resize((128, 128))
                    pi_limage.save(cache_path)
                    logging.debug(f"Saved image in cache for playlist: {playlist_name}")
                except Exception as e:
                    logging.error(f"Failed to save image for playlist {playlist_name}: {e}")

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
        logging.debug("Saving playlist data to JSON file")
        w = io.StringIO()
        json.dump(playlist_data, w)
        content = w.getvalue()

        with open("playlist_data.json", "w") as f:
            f.write(content)

        w.close()
        logging.info("Successfully saved playlist data to JSON file")

    except (IOError, OSError) as e:
        logging.error(f"An error occurred while writing to the file: {e}")
    except TypeError as e:
        logging.error(f"An error occurred: The playlist_data is not JSON serializable: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def download_playlist(playlist_id: str, path: str = "."):
    logging.info(f"Starting to download playlist: {playlist_id}")
    
    def get_playlist_name(playlist_id_to_lookup):
        sp = login_spotify()
        return sp.playlist(str(playlist_id_to_lookup))['name']

    try:
        playlist_name = get_playlist_name(playlist_id)
        logging.debug(f"Retrieved playlist name: {playlist_name}")
    except Exception as e:
        logging.error(f"Failed to get playlist name: {e}")
        raise

    path = os.path.join(path, "Playlists")
    logging.debug(f"Download path set to: {path}")

    if not os.path.exists(path):
        os.makedirs(path)
        logging.debug(f"Created download directory: {path}")

    full_path = os.path.join(path, playlist_name)
    if os.path.exists(full_path):
        logging.info(f"Playlist already exists at: {full_path}")
        logging.info("Updating playlist")

    try:
        sp = login_spotify()
        playlist = sp.playlist(playlist_id)
        tracks = playlist['tracks']
        track_items = tracks['items']

        while tracks['next']:
            tracks = sp.next(tracks)
            track_items.extend(tracks['items'])

        logging.info(f"Found {len(track_items)} tracks in playlist")

        def download_track_thread(track_item, track_path):
            try:
                track = track_item['track']
                track_name = track['name']
                track_id = track['id']
                logging.debug(f"Starting download for track: {track_name}")
                download_and_save_mp3(track_id, f"{track_name}.mp3", track_path, skip=True)
                logging.debug(f"Successfully downloaded: {track_name}")
            except Exception as e:
                logging.error(f"Error downloading track {track_name}: {e}")

        threads = []
        for track_item in track_items:
            thread = threading.Thread(
                target=download_track_thread,
                args=(track_item, full_path),
                daemon=True
            )
            threads.append(thread)
            thread.start()

        logging.debug("Waiting for all download threads to complete")
        for thread in threads:
            thread.join()

        logging.info(f"Successfully downloaded playlist to: {full_path}")


    except requests.exceptions.Timeout:
        logging.error(f"Request timed out after {timeout} seconds")
        raise
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download playlist: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise

def download_all_playlists(path):
    logging.info(f"Starting to download all playlists to: {path}")

    if not os.path.exists(path):
        os.makedirs(path)
        logging.debug(f"Created download path: {path}")

    try:
        with open('playlist_data.json', 'r') as f:
            playlist_data = json.load(f)
        logging.info(f"Found {len(playlist_data)} playlists to download")
    except FileNotFoundError:
        logging.error("playlist_data.json not found")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in playlist_data.json: {e}")
        raise

    def download_playlist_thread(playlist_id, playlist_path):
        try:
            download_playlist(playlist_id, playlist_path)
        except Exception as e:
            logging.error(f"Error downloading playlist: {e}")
    
    threads = []
    for playlist in playlist_data:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        logging.debug(f"Creating download thread for playlist: {playlist_name}")
        
        thread = threading.Thread(
            target=download_playlist_thread,
            args=(playlist_id, path + playlist_name + "/"),
            daemon=True
        )
        threads.append(thread)
        thread.start()
    
    logging.debug("Waiting for all download threads to complete")
    for thread in threads:
        thread.join()
    
    logging.info("All playlists download completed")
