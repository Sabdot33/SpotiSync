import os
import sys
import schedule
import json
import spotipy
import requests
import zipfile
import pystray
from time import sleep, strftime, localtime
from modules.download import download_and_save_mp3
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image
from threading import Thread
from pystray import MenuItem, Menu
from PIL import Image
from io import BytesIO
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog, QMainWindow, QHBoxLayout, QTabWidget, QWidget, QCheckBox, QVBoxLayout, QLineEdit, QLabel, QPushButton, QScrollArea, QTextEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from configparser import ConfigParser

# Placeholder Values
DOWNLOAD_PATH = "/place/holder"
DEBUG = None
# Hardcoded values
CONFIG_FILE = "config.ini"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SpotiSync")
        self.setGeometry(100, 100, 800, 800)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.create_tabs()
        
    def show_error_message(type, error_message):
        """
        Displays an error message box.

        Args:
            type (str): The type of error: critical, information, question
            error_message (str): A detailed error message.
        """
        QMessageBox.critical(QWidget(), "Error", error_message) if type == "critical" else \
        QMessageBox.information(QWidget(), "Info", error_message) if type == "information" else \
        QMessageBox.question(QWidget(), "Question", error_message)
        

    @staticmethod
    def enter_value_and_return(message, DEBUG=False):
        input_field, ok = QInputDialog.getText(QWidget(),"Enter new value:", message)
        if ok:
            if DEBUG: print("DEBUG: " + str(input_field))
            return str(input_field)
        else:
            raise Exception("User cancelled")

    def create_tabs(self):
        self.synchronization_tab = QWidget()
        self.playlists_tab = QWidget()
        self.logs_tab = QWidget()
        self.settings_tab = QWidget()
        self.artists_tab = QWidget()

        self.tab_widget.addTab(self.synchronization_tab, "Synchronization")
        self.tab_widget.addTab(self.playlists_tab, "Playlists")
        self.tab_widget.addTab(self.artists_tab, "Artists")
        self.tab_widget.addTab(self.logs_tab, "Logs")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        self.create_synchronization_tab()
        self.create_playlists_tab()
        self.create_artists_tab()
        self.create_logs_tab()
        self.create_settings_tab()

    def create_synchronization_tab(self):
        layout = QVBoxLayout()
            
        welcome_label = QLabel("Welcome to SpotiSync!")
        welcome_label.setStyleSheet("font-size: 24pt;")

        welcome_desc = QLabel("This project is supposed to be a set-and-forget thing, \nmeaning you run it once, and it just works.")
        welcome_desc.setWordWrap(True)

        posix_label = QLabel("")
        if os.name == "posix":
            posix_label.setText("Note that the tray icon will very likely NOT work on Linux")
            posix_label.setStyleSheet("color: red; font-weight: bold;")

        sync_button = QPushButton("Force Synchronization")
        sync_button.clicked.connect(force_trigger_sync_thread)
        quit_to_tray_button = QPushButton("Quit to Tray")
        quit_to_tray_button.clicked.connect(lambda self: quit_to_tray(self))

        layout.addWidget(welcome_label)
        layout.addWidget(welcome_desc)
        layout.addWidget(posix_label)
        layout.addWidget(sync_button)
        layout.addWidget(quit_to_tray_button)

        self.synchronization_tab.setLayout(layout)
        


    def create_playlists_tab(self):
        layout = QVBoxLayout()

        top_label = QLabel("Playlists - Choose a playlist to download")
        top_label.setStyleSheet("font-size: 20pt;")

        top_desc = QLabel("Download all playlists or choose one to download; \nThis Menu will not change its appearance \nbut the playlists will be downloaded to your Downloads folder")
        top_desc.setWordWrap(True)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: update_playlists_tab(DEBUG=DEBUG))
        
        download_all_button = QPushButton("Download all playlists")
        download_all_button.clicked.connect(lambda: download_all_playlists_in_thread(path=DOWNLOAD_PATH, DEBUG=DEBUG))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout()

        def update_playlists_tab(DEBUG=False):
            fetch_playlists(DEBUG)

            # Loop over the layout's widgets and remove them
            while playlist_layout.count():
                item = playlist_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            
            with open ('playlist_data.json', 'r') as pld:
                playlist_data = json.load(pld)
                
            for playlist in playlist_data:
                playlist_name = playlist['name']
                playlist_id = playlist['id']
                
                if DEBUG: print(f"IMG ID {playlist_id}")
    
                Hlayout = QHBoxLayout()

                if os.path.exists(f"assets/cache/" + playlist_id + ".jpg"):
                    pixmap = QPixmap(f"assets/cache/" + playlist_id + ".jpg")
                else:
                    pixmap = QPixmap("assets/playlist.png").scaled(128, 128, Qt.KeepAspectRatio)
                
                playlist_image_label = QLabel()
                playlist_image_label.setPixmap(pixmap)
                
                playlist_label = QLabel(playlist_name)
                playlist_label.setWordWrap(True)
                    
                # Okay this is interesting:
                # The problem is that the button will not pass through the first argument to the download_playlists_in_thread function
                # Well actually it will but it passes through "False" no matter the input
                # I have no idea how to fix this because this is very likely to be a library error.
                # The way i deal with it is i pass throught that first argument and just let it be and then interestingly, 
                # the second argument works fine as it passes through the actual string of the ID
                playlist_button = QPushButton("Download")
                playlist_button.clicked.connect(
                    lambda 
                    playlist_name=playlist_name,
                    playlist_id=playlist_id,
                    path=DOWNLOAD_PATH,
                    DEBUG=DEBUG:
                    download_playlists_in_thread(
                    playlist_name=playlist_name,
                    playlist_id=playlist_id,
                    path=path,
                    DEBUG=DEBUG
                ))
                
                is_downloaded = os.path.exists(DOWNLOAD_PATH + playlist_name + "/")
                
                is_downloaded_label = QLabel()
                if is_downloaded:
                    is_downloaded_label.setPixmap(QPixmap("assets/checkmark.png"))
                    playlist_button.setText("Update")

                Hlayout.addWidget(playlist_image_label)
                Hlayout.addWidget(playlist_label)
                Hlayout.addWidget(playlist_button)
                Hlayout.addWidget(is_downloaded_label)
                
                playlist_layout.addLayout(Hlayout)
        
        if os.path.exists("./assets/cache") == False:
            MainWindow.show_error_message("information", "Cache folder not found. Startup might take some time.")
        update_playlists_tab(DEBUG=DEBUG)
        
        playlist_widget.setLayout(playlist_layout)
        scroll_area.setWidget(playlist_widget)
        
        layout.addWidget(top_label)
        layout.addWidget(top_desc)
        layout.addWidget(refresh_button)
        layout.addWidget(download_all_button)
        layout.addWidget(scroll_area)

        self.playlists_tab.setLayout(layout)

    def create_artists_tab(self):
        layout = QVBoxLayout()

        artists_label = QLabel("Artists")
        artists_label.setStyleSheet("font-size: 20pt;")

        artists_desc = QLabel("Search for an artist and download all their songs")
        artists_desc.setWordWrap(True)
        
        search_bar = QLineEdit()
        search_bar.returnPressed.connect(lambda: search_artist_and_display(search_bar.text(), DEBUG=DEBUG))
        
        search_button = QPushButton("Search")
        search_button.setStyleSheet("width: 100px;")
        search_button.clicked.connect(lambda: search_artist_and_display(search_bar.text(), DEBUG=DEBUG))
        
        Search_layout = QHBoxLayout()
        Search_layout.addWidget(search_bar)
        Search_layout.addWidget(search_button)
        
        Search_widget = QWidget()
        Search_widget.setLayout(Search_layout)
        
        artist_widget = QWidget()
        artist_layout = QVBoxLayout()
        
        def search_artist_and_display(query, DEBUG=False):
            
            # Loop over the layout's widgets and remove them
            while artist_layout.count():
                item = artist_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            
            
            if DEBUG: print(f"DEBUG: Searching for artist {query}")
            search_artist(query, DEBUG=DEBUG)
            with open("artist_data.json", "r") as f:
                artist_data = json.load(f)
                
            for artist in artist_data:
                artist_name = artist['name']
                artist_image = artist['image']
                artist_id = artist['id']
                
                response = requests.get(artist_image, stream=True, timeout=1)
                response.raise_for_status()
                image_data = b''
                for chunk in response.iter_content(1024):
                    image_data += chunk
                PILimage = Image.open(BytesIO(image_data))
                artist_image = PILimage.resize((128, 128))
                if DEBUG: print(f"DEBUG: Artist image downloaded for {artist_name}")
                
                    # Convert PIL Image to bytes buffer
                buffer = BytesIO()
                artist_image.save(buffer, format='PNG')
                buffer.seek(0)
    
                # Create QPixmap from bytes buffer
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.read())

                Hlayout = QHBoxLayout()
                
                image = QLabel()
                image.setPixmap(pixmap)
                
                label = QLabel(text=artist_name)
                label.setStyleSheet("font-size: 20pt; text-align: center;")
                
                artist_button = QPushButton(text="Download")
                artist_button.clicked.connect(
                                            lambda 
                                            playlist_name=artist_name,
                                            artist_id=artist_id: 
                                            get_and_download_artist_albums_and_respective_tracks_thread(
                                            playlist_name=artist_name,
                                            artist_id=artist_id,
                                            path=DOWNLOAD_PATH + "Artists/",        
                                            DEBUG=DEBUG
                                            ))
                
                # Check if the artist has already been downloaded
                is_downloaded = os.path.exists(DOWNLOAD_PATH + "Artists/" + artist_name + "/")
                
                is_downloaded_label = QLabel("")
                if is_downloaded:
                    is_downloaded_label.setPixmap(QPixmap("assets/checkmark.png"))
                    artist_button.setText("Update")
                    
                Hlayout.addWidget(image)
                Hlayout.addWidget(label)
                Hlayout.addWidget(artist_button)
                Hlayout.addWidget(is_downloaded_label)
                
                HWidget = QWidget()
                HWidget.setLayout(Hlayout)
                
                artist_layout.addWidget(HWidget)
                
                if DEBUG: print(f"DEBUG: Artist {artist_name} added to GUI: {label}")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(artists_label)
        layout.addWidget(artists_desc)
        layout.addWidget(Search_widget)
        layout.addWidget(scroll_area)
        
        artist_widget.setLayout(artist_layout)
        scroll_area.setWidget(artist_widget)
        
        self.artists_tab.setLayout(layout)

    def create_logs_tab(self):
        layout = QVBoxLayout()

        logs_label = QLabel("Logs")
        logs_label.setStyleSheet("font-size: 20pt;")

        logs_desc = QLabel("Here you can take a look at what went wrong with which songs. \nNote that this section only takes your liked songs in account, not your playlists")
        logs_desc.setWordWrap(True)

        logs_button = QPushButton("Load Logs")
        logs_button.clicked.connect(lambda: logs_text.setText(get_logs()))

        logs_text = QTextEdit("")
        logs_text.setReadOnly(True)
        logs_text.setStyleSheet("background-color: #202020; color: #fffcf6; border: 1px solid black; border-radius: 5px; font-family: monospace")

        layout.addWidget(logs_label)
        layout.addWidget(logs_desc)
        layout.addWidget(logs_button)
        layout.addWidget(logs_text)

        self.logs_tab.setLayout(layout)

    def create_settings_tab(self):
        layout = QVBoxLayout()

        settings_label = QLabel("Settings - not much to see here yet")
        settings_label.setStyleSheet("font-size: 20pt;")

        quit_to_tray_button = QPushButton("Quit to Tray")
        quit_to_tray_button.clicked.connect(lambda: quit_to_tray(self))
        
        quit_program = QPushButton("Quit")
        quit_program.clicked.connect(self.close)

        layout.addWidget(settings_label)
        layout.addWidget(quit_to_tray_button)
        layout.addWidget(quit_program)

        self.settings_tab.setLayout(layout)
        
