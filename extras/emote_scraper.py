#!/usr/bin/env python3
"""
Twitch Emote Scraper - v0.2
Scrapes top 100 emotes from Twitch, BTTV, FFZ, and 7TV from StreamElements stats
Downloads emotes and creates a JSON mapping file
Features: Rate limiting, failed emote logging, and retry mechanism
"""

import os
import sys
import json
import signal
import shutil
import subprocess
import tempfile
import time
import argparse
from pathlib import Path

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\n[INFO] Shutdown requested. Cleaning up...")
    shutdown_requested = True


# Register signal handler
signal.signal(signal.SIGINT, signal_handler)


def setup_environment():
    """Set up virtual environment and install dependencies"""
    print("[INFO] Setting up virtual environment...")
    
    # Create temporary venv directory
    venv_dir = tempfile.mkdtemp(prefix="emote_scraper_venv_")
    print(f"[INFO] Virtual environment location: {venv_dir}")
    
    try:
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        
        # Determine pip path based on OS
        if os.name == 'nt':  # Windows
            pip_path = os.path.join(venv_dir, "Scripts", "pip")
            python_path = os.path.join(venv_dir, "Scripts", "python")
        else:  # Unix-like
            pip_path = os.path.join(venv_dir, "bin", "pip")
            python_path = os.path.join(venv_dir, "bin", "python")
        
        print("[INFO] Installing required packages...")
        # Install required packages
        packages = ["requests", "pillow"]
        subprocess.run([pip_path, "install", "-q"] + packages, check=True)
        
        print("[INFO] Environment setup complete")
        return venv_dir, python_path
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to set up environment: {e}")
        cleanup_venv(venv_dir)
        sys.exit(1)


