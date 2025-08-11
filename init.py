import subprocess
import time
import yaml
from datetime import datetime, timedelta

CONFIG_FILE = 'config.yaml'
with open(CONFIG_FILE, 'r') as file:
    config = yaml.safe_load(file)

blacklist = config.get('blacklist', [])
interval = config.get('interval', 2)
focus_minutes = config.get('focus_minutes')
focus_mode = False
focus_start_time = None
focus_end_time = None

def start_focus(minutes: int = None):
    global focus_mode, focus_start_time, focus_end_time
    if minutes is None:
        minutes = focus_minutes
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
    try:
        window_id = subprocess.check_output(['xdotool', 'getactivewindow']).strip()
        window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).strip().decode('utf-8')
        return window_name
    except subprocess.CalledProcessError:
        return None

def block_window(window_name):
    for app in blacklist:
        if app.lower() in window_name.lower():
            subprocess.run(["pkill", "-i", "-f", app], check=False)
            print(f"[BLOCKED] {app}")
while True:
    active_window = get_window()
    if active_window:
        print(f"Active window: {active_window}")
        if is_focus_active():
            block_window(active_window)
    else:
        print("No active window found.")
    time.sleep(interval)