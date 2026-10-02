"""All Things Classroom: Instagram Reel cut (1080x1920, under 90 s, captions burned in).

  python reel.py tts     <kokoro.onnx> <voices.bin> <workdir>
  python reel.py audio   <session.mp4> <workdir>
  python reel.py preview <session.mp4> <workdir> <scene_id> <t> [<t> ...]
  python reel.py scenes  <session.mp4> <workdir>
  python reel.py final   <session.mp4> <workdir> <out.mp4>
  python reel.py cover   <out.jpg>

Everything important stays inside the Reels safe zone: clear of the top ~250 px, the bottom
~420 px (caption and username) and the right ~140 px from mid-height down (action buttons).
"""
import multiprocessing
import os
import re
import sys

from PIL import Image, ImageDraw

import atc_theme as T
from atc_theme import (BORDER, FOREST, INK, IVORY, LEAF, MIST, NIGHT, NOTE, SLATE, TEAL, TEAL_DEEP, WHITE, YELLOW,
                       body, button, card, check_icon, eyebrow, heading, line_icon, lockup, progress, tag, watermark)
from engine import (FPS, F, ClipPlayer, Cues, Dyn, El, add, arc_ring, build, circle, clamp01, ease, final_encode,
                    midi, mix_soundtrack, paste, pluck, render_scene_file, rgba, rrect, text_img, tts, wipe)
from long import grid_card, note

RW, RH = 1080, 1920
X0, VIS_Y = 80, 690
CAP_Y, CAP_CX, CAP_W = 1300, 500, 780
CLIP_SIZE = (920, 518)

CLIPS = {"clipA": [(35.5, 41.35)], "clipB": [(49.85, 55.25)]}
CLIP_CAPTIONS = [
    (35.6, 37.35, "I like the gap in between"), (37.35, 38.6, "where it plays"),
    (38.6, 40.6, "and gives something to anticipate as well."), (40.65, 41.3, "Well done."),
    (49.95, 50.9, "I love this."), (51.0, 53.4, "Yeah, that's how you experiment."),
    (53.85, 55.2, "That's how you experiment."),
]
CAPTION_FIXES = {"thirty seconds": "30 seconds"}

SCENES = [
    {"id": "hook", "bg": "ivory", "lead": 1.95, "tail": 0.3, "items": [
        ("vo", "rh1", "What note comes next?", 0.9),
        ("vo", "rh2", "You just predicted it. That's exactly how AI works.", 0.3),
        ("vo", "rh3", "Here are five AI habits to try with your child this week.", 0.2),
    ]},
    {"id": "m1", "bg": "ivory", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r1a", "One: guess the next note.", 0.25),
        ("clip", "clipA"),
        ("vo", "r1b", "AI always picks the most likely next word. So build three bars in Song Maker, and let your "
                      "child guess the fourth.", 0.2),
    ]},
    {"id": "m2", "bg": "night", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r2a", "Two: play it twice.", 0.2),
        ("vo", "r2b", "Ask again in a brand-new chat. If the facts change, it was guessing.", 0.2),
    ]},
    {"id": "m3", "bg": "mist", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r3a", "Three: flip the key.", 0.2),
        ("vo", "r3b", "Ask why homework is good. Then, in a new chat, ask why it's bad. If it agrees both times, "
                      "it's following your lead.", 0.2),
    ]},
    {"id": "m4", "bg": "night", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r4a", "Four: find the sheet music.", 0.2),
        ("vo", "r4b", "Before your child repeats an AI fact, find it in a real source. No receipt? Don't repeat it.",
         0.2),
    ]},
    {"id": "m5", "bg": "ivory", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r5a", "Five: play it by ear.", 0.2),
        ("vo", "r5b", "Close the tab. Can your child explain it out loud in thirty seconds?", 0.2),
    ]},
    {"id": "clipB", "bg": "night", "lead": 0.2, "tail": 0.3, "items": [("clip", "clipB")]},
    {"id": "challenge", "bg": "mist", "lead": 0.3, "tail": 0.5, "items": [
        ("vo", "rc1", "Your turn. Ask an AI why cats are better. Then, in a new chat, why dogs are better.", 0.3),
        ("vo", "rc2", "Did it flip? Tell us in the comments, and keep your child's name out of it.", 0.2),
    ]},
    {"id": "cta", "bg": "forest", "lead": 0.3, "tail": 0.8, "items": [
        ("vo", "ra1", "Want your child to learn this with a real teacher? That's AI Labs at All Things Classroom.",
         0.3),
        ("vo", "ra2", "Link in bio. Tick AI Labs on the form, and we'll email you.", 0.2),
    ]},
    {"id": "outro", "bg": "forest", "lead": 0.3, "tail": 2.0, "items": [
        ("vo", "ro1", "And this voice? Made with AI. Now you know how to question it.", 0.0),
    ]},
]


