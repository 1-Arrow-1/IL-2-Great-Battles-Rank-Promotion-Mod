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

# Optionally support transliteration if installed
try:
    from transliterate import translit
    HAS_TRANSLIT = True
except ImportError:
    HAS_TRANSLIT = False

try:
    from pypinyin import lazy_pinyin
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

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

def get_font_info(text: str, context: str = "ui"):
    """
    Returns (family_name, font_file) based on text and usage context.
    context: "ui" or "certificate"
    """
    # You can further expand these for more nuanced choices
    if context == "certificate":
        if all('LATIN' in unicodedata.name(char, '') for char in text if char.isalpha()):
            return ("Special Elite", "SpecialElite.ttf")
        elif any('CYRILLIC' in unicodedata.name(char, '') for char in text):
            return ("Kyiv Machine", "Kyiv Machine.ttf")
        elif any('\u4e00' <= char <= '\u9fff' for char in text):
            return ("Noto Sans SC", "NotoSansSC-Regular.otf")
        else:
            return ("DejaVu Sans", "DejaVuSans.ttf")
    else:  # "ui" or default
        if all('LATIN' in unicodedata.name(char, '') for char in text if char.isalpha()):
            return ("Darwin Pro Light", "Darwin Pro Light.otf")
        elif any('CYRILLIC' in unicodedata.name(char, '') for char in text):
            return ("DejaVu Sans", "DejaVuSans.ttf")
        elif any('\u4e00' <= char <= '\u9fff' for char in text):
            return ("Noto Sans SC", "NotoSansSC-Regular.otf")
        else:
            return ("DejaVu Sans", "DejaVuSans.ttf")

def get_script(text, context="ui"):
    """
    Returns 'latin', 'cyrillic', 'chinese', or 'unknown' based on the font family returned.
    """
    family, _ = get_font_info(text, context)
    if family in ("Darwin Pro Light", "Special Elite"):
        return "latin"
    elif family in ("Kyiv Machine", "DejaVu Sans"):
        return "cyrillic"
    elif family == "Noto Sans SC":
        return "chinese"
    else:
        return "unknown"
        
def spaced_out_name(full_name):
    parts = full_name.strip().split(None, 1)
    if len(parts) == 2:
        first, last = parts
        return "\u00A0".join(first) + "\u00A0\u00A0" + "\u00A0".join(last)
    else:
        return "\u00A0".join(full_name)
        
def cleanup_orphaned_promotion_attempts(conn):
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM promotion_attempts
        WHERE pilotId NOT IN (SELECT id FROM pilot)
    """)
    conn.commit()
    log("[CLEANUP] Removed orphaned entries from promotion_attempts")

# ---- Tkinter font (for UI widgets) ----    
def get_tk_font(text, size=16, weight="normal", context="ui"):
    from tkinter import font as tkfont
    family, font_file = get_font_info(text, context)
    load_private_font(font_file)
    return tkfont.Font(family=family, size=size, weight=weight)

# ---- PIL font (for image drawing) ----
def get_pil_font(text, size=22, context="ui"):
    from PIL import ImageFont
    _, font_file = get_font_info(text, context)
    path = os.path.join(RESOURCE_PATH, font_file)
    return ImageFont.truetype(path, size)
    
# ---- Name transliteration helpers ----

def name_to_latin(name):
    """Converts a name (any script) to Latin script for DE/GB/US certificates."""
    script = get_script(name)
    if script == "latin":
        return name
    if script == "cyrillic" and HAS_TRANSLIT:
        return translit(name, 'ru', reversed=True)
    if script == "chinese" and HAS_PYPINYIN:
        return ' '.join(lazy_pinyin(name)).title()
    return name

def name_to_cyrillic(name):
    """Converts a name (any script) to Cyrillic for CCCP certificates."""
    script = get_script(name)
    if script == "cyrillic":
        return name
    if script == "latin" and HAS_TRANSLIT:
        return translit(name, 'ru')
    if script == "chinese" and HAS_PYPINYIN and HAS_TRANSLIT:
        pinyin = ' '.join(lazy_pinyin(name)).title()
        return translit(pinyin, 'ru')
    return name