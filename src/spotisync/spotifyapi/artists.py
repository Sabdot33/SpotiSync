import json
import logging
import os

from .download import download_and_save_mp3
from .spotipy import login_spotify


def download_artist(artist_id, path='.', debug=False):
    if artist_id is None:
        raise ValueError("Artist spoti_id cannot be None")

    sp = login_spotify()

    results = sp.artist_albums(artist_id)

    artist_name = results['items'][0]['artists'][0]['name']
    print(artist_name)

    items = results['items']

    album_data = []
    for item in items:
        album = item
        if album['images']:
            album_name = album['name']
            album_data.append({
                'album_name': album_name,
            })
            tracks = sp.album_tracks(album['spoti_id'])
            track_data = []
            for track in tracks['items']:
                track_data.append({
                    'track_name': track['name'],
                    'track_id': track['spoti_id']
                })
            album_data[-1]['tracks'] = track_data

    with open('albums_and_tracks.json', 'w') as f:
        json.dump(album_data, f, indent=4)

    for album in album_data:
        album_name = album['album_name']
        tracks = album['tracks']
        album_path = os.path.join(path, artist_name, album_name)
        os.makedirs(album_path, exist_ok=True)
        for track in tracks:
            track_name = track['track_name']
            track_id = track['track_id']
            try:
                download_and_save_mp3(track_id, track_name + ".mp3", album_path, debug=debug)
            except Exception as e:
                logging.debug(f"Error downloading {track_name}: {e}")


def search_artist(artist_name, debug: bool = False):
    if artist_name is None or '':
        raise ValueError("Artist name cannot be None")

    sp = login_spotify()

    results = sp.search(q=artist_name, type='artist', limit=6)
    try:
        items = results['artists']['items']
    except Exception as e:
        logging.error(e)

    if len(items) == 0:
        logging.info("No artist found")
        return False

    artist_data = []
    for item in items:
        artist = item
        if artist['images']:
            artist_data.append({
                'name': artist['name'],
                'image': artist['images'][0]['url'],
                'spoti_id': artist['spoti_id']
            })

    with open('artist_data.json', 'w') as f:
        json.dump(artist_data, f, indent=4)

    return True
