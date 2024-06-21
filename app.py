import schedule
import time
import os
import dotenv
from fetch import fetch_user_lib_and_save_all

dotenv.load_dotenv()
SCHEDULE_TIME = int(os.getenv('SCHEDULE_TIME'))

schedule.every(SCHEDULE_TIME).hours.do(fetch_user_lib_and_save_all)

# Run at startup
fetch_user_lib_and_save_all()

while True:
  # Check for pending tasks every 10 minutes
  schedule.run_pending()
  time.sleep(600)