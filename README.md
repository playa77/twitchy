# Minimalist Python Twitch Client

**Status:** Stable, In Development (v1.10.0)

A lightweight, self-contained, GUI-based Twitch.tv client for Debian/Ubuntu-based Linux distributions. This application provides a simple interface for watching streams and reading chat without the need for a web browser, focusing on efficiency and minimal resource usage.

![Application Screenshot](screenshot.png)
*(A screenshot of the application running)*

## Features

- **Self-Contained:** The script automatically creates its own Python virtual environment and installs all necessary dependencies on first run.
- **VLC-Powered Video:** Utilizes an embedded VLC media player instance for robust and efficient video playback.
- **Live Chat:** Includes a read-only IRC chat client that connects to the channel's live chat.
- **URL & Name Parsing:** Accepts either a plain channel name (`shroud`) or a full Twitch URL.
- **Customizable UI:**
  - Light and Dark modes for the chat box.
  - Optional timestamps for chat messages.
  - Volume control slider.
  - True fullscreen video mode (toggled with the `Escape` key).
- **Secure:** Your Twitch OAuth token is stored locally in a `.env` file and is never hard-coded.
- **Graceful Handling:** Resilient to streams ending unexpectedly and robust Ctrl+C handling in the terminal.

## Requirements

- Python 3.8+
- `python3-venv` package
- VLC Media Player

You can install the system-level requirements on Debian/Ubuntu with:
```bash
sudo apt-get update
sudo apt-get install python3 python3-venv vlc
