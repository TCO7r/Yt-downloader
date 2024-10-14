import yt_dlp
import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import webbrowser

import os
import sys

if getattr(sys, 'frozen', False):
    # If the app is frozen (running as an .exe), get the directory it is running from
    base_path = sys._MEIPASS
else:
    # Otherwise, use the current script directory
    base_path = os.path.dirname(os.path.abspath(__file__))

# Add FFmpeg to PATH
os.environ['PATH'] = os.path.join(base_path, 'ffmpeg', 'bin') + os.pathsep + os.environ['PATH']


# Function to handle media download using yt_dlp
def download_media(url, format_option, selected_quality, output_path, progress_callback):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'noplaylist': False if 'list=' in url else True,
        'ignoreerrors': True,    
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_callback],
    }

    if format_option == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'postprocessor_args': [
                '-ar', '44100'
            ],
            'prefer_ffmpeg': True,
        })
    elif format_option == 'mp4':
        if selected_quality:
            ydl_opts.update({
                'format': selected_quality,
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
            })
    else:
        messagebox.showerror("Invalid Format", "Please select a valid format: mp3 or mp4.")
        return

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            progress_callback({'status': 'finished'})
        except yt_dlp.utils.DownloadError as e:
            progress_callback({'status': 'error', 'message': str(e)})

# Function to update progress in the GUI
def progress_hook(progress):
    if progress['status'] == 'downloading':
        percent = float(progress.get('_percent_str', '0.0').strip('%'))
        progress_bar.set(percent / 100)
        status_label.configure(text=f"Downloading... {percent:.2f}%")
    elif progress['status'] == 'finished':
        progress_bar.set(1)
        status_label.configure(text="Download completed successfully!")
        print(f"{progress['filename']} downloaded successfully!")
        reset_download()
    elif progress['status'] == 'error':
        progress_bar.set(0)
        status_label.configure(text="Error during download.")
        messagebox.showerror("Error", f"An error occurred: {progress.get('message', 'Unknown Error')}")
        reset_download()

# Function to reset the GUI for the next download
def reset_download():
    download_button.configure(state="normal")
    progress_bar.set(0)
    status_label.configure(text="Status: Idle")
    quality_menu.set('')
    url_entry.delete(0, ctk.END)

# Function to fetch available video qualities
def fetch_qualities():
    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning("Input Required", "Please enter a YouTube URL.")
        return

    format_option = format_var.get()
    if format_option != 'mp4':
        messagebox.showwarning("Invalid Format", "Quality selection is only available for MP4 format.")
        return

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)

        if 'entries' in info:
            first_video_info = info['entries'][0]
        else:
            first_video_info = info

        qualities = []
        for stream in first_video_info['formats']:
            if 'height' in stream and stream['vcodec'] != 'none':
                quality_label = f"{stream['height']}p"
                qualities.append((quality_label, stream['format_id']))

        quality_menu.configure(values=[q[0] for q in qualities])
        quality_map.clear()
        quality_map.update(qualities)

        if qualities:
            quality_menu.set(qualities[0][0])

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch video qualities: {e}")

# Function to start the download in a separate thread
def start_download():
    url = url_entry.get().strip()
    format_option = format_var.get()
    selected_quality = quality_map.get(quality_menu.get(), None)
    output_path = output_entry.get().strip()

    if not url:
        messagebox.showwarning("Input Required", "Please enter a YouTube URL.")
        return
    if not format_option:
        messagebox.showwarning("Input Required", "Please select a format (mp3 or mp4).")
        return
    if not output_path:
        messagebox.showwarning("Input Required", "Please select an output directory.")
        return

    download_button.configure(state="disabled")
    status_label.configure(text="Starting download...")
    progress_bar.set(0)

    threading.Thread(target=download_media, args=(url, format_option, selected_quality, output_path, progress_hook), daemon=True).start()

# Function to browse and select the output directory
def browse_output():
    directory = filedialog.askdirectory()
    if directory:
        output_entry.delete(0, ctk.END)
        output_entry.insert(0, directory)

# Function to toggle between dark and light mode
def toggle_appearance_mode():
    current_mode = ctk.get_appearance_mode()
    new_mode = "Light" if current_mode == "Dark" else "Dark"
    ctk.set_appearance_mode(new_mode)
    appearance_mode_switch.set(new_mode == "Light")


