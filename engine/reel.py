"""Reels: a spec (list of scenes) -> 1080x1920 30fps mp4 with generated soundtrack.

Scene types and their fields (all text fields optional, sensible defaults):
  clock : top, time, l1, l2, notif_title, notif
  city  : number, label, l1, l2
  table : l1, l2, small
  flip  : l1, l2, roles (list, last one lands with a hit), small
  wake  : serif, l1, l2, small
  seat  : l1, l2, seat_label
  text  : l1, l2, small            (plain kinetic text on red glow)
  end   : cta                       (brand end card; always last)
Every scene has 'dur' in seconds (use multiples of 0.5; 2.5-4).
"""
import math, random, os, subprocess, wave, json
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw
from .core import *

# ---------------- city ----------------
random.seed(3)
BUILD = []
_x = -20
while _x < W + 20:
    bw = random.randint(70, 150); BUILD.append([_x, bw, random.randint(200, 560), random.random()]); _x += bw + random.randint(-6, 10)
MID = min(range(len(BUILD)), key=lambda i: abs(BUILD[i][0] - 610)); BUILD[MID][2] = 700; BUILD[MID][1] = 120
WINS = [(bi, wx, wy, random.random()) for bi, (bx, bw, bh, _) in enumerate(BUILD) for wy in range(30, bh - 20, 42) for wx in range(14, bw - 22, 30)]
BASE = 1560

def draw_city(img, t, light_amt=1.0):
    lay = layer(); d = ImageDraw.Draw(lay)
    ps = []
    for i, (bx, bw, bh, r) in enumerate(BUILD):
        p = eo(prog(t, r * 0.35, r * 0.35 + 0.7)); ps.append(p); h = bh * p
        d.rectangle((bx, BASE - h, bx + bw, BASE), fill=(20, 18, 21, 255), outline=(48, 42, 46, 255), width=2)
        if i == MID and p > 0.95:
            d.polygon([(bx + 40, BASE - h), (bx + bw - 40, BASE - h), (bx + bw / 2, BASE - h - 150)], fill=(20, 18, 21, 255), outline=(48, 42, 46, 255))
            d.line((bx + bw / 2, BASE - h - 150, bx + bw / 2, BASE - h - 240), fill=(48, 42, 46, 255), width=3)
    for (bi, wx, wy, r) in WINS:
        bx, bw, bh, _ = BUILD[bi]
        if wy > bh * ps[bi] - 20 or r >= light_amt * 0.55: continue
        d.rectangle((bx + wx, BASE - wy - 18, bx + wx + 12, BASE - wy), fill=(236, 205, 150, 200 if r > 0.05 else 90))
    d.rectangle((0, BASE, W, H), fill=(14, 12, 14, 255))
    for k in range(10):
        yv = BASE + 40 + k * 34
        d.line((80 + k * 30, yv, W - 80 - k * 30, yv), fill=(120, 30, 40, max(0, 60 - k * 6)), width=2)
    comp(img, lay)

# ---------------- table ----------------
TC, TR, SEATS = (540, 1180), 300, 10
def seat_pos(i, r=440):
    ang = math.pi / 2 + i * 2 * math.pi / SEATS
    return TC[0] + r * math.cos(ang), TC[1] + r * math.sin(ang) * 0.92, ang
CARD = Image.new("RGBA", (92, 132), (0, 0, 0, 0)); _cd = ImageDraw.Draw(CARD)
_cd.rounded_rectangle((0, 0, 91, 131), 12, fill=RED + (255,)); _cd.rounded_rectangle((8, 8, 83, 123), 8, outline=CREAM + (255,), width=3)
_cd.polygon([(46, 34), (66, 66), (46, 98), (26, 66)], outline=CREAM + (255,), width=3)
def tx(p, z, f): return f[0] + (p[0] - f[0]) * z, f[1] + (p[1] - f[1]) * z