def read_create_config():
    """
    Reads or creates a configuration file.

    If the configuration file exists, this function attempts to read it. If the file does not exist, it creates a new configuration file with default settings.

    Returns:
        ConfigParser: The configuration object.
    """
    config = ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
            return config
        except Exception as e:
            print(f"Error reading config file: {e}")
            gui.show_error_message("An error occured while reading your config.ini file:\n\n" + str(e))
            raise e
    else:
        config.add_section('spotipy')
        config.set('spotipy', 'client_id', MainWindow.enter_value_and_return("Enter your Spotify client ID", DEBUG))
        config.set('spotipy', 'client_secret', MainWindow.enter_value_and_return("Enter your Spotify client secret", DEBUG))
        config.set('spotipy', 'redirect_uri', 'http://localhost:8888/callback')
        config.add_section('settings')
        config.set('settings', 'startup_with_gui', 'true')
        config.set('settings', 'debug', 'False')
        config.set('settings', 'download_path', MainWindow.enter_value_and_return("Enter your download full path ending with a slash", DEBUG))
        config.set('settings', 'schedule_time', MainWindow.enter_value_and_return("Enter the time in minutes betweem synchronizations", DEBUG))
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config
 
def login_spotify(DEBUG=False):
    
    config = read_create_config()

    # Create Spotify object
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            scope="user-library-read",
            client_id=config.get('spotipy', 'client_id'),
            client_secret=config.get('spotipy', 'client_secret'),
            redirect_uri=config.get('spotipy', 'redirect_uri')
            )
        )
    
    
    return sp
 
