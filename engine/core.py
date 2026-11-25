"""Brand core for MAFIA NYC content: palette, fonts, drawing helpers."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
BLACK = (11, 10, 12)
CREAM = (242, 233, 220)
RED = (222, 36, 58)
DIM = (140, 128, 118)
FELT = (64, 12, 20)

BRAND = {
    "name": "MAFIA NYC",
    "handle": "@thedonstablemafia",
    "day": "ПЯТНИЦА",
    "time": "7:00 PM",
    "place": "МАНХЭТТЕН",
    "signup": "директ или Telegram",
}

# Fonts: Fira Sans (Cyrillic) + Lora Italic. Paths can be overridden with env MAFIA_FONTS dir.
_FD = os.environ.get("MAFIA_FONTS", "/usr/share/fonts/truetype/google-fonts/ofl/firasans/")
_LORA = os.environ.get("MAFIA_LORA", "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf")
_FILES = {"black": "FiraSans-Black.ttf", "bold": "FiraSans-Bold.ttf", "semi": "FiraSans-SemiBold.ttf",
          "med": "FiraSans-Medium.ttf", "light": "FiraSans-Light.ttf"}
_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc:
        path = _LORA if name == "serif_i" else os.path.join(_FD, _FILES[name])
        _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def eo(p): return 1 - (1 - p) ** 3
def eio(p): return 3 * p * p - 2 * p * p * p
def eback(p):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2

def layer(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))
def bg(color=BLACK, w=W, h=H): return Image.new("RGBA", (w, h), color + (255,))

def comp(img, lay, alpha=1.0):
    if alpha <= 0: return
    if alpha < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)

def glow(img, lay, strength=1.0, radius=18):
    w, h = img.size
    small = lay.reduce(4).filter(ImageFilter.GaussianBlur(radius / 4))
    big = small.resize((w, h), Image.BILINEAR)
    rgb = Image.new("RGB", (w, h)); rgb.paste(big, mask=big.getchannel("A"))
    if strength != 1: rgb = rgb.point(lambda v: int(min(255, v * strength)))
    img.paste(ImageChops.add(img.convert("RGB"), rgb).convert("RGBA"))

def tracked(d, cx, y, text, font, fill, track=0.25, anchor_y="m"):
    widths = [d.textlength(c, font=font) for c in text]
    total = sum(widths) + track * font.size * (len(text) - 1)
    x = cx - total / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=font, fill=fill, anchor="l" + anchor_y)
        x += w + track * font.size

def fit_font(text, name, size, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while size > 20 and d.textlength(text, font=F(name, size)) > maxw: size -= 4
    return F(name, size)

def wrap(text, font, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= maxw: cur = trial
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def kin(img, text, font, cx, y, t, t0, color, per=0.09, dur=0.32, rise=46, glow_it=False):
    """Word-by-word rise-in text, centred on cx."""
    words = text.split(" ")
    d0 = ImageDraw.Draw(img)
    sp = d0.textlength(" ", font=font)
    ws = [d0.textlength(w, font=font) for w in words]
    x = cx - (sum(ws) + sp * (len(words) - 1)) / 2
    lay = layer(*img.size); d = ImageDraw.Draw(lay); any_ = False
    for i, (w, wl) in enumerate(zip(words, ws)):
        p = prog(t, t0 + i * per, t0 + i * per + dur)
        if p > 0:
            any_ = True
            d.text((x, y + (1 - eo(p)) * rise), w, font=font, fill=color + (int(255 * clamp(p * 1.6)),), anchor="lm")
        x += wl + sp
    if any_:
        if glow_it: glow(img, lay.copy(), 0.9, 30)
        comp(img, lay)

_rad_cache = {}
def radial(cx, cy, r, color, alpha=1.0, w=W, h=H):
    key = (cx, cy, r, color, round(alpha, 3), w, h)
    if key in _rad_cache: return _rad_cache[key]
    yy, xx = np.ogrid[0:h, 0:w]
    a = np.clip(1 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r, 0, 1) ** 2 * alpha
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGBA")
    if len(_rad_cache) < 64: _rad_cache[key] = im
    return im

_post = {}
def _post_assets(w, h):
    if (w, h) not in _post:
        yy, xx = np.ogrid[0:h, 0:w]
        dd = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h / 2) / (h * 0.62)) ** 2)
        vig = np.clip(1.08 - dd ** 2 * 0.55, 0.35, 1.0)[..., None].astype(np.float32)
        rng = np.random.default_rng(7)
        grain = [rng.normal(0, 7, (h // 2 + 1, w // 2 + 1)).astype(np.float32) for _ in range(6)]
        _post[(w, h)] = (vig, grain)
    return _post[(w, h)]

def post(img, fi=0, flash=0.0, shake=(0, 0)):
    """Vignette + film grain + optional red flash and shake. Returns uint8 RGB array."""
    w, h = img.size
    if shake != (0, 0): img = ImageChops.offset(img, int(shake[0]), int(shake[1]))
    vig, grain = _post_assets(w, h)
    a = np.asarray(img.convert("RGB")).astype(np.float32) * vig
    a += grain[fi % 6].repeat(2, 0).repeat(2, 1)[:h, :w, None]
    if flash > 0: a = a * (1 - flash) + np.array(RED, np.float32) * flash
    return np.clip(a, 0, 255).astype(np.uint8)

# ---------- shared motifs ----------
def hat(d, cx, cy, s, col, band=None):
    d.ellipse((cx - 150 * s, cy - 22 * s, cx + 150 * s, cy + 30 * s), fill=col)
    d.polygon([(cx - 95 * s, cy), (cx - 80 * s, cy - 120 * s), (cx, cy - 100 * s), (cx + 80 * s, cy - 120 * s), (cx + 95 * s, cy)], fill=col)
    d.rectangle((cx - 92 * s, cy - 30 * s, cx + 92 * s, cy - 8 * s), fill=band or (BLACK + (255,)))

def eye(d, cx, cy, w, h, open_, col):
    if open_ <= 0.02:
        d.line((cx - w, cy, cx + w, cy), fill=col, width=6); return
    top, bot = [], []
    for k in range(41):
        x = -w + 2 * w * k / 40
        yv = h * open_ * (1 - (x / w) ** 2)
        top.append((cx + x, cy - yv)); bot.append((cx + x, cy + yv))
    d.polygon(top + bot[::-1], outline=col, width=6)
    pr = min(h * open_ * 0.8, 46)
    d.ellipse((cx - pr, cy - pr, cx + pr, cy + pr), fill=col)
    d.ellipse((cx - 8, cy - pr * 0.8, cx + 8, cy + pr * 0.8), fill=BLACK + (255,))

ROLES = {
    "МИРНЫЙ": ("МИРНЫЙ", "ЖИТЕЛЬ"), "ДОКТОР": ("ДОКТОР", ""), "ШЕРИФ": ("ШЕРИФ", ""),
    "МАФИЯ": ("МАФИЯ", ""), "ДОН": ("ДОН", "МАФИИ"), "МАНЬЯК": ("МАНЬЯК", ""), "ЛЮБОВНИЦА": ("ЛЮБОВНИЦА", ""),
}
CW, CH = 520, 760
_faces = {}
def card_face(kind, s=1.0):
    """kind: 'back' or a role key from ROLES."""
    key = (kind, s)
    if key in _faces: return _faces[key]
    c = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    if kind == "back":
        d.rounded_rectangle((0, 0, CW - 1, CH - 1), 36, fill=RED + (255,))
        for k in range(-12, 14):
            d.line((40 + k * 60, 40, 40 + k * 60 + 700, 740), fill=(240, 90, 100, 255), width=3)
            d.line((CW - 40 - k * 60, 40, CW - 40 - k * 60 - 700, 740), fill=(240, 90, 100, 255), width=3)
        mask = Image.new("L", (CW, CH), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, CW - 1, CH - 1), 36, fill=255)
        c.putalpha(mask); d = ImageDraw.Draw(c)
        d.rounded_rectangle((22, 22, CW - 23, CH - 23), 24, outline=CREAM + (255,), width=5)
        d.ellipse((CW / 2 - 90, CH / 2 - 90, CW / 2 + 90, CH / 2 + 90), fill=RED + (255,), outline=CREAM + (255,), width=5)
        d.text((CW / 2, CH / 2 + 4), "M", font=F("black", 120), fill=CREAM + (255,), anchor="mm")
    else:
        name, sub = ROLES.get(kind, (kind, ""))
        dark = kind in ("МАФИЯ", "ДОН", "МАНЬЯК")
        bgc, fg = ((18, 16, 18), RED) if dark else (CREAM, BLACK)
        d.rounded_rectangle((0, 0, CW - 1, CH - 1), 36, fill=bgc + (255,))
        d.rounded_rectangle((22, 22, CW - 23, CH - 23), 24, outline=fg + (255,), width=4)
        if dark:
            hat(d, CW / 2, 330, 1.25, RED + (255,), band=(18, 16, 18, 255))
        else:
            d.ellipse((CW / 2 - 110, 200, CW / 2 + 110, 420), outline=fg + (255,), width=6)
            d.text((CW / 2, 312), name[0], font=F("serif_i", 150), fill=fg + (255,), anchor="mm")
        f = fit_font(name, "black", 96, CW - 80)
        d.text((CW / 2, 560), name, font=f, fill=fg + (255,), anchor="mm")
        if sub: d.text((CW / 2, 645), sub, font=F("med", 44), fill=fg + (255,), anchor="mm")
    _faces[key] = c
    return c