# Function to create the GUI
def create_gui():
    global url_entry, format_var, quality_menu, output_entry, download_button, progress_bar, status_label, quality_map, appearance_mode_switch

    quality_map = {}

    # Set initial appearance and theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("grey.json")  # Changed to blue for a more vibrant look

    root = ctk.CTk()
    root.title("TCO - YouTube Downloader")
    root.geometry("700x650")  # Increased size for better spacing
    root.resizable(False, False)
    root.iconbitmap('gg.ico')
    
    # Main frame with padding and border
    main_frame = ctk.CTkFrame(root, corner_radius=15)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Title frame
    title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    title_frame.pack(fill="x", padx=20, pady=(20, 10))

    title_label = ctk.CTkLabel(title_frame, text="YouTube Downloader", font=("Helvetica", 28, "bold"))
    title_label.pack(side="left")

    # Appearance Mode Toggle Switch
    appearance_mode_switch = ctk.CTkSwitch(title_frame, text="Dark Mode", command=toggle_appearance_mode)
    appearance_mode_switch.pack(side="right")
    appearance_mode_switch.select()  # Set to Dark mode by default

    # Content frame
    content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # YouTube URL
    url_frame = ctk.CTkFrame(content_frame)
    url_frame.pack(fill="x", pady=(0, 15))

    url_label = ctk.CTkLabel(url_frame, text="YouTube URL:", anchor="w", font=("Helvetica", 14, "bold"))
    url_label.pack(fill="x", pady=(0, 5))
    url_entry = ctk.CTkEntry(url_frame, width=500, height=40, placeholder_text="Enter YouTube video URL", font=("Helvetica", 12))
    url_entry.pack(fill="x")

    # Format Selection
    format_frame = ctk.CTkFrame(content_frame)
    format_frame.pack(fill="x", pady=(0, 15))

    format_label = ctk.CTkLabel(format_frame, text="Select Format:", anchor="w", font=("Helvetica", 14, "bold"))
    format_label.pack(fill="x", pady=(0, 5))

    format_var = ctk.StringVar(value="mp4")
    format_options_frame = ctk.CTkFrame(format_frame)
    format_options_frame.pack(fill="x", pady=(0, 5))
    
    mp3_radio = ctk.CTkRadioButton(format_options_frame, text="MP3", variable=format_var, value="mp3", font=("Helvetica", 12))
    mp3_radio.pack(side=ctk.LEFT, padx=(0, 20))
    mp4_radio = ctk.CTkRadioButton(format_options_frame, text="MP4", variable=format_var, value="mp4", font=("Helvetica", 12))
    mp4_radio.pack(side=ctk.LEFT)

    # Quality Selection
    quality_frame = ctk.CTkFrame(content_frame)
    quality_frame.pack(fill="x", pady=(0, 15))

    quality_label = ctk.CTkLabel(quality_frame, text="Select Quality (for MP4):", anchor="w", font=("Helvetica", 14, "bold"))
    quality_label.pack(fill="x", pady=(0, 5))
    
    quality_options_inner_frame = ctk.CTkFrame(quality_frame)
    quality_options_inner_frame.pack(fill="x", pady=(0, 5))
    
    quality_menu = ctk.CTkOptionMenu(quality_options_inner_frame, width=200, height=40, values=[], font=("Helvetica", 12))
    quality_menu.pack(side=ctk.LEFT, padx=(0, 10))
    
    fetch_button = ctk.CTkButton(quality_options_inner_frame, text="Fetch Qualities", width=140, height=40, command=fetch_qualities)
    fetch_button.pack(side=ctk.RIGHT)

    # Output Directory
    output_frame = ctk.CTkFrame(content_frame)
    output_frame.pack(fill="x", pady=(0, 15))

    output_label = ctk.CTkLabel(output_frame, text="Output Directory:", anchor="w", font=("Helvetica", 14, "bold"))
    output_label.pack(fill="x", pady=(0, 5))

    output_inner_frame = ctk.CTkFrame(output_frame)
    output_inner_frame.pack(fill="x", pady=(0, 5))
    
    output_entry = ctk.CTkEntry(output_inner_frame, width=400, height=40, placeholder_text="Select output directory", font=("Helvetica", 12))
    output_entry.pack(side=ctk.LEFT, fill="x", expand=True)
    
    browse_button = ctk.CTkButton(output_inner_frame, text="Browse", width=100, height=40, command=browse_output)
    browse_button.pack(side=ctk.RIGHT, padx=(10, 0))

    # Download Button
    download_button = ctk.CTkButton(content_frame, text="Download", width=220, height=50, command=start_download, font=("Helvetica", 14, "bold"))
    download_button.pack(pady=25)

    # Progress Bar
    progress_bar = ctk.CTkProgressBar(content_frame, width=500, height=20)
    progress_bar.pack(pady=(0, 10))
    progress_bar.set(0)

    # Status Label
    status_label = ctk.CTkLabel(content_frame, text="Status: Idle", font=("Helvetica", 12))
    status_label.pack(pady=(0, 20))

    root.mainloop()

if __name__ == "__main__":
    create_gui()
