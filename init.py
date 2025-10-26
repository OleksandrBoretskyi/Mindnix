import subprocess
import time
import yaml
import signal
import sys
from datetime import datetime, timedelta
import argparse

CONFIG_FILE = 'config.yaml'
focus_mode = False
focus_start_time = None
focus_end_time = None
running = True
try:
    with open(CONFIG_FILE, 'r') as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    print(f"[ERROR] Config file '{CONFIG_FILE}' not found!")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"[ERROR] Failed to parse config: {e}")
    sys.exit(1)

blacklist = config.get('blacklist', [])
blacklist_sites = config.get('blacklist_sites', [])
interval = config.get('interval', 2)
focus_minutes = config.get('focus_minutes')

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n[INFO] Shutting down gracefully...")
    if focus_mode:
        stop_focus()
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_focus(minutes: int = None):
    global focus_mode, focus_start_time, focus_end_time
    if minutes is None:
        minutes = focus_minutes
    minutes = int(abs(minutes))
    focus_mode = True
    focus_start_time = datetime.now()
    focus_end_time = focus_start_time + timedelta(minutes=minutes)
    print(f"[FOCUS] Started for {minutes} min (until {focus_end_time:%H:%M:%S}).")

def stop_focus():
    global focus_mode, focus_start_time, focus_end_time
    focus_mode = False
    focus_start_time = None
    focus_end_time = None
    print("[FOCUS] Stopped.")

def is_focus_active() -> bool:
    if not focus_mode:
        return False
    if focus_end_time is None:
        return False
    if datetime.now() >= focus_end_time:
        stop_focus()
        print("[FOCUS] Session ended (time up).")
        return False
    return True

def get_window():
    """Get the currently active window name"""
    try:
        window_id = subprocess.check_output(['xdotool', 'getactivewindow'], 
                                           stderr=subprocess.DEVNULL).strip()
        window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id],
                                             stderr=subprocess.DEVNULL).strip().decode('utf-8')
        return window_name
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def get_active_url():
    """Extract domain/URL information from active browser window title"""
    import re
    try:
        # Get active window title
        window_title = subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowname'],
                                              stderr=subprocess.DEVNULL, timeout=0.5).decode('utf-8').strip()
        domain_pattern = r'\b([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.(?:com|net|org|io|co|tv|me|dev))\b'
        domains = re.findall(domain_pattern, window_title)
        
        if domains:
            return f"https://{domains[0]}"
        words = window_title.split()
        for word in words:
            if '.' in word and word.endswith(('.com', '.net', '.org', '.io', '.co', '.tv', '.me', '.dev')):
                return f"https://{word}"
        
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None

def block_window(window_name):
    """Block blacklisted applications and websites"""
    if not window_name:
        return
    
    # Check for blacklisted apps
    for app in blacklist:
        if app.lower() in window_name.lower():
            subprocess.run(["pkill", "-i", "-f", app], check=False, 
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            print(f"[BLOCKED] App: {app}")

    for site in blacklist_sites:
        domain = site.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

        site_name = domain.split('.')[0]
        
        if domain.lower() in window_name.lower() or site_name.lower() in window_name.lower():
            subprocess.run(["xdotool", "key", "ctrl+w"], check=False,
                         stderr=subprocess.DEVNULL)
            print(f"[BLOCKED] Website: {site}")
            time.sleep(0.2)
            subprocess.run(["xdotool", "key", "Alt+Tab"], check=False,
                         stderr=subprocess.DEVNULL)

def block_website(url):
    """Check if URL matches blacklisted sites"""
    if not url:
        return False
    
    for site in blacklist_sites:
        url_domain = url.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0].lower()
        site_domain = site.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0].lower()
        
        if site_domain in url_domain or url_domain in site_domain:
            subprocess.run(["xdotool", "key", "ctrl+w"], check=False,
                         stderr=subprocess.DEVNULL)
            print(f"[BLOCKED] Website: {site}")
            time.sleep(0.2)
            subprocess.run(["xdotool", "key", "Alt+Tab"], check=False,
                         stderr=subprocess.DEVNULL)
            return True
    return False

def show_status():
    """Display current status"""
    if focus_mode:
        if focus_end_time:
            remaining = focus_end_time - datetime.now()
            if remaining.total_seconds() > 0:
                mins = int(remaining.total_seconds() / 60)
                secs = int(remaining.total_seconds() % 60)
                print(f"\n[STATUS] Focus mode active - {mins}m {secs}s remaining")
            else:
                print("\n[STATUS] Focus session expired")
        else:
            print("\n[STATUS] Focus mode active (no end time)")
    else:
        print("\n[STATUS] Focus mode inactive")
    print(f"[STATUS] Monitoring {len(blacklist)} apps and {len(blacklist_sites)} sites")

parser = argparse.ArgumentParser(
    description='Block distracting apps and websites during focus sessions',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='Examples:\n'
           '  python init.py --focus 25    # Start 25 min focus session\n'
           '  python init.py --status      # Show current status\n'
           '  python init.py               # Run without focus mode'
)
parser.add_argument('--focus', type=int, nargs="?", const=focus_minutes,
                   metavar='MINUTES', 
                   help='Start focus mode for specified minutes (default from config)')
parser.add_argument('--status', action='store_true',
                   help='Show current status and exit')
parser.add_argument('--stop', action='store_true',
                   help='Stop focus mode if active and exit')
parser.add_argument('--verbose', '-v', action='store_true',
                   help='Enable verbose output')
args = parser.parse_args()

if args.status:
    show_status()
    sys.exit(0)

if args.stop:
    if focus_mode:
        stop_focus()
        print("[INFO] Focus mode stopped")
    else:
        print("[INFO] No active focus session")
    sys.exit(0)

if args.focus is not None:
    start_focus(args.focus)

print("[INFO] Monitor started. Press Ctrl+C to stop.")
try:
    while running:
        if is_focus_active():
            active_window = get_window()
            if active_window:
                if args.verbose:
                    print(f"Active window: {active_window}")
                
                block_window(active_window)
                active_url = get_active_url()
                if active_url:
                    block_website(active_url)
        else:
            if args.verbose and running:
                active_window = get_window()
                if active_window:
                    print(f"Active window: {active_window} (monitoring only)")
        
        if running:
            time.sleep(interval)
except KeyboardInterrupt:
    signal_handler(None, None)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)