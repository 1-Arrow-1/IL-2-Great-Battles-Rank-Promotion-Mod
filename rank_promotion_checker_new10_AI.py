import sqlite3
import time
import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, font as tkfont, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import ctypes
import psutil
import sys
import queue
import unicodedata
from datetime import datetime, timedelta
from config import (
    LOG_FILE, CONFIG_FILE, DEFAULT_THRESHOLDS,
    LOCALE_MAP, CEREMONY_MAP, RESOURCE_PATH,
    load_config, setup_config, POLL_INTERVAL
)
from logger import trim_log_to_last_n_missions, log
from promotion import monitor_db, try_promote, get_active_player_id, get_latest_event_year
from certificates import (
      generate_certificate_image_DE,
      generate_certificate_image_US,
      generate_certificate_image_CCCP,
      generate_certificate_image_GB,
  )
from helpers import load_private_font, is_il2_running
import promotion, ui
from ui import show_next_popup

popup_queue = queue.Queue()

promotion.popup_queue = popup_queue
ui.popup_queue = popup_queue       
    
def create_certificate_by_country(
    country, template_path, name, old_rank, new_rank, latest_mission_date_str
):
    if country == 201:
        return generate_certificate_image_DE(template_path, name, old_rank, new_rank, latest_mission_date_str)
    elif country == 103:
        return generate_certificate_image_US(template_path, name, old_rank, new_rank, latest_mission_date_str)
    elif country == 101:
        return generate_certificate_image_CCCP(template_path, name, old_rank, new_rank, latest_mission_date_str)
    elif country == 102:
        return generate_certificate_image_GB(template_path, name, old_rank, new_rank, latest_mission_date_str)
    else:
        raise ValueError(f"Unsupported country code: {country}")

def handle_promotion_certificate(
    country, old_rank_id, new_rank_id, year, name, latest_mission_date_str, base_path, locale, template_map
):
    # Get ranks dynamically:
    old_rank = get_rank_name(country, old_rank_id, year, base_path, locale)
    new_rank = get_rank_name(country, new_rank_id, year, base_path, locale)

    template_path = template_map[country]
    cert_img = create_certificate_by_country(
        country, template_path, name, old_rank, new_rank, latest_mission_date_str
    )
    return cert_img




# --- Main ---
def main():
    load_private_font("Darwin Pro Light.otf")
    root = tk.Tk()
    root.withdraw()
    # make the Tk root available to ui.show_next_popup()
    ui._root = root

    cfg = load_config() if os.path.exists(CONFIG_FILE) else setup_config(root)
    gp         = cfg['game_path']
    max_ranks  = cfg['max_ranks']
    language   = cfg['language']
    thresholds = cfg['thresholds']

    db_path       = os.path.join(gp, "data", "Career", "cp.db")
    insignia_base = os.path.join(gp, "MODS", "Ranks", "data", "swf", "il2", "charactersranks")
    # inject into ui.py so it can do get_rank_name(..., INSIGNIA_BASE, ...)
    ui.INSIGNIA_BASE = insignia_base
    
    global _root
    _root = root
    # schedule our pop-up dispatcher
    root.after(100, show_next_popup)
    ctypes.windll.user32.SetProcessDPIAware()

    def monitor_thread():
        while True:
            log("Waiting for IL-2 to start…")
            while not is_il2_running():
                time.sleep(POLL_INTERVAL)
                if not root.winfo_exists():
                    return  # Clean exit if GUI closed

            log("IL-2 detected. Starting monitor…")
            monitor_db(db_path, thresholds, max_ranks, language, insignia_base)
            log("IL-2 closed. Monitoring will restart on next launch.")

    t = threading.Thread(target=monitor_thread, daemon=True)
    t.start()
    _root.mainloop()

if __name__ == "__main__":
    main()
