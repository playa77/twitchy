# twitch_app.py
# Version: 1.11.0
# Author: Systems Architect AI
# Description: A lightweight, self-contained Twitch client for Ubuntu-based systems.
# Changelog:
#   1.11.0: - Added optional local emote rendering from /emotes subfolder.
#           - Emotes can be toggled on/off via a "Show Emotes" checkbox.
#           - Emote mappings loaded from emotes.json file.
#           - Emotes are displayed inline with chat messages using Tkinter PhotoImage.
#   1.10.0: - Reworked fullscreen toggle to make the video player truly fullscreen
#             by hiding other UI elements, correcting the previous "maximize" behavior.
#   1.9.0:  - Implemented a fullscreen toggle, bound to the <Escape> key.
#           - Added a label to the UI to inform users of the new keybinding.
#   1.8.0:  - Added optional, colored timestamps to the chat box, which can be
#             toggled on/off via a checkbox. Timestamp color is adjusted for
#             readability in both light and dark modes.
#   1.7.0:  - Added a dark mode toggle for the chat box. Usernames remain blue
#             in both light and dark modes for consistent readability.
#   1.6.0:  - Implemented graceful handling for when a stream ends. The app no
#             longer crashes and now displays a "Stream has ended" message.
#           - Instantiated VLC with --ignore-config and --no-osd flags to ensure
#             a neutral video output, unaffected by local VLC settings.

import os
import sys
import socket
import subprocess
import threading
import queue
import time
import json
import re
from pathlib import Path
import signal

# --- Virtual Environment and Dependency Management ---

VENV_DIR = ".venv"
REQUIREMENTS = ["python-vlc", "python-dotenv", "yt-dlp", "Pillow"]

def handle_venv():
    """
    Ensures the script runs inside a virtual environment, creating it and
    installing dependencies if necessary. Re-launches the script inside the
    venv if it's not already running there.
    """
    in_venv = (sys.prefix != sys.base_prefix)
    if in_venv:
        return

    print("--- VENV SETUP REQUIRED ---")
    venv_path = Path(VENV_DIR)
    script_path = Path(__file__).resolve()

    if sys.platform == "win32":
        venv_python = venv_path / "Scripts" / "python.exe"
    else:
        venv_python = venv_path / "bin" / "python"

    if not venv_path.exists():
        print(f"INFO: Creating virtual environment at '{venv_path.resolve()}'...")
        try:
            python_executable = sys.executable
            subprocess.run([python_executable, "-m", "venv", VENV_DIR], check=True)
            print("INFO: Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"FATAL: Failed to create virtual environment. Error: {e}")
            sys.exit(1)

    print(f"INFO: Installing/verifying packages into '{venv_python}'...")
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install"] + REQUIREMENTS,
            check=True, capture_output=True, text=True
        )
        print("INFO: All required packages are installed/verified.")
    except subprocess.CalledProcessError as e:
        stderr_lower = e.stderr.lower()
        if "failed to establish a new connection" in stderr_lower or "temporary failure in name resolution" in stderr_lower:
             print("FATAL: A network error occurred while installing dependencies.")
             print("       Could not connect to the Python Package Index (PyPI) to download packages.")
             print("       Please check your internet connection, DNS settings, and firewall configuration.")
        else:
            print(f"FATAL: Failed to install dependencies. Error: {e.stderr}")
        sys.exit(1)


    print(f"INFO: Re-launching script '{script_path.name}' inside the virtual environment...")
    os.execv(str(venv_python), [str(venv_python), str(script_path)])


