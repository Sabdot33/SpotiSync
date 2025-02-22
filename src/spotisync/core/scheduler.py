import logging
from time import sleep

import schedule

from .config import read_create_config
from ..spotifyapi.favorites import fetch_user_lib_and_save_all


def run_scheduler(debug):
    """
    Runs the scheduler to periodically fetch and download user's Spotify library.
    
    Args:
        debug (bool): Whether to run in debug mode
    """
    try:
        config = read_create_config()
        schedule_time: int = int(config['settings']['schedule_time'])

        if schedule_time < 1:
            logging.error("Schedule time must be at least 1 minute")
            return

        schedule.every(schedule_time).minutes.do(fetch_user_lib_and_save_all)

        logging.info(f"Scheduler started with {schedule_time} minute interval")

        if debug:
            sleep(60)

        # Initial fetch
        try:
            fetch_user_lib_and_save_all()
        except Exception as e:
            logging.error(f"Initial fetch failed: {e}")

        while True:
            try:
                schedule.run_pending()
                sleep(60)
            except KeyboardInterrupt:
                logging.info("Scheduler stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in scheduler loop: {e}")
                sleep(60)  # Wait before retrying
    except Exception as e:
        logging.error(f"Failed to start scheduler: {e}")
