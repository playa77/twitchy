# twitch_app.py
# Version: 1.2.0
# Author: Systems Architect AI
# Description: A lightweight, self-contained Twitch client for Ubuntu-based systems.
# Changelog:
#   1.2.0: - Fixed infinite re-launch loop by replacing the unreliable
#            `os.environ.get("VIRTUAL_ENV")` check with the more robust
#            `sys.prefix != sys.base_prefix` comparison. This correctly
#            detects when the script is running inside the venv.
#          - Added comprehensive and precise logging to the venv handling
#            function to improve transparency during the startup phase.
#   1.1.0: - Refactored startup logic to ensure venv setup completes before
#            dependent libraries (VLC, DotEnv, etc.) are imported.

import os
import sys
import socket
import subprocess
import threading
import queue
import time
from pathlib import Path
import signal

# --- Virtual Environment and Dependency Management ---

VENV_DIR = ".venv"
REQUIREMENTS = ["python-vlc", "python-dotenv", "yt-dlp"]

def handle_venv():
    """
    Ensures the script runs inside a virtual environment, creating it and
    installing dependencies if necessary. Re-launches the script inside the
    venv if it's not already running there.
    """
    print("--- VENV CHECK INITIATED ---")
    print(f"DEBUG: sys.prefix = {sys.prefix}")
    print(f"DEBUG: sys.base_prefix = {sys.base_prefix}")

    # The most reliable check for being in a venv is to see if the current
    # executable's path (sys.prefix) is different from the base system Python.
    in_venv = (sys.prefix != sys.base_prefix)

    if in_venv:
        print("INFO: Already running in a virtual environment. Proceeding.")
        print("--- VENV CHECK COMPLETED ---")
        return

    print("INFO: Not running in a virtual environment. Setup required.")
    venv_path = Path(VENV_DIR)
    script_path = Path(__file__).resolve()

    # Determine the python executable path within the venv
    if sys.platform == "win32":
        venv_python = venv_path / "Scripts" / "python.exe"
    else:
        venv_python = venv_path / "bin" / "python"

    if not venv_path.exists():
        print(f"INFO: Creating virtual environment at '{venv_path.resolve()}'...")
        try:
            # Use the base python executable to create the venv
            python_executable = sys.executable
            subprocess.run([python_executable, "-m", "venv", VENV_DIR], check=True)
            print("INFO: Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"FATAL: Failed to create virtual environment. Error: {e}")
            sys.exit(1)
    else:
        print("INFO: Virtual environment directory already exists.")

    print(f"INFO: Using venv Python executable: {venv_python}")
    print("INFO: Installing/verifying required packages...")
    try:
        # Use capture_output=True to hide the verbose pip output unless there's an error
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install"] + REQUIREMENTS,
            check=True,
            capture_output=True,
            text=True
        )
        # Log stdout from pip for confirmation, even on success.
        if result.stdout:
            print(f"DEBUG: pip install stdout:\n{result.stdout.strip()}")
        print("INFO: All required packages are installed/verified.")
    except subprocess.CalledProcessError as e:
        print(f"FATAL: Failed to install dependencies. Error: {e.stderr}")
        sys.exit(1)

    print(f"INFO: Re-launching script '{script_path.name}' inside the virtual environment...")
    print("--- END OF CURRENT PROCESS ---")
    # Replace the current process with a new one running in the venv
    os.execv(str(venv_python), [str(venv_python), str(script_path)])


