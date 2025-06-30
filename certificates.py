# certificates.py

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import unicodedata
import os
from helpers import select_font_for_text, spaced_out_name, parse_flexible_date
from config import RESOURCE_PATH
from logger import log


def load_font_for(text: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Selects an appropriate font based on the script of `text` and loads it at `size`.
    Falls back to the default PIL font if the specified font cannot be loaded.
    """
    font_file = select_font_for_text(text)
    font_path = os.path.join(RESOURCE_PATH, font_file)
    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        log(f"Failed to load font '{font_file}' at {font_path}; falling back to default font.")
        return ImageFont.load_default()


def generate_certificate_image_DE(
    template_path: str,
    name: str,
    old_rank: str,
    new_rank: str,
    latest_mission_date_str: str
) -> Image.Image:
    cert_img = Image.open(template_path).convert("RGBA")
    overlay = Image.new("RGBA", cert_img.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)

    # Parse dates
    latest_date = parse_flexible_date(latest_mission_date_str)
    effective_date = (latest_date - timedelta(days=14)).strftime("%d.%m.%Y")
    display_date   = latest_date.strftime("%d.%m.%Y")

    # German names are spaced out for authenticity
    name_de = spaced_out_name(name)

    lines = [
        (f"den {old_rank} in der Luftwaffe", 24),
        (name_de,                     24),
        (f"mit Wirkung vom {effective_date} zum", 24),
        (" ".join(new_rank),         24),
    ]
    y = 300
    line_spacing = 38
    image_width, _ = cert_img.size

    # Draw each line centered
    for text, size in lines:
        font = load_font_for(text, size)
        bbox = draw.textbbox((0,0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (image_width - text_width) / 2
        draw.text((x, y), text, font=font, fill=(0,0,0,255))
        y += line_spacing

    # Draw the display date
    font = load_font_for(display_date, 24)
    bbox = draw.textbbox((0,0), display_date, font=font)
    date_width = bbox[2] - bbox[0]
    x_date = ((image_width - date_width) / 2) + 35
    y_bottom = cert_img.size[1] - 350
    draw.text((x_date, y_bottom), display_date, font=font, fill=(0,0,0,255))

    return Image.alpha_composite(cert_img, overlay)


def generate_certificate_image_US(
    template_path: str,
    name: str,
    old_rank: str,
    new_rank: str,
    latest_mission_date_str: str
) -> Image.Image:
    cert_img = Image.open(template_path).convert("RGBA")
    overlay = Image.new("RGBA", cert_img.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)
    image_width, _ = cert_img.size

    # Parse dates
    latest_date    = parse_flexible_date(latest_mission_date_str)
    effective_date = latest_date - timedelta(days=14)

    # Helper for year and ordinals
    def year_to_words_manual(year: int) -> str:
        mapping = {
            40: "forty", 41: "forty-one", 42: "forty-two",
            43: "forty-three", 44: "forty-four", 45: "forty-five",
            46: "forty-six", 47: "forty-seven", 48: "forty-eight",
            49: "forty-nine", 50: "fifty"
        }
        if 1940 <= year <= 1950:
            return mapping.get(year - 1900, str(year))
        return str(year)

    def ordinal_to_words(n: int) -> str:
        base = ["","first","second","third","fourth","fifth","sixth",
                "seventh","eighth","ninth","tenth","eleventh","twelfth",
                "thirteenth","fourteenth","fifteenth","sixteenth",
                "seventeenth","eighteenth","nineteenth"]
        tens = ["","","twenty","thirty"]
        if 1 <= n < 20:
            return base[n]
        if 20 <= n <= 31:
            ten, one = divmod(n, 10)
            if one == 0:
                return tens[ten] + "ieth"
            return f"{tens[ten]}-{base[one]}"
        return str(n)

    def two_digit_ordinal_to_words(n: int) -> str:
        ones = ["","first","second","third","fourth","fifth","sixth",
                "seventh","eighth","ninth"]
        teens = ["tenth","eleventh","twelfth","thirteenth","fourteenth",
                 "fifteenth","sixteenth","seventeenth","eighteenth",
                 "nineteenth"]
        tens = ["","","twenty","thirty","forty","fifty","sixty",
                "seventy","eighty","ninety"]
        tens_ord = ["","","twentieth","thirtieth","fortieth",
                    "fiftieth","sixtieth","seventieth","eightieth",
                    "ninetieth"]
        if 1 <= n < 10:
            return ones[n]
        if 10 <= n < 20:
            return teens[n - 10]
        if n % 10 == 0:
            return tens_ord[n // 10]
        return f"{tens[n // 10]}-{ones[n % 10]}"

    # Prepare text lines and positions
    line1 = f"{old_rank} {name}"
    line2 = new_rank
    line3 = ordinal_to_words(latest_date.day)
    line4 = latest_date.strftime('%B')
    line5 = year_to_words_manual(latest_date.year)
    line6 = ordinal_to_words(effective_date.day)
    line7 = effective_date.strftime('%B')
    line8 = year_to_words_manual(effective_date.year)
    line9 = two_digit_ordinal_to_words((effective_date.year - 1776) % 100)

    positions = [
        (220, 348, line1),
        (330, 395, line2),
        (330, 470, line3),
        (553, 470, line4),
        (248, 494, line5),
        (337, 787, line6),
        (571, 787, line7),
        (471, 812, line8),
        (551, 835, line9),
    ]

    SIZE = 18
    for x, y, text in positions:
        font = load_font_for(text, SIZE)
        draw.text((x, y), text, font=font, fill=(0,0,0,255))

    return Image.alpha_composite(cert_img, overlay)


def generate_certificate_image_CCCP(
    template_path: str,
    name: str,
    old_rank: str,
    new_rank: str,
    latest_mission_date_str: str
) -> Image.Image:
    cert_img = Image.open(template_path).convert("RGBA")
    overlay = Image.new("RGBA", cert_img.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)

    latest_date = parse_flexible_date(latest_mission_date_str)
    day         = str(latest_date.day)
    months_ru   = [
        "", "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    month_ru   = months_ru[latest_date.month]
    year_last2 = latest_date.strftime("%y")

    positions = [
        (203, 511, name),
        (252, 580, new_rank),
        (142, 705, day),
        (283, 700, month_ru),
        (530, 705, year_last2),
    ]

    SIZE = 24
    for x, y, text in positions:
        font = load_font_for(text, SIZE)
        draw.text((x, y), text, font=font, fill=(0,0,0,255))

    return Image.alpha_composite(cert_img, overlay)


def generate_certificate_image_GB(
    template_path: str,
    name: str,
    old_rank: str,
    new_rank: str,
    latest_mission_date_str: str
) -> Image.Image:
    cert_img = Image.open(template_path).convert("RGBA")
    overlay = Image.new("RGBA", cert_img.size, (255,255,255,0))
    draw    = ImageDraw.Draw(overlay)
    image_width, _ = cert_img.size

    latest_date = parse_flexible_date(latest_mission_date_str)
    def ordinal_suffix(n: int) -> str:
        if 10 <= n % 100 <= 20:
            return 'th'
        return {1:'st',2:'nd',3:'rd'}.get(n%10,'th')

    # Prepare lines: (text, x, y, size)
    lines = [
        (f"{old_rank} {name}",      'center', 538, 24),
        (new_rank,                  306,       585, 24),
        (f"{latest_date.day}{ordinal_suffix(latest_date.day)}", 100, 703, 24),
        (latest_date.strftime('%B'),  258,      703, 24),
        (str(latest_date.year),       416,      743, 24),
    ]

    for text, x, y, size in lines:
        font = load_font_for(text, size)
        if x == 'center':
            bbox = draw.textbbox((0,0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (image_width - text_width) // 2
        draw.text((x, y), text, font=font, fill=(0,0,0,255))

    return Image.alpha_composite(cert_img, overlay)
