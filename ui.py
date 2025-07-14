# ui.py
import os
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk
from logger import log
import queue
from config import *
from helpers import spaced_out_name, parse_flexible_date
from ranks import get_rank_name
from certificates import (
    generate_certificate_image_DE, generate_certificate_image_US,
    generate_certificate_image_CCCP, generate_certificate_image_GB
)
# will be injected by main.py after computing insignia_base
INSIGNIA_BASE = None

# --- Player Popup (unchanged) ---
def show_promotion_popup(ceremony, insignia, rank_title, language, on_close,
                         country=None, first=None, last=None,
                         old_rank_id=None, new_rank_id=None, latest_mission_date=None
                         ):
    

    popup = tk.Toplevel(_root)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.configure(bg="#3f3f3f")
    
    # Frame containing everything
    container = tk.Frame(popup, bg="#3f3f3f")
    container.pack(padx=3, pady=3, fill="both", expand=True)

    # Main content goes in here
    content_frame = tk.Frame(container, bg="#191919")
    content_frame.pack(fill="both", expand=True)
    
    outer = tk.Frame(content_frame, bg="#191919")
    outer.pack(side="top", fill="both", expand=True)
    #outer = tk.Frame(popup, bg="#191919")
    #outer.pack(padx=3, pady=3)
    

    # Left: Ceremony
    left = tk.Frame(outer, bg="#191919")
    left.pack(side="left", anchor="n")
    if ceremony and os.path.exists(ceremony):
        img_c = Image.open(ceremony)
        ph_c  = ImageTk.PhotoImage(img_c, master=popup)
        lbl_c = tk.Label(left, image=ph_c, bg="#191919")
        lbl_c.image = ph_c
        lbl_c.pack(padx=(10,20), pady=10)
    else:
        log(f"Ceremony missing: {ceremony}")

    # Middle: certificate for all countries (dynamic)
    template_map = {
        country: os.path.join(RESOURCE_PATH, filename)
        for country, filename in {
            201: "certificate_template.png",
            103: "Promotion_certificate_US.png",
            101: "Promotion_certificate_RU.png",
            102: "Promotion_certificate_GB.png"
        }.items()
    }

    # --- Get name, ranks, locale ---
    name = f"{first} {last}".strip() if first and last else ""
    locale = LOCALE_MAP.get(language.upper(), "eng") #if LOCALE_MAP else "eng"
    year = None
    try:
        year = parse_flexible_date(latest_mission_date).year if latest_mission_date else 1941
    except Exception:
        year = 1941

    # Dynamic rank fetching
    old_rank = get_rank_name(country, old_rank_id, year, INSIGNIA_BASE, locale) if old_rank_id is not None else ""
    new_rank = get_rank_name(country, new_rank_id, year, INSIGNIA_BASE, locale) if new_rank_id is not None else ""

    # German name is spaced out for authenticity
    #display_name = name

    # --- Certificate generator dispatch ---
    cert_img = None
    if country in template_map and os.path.exists(template_map[country]):
        template_path = template_map[country]
        if country == 201:
            cert_img = generate_certificate_image_DE(template_path, name, old_rank, new_rank, latest_mission_date)
        elif country == 103:
            cert_img = generate_certificate_image_US(template_path, name, old_rank, new_rank, latest_mission_date)
        elif country == 101:
            cert_img = generate_certificate_image_CCCP(template_path, name, old_rank, new_rank, latest_mission_date)
        elif country == 102:
            cert_img = generate_certificate_image_GB(template_path, name, old_rank, new_rank, latest_mission_date)
    else:
        log(f"No template for country {country}, or template not found.")

    # --- Save and show certificate ---
    if cert_img:
        filename = f"promotion_certificate_{country}_{name.replace(' ', '_')}_{new_rank}_{latest_mission_date}.png"
        try:
            cert_img.save(filename)
            log(f"Certificate saved to {filename}")
        except Exception as e:
            log(f"Failed to save certificate: {e}")

        factor = 1  # adjust as needed for scaling
        cert_width = int(cert_img.width * factor)
        cert_height = int(cert_img.height * factor)
        cert_tk = ImageTk.PhotoImage(
            cert_img.resize((cert_width, cert_height), Image.LANCZOS),
            master=popup
        )

        mid = tk.Frame(outer, bg="#191919")
        mid.pack(side="left", anchor="n", padx=(0, 20))
        tk.Label(mid, image=cert_tk, bg="#191919").pack()
        mid.cert_img = cert_tk  # avoid GC

    # Right: as before
    right = tk.Frame(outer, bg="#191919")
    right.pack(side="left", fill="both", expand=True)
    tk.Frame(right, bg="#191919").pack(side="top", fill="y", expand=True)
    content = tk.Frame(right, bg="#191919")
    content.pack(anchor="center")
    font_c = tkfont.Font(family="Darwin Pro Light", size=16)
    intros = {
        "ENG":"Congratulations –\nyou have been promoted to:",
        "DEU":"Herzlichen Glückwunsch –\nSie wurden befördert zu:",
        "RU":"Поздравляем –\nвы были повышены до:",
        "CHS":"祝贺 –\n您已晋升为：",
        "ESP":"¡Felicidades –\nhas sido ascendido a:",
        "FRA":"Félicitations –\nVous avez été promu au:",
        "POL":"Gratulacje –\nZostałeś awansowany na:"
    }
    intro_text = intros.get(language.upper(), intros["ENG"])
    tk.Label(
        content, text=intro_text, fg="#dadada", bg="#191919",
        font=font_c, justify="center"
    ).pack(pady=(0,4))
    if os.path.exists(insignia):
        img_i = Image.open(insignia)
        w, h = img_i.size
        img_i = img_i.resize((int(w*1.3), int(h*1.3)), Image.LANCZOS)
        ph_i  = ImageTk.PhotoImage(img_i, master=popup)
        lbl_i = tk.Label(content, image=ph_i, bg="#191919")
        lbl_i.image = ph_i
        lbl_i.pack(pady=(0,4))
    else:
        log(f"Insignia missing: {insignia}")
    tk.Label(
        content, text=rank_title, fg="#4ea5f5", bg="#191919",
        font=font_c, justify="center"
    ).pack(pady=(0,10))
    tk.Frame(right, bg="#191919").pack(side="top", fill="y", expand=True)
    
    # --- Manual Close Button ---
    close_button = tk.Button(
        container,
        text="Close",
        command=on_close,
        bg="#2f2f2f",
        fg="#dadada",
        font=tkfont.Font(size=12)
    )
    close_button.pack(side="bottom", pady=(5, 5))

    popup.update_idletasks()
    rw, rh = popup.winfo_reqwidth(), popup.winfo_reqheight()
    sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
    popup.geometry(f"{rw}x{rh}+{(sw-rw)//2}+{(sh-rh)//2}")
    
    popup.after(18000, on_close)
    return popup


