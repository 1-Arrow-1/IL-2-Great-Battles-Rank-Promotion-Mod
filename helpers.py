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
        return "\u00A0".join(first) + "\u00A0\u00A0" + "\u00A0".join(last)
    else:
        return "\u00A0".join(full_name)

def draw_spaced_name(draw, x_center, y, name, font, gap_factor=1.25):
    first_last = name.strip().split(None, 1)
    chars = list(first_last[0]) + ['  '] + list(first_last[1]) if len(first_last) == 2 else list(name)

    # Measure total width dynamically
    widths = []
    for c in chars:
        if c.strip() == '':
            space_width = draw.textlength(' ', font=font)
            widths.append(space_width * 2)  # double space between names
        else:
            w = draw.textlength(c, font=font)
            widths.append(w * gap_factor)

    total_width = sum(widths)
    x = x_center - total_width / 2

    for c, w in zip(chars, widths):
        if c.strip() == '':
            x += w  # spacing only
        else:
            draw.text((x, y), c, font=font, fill=(0, 0, 0, 255))
            x += w

        
def cleanup_orphaned_promotion_attempts(conn):
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM promotion_attempts
        WHERE pilotId NOT IN (SELECT id FROM pilot)
    """)
    conn.commit()
    log("[CLEANUP] Removed orphaned entries from promotion_attempts")