def cleanup_venv(venv_dir):
    """Clean up virtual environment"""
    if os.path.exists(venv_dir):
        print(f"[INFO] Cleaning up virtual environment: {venv_dir}")
        try:
            shutil.rmtree(venv_dir)
            print("[INFO] Virtual environment cleaned up successfully")
        except Exception as e:
            print(f"[WARNING] Could not remove venv directory: {e}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Scrape top 100 emotes from Twitch, BTTV, FFZ, and 7TV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal run - scrape all emotes
  python3 emote_scraper.py
  
  # Retry failed emotes from log file
  python3 emote_scraper.py --retry-log failed_emotes.json
  
  # Use custom delay between requests (in milliseconds)
  python3 emote_scraper.py --delay 1000
        """
    )
    parser.add_argument(
        '--retry-log',
        type=str,
        help='Path to failed emotes log file. If provided, only retry emotes from this file.'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=500,
        help='Delay between requests in milliseconds (default: 500ms)'
    )
    return parser.parse_args()


def main_script():
    """Main script logic after environment is set up"""
    import requests
    from PIL import Image
    from io import BytesIO
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Configuration
    EMOTE_DIR = Path("emotes")
    JSON_OUTPUT = Path("emote_mapping.json")
    FAILED_LOG = Path("failed_emotes.json")
    STREAMELEMENTS_API = "https://api.streamelements.com/kappa/v2/chatstats/global/stats"
    REQUEST_DELAY = args.delay / 1000.0  # Convert ms to seconds
    
    print(f"[INFO] Request delay set to {args.delay}ms")
    
    # Create emote directory
    EMOTE_DIR.mkdir(exist_ok=True)
    print(f"[INFO] Emote directory: {EMOTE_DIR.absolute()}")
    
    # Load existing mapping if it exists
    existing_mapping = {}
    if JSON_OUTPUT.exists():
        print("[INFO] Loading existing emote mapping...")
        try:
            with open(JSON_OUTPUT, 'r', encoding='utf-8') as f:
                existing_mapping = json.load(f)
            print(f"[INFO] Loaded {len(existing_mapping)} existing emote mappings")
        except Exception as e:
            print(f"[WARNING] Could not load existing mapping: {e}")
    
    # Check if we're in retry mode
    retry_mode = False
    failed_emotes_to_retry = []
    
    if args.retry_log:
        retry_mode = True
        retry_log_path = Path(args.retry_log)
        if not retry_log_path.exists():
            print(f"[ERROR] Retry log file not found: {args.retry_log}")
            sys.exit(1)
        
        print(f"[INFO] Retry mode enabled - loading failed emotes from {args.retry_log}")
        try:
            with open(retry_log_path, 'r', encoding='utf-8') as f:
                failed_emotes_to_retry = json.load(f)
            print(f"[INFO] Loaded {len(failed_emotes_to_retry)} failed emotes to retry")
        except Exception as e:
            print(f"[ERROR] Could not load retry log: {e}")
            sys.exit(1)
    
    # Track failed emotes
    failed_emotes = []
    
    if not retry_mode:
        # Fetch global stats from StreamElements
        print("[INFO] Fetching global emote statistics from StreamElements...")
        try:
            response = requests.get(STREAMELEMENTS_API, timeout=30)
            response.raise_for_status()
            data = response.json()
            print("[INFO] Successfully retrieved global statistics")
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch data from StreamElements: {e}")
            sys.exit(1)
        
        # Extract emote lists (top 100 from each)
        twitch_emotes = data.get('twitchEmotes', [])[:100]
        bttv_emotes = data.get('bttvEmotes', [])[:100]
        ffz_emotes = data.get('ffzEmotes', [])[:100]
        seventv_emotes = data.get('sevenTVEmotes', [])[:100]
        
        print(f"\n[INFO] Found emotes:")
        print(f"  - Twitch: {len(twitch_emotes)}")
        print(f"  - BTTV: {len(bttv_emotes)}")
        print(f"  - FFZ: {len(ffz_emotes)}")
        print(f"  - 7TV: {len(seventv_emotes)}")
        print()
    else:
        # In retry mode, we already have the emotes list
        twitch_emotes = []
        bttv_emotes = []
        ffz_emotes = []
        seventv_emotes = []
        
        # Organize failed emotes by provider
        for emote_info in failed_emotes_to_retry:
            provider = emote_info.get('provider', '')
            if provider == 'twitch':
                twitch_emotes.append(emote_info)
            elif provider == 'bttv':
                bttv_emotes.append(emote_info)
            elif provider == 'ffz':
                ffz_emotes.append(emote_info)
            elif provider == '7tv':
                seventv_emotes.append(emote_info)
    
    emote_mapping = {}
    total_emotes = len(twitch_emotes) + len(bttv_emotes) + len(ffz_emotes) + len(seventv_emotes)
    processed = 0
    
    def download_emote(url, emote_name, provider, emote_id):
        """Download and save an emote"""
        global shutdown_requested
        
        if shutdown_requested:
            return None
        
        # Sanitize filename
        safe_name = "".join(c for c in emote_name if c.isalnum() or c in "._- ")
        safe_name = safe_name.strip()
        if not safe_name:  # Handle edge case where name becomes empty
            safe_name = f"{provider}_{emote_id}"
        
        # Check if emote already exists in directory
        existing_files = list(EMOTE_DIR.glob(f"{safe_name}.*"))
        
        if existing_files:
            # File exists, check if it's already mapped
            existing_file = existing_files[0]
            # Convert to absolute path first, then to relative from cwd
            absolute_path = existing_file.resolve()
            cwd_absolute = Path.cwd().resolve()
            relative_path = str(absolute_path.relative_to(cwd_absolute))
            
            if emote_name in existing_mapping and existing_mapping[emote_name] == relative_path:
                print(f"  [SKIP] {emote_name} (already mapped)")
                return existing_mapping[emote_name]
            else:
                print(f"  [MAP] {emote_name} (file exists, updating mapping)")
                return relative_path
        
        # Add delay before download (be nice to CDNs)
        time.sleep(REQUEST_DELAY)
        
        # Download emote
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Detect image format
            img = Image.open(BytesIO(response.content))
            img_format = img.format.lower() if img.format else 'png'
            
            # Save image
            filename = f"{safe_name}.{img_format}"
            filepath = EMOTE_DIR / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Calculate relative path from absolute paths
            absolute_path = filepath.resolve()
            cwd_absolute = Path.cwd().resolve()
            relative_path = str(absolute_path.relative_to(cwd_absolute))
            
            print(f"  [DOWNLOAD] {emote_name} -> {filename}")
            return relative_path
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"{e.response.status_code} {e.response.reason}"
            print(f"  [ERROR] Failed to download {emote_name}: {error_msg} for url: {url}")
            
            # Log failed emote
            failed_emotes.append({
                'emote': emote_name,
                'id': emote_id,
                'provider': provider,
                'url': url,
                'error': error_msg
            })
            return None
            
        except Exception as e:
            print(f"  [ERROR] Failed to download {emote_name}: {e}")
            
            # Log failed emote
            failed_emotes.append({
                'emote': emote_name,
                'id': emote_id,
                'provider': provider,
                'url': url,
                'error': str(e)
            })
            return None
    
    # Process Twitch emotes
    if twitch_emotes:
        print("\n[INFO] Processing Twitch emotes...")
        for emote_data in twitch_emotes:
            if shutdown_requested:
                break
            
            processed += 1
            emote_id = emote_data.get('id', '')
            emote_name = emote_data.get('emote', '')
            
            if not emote_id or not emote_name:
                continue
            
            # Twitch emote URL format
            url = f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/3.0"
            
            print(f"[{processed}/{total_emotes}] Twitch: {emote_name}")
            path = download_emote(url, emote_name, 'twitch', emote_id)
            if path:
                emote_mapping[emote_name] = path
    
    # Process BTTV emotes
    if bttv_emotes:
        print("\n[INFO] Processing BTTV emotes...")
        for emote_data in bttv_emotes:
            if shutdown_requested:
                break
            
            processed += 1
            emote_id = emote_data.get('id', '')
            emote_name = emote_data.get('emote', '')
            
            if not emote_id or not emote_name:
                continue
            
            # BTTV emote URL format
            url = f"https://cdn.betterttv.net/emote/{emote_id}/3x"
            
            print(f"[{processed}/{total_emotes}] BTTV: {emote_name}")
            path = download_emote(url, emote_name, 'bttv', emote_id)
            if path:
                emote_mapping[emote_name] = path
    
    # Process FFZ emotes
    if ffz_emotes:
        print("\n[INFO] Processing FFZ emotes...")
        for emote_data in ffz_emotes:
            if shutdown_requested:
                break
            
            processed += 1
            emote_id = emote_data.get('id', '')
            emote_name = emote_data.get('emote', '')
            
            if not emote_id or not emote_name:
                continue
            
            # FFZ emote URL format - try multiple sizes
            # FFZ CDN sometimes doesn't have all sizes, so we'll try 4x, 2x, 1x
            urls_to_try = [
                f"https://cdn.frankerfacez.com/emoticon/{emote_id}/4",
                f"https://cdn.frankerfacez.com/emoticon/{emote_id}/2",
                f"https://cdn.frankerfacez.com/emoticon/{emote_id}/1"
            ]
            
            print(f"[{processed}/{total_emotes}] FFZ: {emote_name}")
            
            path = None
            for idx, url in enumerate(urls_to_try):
                if idx > 0:
                    print(f"  [RETRY] Trying alternative size...")
                path = download_emote(url, emote_name, 'ffz', emote_id)
                if path:
                    # Success! Remove from failed list if it was added
                    failed_emotes[:] = [e for e in failed_emotes if not (e['id'] == emote_id and e['provider'] == 'ffz')]
                    break
            
            if path:
                emote_mapping[emote_name] = path
    
    # Process 7TV emotes
    if seventv_emotes:
        print("\n[INFO] Processing 7TV emotes...")
        for emote_data in seventv_emotes:
            if shutdown_requested:
                break
            
            processed += 1
            emote_id = emote_data.get('id', '')
            emote_name = emote_data.get('emote', '')
            
            if not emote_id or not emote_name:
                continue
            
            # 7TV emote URL format (using 4x webp)
            url = f"https://cdn.7tv.app/emote/{emote_id}/4x.webp"
            
            print(f"[{processed}/{total_emotes}] 7TV: {emote_name}")
            path = download_emote(url, emote_name, '7tv', emote_id)
            if path:
                emote_mapping[emote_name] = path
    
    # Save mapping to JSON
    if not shutdown_requested:
        print(f"\n[INFO] Saving emote mapping to {JSON_OUTPUT}...")
        try:
            with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
                json.dump(emote_mapping, f, indent=2, ensure_ascii=False)
            print(f"[SUCCESS] Saved {len(emote_mapping)} emote mappings")
            print(f"[INFO] JSON file location: {JSON_OUTPUT.absolute()}")
        except Exception as e:
            print(f"[ERROR] Failed to save mapping: {e}")
        
        # Save failed emotes log
        if failed_emotes:
            print(f"\n[WARNING] {len(failed_emotes)} emotes failed to download")
            print(f"[INFO] Saving failed emotes log to {FAILED_LOG}...")
            try:
                with open(FAILED_LOG, 'w', encoding='utf-8') as f:
                    json.dump(failed_emotes, f, indent=2, ensure_ascii=False)
                print(f"[INFO] Failed emotes log saved: {FAILED_LOG.absolute()}")
                print(f"[INFO] To retry failed emotes, run: python3 {sys.argv[0]} --retry-log {FAILED_LOG}")
            except Exception as e:
                print(f"[ERROR] Failed to save failed emotes log: {e}")
        else:
            print(f"\n[SUCCESS] All emotes downloaded successfully!")
            # Remove failed log if it exists and we have no failures
            if FAILED_LOG.exists():
                try:
                    FAILED_LOG.unlink()
                    print(f"[INFO] Removed old failed emotes log")
                except Exception as e:
                    print(f"[WARNING] Could not remove old failed log: {e}")
    else:
        print("\n[WARNING] Script interrupted. Partial results may be incomplete.")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total emotes processed: {processed}/{total_emotes}")
    print(f"Emotes successfully mapped: {len(emote_mapping)}")
    print(f"Emotes failed: {len(failed_emotes)}")
    print(f"Emote directory: {EMOTE_DIR.absolute()}")
    print(f"Mapping file: {JSON_OUTPUT.absolute()}")
    if failed_emotes:
        print(f"Failed emotes log: {FAILED_LOG.absolute()}")
    print("="*60)


if __name__ == "__main__":
    print("="*60)
    print("Twitch Emote Scraper - v0.2")
    print("="*60)
    
    # Set up environment
    venv_dir, python_path = setup_environment()
    
    try:
        # Run main script in the virtual environment
        print("\n[INFO] Starting emote scraping process...")
        print("="*60 + "\n")
        
        # Execute the main script
        main_script()
        
    except KeyboardInterrupt:
        print("\n[INFO] Script interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        if not shutdown_requested:
            print("\n[INFO] Process completed")
        cleanup_venv(venv_dir)
        print("\n[INFO] Script finished")
