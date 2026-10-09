#!/usr/bin/env python3
"""Render the TAICY hype videos: an Instagram Reel (9:16) and a LinkedIn video (1:1).

    python3 promo.py insta.json
    python3 promo.py linkedin.json

Every shot's picture comes from a privacy-safe clip made by sanitize.py (students'
faces and Zoom names blurred, the facilitator sharp). Pop captions are timed from
word-level speech recognition, cached in <edl>_words.json.
"""
import argparse
import difflib
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "parent-highlight-taicy-round2"))
sys.path.insert(0, os.path.join(HERE, "..", "instagram-reel-taicy-round2"))
import graphics as g  # noqa: E402
import music  # noqa: E402
from render import FF, measure_lufs, run  # noqa: E402

import sanitize  # noqa: E402

SR = 48000
FPS = 25
FORMATS = {
    "reel": {"W": 1080, "H": 1920, "foot": (0, 490, 1080, 1080), "head_y": 236, "head_h": 240,
             "head_sizes": (74, 68, 62, 56), "head_w": 960, "pill_y": 1172, "cap_y": 1236,
             "cap_font": 66, "cap_w": 940, "cap_lh": 82, "wordmark": (540, 176, 46)},
    "linkedin": {"W": 1080, "H": 1080, "foot": (0, 236, 1080, 608), "head_y": 66, "head_h": 166,
                 "head_sizes": (60, 56, 52, 48), "head_w": 1000, "pill_y": 856, "cap_y": 906,
                 "cap_font": 54, "cap_w": 1000, "cap_lh": 66, "wordmark": (540, 18, 38)},
}
WHO = {
    "coach": ("COACH VK", g.GOLD, g.NAVY),
    "student": ("STUDENT", g.TEAL, g.NAVY),
    "play": ("LIVE GAMEPLAY", g.SLATE, g.WHITE),
}
# where to look in each recording (source pixels)
VK_CENTER = {"r2": (1953, 300), "sep20": (1920, 330), "oct04": (1930, 640)}
PROJECT = (1460, 300)  # top-left of the student's game panel in oct04 (crop stays clear of browser chrome and the chat)
TAICY_LOGO = os.path.join(HERE, "assets", "taicy_logo.jpg")
FREE_SESSION = "https://tally.so/r/gDgLeN"  # free live session sign-up


# ------------------------------------------------------------------ geometry

