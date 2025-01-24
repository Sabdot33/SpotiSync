import logging
from time import sleep

import schedule

from .config import read_create_config
from ..spotifyapi.favorites import fetch_user_lib_and_save_all


def run_scheduler(debug):
    config = read_create_config()
    schedule_time: int = int(config['settings']['schedule_time'])

    schedule.every(schedule_time).minutes.do(fetch_user_lib_and_save_all, debug)

    logging.debug(f"Schedule time: {schedule_time}")

    if debug:
        sleep(60)
    fetch_user_lib_and_save_all()

    while True:
        # Check for pending tasks every minute
        schedule.run_pending()
        sleep(60)