def run_app():
    """
    Contains the main application logic. This function is only called after
    the virtual environment is verified and all dependencies are installed.
    """
    # --- Application-Specific Imports ---
    try:
        import tkinter as tk
        from tkinter import messagebox, TclError
        import vlc
        from dotenv import load_dotenv
        from PIL import Image, ImageTk
    except ImportError as e:
        print(f"FATAL: A required library could not be imported: {e}")
        sys.exit(1)


    # --- Application Classes ---

    class TwitchIRCClient(threading.Thread):
        """
        A threaded client to connect to Twitch IRC and listen for chat messages.
        """
        def __init__(self, nickname, token, channel, message_queue):
            super().__init__(daemon=True)
            self.nickname = nickname
            self.token = token
            self.channel = channel.lower()
            self.message_queue = message_queue
            self.server = "irc.chat.twitch.tv"
            self.port = 6667
            self.sock = None
            self._stop_event = threading.Event()

        def run(self):
            """Main loop for the IRC client thread."""
            print(f"INFO: IRC client thread started for channel '{self.channel}'.")
            try:
                self.sock = socket.socket()
                self.sock.connect((self.server, self.port))

                pass_cmd = f"PASS oauth:{self.token}\r\n"
                nick_cmd = f"NICK {self.nickname}\r\n"
                join_cmd = f"JOIN #{self.channel}\r\n"

                self.sock.send(pass_cmd.encode("utf-8"))
                self.sock.send(nick_cmd.encode("utf-8"))
                self.sock.send(join_cmd.encode("utf-8"))

                print("INFO: Authenticated and joined Twitch IRC channel.")

                while not self._stop_event.is_set():
                    try:
                        self.sock.settimeout(1.0)
                        resp = self.sock.recv(2048).decode("utf-8")

                        if not resp:
                            self.message_queue.put("System: Connection closed by server.")
                            break

                        if resp.startswith("PING"):
                            self.sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                        elif "PRIVMSG" in resp and f"PRIVMSG #{self.channel}" in resp:
                            try:
                                # Only process actual chat messages for our channel
                                username = resp.split('!')[0][1:]
                                message = resp.split(f'PRIVMSG #{self.channel}')[1].split(':', 1)[1].strip()
                                formatted_message = f"{username}: {message}"
                                self.message_queue.put(formatted_message)
                            except (IndexError, ValueError):
                                pass
                    except socket.timeout:
                        continue
                    except Exception as e:
                        self.message_queue.put(f"System: IRC Error - {e}")
                        break

            except Exception as e:
                error_msg = f"System: Failed to connect to Twitch IRC. Error: {e}"
                print(f"ERROR: {error_msg}")
                self.message_queue.put(error_msg)
            finally:
                if self.sock:
                    self.sock.close()
                print("INFO: IRC client thread has stopped.")

        def stop(self):
            """Signals the thread to stop."""
            self._stop_event.set()
            print("INFO: Stop signal sent to IRC client thread.")


    class TwitchApp:
        """
        The main application class for the Tkinter GUI.
        """
        def __init__(self, root):
            self.root = root
            self.root.title("Twitchy")
            self.root.geometry("1024x768")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.bind("<Escape>", self.toggle_fullscreen)

            if not self.load_config():
                self.root.destroy()
                return

            self.vlc_instance = None
            self.vlc_player = None
            self.vlc_event_manager = None
            self.irc_thread = None
            self.message_queue = queue.Queue()
            self.is_fullscreen = False

            # --- Emote System ---
            self.emote_dict = {}
            self.emote_images = {}
            self.load_emotes()

            # --- Define color schemes and UI state variables ---
            self.light_mode_colors = {
                'bg': 'white', 'fg': 'black', 'system_fg': 'gray', 'timestamp_fg': '#228B22'
            }
            self.dark_mode_colors = {
                'bg': '#2E2E2E', 'fg': '#CCCCCC', 'system_fg': '#888888', 'timestamp_fg': '#8FBC8F'
            }
            self.dark_mode_var = tk.BooleanVar(value=False)
            self.timestamps_var = tk.BooleanVar(value=False)
            self.emotes_var = tk.BooleanVar(value=True)

            self.create_widgets()
            self.poll_message_queue()

        def load_emotes(self):
            """Loads emote mappings from emotes.json and prepares image cache."""
            emotes_json_path = Path("emotes.json")
            if not emotes_json_path.is_file():
                print("WARNING: emotes.json not found. Emote rendering will be disabled.")
                return

            try:
                with open(emotes_json_path, 'r', encoding='utf-8') as f:
                    self.emote_dict = json.load(f)
                print(f"INFO: Loaded {len(self.emote_dict)} emote mappings from emotes.json")
            except Exception as e:
                print(f"WARNING: Failed to load emotes.json: {e}")
                return

            # Pre-load and cache emote images
            for emote_name, emote_path in self.emote_dict.items():
                full_path = Path(emote_path)
                if full_path.is_file():
                    try:
                        # Load and resize emote to reasonable chat size
                        img = Image.open(full_path)
                        img = img.resize((28, 28), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.emote_images[emote_name] = photo
                    except Exception as e:
                        print(f"WARNING: Failed to load emote {emote_name} from {emote_path}: {e}")
                else:
                    print(f"WARNING: Emote file not found: {emote_path}")

            print(f"INFO: Successfully cached {len(self.emote_images)} emote images")

        def load_config(self):
            """Loads configuration from .env file."""
            print("INFO: Loading configuration from .env file.")
            env_path = Path(".env")
            if not env_path.is_file():
                messagebox.showerror(
                    "Configuration Error",
                    "The .env file was not found in the script's directory.\n\n"
                    "Please create a .env file with:\n"
                    "TWITCH_OAUTH_TOKEN=your_token_here\n"
                    "TWITCH_NICKNAME=your_twitch_username"
                )
                return False

            load_dotenv(dotenv_path=env_path)
            self.TWITCH_OAUTH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")
            self.TWITCH_NICKNAME = os.getenv("TWITCH_NICKNAME")

            if not self.TWITCH_OAUTH_TOKEN or not self.TWITCH_NICKNAME:
                messagebox.showerror(
                    "Configuration Error",
                    "TWITCH_OAUTH_TOKEN or TWITCH_NICKNAME is missing from the .env file."
                )
                return False

            print("INFO: Configuration loaded successfully.")
            return True

        def create_widgets(self):
            """Creates and arranges all the GUI widgets."""
            self.control_frame = tk.Frame(self.root)
            self.control_frame.pack(fill=tk.X, padx=5, pady=5)

            channel_label = tk.Label(self.control_frame, text="Twitch Channel:")
            channel_label.pack(side=tk.LEFT, padx=(0, 5))

            self.channel_entry = tk.Entry(self.control_frame)
            self.channel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.channel_entry.bind("<Return>", self.load_stream)

            self.load_button = tk.Button(self.control_frame, text="Load Stream", command=self.load_stream)
            self.load_button.pack(side=tk.LEFT, padx=(5, 0))

            self.volume_var = tk.IntVar(value=100)
            self.volume_slider = tk.Scale(
                self.control_frame,
                from_=0, to=100, orient=tk.HORIZONTAL,
                variable=self.volume_var, command=self.set_volume,
                label="Volume", length=150, state=tk.DISABLED
            )
            self.volume_slider.pack(side=tk.LEFT, padx=(10, 0))

            # Second row for checkboxes
            self.options_frame = tk.Frame(self.root)
            self.options_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

            self.dark_mode_toggle = tk.Checkbutton(
                self.options_frame, text="Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode
            )
            self.dark_mode_toggle.pack(side=tk.LEFT, padx=(0, 5))

            self.timestamps_toggle = tk.Checkbutton(
                self.options_frame, text="Show Timestamps", variable=self.timestamps_var
            )
            self.timestamps_toggle.pack(side=tk.LEFT, padx=(0, 5))

            self.emotes_toggle = tk.Checkbutton(
                self.options_frame, text="Show Emotes", variable=self.emotes_var
            )
            self.emotes_toggle.pack(side=tk.LEFT, padx=(0, 5))

            fullscreen_label = tk.Label(self.options_frame, text="(ESC to toggle fullscreen)", fg="grey")
            fullscreen_label.pack(side=tk.RIGHT, padx=(10, 0))

            self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
            self.main_pane.pack(fill=tk.BOTH, expand=True)

            self.video_frame = tk.Frame(self.main_pane, bg="black")
            self.main_pane.add(self.video_frame, width=800)

            self.chat_frame = tk.Frame(self.main_pane)
            self.main_pane.add(self.chat_frame, width=224)

            chat_scrollbar = tk.Scrollbar(self.chat_frame)
            chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self.chat_box = tk.Text(
                self.chat_frame, wrap=tk.WORD, state=tk.DISABLED,
                yscrollcommand=chat_scrollbar.set,
                background=self.light_mode_colors['bg'],
                foreground=self.light_mode_colors['fg']
            )
            self.chat_box.pack(fill=tk.BOTH, expand=True)
            chat_scrollbar.config(command=self.chat_box.yview)

            self.chat_box.tag_configure('username_color', foreground="#3465A4")
            self.chat_box.tag_configure('system_message', foreground=self.light_mode_colors['system_fg'])
            self.chat_box.tag_configure('timestamp_color', foreground=self.light_mode_colors['timestamp_fg'])

        def toggle_fullscreen(self, event=None):
            """Toggles video fullscreen by hiding/showing UI elements."""
            self.is_fullscreen = not self.is_fullscreen
            self.root.attributes("-fullscreen", self.is_fullscreen)
            
            if self.is_fullscreen:
                # Entering fullscreen: hide controls and chat
                self.control_frame.pack_forget()
                self.options_frame.pack_forget()
                self.main_pane.forget(self.chat_frame)
                print("INFO: Video fullscreen enabled.")
            else:
                # Exiting fullscreen: restore controls and chat
                self.control_frame.pack(fill=tk.X, padx=5, pady=5, before=self.main_pane)
                self.options_frame.pack(fill=tk.X, padx=5, pady=(0, 5), before=self.main_pane)
                self.main_pane.add(self.chat_frame)
                # Ensure sash is visible and positioned reasonably
                try:
                    # Attempt to restore a reasonable sash position
                    self.main_pane.sash_place(0, self.root.winfo_width() - 250, 0)
                except TclError:
                    # Fallback if sash cannot be placed (e.g., window not fully mapped)
                    pass
                print("INFO: Video fullscreen disabled.")

        def toggle_dark_mode(self):
            """Switches the chat box color scheme between light and dark."""
            is_dark = self.dark_mode_var.get()
            colors = self.dark_mode_colors if is_dark else self.light_mode_colors

            print(f"INFO: Toggling chat theme to {'Dark' if is_dark else 'Light'} Mode.")
            self.chat_box.config(background=colors['bg'], foreground=colors['fg'])
            self.chat_box.tag_configure('system_message', foreground=colors['system_fg'])
            self.chat_box.tag_configure('timestamp_color', foreground=colors['timestamp_fg'])

        def set_volume(self, volume_level):
            """Callback function for the volume slider."""
            if self.vlc_player:
                try:
                    self.vlc_player.audio_set_volume(int(volume_level))
                except (ValueError, TclError):
                    pass

        def load_stream(self, event=None):
            """Fetches stream URL, starts video playback, and connects to chat."""
            raw_input = self.channel_entry.get().strip()
            if not raw_input:
                messagebox.showwarning("Input Error", "Please enter a Twitch channel name or URL.")
                return

            channel = raw_input
            if "twitch.tv/" in channel.lower():
                try:
                    channel = channel.rstrip('/').split('/')[-1]
                except IndexError:
                    messagebox.showerror("Input Error", f"Could not parse channel name from URL:\n{raw_input}")
                    return

            if not channel:
                messagebox.showerror("Input Error", f"Could not parse a valid channel name from:\n{raw_input}")
                return

            print(f"INFO: Attempting to load stream for channel: '{channel}' (from input: '{raw_input}')")
            self.load_button.config(state=tk.DISABLED, text="Loading...")
            self.root.update_idletasks()

            self.stop_current_stream()

            stream_url = self.get_stream_url(channel)
            if not stream_url:
                messagebox.showerror("Stream Error", f"Could not get stream URL for '{channel}'.\nCheck if the channel is live and the name is correct.")
                self.load_button.config(state=tk.NORMAL, text="Load Stream")
                return

            try:
                self.vlc_instance = vlc.Instance("--ignore-config", "--no-osd")
                self.vlc_player = self.vlc_instance.media_player_new()
                self.vlc_player.set_xwindow(self.video_frame.winfo_id())

                self.vlc_event_manager = self.vlc_player.event_manager()
                self.vlc_event_manager.event_attach(
                    vlc.EventType.MediaPlayerEndReached,
                    self.handle_stream_end
                )

                media = self.vlc_instance.media_new(stream_url)
                self.vlc_player.set_media(media)
                self.vlc_player.play()
                self.set_volume(self.volume_var.get())
                self.volume_slider.config(state=tk.NORMAL)
                print(f"INFO: VLC player started for stream: {stream_url}")
            except Exception as e:
                messagebox.showerror("VLC Error", f"Failed to start VLC player. Error: {e}\n\nEnsure VLC is installed on your system.")
                self.load_button.config(state=tk.NORMAL, text="Load Stream")
                return

            self.message_queue = queue.Queue()
            self.clear_chat_box()
            self.irc_thread = TwitchIRCClient(
                self.TWITCH_NICKNAME,
                self.TWITCH_OAUTH_TOKEN,
                channel,
                self.message_queue
            )
            self.irc_thread.start()

            self.load_button.config(state=tk.NORMAL, text="Load Stream")

        def get_stream_url(self, channel):
            """Uses yt-dlp to get the direct stream URL."""
            twitch_url = f"https://www.twitch.tv/{channel}"
            print(f"INFO: Running yt-dlp to get stream URL for {twitch_url}")
            try:
                command = ["yt-dlp", "-f", "best", "-g", twitch_url]
                result = subprocess.run(
                    command,
                    capture_output=True, text=True, check=True, timeout=15
                )
                stream_url = result.stdout.strip()
                if not stream_url.startswith("http"):
                    print(f"ERROR: yt-dlp returned an invalid URL: {stream_url}")
                    return None
                return stream_url
            except FileNotFoundError:
                print("ERROR: yt-dlp command not found. Is it installed in the venv?")
                return None
            except subprocess.CalledProcessError as e:
                print(f"ERROR: yt-dlp failed. Error: {e.stderr.strip()}")
                return None
            except subprocess.TimeoutExpired:
                print("ERROR: yt-dlp command timed out.")
                return None

        def poll_message_queue(self):
            """Periodically checks the queue for new messages from the IRC thread."""
            try:
                while True:
                    message = self.message_queue.get_nowait()
                    self.add_message_to_chat(message)
            except queue.Empty:
                pass
            finally:
                self.root.after(100, self.poll_message_queue)

        def parse_message_with_emotes(self, message_text):
            """
            Parses a message and returns a list of tuples: (type, content)
            where type is either 'text' or 'emote', and content is the string or emote name.
            """
            if not self.emotes_var.get() or not self.emote_images:
                return [('text', message_text)]

            # Build regex pattern to match emote names
            # Sort by length descending to match longer emotes first
            emote_names = sorted(self.emote_images.keys(), key=len, reverse=True)
            # Escape special regex characters in emote names
            escaped_names = [re.escape(name) for name in emote_names]
            pattern = '|'.join(escaped_names)
            
            if not pattern:
                return [('text', message_text)]

            result = []
            last_end = 0
            
            for match in re.finditer(pattern, message_text):
                # Add text before the emote
                if match.start() > last_end:
                    result.append(('text', message_text[last_end:match.start()]))
                
                # Add the emote
                result.append(('emote', match.group()))
                last_end = match.end()
            
            # Add remaining text after last emote
            if last_end < len(message_text):
                result.append(('text', message_text[last_end:]))
            
            return result if result else [('text', message_text)]

        def add_message_to_chat(self, message):
            """Appends a message to the chat box, with optional timestamp and emotes, and scrolls."""
            self.chat_box.config(state=tk.NORMAL)

            # Add timestamp if enabled
            if self.timestamps_var.get():
                timestamp_str = f"[{time.strftime('%H:%M:%S')}] "
                self.chat_box.insert(tk.END, timestamp_str, 'timestamp_color')

            try:
                if message.startswith("System:"):
                    self.chat_box.insert(tk.END, message + "\n", 'system_message')
                elif ': ' in message:
                    separator_index = message.index(': ')
                    username_part = message[:separator_index + 1]
                    message_part = message[separator_index + 1:]
                    
                    # Insert username
                    self.chat_box.insert(tk.END, username_part, 'username_color')
                    
                    # Parse and insert message with emotes
                    parsed = self.parse_message_with_emotes(message_part)
                    for item_type, content in parsed:
                        if item_type == 'text':
                            self.chat_box.insert(tk.END, content)
                        elif item_type == 'emote' and content in self.emote_images:
                            self.chat_box.image_create(tk.END, image=self.emote_images[content])
                    
                    self.chat_box.insert(tk.END, "\n")
                else:
                    self.chat_box.insert(tk.END, message + "\n")
            except ValueError:
                self.chat_box.insert(tk.END, message + "\n")

            self.chat_box.config(state=tk.DISABLED)
            self.chat_box.see(tk.END)

        def clear_chat_box(self):
            """Clears all text from the chat box."""
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.delete('1.0', tk.END)
            self.chat_box.config(state=tk.DISABLED)

        def stop_current_stream(self):
            """Stops the VLC player and the IRC client thread if they are running."""
            if self.vlc_event_manager:
                self.vlc_event_manager.event_detach(vlc.EventType.MediaPlayerEndReached)
                self.vlc_event_manager = None

            if self.vlc_player:
                print("INFO: Stopping VLC player.")
                self.vlc_player.stop()
                self.vlc_player = None
                self.vlc_instance = None
                self.volume_slider.config(state=tk.DISABLED)

            if self.irc_thread and self.irc_thread.is_alive():
                print("INFO: Stopping IRC client thread.")
                self.irc_thread.stop()
                self.irc_thread.join(timeout=2)
            self.irc_thread = None

        def handle_stream_end(self, event):
            """
            VLC event handler for when the media ends.
            Schedules cleanup to run on the main thread.
            """
            print("INFO: VLC 'MediaPlayerEndReached' event triggered.")
            self.root.after(0, self.cleanup_after_stream_end)

        def cleanup_after_stream_end(self):
            """
            Performs cleanup tasks on the main thread after a stream has ended.
            """
            print("INFO: Running cleanup routine after stream ended.")
            self.add_message_to_chat("System: Stream has ended.")
            self.stop_current_stream()
            self.load_button.config(state=tk.NORMAL, text="Load Stream")


        def on_closing(self):
            """Handles the application closing event."""
            print("INFO: Close button clicked. Shutting down.")
            self.stop_current_stream()
            try:
                self.root.destroy()
            except TclError:
                pass


    # --- Main Execution Logic ---
    def signal_handler(sig, frame):
        print("\nINFO: Ctrl+C detected. Exiting gracefully.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        root = tk.Tk()
        app = TwitchApp(root)
        if root.winfo_exists():
            root.mainloop()
        else:
            print("INFO: Application failed to initialize. Exiting.")
            sys.exit(1)
    except Exception as e:
        print(f"FATAL: An unhandled exception occurred in the main application: {e}")
        try:
            messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n\n{e}\n\nThe application will now close.")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    handle_venv()
    run_app()

