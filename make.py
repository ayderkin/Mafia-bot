#!/usr/bin/env python3
"""MAFIA NYC daily content generator.

  python3 make.py                       # today's pack -> ./output/<date>/
  python3 make.py --date 2026-11-27     # pack for a given date
  python3 make.py --spec today.json     # use texts written for today (see README) instead of the library
  python3 make.py --no-reel             # skip video even on reel days
  python3 make.py --week                # 7 days starting --date (preview)

Weekly plan (game night = Friday 7:00 PM):
  Mon: role story + countdown            + REEL
  Tue: fact story + countdown            + feed poster 4:5
  Wed: question story + countdown        + REEL
  Thu: quote story + countdown           + story poster 9:16
  Fri: game-day story + story poster     + REEL
  Sat: thank-you story
  Sun: fact story + question story
"""
import argparse, datetime as dt, json, os, sys, copy

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from engine import stills
from engine.reel import make_reel
from engine.stills import MONTHS

LIB = json.load(open(os.path.join(ROOT, "content", "library.json"), encoding="utf-8"))
PLAN = {0: (["role", "countdown"], "reel", None), 1: (["fact", "countdown"], None, "4x5"),
        2: (["question", "countdown"], "reel", None), 3: (["quote", "countdown"], None, "9x16"),
        4: (["gameday"], "reel", "9x16"), 5: (["thanks"], None, None), 6: (["fact", "question"], None, None)}

def next_friday(d):
    return d + dt.timedelta(days=(4 - d.weekday()) % 7)

def pick(lst, d, salt=0):
    n = d.toordinal() + salt * 7
    return lst[n % len(lst)]

def build_day(d, out, spec=None, reel=True):
    os.makedirs(out, exist_ok=True)
    spec = spec or {}
    stories, reel_kind, poster_size = PLAN[d.weekday()]
    game = next_friday(d)
    gdate = f"{game.day} {MONTHS[game.month - 1].lower()}"
    captions, made = [], []
    sspecs = spec.get("stories") or [{"type": s} for s in stories]
    for i, s in enumerate(sspecs, 1):
        ty = s["type"]; p = os.path.join(out, f"{d}_story{i}_{ty}.jpg")
        if ty == "countdown":
            stills.story_countdown(p, (game - d).days)
        elif ty == "gameday":
            stills.story_gameday(p, s.get("line", "ЕЩЁ ЕСТЬ СВОБОДНЫЕ МЕСТА"))
        elif ty == "role":
            r = s if "role" in s else pick(LIB["roles"], d)
            stills.story_role(p, r["role"], r["text"])
        elif ty == "fact":
            f = s if "text" in s else pick(LIB["facts"], d, i)
            stills.story_fact(p, f.get("title", "ФАКТ О МАФИИ"), f["text"])
        elif ty == "question":
            q = s.get("question") or pick(LIB["questions"], d, i)
            stills.story_question(p, q)
            captions.append(f"Сторис {i}: добавьте стикер «Опрос» в пунктирную рамку (варианты: «Да» / «Нет» или свои).")
        elif ty == "quote":
            q = s if "quote" in s else pick(LIB["quotes"], d)
            stills.story_quote(p, q["quote"], q.get("author", ""))
        elif ty == "thanks":
            stills.story_thanks(p, s.get("text", "Спасибо всем, кто был за столом! Кто вчера блефовал лучше всех? Отмечай в комментариях."))
        else:
            continue
        made.append(p)
    psize = spec.get("poster", poster_size)
    if psize:
        p = os.path.join(out, f"{d}_poster_{psize}.jpg")
        stills.poster(p, game, psize, spec.get("poster_extra", ""))
        made.append(p)
        captions.append("Подпись к афише:\n" + spec.get("poster_caption", LIB["captions"]["poster"].format(date=gdate)) + "\n\n" + LIB["hashtags"])
    if d.weekday() == 5:
        captions.append("Подпись к сторис/посту:\n" + LIB["captions"]["thanks"].format(date=gdate))
    rspec = spec.get("reel")
    if reel and (reel_kind or rspec):
        if not rspec:
            week = d.isocalendar()[1]
            idx = (week * 3 + [0, 2, 4].index(d.weekday())) % len(LIB["reels"]) if d.weekday() in (0, 2, 4) else 0
            rspec = copy.deepcopy(LIB["reels"][idx])
        p = os.path.join(out, f"{d}_reel_{rspec.get('id', 'custom')}.mp4")
        make_reel(rspec, p, os.path.join(out, "_work"))
        try: os.rmdir(os.path.join(out, "_work"))
        except OSError: pass
        made.append(p)
        captions.insert(0, "Подпись к Reels:\n" + rspec.get("caption", "") + "\n\n" + LIB["hashtags"])
    with open(os.path.join(out, f"{d}_captions.txt"), "w", encoding="utf-8") as f:
        f.write(f"MAFIA NYC — материалы на {d} ({['пн','вт','ср','чт','пт','сб','вс'][d.weekday()]}). Ближайшая игра: пятница, {gdate}, 7:00 PM.\n\n")
        f.write("\n\n---\n\n".join(captions) if captions else "Сегодня только сторис — подписи не нужны.")
    made.append(os.path.join(out, f"{d}_captions.txt"))
    return made

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date"); ap.add_argument("--out", default=os.path.join(ROOT, "output"))
    ap.add_argument("--spec"); ap.add_argument("--no-reel", action="store_true"); ap.add_argument("--week", action="store_true")
    a = ap.parse_args()
    d = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
    spec = json.load(open(a.spec, encoding="utf-8")) if a.spec else None
    days = [d + dt.timedelta(days=k) for k in range(7)] if a.week else [d]
    for day in days:
        for p in build_day(day, os.path.join(a.out, str(day)), spec if not a.week else None, not a.no_reel):
            print(p)
