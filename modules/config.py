import os
from configparser import ConfigParser
from modules import popups

CONFIG_FILE = "config.ini"

def read_create_config():
    """
    Reads or creates a configuration file.

    If the configuration file exists, this function attempts to read it. If the file does not exist, it creates a new configuration file with default settings.

    Returns:
        ConfigParser: The configuration object.
    """
    config = ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
            return config
        except Exception as e:
            print(f"Error reading config file: {e}")
            popups.show_error_message("An error occured while reading your config.ini file:\n\n" + str(e))
            raise e
    else:
        pass
        config.add_section('spotipy')
        config.set('spotipy', 'client_id', popups.enter_value_and_return("Enter your Spotify client ID"))
        config.set('spotipy', 'client_secret', popups.enter_value_and_return("Enter your Spotify client secret"))
        config.set('spotipy', 'redirect_uri', 'http://localhost:8888/callback')
        config.add_section('settings')
        config.set('settings', 'startup_with_gui', 'true')
        config.set('settings', 'debug', 'False')
        config.set('settings', 'download_path', popups.enter_value_and_return("Enter your download full path ending with a slash"))
        config.set('settings', 'schedule_time', popups.enter_value_and_return("Enter the time in minutes betweem synchronizations"))
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config