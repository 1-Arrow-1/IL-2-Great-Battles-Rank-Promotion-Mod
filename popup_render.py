# In ui.py or a new file like popup_render.py

import os
from PIL import Image, ImageDraw, ImageFont
from config import RESOURCE_PATH, LOCALE_MAP
from helpers import parse_flexible_date
from ranks import get_rank_name
from config import RESOURCE_PATH
from logger import log
from certificates import (
    generate_certificate_image_DE, generate_certificate_image_US,
    generate_certificate_image_CCCP, generate_certificate_image_GB
)
import unicodedata

def render_promotion_popup_to_image(ceremony, insignia, rank_title, language,
                                     country=None, first=None, last=None,
                                     old_rank_id=None, new_rank_id=None,
                                     latest_mission_date=None,
                                     INSIGNIA_BASE=None):
    try:
        def is_latin(text):
            return all('LATIN' in unicodedata.name(char, '') for char in text if char.isalpha())

        def is_cyrillic(text):
            return any('CYRILLIC' in unicodedata.name(char, '') for char in text)

        def is_chinese(text):
            return any('\u4e00' <= char <= '\u9fff' for char in text)
            
        # --- Setup ---
        name = f"{first} {last}".strip()
        locale = LOCALE_MAP.get(language.upper(), "eng")
        year = 1941
        try:
            if latest_mission_date:
                year = parse_flexible_date(latest_mission_date).year
        except Exception:
            pass

        old_rank = get_rank_name(country, old_rank_id, year, INSIGNIA_BASE, locale) if old_rank_id is not None else ""
        new_rank = get_rank_name(country, new_rank_id, year, INSIGNIA_BASE, locale) if new_rank_id is not None else ""

        # --- Certificate Image Generation ---
        template_map = {
            201: "certificate_template.png",
            103: "Promotion_certificate_US.png",
            101: "Promotion_certificate_RU.png",
            102: "Promotion_certificate_GB.png"
        }
        cert_img = None
        if country in template_map:
            template_path = os.path.join(RESOURCE_PATH, template_map[country])
            if os.path.exists(template_path):
                if country == 201:
                    cert_img = generate_certificate_image_DE(template_path, name, old_rank, new_rank, latest_mission_date)
                elif country == 103:
                    cert_img = generate_certificate_image_US(template_path, name, old_rank, new_rank, latest_mission_date)
                elif country == 101:
                    cert_img = generate_certificate_image_CCCP(template_path, name, old_rank, new_rank, latest_mission_date)
                elif country == 102:
                    cert_img = generate_certificate_image_GB(template_path, name, old_rank, new_rank, latest_mission_date)

        # --- Load Other Images ---
        ceremony_img = Image.open(ceremony) if os.path.exists(ceremony) else None
        insignia_img = Image.open(insignia) if os.path.exists(insignia) else None

        # --- Scaling ---
        cert_img = cert_img.resize((int(cert_img.width * 0.9), int(cert_img.height * 0.9)), Image.LANCZOS)
        if insignia_img:
            insignia_img = insignia_img.resize((int(insignia_img.width * 1.3), int(insignia_img.height * 1.3)), Image.LANCZOS)
        if ceremony_img:
            ceremony_img = ceremony_img.resize((cert_img.height, cert_img.height), Image.LANCZOS)

        # --- Layout Sizes ---
        gap = 20
        bg_color = (25, 25, 25)
        w = (ceremony_img.width if ceremony_img else 0) + cert_img.width + (insignia_img.width if insignia_img else 300) + gap * 6
        h = cert_img.height + 80

        result = Image.new("RGB", (w, h), bg_color)
        draw = ImageDraw.Draw(result)

        # --- Composite Layout ---
        x = gap
        if ceremony_img:
            result.paste(ceremony_img, (x, gap))
            x += ceremony_img.width + gap

        result.paste(cert_img, (x, gap))
        x += cert_img.width + gap

        text_x = x
        y_cursor = gap + 20
        
        def select_display_font(text, size):
            if is_latin(text):
                return ImageFont.truetype(os.path.join(RESOURCE_PATH, "Darwin Pro Light.otf"), size)
            elif is_cyrillic(text) or is_chinese(text):
                return ImageFont.truetype(os.path.join(RESOURCE_PATH, "DejaVuSans.ttf"), size)
            else:
                return ImageFont.truetype(os.path.join(RESOURCE_PATH, "DejaVuSans.ttf"), size)
                
        #font_path = os.path.join(RESOURCE_PATH, "Darwin Pro Light.otf")
        

        intro_map = {
            "ENG": "Congratulations – \nyou have been promoted to:",
            "DEU": "Herzlichen Glückwunsch – \nSie wurden befördert zu:",
            "RU": "Поздравляем – \nвы были повышены до:",
            "CHS": "祝贺 – \n您已晋升为：",
            "ESP": "¡Felicidades – \nhas sido ascendido a:",
            "FRA": "Félicitations – \nVous avez été promu au:",
            "POL": "Gratulacje – \nZostałeś awansowany na:"
        }
        # Determine available width for right section
        right_section_width = insignia_img.width if insignia_img else 300

        # Draw intro text centered
        intro_text = intro_map.get(language.upper(), intro_map["ENG"])
        font_label = select_display_font(intro_text, 22)
        font_rank  = select_display_font(new_rank, 24)
        bbox = draw.textbbox((0, 0), intro_text, font=font_label)
        intro_w = bbox[2] - bbox[0]
        intro_h = bbox[3] - bbox[1]
        intro_x = text_x + (right_section_width - intro_w) // 2
        draw.text((intro_x, y_cursor), intro_text, fill=(218, 218, 218), font=font_label)
        y_cursor += intro_h + 10

        if insignia_img:
            insignia_x = text_x + (right_section_width - insignia_img.width) // 2
            result.paste(insignia_img, (insignia_x, y_cursor), mask=insignia_img.convert("RGBA"))
            y_cursor += insignia_img.height + 10

        bbox = draw.textbbox((0, 0), new_rank, font=font_rank)
        rank_w = bbox[2] - bbox[0]
        rank_h = bbox[3] - bbox[1]
        rank_x = text_x + (right_section_width - rank_w) // 2
        draw.text((rank_x, y_cursor), new_rank, fill=(78, 165, 245), font=font_rank)




        # --- Save Image ---
        filename = f"promotion_popup_{country}_{name.replace(' ', '_')}_{new_rank}_{latest_mission_date}.png"
        filepath = os.path.join(os.getcwd(), filename)
        result.save(filepath)
        log(f"Saved full promotion popup to: {filepath}")

    except Exception as e:
        log(f"[ERROR] Failed to render popup image: {e}")
