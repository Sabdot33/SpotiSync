"""SpotiSync Spotify API Module

This module provides the Spotify API integration functionality for the SpotiSync application.
It includes playlist management, artist search, and music download capabilities.
"""

from .artists import search_artist, download_artist
from .download import download_and_save_mp3
from .favorites import fetch_user_lib_and_save_all
from .playlists import download_playlist, fetch_playlists

__all__ = [
    'search_artist',
    'download_artist',
    'download_and_save_mp3',
    'fetch_user_lib_and_save_all',
    'download_playlist',
    'fetch_playlists'
]