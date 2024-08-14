# NEEDED WINDOWS DEPENDENCIES: (PIL) pystray requests {dotenv}: load_dotenv spotipy schedule
# NEEDED LINUX DEPENDENCIES: pystray requests load_dotenv spotipy schedule

from tkinter import ttk
from threading import Thread
from modules.search_and_download_artists import *
from modules.fetch_favorite_songs import fetch_user_lib_and_save_all
from modules.schedule_download import run_scheduler
from modules.fetch_and_download_playlists import *
from time import sleep
from PIL import Image, ImageTk
from pystray import MenuItem, Menu
from dotenv import load_dotenv
import tkinter as tk
import pystray
import os
import json
import requests
import io

load_dotenv()
download_path = os.getenv('DOWNLOAD_PATH_MUSIC')

global debug

# if you're reading this i'm sorry i really am please dont kill me
debugenv = os.getenv('DEBUG')
if debugenv == "True":
    debug = True
elif debugenv == "False":
    debug = False
else:
    print("WARN: Invalid value for DEBUG, defaulting to False") 
    debug = False

if not download_path.endswith("/"):
    download_path += "/"
    if debug: print(f"DEBUG: Added trailing slash to download_path: {download_path}")
    
startupenv = os.getenv('STARTUP_WITH_GUI')
if startupenv == "True" or "TRUE" or "true":
    STARTUP_WITH_GUI = True
elif debugenv == "False" or "FALSE" or "false":
    STARTUP_WITH_GUI = False
else:
    print("WARN: Invalid value for STARTUP_WITH_GUI, defaulting to True") 
    STARTUP_WITH_GUI = True

if debug: print(f"DEBUG: Download path: {download_path}")

def force_trigger_sync_thread():
    force_trigger_sync_thread = Thread(target=force_trigger_sync)
    force_trigger_sync_thread.daemon = True
    force_trigger_sync_thread.start()

def force_trigger_sync():
    if debug: print("DEBUG: Triggering synchronization")
    force_sync_thread = Thread(target=fetch_user_lib_and_save_all, args=(debug,))
    force_sync_thread.start()
    
    while force_sync_thread.is_alive():
        status_label.config(text="Synchronization in progress...")
        sync_button.config(state=tk.DISABLED)
        root.update()
    else:
        sync_button.config(state=tk.NORMAL)
        status_label.config(text="Synchronization complete!")
        root.update()
        def i_probably_could_have_done_this_better_but_i_am_lazy():
            sleep(3)
            status_label.config(text="")
            root.update()
        Thread(target=i_probably_could_have_done_this_better_but_i_am_lazy).start()

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
        logs.close()

def reset_window_size():
    if debug: print("DEBUG: Resetting window size")
    notebook.configure(width=800, height=400)

def quit_to_tray():
    if debug: print("DEBUG: Quitting to tray")
    root.withdraw()
    
def download_playlists_in_thread(playlist_id, playlist_name, path=download_path, debug=debug):
    dwthread = Thread(target=download_playlist, args=(playlist_id, playlist_name, path, debug))
    dwthread.start()
    
def download_all_playlists_in_thread(path=download_path, debug=debug):
    dwthread = Thread(target=download_all_playlists, args=(path, debug))
    dwthread.start()

def on_click_tray():
    if debug: print("DEBUG: Clicked tray icon")
    root.deiconify()

def on_exit():
    if debug: print("DEBUG: Exiting")
    root.destroy()
    os._exit(0)

def create_tray_icon(root):
    icon = pystray.Icon("SpotiSync")
    icon.icon = Image.open("./assets/sync_icon.png")
    icon.title = "SpotiSync"
    icon.on_left_click = on_click_tray
    icon.menu = Menu(
        MenuItem('Open GUI', root.deiconify),
        MenuItem('Force Synchronization', force_trigger_sync),
        MenuItem('Quit', on_exit)
    )
    if os.name == "posix":
        if debug: print("DEBUG: Setting backend")
        # gtk xorg appindicator; win32; darwin
        #os.environ["PYSTRAY_BACKEND"] = "win32"
    icon.run_detached()
    backend = os.getenv("PYSTRAY_BACKEND")
    if debug: print(f"DEBUG: Created tray icon with backend: {backend}")

root = tk.Tk()

# Create tray icon in detached mode
create_tray_icon(root)

# Scheduler running in BG
sync_thread = Thread(target=run_scheduler, args=(debug,))
sync_thread.daemon = True
sync_thread.start()


