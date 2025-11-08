# 🟣 Minimalist Python Twitch Client

**Version:** 1.10.0  
**Author:** Systems Architect AI  
**Platform:** Ubuntu-based systems (tested on 22.04+)  
**License:** MIT  

A lightweight, self-contained desktop Twitch client written entirely in Python and Tkinter.  
It supports live video playback, real-time chat via Twitch IRC, dark mode, optional timestamps, and fullscreen toggling — all in a single script.

---

## 🚀 Features

- 🎥 **Stream Playback** — Plays live Twitch streams using `python-vlc` and `yt-dlp` for URL resolution.  
- 💬 **Real-Time Chat** — Connects to Twitch IRC for full live chat integration.  
- 🌗 **Dark Mode Toggle** — Switch instantly between light and dark chat themes.  
- 🕒 **Timestamps** — Optional colored timestamps for chat messages.  
- 🔊 **Volume Control** — Smooth control via slider with live updates to VLC.  
- ⛔ **Graceful Shutdown** — Handles stream end, connection loss, and app close cleanly.  
- 🧩 **Self-Managing Virtual Environment** — Automatically creates `.venv` and installs dependencies if missing.  
- ⌨️ **Keyboard Shortcut:**  
  - `ESC` → Toggle fullscreen mode.

---

## 🧠 Architecture Overview

```
twitch_app.py
├── handle_venv()          → Creates .venv, installs dependencies, relaunches script
├── run_app()              → Main entry point for GUI
│
├── TwitchApp              → Main Tkinter GUI
│   ├── load_config()      → Loads .env with OAuth and nickname
│   ├── load_stream()      → Fetches stream URL via yt-dlp, starts VLC
│   ├── poll_message_queue → Fetches and displays chat messages
│   ├── toggle_dark_mode() → Switches chat theme
│   ├── toggle_fullscreen()→ Hides UI and chat for pure video playback
│   └── handle_stream_end()→ Cleans up when stream finishes
│
└── TwitchIRCClient(Thread)
    ├── Connects to Twitch IRC over TCP
    ├── Handles PING/PONG
    ├── Parses PRIVMSG into chat queue
    └── Gracefully stops on shutdown
```

---

## 🧩 Requirements

The script automatically manages dependencies via a virtual environment, but if you want to install them manually:

```bash
sudo apt install vlc python3-venv
pip install python-vlc python-dotenv yt-dlp
```

Dependencies:
- `python-vlc`
- `python-dotenv`
- `yt-dlp`

---

## ⚙️ Setup & Configuration

1. **Clone or copy** the `twitch_app.py` file into a directory of your choice.  
2. In the same directory, create a `.env` file with your Twitch credentials:

   ```bash
   TWITCH_OAUTH_TOKEN=your_oauth_token_here
   TWITCH_NICKNAME=your_twitch_username
   ```

   > To generate an OAuth token, visit:  
   > [https://twitchapps.com/tmi](https://twitchapps.com/tmi)

3. **Run the app:**

   ```bash
   python3 twitch_app.py
   ```

   The script will:
   - Create a `.venv` if none exists.
   - Install all dependencies inside it.
   - Relaunch itself automatically from the virtual environment.

---

## 🖥️ Usage

1. **Enter a Twitch channel name** (e.g. `summit1g`, `amouranth`) or paste a full URL (e.g. `https://www.twitch.tv/xqc`).  
2. Click **Load Stream** or press **Enter**.  
3. The stream will begin playback; chat connects automatically.  

**Controls:**
- 🔉 Volume: Adjust via slider.
- 🕶 Dark Mode: Toggle chat theme.
- 🕓 Timestamps: Add colored timestamps to messages.
- ⌨️ ESC: Toggle fullscreen (video only).

---

## 🧰 Troubleshooting

| Problem | Likely Cause | Solution |
|----------|---------------|-----------|
| **“.env not found”** | Missing config file | Create `.env` with your Twitch token and nickname. |
| **“VLC Error”** | VLC not installed or missing bindings | Install VLC via `sudo apt install vlc`. |
| **“Failed to connect to Twitch IRC”** | Invalid token or network issue | Regenerate token or check firewall/DNS. |
| **“yt-dlp not found”** | Dependency missing or install failed | Run `pip install yt-dlp` manually in `.venv`. |
| **No video** | Stream offline | Verify channel is live. |
| **Virtualenv setup loop** | Corrupt `.venv` | Delete `.venv` folder and restart script. |

---

## 🧱 Technical Notes

- Uses **yt-dlp** to fetch the best available HLS stream URL for Twitch.  
- Connects directly to **Twitch IRC (`irc.chat.twitch.tv:6667`)** for minimal latency chat.  
- GUI built with **Tkinter**, with dynamic layout resizing and theme-aware text rendering.  
- Video rendering via **libVLC**, instantiated with `--ignore-config` and `--no-osd` for consistent playback.  
- IRC thread is fully daemonized and uses a `queue.Queue` for thread-safe message passing.  
- Fullscreen mode hides non-video UI elements (true fullscreen, not just maximized).

---

## 🧾 Changelog

**1.10.0**
- Reworked fullscreen toggle to truly hide UI elements (was previously only maximized).

**1.9.0**
- Added ESC keybinding for fullscreen toggle.
- UI label for new shortcut.

**1.8.0**
- Added optional colored timestamps in chat (toggle via checkbox).

**1.7.0**
- Implemented dark mode toggle for chat box.

**1.6.0**
- Improved handling for ended streams (no crash, message shown).
- VLC initialized with clean flags (`--ignore-config`, `--no-osd`).

---

## 🧑‍💻 Development Notes

- Designed to be single-file deployable — no extra modules or packaging required.  
- Fully compatible with Python ≥3.8 on Ubuntu systems.  
- Uses **relative paths** and auto-managed environment setup for portability.  
- Verbose logging output aids debugging and tracing of events.

---

## 🧮 Example Run

```
$ python3 twitch_app.py
--- VENV SETUP REQUIRED ---
INFO: Creating virtual environment at '/home/user/twitch/.venv'...
INFO: Virtual environment created successfully.
INFO: Installing/verifying packages...
INFO: All required packages are installed/verified.
INFO: Re-launching script 'twitch_app.py' inside the virtual environment...
INFO: Loading configuration from .env file.
INFO: Configuration loaded successfully.
INFO: IRC client thread started for channel 'xqc'.
INFO: VLC player started for stream: https://...
```

---

## 🧑‍⚖️ License

This project is released under the **MIT License**.  
You may use, modify, and distribute it freely.

---

**Enjoy a clean, dependency-free Twitch experience — built for Linux power users.**
