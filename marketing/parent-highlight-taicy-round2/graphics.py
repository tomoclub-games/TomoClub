"""Brand graphics for the TAICY Round 2 parent highlight (1920x1080, 16:9).

Everything is drawn with Pillow from the TomoClub web palette and the Outfit
typeface, so the video matches tomoclub.org/parents. Layers are written as
transparent PNGs that render.py composites over the footage with ffmpeg.
"""
import math
import os
import re

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080

# tomoclub.org palette (styles.css / b2c-parents)
NAVY = (15, 23, 42)
DEEP = (8, 13, 27)
SLATE = (51, 65, 85)
SURFACE = (30, 41, 59)
TEAL = (42, 180, 184)
TEAL_TEXT = (79, 209, 213)
GOLD = (253, 198, 45)
CRIMSON = (179, 65, 88)
CRIMSON_TEXT = (231, 132, 154)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)

# Title-safe area (SMPTE ST 2046-1, 90%): all text stays inside it.
SAFE_X0, SAFE_Y0, SAFE_X1, SAFE_Y1 = 96, 54, 1824, 1026

# Footage window and the caption band under it.
FOOT = (96, 54, 1408, 792)  # x, y, w, h (16:9)
FOOT_R = 22
SIDE_X0, SIDE_X1 = 1544, 1824
CAP_Y = 866  # top of the caption band
CAP_CX = FOOT[0] + FOOT[2] // 2

# Contact details and CTA (from tomoclub.org and tomoclub.org/parents).
CTA = "Book a FREE trial class"
CTA_URL = "tomoclub.org/parents"
QR_URL = "https://www.tomoclub.org/parents?utm_source=video&utm_medium=parent_highlight&utm_campaign=taicy_r2"
EMAIL = "info@tomoclub.org"
PHONE = "+1 650 547-8082"
SOCIALS = "Instagram @tomoclub_edu   ·   YouTube @tomoclubedu   ·   WhatsApp channel: TomoClub"

ROLE_STYLE = {
    # role: (pill label, pill fill, pill text)
    "question": ("FACILITATOR ASKS", GOLD, NAVY),
    "student": ("STUDENT VOICE", TEAL, NAVY),
    "insight": ("THE LEARNING", CRIMSON, WHITE),
    "facilitator": ("FACILITATOR", SLATE, WHITE),
    "play": ("IN THE GAME", SLATE, TEAL_TEXT),
}


def font(weight, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", f"Outfit-{weight}.ttf"), size)


def text_w(draw, s, f, tracking=0):
    if not s:
        return 0
    return draw.textlength(s, font=f) + tracking * (len(s) - 1)


def draw_text(draw, xy, s, f, fill, tracking=0, anchor="la"):
    """Draw text with optional letter-spacing (tracking in px)."""
    if not tracking:
        draw.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    x, y = xy
    total = text_w(draw, s, f, tracking)
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    # Per-glyph drawing must share one baseline, so convert the vertical anchor to it.
    ascent, descent = f.getmetrics()
    y += {"a": ascent, "t": ascent, "m": (ascent - descent) / 2, "s": 0, "d": -descent}[anchor[1]]
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += draw.textlength(ch, font=f) + tracking


def wordmark(draw, xy, size, anchor="la"):
    """TomoClub wordmark as on the site nav: To (teal) mo (gold) Club (crimson), Outfit 800, -0.04em."""
    f = font(800, size)
    tr = -0.04 * size
    parts = [("To", TEAL), ("mo", GOLD), ("Club", CRIMSON)]
    total = sum(text_w(draw, p, f, tr) for p, _ in parts) + tr * 2
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    for p, c in parts:
        draw_text(draw, (x, y), p, f, c, tracking=tr, anchor="l" + anchor[1])
        x += text_w(draw, p, f, tr) + tr
    return total


def radial_glow(size, center, radius, color, alpha):
    layer = Image.new("RGBA", size, color + (0,))
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(radius * 0.45))
    layer.putalpha(mask)
    return layer