root.title("SpotiSync")
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)
notebook.configure(width=800,
                   height=400,
                   )

frame1 = tk.Frame(notebook)
frame2 = tk.Frame(notebook)
frame3 = tk.Frame(notebook)
frame4 = tk.Frame(notebook)
frame5 = tk.Frame(notebook)

notebook.add(frame1, text="Synchronization")
notebook.add(frame4, text="Playlists")
notebook.add(frame5, text="Artists")
notebook.add(frame2, text="Logs")
notebook.add(frame3, text="Settings")

# Frame 1 - Main: Synchronization
welcome_label = tk.Label(frame1, text="Welcome to SpotiSync!", font=("Arial", 24), padx=10, pady=25)
welcome_label.pack()

welcome_desc = tk.Label(frame1, text="This project is supposed to be a set-and-forget thing,"
                                    "\nmeaning you run it once, and it just works."
                                    "\nI will automatically download your liked songs as configured"
                                    "\nbut you can also download any of your saved playlists"
                                    "\n\nNow sometimes things don't work so i've included a logs section"
                                    "\nwhere you can check what's wrong with your configuration"
                                    "\n\nI hope you enjoy!", font=("Arial", 12), justify="center")
welcome_desc.pack()

if os.name == "posix":
    if debug: print("DEBUG: Printing Warning")
    warn_label = tk.Label(frame1, text="Note that the tray icon will very likely NOT work on Linux", font=("Arial", 12), foreground="red")
    warn_label.pack()

status_label = tk.Label(frame1, text="")
status_label.pack()

sync_button = tk.Button(frame1, text="Force Synchronization", command=force_trigger_sync_thread)
sync_button.pack(anchor="n")

quit_to_tray_button = tk.Button(frame1, text="Quit to Tray", command=quit_to_tray)
quit_to_tray_button.pack(anchor="s")

# Frame 2 - Logs
notebook.bind("<<NotebookTabChanged>>", lambda event: show_logs() if event.widget.index(event.widget.select()) == 3 else reset_window_size())

logs_desc = tk.Label(frame2, text="Here you can take a look at what went wrong with which songs.\n Note that this section only takes your liked songs in account, not your playlists", font=("Arial", 12))
logs_desc.pack(padx=10, pady=25)

logs_button = tk.Button(frame2, text="Load Logs", command=show_logs, padx=10, pady=10)
logs_button.pack()

empty_label_for_space = tk.Label(frame2, text="").pack()

logs_label = tk.Label(frame2,
                      text="",
                      padx=10,
                      pady=10,
                      wraplength=1300,
                      justify="left",
                      font=("Courier New", 10) if os.name == "nt" else ("monospace", 10),
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

# Frame 4 - Playlists
fetch_playlists(debug)

with open ('playlist_data.json', 'r') as pld:
    playlist_data = json.load(pld)
    
playlist_labels = []
playlist_buttons = []
playlist_names = []

scrollbar = tk.Scrollbar(frame4)
canvas = tk.Canvas(frame4, yscrollcommand=scrollbar.set)
scrollbar.config(command=canvas.yview)

frame_for_canvas = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame_for_canvas, anchor="nw")
frame_for_canvas.bind("<Configure>", lambda event, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))

canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

top_label = tk.Label(frame_for_canvas, text="Playlists - Choose a playlist to download", font=("Arial", 20))
top_label.grid(row=0, column=0, columnspan=2, padx=50, pady=15)

top_desc = tk.Label(frame_for_canvas, text="Download all playlists or choose one to download;\nThis Menu will not change its appearance\n but the playlists will be downloaded to your Downloads folder", font=("Arial", 12))
top_desc.grid(row=1, column=0, columnspan=2, padx=50, pady=15, sticky="ew", ipadx=5, ipady=5, )

download_all_button = tk.Button(frame_for_canvas, text="Download all playlists", command=lambda: download_all_playlists(path=download_path, debug=debug))
download_all_button.grid(row=2, column=0, padx=50, pady=15, ipadx=5, ipady=5, sticky="ew")


