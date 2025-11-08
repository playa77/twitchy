# Minimalist Python Twitch Client

A lean, no-nonsense Twitch client for Ubuntu that does exactly what you need and nothing more. Built for people who want a quality stream on their third monitor while actually getting work done.

## Philosophy

This isn't another bloated Electron app trying to be everything to everyone. It's a lightweight, self-contained Python application that:

- Plays Twitch streams in high quality
- Shows live chat (when you want to glance at it)
- Stays out of your way
- Uses minimal system resources
- Doesn't nag you to subscribe, follow, or engage

Perfect for multitaskers who want Twitch ambient in the background without the distraction of a full browser tab or the official app's notification spam.

## Features

- **Clean Video Playback**: Powered by VLC for reliable, hardware-accelerated streaming
- **Live Chat Integration**: Real-time Twitch IRC chat display with optional emotes
- **Dark Mode**: Easy on the eyes during long work sessions
- **Timestamps**: Optional chat timestamps for context
- **Fullscreen Toggle**: Press `ESC` to toggle true fullscreen mode
- **Volume Control**: Integrated slider, no hunting for system controls
- **Local Emote Support**: Render custom emotes from your `/emotes` folder
- **Graceful Stream Handling**: Won't crash when streams end
- **Self-Contained**: Automatically manages its own virtual environment and dependencies

## Prerequisites

- **Ubuntu** (or any Debian-based Linux distribution)
- **Python 3.8+**
- **VLC Media Player**: `sudo apt install vlc`
- **Internet connection** for initial setup

## Installation

1. **Clone or download** this repository to your local machine

2. **Install VLC** (if not already installed):
   ```bash
   sudo apt install vlc
   ```
      
# 3. **Get your Twitch OAuth token**:
#    - Visit [https://twitchapps.com/tmi/](https://twitchapps.com/tmi/)
#   - Connect with your Twitch account
#   - Copy the OAuth token (starts with `oauth:` - you can include this prefix or omit it)
# THIS DOES NOT WORK ANYMORE

4. **Create a `.env` file** in the same directory as `twitch_app.py`:
   ```env
   TWITCH_OAUTH_TOKEN=your_oauth_token_here
   TWITCH_NICKNAME=your_twitch_username
   ```

5. **Run the application**:
   ```bash
   python3 twitch_app.py
   ```

The first run will automatically:
- Create a virtual environment (`.venv/`)
- Install all required Python packages
- Re-launch itself in the virtual environment

Subsequent runs will start instantly.

## Usage

1. **Launch the app**: `python3 twitch_app.py`
2. **Enter a channel name** (e.g., `xqc`) or full URL (e.g., `https://twitch.tv/xqc`)
3. **Press Enter** or click "Load Stream"
4. **Adjust settings** as needed:
   - Dark Mode toggle for chat
   - Show Timestamps for message context
   - Show Emotes to render custom emotes
   - Volume slider for quick adjustments
5. **Press ESC** to toggle fullscreen mode

That's it. No account required (beyond the OAuth for chat), no tracking, no BS.

## Optional: Custom Emotes

Want to see your favorite emotes in chat?

1. Create an `emotes/` folder in the same directory as the script
2. Add your emote images (PNG, JPG, GIF) to this folder
3. Create an `emotes.json` file mapping emote codes to file paths:

```json
{
  "Kappa": "emotes/Kappa.png",
  "PogChamp": "emotes/PogChamp.png",
  "LUL": "emotes/LUL.png"
}
```

4. Toggle "Show Emotes" in the UI to enable/disable rendering

## Keyboard Shortcuts

- **Enter** (in channel field): Load stream
- **ESC**: Toggle fullscreen video mode

## Why This Exists

Because sometimes you just want to watch a stream without:
- A Chromium-based browser eating 2GB of RAM
- Autoplay videos in the sidebar
- "Gift a sub!" overlays every 5 minutes
- Recommended channels you don't care about
- Your browser's 47 other tabs slowing everything down

This is for the focused multitasker. The person with code on rwo monitors and a stream on the third. The minimalist who respects their system resources.

## Technical Notes

- Built with Python's `tkinter` for minimal dependencies
- Uses `python-vlc` bindings for video playback
- Connects directly to Twitch IRC (no intermediary services)
- `yt-dlp` handles stream URL resolution
- Fully self-contained with automatic dependency management

## Troubleshooting

**"Network error while installing dependencies"**
- Check your internet connection
- Verify DNS settings
- Ensure PyPI isn't blocked by your firewall

**"Could not get stream URL"**
- Verify the channel is currently live
- Check the channel name spelling
- Ensure `yt-dlp` is installed correctly

**VLC player won't start**
- Confirm VLC is installed: `vlc --version`
- Try reinstalling: `sudo apt install --reinstall vlc`

**Chat not connecting**
- Verify your `.env` file has valid credentials
- Ensure OAuth token is current (they can expire)
- Check that username matches your Twitch account

## License

Do whatever you want with this. It's yours now.

## Contributing

This is a personal tool that happens to be shared. If you want to fork it and add features for your own use, go for it. Pull requests welcome if they align with the minimalist philosophy, but no promises.

---

**Built for productivity. Designed for simplicity. Perfect for your fourth monitor.**
