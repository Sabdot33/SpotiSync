import sys
import os
import json
import logging
import requests
from io import BytesIO
from threading import Thread
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QListWidget, QTabWidget,
                             QPushButton, QLineEdit, QScrollArea, QTextEdit,
                             QComboBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from .pyqtSwitch import PyQtSwitch
from .popups import show_error_message
from ..core.config import read_create_config, CONFIG_FILE
from ..spotifyapi.artists import search_artist, download_artist
from ..spotifyapi.favorites import fetch_user_lib_and_save_all
from ..spotifyapi.playlists import download_all_playlists, fetch_playlists, download_playlist

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpotiSync")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize instance variables
        self.DEBUG = None
        self.style = None
        self.PATH = None
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Load configuration
        self.load_config()
        
        # Initialize UI components
        self.init_ui(layout)
    
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
    
    def init_ui(self, layout):
        # Initialize tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.synchronization_tab = QWidget()
        self.playlists_tab = QWidget()
        self.artists_tab = QWidget()
        self.logs_tab = QWidget()
        self.settings_tab = QWidget()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.synchronization_tab, "Synchronization")
        self.tab_widget.addTab(self.playlists_tab, "Playlists")
        self.tab_widget.addTab(self.artists_tab, "Artists")
        self.tab_widget.addTab(self.logs_tab, "Logs")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Load assets
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.default_playlist_pixmap = QPixmap(os.path.join(package_dir, "assets", "playlist.png")).scaled(128, 128, Qt.KeepAspectRatio)
        self.checkmark_pixmap = QPixmap(os.path.join(package_dir, "assets", "checkmark.png"))
        
        # Initialize tab contents
        self.create_synchronization_tab()
        self.create_playlists_tab()
        self.create_artists_tab()
        self.create_logs_tab()
        self.create_settings_tab()
    
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
        sync_button.clicked.connect(lambda: Thread(target=fetch_user_lib_and_save_all, args=()).start())
        
        layout.addWidget(intro_label)
        layout.addWidget(intro_desc)
        layout.addWidget(features_label)
        layout.addWidget(features_list)
        layout.addWidget(sync_button)
        
        self.synchronization_tab.setLayout(layout)
    
    def create_playlists_tab(self):
        layout = QVBoxLayout()
        
        top_label = QLabel("Playlists - Choose a playlist to download")
        top_label.setStyleSheet("font-size: 20pt;")
        
        top_desc = QLabel(
            "Download all playlists or choose one to download; \nThis Menu will not change its appearance "
            "\nbut the playlists will be downloaded to your Downloads folder")
        top_desc.setWordWrap(True)
        
        refresh_button = QPushButton("Refresh")
        download_all_button = QPushButton("Download all playlists")
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        playlist_widget = QWidget()
        self.playlist_layout = QVBoxLayout()
        playlist_widget.setLayout(self.playlist_layout)
        scroll_area.setWidget(playlist_widget)
        
        refresh_button.clicked.connect(self.update_playlists_tab)
        download_all_button.clicked.connect(
            lambda: Thread(target=download_all_playlists, args=(self.PATH, self.DEBUG)).start())
        
        layout.addWidget(top_label)
        layout.addWidget(top_desc)
        layout.addWidget(refresh_button)
        layout.addWidget(download_all_button)
        layout.addWidget(scroll_area)
        
        self.playlists_tab.setLayout(layout)
        
        # Update playlists when tab is selected
        self.tab_widget.currentChanged.connect(lambda index: self.update_playlists_tab() if index == 1 else None)
    
    def update_playlists_tab(self):
        # Clear existing items
        while self.playlist_layout.count():
            item = self.playlist_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        # Fetch playlists
        fetching = Thread(target=fetch_playlists)
        fetching.start()
        fetching.join()
        
        try:
            with open("playlist_data.json", 'r') as pld:
                playlist_data = json.load(pld)
            
            # Create cache directory if it doesn't exist
            package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(package_dir, "cache")
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            
            for playlist in playlist_data:
                playlist_name = playlist['name']
                playlist_id = playlist['id']
                
                hlayout = QHBoxLayout()
                
                cache_path = os.path.join(cache_dir, playlist_id + ".jpg")
                pixmap = QPixmap(cache_path) if os.path.exists(cache_path) else self.default_playlist_pixmap
                
                playlist_image_label = QLabel()
                playlist_image_label.setPixmap(pixmap)
                
                playlist_label = QLabel(playlist_name)
                playlist_label.setWordWrap(True)
                
                playlist_button = QPushButton("Download")
                playlist_button.setToolTip(playlist_id)
                playlist_button.clicked.connect(
                    lambda checked, btn=playlist_button:
                    Thread(target=download_playlist, args=(btn.toolTip(), self.PATH)).start())
                
                is_downloaded_label = QLabel()
                if os.path.exists(os.path.join(self.PATH, playlist_name)):
                    is_downloaded_label.setPixmap(self.checkmark_pixmap)
                    playlist_button.setText("Update")
                
                hlayout.addWidget(playlist_image_label)
                hlayout.addWidget(playlist_label)
                hlayout.addWidget(playlist_button)
                hlayout.addWidget(is_downloaded_label)
                
                container = QWidget()
                container.setLayout(hlayout)
                self.playlist_layout.addWidget(container)
        except Exception as e:
            show_error_message("critical", f"Error loading playlists: {str(e)}")
    
    def create_artists_tab(self):
        layout = QVBoxLayout()
        
        artists_label = QLabel("Artists")
        artists_label.setStyleSheet("font-size: 20pt;")
        
        artists_desc = QLabel("Search for an artist and download all their songs")
        artists_desc.setWordWrap(True)
        
        search_bar = QLineEdit()
        search_button = QPushButton("Search")
        search_button.setStyleSheet("width: 100px;")
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(search_bar)
        search_layout.addWidget(search_button)
        
        search_widget = QWidget()
        search_widget.setLayout(search_layout)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.artist_layout = QVBoxLayout()
        artist_widget = QWidget()
        artist_widget.setLayout(self.artist_layout)
        scroll_area.setWidget(artist_widget)
        
        def search_handler():
            query = search_bar.text()
            if query:
                self.search_artist_and_display(query)
        
        search_bar.returnPressed.connect(search_handler)
        search_button.clicked.connect(search_handler)
        
        layout.addWidget(artists_label)
        layout.addWidget(artists_desc)
        layout.addWidget(search_widget)
        layout.addWidget(scroll_area)
        
        self.artists_tab.setLayout(layout)
    
    def search_artist_and_display(self, query):
        # Clear existing items
        while self.artist_layout.count():
            item = self.artist_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        try:
            search_artist(query)
            with open("artist_data.json", "r") as f:
                artist_data = json.load(f)
            
            for artist in artist_data:
                artist_name = artist['name']
                artist_image_url = artist['image']
                artist_id = artist['id']
                
                # Download and process artist image
                response = requests.get(artist_image_url, stream=True, timeout=5)
                image_data = response.content
                artist_image = Image.open(BytesIO(image_data))
                artist_image = artist_image.resize((128, 128))
                
                # Convert to QPixmap
                buffer = BytesIO()
                artist_image.save(buffer, format='PNG')
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.getvalue())
                
                # Create layout for artist item
                hlayout = QHBoxLayout()
                
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                
                name_label = QLabel(artist_name)
                name_label.setStyleSheet("font-size: 20pt; text-align: center;")
                
                download_button = QPushButton("Download")
                download_button.setToolTip(artist_id)
                download_button.clicked.connect(
                    lambda checked, btn=download_button:
                    Thread(target=download_artist, args=(btn.toolTip(), self.PATH)).start())
                
                is_downloaded_label = QLabel()
                if os.path.exists(os.path.join(self.PATH, "Artists", artist_name)):
                    is_downloaded_label.setPixmap(self.checkmark_pixmap)
                    download_button.setText("Update")
                
                hlayout.addWidget(image_label)
                hlayout.addWidget(name_label)
                hlayout.addWidget(download_button)
                hlayout.addWidget(is_downloaded_label)
                
                container = QWidget()
                container.setLayout(hlayout)
                self.artist_layout.addWidget(container)
        
        except Exception as e:
            show_error_message("critical", f"Error searching for artist: {str(e)}")
    
    def create_logs_tab(self):
        layout = QVBoxLayout()
        
        logs_label = QLabel("Logs")
        logs_label.setStyleSheet("font-size: 20pt;")
        
        logs_desc = QLabel(
            "Here you can take a look at what went wrong with which songs. "
            "\nNote that this section only takes your liked songs in account, not your playlists")
        logs_desc.setWordWrap(True)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        
        load_logs_button = QPushButton("Load Logs")
        load_logs_button.clicked.connect(self.load_logs)
        
        layout.addWidget(logs_label)
        layout.addWidget(logs_desc)
        layout.addWidget(load_logs_button)
        layout.addWidget(self.logs_text)
        
        self.logs_tab.setLayout(layout)
    
    def load_logs(self):
        try:
            with open("errors.log", "r") as f:
                self.logs_text.setText(f.read())
        except FileNotFoundError:
            self.logs_text.setText("No log file found")
        except Exception as e:
            show_error_message("critical", f"Error loading logs: {str(e)}")
    
    def create_settings_tab(self):
        layout = QVBoxLayout()
        
        settings_label = QLabel("Settings")
        settings_label.setStyleSheet("font-size: 20pt;")
        
        # Spotify API Credentials section
        credentials_label = QLabel("Spotify Credentials - These are your API Credentials you got from Spotify")
        credentials_label.setStyleSheet("font-size: 12pt;")
        
        client_id_label = QLabel("Client ID")
        client_id_box = QLineEdit(read_create_config().get('spotipy', 'client_id'))
        client_id_box.setReadOnly(True)
        
        client_secret_label = QLabel("Client Secret")
        client_secret_box = QLineEdit(read_create_config().get('spotipy', 'client_secret'))
        client_secret_box.setEchoMode(QLineEdit.Password)
        client_secret_box.setReadOnly(True)
        
        show_secret_btn = QPushButton("Show Secret")
        hide_secret_btn = QPushButton("Hide Secret")
        show_secret_btn.clicked.connect(lambda: client_secret_box.setEchoMode(QLineEdit.Normal))
        hide_secret_btn.clicked.connect(lambda: client_secret_box.setEchoMode(QLineEdit.Password))
        
        secret_btn_layout = QHBoxLayout()
        secret_btn_layout.addWidget(show_secret_btn)
        secret_btn_layout.addWidget(hide_secret_btn)
        
        # Download Path section
        download_path_label = QLabel("Download Path - Root Path of where the songs will be downloaded")
        download_path_box = QLineEdit(self.PATH)
        download_path_box.setReadOnly(True)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(lambda: self.get_directory(download_path_box))
        
        # Style section
        style_label = QLabel("Style - The style of the GUI")
        style_combo = QComboBox()
        style_combo.addItems(self.get_available_styles())
        style_combo.setCurrentText(self.style.split('.')[0])
        style_combo.currentTextChanged.connect(self.change_style)
        
        # Add all widgets to layout
        layout.addWidget(settings_label)
        layout.addWidget(credentials_label)
        layout.addWidget(client_id_label)
        layout.addWidget(client_id_box)
        layout.addWidget(client_secret_label)
        layout.addWidget(client_secret_box)
        layout.addLayout(secret_btn_layout)
        layout.addWidget(download_path_label)
        layout.addWidget(download_path_box)
        layout.addWidget(browse_button)
        layout.addWidget(style_label)
        layout.addWidget(style_combo)
        
        self.settings_tab.setLayout(layout)
    
    def get_available_styles(self):
        styles = []
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        style_dir = os.path.join(package_dir, "assets", "styles")
        if os.path.exists(style_dir):
            for file in os.listdir(style_dir):
                if file.endswith(".qss"):
                    styles.append(file[:-4])
        return styles
    
    def change_style(self, style_name):
        config = read_create_config()
        style_file = f"{style_name}.qss"
        config.set('settings', 'style', style_file)
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        style_path = os.path.join(package_dir, "assets", "styles", style_file)
        if os.path.exists(style_path):
            with open(style_path, 'r') as f:
                self.setStyleSheet(f.read())
    
    def get_directory(self, line_edit):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if dir_path:
            config = read_create_config()
            config.set('settings', 'download_path', dir_path)
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
            line_edit.setText(dir_path)
            self.PATH = dir_path

if __name__ == "__main__":
    from spotisync.main import main
    main()