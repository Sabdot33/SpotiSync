import configparser
import os
from configparser import ConfigParser

from ..gui.popups import show_error_message, enter_value_and_return

CONFIG_FILE = "config.ini"


def check_for_blanks():
    """
    yet to be implemented
    """
    pass


def read_create_config() -> configparser.ConfigParser:
    """
    Reads or creates a configuration file.

    If the configuration file exists, this function attempts to read it. If the file does not exist, it creates a new configuration file with default settings.

    Returns:
        ConfigParser: The configuration object.
    """

    check_for_blanks()

    config = ConfigParser()

    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
            return config
        except Exception as e:
            print(f"Error reading config file: {e}")
            show_error_message("critical", "An error occured while reading your config.ini file:\n\n" + str(e))
            raise e
    else:
        pass
        config.add_section('spotifyapi')
        config.set('spotifyapi', 'client_id', enter_value_and_return("Enter your Spotify client ID"))
        config.set('spotifyapi', 'client_secret', enter_value_and_return("Enter your Spotify client secret"))
        config.set('spotifyapi', 'redirect_uri', 'http://localhost:8888/callback')
        config.add_section('settings')
        config.set('settings', 'startup_with_gui', 'true')
        config.set('settings', 'debug', 'False')
        config.set('settings', 'download_path',
                   enter_value_and_return("Enter your download full path ending with a \\ backslash \\"))
        config.set('settings', 'schedule_time',
                   enter_value_and_return("Enter the time in minutes betweem synchronizations"))
        config.set('settings', 'style', 'default')

        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config
