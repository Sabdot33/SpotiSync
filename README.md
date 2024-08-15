# SpotiSync

Tired of streaming limitations? SpotiSync empowers you to download your entire Spotify library in MP3 format, creating a permanent, local copy on your computer. No more worrying about internet connectivity or service disruptions.

- Enjoy your music anytime, anywhere, even without an internet connection and sort your library according to the metadata provided by Spotify
- Extracted songs can be easily viewed thanks to a json file.
- Run the program in the background for automatic syncing at your chosen intervals.

SpotiSync was made to break the chains of streaming and puts you in control.

## Credits and notes

This project is made Possible by Yank, the downloading engine of my code, check it out [here](https://github.com/G3VV/Yank)

### Disclaimer ⚠️

This project is not affiliated with Yank!

## Features uses and known issues

### Use cases

SpotiSync liberates your Spotify library, enabling offline access, permanent backups, and personalized music management, so you can ditch the limitations and enjoy your tunes anytime, anywhere, exactly how you like and if you discover a new tune to add, just like it on Spotify and it will automatically be synchronized as long as this app is running.

I started this project because in my opinion Spotify has made some questionable business choices and as a response to that I wanted to break the chains in an interesting and as user-friendly as possible way.

### Features

- [✓] Extract your liked songs into a json file
- [✓] Download your Spotify library in mp3 format
- [✓] Playlist downloader (Soon to be synchronizer too)
- [✓] Download all albums from your favorite Artist
- [✓] Sync in the background
- [✓] Runs in a venv

### Bugs

- [ ] on windows, logs are limited and the terminal will NOT print the logs, this is because of encoding and decoding issues with for example russian characters
- [ ] Tray icon does not work properly on Linux (Tested on Cinnamon and KDE)
      Note that this is likely a bug in the pystray library

## Installation

### Dependencies

- [python 3.X](https://www.python.org/downloads/)
- [pip](https://pypi.org/project/pip/)

### Python venv

- Clone the repository
- get a Spotify API key

  - Log in [here](https://developer.spotify.com/dashboard/)
  - Create an app
    - set Redirect URIs to `http://localhost:8888/callback`
  - navigate to its settings
  - Copy the `client_id` and `client_secret`

- After setting up your API, run the following commands:

  ```bash
  python -m venv venv
  ```

  ```bash
  source venv/bin/activate
  ```

  or on windows:

  ```bash
  venv\Scripts\activate
  ```

  ```bash
  pip install -r requirements.txt
  ```

  ```bash
  python3 gui.py
  ```

- You get asked for the API credentials
- Authenticate the app in your browser
- You're good to go!
