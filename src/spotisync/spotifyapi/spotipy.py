import json
import logging
import os
from typing import Any, Dict, List

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from ..core.config import read_create_config

# Import logging configuration from core module
from ..core.logger import setup_logging

# Setup logging for this module
logger = setup_logging(__name__)

def login_spotify() -> spotipy.Spotify:
    """Logs in to Spotify using the credentials from the config file.

    Returns:
        spotipy.Spotify: A Spotify client instance.
    """
    logging.info("Initializing Spotify login")
    try:
        config = read_create_config()
        client_id = config['spotifyapi']['client_id']
        client_secret = config['spotifyapi']['client_secret']
        redirect_uri = config['spotifyapi']['redirect_uri']
        scope = config['spotifyapi'].get('scope', 'user-library-read playlist-read-private')
        logging.debug("Successfully read Spotify configuration")

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        logging.info("Successfully authenticated with Spotify")
        return sp

    except KeyError as e:
        logging.error(f"Missing configuration key: {e}")
        raise ValueError(f"Missing configuration key: {e}")
    except Exception as e:
        logging.error(f"Failed to initialize Spotify client: {e}")
        raise

def fetch_user_lib():
    """
    Fetches the user's saved tracks from Spotify and saves the song data to a JSON file.

    Returns:
        None
    """
    logging.info("Starting to fetch user's saved tracks")
    try:
        sp = login_spotify()
        logging.debug("Successfully logged in to Spotify")

        results = sp.current_user_saved_tracks(limit=50)
        tracks = results['items']
        logging.debug(f"Initially fetched {len(tracks)} tracks")

        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            logging.debug(f"Fetched additional tracks, total count: {len(tracks)}")

        # Extract song names and URLs (oldest first)
        song_data = []
        tracks = tracks[::-1]
        logging.info(f"Processing {len(tracks)} tracks")

        for item in tracks:
            track = item['track']
            song_data.append({
                'name': track['name'],
                'url': track['external_urls']['spotify'],
                'id': track['id']
            })
            logging.debug(f"Processed track: {track['name']}")

        try:
            logging.debug("Writing song data to JSON file")
            with open('song_data.json', 'w') as f:
                json.dump(song_data, indent=4, fp=f)
                f.flush()  # Ensure data is written to disk
            logging.info(f"Successfully saved {len(song_data)} tracks to song_data.json")

        except (IOError, OSError) as e:
            logging.error(f"Failed to write to song_data.json: {e}")
            raise
        except TypeError as e:
            logging.error(f"JSON serialization error: {e}")
            raise

    except Exception as e:
        logging.error(f"Failed to fetch user library: {e}")
        raise

    logging.debug("Completed fetching and saving user library")
