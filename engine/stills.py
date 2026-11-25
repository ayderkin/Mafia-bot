"""Static stories (1080x1920) and posters (1080x1350 / 1080x1920)."""
from PIL import Image, ImageDraw
from .core import *

MONTHS = ["ЯНВАРЯ", "ФЕВРАЛЯ", "МАРТА", "АПРЕЛЯ", "МАЯ", "ИЮНЯ", "ИЮЛЯ", "АВГУСТА", "СЕНТЯБРЯ", "ОКТЯБРЯ", "НОЯБРЯ", "ДЕКАБРЯ"]

def plural_days(n):
    if n % 10 == 1 and n % 100 != 11: return "ДЕНЬ"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14: return "ДНЯ"
    return "ДНЕЙ"

def _save(img, path, fi=0):
    Image.fromarray(post(img, fi)).save(path, quality=93)

def _header(img, w):
    d = ImageDraw.Draw(img)
    tracked(d, w / 2, 130, BRAND["name"], F("semi", 34), CREAM + (200,), 0.5)
    d.line((w / 2 - 60, 175, w / 2 + 60, 175), fill=RED + (255,), width=3)

def _footer(img, w, h, cta=None):
    d = ImageDraw.Draw(img)
    if cta:
        f = fit_font(cta, "black", 52, w - 300)
        d.rounded_rectangle((150, h - 330, w - 150, h - 210), 60, fill=RED + (255,))
        d.text((w / 2, h - 270), cta, font=f, fill=CREAM + (255,), anchor="mm")
    d.text((w / 2, h - 140), BRAND["handle"], font=F("med", 40), fill=DIM + (255,), anchor="mm")

def _when(d, w, y, color=CREAM):
    tracked(d, w / 2, y, f'{BRAND["day"]} · {BRAND["time"]} · {BRAND["place"]}', F("semi", 42), color + (255,), 0.15)

def story_countdown(path, days):
    img = bg(); img.alpha_composite(radial(540, 820, 900, (120, 16, 30), 0.5))
    _header(img, W); d = ImageDraw.Draw(img)
    if days <= 0:
        return story_gameday(path)
    big = str(days)
    lay = layer(); dl = ImageDraw.Draw(lay)
    dl.text((540, 780), big, font=F("black", 620), fill=RED + (255,), anchor="mm")
    glow(img, lay.copy(), 1.0, 60); comp(img, lay)
    d = ImageDraw.Draw(img)
    d.text((540, 1170), f"{plural_days(days)} ДО ИГРЫ", font=F("black", 110), fill=CREAM + (255,), anchor="mm")
    _when(d, W, 1300)
    _footer(img, W, H, "ЗАНЯТЬ МЕСТО")
    _save(img, path)

def story_gameday(path, line="ЕЩЁ ЕСТЬ СВОБОДНЫЕ МЕСТА"):
    img = bg(); img.alpha_composite(radial(540, 700, 800, (140, 14, 30), 0.55))
    _header(img, W)
    lay = layer(); dl = ImageDraw.Draw(lay)
    eye(dl, 360, 520, 140, 80, 1.0, RED + (255,)); eye(dl, 720, 520, 140, 80, 1.0, RED + (255,))
    dl.text((540, 860), "СЕГОДНЯ", font=F("black", 220), fill=RED + (255,), anchor="mm")
    glow(img, lay.copy(), 1.1, 50); comp(img, lay)
    d = ImageDraw.Draw(img)
    d.text((540, 1100), BRAND["time"], font=fit_font(BRAND["time"], "black", 260, 900), fill=CREAM + (255,), anchor="mm")
    tracked(d, 540, 1300, BRAND["place"], F("semi", 50), CREAM + (255,), 0.45)
    tracked(d, 540, 1400, line, F("med", 36), DIM + (255,), 0.15)
    _footer(img, W, H, "ПИШИ — ЗАПИШЕМ")
    _save(img, path)