def draw_table(img, t, mode, z=1.0, focus=TC, pulse=0.0, seat_label="ТЫ?"):
    img.alpha_composite(radial(TC[0], TC[1], 760, (255, 190, 120), 0.22))
    lay = layer(); d = ImageDraw.Draw(lay); cx, cy = tx(TC, z, focus)
    for i in range(SEATS):
        if mode == "players" and i == 0: continue
        sx, sy, _ = seat_pos(i); sx, sy = tx((sx, sy), z, focus); r = 74 * z
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(30, 26, 28, 255), outline=(60, 52, 54, 255), width=3)
    R = TR * z
    d.ellipse((cx - R - 22 * z, cy - R * 0.92 - 22 * z, cx + R + 22 * z, cy + R * 0.92 + 22 * z), fill=(46, 30, 24, 255))
    d.ellipse((cx - R, cy - R * 0.92, cx + R, cy + R * 0.92), fill=FELT + (255,), outline=(110, 30, 40, 255), width=4)
    d.ellipse((cx - R * 0.72, cy - R * 0.66, cx + R * 0.72, cy + R * 0.66), outline=(100, 26, 36, 255), width=2)
    comp(img, lay)
    if mode == "cards":
        for i in range(SEATS):
            p = eo(prog(t, 0.55 + i * 0.09, 0.95 + i * 0.09))
            if p <= 0: continue
            sx, sy, ang = seat_pos(i, 225)
            x = TC[0] + (sx - TC[0]) * p; y = TC[1] + (sy - TC[1]) * p
            c = CARD.rotate(-math.degrees(ang) + 90 + (1 - p) * 220, expand=True, resample=Image.BICUBIC)
            img.alpha_composite(c, (int(x - c.width / 2), int(y - c.height / 2)))
    if mode == "players":
        lay = layer(); d = ImageDraw.Draw(lay)
        for i in range(1, SEATS):
            p = eback(prog(t, 0.05 + i * 0.07, 0.4 + i * 0.07))
            if p <= 0.15: continue
            sx, sy, _ = seat_pos(i); sx, sy = tx((sx, sy), z, focus)
            r = 58 * z * p; hr = 26 * z * p
            d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(58, 52, 54, 255))
            d.ellipse((sx - hr, sy - hr - 10 * z, sx + hr, sy + hr - 10 * z), fill=CREAM + (235,))
            d.chord((sx - 46 * z * p, sy + 6 * z, sx + 46 * z * p, sy + 6 * z + 84 * z * p), 180, 360, fill=CREAM + (235,))
        comp(img, lay)
        sx, sy, _ = seat_pos(0); sx, sy = tx((sx, sy), z, focus)
        lay = layer(); d = ImageDraw.Draw(lay); r = 74 * z
        d.ellipse((sx - r, sy - r, sx + r, sy + r), outline=RED + (255,), width=int(6 * z))
        rr = r * (1 + 0.55 * pulse)
        d.ellipse((sx - rr, sy - rr, sx + rr, sy + rr), outline=RED + (int(200 * (1 - pulse)),), width=4)
        d.text((sx, sy), seat_label, font=fit_font(seat_label, "black", 48 * z, 2 * r - 16), fill=CREAM + (255,), anchor="mm")
        glow(img, lay.copy(), 1.1, 34); comp(img, lay)

def _headline(img, t, s, d1=0.1, d2=0.35, size1=104, size2=112):
    if s.get("l1"): kin(img, s["l1"], fit_font(s["l1"], "black", size1, 980), 540, 290, t, d1, CREAM)
    if s.get("l2"): kin(img, s["l2"], fit_font(s["l2"], "black", size2, 980), 540, 415, t, d2, RED, glow_it=True)

def _small(img, t, text, y, t0):
    if not text: return
    lay = layer(); d = ImageDraw.Draw(lay)
    tracked(d, 540, y, text, fit_font(text, "med", 40, 1000 - 0.3 * 40 * len(text)), CREAM + (230,), 0.3)
    comp(img, lay, prog(t, t0, t0 + 0.3))

