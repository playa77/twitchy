# Minimalist Python Twitch Client

A lightweight, self-contained, GUI-based Twitch client for Debian/Ubuntu-based Linux distributions. This application provides a simple interface for watching Twitch streams and reading chat without the overhead of a web browser.

## Features

*   **All-In-One Script:** Runs from a single Python file with no manual setup required.
*   **Automatic Dependency Management:** Automatically creates a virtual environment and installs necessary packages on first launch.
*   **Video and Chat:** A clean, two-pane view for video playback and a read-only chat box.
*   **Neutral Video Playback:** Ensures that your local VLC settings do not alter the stream's color or add overlays.
*   **Robust Stream Handling:** Gracefully handles when a stream ends, preventing application crashes.
*   **Customizable Chat:**
    *   Toggleable Dark Mode for comfortable viewing.
    *   Toggleable `[HH:MM:SS]` timestamps for each message.
    *   Colored usernames for improved readability.
*   **Simple Controls:** Load streams by channel name or full URL, and adjust volume with a slider.

## Requirements

Before running the script, you must have the following system packages installed:
*   `python3`
*   `python3-venv`
*   `vlc`

You can install them on a Debian/Ubuntu system with the command:
```bash
sudo apt-get update && sudo apt-get install -y python3 python3-venv vlc