def hexagon(cx, cy, r, rot=30):
    return [(cx + r * math.cos(math.radians(a + rot)), cy + r * math.sin(math.radians(a + rot))) for a in range(0, 360, 60)]


def background():
    """Navy canvas with soft teal/gold glows and faint hexagons (a nod to the strategy game)."""
    img = Image.new("RGBA", (W, H), DEEP + (255,))
    # vertical gradient DEEP -> NAVY
    grad = Image.new("RGBA", (1, H))
    for y in range(H):
        t = y / (H - 1)
        grad.putpixel((0, y), tuple(int(DEEP[i] + (NAVY[i] - DEEP[i]) * t) for i in range(3)) + (255,))
    img = grad.resize((W, H))
    img.alpha_composite(radial_glow((W, H), (160, 80), 520, TEAL, 46))
    img.alpha_composite(radial_glow((W, H), (1840, 1040), 560, GOLD, 30))
    img.alpha_composite(radial_glow((W, H), (1900, 200), 380, CRIMSON, 34))
    hexes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(hexes)
    for cx, cy, r, a in [(1700, 930, 150, 16), (1860, 760, 90, 12), (1560, 1080, 110, 10), (60, 1000, 120, 10), (1880, 90, 70, 12)]:
        d.polygon(hexagon(cx, cy, r), outline=(255, 255, 255, a), width=3)
    img.alpha_composite(hexes)
    return img