# ---------------- scene renderers: fn(t, s) -> RGBA ----------------
def sc_clock(t, s):
    img = bg(); img.alpha_composite(radial(540, 820, 900, (90, 10, 20), 0.55))
    lay = layer(); dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle((130, 250, 950, 1700), 80, outline=DIM + (90,), width=4)
    dl.rounded_rectangle((440, 285, 640, 320), 18, fill=DIM + (70,))
    comp(img, lay, eo(prog(t, 0, 0.5)))
    lay = layer(); dl = ImageDraw.Draw(lay)
    tracked(dl, 540, 520, s.get("top", BRAND["day"]), F("med", 44), CREAM + (230,), 0.45)
    comp(img, lay, prog(t, 0.05, 0.35))
    parts = s.get("time", BRAND["time"]).split()
    hh, mm = parts[0].split(":"); ampm = parts[1] if len(parts) > 1 else ""
    big = F("black", 300); sm = F("black", 90); a = prog(t, 0, 0.3)
    lay = layer(); dl = ImageDraw.Draw(lay)
    wh, wm, wc = dl.textlength(hh, font=big), dl.textlength(mm, font=big), dl.textlength(":", font=big)
    wa = dl.textlength(ampm, font=sm) + 20 if ampm else 0
    x0 = 540 - (wh + wc + wm + wa) / 2; yc = 720 + (1 - eo(a)) * 40
    dl.text((x0, yc), hh, font=big, fill=CREAM + (255,), anchor="lm")
    if int(t * 2) % 2 == 0: dl.text((x0 + wh, yc - 10), ":", font=big, fill=RED + (255,), anchor="lm")
    dl.text((x0 + wh + wc, yc), mm, font=big, fill=CREAM + (255,), anchor="lm")
    if ampm: dl.text((x0 + wh + wc + wm + 20, yc + 85), ampm, font=sm, fill=RED + (255,), anchor="ls")
    comp(img, lay, a)
    if s.get("l1"): kin(img, s["l1"], fit_font(s["l1"], "black", 104, 760), 540, 1010, t, 0.55, CREAM)
    if s.get("l2"): kin(img, s["l2"], fit_font(s["l2"], "black", 150, 760), 540, 1150, t, 0.9, RED, glow_it=True)
    p = prog(t, 1.65, 2.05)
    if p > 0 and s.get("notif"):
        lay = layer(); dl = ImageDraw.Draw(lay); y = 1360 + (1 - eo(p)) * 120
        dl.rounded_rectangle((180, y, 900, y + 170), 36, fill=(32, 29, 32, 240), outline=(70, 64, 66, 255), width=2)
        dl.rounded_rectangle((215, y + 45, 295, y + 125), 20, fill=RED + (255,))
        dl.rectangle((231, y + 66, 279, y + 104), outline=CREAM + (255,), width=4)
        dl.line((231, y + 66, 255, y + 88, 279, y + 66), fill=CREAM + (255,), width=4)
        dl.text((325, y + 62), s.get("notif_title", "Сообщения"), font=F("semi", 36), fill=CREAM + (255,), anchor="lm")
        dl.text((325, y + 112), s["notif"], font=fit_font(s["notif"], "light", 36, 540), fill=DIM + (255,), anchor="lm")
        dl.text((865, y + 62), "сейчас", font=F("light", 28), fill=DIM + (255,), anchor="rm")
        comp(img, lay, clamp(p * 1.5))
    return img

def sc_city(t, s):
    img = bg(); img.alpha_composite(radial(540, BASE, 1100, (120, 16, 30), 0.65))
    draw_city(img, t, 0.3 + 0.7 * prog(t, 0.3, 1.6))
    lay = layer(); d = ImageDraw.Draw(lay)
    if "number" in s:
        n = int(int(s["number"]) * eo(prog(t, 0.1, 1.2)))
        d.text((540, 330), f"{n:,}".replace(",", " "), font=F("black", 170), fill=CREAM + (255,), anchor="mm")
    if s.get("label"): tracked(d, 540, 470, s["label"], F("med", 42), CREAM + (220,), 0.45)
    comp(img, lay, prog(t, 0, 0.25))
    if s.get("l1"): kin(img, s["l1"], fit_font(s["l1"], "black", 100, 980), 540, 640, t, 1.45, CREAM)
    if s.get("l2"): kin(img, s["l2"], fit_font(s["l2"], "black", 128, 980), 540, 770, t, 1.8, RED, glow_it=True)
    return img

