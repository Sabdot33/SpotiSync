from modules.favorites import fetch_user_lib_and_save_all
from modules.config import read_create_config
from time import sleep
import schedule

def run_scheduler(DEBUG):
    
    config = read_create_config()
    SCHEDULE_TIME = int(config['settings']['schedule_time'])
    config = None
    
    schedule.every(SCHEDULE_TIME).minutes.do(fetch_user_lib_and_save_all, DEBUG)

    # Run at startup
    if DEBUG: sleep(60)
    fetch_user_lib_and_save_all(DEBUG)

    while True:
      # Check for pending tasks every minute
      sleep(60)
      schedule.run_pending()