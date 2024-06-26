import tkinter as tk
from tkinter import ttk
from threading import Thread
from fetch import fetch_user_lib_and_save_all
from schedule_download import run_scheduler
from time import sleep
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import os
from dotenv import load_dotenv

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

def on_quit_entire_program(icon):
    icon.stop()
    os._exit(911) # TODO: change this...
    
def setup_tray_icon_traits(icon):
    icon.visible = True
    icon.gui = 'gtk' # TODO: has to be changed to something linux and windows compatible

def create_tray_icon():
    icon = pystray.Icon("SpotiSync")
    icon.icon = Image.open("sync_icon.png")
    icon.title = "SpotiSync"
    icon.menu = pystray.Menu(
        item('Open GUI', root.deiconify), # FIXME on linux
        item('Force Synchronization', fetch_user_lib_and_save_all),
        item('Quit', on_quit_entire_program)
    )
    icon.run(setup_tray_icon_traits)
    if debug: print("DEBUG: Created tray icon")


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
        
def show_logs():
    if debug: print("DEBUG: Showing logs")
    logs_label.config(state="normal")
    if not os.path.exists("errors.log"):
        logs_label.config(text="No log file found")
    else:
        notebook.configure(width=1400, height=600)
        with open("errors.log", "r") as logs:
            logs_label.config(text=logs.read())
            logs_button.config(text="Reload Logs")
            root.update()

def reset_window_size():
    if debug: print("DEBUG: Resetting window size")
    notebook.configure(width=800, height=400)

def quit_to_tray():
    if debug: print("DEBUG: Quitting to tray")
    root.withdraw()

# Tray icon thread
tray_icon_thread = Thread(target=create_tray_icon)
tray_icon_thread.daemon = True
tray_icon_thread.start()

# Scheduler running in BG
sync_thread = Thread(target=run_scheduler)
sync_thread.daemon = True
sync_thread.start()

root = tk.Tk()

root.title("SpotiSync")
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)
notebook.configure(width=800,
                   height=400,
                   )

frame1 = tk.Frame(notebook)
frame2 = tk.Frame(notebook)
frame3 = tk.Frame(notebook)

notebook.add(frame1, text="Synchronization")
notebook.add(frame2, text="Logs")
notebook.add(frame3, text="Settings")

# Frame 1 - Main: Synchronization
sync_button = tk.Button(frame1, text="Force Synchronization", command=force_trigger_sync)
sync_button.pack(anchor="n")

quit_to_tray_button = tk.Button(frame1, text="Quit to Tray", command=quit_to_tray)
quit_to_tray_button.pack(anchor="s")

# Frame 2 - Logs
notebook.bind("<<NotebookTabChanged>>", lambda event: show_logs() if event.widget.index(event.widget.select()) == 1 else reset_window_size())

logs_button = tk.Button(frame2, text="Load Logs", command=show_logs)
logs_button.pack()

logs_label = tk.Label(frame2,
                      text="",
                      padx=10,
                      pady=10,
                      wraplength=1300,
                      justify="left",
                      font=("Monospace", 10),
                      background="#202020",
                      foreground="#fffcf6",
                      relief="solid",
                      border="1")

logs_label.config(state="disabled")
logs_label.pack()

# Frame 3 - Settings
quit_to_tray_button = tk.Button(frame3, text="Quit to Tray", command=quit_to_tray)
quit_to_tray_button.pack()

quit_program = tk.Button(frame3, text="Quit", command=root.destroy)
quit_program.pack()

root.mainloop()