def fetch_playlists(DEBUG=False):
    """
    Fetches the user's saved playlists from Spotify and saves the playlist data to a JSON file.

    Args:
        DEBUG (bool, optional): If True, prints DEBUG information. Defaults to False.

    Returns:
        None
    """
    
    sp = login_spotify()

    # Fetch user's saved playlists
    results = sp.current_user_playlists(limit=50)
    playlists = results['items']

    # Fetch all pages of results
    while results['next']:
        results = sp.next(results)
        playlists.extend(results['items'])

    # Extract playlist names and URLs
    playlist_data = []
    playlists = playlists#[::-1]
    for playlist in playlists:
        images = playlist['images']
        
        # save image in cache folder
        if os.path.exists(f"assets/cache/" + playlist["id"] + ".jpg"):
            if DEBUG: print("Image already exists in cache")
            pass
        else:
            if images:
                image_url = images[0]['url']
                response = requests.get(image_url)
                PILimage = Image.open(BytesIO(response.content))
                PILimage = PILimage.resize((128, 128))
                if not os.path.exists('./assets/cache/'):
                    os.makedirs('./assets/cache/')
                PILimage.save(f'./assets/cache/{playlist["id"]}.jpg')
                if DEBUG: print("Image saved in cache")
        
        if images:
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

    with open('playlist_data.json', 'w') as f:
        json.dump(playlist_data, f, indent=4)
        
