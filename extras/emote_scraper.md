# Twitch Emote Scraper

A robust Python script that scrapes the top 100 most-used emotes from Twitch, BetterTTV (BTTV), FrankerFaceZ (FFZ), and 7TV based on global usage statistics from StreamElements.

## Features

- **Multi-Platform Support**: Downloads emotes from all major Twitch emote providers
  - Twitch native emotes
  - BetterTTV (BTTV)
  - FrankerFaceZ (FFZ)
  - 7TV
- **Self-Contained**: Automatically manages virtual environment and dependencies
- **Rate Limited**: Respectful 500ms delay between requests (configurable)
- **Smart Duplicate Detection**: Skips already-downloaded emotes
- **Failed Emote Logging**: Tracks failed downloads for easy retry
- **Retry Mechanism**: Re-attempt failed downloads from log file
- **Fallback URLs**: Tries multiple image sizes for FFZ emotes
- **Graceful Interruption**: Handles Ctrl+C cleanly with automatic cleanup
- **JSON Mapping**: Creates a mapping file of emote names to local file paths

## Requirements

- Python 3.6 or higher
- Internet connection
- Ubuntu (or any Linux distribution)
- ~50MB free disk space for emotes

## Installation

No installation required! The script is fully self-contained and will:
1. Create its own temporary virtual environment
2. Install required dependencies (`requests`, `pillow`)
3. Clean up automatically when finished

Simply download the script and make it executable:

```bash
chmod +x emote_scraper.py
```

## Usage

### Basic Usage

Download all top 100 emotes from each platform:

```bash
python3 emote_scraper.py
```

### Retry Failed Downloads

If some emotes failed to download, retry them using the generated log file:

```bash
python3 emote_scraper.py --retry-log failed_emotes.json
```

### Custom Rate Limiting

Adjust the delay between requests (in milliseconds):

```bash
# Use 1 second delay (extra cautious)
python3 emote_scraper.py --delay 1000

# Use 250ms delay (faster, but less polite)
python3 emote_scraper.py --delay 250
```

### Combined Options

```bash
python3 emote_scraper.py --retry-log failed_emotes.json --delay 750
```

## Command Line Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--retry-log` | string | None | Path to failed emotes log file. If provided, only retry emotes from this file. |
| `--delay` | integer | 500 | Delay between requests in milliseconds. |

## Output Files

### `emotes/` Directory

Contains all downloaded emote images with their exact names. Files are saved in their original format (PNG, WebP, GIF, etc.).

Example structure:
```
emotes/
├── Kappa.png
├── PogChamp.png
├── KEKW.webp
├── monkaS.png
└── ...
```

### `emote_mapping.json`

JSON file mapping emote names to their local file paths:

```json
{
  "Kappa": "emotes/Kappa.png",
  "PogChamp": "emotes/PogChamp.png",
  "KEKW": "emotes/KEKW.webp",
  "monkaS": "emotes/monkaS.png"
}
```

### `failed_emotes.json`

Log file containing details about failed downloads (only created if there are failures):

```json
[
  {
    "emote": "SomeEmote",
    "id": "12345",
    "provider": "ffz",
    "url": "https://cdn.frankerfacez.com/emoticon/12345/4",
    "error": "404 Not Found"
  }
]
```

## How It Works

1. **Data Source**: Fetches global emote usage statistics from StreamElements API
2. **Top 100 Selection**: Extracts the top 100 most-used emotes from each platform
3. **Smart Download**: 
   - Checks if emote already exists locally
   - Downloads from platform-specific CDNs
   - Applies rate limiting between requests
   - Tries fallback URLs for FFZ emotes (4x → 2x → 1x)
4. **Mapping Generation**: Creates JSON mapping of emote names to file paths
5. **Error Logging**: Tracks any failed downloads for easy retry

## CDN URLs Used

- **Twitch**: `https://static-cdn.jtvnw.net/emoticons/v2/{id}/default/dark/3.0`
- **BTTV**: `https://cdn.betterttv.net/emote/{id}/3x`
- **FFZ**: `https://cdn.frankerfacez.com/emoticon/{id}/{size}` (tries 4, 2, 1)
- **7TV**: `https://cdn.7tv.app/emote/{id}/4x.webp`

## Error Handling

The script handles various error scenarios gracefully:

- **404 Not Found**: Logs the failure and continues
- **Network Timeouts**: Catches and logs timeout errors
- **Invalid Images**: Skips corrupted/invalid image data
- **Ctrl+C**: Cleans up virtual environment and saves progress
- **Duplicate Names**: Sanitizes filenames to avoid conflicts

## Troubleshooting

### High Failure Rate

If many emotes fail to download:
1. Check your internet connection
2. Increase the delay: `--delay 1000`
3. Try again later (CDN may be temporarily unavailable)
4. Use retry mode: `--retry-log failed_emotes.json`

### Permission Errors

Ensure you have write permissions in the current directory:
```bash
chmod +w .
```

### Python Version Issues

Check your Python version:
```bash
python3 --version
```

Ensure it's 3.6 or higher.

## Performance

- **Download Speed**: ~500ms per emote (with default rate limiting)
- **Total Time**: Approximately 3-4 minutes for 400 emotes
- **Storage**: ~30-50MB for all emotes
- **Memory**: <100MB peak usage

## Best Practices

1. **Be Respectful**: Don't decrease the delay below 250ms to avoid overwhelming CDN services
2. **Use Retry Mode**: If failures occur, use `--retry-log` instead of re-downloading everything
3. **Check Logs**: Review `failed_emotes.json` to understand why emotes failed
4. **Keep Mappings**: The `emote_mapping.json` file is useful for integration with other tools

## Integration Example

Using the emote mapping in your Python code:

```python
import json

# Load emote mapping
with open('emote_mapping.json', 'r') as f:
    emotes = json.load(f)

# Get path to specific emote
kappa_path = emotes.get('Kappa')
if kappa_path:
    print(f"Kappa emote located at: {kappa_path}")
```

## License

This script is provided as-is for personal and educational use. Please respect the terms of service of Twitch, BTTV, FFZ, and 7TV when using their emotes.

## Version History

### v0.2 (Current)
- Added rate limiting with configurable delay
- Implemented failed emote logging
- Added retry mechanism via `--retry-log` parameter
- Added FFZ fallback URL support
- Improved error messages with detailed logging
- Better handling of edge cases (empty names, special characters)

### v0.1
- Initial release
- Basic scraping functionality
- Self-contained virtual environment management
- JSON mapping generation

## Credits

- **Data Source**: [StreamElements Chat Stats](https://stats.streamelements.com/c/global)
- **Emote Providers**: Twitch, BetterTTV, FrankerFaceZ, 7TV

## Support

If you encounter issues:
1. Check the `failed_emotes.json` log file for specific error messages
2. Try increasing the delay between requests
3. Ensure you have a stable internet connection
4. Verify the StreamElements API is accessible

---

**Note**: This script is for personal use. Emote images are property of their respective creators and platforms. Please respect copyright and usage terms.
