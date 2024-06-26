import schedule
import time
import os
import dotenv
from fetch import fetch_user_lib_and_save_all

def run_scheduler(debug=False):
  
    if debug: 
      print("DEBUG: Running scheduler")
      dbg=True  
    else:
      dbg=False
    
    dotenv.load_dotenv()
    SCHEDULE_TIME = int(os.getenv('SCHEDULE_TIME'))

    schedule.every(SCHEDULE_TIME).hours.do(fetch_user_lib_and_save_all, debug=dbg)

    # Run at startup
    print("If you see this you good my man")
    fetch_user_lib_and_save_all(debug=dbg)

    while True:
      # Check for pending tasks every 10 minutes
      schedule.run_pending()
      time.sleep(60)

if __name__ == "__main__":
  run_scheduler()