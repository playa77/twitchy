# README.md
## Introduction
A lightweight, self-contained Twitch client for Ubuntu-based systems. This application allows users to watch Twitch streams, read chat, and customize their viewing experience with features like dark mode, timestamps, and emote rendering.

## Features

* Watch live Twitch streams
* Read chat with real-time message updates
* Customize the application with dark mode, timestamp display, and emote rendering
* Support for optional local emote rendering from the `/emotes` subfolder
* Fullscreen toggle with the <Escape> key
* Volume control with a slider
* Error handling for stream connection issues, VLC player errors, and IRC client errors

## Prerequisites
* Python 3.x
* Ubuntu-based system
* VLC media player installed
* yt-dlp installed (for stream URL retrieval)
* A Twitch account with a valid OAuth token

## Setup
1. Clone the repository or download the script.
2. Create a `.env` file in the script's directory with your Twitch OAuth token and nickname:
   ```
   TWITCH_OAUTH_TOKEN=your_token_here
   TWITCH_NICKNAME=your_twitch_username
   ```
3. Run the `twitch_app.py` script. The application will create a virtual environment, install dependencies, and launch the GUI.

## Usage
1. Enter a Twitch channel name or URL in the input field.
2. Click the "Load Stream" button to start the stream.
3. Use the volume slider to adjust the volume.
4. Toggle dark mode, timestamp display, and emote rendering using the checkboxes.
5. Use the Esc key to toggle fullscreen mode.
6. Close the application by clicking the close button or pressing Ctrl+C.

## Troubleshooting
* If the application fails to connect to the stream, check your internet connection and Twitch account status.
* If the VLC player fails to start, ensure that VLC is installed and configured correctly on your system.
* If the IRC client fails to connect, check your Twitch OAuth token and nickname.

## Changelog
See the `twitch_app.py` script for the detailed changelog.

## Notes
* This application is designed to be lightweight and efficient. However, it may consume significant system resources depending on the stream quality and system configuration.
* The application uses a virtual environment to manage dependencies. Ensure that the virtual environment is properly cleaned up after use.