def crop_for(shot, aspect):
    """Source crop (x, y, w, h) for a shot's view at the window's aspect ratio (w/h)."""
    src = shot["src"]
    sw, sh = sanitize.SOURCES[src]["size"]
    view = shot["view"]
    if "crop" in shot:
        return tuple(shot["crop"])
    if view == "vk":
        tx, ty, tw, th = sanitize.SOURCES[src]["vk_tile"]
        h = th if aspect >= 1 else th
        w = min(tw, int(round(h * aspect)))
        h = int(round(w / aspect))
        cx, cy = VK_CENTER[src]
        x = min(max(cx - w // 2, tx), tx + tw - w)
        y = min(max(cy - h // 2, ty), ty + th - h)
        return (x, y, w, h)
    if view == "project":
        x0, y0 = PROJECT
        w = 960
        h = int(round(w / aspect))
        y = y0 if aspect >= 1 else y0
        if aspect >= 1.5:  # 16:9 window: the plane cards near the top of the panel
            y = 330
        return (x0, y, w, min(h, sh - y))
    if view == "game":
        cx = shot.get("cx", sw // 2 if src != "oct04" else 1170)
        h = min(sh, int(round(sw / aspect)))
        w = int(round(h * aspect))
        x = min(max(cx - w // 2, 0), sw - w)
        return (x, (sh - h) // 2, w, h)
    # "fit"/"gallery"/"slide": the whole frame at 16:9 (handled by fit mode when the window isn't 16:9)
    h = sh
    w = min(sw, int(round(h * 16 / 9)))
    return ((sw - w) // 2, 0, w, h)


def is_fit(shot, fmt):
    return shot["view"] in ("gallery", "slide", "fit") and abs(fmt["foot"][2] / fmt["foot"][3] - 16 / 9) > 0.05


# ------------------------------------------------------------------ graphics

def background(fmt, hexes=True):
    W, H = fmt["W"], fmt["H"]
    grad = Image.new("RGBA", (1, H))
    for y in range(H):
        t = y / (H - 1)
        grad.putpixel((0, y), tuple(int(g.DEEP[i] + (g.NAVY[i] - g.DEEP[i]) * t) for i in range(3)) + (255,))
    img = grad.resize((W, H))
    img.alpha_composite(g.radial_glow((W, H), (int(W * 0.1), int(H * 0.08)), int(W * 0.5), g.TEAL, 60))
    img.alpha_composite(g.radial_glow((W, H), (int(W * 0.95), int(H * 0.95)), int(W * 0.52), g.GOLD, 40))
    img.alpha_composite(g.radial_glow((W, H), (W, int(H * 0.22)), int(W * 0.35), g.CRIMSON, 40))
    d = ImageDraw.Draw(img)
    for cx, cy, r, a in [(W - 100, H - 160, 170, 16), (90, H - 220, 120, 12), (W - 40, 130, 90, 12)][:3 if hexes else 0]:
        d.polygon(g.hexagon(cx, cy, r), outline=(255, 255, 255, a), width=3)
    x, y, s = fmt["wordmark"]
    g.wordmark(d, (x, y), s, anchor="mt")
    return img


def chrome(fmt):
    """Teal line above the footage and a caption scrim over its lower part (reel only)."""
    W, H = fmt["W"], fmt["H"]
    fx, fy, fw, fh = fmt["foot"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if fmt is FORMATS["reel"]:
        scrim = Image.new("L", (1, fh))
        for y in range(fh):
            t = (y - 600) / 480
            scrim.putpixel((0, y), int(200 * max(0, min(1, t)) ** 1.3))
        black = Image.new("RGBA", (fw, fh), (8, 13, 27, 255))
        black.putalpha(scrim.resize((fw, fh)))
        img.alpha_composite(black, (fx, fy))
    d = ImageDraw.Draw(img)
    d.line([0, fy, W, fy], fill=g.TEAL + (200,), width=4)
    if fmt is FORMATS["linkedin"]:
        d.line([0, fy + fh, W, fy + fh], fill=g.TEAL + (120,), width=2)
    return img


def rich_words(text):
    out, gold = [], False
    for tok in text.split():
        if tok.startswith("*"):
            gold = True
        out.append((tok.strip("*"), gold))
        if tok.endswith("*"):
            gold = False
    return out


def headline_png(fmt, text):
    W, hh = fmt["W"], fmt["head_h"]
    img = Image.new("RGBA", (W, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for size in fmt["head_sizes"]:
        f = g.font(800, size)
        lines = []
        for part in text.split("|"):
            cur = []
            for w in rich_words(part):
                trial = cur + [w]
                if d.textlength(" ".join(x for x, _ in trial), font=f) <= fmt["head_w"] or not cur:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = [w]
            lines.append(cur)
        if len(lines) <= 2:
            break
    lh = int(size * 1.12)
    y = (hh - lh * len(lines)) // 2
    for line in lines:
        x = (W - d.textlength(" ".join(x for x, _ in line), font=f)) / 2
        for word, gold in line:
            d.text((x, y), word, font=f, fill=g.GOLD if gold else g.WHITE, stroke_width=3, stroke_fill=g.DEEP)
            x += d.textlength(word + " ", font=f)
        y += lh
    return img


def pill_png(fmt, who):
    label, fill, fg = WHO[who]
    img = Image.new("RGBA", (fmt["W"], 60), (0, 0, 0, 0))
    g.pill(ImageDraw.Draw(img), fmt["W"] / 2, 8, label, fill, fg, size=22, pad_x=20, h=44, anchor="m")
    return img


def two_lines(d, ws, f, maxw):
    if d.textlength(" ".join(ws), font=f) <= maxw:
        return [ws]
    for i in range(len(ws) - 1, 0, -1):
        a, b = ws[:i], ws[i:]
        if d.textlength(" ".join(a), font=f) <= maxw and d.textlength(" ".join(b), font=f) <= maxw:
            while len(a) > 1 and d.textlength(" ".join(a[:-1]), font=f) >= d.textlength(" ".join([a[-1]] + b), font=f):
                a, b = a[:-1], [a[-1]] + b
            return [a, b]
    return None


def chunk_words(fmt, words):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    f = g.font(800, fmt["cap_font"])
    chunks, cur = [], []
    for w in words:
        trial = cur + [w]
        if cur and not two_lines(d, [x["w"] for x in trial], f, fmt["cap_w"]):
            chunks.append(cur)
            trial = [w]
        cur = trial
        if (w["w"][-1] in ".?!" and len(cur) >= 2) or len(cur) >= 6:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def caption_png(fmt, chunk, hi):
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    f = g.font(800, fmt["cap_font"])
    lines = two_lines(d0, [w["w"] for w in chunk], f, fmt["cap_w"]) or [[w["w"] for w in chunk]]
    lh = fmt["cap_lh"]
    img = Image.new("RGBA", (fmt["W"], lh * 2 + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 8 if len(lines) == 2 else 8 + lh // 2
    k = 0
    for line in lines:
        x = (fmt["W"] - d.textlength(" ".join(line), font=f)) / 2
        for word in line:
            d.text((x, y), word, font=f, fill=g.GOLD if k == hi else g.WHITE, stroke_width=7, stroke_fill=(8, 13, 27))
            x += d.textlength(word + " ", font=f)
            k += 1
        y += lh
    return img


def taicy_sticker(width):
    """The TAICY logo on a white rounded card with a soft shadow (it is designed on white)."""
    logo = Image.open(TAICY_LOGO).convert("RGBA")
    pad = int(width * 0.06)
    lw = width - 2 * pad
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    card = Image.new("RGBA", (width + 40, logo.height + 2 * pad + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 28, 20 + width, 28 + logo.height + 2 * pad], 34, fill=(0, 0, 0, 150))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(card).rounded_rectangle([20, 20, 20 + width, 20 + logo.height + 2 * pad], 34, fill=(255, 255, 255, 255))
    card.alpha_composite(logo, (20 + pad, 20 + pad))
    return card


def qr_png(url, size):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2, box_size=10)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color=g.NAVY, back_color=(255, 255, 255)).convert("RGBA").resize((size, size), Image.NEAREST)


def button(d, cx, y, label, w, h, size):
    bx = cx - w / 2
    d.rounded_rectangle([bx, y + 8, bx + w, y + h + 8], h // 2, fill=(150, 110, 10, 255))
    d.rounded_rectangle([bx, y, bx + w, y + h], h // 2, fill=g.GOLD)
    f = g.font(800, size)
    tw = d.textlength(label, font=f)
    tx = cx - (tw + 50) / 2
    d.text((tx, y + h / 2 + 2), label, font=f, fill=g.NAVY, anchor="lm")
    ax, ay = tx + tw + 20, y + h / 2 + 2
    d.line([ax, ay, ax + 28, ay], fill=g.NAVY, width=6)
    d.line([ax + 16, ay - 12, ax + 29, ay, ax + 16, ay + 12], fill=g.NAVY, width=6, joint="curve")


def layer(fmt):
    return Image.new("RGBA", (fmt["W"], fmt["H"]), (0, 0, 0, 0))


def text_c(d, y, s, size, fill, weight=800, W=1080):
    d.text((W / 2, y), s, font=g.font(weight, size), fill=fill, anchor="mt")


def rich_c(d, y, text, size, W=1080, weight=800):
    f = g.font(weight, size)
    words = rich_words(text)
    x = (W - d.textlength(" ".join(w for w, _ in words), font=f)) / 2
    for w, gold in words:
        d.text((x, y), w, font=f, fill=g.GOLD if gold else g.WHITE)
        x += d.textlength(w + " ", font=f)


PRIZES = ["Nintendo Switch game", "LEGO Creator set", "Kindle", "Amazon Echo Dot", "Headphones", "Amazon gift card"]


def card_layers(fmt, kind, out, extra):
    """Each card is a background plus layers that slide in at their start times."""
    W, H = fmt["W"], fmt["H"]
    reel = fmt is FORMATS["reel"]
    opt = lambda k, default: extra.get(k, default)  # noqa: E731  per-shot text overrides from the EDL
    base = background(fmt)
    base.save(f"{out}/{kind}_0.png")
    layers = [(f"{kind}_0.png", 0.0)]

    def add(img, t):
        n = len(layers)
        img.save(f"{out}/{kind}_{n}.png")
        layers.append((f"{kind}_{n}.png", t))

    if kind == "prizes":
        l = layer(fmt)
        st = taicy_sticker(560 if reel else 470)
        l.alpha_composite(st, ((W - st.width) // 2, 280 if reel else 80))
        add(l, 0.0)
        y0 = (280 + st.height + 40) if reel else (80 + st.height + 34)
        l = layer(fmt); d = ImageDraw.Draw(l)
        rich_c(d, y0, "Prizes up for *grabs*", 70 if reel else 62, W)
        add(l, 0.35)
        cw, chh, gap = (460, 92, 20) if reel else (470, 84, 20)
        cols = 2
        gx = (W - (cw * cols + gap)) // 2
        gy = y0 + (110 if reel else 100)
        for i, p in enumerate(PRIZES):
            l = layer(fmt); d = ImageDraw.Draw(l)
            x = gx + (i % cols) * (cw + gap)
            y = gy + (i // cols) * (chh + gap)
            d.rounded_rectangle([x, y, x + cw, y + chh], chh // 2, fill=(30, 41, 59, 240), outline=g.GOLD + (200,), width=3)
            d.ellipse([x + 22, y + chh / 2 - 9, x + 40, y + chh / 2 + 9], fill=g.GOLD)
            d.text((x + 58, y + chh / 2), p, font=g.font(700, 36 if reel else 34), fill=g.WHITE, anchor="lm")
            add(l, 0.6 + 0.12 * i)
        ly = gy + 3 * (chh + gap) + (24 if reel else 16)
        l = layer(fmt); d = ImageDraw.Draw(l)
        text_c(d, ly, "+ paid internships for standout students", 40 if reel else 36, g.TEAL_TEXT, 700, W)
        add(l, 1.5)
        l = layer(fmt); d = ImageDraw.Draw(l)
        rich_c(d, ly + (90 if reel else 76), "Winners announced *soon*", 76 if reel else 64, W)
        add(l, 2.0)

    elif kind == "taicy":  # reel: a quick title card between the AI build and the live games
        l = layer(fmt)
        st = taicy_sticker(640)
        l.alpha_composite(st, ((W - st.width) // 2, 500))
        add(l, 0.0)
        y = 500 + st.height + 30
        l = layer(fmt); d = ImageDraw.Draw(l)
        rich_c(d, y, "Real problems. *Real solutions.*", 64, W)
        text_c(d, y + 84, "Ages 8–15  ·  open globally", 40, g.TEAL_TEXT, 700, W)
        add(l, 0.3)
        for i, (tag, line) in enumerate([("ROUND 1", "Build with AI"), ("ROUND 2", "Win as a team, live")]):
            l = layer(fmt); d = ImageDraw.Draw(l)
            x0, y0 = 120, y + 190 + i * 128
            d.rounded_rectangle([x0, y0, W - x0, y0 + 104], 52, fill=(30, 41, 59, 240),
                                outline=(g.GOLD if i == 0 else g.TEAL) + (200,), width=3)
            g.pill(d, x0 + 28, y0 + 30, tag, g.GOLD if i == 0 else g.TEAL, g.NAVY, size=22, h=44)
            d.text((x0 + 210, y0 + 52), line, font=g.font(800, 44), fill=g.WHITE, anchor="lm")
            add(l, 0.65 + 0.3 * i)

    elif kind == "round":  # a round's title: pill, two-line title, one line of detail
        y = opt("y", 700 if reel else 330)
        l = layer(fmt); d = ImageDraw.Draw(l)
        g.pill(d, W / 2, y, opt("tag", "ROUND 1  ·  CREATE"), g.GOLD if opt("gold", True) else g.TEAL, g.NAVY,
               size=26 if reel else 22, h=54 if reel else 46, pad_x=24, anchor="m")
        add(l, 0.0)
        size = 84 if reel else 64
        for k, line in enumerate(opt("title", "Spot a real problem.|*Build the fix with AI.*").split("|")):
            l = layer(fmt); d = ImageDraw.Draw(l)
            rich_c(d, y + (110 if reel else 86) + k * int(size * 1.15), line, size, W)
            add(l, 0.2 + 0.25 * k)
        l = layer(fmt); d = ImageDraw.Draw(l)
        text_c(d, y + (110 if reel else 86) + 2 * int(size * 1.15) + 30, opt("sub", ""), 40 if reel else 32,
               (203, 213, 225), 600, W)
        add(l, 0.75)

    elif kind == "rubric":  # LinkedIn: how Round 1 was judged, and the AI Use Log
        l = layer(fmt); d = ImageDraw.Draw(l)
        g.pill(d, W / 2, 70, "ROUND 1  ·  HOW IT WAS JUDGED", g.GOLD, g.NAVY, size=20, h=42, anchor="m")
        rich_c(d, 130, "Judges scored the *thinking,*", 52, W)
        rich_c(d, 192, "not the production.", 52, W)
        add(l, 0.0)
        for i, (name, pct) in enumerate([("Problem identification", 25), ("Proposed solution", 25),
                                         ("Working prototype & AI use", 30), ("Pitch / explanation", 20)]):
            l = layer(fmt); d = ImageDraw.Draw(l)
            y0 = 290 + i * 70
            d.text((90, y0 + 22), name, font=g.font(700, 32), fill=g.WHITE, anchor="lm")
            bx, bw = 560, 340
            d.rounded_rectangle([bx, y0 + 8, bx + bw, y0 + 36], 14, fill=(30, 41, 59, 255))
            d.rounded_rectangle([bx, y0 + 8, bx + int(bw * pct / 30), y0 + 36], 14, fill=g.GOLD if pct == 30 else g.TEAL)
            d.text((bx + bw + 24, y0 + 22), f"{pct}%", font=g.font(800, 32), fill=g.GOLD if pct == 30 else g.WHITE, anchor="lm")
            add(l, 0.4 + 0.2 * i)
        l = layer(fmt); d = ImageDraw.Draw(l)
        x0, y0, x1 = 70, 600, W - 70
        d.rounded_rectangle([x0, y0, x1, y0 + 330], 28, fill=(30, 41, 59, 235), outline=g.TEAL + (160,), width=2)
        d.text((W / 2, y0 + 30), "Every entry came with an AI Use Log", font=g.font(800, 38), fill=g.WHITE, anchor="mt")
        for k, q in enumerate(["What did you ask?", "What did you change?", "What did AI get wrong?"]):
            d.text((W / 2, y0 + 100 + k * 54), q, font=g.font(700, 36), fill=g.TEAL_TEXT if k < 2 else g.GOLD, anchor="mt")
        d.text((W / 2, y0 + 270), "AI can help build the idea. The thinking must be theirs.", font=g.font(400, 28),
               fill=(203, 213, 225), anchor="mt")
        add(l, 1.4)

    elif kind == "wrap":  # congratulations, without naming anyone
        l = layer(fmt)
        st = taicy_sticker(600 if reel else 440)
        sy = 480 if reel else 90
        l.alpha_composite(st, ((W - st.width) // 2, sy))
        add(l, 0.0)
        y = sy + st.height + (40 if reel else 24)
        l = layer(fmt); d = ImageDraw.Draw(l)
        rich_c(d, y, opt("title", "TAICY 2026 is a *wrap!*"), 80 if reel else 64, W)
        add(l, 0.3)
        y += 120 if reel else 96
        l = layer(fmt); d = ImageDraw.Draw(l)
        text_c(d, y, "Congratulations to our winners", 52 if reel else 42, g.GOLD, 800, W)
        text_c(d, y + (70 if reel else 56), "and to every young innovator", 48 if reel else 38, g.WHITE, 700, W)
        text_c(d, y + (132 if reel else 104), "who took on the challenge.", 48 if reel else 38, g.WHITE, 700, W)
        add(l, 0.8)

    elif kind == "explainer":  # LinkedIn: what TAICY is
        l = layer(fmt)
        st = taicy_sticker(400)
        l.alpha_composite(st, ((W - st.width) // 2, 64))
        add(l, 0.0)
        y = 64 + st.height + 6
        l = layer(fmt); d = ImageDraw.Draw(l)
        text_c(d, y, "Ages 8–15  ·  Free to enter  ·  Open globally", 30, g.TEAL_TEXT, 700, W)
        add(l, 0.3)
        y += 62
        for i, (tag, title, lines) in enumerate([
            ("ROUND 1  ·  CREATE", "Solve a real problem with AI",
             ["Spot a problem they actually noticed", "Build a working prototype with any AI tool",
              "Log what they asked, changed and what AI got wrong"]),
            ("ROUND 2  ·  LEAD", "Win as a team, live",
             ["Random teams, live multiplayer strategy games", "No rulebook: figure it out together",
              "Every game ends with a coach-led debrief"])]):
            l = layer(fmt); d = ImageDraw.Draw(l)
            x0, y0, x1 = 60, y + i * 330, W - 60
            d.rounded_rectangle([x0, y0, x1, y0 + 310], 28, fill=(30, 41, 59, 235), outline=(255, 255, 255, 34), width=2)
            g.pill(d, x0 + 30, y0 + 28, tag, g.GOLD if i == 0 else g.TEAL, g.NAVY, size=20, h=40)
            d.text((x0 + 30, y0 + 88), title, font=g.font(800, 44), fill=g.WHITE)
            for k, line in enumerate(lines):
                yy = y0 + 160 + k * 46
                d.ellipse([x0 + 34, yy + 12, x0 + 48, yy + 26], fill=g.GOLD if i == 0 else g.TEAL)
                d.text((x0 + 64, yy), line, font=g.font(400, 32), fill=(203, 213, 225))
            add(l, 0.6 + 0.6 * i)

    elif kind == "cta" and reel:
        l = layer(fmt); d = ImageDraw.Draw(l)
        text_c(d, 360, opt("h1", "Want your child"), 92, g.WHITE, 800, W)
        text_c(d, 466, opt("h2", "in the next one?"), 92, g.GOLD, 800, W)
        add(l, 0.1)
        l = layer(fmt); d = ImageDraw.Draw(l)
        rich_c(d, 640, opt("sub", "One live, coach-led session. *Free.*"), 56, W, 700)
        add(l, 0.6)
        l = layer(fmt); d = ImageDraw.Draw(l)
        button(d, W / 2, 760, "Join a free session", 820, 132, 56)
        add(l, 1.0)
        l = layer(fmt); d = ImageDraw.Draw(l)
        text_c(d, 970, "Link in bio", 56, g.WHITE, 800, W)
        add(l, 1.4)
        l = layer(fmt); d = ImageDraw.Draw(l)
        text_c(d, 1090, "Live  ·  Coach-led  ·  Ages 8–15", 38, (203, 213, 225), 600, W)
        d.rounded_rectangle([140, 1186, W - 140, 1276], 45, outline=g.GOLD + (220,), width=3)
        text_c(d, 1210, opt("follow", "Follow @tomoclub_edu for the winners"), 38, g.GOLD, 700, W)
        add(l, 1.8)

    elif kind == "cta":  # LinkedIn: one route for parents, one for schools
        l = layer(fmt); d = ImageDraw.Draw(l)
        text_c(d, 76, opt("h1", "Want this for your child"), 58, g.WHITE, 800, W)
        rich_c(d, 146, opt("h2", "or your *school?*"), 58, W)
        add(l, 0.1)
        utm = f"utm_source=linkedin&utm_medium=video&utm_campaign={opt('campaign', 'taicy_hype')}"
        for i, (tag, head, sub, url, qr_url) in enumerate([
            ("PARENTS", "Join a free live session", "Coach-led · Ages 8–15", "Scan, or tap the link in the post",
             f"{FREE_SESSION}?{utm}"),
            ("EDUCATORS & SCHOOLS", "Bring TAICY to your school", "Game-based AI literacy + SEL", "tomoclub.org/contact-us",
             f"https://www.tomoclub.org/contact-us?{utm}")]):
            l = layer(fmt); d = ImageDraw.Draw(l)
            x0 = 50 + i * 500
            y0 = 250
            d.rounded_rectangle([x0, y0, x0 + 480, y0 + 620], 30, fill=(30, 41, 59, 240), outline=(255, 255, 255, 34), width=2)
            g.pill(d, x0 + 240, y0 + 28, tag, g.GOLD if i == 0 else g.TEAL, g.NAVY, size=19, h=38, anchor="m")
            for k, line in enumerate(g.wrap(d, head, g.font(800, 40), 420)):
                d.text((x0 + 240, y0 + 92 + k * 48), line, font=g.font(800, 40), fill=g.WHITE, anchor="mt")
            d.text((x0 + 240, y0 + 200), sub, font=g.font(400, 28), fill=g.MUTED, anchor="mt")
            qs = 240
            d.rounded_rectangle([x0 + 240 - qs / 2 - 12, y0 + 252, x0 + 240 + qs / 2 + 12, y0 + 252 + qs + 24], 16, fill=(255, 255, 255))
            l.alpha_composite(qr_png(qr_url, qs), (int(x0 + 240 - qs / 2), y0 + 264))
            d.text((x0 + 240, y0 + 540), url, font=g.font(700, 30 if i else 26), fill=g.TEAL_TEXT if i else g.GOLD, anchor="mt")
            add(l, 0.6 + 0.5 * i)
        l = layer(fmt); d = ImageDraw.Draw(l)
        rich_c(d, 902, opt("foot", "TAICY winners announced *soon.* Follow TomoClub for the reveal."), 34, W, 700)
        text_c(d, 960, "info@tomoclub.org  ·  +1 650 547-8082", 30, g.MUTED, 400, W)
        add(l, 1.8)
    return layers


# ------------------------------------------------------------------ words

def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def load_audio(src):
    path = sanitize.SOURCES[src]["path"]
    npy = os.path.splitext(path)[0] + ".mono16000.npy"
    if not os.path.exists(npy):
        raw = subprocess.run([FF, "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                             capture_output=True, check=True).stdout
        np.save(npy, np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768)
    return np.load(npy, mmap_mode="r")


def word_timings(shots, cache_p, model_dir):
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    model = None
    for s in shots:
        if "card" in s:
            continue
        key = f"{s['src']}|{s['a_in']}|{s['a_out']}|{s['text']}"
        if key in cache:
            s["words"] = cache[key]
            continue
        if model is None:
            from faster_whisper import WhisperModel
            model = WhisperModel(model_dir, device="cpu", compute_type="int8")
        audio = load_audio(s["src"])
        seg = np.array(audio[int(s["a_in"] * 16000):int(s["a_out"] * 16000)])
        res, _ = model.transcribe(seg, language="en", word_timestamps=True, beam_size=5, condition_on_previous_text=False)
        heard = [(norm(w.word), w.start) for r in res for w in r.words if norm(w.word)]
        cap = s["text"].split()
        sm = difflib.SequenceMatcher(a=[norm(w) for w in cap], b=[h[0] for h in heard], autojunk=False)
        m = {}
        for blk in sm.get_matching_blocks():
            for j in range(blk.size):
                m[blk.a + j] = heard[blk.b + j][1]
        dur = s["a_out"] - s["a_in"]
        times = [m.get(i) for i in range(len(cap))]
        times[0] = min(times[0] if times[0] is not None else 0.0, 0.25)
        for i in range(1, len(times)):
            if times[i] is None or times[i] <= times[i - 1]:
                nxt = next((t for t in times[i + 1:] if t is not None and t > times[i - 1]), dur)
                gap = next((j for j in range(i + 1, len(times)) if times[j] is not None and times[j] > times[i - 1]), len(times))
                times[i] = times[i - 1] + (nxt - times[i - 1]) / (gap - i + 1)
        s["words"] = [{"w": w, "t": round(float(t), 3)} for w, t in zip(cap, times)]
        cache[key] = s["words"]
    json.dump(cache, open(cache_p, "w"), indent=0)


# ------------------------------------------------------------------ render

def venc():
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-level:v", "4.1", "-g", str(FPS * 2), "-color_primaries", "bt709", "-color_trc", "bt709",
            "-colorspace", "bt709", "-r", str(FPS)]


def footage_filter(shot, fmt, dur, speed=1.0):
    fx, fy, fw, fh = fmt["foot"]
    pts = f"setpts=(PTS-STARTPTS)/{speed}" if speed != 1 else "setpts=PTS-STARTPTS"
    if shot["view"] == "fitv":  # a portrait phone video: the whole crop, centred over a blurred fill of itself
        sw, sh = sanitize.SOURCES[shot["src"]]["size"]
        x, y, w, h = shot.get("crop", (0, 0, sw, sh))
        k = min(fw / w, fh / h)
        tw, th = int(w * k) // 2 * 2, int(h * k) // 2 * 2
        return (f"[0:v]{pts},fps={FPS},crop={w}:{h}:{x}:{y},split[fa][fb];"
                f"[fa]scale={tw}:{th}:flags=lanczos[fg];"
                f"[fb]scale={fw}:{fh}:force_original_aspect_ratio=increase,crop={fw}:{fh},gblur=sigma=30,"
                f"eq=brightness=-0.2:saturation=0.8[bg];[bg][fg]overlay={(fw - tw) // 2}:{(fh - th) // 2}[foot]")
    if is_fit(shot, fmt):
        x, y, w, h = crop_for(shot, 16 / 9)
        bh = int(round(fw * 9 / 16 / 2)) * 2
        return (f"[0:v]{pts},fps={FPS},crop={w}:{h}:{x}:{y},split[fa][fb];"
                f"[fa]scale={fw}:{bh}:flags=lanczos[fg];"
                f"[fb]scale=-2:{fh}:flags=bilinear,crop={fw}:{fh},gblur=sigma=28,eq=brightness=-0.18:saturation=0.8[bg];"
                f"[bg][fg]overlay=0:{(fh - bh) // 2}[foot]")
    x, y, w, h = crop_for(shot, fw / fh)
    zoom = shot.get("zoom", 0.06)
    z = (f",scale=w='trunc({fw}*(1+{zoom}*t/{dur:.3f})/2)*2':h=-2:eval=frame:flags=bicubic,crop={fw}:{fh}"
         if zoom else "")
    return f"[0:v]{pts},fps={FPS},crop={w}:{h}:{x}:{y},scale={fw}:{fh}:flags=lanczos{z}[foot]"


def render_shot(shot, fmt, clip, gdir, seg, head_png, head_new, pill_path, caps):
    dur = shot["a_out"] - shot["a_in"]
    W, H = fmt["W"], fmt["H"]
    fx, fy, fw, fh = fmt["foot"]
    args = ["-i", clip]
    imgs = [os.path.join(gdir, "bg.png"), os.path.join(gdir, "chrome.png"), head_png, pill_path] + [c["png"] for c in caps]
    for p in imgs:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", p]
    fc = footage_filter(shot, fmt, dur, shot.get("speed", 1.0))
    fc += f";[1:v][foot]overlay={fx}:{fy}[a0];[a0][2:v]overlay=0:0[a1]"
    hy = fmt["head_y"]
    if head_new:
        fc += f";[3:v]format=rgba,fade=t=in:st=0:d=0.22:alpha=1[hd];[a1][hd]overlay=0:'{hy}+30*max(0,1-t/0.22)'[a2]"
    else:
        fc += f";[a1][3:v]overlay=0:{hy}[a2]"
    fc += f";[a2][4:v]overlay=0:{fmt['pill_y']}[a3]"
    cur = "[a3]"
    for k, c in enumerate(caps):
        fc += f";{cur}[{5 + k}:v]overlay=0:{fmt['cap_y']}:enable='between(t,{c['t0']:.3f},{c['t1'] - 0.001:.3f})'[c{k}]"
        cur = f"[c{k}]"
    fc += f";{cur}format=yuv420p[vout]"
    run(args + ["-filter_complex", fc, "-map", "[vout]", "-an", "-t", f"{dur:.3f}"] + venc() + [seg])


def render_card(layers, dur, gdir, seg):
    args = []
    for p, _ in layers:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", os.path.join(gdir, p)]
    fc = "[0:v]format=rgba[l0]"
    cur = "[l0]"
    for k, (_, t_in) in enumerate(layers[1:], start=1):
        fc += (f";[{k}:v]format=rgba,fade=t=in:st={t_in:.2f}:d=0.3:alpha=1[f{k}];"
               f"{cur}[f{k}]overlay=0:'28*max(0,1-(t-{t_in:.2f})/0.3)*gte(t,{t_in:.2f})'[m{k}]")
        cur = f"[m{k}]"
    fc += f";{cur}fade=t=in:st=0:d=0.2,fade=t=out:st={dur - 0.35:.3f}:d=0.35,format=yuv420p[vout]"
    run(args + ["-filter_complex", fc, "-map", "[vout]", "-t", f"{dur:.3f}"] + venc() + [seg])


def clip_loudness(src, t0, dur):
    err = run(["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", sanitize.SOURCES[src]["path"], "-vn", "-af", "ebur128",
               "-f", "null", "-"])
    tail = err[err.rfind("Summary:"):]
    for line in tail.splitlines():
        if line.strip().startswith("I:"):
            v = float(line.split()[1])
            return v if v > -70 else -23.0
    return -23.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("--build", default=None)
    ap.add_argument("--only")
    ap.add_argument("--keep", action="store_true", help="reuse existing segments")
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "medium.en"))
    a = ap.parse_args()
    edl_path = os.path.abspath(a.edl) if os.path.exists(a.edl) else os.path.join(HERE, a.edl)
    base = os.path.dirname(edl_path)  # build/, out/ and the caption cache live next to the EDL
    edl = json.load(open(edl_path))
    name = os.path.splitext(os.path.basename(a.edl))[0]
    fmt = FORMATS[edl["format"]]
    build = a.build or os.path.join(base, "build", name)
    gdir, sdir, cdir = (os.path.join(build, d) for d in ("gfx", "segments", "clips"))
    for d in (gdir, sdir, cdir):
        os.makedirs(d, exist_ok=True)
    out = os.path.join(base, edl["output"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shots = edl["shots"]
    for s in shots:
        if "card" in s:
            s["dur"] = round(s["dur"] * FPS) / FPS
        else:
            s["a_out"] = round(s["a_in"] + round((s["a_out"] - s["a_in"]) * FPS) / FPS, 4)
    word_timings(shots, os.path.join(base, f"{name}_words.json"), a.model)

    background(fmt).save(os.path.join(gdir, "bg.png"))
    chrome(fmt).save(os.path.join(gdir, "chrome.png"))
    only = set(a.only.split(",")) if a.only else None
    privacy = {}
    segs, t, head, head_png, marks = [], 0.0, None, None, {}
    for n, s in enumerate(shots):
        seg = os.path.join(sdir, f"{n:02d}_{s['id']}.mov")
        todo = (not only or s["id"] in only) and not (a.keep and os.path.exists(seg))
        if "card" in s:
            if todo:
                render_card(card_layers(fmt, s["card"], gdir, s), s["dur"], gdir, seg)
            marks.setdefault(s["card"], t)
            if s.get("mark"):
                marks[s["mark"]] = t
            t += s["dur"]
            segs.append(seg)
            continue
        dur = s["a_out"] - s["a_in"]
        speed = s.get("speed", 1.0)
        head_new = bool(s.get("head")) and s["head"] != head
        if s.get("head"):
            head = s["head"]
            head_png = os.path.join(gdir, f"head_{n:02d}.png")
            headline_png(fmt, head).save(head_png)
        pp = os.path.join(gdir, f"pill_{s['who']}.png")
        pill_png(fmt, s["who"]).save(pp)
        caps = []
        words = s["words"]
        for ci, chunk in enumerate(chunk_words(fmt, words)):
            idx = words.index(chunk[-1]) + 1
            nxt = words[idx]["t"] if idx < len(words) else None
            for wi, w in enumerate(chunk):
                t0 = 0.0 if (ci == 0 and wi == 0) else w["t"]
                t1 = chunk[wi + 1]["t"] if wi + 1 < len(chunk) else (nxt if nxt is not None else dur)
                p = os.path.join(gdir, f"cap_{n:02d}_{ci}_{wi}.png")
                caption_png(fmt, chunk, wi).save(p)
                caps.append({"png": p, "t0": t0, "t1": min(t1, dur)})
        if s.get("mark"):
            marks[s["mark"]] = t
        if todo:
            v_in = s.get("v_in", s["a_in"])
            clip = os.path.join(cdir, f"{s['src']}_{v_in:.2f}_{dur * speed:.2f}.mov")
            if not os.path.exists(clip):
                privacy[s["id"]] = sanitize.sanitize(s["src"], v_in, dur * speed + 0.1, clip)
                privacy[s["id"]]["faces_outside_vk"] = sanitize.face_check(s["src"], clip)
            render_shot(s, fmt, clip, gdir, seg, head_png, head_new, pp, caps)
        print(f"  [{n + 1:2}/{len(shots)}] {s['id']:12} {dur:5.2f}s @ {t:6.2f}s", flush=True)
        segs.append(seg)
        t += dur
    total = t
    if privacy:
        rep = os.path.join(build, "privacy_report.json")
        old = json.load(open(rep)) if os.path.exists(rep) else {}
        old.update({k: {kk: vv for kk, vv in v.items() if kk != "modes"} for k, v in privacy.items()})
        json.dump(old, open(rep, "w"), indent=1)
    if only:
        return

    lst = os.path.join(build, "concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in segs)
    video = os.path.join(build, "video.mov")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    # voices: each shot's words, loudness-matched; cards are silence
    prev = None
    for s in shots:
        if "card" in s:
            continue
        dur = s["a_out"] - s["a_in"]
        if s.get("joined"):  # continues the previous sentence: same gain, no fades at the join
            gain = prev["_gain"]
            prev["_fo"] = 0
        else:
            gain = max(min(-18.0 - clip_loudness(s["src"], s["a_in"], dur), 12.0), -12.0)
        s["_gain"], s["_fo"], s["_fi"] = gain, s.get("fade_out", 0.03), 0 if s.get("joined") else 0.02
        prev = s
    inputs, chains, idx = [], [], 0
    for k, s in enumerate(shots):
        if "card" in s:
            chains.append(f"anullsrc=r={SR}:cl=stereo,atrim=0:{s['dur']:.4f},asetpts=PTS-STARTPTS[v{k}]")
            continue
        dur = s["a_out"] - s["a_in"]
        inputs += ["-ss", f"{s['a_in']:.3f}", "-t", f"{dur:.3f}", "-i", sanitize.SOURCES[s["src"]]["path"]]
        chains.append(f"[{idx}:a]asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo,"
                      f"pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,highpass=f=90,volume={s['_gain']:.2f}dB,"
                      f"acompressor=threshold=-20dB:ratio=3:attack=5:release=150:makeup=1.5,"
                      + (f"afade=t=in:d={s['_fi']}," if s["_fi"] else "")
                      + (f"afade=t=out:st={dur - s['_fo']:.3f}:d={s['_fo']:.3f}," if s["_fo"] else "")
                      + f"apad=whole_dur={dur:.4f},atrim=0:{dur:.4f}[v{k}]")
        idx += 1
    voice = os.path.join(build, "voice.wav")
    run(inputs + ["-filter_complex", ";".join(chains) + ";" + "".join(f"[v{k}]" for k in range(len(shots)))
                  + f"concat=n={len(shots)}:v=0:a=1[vo]", "-map", "[vo]", "-c:a", "pcm_s16le", voice])

    # music
    mcfg = edl.get("music", {})
    music.BPM = mcfg.get("bpm", 120)
    music.BEAT = 60 / music.BPM
    music.BAR = 4 * music.BEAT
    if "prog" in mcfg:
        music.PROG, music.ROOTS = mcfg["prog"], mcfg["roots"]
    mus = os.path.join(build, "music.wav")
    drop = marks.get(mcfg.get("drop_at", "cta"), total - 8)
    bd = (marks.get(mcfg["breakdown"][0]), marks.get(mcfg["breakdown"][1])) if "breakdown" in mcfg else (None, None)
    music.make_track(mus, total, drop, breakdown=bd)
    I, TP = -14, -1.0
    mvol = mcfg.get("volume_db", -9)
    for variant, with_music in (("", True), ("_no-music", False)):
        mix = os.path.join(build, f"mix{variant}.wav")
        if with_music:
            fc = (f"[1:a]volume={mvol}dB,highshelf=f=6000:g=2[m];[0:a]asplit=2[vo][sc];"
                  f"[m][sc]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=350:makeup=1[md];"
                  f"[vo][md]amix=inputs=2:duration=first:normalize=0[mx]")
            run(["-i", voice, "-i", mus, "-filter_complex", fc, "-map", "[mx]", "-c:a", "pcm_s24le", mix])
        else:
            run(["-i", voice, "-c:a", "pcm_s24le", mix])
        err = run(["-i", mix, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"])
        js = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
        ln = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
              f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
        mastered = os.path.join(build, f"master{variant}.wav")
        run(["-i", mix, "-af", ln + f",aresample={SR}", "-c:a", "pcm_s24le", mastered])
        got = measure_lufs(mastered)
        if abs(got - I) > 0.5:
            fixed = mastered.replace(".wav", "_fix.wav")
            run(["-i", mastered, "-af", f"volume={I - got:.2f}dB,alimiter=limit={10 ** (TP / 20):.4f}:level=false",
                 "-c:a", "pcm_s24le", fixed])
            mastered = fixed
        dst = out.replace(".mp4", f"{variant}.mp4")
        run(["-i", video, "-i", mastered, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-ar", str(SR), "-movflags", "+faststart", "-metadata", f"title={edl['title']}",
             "-metadata", "copyright=© 2026 TomoClub", dst])
        print(f"{dst}  {total:.1f}s  {measure_lufs(dst):.1f} LUFS")


if __name__ == "__main__":
    main()
