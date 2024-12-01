import json
import os
import sys
from io import BytesIO
from threading import Thread

import pystray
import requests
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QListWidget, QMainWindow, QTabWidget, \
    QVBoxLayout, QLabel, QScrollArea, QLineEdit, QWidget, QPushButton, QHBoxLayout
import logging
from logging.handlers import RotatingFileHandler

from .popups import show_error_message
from ..core.config import read_create_config
from ..spotifyapi.artists import search_artist, download_artist
from ..spotifyapi.favorites import fetch_user_lib_and_save_all
from ..spotifyapi.playlists import download_all_playlists, fetch_playlists, download_playlist

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600

MAX_LOG_SIZE = 1024 * 1024 * 1


def set_up_logging() -> logging.root:
    log_handler = logging.getLogger()
    # TODO: Load logging level from config
    log_handler.setLevel(logging.DEBUG)

    try:
        with open("../SpotiSync.log", 'x') as f:
            f.write("")
    except FileExistsError:
        logging.debug("log file already exists")
    # Create file handler
    file_handler = logging.handlers.RotatingFileHandler("../SpotiSync.log", maxBytes=MAX_LOG_SIZE)
    file_handler.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    log_handler.addHandler(file_handler)
    log_handler.addHandler(console_handler)

    return log_handler


logger = set_up_logging()


class TrayManager:
    def __init__(self):
        self.icon = None

    def create_tray_icon(self) -> pystray.Icon:
        logging.debug("Creating tray icon")

        # TODO: make this kill the main app + rename the option from Hide to Exit
        def on_exit(icon: pystray.Icon):
            icon.stop()
            raise SystemExit

        # Load and verify image
        icon_image = Image.open(os.path.join("spotisync", "assets", "sync_icon.png"))
        icon_image.load()

        icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)

        self.icon = pystray.Icon(
            "SpotiSync",
            icon_image,
            menu=pystray.Menu(
                pystray.MenuItem("Show", lambda: print("dshkfjlédfsfdssdfsfd")),
                pystray.MenuItem("Hide this Icon", on_exit),
            ),
        )
        return self.icon