def story_role(path, role, text):
    img = bg(); img.alpha_composite(radial(540, 700, 800, (120, 16, 30), 0.45))
    _header(img, W); d = ImageDraw.Draw(img)
    tracked(d, 540, 260, "РОЛЬ ДНЯ", F("semi", 44), RED + (255,), 0.45)
    c = card_face(role).resize((int(CW * 0.82), int(CH * 0.82)), Image.BICUBIC)
    if role in ("МАФИЯ", "ДОН", "МАНЬЯК"):
        g = layer(); g.alpha_composite(c, (540 - c.width // 2, 340))
        r = Image.new("RGBA", (W, H), RED + (0,)); r.putalpha(g.getchannel("A")); glow(img, r, 0.9, 60)
    img.alpha_composite(c, (540 - c.width // 2, 340))
    d = ImageDraw.Draw(img)
    f = F("med", 50)
    y = 1040
    for ln in wrap(text, f, 860)[:6]:
        d.text((540, y), ln, font=f, fill=CREAM + (255,), anchor="mm"); y += 70
    _footer(img, W, H, "А ТЫ СЫГРАЕШЬ ЕЁ?")
    _save(img, path)

def story_fact(path, title, text):
    img = bg(); img.alpha_composite(radial(540, 900, 900, (110, 14, 28), 0.4))
    _header(img, W); d = ImageDraw.Draw(img)
    hat(d, 540, 420, 0.7, CREAM + (255,))
    tracked(d, 540, 540, title, F("semi", 44), RED + (255,), 0.4)
    f = F("black", 82); lines = wrap(text, f, 900)
    if len(lines) > 7: f = F("black", 66); lines = wrap(text, f, 920)
    y = 960 - (len(lines) - 1) * f.size * 0.6
    for ln in lines:
        d.text((540, y), ln, font=f, fill=CREAM + (255,), anchor="mm"); y += f.size * 1.2
    _footer(img, W, H, None)
    tracked(d, 540, 1600, "ПРОВЕРИШЬ ЗА СТОЛОМ?", F("semi", 40), DIM + (255,), 0.25)
    _save(img, path)

def story_question(path, question, hint="ОТВЕТЬ В ОПРОСЕ НИЖЕ"):
    img = bg(); img.alpha_composite(radial(540, 600, 800, (120, 16, 30), 0.45))
    _header(img, W); d = ImageDraw.Draw(img)
    d.text((540, 330), "?", font=F("black", 260), fill=RED + (255,), anchor="mm")
    f = F("black", 92); lines = wrap(question, f, 900)
    y = 640
    for ln in lines[:5]:
        d.text((540, y), ln, font=f, fill=CREAM + (255,), anchor="mm"); y += 110
    tracked(d, 540, y + 50, hint, F("semi", 38), DIM + (255,), 0.25)
    # reserved zone for Instagram poll sticker
    top = y + 140
    for x in range(160, 920, 40): d.line((x, top, x + 20, top), fill=(70, 62, 64, 255), width=3)
    for x in range(160, 920, 40): d.line((x, top + 360, x + 20, top + 360), fill=(70, 62, 64, 255), width=3)
    d.text((540, H - 140), BRAND["handle"], font=F("med", 40), fill=DIM + (255,), anchor="mm")
    _save(img, path)

def story_quote(path, quote, author=""):
    img = bg(); img.alpha_composite(radial(540, 900, 900, (110, 14, 28), 0.35))
    _header(img, W); d = ImageDraw.Draw(img)
    d.text((540, 520), "«", font=F("black", 300), fill=RED + (255,), anchor="mm")
    f = F("serif_i", 84); lines = wrap(quote, f, 880)
    y = 760
    for ln in lines[:7]:
        d.text((540, y), ln, font=f, fill=CREAM + (255,), anchor="mm"); y += 110
    if author: tracked(d, 540, y + 50, author.upper(), F("semi", 38), DIM + (255,), 0.3)
    _footer(img, W, H, f"КАЖДУЮ ПЯТНИЦУ · {BRAND['time']}")
    _save(img, path)

def story_thanks(path, text="Спасибо всем, кто был за столом! Кто сегодня блефовал лучше всех? Отмечай в комментариях."):
    img = bg(); img.alpha_composite(radial(540, 800, 900, (120, 16, 30), 0.45))
    _header(img, W); d = ImageDraw.Draw(img)
    hat(d, 540, 450, 0.9, RED + (255,))
    d.text((540, 650), "СПАСИБО", font=F("black", 190), fill=CREAM + (255,), anchor="mm")
    d.text((540, 830), "ЗА ИГРУ", font=F("black", 190), fill=RED + (255,), anchor="mm")
    f = F("med", 50); y = 1040
    for ln in wrap(text, f, 860)[:5]:
        d.text((540, y), ln, font=f, fill=CREAM + (255,), anchor="mm"); y += 70
    _footer(img, W, H, "СЛЕДУЮЩАЯ ИГРА — ПЯТНИЦА")
    _save(img, path)

def poster(path, date, size="4x5", extra=""):
    """Game poster. date: datetime.date of the game."""
    w, h = (1080, 1350) if size == "4x5" else (1080, 1920)
    img = bg(w=w, h=h); img.alpha_composite(radial(w // 2, int(h * 0.38), 900, (120, 16, 30), 0.5, w, h))
    d = ImageDraw.Draw(img)
    m = 50
    d.rectangle((m, m, w - m, h - m), outline=RED + (255,), width=5)
    d.rectangle((m + 16, m + 16, w - m - 16, h - m - 16), outline=(120, 100, 80, 255), width=2)
    s = h / 1350
    hat(d, w / 2, 230 * s, 0.75, CREAM + (255,))
    d.text((w / 2, 400 * s), "MAFIA", font=F("black", 230), fill=CREAM + (255,), anchor="mm")
    lay = layer(w, h); dl = ImageDraw.Draw(lay)
    dl.text((w / 2, 600 * s), "NYC", font=F("black", 230), fill=RED + (255,), anchor="mm")
    glow(img, lay.copy(), 1.0, 50); comp(img, lay)
    d = ImageDraw.Draw(img)
    d.line((w / 2 - 240, 740 * s, w / 2 + 240, 740 * s), fill=DIM + (200,), width=2)
    d.text((w / 2, 830 * s), f"{date.day} {MONTHS[date.month - 1]}", font=F("black", 110), fill=CREAM + (255,), anchor="mm")
    tracked(d, w / 2, 940 * s, f'{BRAND["day"]} · {BRAND["time"]}', F("semi", 50), CREAM + (255,), 0.2)
    tracked(d, w / 2, 1010 * s, BRAND["place"], F("semi", 50), RED + (255,), 0.45)
    if extra: d.text((w / 2, 1068 * s), extra, font=fit_font(extra, "med", 40, w - 240), fill=DIM + (255,), anchor="mm")
    cy = 1150 * s
    d.rounded_rectangle((170, cy - 55, w - 170, cy + 55), 55, fill=RED + (255,))
    d.text((w / 2, cy), "ЗАПИСЬ: " + BRAND["signup"].upper(), font=fit_font("ЗАПИСЬ: " + BRAND["signup"].upper(), "black", 46, w - 400), fill=CREAM + (255,), anchor="mm")
    d.text((w / 2, h - 88 * s), BRAND["handle"], font=F("med", 38), fill=DIM + (255,), anchor="mm")
    _save(img, path)