def sc_table(t, s):
    img = bg(); draw_table(img, t, "cards")
    _headline(img, t, s, 0.15, 0.45)
    _small(img, t, s.get("small"), 1760, 1.7)
    p = eio(prog(t, 0, 0.32))
    if p < 1:
        lay = layer(); ImageDraw.Draw(lay).rectangle((0, 0, W, int(H * (1 - p))), fill=RED + (255,)); comp(img, lay)
    return img

def _flip_times(n, dur):
    span = min(dur - 0.9, 0.5 * n + 0.1)
    return [0.35 + i * (span - 0.35) / max(1, n - 1) for i in range(n)] if n > 1 else [0.6]

def sc_flip(t, s):
    roles = s.get("roles", ["МИРНЫЙ", "ДОКТОР", "ШЕРИФ", "МАФИЯ"])
    ft = _flip_times(len(roles), s["dur"])
    last = roles[-1]; dark = last in ("МАФИЯ", "ДОН", "МАНЬЯК")
    img = bg(); img.alpha_composite(radial(540, 1080, 800, (120, 16, 30), round(0.35 + 0.35 * prog(t, ft[-1], ft[-1] + 0.25), 2)))
    _headline(img, t, s, 0.05, 0.3, 112, 100)
    face = "back"; sx = 1.0
    for i, f in enumerate(ft):
        if t >= f: face = roles[i]
    for i, f in enumerate(ft):
        if f - 0.12 <= t < f + 0.12:
            sx = abs((t - f) / 0.12); face = (roles[i - 1] if i > 0 else "back") if t < f else roles[i]
    sx = max(sx, 0.02); enter = eback(prog(t, 0, 0.35)); scale = 0.85 + 0.15 * enter
    landed = face == last and t >= ft[-1]
    if landed: scale *= 1 + 0.06 * math.sin(prog(t, ft[-1] + 0.12, ft[-1] + 0.3) * math.pi)
    c = card_face(face); cw, ch = max(2, int(CW * sx * scale)), int(CH * scale)
    c2 = c.resize((cw, ch), Image.BICUBIC); y = 1080 + (1 - enter) * 300
    if landed and dark:
        g = layer(); g.alpha_composite(c2, (int(540 - cw / 2), int(y - ch / 2)))
        r = Image.new("RGBA", (W, H), RED + (0,)); r.putalpha(g.getchannel("A")); glow(img, r, 0.9, 60)
    img.alpha_composite(c2, (int(540 - cw / 2), int(y - ch / 2)))
    _small(img, t, s.get("small"), 1600, ft[-1] + 0.4)
    return img

def sc_wake(t, s):
    img = bg()
    if s.get("serif"):
        lay = layer(); d = ImageDraw.Draw(lay)
        d.text((540, 820), s["serif"], font=fit_font(s["serif"], "serif_i", 92, 960), fill=CREAM + (255,), anchor="mm")
        comp(img, lay, prog(t, 0.1, 0.5) * (1 - prog(t, 1.0, 1.25)))
    o = eo(prog(t, 1.25, 1.6))
    if t >= 1.2:
        img.alpha_composite(radial(540, 800, 700, (140, 14, 30), round(0.5 * o, 2)))
        lay = layer(); d = ImageDraw.Draw(lay)
        eye(d, 360, 760, 140, 80, o, RED + (255,)); eye(d, 720, 760, 140, 80, o, RED + (255,))
        glow(img, lay.copy(), 1.2, 40); comp(img, lay)
    if s.get("l1"): kin(img, s["l1"], fit_font(s["l1"], "black", 120, 980), 540, 1060, t, 1.35, CREAM, per=0.0)
    if s.get("l2"): kin(img, s["l2"], fit_font(s["l2"], "black", 250, 1000), 540, 1240, t, 1.5, RED, per=0.0, rise=80, glow_it=True)
    _small(img, t, s.get("small"), 1520, 2.1)
    return img

