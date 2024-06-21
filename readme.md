# SpotiSync

SpotiSync allows you to download your Spotify library in mp3 format and store it in your computer so you can free yourself from the evil corporate overlords that control your privacy and data.

## Credits

This project is made Possible by Yank, the downloading engine of my code, check it out [here](https://github.com/G3VV/Yank)

## Features

- [✓] Extract your liked songs into a json file</li>
- [✓] Download your Spotify library in mp3 format</li>
- [✓] Argument parser</li>
- [✕] Sync in the background (Soon™)</li>
- [✕] Run in docker (Soon™)</li>

## Installation

- get a Spotify API key
  - Log in [here](https://developer.spotify.com/dashboard/)
  - Create an app and set Redirect URIs to `http://localhost:8888/callback`
  - navigate to its settings
  - Copy the `client_id` and `client_secret` into your .env file
- After setting up your .env file run setup.bat or setup.sh
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
