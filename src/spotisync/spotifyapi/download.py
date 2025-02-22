import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import LiteralString

import requests

# Import logging configuration from core module
from ..core.logger import setup_logging

# Setup logging for this module
logger = setup_logging(__name__)

# Configure thread pool for concurrent downloads
MAX_WORKERS = 4  # Adjust based on system capabilities
download_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)

def download_and_save_mp3(spoti_id, filename="audio.mp3", path: LiteralString | str = ".", skip=False):
    logging.info(f"Starting download for track ID: {spoti_id}")
    logging.debug(f"Download parameters - filename: {filename}, path: {path}, skip: {skip}")

    url = f"http://yank.g3v.co.uk/track/{spoti_id}"
    hasfailed = False
    timeout = 15  # Reduced timeout to 15 seconds for network operations
    response = None

    if not os.path.exists(path):
        logging.debug(f"Creating directory: {path}")
        try:
            os.makedirs(path)
            logging.debug(f"Successfully created directory: {path}")
        except OSError as e:
            logging.error(f"Failed to create directory {path}: {e}")
            raise

    # Check if filename includes a question mark or slashes, if so replace
    original_filename = filename
    filename = filename.replace("?", " huh")
    filename = filename.replace("/" or "//" or "\\" or "\\\\", "slash")
    filename = filename.replace("//", "slash")
    filename = filename.replace("/", "slash")
    filename = filename.replace("\\\\", "slash")
    filename = filename.replace("\\", "slash")
    filename = filename.replace("<", " ")
    filename = filename.replace(">", " ")

    if original_filename != filename:
        logging.debug(f"Sanitized filename from '{original_filename}' to '{filename}'")

    # Create the full path including filename and check if it already exists
    full_path: LiteralString | str = os.path.join(path, filename)
    if os.path.exists(full_path):
        if not skip:
            logging.error(f"File already exists: {full_path}")
            raise FileExistsError("File already exists: " + full_path)
        else:
            logging.debug(f"File already exists (skipping): {full_path}")
            return True

    try:
        logging.debug(f"Initiating download from: {url} with {timeout}s timeout")
        # Disable SSL verification only for localhost connections
        verify_ssl = not url.startswith("https://127.0.0.1")
        response = requests.get(url, stream=True, timeout=timeout, verify=verify_ssl)
        response.raise_for_status()

        # Check content type before saving
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type != 'audio/mpeg':
            if skip:
                logging.warning(f"Downloaded content is not an MP3 file (Content-Type: {content_type})")
                return True
            else:
                logging.error(f"Downloaded content is not an MP3 file (Content-Type: {content_type})")
                raise ValueError("Downloaded content is not an MP3 file")

        logging.debug(f"Starting to write file chunks to {full_path}")
        total_size = int(response.headers.get('content-length', 0))
        bytes_written = 0

        with open(full_path, "wb") as f:
            for chunk in response.iter_content(1024):
                if chunk:  # filter out keep-alive new chunks
                    bytes_written += len(chunk)
                    f.write(chunk)
                    if total_size > 0:
                        progress = (bytes_written / total_size) * 100
                        logging.debug(f"Download progress for {filename}: {progress:.1f}%")

        logging.info(f"Successfully downloaded and saved: {filename} ({bytes_written} bytes)")
        return False

    except requests.exceptions.Timeout:
        error_msg = f"Request timed out after {timeout} seconds"
        if skip:
            logging.warning(error_msg)
            return True
        else:
            logging.error(error_msg)
            raise ValueError(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Error downloading audio: {e}"
        if skip:
            logging.warning(error_msg)
            return True
        else:
            logging.error(error_msg)
            raise ValueError(error_msg)

    except IOError as e:
        error_msg = f"IO Error while writing file {full_path}: {e}"
        logging.error(error_msg)
        raise

    finally:
        if response is not None:
            response.close()
            logging.debug("Closed response connection")

    return hasfailed

def download_multiple_tracks(track_ids, base_path, skip_existing=False):
    """Download multiple tracks concurrently using thread pool."""
    logging.info(f"Starting concurrent download of {len(track_ids)} tracks")
    
    futures = []
    for track_id in track_ids:
        future = download_pool.submit(download_and_save_mp3, track_id, f"{track_id}.mp3", base_path, skip_existing)
        futures.append(future)
    
    return futures

if __name__ == "__main__":
    logging.info("Starting download script in standalone mode")
    inputted_spoti_id = input("Enter the Spotify ID: ")
    download_path = input("Enter the download path (optional, defaults to current directory): ") or "."
    logging.debug(f"User input - Spotify ID: {inputted_spoti_id}, Download path: {download_path}")
    download_and_save_mp3(inputted_spoti_id, filename="audio.mp3", path=download_path)