def sc_seat(t, s):
    img = bg()
    draw_table(img, t, "players", 1.0 + 0.12 * eio(prog(t, 0.2, s["dur"])), focus=(540, 1500), pulse=(t * 2) % 1.0, seat_label=s.get("seat_label", "ТЫ?"))
    _headline(img, t, s)
    return img

def sc_text(t, s):
    img = bg(); img.alpha_composite(radial(540, 960, 900, (120, 16, 30), 0.5))
    if s.get("l1"): kin(img, s["l1"], fit_font(s["l1"], "black", 120, 980), 540, 820, t, 0.1, CREAM)
    if s.get("l2"): kin(img, s["l2"], fit_font(s["l2"], "black", 170, 1000), 540, 980, t, 0.45, RED, glow_it=True)
    _small(img, t, s.get("small"), 1200, 1.2)
    return img

def sc_end(t, s):
    img = bg(); img.alpha_composite(radial(540, 780, 900, (110, 14, 28), 0.45))
    lay = layer(); d = ImageDraw.Draw(lay)
    m = 60; L = (2 * (W - 2 * m) + 2 * (H - 2 * m)) * eio(prog(t, 0, 0.8))
    for (a, b) in [((m, m), (W - m, m)), ((W - m, m), (W - m, H - m)), ((W - m, H - m), (m, H - m)), ((m, H - m), (m, m))]:
        if L <= 0: break
        sl = math.dist(a, b); f = min(1, L / sl)
        d.line((a[0], a[1], a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), fill=RED + (255,), width=5); L -= sl
    comp(img, lay)
    lay = layer(); d = ImageDraw.Draw(lay); hat(d, 540, 470, 0.8, CREAM + (255,)); comp(img, lay, prog(t, 0.05, 0.3))
    for txt, y, col, t0 in [("MAFIA", 680, CREAM, 0.0), ("NYC", 920, RED, 0.18)]:
        q = prog(t, t0, t0 + 0.22)
        if q <= 0: continue
        lay = layer(); d = ImageDraw.Draw(lay)
        d.text((540, y), txt, font=F("black", int(270 * (1.6 - 0.6 * eo(q)))), fill=col + (255,), anchor="mm")
        if col == RED: glow(img, lay.copy(), 1.0, 50)
        comp(img, lay, clamp(q * 2))
    lay = layer(); d = ImageDraw.Draw(lay)
    d.line((300, 1105, 780, 1105), fill=DIM + (200,), width=2)
    tracked(d, 540, 1190, f'КАЖДУЮ {BRAND["day"]} · {BRAND["time"]}'.replace("КАЖДУЮ ПЯТНИЦА", "КАЖДУЮ ПЯТНИЦУ"), F("semi", 50), CREAM + (255,), 0.18)
    tracked(d, 540, 1270, BRAND["place"], F("semi", 50), RED + (255,), 0.45)
    comp(img, lay, prog(t, 0.5, 0.8))
    cta = s.get("cta", "ЗАПИШИСЬ НА ИГРУ")
    lay = layer(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((150, 1420, 930, 1560), 70, fill=RED + (255,))
    d.text((540, 1490), cta, font=fit_font(cta, "black", 64, 700), fill=CREAM + (255,), anchor="mm")
    q = prog(t, 0.85, 1.15)
    if q > 0:
        glow(img, lay.copy(), 0.75 + 0.25 * math.sin(t * math.pi * 2), 40); comp(img, lay, clamp(q * 1.5))
    lay = layer(); d = ImageDraw.Draw(lay)
    d.text((540, 1640), BRAND["signup"], font=F("light", 42), fill=CREAM + (230,), anchor="mm")
    d.text((540, 1745), BRAND["handle"], font=F("med", 44), fill=DIM + (255,), anchor="mm")
    comp(img, lay, prog(t, 1.1, 1.4))
    return img

RENDER = {"clock": sc_clock, "city": sc_city, "table": sc_table, "flip": sc_flip, "wake": sc_wake, "seat": sc_seat, "text": sc_text, "end": sc_end}

def frame(spec, si, fi):
    s = spec["scenes"][si]; t = fi / FPS
    img = RENDER[s["type"]](t, s)
    flash = 0.55 * (1 - prog(t, 0, 0.12)) if si > 0 else 0
    shake = (0, 0); k = fi
    if s["type"] == "flip":
        f = _flip_times(len(s.get("roles", [0, 0, 0, 0])), s["dur"])[-1]
        if f + 0.1 <= t < f + 0.3: shake = ((-1) ** k * 10, (-1) ** (k + 1) * 6)
    if s["type"] == "end" and t < 0.25: shake = ((-1) ** k * 12 * (1 - t / 0.25), 0)
    if s["type"] == "wake" and 1.5 <= t < 1.7: shake = ((-1) ** k * 10, 0)
    return post(img, si * 1000 + fi, flash, shake)

def _render_scene(args):
    spec, si, outdir = args
    n = int(round(spec["scenes"][si]["dur"] * FPS))
    tmp = os.path.join(outdir, f"_scene{si}.tmp.mp4"); final = os.path.join(outdir, f"_scene{si}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for fi in range(n): p.stdin.write(frame(spec, si, fi).tobytes())
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError(f"ffmpeg failed on scene {si}")
    os.replace(tmp, final); return final

# ---------------- audio ----------------
SR = 44100
def build_audio(spec, path, seed=1):
    from scipy.signal import butter, sosfilt, fftconvolve
    rng = np.random.default_rng(seed)
    starts, t0 = [], 0.0
    for s in spec["scenes"]: starts.append(t0); t0 += s["dur"]
    DUR = t0; N = int(SR * DUR); dry = np.zeros(N); send = np.zeros(N)
    tt = lambda d: np.arange(int(SR * d)) / SR
    def add(buf, st, sig, g=1.0):
        i = int(st * SR); j = min(N, i + len(sig))
        if 0 <= i < N: buf[i:j] += sig[: j - i] * g
    lp = lambda x, f: sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)
    hp = lambda x, f: sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)
    bp = lambda x, a, b: sosfilt(butter(2, [a, b], "band", fs=SR, output="sos"), x)
    note = lambda n: 440 * 2 ** ((n - 69) / 12)
    def kick(g=1.0):
        t = tt(0.45); f = 45 + 95 * np.exp(-t * 28)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * g + hp(rng.normal(0, 1, len(t)), 3000) * np.exp(-t * 180) * 0.15
    def clap():
        t = tt(0.25); env = np.exp(-t * 22); env[: int(0.012 * SR)] *= 1.6
        return bp(rng.normal(0, 1, len(t)), 900, 3500) * env * 0.5
    def hat(o=False):
        t = tt(0.2 if o else 0.05); return hp(rng.normal(0, 1, len(t)), 7000) * np.exp(-t * (18 if o else 90)) * 0.22
    def tick():
        t = tt(0.03); return (hp(rng.normal(0, 1, len(t)), 2500) * 0.5 + np.sin(2 * np.pi * 1800 * t)) * np.exp(-t * 300) * 0.5
    _pc = {}
    def pluck(f, d=0.9, g=0.35):
        k = (round(f, 2), d)
        if k not in _pc:
            n = int(SR * d); p = int(SR / f); b = rng.uniform(-1, 1, p); out = np.zeros(n)
            for i in range(n):
                out[i] = b[i % p]; b[i % p] = 0.996 * 0.5 * (b[i % p] + b[(i + 1) % p])
            _pc[k] = lp(out, 3500)
        return _pc[k] * g
    def bass(f, d=0.45, g=0.5):
        t = tt(d); s = np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + np.sin(2 * np.pi * f * t)
        return lp(s, 400) * np.minimum(1, t / 0.005) * np.exp(-t * 3) * g
    def boom(g=1.0, d=2.5):
        t = tt(d); f = 32 + 40 * np.exp(-t * 5)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6) + lp(rng.normal(0, 1, len(t)), 600) * np.exp(-t * 4) * 0.6) * g
    def whoosh(d=0.45, g=0.35):
        t = tt(d); n = rng.normal(0, 1, len(t)); x = t / d
        return (lp(n, 900) * (1 - x) + bp(n, 1500, 6000) * x) * x ** 2.2 * g
    def riser(d, g=0.3):
        t = tt(d); x = t / d
        return (bp(rng.normal(0, 1, len(t)), 2000, 9000) * x ** 2 + np.sin(2 * np.pi * np.cumsum(150 + 650 * x ** 2) / SR) * 0.3 * x ** 2) * g
    def bell(f, g=0.25, d=2.5):
        t = tt(d); return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) + 0.25 * np.sin(2 * np.pi * f * 5.4 * t)) * np.exp(-t * 2.2) * g
    def pad(freqs, d, g=0.12):
        t = tt(d); s = np.zeros(len(t))
        for f in freqs:
            for det in (-0.6, 0.6):
                ph = (f + det) * t; s += 2 * (ph - np.floor(ph + 0.5))
        return lp(s, 1400) * np.minimum(1, t / 0.3) * np.minimum(1, np.maximum(0, d - t) / 1.2) * g

    PROG = [([57, 60, 64, 69], 33), ([57, 60, 64, 72], 33), ([53, 57, 60, 65], 29), ([52, 56, 59, 64], 28)]
    tA = tt(DUR)
    drone = lp(np.sin(2 * np.pi * 55 * tA) + 0.5 * np.sin(2 * np.pi * 82.41 * tA) + 0.3 * np.sin(2 * np.pi * 110.3 * tA) + 0.15 * rng.normal(0, 1, N), 300)
    denv = np.full(N, 0.25); denv[: int(1.5 * SR)] = np.linspace(0, 0.25, int(1.5 * SR))[: min(N, int(1.5 * SR))]

    def groove(a, b, full=False):
        bar = 0
        for sec in np.arange(a, b - 0.01, 1.0):
            notes, bn = PROG[bar % 4]; bar += 1
            for k in range(4):
                tb = sec + k * 0.25
                if tb < b: add(dry, tb, pluck(note(notes[k]), 0.6, 0.22)); add(send, tb, pluck(note(notes[k]), 0.6, 0.12))
            for k in range(2):
                tb = sec + 0.5 + k * 0.25
                if tb < b: add(dry, tb, pluck(note(notes[3 - k] + 12), 0.5, 0.12))
            add(dry, sec, bass(note(bn), 0.45))
            if sec + 0.5 < b: add(dry, sec + 0.5, bass(note(bn), 0.4, 0.4))
        for bt in np.arange(a, b - 0.01, 0.5): add(dry, bt, kick(0.85 if full or (bt - a) % 1 == 0 else 0.55))
        for bt in np.arange(a + 0.25, b - 0.01, 0.5): add(dry, bt, hat(full and (bt - a) % 1 > 0.6))
        if full:
            for bt in np.arange(a + 0.5, b - 0.01, 1.0): add(dry, bt, clap()); add(send, bt, clap(), 0.5)

    for i, (s, st) in enumerate(zip(spec["scenes"], starts)):
        d = s["dur"]; ty = s["type"]
        if i > 0 and ty != "end": add(dry, st - 0.45, whoosh())
        if ty == "clock":
            for k in range(int(d * 2)): add(dry, st + k * 0.5, tick(), 0.6 if k % 2 == 0 else 0.4)
            if s.get("notif"):
                for o, n in ((1.65, 88), (1.78, 93)): add(send, st + o, bell(note(n), 0.18, 1.2)); add(dry, st + o, bell(note(n), 0.12, 1.2))
        elif ty == "city":
            for b in np.arange(0, d - 0.1, 1.0): add(dry, st + b, kick(0.7)); add(dry, st + b + 0.18, kick(0.45))
            if "number" in s:
                tc = 0.1
                while tc < 1.2: add(dry, st + tc, tick(), 0.25); tc += 0.03 + 0.08 * ((tc - 0.1) / 1.1) ** 2
            add(send, st + 1.8, pluck(note(45), 1.5, 0.4))
            for n in (57, 60, 64): add(dry, st + 1.8, pluck(note(n), 1.2, 0.27))
        elif ty in ("table", "flip"):
            groove(st, st + d)
            if ty == "table":
                for k in range(10): add(dry, st + 0.55 + k * 0.09, whoosh(0.12, 0.12))
            else:
                ft = _flip_times(len(s.get("roles", [0, 0, 0, 0])), d)
                for f in ft: add(dry, st + f, tick(), 0.9); add(dry, st + f, whoosh(0.1, 0.15))
                add(dry, st + ft[-1] + 0.1, boom(0.9, 1.4)); add(send, st + ft[-1] + 0.1, clap(), 0.8)
        elif ty == "text":
            groove(st, st + d)
            add(dry, st + 0.45, boom(0.6, 1.2))
        elif ty == "wake":
            denv[int(st * SR): int((st + d) * SR)] = 0.05
            if s.get("serif"): add(send, st + 0.1, bell(note(81), 0.22, 3.0)); add(dry, st + 0.1, bell(note(81), 0.1, 3.0))
            add(dry, st + 1.25, boom(0.7, 1.5)); add(dry, st + 1.5, boom(1.0, 2.0)); add(send, st + 1.5, pluck(note(45), 1.5, 0.5))
            add(dry, st + 1.5, pad([note(45), note(48), note(52)], 1.4, 0.1)); add(dry, st + 1.8, riser(max(0.5, d - 1.8), 0.35))
        elif ty == "seat":
            groove(st, st + d, full=True)
        elif ty == "end":
            add(dry, st - 0.45, whoosh(0.45, 0.4))
            add(dry, st, boom(1.0, 3.0)); add(dry, st, kick(1.0)); add(send, st, clap(), 1.0)
            add(dry, st + 0.18, kick(0.8)); add(send, st + 0.18, clap(), 0.6)
            add(dry, st, pad([note(45), note(57), note(60), note(64)], d, 0.14))
            for n in (57, 64, 69): add(send, st, pluck(note(n), 2.0, 0.32))
            for k, n in enumerate([69, 72, 76, 81]): add(send, st + 1.0 + k * 0.25, pluck(note(n), 1.2, 0.18))
    dry += drone * lp(denv, 5)
    ir_t = tt(2.2); ir = lp(rng.normal(0, 1, len(ir_t)) * np.exp(-ir_t / 0.45), 5000); ir /= np.sqrt(np.sum(ir ** 2))
    wet = fftconvolve(send, ir)[:N]
    mix = np.tanh((dry + send * 0.7 + wet * 0.55) * 1.1)
    mix *= np.interp(tA, [0, max(0, DUR - 1.5), DUR], [1, 1, 0]); mix /= np.max(np.abs(mix)) / 0.89
    R = np.concatenate([np.zeros(300), wet[:-300]]) * 0.05 + mix
    R /= max(1, np.max(np.abs(R)) / 0.89)
    st2 = np.stack([mix, R], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st2 * 32767).astype(np.int16).tobytes())

def make_reel(spec, out_path, workdir, procs=2):
    os.makedirs(workdir, exist_ok=True)
    if spec["scenes"][-1]["type"] != "end": spec["scenes"].append({"type": "end", "dur": 4.0})
    with Pool(procs) as pool:
        files = pool.map(_render_scene, [(spec, i, workdir) for i in range(len(spec["scenes"]))])
    lst = os.path.join(workdir, "_list.txt")
    with open(lst, "w") as f:
        for p in files: f.write(f"file '{os.path.abspath(p)}'\n")
    vid = os.path.join(workdir, "_video.mp4"); wav = os.path.join(workdir, "_music.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    build_audio(spec, wav)
    tmp = out_path + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out_path)
    for p in files + [lst, vid, wav]:
        try: os.remove(p)
        except OSError: pass
    return out_path
