import configparser
import os
import multiprocessing
import subprocess
import sys
import shutil
from configparser import ConfigParser

from .utils import show_error_message, enter_value_and_return
from .yank import check_and_setup_yank

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.ini")
YANK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Yank_src")

def run_yank_script(yank_script, yank_dir):
    subprocess.run([sys.executable, yank_script], cwd=yank_dir)

def start_yank_process():
    """Start the Yank process in a separate process."""
    try:
        # Ensure Yank config exists
        yank_config = os.path.join(YANK_DIR, "config.ini")
        if not os.path.exists(yank_config):
            try:
                # Try creating a symlink first
                if os.name == 'nt':  # Windows
                    subprocess.run(['mklink', yank_config, CONFIG_FILE], shell=True, check=True)
                else:  # Unix-like
                    os.symlink(CONFIG_FILE, yank_config)
            except (subprocess.CalledProcessError, OSError):
                # If symlink fails, fall back to copying
                shutil.copy2(CONFIG_FILE, yank_config)
        
        # Start Yank process
        yank_script = os.path.join(YANK_DIR, "index.py")
        process = multiprocessing.Process(
            target=run_yank_script,
            args=(yank_script, YANK_DIR)
        )
        process.daemon = True  # Set as daemon so it terminates with the main process
        process.start()
        return process
    except Exception as e:
        error_msg = f"Failed to start Yank process: {str(e)}"
        show_error_message("critical", error_msg)
        raise RuntimeError(error_msg)

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
    Also starts the Yank process if configuration is successful.

    Returns:
        ConfigParser: The configuration object.
    """
    check_for_blanks()
    check_and_setup_yank()

    config = ConfigParser()

    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
            # Ensure download path uses correct path separators
            if 'settings' in config and 'download_path' in config['settings']:
                download_path = config['settings']['download_path']
                download_path = os.path.normpath(download_path)
                config.set('settings', 'download_path', download_path)
            
            # Start Yank process after successful config read
            start_yank_process()
            return config
        except Exception as e:
            print(f"Error reading config file: {e}")
            show_error_message("critical", "An error occured while reading your config.ini file:\n\n" + str(e))
            raise e
    else:
        config.add_section('deezerapi')
        config.set('deezerapi', 'deezer_arl', enter_value_and_return("Enter your Deezer account ARL cookie"))
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
        
        # Start Yank process after creating new config
        start_yank_process()
        return config