def fix(text):
    for k, v in CAPTION_FIXES.items():
        text = text.replace(k, v)
    return text


def timeline(work):
    return build(work, SCENES, CLIPS)


# ---------------------------------------------------------------- captions

def caption_chunks(text, max_chars=42):
    out = []
    for sent in re.split(r"(?<=[.?!])\s+", text):
        words = sent.split()
        target = len(sent) / -(-len(sent) // max_chars)
        cur = ""
        for i, w in enumerate(words):
            if cur and len(cur) + 1 + len(w) > target + 6 and len(words) - i >= 2:
                out.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            out.append(cur)
    return out


def caption_sprite(text, color=WHITE):
    font, max_w = F(52, 700, "DMSans"), CAP_W - 56
    if font.getlength(text) > max_w:
        words = text.split()
        best = min(range(1, len(words)), key=lambda i: max(font.getlength(" ".join(words[:i])),
                                                            font.getlength(" ".join(words[i:]))))
        text = " ".join(words[:best]) + "\n" + " ".join(words[best:])
    t = text_img(text, 52, 700, "DMSans", color, align="center", lh=1.14)
    box = rrect(t.width + 56, t.height + 30, 16, fill=rgba(NIGHT, 235))
    box.alpha_composite(t, (28, 13))
    return box


def caption_elements(sc):
    cues = []
    for it in sc["items"]:
        if it["kind"] == "vo":
            parts = caption_chunks(fix(it["text"]))
            total = sum(len(p) for p in parts)
            t = it["start"]
            for p in parts:
                d = it["dur"] * len(p) / total
                cues.append((t, t + d, p, WHITE))
                t += d
        else:
            off = 0.0
            for a, b in it["segs"]:
                for s, e, txt in CLIP_CAPTIONS:
                    if s < b and e > a:
                        cues.append((it["start"] + off + max(s, a) - a, it["start"] + off + min(e, b) - a, txt,
                                     YELLOW))
                off += b - a
    els = []
    for i, (a, b, txt, col) in enumerate(cues):
        nxt = cues[i + 1][0] if i + 1 < len(cues) else None
        t1 = b + 0.25 if nxt is None or nxt - b > 0.35 else nxt
        img = caption_sprite(txt, col)
        els.append(El(img, CAP_CX - img.width / 2, CAP_Y, a, min(t1, sc["dur"] - 0.3), dur=0.12, dy=8, fade=0.1))
    return els


# ---------------------------------------------------------------- layout pieces

def top(dark, n=None):
    wm = watermark(dark, 30)
    els = [El(wm, RW - X0 - wm.width, 252, -1, dy=0)]
    if n:
        els.append(El(progress(n, dark, w=46, gap=10), X0, 272, -1, dy=0))
    return els


def header(label, title, dark, size=100):
    return [El(eyebrow(label, dark, 26), X0, 336, 0.0), El(heading(title, size, dark, max_w=920, lh=1.02), X0, 400, 0.08)]


def chat(x, y, title, q, a, t0, a_hl=None, t_hl=None, w=440, h=470, fs=32, type_dur=1.6):
    win = card(w, h, "white")
    d = ImageDraw.Draw(win)
    for i, col in enumerate((FOREST, TEAL, YELLOW)):
        d.ellipse([26 + i * 28, 28, 44 + i * 28, 46], fill=rgba(col))
    win.alpha_composite(text_img(title, 28, 600, "DMSans", SLATE), (122, 20))
    d.line([(2, 72), (w - 2, 72)], fill=rgba(BORDER), width=2)
    qt = text_img(q, fs, 600, "DMSans", WHITE, max_w=w - 100)
    qb = rrect(qt.width + 40, qt.height + 30, 14, fill=rgba(FOREST))
    qb.alpha_composite(qt, (20, 13))
    ay = 98 + qb.height + 22
    at = text_img(a, fs, 500, "DMSans", INK, max_w=w - 90)
    ab = rrect(at.width + 40, at.height + 30, 14, fill=rgba(MIST))
    els = [El(win, x, y, t0), El(qb, x + w - 22 - qb.width, y + 98, t0 + 0.25, dy=12),
           El(text_img("AI", 24, 700, "DMSans", SLATE), x + 24, y + ay, t0 + 0.6, dy=0),
           El(ab, x + 20, y + ay + 36, t0 + 0.6, dy=10)]
    ta = t0 + 0.75

    def typed(frame, t, op):
        paste(frame, wipe(at, (t - ta) / type_dur, int(fs * 1.16)), x + 40, y + ay + 49, op)

    els.append(Dyn(typed, ta, t_hl if a_hl else None, fadein=0.01, fade=0.2))
    if a_hl:
        els.append(El(text_img(a_hl, fs, 500, "DMSans", INK, TEAL_DEEP, max_w=w - 90, accent_weight=700), x + 40,
                      y + ay + 49, t_hl, dy=0, dur=0.25))
    return els


def clip_elements(src, segs, t_start):
    player = ClipPlayer(src, segs, CLIP_SIZE)
    dur = sum(b - a for a, b in segs)
    mask = rrect(*CLIP_SIZE, 20, fill=(255, 255, 255, 255)).getchannel("A")

    def video(frame, t, op):
        f = player.at(min(t - t_start, dur - 1 / FPS))
        if f is not None:
            frame.paste(f, (X0, VIS_Y), mask if op >= 0.997 else mask.point(lambda v: int(v * op)))

    note_ = body("Varchas with TomoClub students · faces blurred", 26, True)
    row = Image.new("RGBA", (40 + note_.width, 36), (0, 0, 0, 0))
    row.alpha_composite(line_icon("lock", 28, IVORY), (0, 2))
    row.alpha_composite(note_, (40, 0))
    lab = tag("Live class · Chrome Music Lab", "yellow", 26, padx=18, pady=10)
    return [Dyn(video, t_start, t_start + dur, fadein=0.2, fade=0.3),
            El(lab, X0 + 20, VIS_Y + 20, t_start + 0.1, t_start + dur, dy=0),
            El(row, X0, VIS_Y + CLIP_SIZE[1] + 22, t_start + 0.1, t_start + dur, dy=0)]


# ---------------------------------------------------------------- scenes

def s_hook(sc, q, src):
    t2, t3 = q("rh2"), q("rh3")
    els = top(False)
    for txt, a, b in (("What note\ncomes next?", -1, t2), ("You just\n*predicted* it.", t2, t3),
                      ("*5 AI habits*\nto try at home", t3, None)):
        els.append(El(heading(txt, 108, align="center", lh=1.02), RW / 2, 360, a, (b - 0.35) if b else None,
                      center=True, fade=0.25))
    cell, cols, rows, pad = 96, 9, 5, 24
    g = grid_card(cols, rows, cell, pad)
    gx, gy = (RW - g.width) // 2, VIS_Y
    els.append(El(g, gx, gy, -1, t3 - 0.1))
    ox, oy = gx + pad, gy + pad
    ph = Image.new("RGBA", (cell, rows * cell), rgba(TEAL, 46))

    def playhead(frame, t, op):
        k = (t - 0.15) / 0.22
        if -0.5 <= k <= 8.3:
            paste(frame, ph, ox + k * cell, oy, op)

    els.append(Dyn(playhead, 0.0, 2.0, fadein=0.05, fade=0.2))
    rows_of, cols_of = {72: 4, 76: 2, 79: 0}, {4: NOTE[7], 2: NOTE[5], 0: NOTE[3]}
    for k, n in enumerate([72, 76, 79] * 2 + [72, 76]):
        r = rows_of[n]
        els.append(El(note(cell, cols_of[r], 10, 12), ox + k * cell + 6, oy + r * cell + 6, 0.15 + k * 0.22,
                      t3 - 0.1, dur=0.18, dy=10))
    qcol = Image.new("RGBA", (cell, rows * cell), rgba(YELLOW, 70))
    qm = heading("?", 130)

    def question(frame, t, op):
        paste(frame, qcol, ox + 8 * cell, oy, op * (0.7 + 0.3 * abs(((t * 1.4) % 2) - 1)))
        paste(frame, qm, ox + 8 * cell + (cell - qm.width) / 2 + 2, oy + 1.1 * cell, op)

    els.append(Dyn(question, 1.85, t2 - 0.05, fadein=0.2, fade=0.2))
    els.append(El(note(cell, YELLOW, 10, 12), ox + 8 * cell + 6, oy + 6, t2, t3 - 0.1, dur=0.25, dy=10))
    lab = tag("Most likely next note", "forest", 30)
    els.append(El(lab, gx + g.width - lab.width, gy - lab.height - 14, t2 + 0.2, t3 - 0.1))
    cols5 = [(FOREST, WHITE), (TEAL_DEEP, WHITE), (YELLOW, FOREST), (LEAF, FOREST), (TEAL, FOREST)]
    for i, (bgc, fg) in enumerate(cols5):
        b = rrect(150, 150, 20, fill=rgba(bgc))
        num = text_img(str(i + 1), 84, 800, "Manrope", fg)
        b.alpha_composite(num, ((150 - num.width) // 2, 14))
        els.append(El(b, RW / 2 - (5 * 150 + 4 * 28) / 2 + i * 178, 920 - i * 40, t3 + 0.2 + i * 0.1))
    return els + caption_elements(sc)


def s_m1(sc, q, src):
    clip = next(it for it in sc["items"] if it["kind"] == "clip")
    tc, tb = clip["start"], q("r1b")
    els = top(False, 1) + header("Habit 1 of 5", "Guess the\nNext Note", False)
    els += clip_elements(src, clip["segs"], tc)
    co = tag("Anticipate = predict", "yellow", 40, padx=30, pady=14)
    els.append(El(co, RW - X0 - co.width - 20, VIS_Y + 420, tc + 3.7, tc + clip["dur"], dx=24, dy=0))
    cell, cols, nrows, pad = 52, 16, 8, 24
    g = grid_card(cols, nrows, cell, pad, bar=4)
    gx = (RW - g.width) // 2
    els.append(El(g, gx, VIS_Y, tb))
    ox, oy = gx + pad, VIS_Y + pad
    for k, r in enumerate([7, 5, 3, 5, 6, 4, 2, 4, 5, 3, 1, 3]):
        els.append(El(note(cell, NOTE[r], 6, 6), ox + k * cell + 3, oy + r * cell + 3, tb + 0.3 + k * 0.06, dur=0.2,
                      dy=8))
    t_q = q("r1b", "let your child")
    els.append(El(Image.new("RGBA", (4 * cell, nrows * cell), rgba(YELLOW, 60)), ox + 12 * cell, oy, t_q, dy=0))
    qm = heading("?", 100)
    els.append(El(qm, ox + 14 * cell - qm.width / 2, oy + (nrows * cell - qm.height) / 2, t_q, dy=0))
    lab = tag("Bar 4: your child guesses", "forest", 32)
    els.append(El(lab, gx, VIS_Y + g.height + 24, t_q + 0.2))
    return els + caption_elements(sc)


def s_m2(sc, q, src):
    tb, t_new, t_hl = q("r2b"), q("r2b", "in a brand-new"), q("r2b", "If the facts")
    qn = "When did our town's library open?"
    els = top(True, 2) + header("Habit 2 of 5", "Play It\nTwice", True)
    els += chat(X0, VIS_Y, "Chat 1", qn, "It opened in 1962.", tb - 0.4, "It opened in *1962.*", t_hl)
    els += chat(X0 + 480, VIS_Y, "New chat", qn, "It first opened in 1958.", t_new, "It first opened in *1958.*",
                t_hl)
    co = tag("The year changed. It was guessing.", "yellow", 36, padx=26, pady=14)
    els.append(El(co, RW / 2 - co.width / 2 - 20, VIS_Y + 500, t_hl + 0.1))
    return els + caption_elements(sc)


def s_m3(sc, q, src):
    tb, t2, td = q("r3b"), q("r3b", "Then, in a new chat"), q("r3b", "If it agrees")
    els = top(False, 3) + header("Habit 3 of 5", "Flip the\nKey", False)
    els += chat(X0, VIS_Y, "Chat 1", "Why is homework good?", "Great question! It builds routine and practice...",
                tb)
    els += chat(X0 + 480, VIS_Y, "New chat", "Why is homework bad?", "Great question! It eats into play and sleep...",
                t2)
    co = tag("It agreed both times", "forest", 38, padx=28, pady=14)
    els.append(El(co, RW / 2 - co.width / 2 - 20, VIS_Y + 500, td + 0.1))
    return els + caption_elements(sc)


def s_m4(sc, q, src):
    tb = q("r4b")
    els = top(True, 4) + header("Habit 4 of 5", "Find the\nSheet Music", True)
    rw, rh = 680, 440
    r = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    rd = ImageDraw.Draw(r)
    zig = 20
    rd.polygon([(0, 0), (rw, 0), (rw, rh - zig)] + [(i * zig, rh - (zig if i % 2 == 0 else 0))
                                                    for i in range(rw // zig, -1, -1)], fill=rgba(WHITE))
    hd = text_img("FACT  RECEIPT", 48, 800, "Manrope", FOREST, tracking=2)
    r.alpha_composite(hd, ((rw - hd.width) // 2, 34))
    for xx in range(44, rw - 44, 20):
        rd.line([(xx, 116), (xx + 10, 116)], fill=BORDER, width=3)
    for i, it in enumerate(["Found a real source", "Opened it myself", "Saw the exact line"]):
        y = 146 + i * 90
        rd.rounded_rectangle([44, y, 96, y + 52], 10, outline=(150, 165, 158), width=4)
        r.alpha_composite(text_img(it, 36, 600, "DMSans", INK), (120, y + 6))
    rx, ry = (RW - rw) // 2, VIS_Y
    els.append(El(r, rx, ry, tb))
    for i, sub in enumerate(("find it in a real", "real source", "No receipt")):
        els.append(El(check_icon(60), rx + 40, ry + 142 + i * 90, q("r4b", sub) - 0.15, dur=0.25, dy=8))
    rule = tag("No receipt? Don't repeat it.", "yellow", 38, padx=28, pady=14)
    els.append(El(rule, RW / 2 - rule.width / 2, ry + rh + 26, q("r4b", "No receipt")))
    return els + caption_elements(sc)


def s_m5(sc, q, src):
    t0r, t1r = q("r5b", "explain it"), sc["dur"] - 0.4
    els = top(False, 5) + header("Habit 5 of 5", "Play It\nBy Ear", False)
    ring = 440
    rx, ry = (RW - ring) // 2, VIS_Y

    def timer(frame, t, op):
        p = clamp01((t - t0r) / (t1r - t0r))
        paste(frame, arc_ring(ring, 1 - p, TEAL, BORDER, width=28), rx, ry, op)
        txt = heading(f"0:{int(round(30 * (1 - p))):02d}", 110)
        paste(frame, txt, rx + (ring - txt.width) / 2, ry + (ring - txt.height) / 2 - 8, op)

    els.append(Dyn(timer, q("r5b"), fadein=0.3))
    a = tag("Close the tab. Explain it out loud.", "forest", 34)
    els.append(El(a, RW / 2 - a.width / 2, ry + ring + 30, q("r5b") + 0.2))
    return els + caption_elements(sc)


def s_clipB(sc, q, src):
    clip = sc["items"][0]
    els = top(True) + header("Experiment like this", "That's how you\n*experiment.*", True, size=96)
    els += clip_elements(src, clip["segs"], clip["start"])
    return els + caption_elements(sc)


def s_challenge(sc, q, src):
    els = top(False) + header("Your turn", "Can your child\nmake an AI *flip?*", False)

    def step(n, text, extra=None):
        c = card(920, 120 if not extra else 190, "white")
        b = circle(68, fill=rgba(FOREST))
        num = text_img(str(n), 40, 800, "Manrope", WHITE)
        b.alpha_composite(num, ((68 - num.width) // 2, (68 - num.height) // 2 + 1))
        c.alpha_composite(b, (26, 26))
        c.alpha_composite(heading(text, 36, max_w=780), (118, 36))
        x = 118
        for e in extra or []:
            c.alpha_composite(e, (x, 108))
            x += e.width + 18
        return c

    fl, hd = tag("FLIPPED", "forest", 34, padx=22, pady=10), tag("HELD", "teal", 34, padx=22, pady=10)
    els.append(El(step(1, "Chat 1: “Why are cats better?”"), X0, VIS_Y + 10, q("rc1", "Ask an AI")))
    els.append(El(step(2, "New chat: “Why are dogs better?”"), X0, VIS_Y + 150, q("rc1", "Then, in a new")))
    els.append(El(step(3, "Comment what happened", [fl, hd]), X0, VIS_Y + 290, q("rc2", "Tell us")))
    ban = card(920, 84, "white")
    ban.alpha_composite(line_icon("lock", 38, FOREST), (30, 22))
    ban.alpha_composite(heading("Keep your child's name out of it", 32), (88, 22))
    els.append(El(ban, X0, VIS_Y + 506, q("rc2", "keep your child")))
    return els + caption_elements(sc)


def s_cta(sc, q, src):
    els = top(True) + [El(eyebrow("AI Labs at All Things Classroom", True, 26), X0, 336, 0.0),
                       El(heading("Don't just use AI.\n*Understand it.*", 92, True, lh=1.04), X0, 400, 0.1)]
    for i, (p, sub) in enumerate((("Live online classes", None), ("The same teacher every week", "real teacher"),
                                  ("Monthly, no lock-ins", "That's AI Labs"))):
        row = Image.new("RGBA", (900, 56), (0, 0, 0, 0))
        row.alpha_composite(circle(18, fill=rgba(LEAF)), (0, 16))
        row.alpha_composite(body(p, 40, True, weight=600, color=WHITE), (40, 0))
        els.append(El(row, X0, 640 + i * 66, (q("ra1", sub) if sub else q("ra1")) + 0.1, dx=20, dy=0))
    f = card(920, 300, "white")
    f.alpha_composite(heading("Let's talk", 48), (40, 30))
    f.alpha_composite(body("Program interested in", 26, weight=600, color=INK), (40, 104))
    f.alpha_composite(rrect(40, 40, 8, fill=rgba(WHITE), outline=rgba(SLATE), ow=2), (40, 148))
    f.alpha_composite(body("AI Labs (AI Literacy)", 34, weight=600, color=INK), (98, 146))
    f.alpha_composite(body("Link in bio · allthingsclassroom.com", 26), (40, 236))
    fy = 880
    els.append(El(f, X0, fy, q("ra2") - 0.4))
    els.append(El(check_icon(40, FOREST), X0 + 40, fy + 148, q("ra2", "Tick AI Labs"), dur=0.2, dy=6))
    ok = tag("We'll email you", "yellow", 30, padx=20, pady=12)
    els.append(El(ok, X0 + 920 - ok.width - 30, fy + 30, q("ra2", "and we'll"), dx=16, dy=0))
    return els + caption_elements(sc)


def s_outro(sc, q, src):
    D = sc["dur"]
    LOCK = lockup(120, True)
    t_end = q.end("ro1")
    els = [El(eyebrow("By the way", True), RW / 2 - 90, 560, q("ro1"), t_end - 0.1),
           El(heading("This voice was\nmade with *AI.*", 100, True, align="center", lh=1.04), RW / 2, 630,
              q("ro1", "Made with"), t_end - 0.1, center=True),
           El(LOCK, RW / 2, 600, t_end + 0.1, D - 0.4, center=True, fade=0.4),
           El(body("allthingsclassroom.com", 44, True, weight=600, align="center"), RW / 2, 600 + LOCK.height + 60,
              t_end + 0.3, D - 0.4, center=True, fade=0.4),
           El(body("Form link in bio", 34, True, align="center"), RW / 2, 600 + LOCK.height + 126, t_end + 0.4,
              D - 0.4, center=True, fade=0.4)]
    return els + caption_elements(sc)


BUILDERS = {"hook": s_hook, "m1": s_m1, "m2": s_m2, "m3": s_m3, "m4": s_m4, "m5": s_m5, "clipB": s_clipB,
            "challenge": s_challenge, "cta": s_cta, "outro": s_outro}


# ---------------------------------------------------------------- plumbing

def elements(sc, src):
    els = BUILDERS[sc["id"]](sc, Cues(sc), src)
    for e in els:
        if e.t1 is None:
            e.t1, e.fade = sc["dur"] - 0.3, 0.26
    return T.bg_image(sc["bg"], RW, RH), els


def frame_fn(bg, els):
    def f(t):
        fr = bg.copy()
        for e in els:
            e.draw(fr, t)
        return fr
    return f


def render_job(args):
    i, sc, src, work = args
    bg, els = elements(sc, src)
    render_scene_file(os.path.join(work, "scenes", f"{i:02d}_{sc['id']}.mp4"), (RW, RH), sc["frames"],
                      frame_fn(bg, els))
    return sc["id"]


def cue_fx(fx, tl):
    by = {s["id"]: s for s in tl}
    for k, n in enumerate([72, 76, 79] * 2 + [72, 76]):
        add(fx, pluck(midi(n), 1.4), 0.15 + k * 0.22, 0.30, pan=-0.2 + 0.05 * k)
    t_res = Cues(by["hook"])("rh2")
    add(fx, pluck(midi(79), 2.0), t_res, 0.34)
    add(fx, pluck(midi(91), 2.0, 0.4), t_res + 0.02, 0.10)
    for sid, vid in (("m1", "r1a"), ("m2", "r2a"), ("m3", "r3a"), ("m4", "r4a"), ("m5", "r5a"), ("challenge", "rc1"),
                     ("cta", "ra1")):
        t = by[sid]["start"] + Cues(by[sid])(vid) - 0.2
        add(fx, pluck(midi(79), 1.2), t, 0.13, pan=-0.2)
        add(fx, pluck(midi(83), 1.4), t + 0.1, 0.13, pan=0.2)
    return t_res


def cover(out):
    img = T.bg_image("ivory", RW, RH).convert("RGBA")
    wm = lockup(54, False, tagline=False)
    img.alpha_composite(wm, ((RW - wm.width) // 2, 330))
    h = heading("What note\ncomes *next?*", 130, align="center", lh=1.0)
    img.alpha_composite(h, ((RW - h.width) // 2, 520))
    cell, cols, rows, pad = 80, 9, 5, 20
    g = grid_card(cols, rows, cell, pad)
    for k, r in enumerate([4, 2, 0, 4, 2, 0, 4, 2]):
        g.alpha_composite(note(cell, {4: NOTE[7], 2: NOTE[5], 0: NOTE[3]}[r], 9, 10), (pad + k * cell + 5,
                                                                                       pad + r * cell + 5))
    g.alpha_composite(Image.new("RGBA", (cell, rows * cell), rgba(YELLOW, 110)), (pad + 8 * cell, pad))
    qm = heading("?", 110)
    g.alpha_composite(qm, (pad + 8 * cell + (cell - qm.width) // 2, pad + int(1.1 * cell)))
    img.alpha_composite(g, ((RW - g.width) // 2, 860))
    t = tag("5 AI habits to try with your child", "forest", 40, padx=30, pady=16)
    img.alpha_composite(t, ((RW - t.width) // 2, 1360))
    img.convert("RGB").save(out, quality=92)


def main():
    mode = sys.argv[1]
    if mode == "tts":
        return tts(*sys.argv[2:4], SCENES, sys.argv[4], speed=1.1)
    if mode == "cover":
        return cover(sys.argv[2])
    src, work = sys.argv[2:4]
    tl = timeline(work)
    if mode == "audio":
        print("soundtrack", mix_soundtrack(tl, src, work, cue_fx, bpm=108, bed_lufs=-31.0))
    elif mode == "preview":
        sc = next(s for s in tl if s["id"] == sys.argv[4])
        os.makedirs(os.path.join(work, "preview"), exist_ok=True)
        f = frame_fn(*elements(sc, src))
        last = 0
        for t in sorted(float(x) for x in sys.argv[5:]):
            for n in range(last, int(t * FPS)):
                f(n / FPS)
            last = int(t * FPS)
            path = os.path.join(work, "preview", f"{sc['id']}_{t:05.2f}.png")
            f(t).save(path)
            print(path)
    elif mode == "scenes":
        os.makedirs(os.path.join(work, "scenes"), exist_ok=True)
        jobs = sorted([(i, s, src, work) for i, s in enumerate(tl)], key=lambda j: -j[1]["frames"])
        with multiprocessing.Pool(4) as pool:
            for sid in pool.imap_unordered(render_job, jobs):
                print("rendered", sid, flush=True)
    elif mode == "final":
        final_encode(tl, work, sys.argv[4], crf=17, gop=60)
        print("wrote", sys.argv[4])


if __name__ == "__main__":
    main()