def run_app():
    """
    Contains the main application logic. This function is only called after
    the virtual environment is verified and all dependencies are installed.
    """
    # --- Application-Specific Imports ---
    # These are safe to import now.
    try:
        import tkinter as tk
        from tkinter import messagebox, TclError
        import vlc
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"FATAL: A required library could not be imported: {e}")
        print("This should not happen if the venv setup was successful.")
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

                # Note: Twitch requires the "oauth:" prefix for the PASS command.
                pass_cmd = f"PASS oauth:{self.token}\r\n"
                nick_cmd = f"NICK {self.nickname}\r\n"
                join_cmd = f"JOIN #{self.channel}\r\n"

                self.sock.send(pass_cmd.encode("utf-8"))
                self.sock.send(nick_cmd.encode("utf-8"))
                self.sock.send(join_cmd.encode("utf-8"))

                print("INFO: Authenticated and joined Twitch IRC channel.")

                while not self._stop_event.is_set():
                    try:
                        # Set a timeout to allow the loop to check the stop event
                        self.sock.settimeout(1.0)
                        resp = self.sock.recv(2048).decode("utf-8")

                        if not resp:
                            # Connection closed by server
                            self.message_queue.put("System: Connection closed by server.")
                            break

                        if resp.startswith("PING"):
                            self.sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                        elif "PRIVMSG" in resp:
                            # Format: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message
                            try:
                                username = resp.split('!')[0][1:]
                                message = resp.split('PRIVMSG #')[1].split(':', 1)[1].strip()
                                formatted_message = f"{username}: {message}"
                                self.message_queue.put(formatted_message)
                            except IndexError:
                                # Not a standard chat message, ignore
                                pass
                    except socket.timeout:
                        continue # Go back to the start of the loop to check stop_event
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
            self.root.title("Minimalist Python Twitch Client")
            self.root.geometry("1024x768")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # --- Load Configuration ---
            self.TWITCH_OAUTH_TOKEN = None
            self.TWITCH_NICKNAME = None
            if not self.load_config():
                # Error is shown in the method, just exit
                self.root.destroy()
                return

            # --- Class Members ---
            self.vlc_instance = None
            self.vlc_player = None
            self.irc_thread = None
            self.message_queue = queue.Queue()

            # --- GUI Setup ---
            self.create_widgets()

            # Start polling the message queue
            self.poll_message_queue()

        def load_config(self):
            """Loads configuration from .env file."""
            print("INFO: Loading configuration from .env file.")
            env_path = Path(".env")
            if not env_path.is_file():
                messagebox.showerror(
                    "Configuration Error",
                    "The .env file was not found in the script's directory.\n\n"
                    "Please create a .env file with the following content:\n"
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
            # --- Top Control Frame ---
            control_frame = tk.Frame(self.root)
            control_frame.pack(fill=tk.X, padx=5, pady=5)

            channel_label = tk.Label(control_frame, text="Twitch Channel:")
            channel_label.pack(side=tk.LEFT, padx=(0, 5))

            self.channel_entry = tk.Entry(control_frame)
            self.channel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.channel_entry.bind("<Return>", self.load_stream) # Allow pressing Enter

            self.load_button = tk.Button(control_frame, text="Load Stream", command=self.load_stream)
            self.load_button.pack(side=tk.LEFT, padx=(5, 0))

            # --- Main Content PanedWindow ---
            main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
            main_pane.pack(fill=tk.BOTH, expand=True)

            # --- Video Frame ---
            self.video_frame = tk.Frame(main_pane, bg="black")
            self.video_frame.pack(fill=tk.BOTH, expand=True)
            main_pane.add(self.video_frame, width=800) # Initial width

            # --- Chat Frame ---
            chat_frame = tk.Frame(main_pane)
            chat_frame.pack(fill=tk.BOTH, expand=True)
            main_pane.add(chat_frame, width=224) # Initial width

            chat_scrollbar = tk.Scrollbar(chat_frame)
            chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self.chat_box = tk.Text(
                chat_frame,
                wrap=tk.WORD,
                state=tk.DISABLED, # Read-only
                yscrollcommand=chat_scrollbar.set
            )
            self.chat_box.pack(fill=tk.BOTH, expand=True)
            chat_scrollbar.config(command=self.chat_box.yview)

        def load_stream(self, event=None):
            """Fetches stream URL, starts video playback, and connects to chat."""
            channel = self.channel_entry.get().strip()
            if not channel:
                messagebox.showwarning("Input Error", "Please enter a Twitch channel name.")
                return

            print(f"INFO: Attempting to load stream for channel: {channel}")
            self.load_button.config(state=tk.DISABLED, text="Loading...")
            self.root.update_idletasks()

            # --- Stop existing processes first ---
            self.stop_current_stream()

            # --- Get Stream URL with yt-dlp ---
            stream_url = self.get_stream_url(channel)
            if not stream_url:
                messagebox.showerror("Stream Error", f"Could not get stream URL for '{channel}'.\nCheck if the channel is live and the name is correct.")
                self.load_button.config(state=tk.NORMAL, text="Load Stream")
                return

            # --- Start VLC Player ---
            try:
                self.vlc_instance = vlc.Instance("--no-xlib")
                self.vlc_player = self.vlc_instance.media_player_new()
                media = self.vlc_instance.media_new(stream_url)
                # Important: Set HWND/XWindow ID before playing
                # For Linux/Ubuntu, we use set_xwindow
                self.vlc_player.set_xwindow(self.video_frame.winfo_id())
                self.vlc_player.set_media(media)
                self.vlc_player.play()
                print(f"INFO: VLC player started for stream: {stream_url}")
            except Exception as e:
                messagebox.showerror("VLC Error", f"Failed to start VLC player. Error: {e}\n\nEnsure VLC is installed on your system.")
                self.load_button.config(state=tk.NORMAL, text="Load Stream")
                return

            # --- Start IRC Client ---
            self.message_queue = queue.Queue() # Clear queue for new channel
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
                # We want the best quality stream URL
                command = ["yt-dlp", "-f", "best", "-g", twitch_url]
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=15
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
                # Schedule the next check
                self.root.after(100, self.poll_message_queue)

        def add_message_to_chat(self, message):
            """Appends a message to the chat box and scrolls down."""
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.insert(tk.END, message + "\n")
            self.chat_box.config(state=tk.DISABLED)
            self.chat_box.see(tk.END) # Auto-scroll

        def clear_chat_box(self):
            """Clears all text from the chat box."""
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.delete('1.0', tk.END)
            self.chat_box.config(state=tk.DISABLED)

        def stop_current_stream(self):
            """Stops the VLC player and the IRC client thread if they are running."""
            if self.vlc_player:
                print("INFO: Stopping VLC player.")
                self.vlc_player.stop()
                self.vlc_player = None
                self.vlc_instance = None

            if self.irc_thread and self.irc_thread.is_alive():
                print("INFO: Stopping IRC client thread.")
                self.irc_thread.stop()
                self.irc_thread.join(timeout=2) # Wait for thread to finish
            self.irc_thread = None

        def on_closing(self):
            """Handles the application closing event."""
            print("INFO: Close button clicked. Shutting down.")
            self.stop_current_stream()
            try:
                self.root.destroy()
            except TclError:
                # Can happen if the window is already being destroyed
                pass

    # --- Main Execution Logic ---

    # Set up signal handler for Ctrl+C
    def signal_handler(sig, frame):
        print("\nINFO: Ctrl+C detected. Exiting gracefully.")
        # Since this handler runs outside the Tkinter main loop,
        # we need a safe way to shut down. We'll just exit.
        # The daemon threads will be terminated automatically.
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Run the Tkinter application
    try:
        root = tk.Tk()
        app = TwitchApp(root)
        if not root.winfo_exists(): # Check if window was destroyed during init
            print("INFO: Application failed to initialize. Exiting.")
            sys.exit(1)
        root.mainloop()
    except Exception as e:
        print(f"FATAL: An unhandled exception occurred in the main application: {e}")
        # Use a fallback message box if Tkinter is still usable
        try:
            messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n\n{e}\n\nThe application will now close.")
        except Exception:
            pass # If Tkinter is broken, we can't show a message box.
        sys.exit(1)


if __name__ == "__main__":
    # First, ensure we are in a properly configured virtual environment.
    # This will either continue execution or re-launch the script.
    handle_venv()

    # If handle_venv() returns, we are guaranteed to be in the correct venv.
    # Now, we can run the main application logic which performs the
    # necessary (and now safe) imports.
    run_app()
