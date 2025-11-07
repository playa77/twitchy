# Minimalist Python Twitch Client

A lightweight, self-contained, GUI-based Twitch.tv client for Debian/Ubuntu-based Linux distributions. This application provides a simple interface to watch streams and follow chat without the overhead of a web browser.

## Features

- **Lightweight Playback:** Uses an embedded VLC instance for efficient video playback.
- **Simple UI:** A clean, single-window interface with a video player and a read-only chat box.
- **Flexible Input:** Accepts both channel names (e.g., `shroud`) and full Twitch URLs.
- **Volume Control:** An integrated slider to adjust stream volume.
- **Readable Chat:** Usernames are colored to be easily distinguishable from messages.
- **Self-Contained:** The script automatically creates its own Python virtual environment and installs all necessary dependencies on first run.

## Requirements

Before running the script, you need to have the following installed on your system:

1.  **Python 3.8+**
2.  **VLC Media Player:** The application requires VLC to be installed.
    ```bash
    sudo apt-get update
    sudo apt-get install vlc
    ```
3.  **Tkinter:** This is the standard GUI library for Python and is often included. If not, you can install it.
    ```bash
    sudo apt-get install python3-tk
    ```

## Setup

1.  **Download the Script:** Save the `twitch_app.py` script to a directory of your choice.

2.  **Create the `.env` file:** In the same directory as the script, create a file named `.env`. This file will store your Twitch credentials.

3.  **Add Your Credentials:** Open the `.env` file and add your Twitch OAuth token and username in the following format.

    ```env
    # Get your token from a site like https://twitchapps.com/tmi/
    # IMPORTANT: Do NOT include the "oauth:" prefix in the token string.
    TWITCH_OAUTH_TOKEN=your_long_alphanumeric_token_here

    # Your Twitch username, preferably in all lowercase.
    TWITCH_NICKNAME=your_twitch_username
    ```

## Usage

To run the application, simply execute the script with Python 3:

```bash
python3 twitch_app.py
