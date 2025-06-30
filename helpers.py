import os
import psutil
import ctypes
import unicodedata
from datetime import datetime
from logger import log
from config import RESOURCE_PATH

# --- Helpers ---
def is_il2_running() -> bool:
    for p in psutil.process_iter(("name",)):
        try:
            if p.info["name"] and p.info["name"].lower() == "il-2.exe":
                return True
        except:
            pass
    return False

# --- Private Font Loader --------------------------------
def load_private_font(font_file: str):
    path = os.path.join(RESOURCE_PATH, font_file)
    if os.path.exists(path):
        try:
            ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0)
            log(f"Loaded font {font_file}")
        except Exception as e:
            log(f"Failed loading font {font_file}: {e}")
    else:
        log(f"Font not found: {font_file}")
        
def parse_flexible_date(date_str):
    """
    Parse a date string in either 'YYYY-MM-DD' or 'YYYY.MM.DD' format.
    Raises ValueError if the format is unrecognized.
    """
    for fmt in ("%Y-%m-%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date '{date_str}' is not in a recognized format ('%Y-%m-%d' or '%Y.%m.%d')")

def select_font_for_text(text):
    """
    Select a suitable font for the input text based on its script.
    """
    if all('LATIN' in unicodedata.name(char, '') for char in text if char.isalpha()):
        return "SpecialElite.ttf"
    elif any('CYRILLIC' in unicodedata.name(char, '') for char in text):
        return "Kyiv Machine.ttf"
    elif any('\u4e00' <= char <= '\u9fff' for char in text):
        return "NotoSansSC-Regular.otf"
    else:
        return "DejaVuSans.ttf"
        
def spaced_out_name(full_name):
    parts = full_name.strip().split(None, 1)
    if len(parts) == 2:
        first, last = parts
        return " ".join(first) + "  " + " ".join(last)
    else:
        return " ".join(full_name)