import schedule
import os
import dotenv
from time import sleep
from .fetch_favorite_songs import fetch_user_lib_and_save_all

def run_scheduler(debug=False):
  
    if debug: 
      print("DEBUG: Running scheduler")
      dbg=True  
    else:
      dbg=False
    
    dotenv.load_dotenv()
    SCHEDULE_TIME = int(os.getenv('SCHEDULE_TIME'))

    schedule.every(SCHEDULE_TIME).minutes.do(fetch_user_lib_and_save_all, debug=dbg)

    # Run at startup
    
    # i'm adding these two lines for my sanity when testing
    sleep(60)
    fetch_user_lib_and_save_all(debug=dbg)

    while True:
      # Check for pending tasks every minute
      schedule.run_pending()
      sleep(60)

if __name__ == "__main__":
  run_scheduler()