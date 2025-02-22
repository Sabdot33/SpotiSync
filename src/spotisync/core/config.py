import configparser
import os
import multiprocessing
import subprocess
import sys
import shutil
from configparser import ConfigParser

from .utils import show_error_message, enter_value_and_return

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.ini")

def check_for_blanks():
    """
    Check if config.ini exists and has all required values.
    If any values are missing or blank, prompt the user for input.
    """
    if os.path.exists(CONFIG_FILE):
        config = ConfigParser()
        config.read(CONFIG_FILE)
        
        # Define required sections and their fields
        required_config = {
            'deezerapi': ['deezer_arl'],
            'spotifyapi': ['client_id', 'client_secret', 'redirect_uri'],
            'settings': ['startup_with_gui', 'debug', 'download_path', 'schedule_time', 'style']
        }
        
        # Check each section and field
        for section, fields in required_config.items():
            if not config.has_section(section):
                config.add_section(section)
            
            for field in fields:
                if not config.has_option(section, field) or not config.get(section, field).strip():
                    if section == 'spotifyapi':
                        if field == 'redirect_uri':
                            config.set(section, field, 'http://localhost:8888/callback')
                        else:
                            value = enter_value_and_return(f"Enter your Spotify {field}")
                            config.set(section, field, value)
                    elif section == 'deezerapi':
                        value = enter_value_and_return("Enter your Deezer account ARL cookie")
                        config.set(section, field, value)
                    elif section == 'settings':
                        if field == 'startup_with_gui':
                            config.set(section, field, 'true')
                        elif field == 'debug':
                            config.set(section, field, 'False')
                        elif field == 'download_path':
                            value = enter_value_and_return("Enter your download full path ending with a \\ backslash \\")
                            config.set(section, field, value)
                        elif field == 'schedule_time':
                            value = enter_value_and_return("Enter the time in minutes between synchronizations")
                            config.set(section, field, value)
                        elif field == 'style':
                            config.set(section, field, 'default')
        
        # Save any changes made
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)


def read_create_config() -> configparser.ConfigParser:
    """Reads or creates a configuration file.
    If the configuration file exists, this function attempts to read it. 
    If the file does not exist, it creates a new configuration file with default settings.
    Returns:
        ConfigParser: The configuration object.
    """
    check_for_blanks()

    config = ConfigParser()

    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
            # Ensure download path uses correct path separators
            if 'settings' in config and 'download_path' in config['settings']:
                download_path = config['settings']['download_path']
                download_path = os.path.normpath(download_path)
                config.set('settings', 'download_path', download_path)
            return config
        except Exception as e:
            print(f"Error reading config file: {e}")
            show_error_message("critical", "An error occurred while reading your config.ini file:\n\n" + str(e))
            raise e
    else:
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
                   enter_value_and_return("Enter the time in minutes between synchronizations"))
        config.set('settings', 'style', 'default')

        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return config
