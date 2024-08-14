# NEEDED WINDOWS DEPENDENCIES: (PIL) pystray requests {dotenv}: load_dotenv spotipy schedule
# NEEDED LINUX DEPENDENCIES: pystray requests load_dotenv spotipy schedule

import pystray
import os
import json
import requests
import io
import sys
from threading import Thread
from modules.search_and_download_artists import *
from modules.fetch_favorite_songs import fetch_user_lib_and_save_all
from modules.schedule_download import run_scheduler
from modules.fetch_and_download_playlists import *
from time import sleep
from PIL import Image
from pystray import MenuItem, Menu
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QTabWidget, QWidget, QCheckBox, QVBoxLayout, QLineEdit, QLabel, QPushButton, QScrollArea, QScrollBar, QMenu, QAction, QTextBrowser, QTextEdit
from PyQt5.QtGui import QPixmap, QTextCursor
from PyQt5.QtCore import Qt, QPoint

load_dotenv()
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH_MUSIC')

DEBUG = os.getenv('DEBUG').lower() == 'true'

if DEBUG: print(f"DEBUG: Download path: {DOWNLOAD_PATH}")

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
    try :
        return open("errors.log", "r").read()
    except FileNotFoundError:
        return "No log file found"
    
def download_playlists_in_thread(playlist_name, playlist_id, path=DOWNLOAD_PATH, DEBUG=False):
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

# TODO: uncomment and pray
create_tray_icon()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SpotiSync")
        self.setGeometry(100, 100, 800, 800)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.create_tabs()

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
            
            # TODO: Remove previous widgets in artist_layout
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
                PILimage = Image.open(io.BytesIO(image_data))
                artist_image = PILimage.resize((128, 128))
                if DEBUG: print(f"DEBUG: Artist image downloaded for {artist_name}")
                
                    # Convert PIL Image to bytes buffer
                buffer = io.BytesIO()
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

STARTUP_WITH_GUI = os.getenv('STARTUP_WITH_GUI').lower() == 'true'

app = QApplication(sys.argv)
gui = MainWindow()
gui.show()
if STARTUP_WITH_GUI == False:
    gui.hide()
sys.exit(app.exec_())

