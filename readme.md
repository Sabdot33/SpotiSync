# SpotiSync

Tired of streaming limitations? SpotiSync empowers you to download your entire Spotify library in MP3 format, creating a permanent, local copy on your computer. No more worrying about internet connectivity or service disruptions.

- Enjoy your music anytime, anywhere, even without an internet connection and sort your library according to the metadata provided by Spotify
- Extracted songs can be easily viewed thanks to a json file.
- Run the program in the background for automatic syncing at your chosen intervals.

SpotiSync was made to break the chains of streaming and puts you in control.

## Credits and notes

This project is made Possible by Yank, the downloading engine of my code, check it out [here](https://github.com/G3VV/Yank)

## Features and uses

### Use cases

SpotiSync liberates your Spotify library, enabling offline access, permanent backups, and personalized music management, so you can ditch the limitations and enjoy your tunes anytime, anywhere, exactly how you like and if you discover a new tune to add, just like it on Spotify and it will automatically be synchronized as long as this app is running.

### Features

- [✓] Extract your liked songs into a json file
- [✓] Download your Spotify library in mp3 format
- [✓] Argument parser
- [✓] Sync in the background
- [✓] Set up itself in a venv

## Installation

### Dependencies

- [python 3.X](https://www.python.org/downloads/)
- [pip](https://pypi.org/project/pip/)

### Python venv

- Clone the repository
- get a Spotify API key

  - Log in [here](https://developer.spotify.com/dashboard/)
  - Create an app and set Redirect URIs to `http://localhost:8888/callback`
  - navigate to its settings
  - Copy the `client_id` and `client_secret` into your .env file

  ```env
  # Enter your Spotify API credentials here
  SPOTIFY_CLIENT_ID=yourID
  SPOTIFY_CLIENT_SECRET=yourSecret

  # Time between two synchronizations in hours
  SCHEDULE_TIME=8

  # This should not be changed unless you know what you're doing
  SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
  ```

- After setting up your .env file run setup.bat or setup.sh
- Authenticate the app in your browser
- You're good to go!
