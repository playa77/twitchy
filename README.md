# Minimalist Python Twitch Client

A lean, no-nonsense Twitch client for Ubuntu that does exactly what you need and nothing more. Built for people who want a quality stream on their fourth monitor while actually getting work done.

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
- **Twitch CLI** (for token generation)
- **Internet connection** for initial setup

## Installation

### 1. Install VLC

```bash
sudo apt install vlc
```

### 2. Install Twitch CLI

Download and install the official Twitch CLI:

```bash
# Download the latest release for Linux
wget https://github.com/twitchdev/twitch-cli/releases/latest/download/twitch-cli_Linux_x86_64.tar.gz

# Extract it
tar -xzf twitch-cli_Linux_x86_64.tar.gz

# Move to a directory in your PATH
sudo mv twitch /usr/local/bin/

# Verify installation
twitch version
```

### 3. Configure Twitch CLI

First, you need to register an application on Twitch:

1. Go to the [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Click **"Register Your Application"**
3. Fill in:
   - **Name**: Whatever you want (e.g., "My Chat Client")
   - **OAuth Redirect URLs**: `http://localhost:3000`
   - **Category**: "Chat Bot"
4. Click **"Create"**
5. Click **"Manage"** and note your **Client ID**
6. Click **"New Secret"** and note your **Client Secret**

Now configure the CLI with your credentials:

```bash
twitch configure
```

When prompted, enter:
- Your **Client ID**
- Your **Client Secret**

### 4. Generate Your OAuth Token

Generate a user access token with chat permissions:

```bash
twitch token -u -s 'chat:read chat:edit'
```

This will:
1. Open your browser to authorize the application
2. Click **"Authorize"**
3. Return to your terminal where the token will be displayed

Copy the **User Access Token** from the output (not the refresh token).

### 5. Create Your Configuration File

Create a `.env` file in the same directory as `twitch_app.py`:

```env
TWITCH_OAUTH_TOKEN=your_access_token_here
TWITCH_NICKNAME=your_twitch_username
```

**Important**: 
- Use just the access token value itself
- The app will automatically add the `oauth:` prefix when connecting to IRC
- Your nickname should be your Twitch username (lowercase)

### 6. Run the Application

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

That's it. No tracking, no BS.

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

## Token Expiration & Refresh

User access tokens expire after a few hours. When your chat stops connecting:

```bash
# Use the refresh token to get a new access token
twitch token --refresh your_refresh_token_here
```

Or simply regenerate a fresh token:

```bash
twitch token -u -s 'chat:read chat:edit'
```

Update your `.env` file with the new token.

## Why This Exists

Because sometimes you just want to watch a stream without:
- A Chromium-based browser eating 2GB of RAM
- Autoplay videos in the sidebar
- "Gift a sub!" overlays every 5 minutes
- Recommended channels you don't care about
- Your browser's 47 other tabs slowing everything down

This is for the focused multitasker. The person with code on three monitors and a stream on the fourth. The minimalist who respects their system resources.

## Technical Notes

- Built with Python's `tkinter` for minimal dependencies
- Uses `python-vlc` bindings for video playback
- Connects directly to Twitch IRC (no intermediary services)
- Uses OAuth 2.0 user access tokens (modern standard)
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

**Chat not connecting / "Login authentication failed"**
- Your OAuth token may have expired—generate a new one
- Verify your `.env` file has the correct token value
- Ensure username matches your Twitch account exactly
- The app adds `oauth:` prefix automatically—don't include it in `.env`

**"Improperly formatted auth"**
- Usually means the token format is wrong
- Regenerate the token using `twitch token -u -s 'chat:read chat:edit'`
- Make sure you copied the access token, not the refresh token

## License

Do whatever you want with this. It's yours now.

## Contributing

This is a personal tool that happens to be shared. If you want to fork it and add features for your own use, go for it. Pull requests welcome if they align with the minimalist philosophy, but no promises.

---

**Built for productivity. Designed for simplicity. Perfect for your fourth monitor.**
