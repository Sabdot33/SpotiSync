import os
import shutil
import sys
import json
import requests
import send2trash
import logging
from threading import Thread
from PIL import Image
from io import BytesIO
from PyQt5.QtWidgets import QApplication, QListWidget, QMainWindow, QHBoxLayout, QTabWidget, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton, QScrollArea, QTextEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from modules.pyqtSwitch import PyQtSwitch
from modules.playlists import fetch_playlists, download_all_playlists, download_playlist
from modules.artists import download_artist, search_artist
from modules.config import read_create_config
from modules.favorites import fetch_user_lib_and_save_all
from modules.scheduler import run_scheduler

# Hardcoded values
CONFIG_FILE = "config.ini"

# Configuration loading
config = read_create_config()

DOWNLOAD_PATH = config['settings']['download_path']
if not DOWNLOAD_PATH.endswith("/"):
    DOWNLOAD_PATH += "/"
DEBUG = config['settings']['debug'].lower() == 'true'
    
STARTUP_WITH_GUI = config['settings']['startup_with_gui']

logging.debug(f"Download path: {DOWNLOAD_PATH}")

class MainWindow(QMainWindow):
    # init
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SpotiSync")
        self.setGeometry(100, 100, 800, 800)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.create_tabs()

    # Tabs
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

    # Synchronization Tab
    def create_synchronization_tab(self):
        layout = QVBoxLayout()
        
        intro_label = QLabel("Welcome to SpotiSync!")
        intro_label.setStyleSheet("font-size: 30pt; font-weight: bold;")

        intro_desc = QLabel("A simple tool to synchronize your Spotify playlists with your local music library.")
        intro_desc.setWordWrap(True)

        features_label = QLabel("Features")
        features_label.setStyleSheet("font-size: 24pt; font-weight: bold;")

        features_list = QListWidget()
        features_list.addItems([
            "Download your Spotify playlists",
            "Download your liked songs",
            "Download songs from artists you've searched for",
            "Use a tray icon to start synchronization",
            "Customizable settings for your convenience"
        ])

        sync_button = QPushButton("Force Synchronization")
        sync_button.clicked.connect(lambda: Thread(target=fetch_user_lib_and_save_all, args=(DEBUG,)).start())
        quit_to_tray_button = QPushButton("Quit to Tray")
        quit_to_tray_button.clicked.connect(quit_to_tray)

        layout.addWidget(intro_label)
        layout.addWidget(intro_desc)
        layout.addWidget(features_label)
        layout.addWidget(features_list)
        layout.addWidget(sync_button)
        layout.addWidget(quit_to_tray_button)

        self.synchronization_tab.setLayout(layout)

    # Playlists Tab
    def create_playlists_tab(self):
        layout = QVBoxLayout()
        
        self.tab_widget.currentChanged.connect(lambda index: update_playlists_tab(DEBUG=DEBUG) if index == 1 else None)
        
        top_label = QLabel("Playlists - Choose a playlist to download")
        top_label.setStyleSheet("font-size: 20pt;")

        top_desc = QLabel("Download all playlists or choose one to download; \nThis Menu will not change its appearance \nbut the playlists will be downloaded to your Downloads folder")
        top_desc.setWordWrap(True)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: update_playlists_tab(DEBUG=DEBUG))
        
        download_all_button = QPushButton("Download all playlists")
        download_all_button.clicked.connect(lambda: Thread(target=download_all_playlists, args=(DOWNLOAD_PATH, DEBUG)).start)

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
                    
                # The first argument of the lambda function is always False, no matter it's type or value,
                # so pass it through and use the second argument for the playlist ID.
                playlist_button = QPushButton("Download")
                playlist_button.clicked.connect(
                    lambda 
                    playlist_name=playlist_name,
                    playlist_id=playlist_id,
                    path=DOWNLOAD_PATH,
                    DEBUG=DEBUG:
                    Thread(target=download_playlist, args=(playlist_id, path, DEBUG)).start())
                
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
        
        playlist_widget.setLayout(playlist_layout)
        scroll_area.setWidget(playlist_widget)
        
        layout.addWidget(top_label)
        layout.addWidget(top_desc)
        layout.addWidget(refresh_button)
        layout.addWidget(download_all_button)
        layout.addWidget(scroll_area)

        self.playlists_tab.setLayout(layout)

    # Artists Tab
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
                                            Thread(target=download_artist, args=(artist_id, DOWNLOAD_PATH, DEBUG)).start())
                
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

    # Logs Tab
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

    # Settings Tab
    def create_settings_tab(self):
        layout = QVBoxLayout()

        settings_label = QLabel("Settings")
        settings_label.setStyleSheet("font-size: 20pt;")
        
        # Spotify API Credentials - READ ONLY
        label_spotify_credentials = QLabel("Spotify Credentials - These are you API Credentials you got from Spotify")
        label_spotify_credentials.setStyleSheet("font-size: 12pt;")
        
        label1 = QLabel("Client ID")
        
        spotify_client_id = read_create_config().get('spotipy', 'client_id')
        spotify_client_id_box = QLineEdit(spotify_client_id)
        spotify_client_id_box.setReadOnly(True)
        
        label2 = QLabel("Client Secret")
        
        spotify_client_secret_box = QLineEdit(read_create_config().get('spotipy', 'client_secret'))
        spotify_client_secret_box.setEchoMode(QLineEdit.Password)
        spotify_client_secret_box.setReadOnly(True)

        client_secret_show = QPushButton("Show Secret")
        client_secret_show.clicked.connect(lambda: spotify_client_secret_box.setEchoMode(QLineEdit.Normal))
        
        client_secret_hide = QPushButton("Hide Secret")
        client_secret_hide.clicked.connect(lambda: spotify_client_secret_box.setEchoMode(QLineEdit.Password))
        
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(client_secret_show)
        Hlayout.addWidget(client_secret_hide)
        
        HWidget = QWidget()
        HWidget.setLayout(Hlayout)
        
        layout_spotify_credentials = QVBoxLayout()
        
        layout_spotify_credentials.addWidget(label1)
        layout_spotify_credentials.addWidget(spotify_client_id_box)
        layout_spotify_credentials.addWidget(label2)
        layout_spotify_credentials.addWidget(spotify_client_secret_box)
        layout_spotify_credentials.addWidget(HWidget)
        
        widget_spotify_credentials = QWidget()
        widget_spotify_credentials.setLayout(layout_spotify_credentials)
        
        # Update Interval
        layout_schedule_time = QVBoxLayout()
        label_schedule_time = QLabel("Update Interval - Time between two Synchronizations in minutes")
        
        schedule_time = read_create_config().getint('settings', 'schedule_time')
        schedule_time_box = QLineEdit(str(schedule_time))
        schedule_time_box.returnPressed.connect(lambda: self.schedule_time_save(schedule_time_box.text(), 'settings', 'schedule_time', DEBUG))
        schedule_time_box.setStyleSheet("width: padding-left: 100px;;")
        
        schedule_time_save = QPushButton("Save")
        schedule_time_save.clicked.connect(lambda: self.schedule_time_save(schedule_time_box.text(), 'settings', 'schedule_time', DEBUG))
        
        layout_schedule_time.addWidget(label_schedule_time)
        layout_schedule_time.addWidget(schedule_time_box)
        layout_schedule_time.addWidget(schedule_time_save)
        widget_schedule_time = QWidget()
        widget_schedule_time.setLayout(layout_schedule_time)
        
        # Download Path
        layout_download_path = QVBoxLayout()
        label_download_path = QLabel("Download Path - Root Path of where the songs will be downloaded.")
        
        download_path = read_create_config().get('settings', 'download_path')
        download_path_box = QLineEdit(download_path)
        download_path_box.setStyleSheet("background-color: #202020; color: #fffcf6; border: 1px solid black; border-radius: 5px;")
        download_path_box.returnPressed.connect(lambda: self.dw_path_save(download_path_box.text(), 'settings', 'download_path', DEBUG))
        
        download_path_save = QPushButton("Save")
        download_path_save.clicked.connect(lambda: self.dw_path_save(download_path_box.text(), 'settings', 'download_path', DEBUG))
        
        layout_download_path.addWidget(label_download_path)
        layout_download_path.addWidget(download_path_box)
        layout_download_path.addWidget(download_path_save)
        widget_download_path = QWidget()
        widget_download_path.setLayout(layout_download_path)

        # Debug Mode
        layout_debug = QHBoxLayout()
        label_debug = QLabel("Debug Mode")
        
        switch_debug = PyQtSwitch()
        switch_debug.setChecked(read_create_config().getboolean('settings', 'debug'))
        switch_debug.setAnimation(True)
        switch_debug.setStyleSheet("background-color: #202020; color: #fffcf6; border: 1px solid black; border-radius: 5px;")
        switch_debug.toggled.connect(lambda checked: self.any_toggle(checked, 'settings', 'debug', DEBUG))
        
        layout_debug.addWidget(label_debug)
        layout_debug.addWidget(switch_debug)
        
        widget_debug = QWidget()
        widget_debug.setLayout(layout_debug)
        
        # Startup with GUI 
        layout_startup = QHBoxLayout()
        label_startup = QLabel("Startup with GUI")
        
        switch_startup = PyQtSwitch()
        switch_startup.setChecked(read_create_config().getboolean('settings', 'startup_with_gui'))
        switch_startup.setAnimation(True)
        switch_startup.setStyleSheet("background-color: #202020; color: #fffcf6; border: 1px solid black; border-radius: 5px;")
        switch_startup.toggled.connect(lambda checked: self.any_toggle(checked, 'settings', 'startup_with_gui', DEBUG))
        
        layout_startup.addWidget(label_startup)
        layout_startup.addWidget(switch_startup)
        
        widget_startup = QWidget()
        widget_startup.setLayout(layout_startup)
        
        # Quit to tray
        quit_to_tray_button = QPushButton("Quit to Tray")
        quit_to_tray_button.clicked.connect(quit_to_tray)
        
        quit_program = QPushButton("Quit")
        quit_program.clicked.connect(on_exit)

        layout.addWidget(settings_label)
        layout.addWidget(widget_schedule_time)
        layout.addWidget(widget_download_path)
        layout.addWidget(widget_debug)
        layout.addWidget(widget_startup)
        layout.addWidget(label_spotify_credentials)
        layout.addWidget(widget_spotify_credentials)
        layout.addWidget(quit_to_tray_button)
        layout.addWidget(quit_program)
        
        self.settings_tab.setLayout(layout)
        
    # Switch/Input logic
    def any_toggle(self, checked, section, option, DEBUG):
        config = read_create_config()
        config.set(section, option, str(checked))
        if DEBUG: print(f"DEBUG: {section}: {option} set to {checked}")
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

    def dw_path_save(self, path, section, option, DEBUG):
        userinput = self.show_error_message("question", f"Your files will be copied to the new download path: {path}\nThis will take some time and the files will NOT be verified.\nYou can also change this manually in your config.ini.\n\nAre you sure you want to continue?")
            
        if userinput == True: 
            
            if not path.endswith('/'):
                path += '/'
                
            try:
                if path != DOWNLOAD_PATH:
                    shutil.copytree(DOWNLOAD_PATH, path, dirs_exist_ok=True)

                config = read_create_config()
                config.read(CONFIG_FILE)
                config.set(section, option, path)
                
                with open(CONFIG_FILE, 'w') as configfile:
                    config.write(configfile)

                if DEBUG:
                    print(f"DEBUG: {section}: {option} set to {path}")
                        
                try:
                    send2trash(path)
                except Exception as e:
                    self.show_error_message("critical", f"Error trashing old download path: {str(e)}\n\nnot deleting.")
                    self.show_error_message("information", "Download path saved successfully! Please restart SpotiSync.")
                    on_exit()
            
            except Exception as e:
                self.show_error_message("critical", "Error copying files...")
                
        else:
            self.show_error_message("information", "Cancelled")
            
    def schedule_time_save(self, time, section, option, DEBUG):
        """
        Saves the schedule time to the configuration file.

        Args:
            time (str): The schedule time to save.
            section (str): The configuration section.
            option (str): The configuration option.
            DEBUG (bool): Debug mode flag.

        Raises:
            ValueError: If the input time is not a positive integer.
        """
        try:
            time = int(time)
            if time <= 0:
                raise ValueError("Schedule time must be a positive integer")
        except ValueError:
            self.show_error_message("critical", "Invalid schedule time. Please enter a positive integer.")
            return
        
        config = read_create_config()
        config.set(section, option, str(time))
        if DEBUG: print(f"DEBUG: {section}: {option} set to {time}")
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

