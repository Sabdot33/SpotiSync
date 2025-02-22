import io
import json
import logging
import os
import threading

from .download import download_and_save_mp3
from .spotipy import login_spotify

# Import logging configuration from core module
from ..core.logger import setup_logging

# Setup logging for this module
logger = setup_logging(__name__)

def download_artist(artist_id: str, path: str = '.'):
    logging.info(f"Starting to download artist with ID: {artist_id}")
    if artist_id is None:
        logging.error("artist_id cannot be None")
        raise ValueError("artist_id cannot be None")

    sp = login_spotify()
    logging.debug("Successfully logged in to Spotify")

    results = sp.artist_albums(artist_id)
    logging.debug(f"Retrieved {len(results['items'])} albums for artist")

    try:
        artist_name = results['items'][0]['artists'][0]['name']
        logging.info(f"Processing albums for: {artist_name}")
    except (IndexError, KeyError) as e:
        logging.error(f"Could not get artist name: {e}")
        raise ValueError(f"Could not get artist name: {e}")

    items = results['items']
    album_data = []

    for item in items:
        album = item
        if album['images']:
            album_name = album['name']
            logging.debug(f"Processing album: {album_name}")
            album_data.append({
                'album_name': album_name,
            })

            try:
                tracks = sp.album_tracks(album['id'])
                track_data = []

                if not tracks or 'items' not in tracks:
                    logging.error(f"No tracks data returned for album: {album_name}")
                    continue

                logging.debug(f"Found {len(tracks['items'])} tracks in album: {album_name}")
                for track in tracks['items']:
                    track_data.append({
                        'track_name': track['name'],
                        'track_id': track['id']
                    })
                album_data[-1]['tracks'] = track_data

            except Exception as e:
                logging.error(f"Error getting tracks for album {album_name}: {e}")
                continue

    try:
        logging.debug("Saving album data to JSON file")
        w = io.StringIO()
        json.dump(album_data, w)
        content = w.getvalue()

        with open("albums_and_tracks.json", "w") as f:
            f.write(content)

        w.close()
        logging.debug("Successfully saved album data to JSON file")

    except (IOError, OSError) as e:
        logging.error(f"An error occurred while writing to the file: {e}")
    except TypeError as e:
        logging.error(f"An error occurred: The album_and_tracks is not JSON serializable: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    def download_track_thread(track_id, track_name, album_path):
        try:
            logging.debug(f"Starting download for track: {track_name}")
            download_and_save_mp3(track_id, track_name + ".mp3", album_path, skip=True)
            logging.debug(f"Successfully downloaded: {track_name}")
        except Exception as e:
            logging.error(f"Error downloading {track_name}: {e}")

    threads = []
    for album in album_data:
        album_name = album['album_name']
        tracks = album['tracks']
        album_path = os.path.join(path, "Artists", artist_name, album_name)

        album_path = album_path.replace("?", " huh")
        album_path = album_path.replace("<", " ")
        album_path = album_path.replace(">", " ")

        logging.debug(f"Creating album directory: {album_path}")
        os.makedirs(album_path, exist_ok=True)

        for track in tracks:
            thread = threading.Thread(
                target=download_track_thread,
                args=(track['track_id'], track['track_name'], album_path),
                daemon=True
            )
            threads.append(thread)
            thread.start()

    logging.debug("Waiting for all download threads to complete")
    for thread in threads:
        thread.join()

    logging.info(f"Done downloading {artist_name}")


def search_artist(artist_name):
    logging.info(f"Searching for artist: {artist_name}")
    if artist_name is None or artist_name == '':
        logging.error("Artist name cannot be None or empty")
        raise ValueError("Artist name cannot be None or empty")

    sp = login_spotify()
    logging.debug("Successfully logged in to Spotify")

    results = sp.search(q=artist_name, type='artist', limit=6)
    try:
        items = results['artists']['items']
        logging.debug(f"Found {len(items)} matching artists")
    except Exception as e:
        logging.error(f"Error searching for artist: {e}")
        return -1

    if len(items) == 0:
        logging.info("No artist found")
        return False

    artist_data = []

    for artist in items:
        data = {
            'name': artist['name'],
            'id': artist['id']
        }

        if artist['images']:
            data['image'] = artist['images'][0]['url']

        artist_data.append(data)
        logging.debug(f"Added artist to results: {artist['name']}")

    try:
        logging.debug("Saving artist data to JSON file")
        w = io.StringIO()
        json.dump(artist_data, w)
        content = w.getvalue()

        with open("artist_data.json", "w") as f:
            f.write(content)

        w.close()
        logging.debug("Successfully saved artist data to JSON file")

    except (IOError, OSError) as e:
        logging.error(f"An error occurred while writing to the file: {e}")
    except TypeError as e:
        logging.error(f"An error occurred: The artist_data is not JSON serializable: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return True
