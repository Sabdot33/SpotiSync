import json
import logging
import os
import shutil
import sys

import PIL.Image
import send2trash
from io import BytesIO
from logging.handlers import RotatingFileHandler as RotatingFileHandler
from threading import Thread

import pystray
import requests
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QListWidget, QMainWindow, QTabWidget, \
    QVBoxLayout, QLabel, QScrollArea, QLineEdit, QWidget, QPushButton, QHBoxLayout, QTextEdit, QComboBox

from .popups import show_error_message
from ..core.config import read_create_config, CONFIG_FILE
from ..spotifyapi.artists import search_artist, download_artist
from ..spotifyapi.favorites import fetch_user_lib_and_save_all
from ..spotifyapi.playlists import download_all_playlists, fetch_playlists, download_playlist
from ..gui.pyqtSwitch import PyQtSwitch

WINDOW_WIDTH: int = 400
WINDOW_HEIGHT: int = 600

MAX_LOG_SIZE: int = 1024 * 1024 * 1


def set_up_logging() -> logging.root:
    log_handler = logging.getLogger()
    # TODO: Load logging level from config
    log_handler.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler("SpotiSync.log", maxBytes=MAX_LOG_SIZE)
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
        self.icon: pystray.Icon = None

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

        self.default_playlist_pixmap = QPixmap(os.path.join("spotisync", "assets", "playlist.png")).scaled(128, 128, Qt.KeepAspectRatio)
        self.checkmark_pixmap = QPixmap(os.path.join("spotisync", "assets", "checkmark.png"))

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
        self.create_logs_tab()
        self.create_settings_tab()

    def create_synchronization_tab(self):

        # TODO: OPTIMIZE ME AS FUCK
        def get_downloaded_amount() -> str:

            try:
                actually = len(os.listdir(os.path.join(self.PATH, "Favorites")))
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

    def create_playlists_tab(self):
        layout = QVBoxLayout()

        self.tab_widget.currentChanged.connect(lambda index: update_playlists_tab() if index == 1 else None)

        top_label = QLabel("Playlists - Choose a playlist to download")
        top_label.setStyleSheet("font-size: 20pt;")

        top_desc = QLabel(
            "Download all playlists or choose one to download; \nThis Menu will not change its appearance "
            "\nbut the playlists will be downloaded to your Downloads folder")
        top_desc.setWordWrap(True)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: update_playlists_tab())

        download_all_button = QPushButton("Download all playlists")
        download_all_button.clicked.connect(
            lambda: Thread(target=download_all_playlists, args=(self.PATH, self.DEBUG)).start())

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout()

        def update_playlists_tab():

            path = self.PATH

            fetching = Thread(target=fetch_playlists)
            fetching.start()

            # Loop over the layout's widgets and remove them
            while playlist_layout.count():
                item = playlist_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            fetching.join()

            with open(os.path.join("playlist_data.json"), 'r') as pld:
                playlist_data = json.load(pld)

            for playlist in playlist_data:
                playlist_name = playlist['name']
                playlist_id: str = playlist['id']

                logging.debug(f"IMG ID {playlist_id}")

                hlayout = QHBoxLayout()

                cache_path = os.path.join("cache", playlist_id + ".jpg")

                if os.path.exists(cache_path):
                    pixmap = QPixmap(cache_path)
                else:
                    pixmap = self.default_playlist_pixmap

                playlist_image_label = QLabel()
                playlist_image_label.setPixmap(pixmap)

                playlist_label = QLabel(playlist_name)
                playlist_label.setWordWrap(True)

                # The first argument of the lambda function is always False, no matter it's msg_type or value,
                # so pass it through and use the second argument for the playlist ID.
                playlist_button = QPushButton("Download")
                playlist_button.setToolTip(playlist_id)
                playlist_button.clicked.connect(
                    lambda checked, btn = playlist_button:
                    Thread(target=download_playlist, args=(btn.toolTip(), path)).start())

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

    def create_artists_tab(self):
        layout = QVBoxLayout()

        artists_label = QLabel("Artists")
        artists_label.setStyleSheet("font-size: 20pt;")

        artists_desc = QLabel("Search for an artist and download all their songs")
        artists_desc.setWordWrap(True)

        search_bar = QLineEdit()
        search_bar.returnPressed.connect(lambda: search_artist_and_display(self.PATH, search_bar.text()))

        search_button = QPushButton("Search")
        search_button.setStyleSheet("width: 100px;")
        search_button.clicked.connect(lambda: search_artist_and_display(self.PATH, search_bar.text()))

        search_layout = QHBoxLayout()
        search_layout.addWidget(search_bar)
        search_layout.addWidget(search_button)

        search_widget = QWidget()
        search_widget.setLayout(search_layout)

        artist_widget = QWidget()
        artist_layout = QVBoxLayout()

        def search_artist_and_display(base_path: str, query: str):

            if query == "":
                return 0

            # Loop over the layout's widgets and remove them
            while artist_layout.count():
                item = artist_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            logging.debug(f"Searching for artist {query}")
            search_artist(query)
            with open(os.path.join("artist_data.json"), "r") as f:
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
                pi_limage = Image.open(BytesIO(image_data))
                artist_image = pi_limage.resize((128, 128))
                logging.debug(f"Artist image downloaded for {artist_name}")

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
                artist_button.setToolTip(artist_id)

                artist_button.clicked.connect(
                    lambda checked, btn = artist_button:
                    Thread(target=download_artist, args=(btn.toolTip(), base_path)).start())

                # Check if the artist has already been downloaded
                is_downloaded = os.path.exists(os.path.join(base_path, "Artists", artist_name))

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

                logging.debug(f"Artist {artist_name} added to GUI: {label}")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        layout.addWidget(artists_label)
        layout.addWidget(artists_desc)
        layout.addWidget(search_widget)
        layout.addWidget(scroll_area)

        artist_widget.setLayout(artist_layout)
        scroll_area.setWidget(artist_widget)

        self.artists_tab.setLayout(layout)

    def create_logs_tab(self):

        def get_logs():
            logging.debug("Getting logs")
            try:
                return open("errors.log", "r").read()
            except FileNotFoundError:
                return "No log file found"

        layout = QVBoxLayout()

        logs_label = QLabel("Logs")
        logs_label.setStyleSheet("font-size: 20pt;")

        logs_desc = QLabel(
            "Here you can take a look at what went wrong with which songs. "
            "\nNote that this section only takes your liked songs in account, not your playlists")
        logs_desc.setWordWrap(True)

        logs_button = QPushButton("Load Logs")
        logs_button.clicked.connect(lambda: logs_text.setText(get_logs()))

        logs_text = QTextEdit("")
        logs_text.setReadOnly(True)

        layout.addWidget(logs_label)
        layout.addWidget(logs_desc)
        layout.addWidget(logs_button)
        layout.addWidget(logs_text)

        self.logs_tab.setLayout(layout)

    def create_settings_tab(self):
        layout = QVBoxLayout()

        settings_label = QLabel("Settings")
        settings_label.setStyleSheet("font-size: 20pt;")

        # Spotify API Credentials - READ ONLY
        label_spotify_credentials = QLabel("Spotify Credentials - These are your API Credentials you got from Spotify")
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

        hlayout = QHBoxLayout()
        hlayout.addWidget(client_secret_show)
        hlayout.addWidget(client_secret_hide)

        h_widget = QWidget()
        h_widget.setLayout(hlayout)

        layout_spotify_credentials = QVBoxLayout()

        layout_spotify_credentials.addWidget(label1)
        layout_spotify_credentials.addWidget(spotify_client_id_box)
        layout_spotify_credentials.addWidget(label2)
        layout_spotify_credentials.addWidget(spotify_client_secret_box)
        layout_spotify_credentials.addWidget(h_widget)

        widget_spotify_credentials = QWidget()
        widget_spotify_credentials.setLayout(layout_spotify_credentials)

        # Update Interval
        layout_schedule_time = QVBoxLayout()
        label_schedule_time = QLabel("Update Interval - Time between two Synchronizations in minutes")

        save_action = lambda: self.schedule_time_save(schedule_time_box.text(), 'settings', 'schedule_time')

        schedule_time = read_create_config().getint('settings', 'schedule_time')
        schedule_time_box = QLineEdit(str(schedule_time))
        schedule_time_box.returnPressed.connect(save_action)
        schedule_time_box.setStyleSheet("width: padding-left: 100px;;")

        schedule_time_save = QPushButton("Save")
        schedule_time_save.clicked.connect(save_action)

        layout_schedule_time.addWidget(label_schedule_time)
        layout_schedule_time.addWidget(schedule_time_box)
        layout_schedule_time.addWidget(schedule_time_save)
        widget_schedule_time = QWidget()
        widget_schedule_time.setLayout(layout_schedule_time)

        # Style
        def get_styles():
            styles = []
            for file in os.listdir(os.path.join("spotisync", "assets", "styles")):
                if file.endswith(".qss"):
                    styles.append(file[:-4])
            return styles

        def set_style(style):
            filename = f"{style}.qss"
            config = read_create_config()
            config.set('settings', 'style', filename)
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
            style_path = open(os.path.join("assets", "styles", filename)).read()
            self.setStyleSheet(style_path)

        layout_style = QVBoxLayout()
        label_style = QLabel("Style - The style of the GUI")

        style = read_create_config().get('settings', 'style')
        style = style.split(".")[0]
        style_box = QComboBox()
        style_box.addItems(get_styles())
        style_box.setCurrentText(style)
        style_box.currentTextChanged.connect(lambda: set_style(style_box.currentText()))

        layout_style.addWidget(label_style)
        layout_style.addWidget(style_box)
        widget_style = QWidget()
        widget_style.setLayout(layout_style)

        # Download Path
        layout_download_path = QVBoxLayout()
        label_download_path = QLabel("Download Path - Root Path of where the songs will be downloaded.")

        download_path = read_create_config().get('settings', 'download_path')
        download_path_box = QLineEdit(download_path)
        download_path_box.returnPressed.connect(
            lambda: self.dw_path_save(download_path_box.text(), 'settings', 'download_path'))

        download_path_save = QPushButton("Save")
        download_path_save.clicked.connect(
            lambda: self.dw_path_save(download_path_box.text(), 'settings', 'download_path'))

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
        switch_debug.setStyleSheet(
            "background-color: #202020; color: #fffcf6; border: 1px solid black; border-radius: 5px;")
        switch_debug.toggled.connect(lambda checked: self.any_toggle(checked, 'settings', 'debug'))

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
        switch_startup.setStyleSheet(
            "background-color: #202020; color: #fffcf6; border: 1px solid black; border-radius: 5px;")
        switch_startup.toggled.connect(lambda checked: self.any_toggle(checked, 'settings', 'startup_with_gui'))

        layout_startup.addWidget(label_startup)
        layout_startup.addWidget(switch_startup)

        widget_startup = QWidget()
        widget_startup.setLayout(layout_startup)

        # Quit to tray
        quit_to_tray_button = QPushButton("Quit to Tray")
        quit_to_tray_button.clicked.connect(lambda: print("balls")) # self.hide() TODO: use self.hide() but with variable so that it does not stop at startup
                                                                                # TODO: (lambda connect codes run at startup idk why)

        quit_program = QPushButton("Quit")
        quit_program.clicked.connect(lambda: print("hi")) # TODO: implement actual shutdown function (lambda connect codes run at startup idk why)

        layout.addWidget(settings_label)
        layout.addWidget(widget_schedule_time)
        layout.addWidget(widget_download_path)
        layout.addWidget(widget_style)
        layout.addWidget(widget_debug)
        layout.addWidget(widget_startup)
        layout.addWidget(label_spotify_credentials)
        layout.addWidget(widget_spotify_credentials)
        layout.addWidget(quit_to_tray_button)
        layout.addWidget(quit_program)

        self.settings_tab.setLayout(layout)

    def any_toggle(self, checked, section, option):
        config = read_create_config()
        config.set(section, option, str(checked))
        logging.debug(f"{section}: {option} set to {checked}")
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

    def dw_path_save(self, path, section, option):
        userinput = self.show_error_message("question",
                                            f"Your files will be copied to the new download path: {path}\n"
                                            f"This will take some time and the files will NOT be verified.\n"
                                            f"You can also change this manually in your config.ini.\n\n"
                                            f"Are you sure you want to continue?")

        if userinput:

            if not path.endswith('/'):
                path += '/'

            try:
                if path != self.PATH:
                    shutil.copytree(self.PATH, path, dirs_exist_ok=True)

                config = read_create_config()
                config.read(CONFIG_FILE)
                config.set(section, option, path)

                with open(CONFIG_FILE, 'w') as configfile:
                    config.write(configfile)

                logging.debug(f"{section}: {option} set to {path}")

                try:
                    send2trash(path)
                except Exception as e:
                    self.show_error_message("critical", f"Error trashing old download path: {str(e)}\n\nnot deleting.")
                    self.show_error_message("information",
                                            "Download path saved successfully! Please restart SpotiSync.")

                    self.cleanup() # TODO: make actually stop the programm

            except Exception as e:
                self.show_error_message("critical", "Error copying files...")
                logging.error(e)

        else:
            self.show_error_message("information", "Cancelled")

    def schedule_time_save(self, time, section, option):
        """
        Saves the schedule time to the configuration file.

        Args:
            time (str): The schedule time to save.
            section (str): The configuration section.
            option (str): The configuration option.

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
        logging.debug(f"{section}: {option} set to {time}")
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources")
        logger.info("Saving Logs")

        try:
            self.icon.stop()
        except Exception as e:
            logger.error("Failed stopping TrayManager: " + str(e))

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

        logging.debug("Deleting jsons'")

        for file in os.listdir():
            if file.endswith(".json"): #  and file != "song_data.json":
                logging.debug(f"Removing {file}")
                os.remove(file)

        logging.debug("Exiting")

        try:
            os._exit(0)
        except:
            raise RuntimeError
        finally:
            exit(0)


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
