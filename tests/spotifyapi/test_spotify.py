import os.path
import pytest
from spotisync.spotifyapi.download import download_and_save_mp3
from spotisync.spotifyapi.playlists import download_playlist, fetch_playlists
from spotisync.spotifyapi.artists import search_artist, download_artist
from spotisync.spotifyapi.favorites import fetch_user_lib_and_save_all

# Test download functionality
def test_download_success():
    download_and_save_mp3("4qDHt2ClApBBzDAvhNGWFd", "myfile.mp3", ".", False)
    assert os.path.exists(os.path.join(".", "myfile.mp3")) == True
    os.remove(os.path.join(".", "myfile.mp3"))

def test_download_invalid_id():
    with pytest.raises(ValueError):
        download_and_save_mp3("invalid_id", "myfile.mp3", ".", False)

def test_download_file_exists():
    # First download
    download_and_save_mp3("4qDHt2ClApBBzDAvhNGWFd", "myfile.mp3", ".", False)
    # Second download should raise FileExistsError
    with pytest.raises(FileExistsError):
        download_and_save_mp3("4qDHt2ClApBBzDAvhNGWFd", "myfile.mp3", ".", False)
    os.remove(os.path.join(".", "myfile.mp3"))

def test_download_skip_existing():
    # First download
    download_and_save_mp3("4qDHt2ClApBBzDAvhNGWFd", "myfile.mp3", ".", False)
    # Second download with skip=True should not raise error
    result = download_and_save_mp3("4qDHt2ClApBBzDAvhNGWFd", "myfile.mp3", ".", True)
    assert result == True  # Should return True indicating it failed but was skipped
    os.remove(os.path.join(".", "myfile.mp3"))

# Test playlist functionality
def test_fetch_playlists(mocker):
    # Mock the Spotify API call
    mock_spotify = mocker.patch('spotisync.spotifyapi.playlists.login_spotify')
    mock_spotify.return_value.current_user_playlists.return_value = {
        'items': [{
            'name': 'Test Playlist',
            'external_urls': {'spotify': 'https://open.spotify.com/playlist/123'},
            'id': '123',
            'images': [{'url': 'https://example.com/image.jpg'}]
        }],
        'next': None
    }
    
    fetch_playlists()
    assert os.path.exists('playlist_data.json')
    os.remove('playlist_data.json')

# Test artist functionality
def test_search_artist(mocker):
    # Mock the Spotify API call
    mock_spotify = mocker.patch('spotisync.spotifyapi.artists.login_spotify')
    mock_spotify.return_value.search.return_value = {
        'artists': {
            'items': [{
                'name': 'Test Artist',
                'id': '123',
                'images': [{'url': 'https://example.com/image.jpg'}]
            }]
        }
    }
    
    result = search_artist('Test Artist')
    assert result == True
    assert os.path.exists('artist_data.json')
    os.remove('artist_data.json')

def test_search_artist_not_found(mocker):
    # Mock the Spotify API call
    mock_spotify = mocker.patch('spotisync.spotifyapi.artists.login_spotify')
    mock_spotify.return_value.search.return_value = {
        'artists': {
            'items': []
        }
    }
    
    result = search_artist('Nonexistent Artist')
    assert result == False