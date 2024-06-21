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

### Method 1 - Docker compose

- create a directory and cd into it
  `mkdir spotisync && cd spotisync`
- create a `.env` file

```env
# Enter your Spotify API credentials here
SPOTIFY_CLIENT_ID=yourID
SPOTIFY_CLIENT_SECRET=yourSecret

#Time between two syncronizations in hours
SCHEDULE_TIME=8 # Hours

# This should not be changed unless you know what you're doing
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```
- get a Spotify API key
  - Log in [here](https://developer.spotify.com/dashboard/)
  - Create an app and set Redirect URIs to `http://localhost:8888/callback`
  - navigate to its settings
  - Copy the `client_id` and `client_secret` into your .env file
- create a `compose.yaml` file:

```yaml
version: "3.8"

services:
  spotisync:
    build: .
    image: ghcr.io/zsabiudj/spotisync:latest
    ports:
      - "5000:5000"
    volumes:
      - .:/app
      - ./downloads:/app/downloads # path to your downloads folder 
    restart: always
    env_file:
      - .env
```
- run the container using `docker compose up -d`

### Method 2 - Python venv

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
