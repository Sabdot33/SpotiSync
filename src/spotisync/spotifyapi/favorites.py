import json
import logging
import os
from time import localtime, strftime

from ..core.config import read_create_config
from ..spotifyapi.download import download_and_save_mp3
from ..spotifyapi.spotipy import fetch_user_lib


def fetch_user_lib_and_save_all(debug=False):
    """
    Fetches the user's saved tracks from Spotify and saves the song data to a JSON file.
    Then, it downloads the audio files for each song and saves them to a specified path.

    Args:
        debug (bool, optional): If True, prints debug information. Defaults to False.

    Returns:
        bool: True if all songs were downloaded successfully, False otherwise.
    """

    config = read_create_config()
    dw_path = (config['settings']['download_path'])
    if not dw_path.endswith("/"):
        dw_path += "/"
    dw_path += "Favorites/"
    config = None

    fetch_user_lib()

    with open('song_data.json', 'r') as f:
        data = json.load(f)

    failed_items = []

    for item in data:
        try:
            download_and_save_mp3(item['spoti_id'], f"{item['name']}.mp3", path=dw_path, debug=debug)
        except Exception as e:
            if os.name == 'nt':
                pass
            else:
                logging.error(f"{item['name']}.mp3 (Error: {e})")
            if not str(e).startswith("File already exists"):
                failed_items.append(f"{item['name']}.mp3:  {e})")

    failed_items = failed_items[::-1]  # Reverse order for most recent track to be at the top

    try:
        os.remove('errors.log')
    except Exception as e:
        logging.error(f"Failed to remove errors.log: {e}")
    with open('errors.log', 'w') as log:
        if len(failed_items) > 0:
            logging.error(f"Failed to download {len(failed_items)} items")
            log.write(
                f"Failed to download {len(failed_items)} items:\n\nSong Name:  Error                                "
                f"                                                      This log is from " + strftime(
                    "%Y-%m-%d %H:%M:%S",
                    localtime()) + "\n--------------------------------------------------------------------------"
                                   "-----------------------------------------------------------------\n")
            # ^First 4 lines of errors.log^
            for item in failed_items:
                try:
                    logging.debug(f"- {item}")
                    log.write(f"- {item}\n")
                except Exception as e:
                    log.write(
                        f"Cloud not log error; python raised an exception: {e}\nSee "
                        f"https://github.com/ZSabiudj/SpotiSync/blob/main/README.md#bugs for more Information\n")
            logging.debug("Logged errors to errors.log")
        else:
            print("All songs downloaded successfully! Enjoy :3")
            return True
