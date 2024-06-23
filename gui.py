import tkinter as tk
from threading import Thread
from fetch import fetch_user_lib_and_save_all
from schedule_download import run_scheduler
from time import sleep
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import os
from dotenv import load_dotenv
import json

# if you're reading this i'm sorry i really am please dont kill me
load_dotenv()
debugenv = os.getenv('DEBUG')
if debugenv == "True":
    debug = True
elif debugenv == "False":
    debug = False
else:
    print("WARN: Invalid value for DEBUG, defaulting to False") 
    debug = False

# TODO: make a better image or something idunno
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

def on_quit_entire_program(icon):
    icon.stop()
    os._exit(911) # TODO: change this...
    

def setup_tray_icon_traits(icon):
    icon.visible = True
    # icon.gui = 'cocoa' # TODO: has to be changed to something linux and windows compatible

def create_tray_icon():
    icon = pystray.Icon("SpotiSync")
    icon.icon = create_image()
    icon.title = "SpotiSync"
    icon.menu = pystray.Menu(
        #item('Open GUI', SpotiSyncGUI()), # TODO: Test this cause i cant yet
        item('Force Synchronization', fetch_user_lib_and_save_all),
        item('Quit', on_quit_entire_program)
    )
    icon.run(setup_tray_icon_traits)
    if debug: print("DEBUG: Created tray icon")

tray_icon_thread = Thread(target=create_tray_icon)
tray_icon_thread.daemon = True
tray_icon_thread.start()

sync_thread = Thread(target=run_scheduler)
sync_thread.daemon = True
sync_thread.start()

class SpotiSyncGUI(tk.Tk):
    def __init__(self):
        
        super().__init__()
        self.title("SpotiSync")
        self.configure(padx=10, pady=10,)
        self.geometry("500x300")
        
        self.status_label = tk.Label(self, text="")
        self.status_label.pack()

        self.sync_button = tk.Button(self, text="Force Synchronization", command=self.force_trigger_sync)
        self.sync_button.pack()
        
        self.output_label = tk.Label(self, text="")
        self.output_label.pack()
                
        self.quit_to_tray_button = tk.Button(self, text="Quit to Tray", command=self.quit_to_tray)
        self.quit_to_tray_button.pack()

        self.quit_button = tk.Button(self, text="Quit", command=self.quit)
        self.quit_button.pack()

    def force_trigger_sync(self):
        if debug: print("DEBUG: Triggering synchronization")
        force_sync_thread = Thread(target=fetch_user_lib_and_save_all)
        force_sync_thread.daemon = True
        force_sync_thread.start()
        
        while force_sync_thread.is_alive():
            self.status_label.config(text="Synchronization in progress...")
            self.sync_button.config(state=tk.DISABLED)
            self.update()
        else:
            self.sync_button.config(state=tk.NORMAL)
            self.status_label.config(text="Synchronization complete!")
            self.update()
            sleep(3)
            self.status_label.config(text="")
            self.update()
            
    def quit_to_tray(self):
        Thread(target=self.destroy).start()

root = SpotiSyncGUI()
root.mainloop()