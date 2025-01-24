import io
import json
import logging
import os

from .download import download_and_save_mp3
from .spotipy import login_spotify


def download_artist(artist_id: str, path: str = '.'):
    if artist_id is None:
        raise ValueError("artist_id cannot be None")

    sp = login_spotify()

    results = sp.artist_albums(artist_id)

    try:
        artist_name = results['items'][0]['artists'][0]['name']
        logging.debug("Processing albums for: %s", artist_name)
    except (IndexError, KeyError) as e:
        logging.error("Could not get artist name: %s", e)

    items = results['items']
    album_data = []

    for item in items:
        album = item
        if album['images']:
            album_name = album['name']
            album_data.append({
                'album_name': album_name,
            })

            try:
                tracks = sp.album_tracks(album['id'])
                track_data = []

                if not tracks or 'items' not in tracks:
                    logging.error("No tracks data returned for album: %s", album_name)
                    continue

                for track in tracks['items']:
                    track_data.append({
                        'track_name': track['name'],
                        'track_id': track['id']
                    })
                album_data[-1]['tracks'] = track_data

            except Exception as e:
                logging.error("Error getting tracks for album %s: %s", album_name, e)
                continue

    try:
        w = io.StringIO()

        json.dump(album_data, w)
        content = w.getvalue()

        with open("albums_and_tracks.json", "w") as f:
            f.write(content)

        w.close()

    except (IOError, OSError) as e:
        logging.error(f"An error occurred while writing to the file: {e}")
    except TypeError as e:
        logging.error(f"An error occurred: The album_and_tracks is not JSON serializable: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    for album in album_data:
        album_name = album['album_name']
        tracks = album['tracks']
        album_path = os.path.join(path, "Artists", artist_name, album_name)

        album_path = album_path.replace("?", " huh")
        album_path = album_path.replace("<", " ")
        album_path = album_path.replace(">", " ")

        os.makedirs(album_path, exist_ok=True)
        for track in tracks:
            track_name = track['track_name']
            track_id = track['track_id']
            try:
                download_and_save_mp3(track_id, track_name + ".mp3", album_path)
            except Exception as e:
                logging.debug(f"Error downloading {track_name}: {e}")

    logging.info(f"Done downloading {artist_name}")


def search_artist(artist_name):
    if artist_name is None or '':
        raise ValueError("Artist name cannot be None")

    sp = login_spotify()

    results = sp.search(q=artist_name, type='artist', limit=6)
    try:
        items = results['artists']['items']
    except Exception as e:
        logging.error(e)
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

    try:
        w = io.StringIO()

        json.dump(artist_data, w)
        content = w.getvalue()

        with open("artist_data.json", "w") as f:
            f.write(content)

        w.close()

    except (IOError, OSError) as e:
        logging.error(f"An error occurred while writing to the file: {e}")
    except TypeError as e:
        logging.error(f"An error occurred: The artist_data is not JSON serializable: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return True