def download_playlist(playlist_id, path=os.getenv('DOWNLOAD_PATH_MUSIC'), DEBUG=False):
    
    # get playlist name with ID:
    def get_playlist_name(playlist_id, DEBUG=False):
        sp = login_spotify(DEBUG)
        return sp.playlist(str(playlist_id))['name']
    
    playlist_name = get_playlist_name(playlist_id, DEBUG)
    
    if DEBUG: print(f"DEBUG: path: {path} playlist_id: {playlist_id} playlist_name: {playlist_name}")
    
    if not path.endswith("/"):
        path += "/"
        if DEBUG: print("DEBUG: Added '/' to path: " + path)
    
    if not os.path.exists(path):
        os.makedirs(path)
        
    # Create the full path including filename and check if it already exists
    full_path = path + playlist_name + "/"
    if os.path.exists(full_path):
        print("playlist already exists: " + full_path)
        print("Updating playlist")   
    if DEBUG: print("DEBUG: Downloading playlist to " + full_path)
        
    url = f"https://yank.g3v.co.uk/playlist/{playlist_id}"
    hasfailed=False
    
    # download the playlist with requests and save the downloaded file to temp.zip
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-200 status codes
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error downloading zip file: {e}")
    # Check content type before saving
    if response.headers.get('content-type', '').lower == 'application/zip':
        raise ValueError("Downloaded data is not a ZIP file")

    # Save the file
    with open("temp.zip", "wb") as f:
        for chunk in response.iter_content(1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                
    # unzip temp.zip to DW_PATH + playlist_name
    if not hasfailed:
        if DEBUG: print("DEBUG: Unzipping playlist")
        with zipfile.ZipFile("temp.zip", 'r') as zip_ref:
            zip_ref.extractall(full_path)
    
    # remove temp.zip
    if DEBUG: print("DEBUG: Removing temp.zip")
    os.remove("temp.zip")
    if DEBUG: print("DEBUG: Playlist downloaded to " + full_path)
    
def download_all_playlists(path, DEBUG=False):
    """
    Downloads all playlists from a JSON file containing playlist data.

    Args:
        path (str): The path where the playlists will be downloaded.
        DEBUG (bool, optional): If True, prints DEBUG information. Defaults to False.

    Returns:
        None

    Raises:
        FileNotFoundError: If the playlist data file does not exist.
        ValueError: If there is an error downloading a playlist.

    This function reads playlist data from a JSON file named 'playlist_data.json' and downloads each playlist to the specified path.
    If the specified path does not exist, it is created.
    If there is an error downloading a playlist, an exception is raised and a message is printed.
    """
    
    if not os.path.exists(path):
        os.makedirs(path)
        if DEBUG: print("DEBUG: Created download path " + path)
        
    with open('playlist_data.json', 'r') as f:
        playlist_data = json.load(f)
        
    for playlist in playlist_data:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        try:
            download_playlist(playlist_id, path + playlist_name + "/", DEBUG)
        except Exception as e:
            print(f"Error downloading playlist {playlist_name}: {e}")

def fetch_user_lib_and_save_all(DEBUG=False):
    """
    Fetches the user's saved tracks from Spotify and saves the song data to a JSON file.
    Then, it downloads the audio files for each song and saves them to a specified path.
    
    Args:
        DEBUG (bool, optional): If True, prints DEBUG information. Defaults to False.
    
    Returns:
        bool: True if all songs were downloaded successfully, False otherwise.
    """
    
    config = read_create_config()
    DW_PATH = config['settings']['download_path'] + "Favorites/"
    config = None
    
    sp = login_spotify(DEBUG)

    results = sp.current_user_saved_tracks(limit=50)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Extract song names and URLs (oldest first)
    song_data = []
    tracks = tracks[::-1]
    for item in tracks:
        track = item['track']
        song_data.append({
            'name': track['name'],
            'url': track['external_urls']['spotify'],
            'id': track['id']
        })

    with open('song_data.json', 'w') as f:
        json.dump(song_data, f, indent=4)

    if DEBUG: print("DEBUG: Song data extracted and saved to song_data.json")

    with open('song_data.json', 'r') as f:
        data = json.load(f)

    failed_items = []

    for item in data:
        try:
            download_and_save_mp3(item['id'], f"{item['name']}.mp3", path=DW_PATH, DEBUG=DEBUG)
        except Exception as e:
            if os.name == 'nt':
                pass
            else:
                if DEBUG: print(f"DEBUG: {item['name']}.mp3 (Error: {e})")
            if not str(e).startswith("File already exists"):
                failed_items.append(f"{item['name']}.mp3:  {e})")
                
    failed_items = failed_items[::-1] # Reverse order for most recent track to be at the top

    try:
        os.remove('errors.log')
    except Exception as e:
        if DEBUG: print(f"DEBUG: {e}")
    with open('errors.log', 'w') as log:
        if len(failed_items) > 0:
            print(f"Failed to download {len(failed_items)} items")
            log.write(f"Failed to download {len(failed_items)} items:\n\nSong Name:  Error                                                                                      This log is from " + strftime("%Y-%m-%d %H:%M:%S", localtime()) + "\n-------------------------------------------------------------------------------------------------------------------------------------------\n")
            # ^First 4 lines of errors.log^
            for item in failed_items:
                try:
                    if DEBUG: print(f"- {item}")
                    log.write(f"- {item}\n")
                except Exception as e:
                    log.write(f"Cloud not log error; python raised an exception: {e}\nSee https://github.com/ZSabiudj/SpotiSync/blob/main/README.md#bugs for more Information\n")
            if DEBUG: print("DEBUG: Logged errors to errors.log")
        else:
            print("All songs downloaded successfully! Enjoy :3")
            return True

def run_scheduler(DEBUG):
    
    config = read_create_config()
    SCHEDULE_TIME = int(config['settings']['schedule_time'])
    config = None
    
    schedule.every(SCHEDULE_TIME).minutes.do(fetch_user_lib_and_save_all, DEBUG)

    # Run at startup
    # i'm adding these two lines for my sanity when testing
    sleep(60)
    fetch_user_lib_and_save_all(DEBUG)

    while True:
      # Check for pending tasks every minute
      schedule.run_pending()
      sleep(60)
      
def search_artist(artist_name, DEBUG=False):
    
    if artist_name is None:
        raise ValueError("Artist name cannot be None")
    
    sp = login_spotify(DEBUG)
    
    results = sp.search(q='artist:' + artist_name, type='artist', limit=10)
    items = results['artists']['items']

    if len(items) == 0:
        if DEBUG: print("No artist found")
        return False
    
    artist_data = []
    for item in items:
        artist = item
        if artist['images']:
            artist_data.append({
                'name': artist['name'],
                'image': artist['images'][0]['url'],
                'id': artist['id']
            })
    
    with open('artist_data.json', 'w') as f:
        json.dump(artist_data, f, indent=4)
        
    return True

def get_and_download_artist_albums_and_respective_tracks(artist_id, path='./', DEBUG=False):
    
    if artist_id is None:
        raise ValueError("Artist id cannot be None")
    
    sp = login_spotify(DEBUG)
    
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
            tracks = sp.album_tracks(album['id'])
            track_data = []
            for track in tracks['items']:
                track_data.append({
                    'track_name': track['name'],
                    'track_id': track['id']
                })
            album_data[-1]['tracks'] = track_data

    with open('albums_and_tracks.json', 'w') as f:
        json.dump(album_data, f, indent=4)
        
    for album in album_data:
        album_name = album['album_name']
        tracks = album['tracks']
        album_path = path + artist_name + '/' + album_name
        os.makedirs(album_path, exist_ok=True)
        for track in tracks:
            track_name = track['track_name']
            track_id = track['track_id']
            try:
                download_and_save_mp3(track_id, track_name + ".mp3", album_path, DEBUG=DEBUG)
            except Exception as e:
                if DEBUG: print(f"Error downloading {track_name}: {e}")
                
def get_and_download_artist_albums_and_respective_tracks_thread(playlist_name, artist_id, path='./', DEBUG=False):
    # playlist_name is a placeholder value
    
    thread = Thread(target=get_and_download_artist_albums_and_respective_tracks, args=(artist_id, path, DEBUG)) 
    thread.start()

def force_trigger_sync_thread():
    if DEBUG: print("DEBUG: Triggering synchronization")
    force_sync_thread = Thread(target=fetch_user_lib_and_save_all, args=(DEBUG,))
    force_sync_thread.start()

def reset_window_size():
    if DEBUG: print("DEBUG: Resetting window size")

def quit_to_tray():
    if DEBUG: print("DEBUG: Quitting to tray")
    gui.hide()
    
def get_logs():
    if DEBUG: print("DEBUG: Getting logs")
    try:
        return open("errors.log", "r").read()
    except FileNotFoundError:
        return "No log file found"
    
def download_playlists_in_thread(playlist_name, playlist_id, path=DOWNLOAD_PATH, DEBUG=False):
    # playlist_name is a placeholder value
    dwthread = Thread(target=download_playlist, args=(playlist_id, path, DEBUG))
    dwthread.start()
    
def download_all_playlists_in_thread(path=DOWNLOAD_PATH, DEBUG=DEBUG):
    dwthread = Thread(target=download_all_playlists, args=(path, DEBUG))
    dwthread.start()

def on_click_tray():
    if DEBUG: print("DEBUG: Clicked tray icon")
    gui.show()

def on_exit():
    if DEBUG: print("DEBUG: Exiting")
    os._exit(0)

def create_tray_icon():
    icon = pystray.Icon("SpotiSync")
    icon.icon = Image.open("./assets/sync_icon.png")
    icon.title = "SpotiSync"
    icon.on_left_click = on_click_tray
    icon.menu = Menu(
        MenuItem('Open GUI', print("NOT WORKING")), # TODO: fix this
        MenuItem('Force Synchronization', force_trigger_sync_thread),
        MenuItem('Quit', on_exit)
    )
    if os.name == "posix":
        if DEBUG: print("DEBUG: Setting backend")
        # gtk xorg appindicator; win32; darwin
        os.environ["PYSTRAY_BACKEND"] = ""
    icon.run_detached()
    backend = os.getenv("PYSTRAY_BACKEND")
    if DEBUG: print(f"DEBUG: Created tray icon with backend: {backend}")

if __name__ == "__main__":
        
    app = QApplication(sys.argv)
    gui = MainWindow()
    
    config = read_create_config()

    DOWNLOAD_PATH = config['settings']['download_path']
    DEBUG = config['settings']['debug'].lower() == 'true'

    if DEBUG: print(f"DEBUG: Download path: {DOWNLOAD_PATH}")

    # TODO: uncomment and pray
    create_tray_icon()
    Thread(target=run_scheduler, args=(DEBUG,)).start()

    STARTUP_WITH_GUI = os.getenv('STARTUP_WITH_GUI').lower() == 'true'

    gui.show()
    if STARTUP_WITH_GUI == False:
        gui.hide()
    sys.exit(app.exec_())