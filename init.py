import subprocess
import time
import yaml
import os

CONFIG_FILE = 'config.yml'
with open(CONFIG_FILE, 'r') as file:
    config = yaml.safe_load(file)


blacklist = config.get('blacklist', [])
interval = config.get('interval', 2)

def get_window():
    try:
        window_id = subprocess.check_output(['xdotool', 'getactivewindow']).strip()
        window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).strip().decode('utf-8')
        return window_name
    except subprocess.CalledProcessError:
        return None

def block_window(window_name):
    try:
        if window_name in blacklist:
            subprocess.run(["pkill", "-i", "-f", window_name])
            print(f"Blocked: {window_name}")
    except subprocess.CalledProcessError:  
        print(f"Failed to block {window_name}")

while True:
    active_window = get_window()
    if active_window:
        print(f"Active window: {active_window}")
        block_window(active_window)
    else:
        print("No active window found.")
    
    time.sleep(interval)