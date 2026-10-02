"""All Things Classroom design tokens and components, following the ATC Brand Design System.

Forest leads, Teal connects, Yellow sparks, Leaf Green whispers. Flat only: no gradients,
glows, shadows or pill shapes. Manrope for headings, DM Sans for body and labels.
The A+T+C monogram has no vector master yet, so only the typographic lockup is used.
"""
from PIL import Image, ImageDraw

from engine import circle, rgba, rrect, text_img

FOREST = (31, 95, 63)        # #1F5F3F
TEAL = (35, 177, 186)        # #23B1BA
YELLOW = (246, 201, 69)      # #F6C945
LEAF = (93, 178, 90)         # #5DB25A
IVORY = (247, 243, 234)      # #F7F3EA
MIST = (232, 244, 247)       # #E8F4F7
WHITE = (255, 255, 255)
NIGHT = (22, 63, 44)         # #163F2C forest-night
TEAL_DEEP = (21, 121, 127)   # #15797F
INK = (26, 43, 36)           # #1A2B24
SLATE = (74, 90, 82)         # #4A5A52
BORDER = (220, 230, 225)     # #DCE6E1

BG = {"ivory": IVORY, "mist": MIST, "white": WHITE, "night": NIGHT, "forest": FOREST}
DARK = {"night", "forest"}

# Song Maker-style rows (0 = high C ... 7 = low C) in brand colours. C, E, G = Forest, Teal, Yellow.
NOTE = [FOREST, TEAL_DEEP, LEAF, YELLOW, LEAF, TEAL, TEAL_DEEP, FOREST]


def is_dark(bg):
    return bg in DARK


def heading(text, size, dark=False, max_w=None, align="left", accent=None, lh=1.08):
    """Manrope 800. Forest on light, White on dark. Accent: Teal (large) on light, Yellow on dark."""
    return text_img(text, size, 800, "Manrope", WHITE if dark else FOREST,
                    accent or (YELLOW if dark else TEAL), max_w, lh=lh, align=align)


def body(text, size, dark=False, max_w=None, weight=500, align="left", accent=None, color=None, lh=1.32):
    """DM Sans. Slate on light, Ivory on dark. Accent: Teal-deep on light, Yellow on dark."""
    return text_img(text, size, weight, "DMSans", color or (IVORY if dark else SLATE),
                    accent or (YELLOW if dark else TEAL_DEEP), max_w, lh=lh, align=align, accent_weight=700)


def eyebrow(text, dark=False, size=26):
    """Section intro: short rule (Teal on light, Yellow on dark) above an uppercase DM Sans label."""
    rule = rrect(64, 6, 3, fill=rgba(YELLOW if dark else TEAL))
    t = text_img(text.upper(), size, 600, "DMSans", TEAL if dark else TEAL_DEEP, tracking=round(size * 0.08))
    img = Image.new("RGBA", (max(64, t.width), 22 + t.height), (0, 0, 0, 0))
    img.alpha_composite(rule, (0, 0))
    img.alpha_composite(t, (0, 20))
    return img


