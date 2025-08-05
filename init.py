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

