import subprocess
import time
import yaml
import os
from datetime import datetime, timedelta

CONFIG_FILE = 'config.yaml'
with open(CONFIG_FILE, 'r') as file:
    config = yaml.safe_load(file)


blacklist = config.get('blacklist', [])
interval = config.get('interval', 2)
focus_minutes = config.get('focus_minutes', 25)
focus_mode = True
focus_start_time = None
focus_end_time = None

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
            try:
                subprocess.run(["pkill", "-i", "-f", app])
                print(f"[BLOCKED] {app}")
            except subprocess.CalledProcessError:
                print(f"[ERROR] Failed to block {app}")

while True:
    active_window = get_window()
    if active_window:
        print(f"Active window: {active_window}")
        block_window(active_window)
    else:
        print("No active window found.")
    
    time.sleep(interval)