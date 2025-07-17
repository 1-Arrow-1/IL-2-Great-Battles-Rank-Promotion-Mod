# config.py
import os
import sys
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Resource path logic for PyInstaller bundles or script run
if getattr(sys, "frozen", False):
    RESOURCE_PATH = sys._MEIPASS
else:
    RESOURCE_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE       = "promotion_config.json"
POLL_INTERVAL     = 5  # seconds
LOG_FILE          = "promotion_debug.log"
DEFAULT_THRESHOLDS = [
    [210,  60, 0.10], [270,  80, 0.10], [340, 100, 0.10],
    [420, 150, 0.075], [500, 200, 0.075], [590, 250, 0.075],
    [690, 350, 0.07], [800, 450, 0.06], [920, 600, 0.05],
]
LOCALE_MAP = {
    "RU": "rus", "CHS": "chs", "ENG": "eng", "DEU": "ger",
    "ESP": "spa", "POL": "pol", "FRA": "fra"
}
CEREMONY_MAP = {
    101: "Ceremony_RU.png",
    102: "Ceremony_GB.png",
    103: "Ceremony_US.png",
    201: "Ceremony_DE.png",
}


# --- Config ---
def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # ensure defaults for each country
        defaults = {'101':5,'102':5,'103':5,'201':5}
        cfg['max_ranks'] = {**defaults, **cfg.get('max_ranks', {})}
        # fallback values
        cfg['PROMOTION_COOLDOWN_DAYS'] = int(cfg.get('PROMOTION_COOLDOWN_DAYS', 2))
        cfg['PROMOTION_FAIL_THRESHOLD'] = int(cfg.get('PROMOTION_FAIL_THRESHOLD', 3))
        return cfg
        
    return {"max_ranks": {'101':5, '102':5, '103':5, '201':5},
        "PROMOTION_COOLDOWN_DAYS": 2,
        "PROMOTION_FAIL_THRESHOLD": 3
    }

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def setup_config(root) -> dict:
    # 1) Pfad abfragen
    game_path = filedialog.askdirectory(parent=root, title="Select IL-2 install folder (root)")
    if not game_path:
        messagebox.showinfo("Abbruch", "Kein Pfad gewählt.", parent=root)
        sys.exit(0)

    # 2) Sprache + pro-Land Max Rank abfragen
    dlg = tk.Toplevel(root)
    dlg.title("Configuration")
    dlg.resizable(False, False)
    dlg.attributes("-topmost", True)
    dlg.lift()
    dlg.grab_set()

    # Language
    tk.Label(dlg, text="Language:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    lang_var = tk.StringVar(value="ENG")
    ttk.Combobox(
        dlg,
        textvariable=lang_var,
        state="readonly",
        values=list(LOCALE_MAP.keys())
    ).grid(row=0, column=1, padx=10, pady=5)

    # Max Ranks pro Country
    labels = [("Soviet Union (101):",5),
              ("Great Britain (102):",5),
              ("USA (103):",5),
              ("Germany (201):",5)]
    vars_rank = []
    for i,(text,default) in enumerate(labels, start=1):
        tk.Label(dlg, text=text).grid(row=i, column=0, padx=10, pady=2, sticky="w")
        var = tk.IntVar(value=default)
        ttk.Combobox(
            dlg,
            textvariable=var,
            state="readonly",
            values=list(range(5,14))
        ).grid(row=i, column=1, padx=10, pady=2)
        vars_rank.append(var)

    def on_ok():
        dlg.destroy()
    def on_cancel():
        dlg.destroy()
        sys.exit(0)

    btnf = tk.Frame(dlg)
    btnf.grid(row=5, column=0, columnspan=2, pady=10)
    ttk.Button(btnf, text="OK", command=on_ok).pack(side="left", padx=5)
    ttk.Button(btnf, text="Cancel", command=on_cancel).pack(side="left", padx=5)

    root.wait_window(dlg)

    max_ranks = {
        '101': vars_rank[0].get(),
        '102': vars_rank[1].get(),
        '103': vars_rank[2].get(),
        '201': vars_rank[3].get(),
    }
    cfg = {
        "game_path":  game_path,
        "max_ranks":  max_ranks,
        "language":   lang_var.get(),
        "thresholds": DEFAULT_THRESHOLDS
    }
    save_config(cfg)
    return cfg
