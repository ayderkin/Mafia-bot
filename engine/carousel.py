"""Feed carousel (1080x1350 slides): an interesting mafia story told slide by slide.

spec = {"id": "...", "caption": "...", "slides": [
    {"kicker": "ИСТОРИЯ МАФИИ", "title": "...", "sub": "..."},   # cover (first slide)
    {"title": "...", "text": "..."},                               # story slides
    ...]}
A brand CTA slide is appended automatically as the last slide.
"""
import os
from PIL import ImageDraw
from .core import *
from .stills import _save

CW, CH = 1080, 1350

def _frame(img, d):
    m = 50
    d.rectangle((m, m, CW - m, CH - m), outline=RED + (255,), width=5)
    d.rectangle((m + 16, m + 16, CW - m - 16, CH - m - 16), outline=(120, 100, 80, 255), width=2)

def _pager(d, i, n):
    tracked(d, CW / 2, CH - 120, f"{i:02d} / {n:02d}", F("semi", 30), DIM + (255,), 0.3)

def _lines(d, text, font, maxw):
    out = []
    for para in text.split("\n"):
        out += wrap(para, font, maxw) if para.strip() else [""]
    return out

def cover(path, s, n):
    img = bg(w=CW, h=CH); img.alpha_composite(radial(CW // 2, 520, 900, (120, 16, 30), 0.55, CW, CH))
    d = ImageDraw.Draw(img); _frame(img, d)
    hat(d, CW / 2, 220, 0.6, CREAM + (255,))
    tracked(d, CW / 2, 340, s.get("kicker", "ИСТОРИЯ МАФИИ"), F("semi", 36), RED + (255,), 0.4)
    f = F("black", 112); lines = _lines(d, s["title"].upper(), f, CW - 220)
    while len(lines) > 4 and f.size > 70:
        f = F("black", f.size - 8); lines = _lines(d, s["title"].upper(), f, CW - 220)
    lh = f.size * 1.05; y0 = 690 - lh * (len(lines) - 1) / 2
    lay = layer(CW, CH); dl = ImageDraw.Draw(lay)
    for k, ln in enumerate(lines):
        col = RED if k == len(lines) - 1 else CREAM
        (dl if col == RED else d).text((CW / 2, y0 + k * lh), ln, font=f, fill=col + (255,), anchor="mm")
    glow(img, lay.copy(), 0.9, 40); comp(img, lay); d = ImageDraw.Draw(img)
    if s.get("sub"):
        fs = F("serif_i", 46); sl = _lines(d, s["sub"], fs, CW - 260)
        for k, ln in enumerate(sl):
            d.text((CW / 2, 1000 + k * 60), ln, font=fs, fill=CREAM + (230,), anchor="mm")
    tracked(d, CW / 2, 1130, "ЛИСТАЙ  →", F("bold", 34), RED + (255,), 0.3)
    _pager(d, 1, n); _save(img, path)

def story(path, s, i, n):
    img = bg(w=CW, h=CH); img.alpha_composite(radial(CW // 2, 300, 800, (110, 14, 28), 0.35, CW, CH))
    d = ImageDraw.Draw(img); _frame(img, d)
    lay = layer(CW, CH); dl = ImageDraw.Draw(lay)
    dl.text((150, 230), f"{i - 1:02d}", font=F("black", 150), fill=RED + (255,), anchor="lm")
    glow(img, lay.copy(), 0.8, 30); comp(img, lay); d = ImageDraw.Draw(img)
    ft = F("black", 72); tl = _lines(d, s["title"].upper(), ft, CW - 300)
    while len(tl) > 2 and ft.size > 50:
        ft = F("black", ft.size - 6); tl = _lines(d, s["title"].upper(), ft, CW - 300)
    y = 380
    for ln in tl:
        d.text((150, y), ln, font=ft, fill=CREAM + (255,), anchor="lm"); y += ft.size * 1.1
    d.line((150, y + 10, 270, y + 10), fill=RED + (255,), width=4); y += 80
    fb = F("med", 52); bl = _lines(d, s["text"], fb, CW - 300)
    while y + len(bl) * fb.size * 1.4 > CH - 200 and fb.size > 32:
        fb = F("med", fb.size - 2); bl = _lines(d, s["text"], fb, CW - 300)
    for ln in bl:
        d.text((150, y + fb.size), ln, font=fb, fill=CREAM + (225,), anchor="ls"); y += fb.size * 1.4
    _pager(d, i, n); _save(img, path)

def cta(path, i, n, line):
    img = bg(w=CW, h=CH); img.alpha_composite(radial(CW // 2, 560, 900, (130, 16, 30), 0.55, CW, CH))
    d = ImageDraw.Draw(img); _frame(img, d)
    lay = layer(CW, CH); dl = ImageDraw.Draw(lay)
    eye(dl, 380, 330, 130, 74, 1.0, RED + (255,)); eye(dl, 700, 330, 130, 74, 1.0, RED + (255,))
    glow(img, lay.copy(), 1.0, 40); comp(img, lay); d = ImageDraw.Draw(img)
    f = F("black", 84); ll = _lines(d, line.upper(), f, CW - 240)
    y = 560 - (len(ll) - 1) * 46
    for ln in ll:
        d.text((CW / 2, y), ln, font=f, fill=CREAM + (255,), anchor="mm"); y += 92
    tracked(d, CW / 2, 820, f'{BRAND["day"]} · {BRAND["time"]}', F("semi", 50), CREAM + (255,), 0.2)
    tracked(d, CW / 2, 895, BRAND["place"], F("semi", 50), RED + (255,), 0.45)
    t = "ЗАПИСЬ: " + BRAND["signup"].upper()
    d.rounded_rectangle((170, 975, CW - 170, 1085), 55, fill=RED + (255,))
    d.text((CW / 2, 1030), t, font=fit_font(t, "black", 46, CW - 400), fill=CREAM + (255,), anchor="mm")
    d.text((CW / 2, 1160), BRAND["handle"], font=F("med", 38), fill=DIM + (255,), anchor="mm")
    _pager(d, i, n); _save(img, path)

def make_carousel(spec, out_dir, prefix):
    slides = spec["slides"]; n = len(slides) + 1; paths = []
    for i, s in enumerate(slides, 1):
        p = os.path.join(out_dir, f"{prefix}_carousel_{i:02d}.jpg")
        (cover(p, s, n) if i == 1 else story(p, s, i, n)); paths.append(p)
    p = os.path.join(out_dir, f"{prefix}_carousel_{n:02d}.jpg")
    cta(p, n, n, spec.get("cta_line", "А у нас мафию вычисляют за один вечер")); paths.append(p)
    return paths