def rounded_mask(size, box, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
    return m


def frame_overlay():
    """Full-frame background with a transparent rounded window where the footage shows through."""
    x, y, w, h = FOOT
    bg = background()
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([x, y + 10, x + w, y + h + 10], FOOT_R, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    bg.alpha_composite(shadow)
    hole = rounded_mask((W, H), [x, y, x + w - 1, y + h - 1], FOOT_R)
    alpha = bg.getchannel("A").point(lambda v: v)
    alpha.paste(0, mask=hole)
    bg.putalpha(alpha)
    ImageDraw.Draw(bg).rounded_rectangle([x - 1, y - 1, x + w, y + h], FOOT_R + 1, outline=(255, 255, 255, 34), width=2)
    return bg


def pill(draw, x, y, label, fill, fg, size=19, pad_x=16, h=36, anchor="l"):
    f = font(700, size)
    tr = 2.2
    tw = text_w(draw, label, f, tr)
    w = tw + pad_x * 2
    if anchor == "m":
        x -= w / 2
    draw.rounded_rectangle([x, y, x + w, y + h], h // 2, fill=fill)
    draw_text(draw, (x + pad_x, y + h / 2 + 1), label, f, fg, tracking=tr, anchor="lm")
    return w


# ---------------------------------------------------------------- sidebar

def sidebar(chapter, stat=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0 = SIDE_X0
    wordmark(d, (x0, SAFE_Y0 + 2), 50, anchor="lt")
    d.line([x0, 132, SIDE_X1, 132], fill=(255, 255, 255, 38), width=2)
    y = 162
    if stat:
        draw_text(d, (x0, y), stat["kicker"], font(700, 18), TEAL_TEXT, tracking=2.4)
        y += 48
        for line in wrap(d, stat["label"], font(600, 28), SIDE_X1 - x0):
            d.text((x0, y), line, font=font(600, 28), fill=WHITE)
            y += 36
        d.text((x0 - 4, y), stat["value"], font=font(800, 110), fill=GOLD)
        y += 138
        for line in wrap(d, stat["note"], font(400, 24), SIDE_X1 - x0):
            d.text((x0, y), line, font=font(400, 24), fill=MUTED)
            y += 32
        return img
    if chapter.get("num"):
        d.text((x0 - 4, y - 18), chapter["num"], font=font(800, 120), fill=GOLD)
        y += 128
    else:
        draw_text(d, (x0, y + 4), "LIVE ON ZOOM", font(700, 18), TEAL_TEXT, tracking=2.4)
        y += 44
    # chapter title, wrapped to the sidebar width
    f = font(700, 36)
    for line in wrap(d, chapter["title"], f, SIDE_X1 - x0):
        d.text((x0, y), line, font=f, fill=WHITE)
        y += 44
    y += 30
    if chapter.get("skills"):
        draw_text(d, (x0, y), "SKILLS IN PLAY", font(700, 18), MUTED, tracking=2.4)
        y += 38
        for s in chapter["skills"]:
            fs = font(600, 24)
            tw = d.textlength(s, font=fs)
            d.rounded_rectangle([x0, y, x0 + tw + 36, y + 46], 23, outline=TEAL + (255,), width=2, fill=(42, 180, 184, 26))
            d.text((x0 + 18, y + 23), s, font=fs, fill=WHITE, anchor="lm")
            y += 60
    # footer of the sidebar, aligned with the bottom of the footage
    fy = FOOT[1] + FOOT[3]
    d.text((x0, fy - 34), "Highlights from", font=font(400, 20), fill=MUTED, anchor="ls")
    d.text((x0, fy - 4), "TAICY 2026 · Round 2", font=font(600, 22), fill=WHITE, anchor="ls")
    return img


def wrap(draw, s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if draw.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- captions

CAP_FONT = (600, 44)
CAP_MAX_CHARS = 42  # per line (Netflix/BBC style guides), max 2 lines
CAP_MAX_W = 1180


def balance_two_lines(draw, words, f):
    """Split words into <=2 lines, each <=CAP_MAX_CHARS and CAP_MAX_W px, as even as possible."""
    s = " ".join(words)
    if len(s) <= CAP_MAX_CHARS and draw.textlength(s, font=f) <= CAP_MAX_W:
        return [s]
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if max(len(a), len(b)) > CAP_MAX_CHARS:
            continue
        wa, wb = draw.textlength(a, font=f), draw.textlength(b, font=f)
        if max(wa, wb) > CAP_MAX_W:
            continue
        # prefer breaking after punctuation, and a slightly longer bottom line
        score = abs(wa - wb) - (60 if a[-1] in ",.?!;:" else 0) + (20 if wa > wb else 0)
        if best is None or score < best[0]:
            best = (score, [a, b])
    return best[1] if best else None


def chunk_caption(text):
    """Split caption text into on-screen chunks of at most two lines.

    '|' marks a forced break (e.g. a change of speaker)."""
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    f = font(*CAP_FONT)
    chunks = []
    for block in [b.strip() for b in text.split("|") if b.strip()]:
        sentences = re.findall(r"[^.?!]+[.?!]*['\"]?", block)
        sentences = [s.strip() for s in sentences if s.strip()]
        cur = []
        for sent in sentences:
            trial = cur + sent.split()
            if balance_two_lines(d, trial, f):
                cur = trial
                continue
            if cur:
                chunks.append(balance_two_lines(d, cur, f))
                cur = []
            words = sent.split()
            if balance_two_lines(d, words, f):
                cur = words
                continue
            # a long sentence: take the most words that fit, preferring a comma break
            while words:
                n = len(words)
                while n > 1 and not balance_two_lines(d, words[:n], f):
                    n -= 1
                # prefer ending a chunk at a comma, or just before a conjunction, over a mid-phrase break
                joins = {"and", "but", "so", "because", "which", "or", "like", "when", "where"}
                breaks = [i + 1 for i in range(n - 1)
                          if (words[i].endswith(",") or words[i + 1].lower().strip(",") in joins) and i + 1 >= n * 0.45]
                if n < len(words) and breaks:
                    n = breaks[-1]
                chunks.append(balance_two_lines(d, words[:n], f))
                words = words[n:]
                if words and balance_two_lines(d, words, f):
                    cur = words
                    break
        if cur:
            chunks.append(balance_two_lines(d, cur, f))
    return chunks


def caption_png(lines, role, speaker):
    """Caption band: role pill + speaker, then up to two centred lines."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    label, fill, fg = ROLE_STYLE[role]
    fs = font(600, 22)
    show_speaker = speaker and speaker not in ("Student", "Live gameplay")
    pw = text_w(d, label, font(700, 19), 2.2) + 32
    sw = (d.textlength(speaker, font=fs) + 14) if show_speaker else 0
    x = CAP_CX - (pw + sw) / 2
    pill(d, x, CAP_Y, label, fill, fg)
    if show_speaker:
        d.text((x + pw + 14, CAP_Y + 19), speaker, font=fs, fill=MUTED, anchor="lm")
    f = font(*CAP_FONT)
    y = CAP_Y + 50
    if len(lines) == 1:
        y += 26
    for line in lines:
        # soft shadow for legibility, then text
        d.text((CAP_CX + 2, y + 3), line, font=f, fill=(0, 0, 0, 160), anchor="mt")
        d.text((CAP_CX, y), line, font=f, fill=WHITE, anchor="mt")
        y += 54
    return img


def blank():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


# ---------------------------------------------------------------- cards
# Each card is a list of (png, fade_in_start_seconds) layers.

def card_title(out):
    base = background()
    d = ImageDraw.Draw(base)
    wordmark(d, (SAFE_X0, SAFE_Y0 + 10), 54, anchor="lt")
    base.save(f"{out}/title_0.png")

    l1 = blank(); d = ImageDraw.Draw(l1)
    draw_text(d, (SAFE_X0, 330), "INSIDE A LIVE TOMOCLUB SESSION", font(700, 26), TEAL_TEXT, tracking=4)
    l1.save(f"{out}/title_1.png")

    l2 = blank(); d = ImageDraw.Draw(l2)
    f = font(800, 104)
    d.text((SAFE_X0 - 4, 380), "Game-based learning,", font=f, fill=WHITE)
    d.text((SAFE_X0 - 4, 500), "live and unscripted.", font=f, fill=GOLD)
    l2.save(f"{out}/title_2.png")

    l3 = blank(); d = ImageDraw.Draw(l3)
    d.text((SAFE_X0, 660), "Two students. Two strategy games. A facilitator who asks instead of tells.", font=font(400, 38), fill=(203, 213, 225))
    d.line([SAFE_X0, 760, SAFE_X0 + 120, 760], fill=CRIMSON, width=6)
    d.text((SAFE_X0, 790), "Highlights from TAICY 2026 · Round 2 (TomoClub AI Innovation Challenge for Youth)", font=font(400, 26), fill=MUTED)
    l3.save(f"{out}/title_3.png")
    return [("title_0.png", 0.0), ("title_1.png", 0.15), ("title_2.png", 0.35), ("title_3.png", 0.8)]


def card_chapter(out, n, ch):
    base = background()
    d = ImageDraw.Draw(base)
    wordmark(d, (SAFE_X0, SAFE_Y0 + 10), 44, anchor="lt")
    base.save(f"{out}/ch{n}_0.png")
    l1 = blank(); d = ImageDraw.Draw(l1)
    d.text((SAFE_X0 - 8, 300), ch["num"], font=font(800, 240), fill=GOLD)
    d.text((SAFE_X0, 580), ch["title"], font=font(800, 110), fill=WHITE)
    l1.save(f"{out}/ch{n}_1.png")
    l2 = blank(); d = ImageDraw.Draw(l2)
    d.text((SAFE_X0, 730), ch["sub"], font=font(400, 40), fill=(203, 213, 225))
    l2.save(f"{out}/ch{n}_2.png")
    return [(f"ch{n}_0.png", 0.0), (f"ch{n}_1.png", 0.1), (f"ch{n}_2.png", 0.35)]


OUTCOMES = [
    ("Strategic thinking", "Plan, test and adapt"),
    ("Communication", "Speak up, and listen"),
    ("Collaboration", "Share roles, win together"),
    ("Resilience", "Bounce back when cornered"),
    ("Reflection", "Debrief, then level up"),
]


def card_outcomes(out):
    base = background()
    d = ImageDraw.Draw(base)
    wordmark(d, (SAFE_X0, SAFE_Y0 + 10), 44, anchor="lt")
    draw_text(d, (W // 2, 250), "THE LEARNING OUTCOME", font(700, 26), TEAL_TEXT, tracking=4, anchor="mm")
    d.text((W // 2, 330), "What your child practices, game after game", font=font(800, 72), fill=WHITE, anchor="mm")
    d.text((W // 2, 410), "Every game ends with a facilitator-led debrief, so the play turns into skills.", font=font(400, 34), fill=(203, 213, 225), anchor="mm")
    base.save(f"{out}/outcomes_0.png")
    layers = [("outcomes_0.png", 0.0)]
    cw, ch_, gap = 316, 250, 22
    x = (W - (cw * 5 + gap * 4)) // 2
    colors = [GOLD, TEAL, CRIMSON_TEXT, GOLD, TEAL]
    for i, (name, desc) in enumerate(OUTCOMES):
        l = blank(); d = ImageDraw.Draw(l)
        x0, y0 = x + i * (cw + gap), 500
        d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch_], 24, fill=(30, 41, 59, 235), outline=(255, 255, 255, 30), width=2)
        d.rounded_rectangle([x0 + 28, y0 + 34, x0 + 76, y0 + 40], 3, fill=colors[i])
        fname = font(700, 34)
        yy = y0 + 70
        for line in wrap(d, name, fname, cw - 56):
            d.text((x0 + 28, yy), line, font=fname, fill=WHITE)
            yy += 42
        fd = font(400, 25)
        dl = wrap(d, desc, fd, cw - 56)
        for k, line in enumerate(dl):
            d.text((x0 + 28, y0 + ch_ - 36 - 32 * (len(dl) - 1 - k)), line, font=fd, fill=MUTED, anchor="ls")
        l.save(f"{out}/outcomes_{i + 1}.png")
        layers.append((f"outcomes_{i + 1}.png", 0.5 + i * 0.22))
    return layers


def icon_mail(d, x, y, s, col):
    d.rounded_rectangle([x, y + s * 0.18, x + s, y + s * 0.82], 4, outline=col, width=3)
    d.line([x + 2, y + s * 0.22, x + s / 2, y + s * 0.55, x + s - 2, y + s * 0.22], fill=col, width=3, joint="curve")


def icon_phone(d, x, y, s, col):
    d.rounded_rectangle([x + s * 0.22, y, x + s * 0.78, y + s], 7, outline=col, width=3)
    d.line([x + s * 0.4, y + s * 0.84, x + s * 0.6, y + s * 0.84], fill=col, width=3)


def icon_globe(d, x, y, s, col):
    d.ellipse([x, y, x + s, y + s], outline=col, width=3)
    d.ellipse([x + s * 0.3, y, x + s * 0.7, y + s], outline=col, width=2)
    d.line([x, y + s / 2, x + s, y + s / 2], fill=col, width=2)


def qr_image(size):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2, box_size=10)
    q.add_data(QR_URL)
    q.make(fit=True)
    img = q.make_image(fill_color=NAVY, back_color=(255, 255, 255)).convert("RGBA")
    return img.resize((size, size), Image.NEAREST)


def card_end(out):
    base = background()
    d = ImageDraw.Draw(base)
    base.save(f"{out}/end_0.png")
    layers = [("end_0.png", 0.0)]

    l = blank(); d = ImageDraw.Draw(l)
    wordmark(d, (SAFE_X0, 118), 76, anchor="lt")
    d.text((SAFE_X0, 250), "Build the child", font=font(800, 92), fill=WHITE)
    d.text((SAFE_X0, 350), "AI can't replace.", font=font(800, 92), fill=GOLD)
    d.text((SAFE_X0, 478), "Live, coach-led online sessions for Grades 3–8.", font=font(400, 36), fill=(203, 213, 225))
    d.text((SAFE_X0, 526), "Team games, real debriefs, real growth.", font=font(400, 36), fill=(203, 213, 225))
    l.save(f"{out}/end_1.png"); layers.append(("end_1.png", 0.2))

    l = blank(); d = ImageDraw.Draw(l)
    bx, by, bw, bh = SAFE_X0, 610, 620, 104
    d.rounded_rectangle([bx, by + 6, bx + bw, by + bh + 6], bh // 2, fill=(150, 110, 10, 255))
    d.rounded_rectangle([bx, by, bx + bw, by + bh], bh // 2, fill=GOLD)
    fc = font(800, 42)
    tw = d.textlength(CTA, font=fc)
    tx = bx + (bw - tw - 50) / 2
    d.text((tx, by + bh / 2 + 2), CTA, font=fc, fill=NAVY, anchor="lm")
    ax, ay = tx + tw + 22, by + bh / 2 + 2
    d.line([ax, ay, ax + 28, ay], fill=NAVY, width=6)
    d.line([ax + 16, ay - 12, ax + 29, ay, ax + 16, ay + 12], fill=NAVY, width=6, joint="curve")
    icon_globe(d, bx + 4, by + bh + 42, 34, TEAL_TEXT)
    d.text((bx + 54, by + bh + 59), CTA_URL, font=font(700, 40), fill=WHITE, anchor="lm")
    d.text((SAFE_X0, 846), "Trial is free  ·  No commitment  ·  Cancel anytime", font=font(600, 28), fill=TEAL_TEXT)
    l.save(f"{out}/end_2.png"); layers.append(("end_2.png", 0.8))

    # right column: QR + contact
    l = blank(); d = ImageDraw.Draw(l)
    cx0, cy0, cw, chh = 1190, 118, 634, 720
    d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + chh], 32, fill=(30, 41, 59, 235), outline=(255, 255, 255, 30), width=2)
    qs = 300
    qx = cx0 + (cw - qs) // 2
    d.rounded_rectangle([qx - 14, cy0 + 50, qx + qs + 14, cy0 + 50 + qs + 28], 20, fill=(255, 255, 255))
    l.alpha_composite(qr_image(qs), (qx, cy0 + 64))
    d.text((cx0 + cw / 2, cy0 + 440), "Scan to book a free trial", font=font(700, 32), fill=WHITE, anchor="mm")
    d.line([cx0 + 50, cy0 + 490, cx0 + cw - 50, cy0 + 490], fill=(255, 255, 255, 36), width=2)
    draw_text(d, (cx0 + 50, cy0 + 530), "TALK TO OUR TEAM", font(700, 20), MUTED, tracking=2.6, anchor="lm")
    icon_mail(d, cx0 + 50, cy0 + 562, 36, TEAL_TEXT)
    d.text((cx0 + 104, cy0 + 580), EMAIL, font=font(600, 34), fill=WHITE, anchor="lm")
    icon_phone(d, cx0 + 50, cy0 + 622, 36, TEAL_TEXT)
    d.text((cx0 + 104, cy0 + 640), PHONE, font=font(600, 34), fill=WHITE, anchor="lm")
    l.save(f"{out}/end_3.png"); layers.append(("end_3.png", 1.3))

    l = blank(); d = ImageDraw.Draw(l)
    d.line([SAFE_X0, 918, SAFE_X1, 918], fill=(255, 255, 255, 30), width=2)
    d.text((SAFE_X0, 960), SOCIALS, font=font(400, 26), fill=MUTED, anchor="lm")
    d.text((SAFE_X1, 960), "© 2026 TomoClub", font=font(400, 24), fill=MUTED, anchor="rm")
    l.save(f"{out}/end_4.png"); layers.append(("end_4.png", 1.8))
    return layers
