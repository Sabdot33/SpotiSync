# SpotiSync

SpotiSync allows you to syncronize your Spotify library in mp3 format into a folder and store it on your computer alongside all the metadata spotify provides to their tracks so you can free yourself from the evil corporate overlords that want to control your privacy and data.

## Credits and notes

This project is made Possible by Yank, the downloading engine of my code, check it out [here](https://github.com/G3VV/Yank)

## Features

- [✓] Extract your liked songs into a json file
- [✓] Download your Spotify library in mp3 format
- [✓] Argument parser
- [✓] Sync in the background
- [✓] Run in docker

## Installation

### Method 1 - Python venv

- get a Spotify API key
  - Log in [here](https://developer.spotify.com/dashboard/)
  - Create an app and set Redirect URIs to `http://localhost:8888/callback`
  - navigate to its settings
  - Copy the `client_id` and `client_secret` into your .env file
- After setting up your .env file run the steps in setup.bat or setup.sh
- Your Terminal should look like this:

  ```bash
  (venv) user@PC:~/Desktop/SpotiSync$
  ```

  or

  ```bat
  (venv) C:\Users\user\Desktop\SpotiSync
  ```

- run `python3 main.py`
- authorize the app in your Browser
- You're good to go!
