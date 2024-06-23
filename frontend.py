import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from fetch import fetch_user_lib_and_save_all
from schedule_download import run_scheduler
import threading
import time
import queue

# Function to create an icon image
def create_image():
    # Generate an image and draw a pattern
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), (255, 255, 255))
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill='black')
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill='black')

    return image

# Function to run your backend synchronization code
def run_sync():
    while True:
        run_scheduler()

# Function to handle the "Quit" action
def on_quit(icon, item):
    icon.stop()

# Function to setup the system tray icon
def setup(icon):
    icon.visible = True
    icon.gui = 'gtk'

# Create the system tray icon
icon = pystray.Icon("SpotiSync")
icon.icon = create_image()
icon.title = "SpotiSync"
icon.menu = pystray.Menu(
    item('Quit', on_quit),
    item('Force Synchronization', fetch_user_lib_and_save_all)
)

# Start a communication channel (example: using a queue)
sync_queue = queue.Queue()

# Function to trigger synchronization from the GUI
def trigger_sync():
    sync_queue.put(True)  # Add a signal to the queue

# Start the synchronization in a separate thread
sync_thread = threading.Thread(target=run_sync)
sync_thread.daemon = True
sync_thread.start()

# Run the system tray icon
icon.run(setup)

# Continuously check the queue for synchronization requests
while True:
    if not sync_queue.empty():
        sync_queue.get()  # Remove the signal and trigger synchronization
        fetch_user_lib_and_save_all()
    time.sleep(1)  # Check the queue every second (adjust as needed)