class MainWindow(QMainWindow, ):
    # init
    def __init__(self):
        super().__init__()

        self.DEBUG = None
        self.style = None
        self.PATH = None
        self.logs_tab = QWidget()
        self.artists_tab = QWidget()
        self.settings_tab = QWidget()
        self.playlists_tab = QWidget()
        self.synchronization_tab = QWidget()
        self.setWindowTitle("SpotiSync")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.default_playlist_pixmap = QPixmap("../assets/playlist.png").scaled(128, 128, Qt.KeepAspectRatio)
        self.checkmark_pixmap = QPixmap("../assets/checkmark.png")

        self.load_config()
        self.create_tabs()

        self.tray_manager = TrayManager
        self.icon = self.tray_manager.create_tray_icon(self)

        self.icon.run_detached()

    def load_config(self):
        config = read_create_config()

        self.PATH = config.get("settings", "download_path")
        if os.name == "posix":
            self.PATH = self.PATH.replace("\\", "/")
        if os.name == "nt":
            self.PATH = self.PATH.replace("/", "\\")
        if not self.PATH.endswith("/") and not self.PATH.endswith("\\"):
            if os.name == "posix":
                self.PATH += "/"
            if os.name == "nt":
                self.PATH += "\\"

        self.style = config.get("settings", "style")
        self.DEBUG = config.get("settings", "debug")

        logger.debug(f"Debug: {self.DEBUG}")
        logger.debug(f"Path: {self.PATH}")
        logger.debug(f"Path: {self.style}")

    def create_tabs(self):

        self.tab_widget.addTab(self.synchronization_tab, "Synchronization")
        self.tab_widget.addTab(self.playlists_tab, "Playlists")
        self.tab_widget.addTab(self.artists_tab, "Artists")
        self.tab_widget.addTab(self.logs_tab, "Logs")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        self.create_synchronization_tab()
        self.create_playlists_tab()
        self.create_artists_tab()
        # self.create_logs_tab()
        # self.create_settings_tab()

    def create_synchronization_tab(self):

        # TODO: OPTIMIZE ME AS FUCK
        def get_downloaded_amount() -> str:

            try:
                actually = len(os.listdir(f"{self.PATH}Favorites\\"))
            except FileNotFoundError:
                actually = 0
            try:
                with open('../../song_data.json', 'r') as f:
                    playlist_data = json.load(f)
            except FileNotFoundError:
                playlist_data = []
            should_be = len(playlist_data)

            amount = str(actually) + '/' + str(should_be)

            if actually == 0 and should_be == 0:
                amount = "N/A"

            return amount

        layout = QVBoxLayout()

        intro_label = QLabel("Welcome to SpotiSync!")
        intro_label.setStyleSheet("font-size: 30pt; font-weight: bold;")

        intro_desc = QLabel("A simple tool to synchronize your Spotify playlists with your local music library.")
        intro_desc.setWordWrap(True)

        features_label = QLabel("Features")
        features_label.setStyleSheet("font-size: 24pt; font-weight: bold;")

        downloaded_label = QLabel("Downloaded Songs:")
        downloaded_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        downloaded_label.setAlignment(Qt.AlignCenter)

        downloaded_amount = QLabel(get_downloaded_amount())
        downloaded_amount.setStyleSheet("font-size: 18pt;")
        downloaded_amount.setAlignment(Qt.AlignCenter)

        features_list = QListWidget()
        features_list.addItems([
            "Download your Spotify playlists",
            "Download your liked songs",
            "Download songs from artists you've searched for",
            "Use a tray icon to start synchronization",
            "Customizable settings for your convenience"
        ])

        sync_button = QPushButton("Force Synchronization")
        sync_button.clicked.connect(lambda: Thread(target=fetch_user_lib_and_save_all, args=()).start())
        quit_to_tray_button = QPushButton("Quit to Tray")
        quit_to_tray_button.clicked.connect(lambda: logger.error("DNF"))

        layout.addWidget(intro_label)
        layout.addWidget(intro_desc)
        layout.addWidget(downloaded_label)
        layout.addWidget(downloaded_amount)
        layout.addWidget(features_label)
        layout.addWidget(features_list)
        layout.addWidget(sync_button)
        layout.addWidget(quit_to_tray_button)

        self.synchronization_tab.setLayout(layout)

    # Playlists Tab
    def create_playlists_tab(self):
        layout = QVBoxLayout()

        self.tab_widget.currentChanged.connect(lambda index: update_playlists_tab(self.DEBUG) if index == 1 else None)

        top_label = QLabel("Playlists - Choose a playlist to download")
        top_label.setStyleSheet("font-size: 20pt;")

        top_desc = QLabel(
            "Download all playlists or choose one to download; \nThis Menu will not change its appearance \nbut the playlists will be downloaded to your Downloads folder")
        top_desc.setWordWrap(True)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: update_playlists_tab(self.DEBUG))

        download_all_button = QPushButton("Download all playlists")
        download_all_button.clicked.connect(
            lambda: Thread(target=download_all_playlists, args=(self.PATH, self.DEBUG)).start)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout()

        def update_playlists_tab(debug=False):

            path = self.PATH

            fetching = Thread(target=fetch_playlists, args=(debug,))
            fetching.start()

            # Loop over the layout's widgets and remove them
            while playlist_layout.count():
                item = playlist_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            fetching.join()

            with open('../../playlist_data.json', 'r') as pld:
                playlist_data = json.load(pld)

            for playlist in playlist_data:
                playlist_name = playlist['name']
                playlist_id = playlist['spoti_id']

                logging.debug(f"IMG ID {playlist_id}")

                hlayout = QHBoxLayout()

                with os.path.join("spotisync", "assets", "cache", playlist_id + ".jpg") as cache_path:
                    if os.path.exists(cache_path):
                        pixmap = QPixmap(cache_path)
                    else:
                        pixmap = self.default_playlist_pixmap

                playlist_image_label = QLabel()
                playlist_image_label.setPixmap(pixmap)

                playlist_label = QLabel(playlist_name)
                playlist_label.setWordWrap(True)

                # The first argument of the lambda function is always False, no matter it's type or value,
                # so pass it through and use the second argument for the playlist ID.
                playlist_button = QPushButton("Download")
                playlist_button.clicked.connect(
                    lambda:
                    Thread(target=download_playlist, args=(playlist_id, path, debug)).start())

                is_downloaded_label = QLabel()
                if os.path.exists(os.path.join(path, playlist_name)):
                    is_downloaded_label.setPixmap(self.checkmark_pixmap)
                    playlist_button.setText("Update")

                hlayout.addWidget(playlist_image_label)
                hlayout.addWidget(playlist_label)
                hlayout.addWidget(playlist_button)
                hlayout.addWidget(is_downloaded_label)

                playlist_layout.addLayout(hlayout)

        if not os.path.exists(os.path.join("cache")):
            show_error_message("information", "Cache folder not found. Startup might take some time.")

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
        search_bar.returnPressed.connect(lambda: search_artist_and_display(search_bar.text(), self.DEBUG))

        search_button = QPushButton("Search")
        search_button.setStyleSheet("width: 100px;")
        search_button.clicked.connect(lambda: search_artist_and_display(search_bar.text(), self.DEBUG))

        search_layout = QHBoxLayout()
        search_layout.addWidget(search_bar)
        search_layout.addWidget(search_button)

        search_widget = QWidget()
        search_widget.setLayout(search_layout)

        artist_widget = QWidget()
        artist_layout = QVBoxLayout()

        def search_artist_and_display(query, debug=False):

            # Loop over the layout's widgets and remove them
            while artist_layout.count():
                item = artist_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            logging.debug(f"debug: Searching for artist {query}")
            search_artist(query, debug=debug)
            with open("../../artist_data.json", "r") as f:
                artist_data = json.load(f)

            for artist in artist_data:
                artist_name = artist['name']
                artist_image = artist['image']
                artist_id = artist['spoti_id']

                response = requests.get(artist_image, stream=True, timeout=1)
                response.raise_for_status()
                image_data = b''
                for chunk in response.iter_content(1024):
                    image_data += chunk
                pi_limage = Image.open(BytesIO(image_data))
                artist_image = pi_limage.resize((128, 128))
                logging.debug(f"debug: Artist image downloaded for {artist_name}")

                # Convert PIL Image to bytes buffer
                buffer = BytesIO()
                artist_image.save(buffer, format='PNG')
                buffer.seek(0)

                # Create QPixmap from bytes buffer
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.read())

                hlayout = QHBoxLayout()

                image = QLabel()
                image.setPixmap(pixmap)

                label = QLabel(text=artist_name)
                label.setStyleSheet("font-size: 20pt; text-align: center;")

                artist_button = QPushButton(text="Download")
                artist_button.clicked.connect(
                    lambda:
                    Thread(target=download_artist, args=(artist_id, self.path, self.DEBUG)).start())

                # Check if the artist has already been downloaded
                is_downloaded = os.path.exists(os.path.join(self.path, "Artists/", artist_name))

                is_downloaded_label = QLabel("")
                if is_downloaded:
                    is_downloaded_label.setPixmap(QPixmap(os.path.join("assets", "checkmark.png")))
                    artist_button.setText("Update")

                hlayout.addWidget(image)
                hlayout.addWidget(label)
                hlayout.addWidget(artist_button)
                hlayout.addWidget(is_downloaded_label)

                h_widget = QWidget()
                h_widget.setLayout(hlayout)

                artist_layout.addWidget(h_widget)

                logging.debug(f"debug: Artist {artist_name} added to GUI: {label}")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        layout.addWidget(artists_label)
        layout.addWidget(artists_desc)
        layout.addWidget(search_widget)
        layout.addWidget(scroll_area)

        artist_widget.setLayout(artist_layout)
        scroll_area.setWidget(artist_widget)

        self.artists_tab.setLayout(layout)

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources")
        logger.info("Saving Logs")

        self.icon.stop()

        # Flush all handlers to ensure logs are written
        for handler in logger.handlers + logging.getLogger().handlers:
            handler.flush()
            if isinstance(handler, logging.FileHandler):
                handler.close()  # Properly close file handlers

        logger.info("Cleanup completed")

        # Ensure all logs are written before exiting
        sys.stdout.flush()
        sys.stderr.flush()

        # Remove handlers after logging is done
        logger.handlers.clear()
        logging.getLogger().handlers.clear()


def main():
    app = QApplication(sys.argv)

    # TODO: Add this to the MainWindow class |CANT ADD BECAUSE MWINDOW IS GUI NOT APP| + improve
    config = read_create_config()
    stylesheet = os.path.join("assets", "styles", config.get('settings', 'style'))
    if not os.path.exists(stylesheet):
        logging.warning(f"Style {stylesheet} not found. Using default stylesheet and resetting config.")
        stylesheet = os.path.join("spotisync", "assets", "styles", "Light.qss")
        config.set('settings', 'style', 'Light.qss')
    with open(stylesheet, 'r') as f:
        stylesheet = f.read()
    app.setStyleSheet(stylesheet)

    gui = MainWindow()
    gui.show()
    try:
        app.exec()
    except Exception as e:
        logger.error(f"An Exception occured: {e}")
    finally:
        gui.cleanup()
    gui.cleanup()