def reset_window_size():
    logging.debug("Resetting window size")

def quit_to_tray():
    if os.name == 'posix':
        if MainWindow.show_error_message("question", "Make sure the tray icon is working.") == True:
            gui.hide()
    else:
        logging.debug("Quitting to tray")
        gui.hide()
    
def get_logs():
    logging.debug("Getting logs")
    try:
        return open("errors.log", "r").read()
    except FileNotFoundError:
        return "No log file found"

def on_click_tray():
    logging.debug("Clicked tray icon")
    gui.show()

def on_exit():
    logging.debug("Exiting")
    
    for file in os.listdir():
        if file.endswith(".json"):
            os.remove(file)
            
    try:
        os._exit(0)
    except:
        raise RuntimeError

def create_tray_icon():
    pass

def setup_logging(DEBUG: bool = False) -> None:
    """
    Sets up logging for the application.

    Args:
        DEBUG (bool): Debug mode flag.
    """
    log_level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='spotisync.log'
    )

if __name__ == "__main__":
        
    app = QApplication(sys.argv)
    gui = MainWindow()

    # TODO: uncomment and pray
    create_tray_icon()
    scheduler = Thread(target=run_scheduler, args=(DEBUG,))
    scheduler.start()


    gui.show()
    if STARTUP_WITH_GUI == False:
        gui.hide()
    sys.exit(app.exec_())