def tag(text, kind="forest", size=28, padx=22, pady=12, weight=600):
    fills = {"forest": (FOREST, WHITE, None), "yellow": (YELLOW, FOREST, None), "teal": (TEAL_DEEP, WHITE, None),
             "white": (WHITE, FOREST, BORDER), "outline": (None, FOREST, FOREST),
             "outline_dark": (None, IVORY, IVORY), "night": (NIGHT, WHITE, None)}
    fill, fg, line = fills[kind]
    caps = text.upper() == text and any(c.isalpha() for c in text)
    t = text_img(text, size, weight, "DMSans", fg, tracking=round(size * 0.06) if caps else 0)
    w, h = t.width + 2 * padx, int(size * 1.2) + 2 * pady
    img = rrect(w, h, 12, fill=rgba(fill) if fill else None, outline=rgba(line) if line else None,
                ow=2 if line else 0)
    img.alpha_composite(t, (padx, (h - t.height) // 2 + 1))
    return img


def button(text, dark=False, size=32):
    """Primary: Forest fill + White text. On dark sections: Yellow fill + Forest text. 8px-style radius."""
    return tag(text, "yellow" if dark else "forest", size=size, padx=34, pady=18, weight=600)


def card(w, h, kind="white", r=22):
    if kind == "white":
        return rrect(w, h, r, fill=rgba(WHITE), outline=rgba(BORDER), ow=2)
    if kind == "forest":
        return rrect(w, h, r + 4, fill=rgba(FOREST))
    if kind == "night":
        img = rrect(w, h, r, fill=rgba(NIGHT))
        ImageDraw.Draw(img).rectangle([r, 0, w - r, 3], fill=rgba(TEAL))
        return img
    if kind == "mist":
        return rrect(w, h, r, fill=rgba(MIST), outline=rgba(BORDER), ow=2)
    raise ValueError(kind)


def lockup(size, dark=False, tagline=True, align="center"):
    """Stacked typographic lockup: All Things / CLASSROOM / LEARN. CREATE. EXPLORE."""
    top = text_img("All Things", size, 800, "Manrope", WHITE if dark else FOREST)
    mid = text_img("CLASSROOM", size, 800, "Manrope", TEAL, tracking=round(size * 0.03))
    parts = [top, mid]
    if tagline:
        parts.append(text_img("LEARN. CREATE. EXPLORE.", max(14, round(size * 0.3)), 600, "DMSans",
                              WHITE if dark else FOREST, tracking=round(size * 0.3 * 0.2)))
    gap = round(size * 0.08)
    w = max(p.width for p in parts)
    h = sum(p.height for p in parts) + gap * (len(parts) - 1) - round(size * 0.12)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i, p in enumerate(parts):
        x = {"center": (w - p.width) // 2, "left": 0, "right": w - p.width}[align]
        img.alpha_composite(p, (x, y))
        y += p.height + gap - (round(size * 0.12) if i == 0 else 0)
    return img


def watermark(dark=False, size=30):
    return lockup(size, dark, tagline=False, align="left")


def progress(n, dark=False, w=56, gap=12):
    img = Image.new("RGBA", (5 * w + 4 * gap, 8), (0, 0, 0, 0))
    for i in range(5):
        if i < n - 1:
            col = rgba(TEAL if dark else FOREST)
        elif i == n - 1:
            col = rgba(YELLOW if dark else TEAL)
        else:
            col = (255, 255, 255, 60) if dark else rgba(BORDER)
        img.alpha_composite(rrect(w, 8, 4, fill=col), (i * (w + gap), 0))
    return img


def check_icon(d, fill=TEAL_DEEP, fg=WHITE):
    img = circle(d, fill=rgba(fill))
    ss = 4
    s = d * ss
    big = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(big).line([(s * 0.28, s * 0.52), (s * 0.44, s * 0.68), (s * 0.74, s * 0.34)], fill=rgba(fg),
                             width=int(s * 0.1), joint="curve")
    img.alpha_composite(big.resize((d, d), Image.LANCZOS))
    return img


def line_icon(kind, size, color):
    """Simple line icons, rounded joins (no clip-art)."""
    ss = 4
    s = size * ss
    w = max(2, int(s * 0.07))
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = rgba(color)
    if kind == "lock":
        d.rounded_rectangle([s * 0.2, s * 0.46, s * 0.8, s * 0.92], s * 0.08, outline=c, width=w)
        d.arc([s * 0.32, s * 0.1, s * 0.68, s * 0.7], 180, 360, fill=c, width=w)
        d.line([(s * 0.32, s * 0.4), (s * 0.32, s * 0.48)], fill=c, width=w)
        d.line([(s * 0.68, s * 0.4), (s * 0.68, s * 0.48)], fill=c, width=w)
    elif kind == "billboard":
        d.rounded_rectangle([s * 0.08, s * 0.14, s * 0.92, s * 0.62], s * 0.05, outline=c, width=w)
        d.line([(s * 0.3, s * 0.62), (s * 0.3, s * 0.92)], fill=c, width=w)
        d.line([(s * 0.7, s * 0.62), (s * 0.7, s * 0.92)], fill=c, width=w)
        for k in range(2):
            d.line([(s * 0.22, s * (0.3 + k * 0.15)), (s * (0.78 - k * 0.2), s * (0.3 + k * 0.15))], fill=c, width=w)
    elif kind == "phone":
        d.rounded_rectangle([s * 0.28, s * 0.06, s * 0.72, s * 0.94], s * 0.08, outline=c, width=w)
        d.line([(s * 0.44, s * 0.82), (s * 0.56, s * 0.82)], fill=c, width=w)
    elif kind == "swap":
        d.line([(s * 0.12, s * 0.36), (s * 0.84, s * 0.36)], fill=c, width=w)
        d.line([(s * 0.66, s * 0.2), (s * 0.84, s * 0.36), (s * 0.66, s * 0.52)], fill=c, width=w, joint="curve")
        d.line([(s * 0.88, s * 0.66), (s * 0.16, s * 0.66)], fill=c, width=w)
        d.line([(s * 0.34, s * 0.5), (s * 0.16, s * 0.66), (s * 0.34, s * 0.82)], fill=c, width=w, joint="curve")
    return img.resize((size, size), Image.LANCZOS)


def bg_image(kind, w, h):
    return Image.new("RGB", (w, h), BG[kind])