for item in playlist_data:
    playlist_image_url = item['image']
    playlist_name = item['name']
    playlist_id = item['id']

    try:
        response = requests.get(playlist_image_url, stream=True, timeout=1)
        response.raise_for_status()
        image_data = b''
        for chunk in response.iter_content(1024):
            image_data += chunk
        PILimage = Image.open(io.BytesIO(image_data))
        playlist_image = PILimage.resize((128, 128))
        playlist_image = ImageTk.PhotoImage(playlist_image)
        if debug: print(f"DEBUG: Playlist image downloaded for {playlist_name}")
    except Exception as e:
        if debug:
            print(f"DEBUG: Error while downloading playlist_image: {e}")
        playlist_image = Image.open("./assets/playlist.png").resize((128, 128))
        playlist_image = ImageTk.PhotoImage(playlist_image)
        
    label = tk.Label(frame_for_canvas, text=playlist_name, image=playlist_image)
    label.image = playlist_image
    
    playlist_button = tk.Button(frame_for_canvas, text=playlist_name,
                                command=lambda playlist_name=playlist_name, playlist_id=playlist_id: download_playlists_in_thread(
                                    playlist_id=playlist_id,
                                    playlist_name=playlist_name,
                                    path=download_path,
                                    debug=debug
                                    ))
    playlist_labels.append(label)
    playlist_buttons.append(playlist_button)
    playlist_names.append(playlist_name)
    if debug: print(f"DEBUG: Playlist {playlist_name} added to GUI: {label}")

def update_playlists_tab(debug=False):
    if debug: print("DEBUG: Updating playlists tab")
    for i in range(len(playlist_labels)):
        # Calculate the row and column indices
        row_num = i // 1 + 3 # Integer division to determine the row (+ 3 because of the elements on the top)
        col_num = i % 1  # Modulus operation to determine the column within the row

        playlist_labels[i].grid(row=row_num, column=col_num*2, padx=10, pady=10, ipadx=10, sticky="ew")
        playlist_buttons[i].grid(row=row_num, column=col_num*2 + 1, padx=10, pady=10, sticky="ew")
        # display "Downloaded" if playlist name already exists at download location
        if playlist_names[i] in os.listdir(download_path):
            downloaded_label = tk.Label(frame_for_canvas, text="Already Downloaded", font=("Arial", 12), foreground="#101010")
            downloaded_label.grid(row=row_num, column=col_num*2 + 2, padx=10, pady=10, sticky="ew")

update_playlists_tab(debug=debug)

# Frame 5 - Artists, Albums
desc_label_artists = tk.Label(frame5, text="Artists", font=("Arial", 20), justify="left")
desc_label_artists.grid(row=0, column=0, padx=10, pady=10)

desc_label_artists_desc = tk.Label(frame5, text="Search for an artist and download all their songs", font=("Arial", 12), justify="left")
desc_label_artists_desc.grid(row=1, column=0, padx=10, pady=10)

search_bar = tk.Entry(frame5, font=("Arial", 12), width=40)
search_bar.grid(row=2, column=0, padx=10, pady=10)

search_button = tk.Button(frame5, text="Search", command=lambda: search_artist_and_display(search_bar.get(), debug=debug))
search_button.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

def search_artist_and_display(query, debug=False):
    
    notebook.configure(width=800, height=800)
    
    if debug: print(f"DEBUG: Searching for artist {query}")
    search_artist(query, debug=debug)
    with open("artist_data.json", "r") as f:
        artist_data = json.load(f)
        
    for artist in artist_data:
        artist_name = artist['name']
        artist_image = artist['image']
        artist_id = artist['id']
        
        response = requests.get(artist_image, stream=True, timeout=1)
        response.raise_for_status()
        image_data = b''
        for chunk in response.iter_content(1024):
            image_data += chunk
        PILimage = Image.open(io.BytesIO(image_data))
        artist_image = PILimage.resize((128, 128))
        artist_image = ImageTk.PhotoImage(artist_image)
        if debug: print(f"DEBUG: Artist image downloaded for {artist_name}")
        
        label = tk.Label(frame5, text=artist_name, image=artist_image)
        label.image = artist_image
        
        artist_button = tk.Button(frame5, text=artist_name,
                                command=lambda artist_name=artist_name, artist_id=artist_id: get_and_download_artist_albums_and_respective_tracks_thread(
                                    artist_id=artist_id,
                                    path=download_path + "Artists/",
                                    debug=debug
                                ))
        if debug: print(f"DEBUG: Artist {artist_name} added to GUI: {label}")
        
        label.grid(row=artist_data.index(artist) + 4, column=0, padx=10, pady=10, sticky="ew")
        artist_button.grid(row=artist_data.index(artist) + 4, column=1, padx=10, pady=10, sticky="ew")
        
root.mainloop()

if STARTUP_WITH_GUI == False:
    sleep(1)
    root.deiconify()
