import json
import logging
import os
import threading
from logging import Logger
from time import localtime, strftime

from ..core.config import read_create_config
from ..spotifyapi.download import download_and_save_mp3
from ..spotifyapi.spotipy import fetch_user_lib

# Import logging configuration from core module
from ..core.logger import setup_logging

# Setup logging for this module
logger = setup_logging(__name__)


def fetch_user_lib_and_save_all():
    """
    Fetches the user's saved tracks from Spotify and saves the song data to a JSON file.
    Then, it downloads the audio files for each song and saves them to a specified path.

    Returns:
        bool: True if all songs were downloaded successfully, False otherwise.
    """

    logging.info("Starting to fetch and save user library")
    config = read_create_config()
    dw_path = config['settings']['download_path']
    dw_path = os.path.join(dw_path, "Favorites")
    dw_path = os.path.normpath(dw_path)
    logging.debug(f"Download path set to: {dw_path}")

    # Validate download path before creating directories
    try:
        parent_dir = os.path.dirname(dw_path)
        if not os.path.exists(parent_dir):
            logging.error(f"Parent directory does not exist: {parent_dir}")
            raise PermissionError(f"Parent directory does not exist: {parent_dir}")
        
        test_file = os.path.join(parent_dir, '.write_test')
        try:
            with open(test_file, 'w') as f:
                f.write('')
            os.remove(test_file)
            logging.debug(f"Write permission verified for: {parent_dir}")
        except (IOError, OSError) as e:
            logging.error(f"No write permission in directory: {parent_dir}")
            raise PermissionError(f"No write permission in directory: {parent_dir}")
            
        os.makedirs(dw_path, exist_ok=True)
        logging.info(f"Created download directory: {dw_path}")
    except PermissionError as e:
        logging.error(f"Permission error: {e}")
        return False
    except Exception as e:
        logging.error(f"Failed to create download directory: {e}")
        return False

    try:
        logging.info("Fetching user library...")
        fetch_user_lib()
    except Exception as e:
        logging.error(f"Failed to fetch user library: {e}")
        return False

    try:
        logging.debug("Reading song data from JSON file")
        with open('song_data.json', 'r') as f:
            data = json.load(f)
        logging.info(f"Found {len(data)} songs in library")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Failed to read song data: {e}")
        return False

    failed_items = []

    def download_track_thread(track_id, track_name):
        try:
            logging.debug(f"Starting download for track: {track_name}")
            download_and_save_mp3(track_id, f"{track_name}.mp3", path=dw_path, skip=True)
            logging.debug(f"Successfully downloaded: {track_name}")
        except Exception as e:
            error_msg = f"{track_name}.mp3 (Error: {e})"
            if not os.name == 'nt':
                logging.error(error_msg)
            if not str(e).startswith("File already exists"):
                failed_items.append(error_msg)
                logging.error(f"Failed to download {track_name}: {e}")

    threads = []
    logging.info("Starting download threads")
    for item in data:
        thread = threading.Thread(
            target=download_track_thread,
            args=(item['id'], item['name']),
            daemon=True
        )
        threads.append(thread)
        thread.start()

    logging.debug("Waiting for all download threads to complete")
    for thread in threads:
        thread.join()

    failed_items = failed_items[::-1]

    try:
        if os.path.exists('errors.log'):
            logging.debug("Removing existing errors.log")
            os.remove('errors.log')
    except Exception as e:
        logging.error(f"Failed to remove errors.log: {e}")

    try:
        with open('errors.log', 'w', encoding='utf-8') as log:
            if failed_items:
                error_count = len(failed_items)
                logging.error(f"Failed to download {error_count} items")
                log.write(
                    f"Failed to download {error_count} items:\n\nSong Name:  Error                                "
                    f"                                                      This log is from {strftime('%Y-%m-%d %H:%M:%S', localtime())}\n"
                    f"-" * 120 + "\n")
                for item in failed_items:
                    try:
                        logging.error(f"- {item}")
                        log.write(f"- {item}\n")
                    except UnicodeEncodeError as e:
                        error_msg = (f"Could not log error; python raised an exception: {e}\nSee "
                                   f"https://github.com/Sabdot33/SpotiSync/blob/main/README.md#bugs for more information")
                        log.write(error_msg)
                        logging.error(error_msg)
                logging.info("Logged errors to errors.log")
                return False
            else:
                logging.info("All songs downloaded successfully!")
                return True
    except Exception as e:
        logging.error(f"Failed to write to errors.log: {e}")
        return False