# --- AI Popup (updated signature) ---
def show_ai_promotion_popup(name, before_insignia, after_insignia, rank_title, language, on_close):
    """
    AI pop-up now shows:
     1) Header + subtext
     2) "before promotion" insignia
     3) "<Name> – Promotion to <rank_title>"
     4) "after promotion" insignia
    """
    popup = tk.Toplevel(_root)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.configure(bg="#3f3f3f")

    outer = tk.Frame(popup, bg="#191919")
    outer.pack(padx=3, pady=3)

    headers = {
        "ENG":"Promotion news",
        "DEU":"Beförderungsmitteilung",
        "RU":"Новости о повышении",
        "CHS":"晋升通知",
        "ESP":"Noticias de ascenso",
        "FRA":"Annonce de promotion",
        "POL":"Aktualności o awansie"
    }
    subs = {
        "ENG":"The High Command is happy to announce the following promotions:",
        "DEU":"Das Oberkommando freut sich, folgende Beförderungen bekanntzugeben:",
        "RU":"Высокое командование с радостью сообщает о следующих повышениях:",
        "CHS":"总司令部很高兴地宣布以下晋升：",
        "ESP":"El Alto Mando se complace en anunciar los siguientes ascensos:",
        "FRA":"Le Haut Commandement est heureux d’annoncer les promotions suivantes :",
        "POL":"Wysokie Dowództwo z przyjemnością ogłasza następujące awanse:"
    }

    font_h = tkfont.Font(family="Darwin Pro Light", size=18, weight="bold")
    font_s = tkfont.Font(family="Darwin Pro Light", size=14)
    font_n = tkfont.Font(family="Darwin Pro Light", size=16)

    # 1) Header
    tk.Label(
        outer,
        text=headers.get(language, headers["ENG"]),
        fg="#dadada",
        bg="#191919",
        font=font_h
    ).pack(anchor="w", pady=(10,4), padx=10)

    # 2) Subtext
    tk.Label(
        outer,
        text=subs.get(language, subs["ENG"]),
        fg="#dadada",
        bg="#191919",
        font=font_s,
        wraplength=400,
        justify="left"
    ).pack(anchor="w", pady=(0,8), padx=10)

    # 3) Row with before insignia, name+text, after insignia
    row = tk.Frame(outer, bg="#191919")
    row.pack(anchor="w", pady=(0,10), padx=10)

    # 3a) Before-promotion insignia
    if os.path.exists(before_insignia):
        img_b = Image.open(before_insignia)
        w_b, h_b = img_b.size
        img_b = img_b.resize((int(w_b * 0.7), int(h_b * 0.7)), Image.LANCZOS)
        ph_b  = ImageTk.PhotoImage(img_b, master=popup)
        tk.Label(row, image=ph_b, bg="#191919").pack(side="left", padx=(0,8))
        row.before_photo = ph_b
    else:
        log(f"AI before-insignia missing: {before_insignia}")

    # 3b) Name + "Promotion to <rank_title>"
    texts = {
        "ENG": f"{name} – Promotion to {rank_title}",
        "DEU": f"{name} – Beförderung zu {rank_title}",
        "RU":  f"{name} – повышение до {rank_title}",
        "CHS": f"{name} – 晋升为{rank_title}",
        "ESP": f"{name} – Ascenso a {rank_title}",
        "FRA": f"{name} – Promotion au grade {rank_title}",
        "POL": f"{name} – Awans do {rank_title}"
    }
    tk.Label(
        row,
        text=texts.get(language, texts["ENG"]),
        fg="#dadada",
        bg="#191919",
        font=font_n,
        justify="left"
    ).pack(side="left")

    # 3c) After-promotion insignia
    if os.path.exists(after_insignia):
        img_a = Image.open(after_insignia)
        w_a, h_a = img_a.size
        img_a = img_a.resize((int(w_a * 0.7), int(h_a * 0.7)), Image.LANCZOS)
        ph_a  = ImageTk.PhotoImage(img_a, master=popup)
        tk.Label(row, image=ph_a, bg="#191919").pack(side="left", padx=(8,0))
        row.after_photo = ph_a
    else:
        log(f"AI after-insignia missing: {after_insignia}")

    popup.update_idletasks()
    rw, rh = popup.winfo_reqwidth(), popup.winfo_reqheight()
    sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
    popup.geometry(f"{rw}x{rh}+{(sw-rw)//2}+{(sh-rh)//2}")
    popup.after(10000, on_close)
    return popup
    
# ——————————————————————————————————————————————————————————————————
# 1) New dispatcher — pulls one item, shows it, and only when
#    the popup destroys itself does it call itself again
def show_next_popup():
    try:
        kind, *args = popup_queue.get_nowait()
    except queue.Empty:
        # keep polling until there is something to show
        _root.after(100, show_next_popup)
        return
    log(f"Dequeued popup kind: {kind}, args: {args}")
    
    # when this popup closes we want to show the next one
    def on_close():
        popup.destroy()
        show_next_popup()

    try:
        if kind == "ai":
            popup = show_ai_promotion_popup(*args, on_close=on_close)
        else:
            log(f"Showing promotion ceremony for player: {args}")
            # Separate out the player args and pass explicitly
            (
                ceremony, insignia, rank_title, language,
                country, first, last, old_rank_id, new_rank_id, latest_mission_date
            ) = args
            popup = show_promotion_popup(
                ceremony, insignia, rank_title, language, on_close,
                country=country, first=first, last=last,
                old_rank_id=old_rank_id, new_rank_id=new_rank_id,
                latest_mission_date=latest_mission_date
            )
    except Exception as e:
        log(f"Exception in popup: {e}")
        _root.after(0, show_next_popup)
        return
