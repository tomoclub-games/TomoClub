"""Drawing toolkit: brand palette, fonts, sprites and a tiny animation system (Pillow)."""
import functools
import math
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 30
FONT_DIR = os.environ.get("FONT_DIR", "fonts")
SYMBOL_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# TomoClub brand (styles.css): navy, logo teal / yellow / crimson, Outfit typeface.
C = {
    "bg0": (8, 13, 28),
    "navy": (15, 23, 42),
    "slate": (30, 41, 59),
    "slate2": (51, 65, 85),
    "line": (71, 85, 105),
    "text": (248, 250, 252),
    "muted": (148, 163, 184),
    "teal": (42, 180, 184),
    "gold": (253, 198, 45),
    "crimson": (179, 65, 88),
    "pink": (240, 128, 150),
    "violet": (167, 139, 250),
    "white": (255, 255, 255),
    "paper": (250, 250, 247),
    "ink": (15, 23, 42),
}
# Song Maker-style pitch colours (row 0 = high C ... row 7 = low C).
PITCH = [(231, 76, 60), (155, 89, 182), (52, 152, 219), (42, 180, 184),
         (46, 204, 113), (241, 196, 15), (243, 156, 18), (231, 76, 60)]


@functools.lru_cache(maxsize=None)
def F(size, weight=700):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"Outfit-{weight}.ttf"), size)


@functools.lru_cache(maxsize=None)
def SYM(size):
    return ImageFont.truetype(SYMBOL_FONT, size)


def ease(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def ease_back(p):
    p = min(1.0, max(0.0, p))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


# ---------------------------------------------------------------- sprites

def rrect(w, h, r, fill=None, outline=None, ow=0, ss=3):
    img = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], r * ss, fill=fill,
                        outline=outline, width=ow * ss)
    return img.resize((w, h), Image.LANCZOS)


def circle(d, fill=None, outline=None, ow=0, ss=3):
    img = Image.new("RGBA", (d * ss, d * ss), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([0, 0, d * ss - 1, d * ss - 1], fill=fill, outline=outline, width=ow * ss)
    return img.resize((d, d), Image.LANCZOS)


def shadowed(img, blur=22, off=(0, 14), alpha=0.5, pad=48, color=(0, 0, 0)):
    w, h = img.size
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = img.getchannel("A").point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", (w, h), rgba(color))
    sh.putalpha(a)
    out.paste(sh, (pad + off[0], pad + off[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out, pad


def _tokens(markup):
    """'plain *accent* plain' -> [(word, accent?)]"""
    out = []
    for i, part in enumerate(re.split(r"\*", markup)):
        for w in part.split(" "):
            if w:
                out.append((w, i % 2 == 1))
    return out


def text_img(markup, size, weight=700, color=C["text"], accent=C["gold"], max_w=None,
             lh=1.16, align="left", accent_weight=None, tracking=0):
    """Wrapped text sprite. '\n' breaks lines, *words* are drawn in the accent colour."""
    font = F(size, weight)
    afont = F(size, accent_weight or weight)
    space = font.getlength(" ") + tracking * 2

    def length(f, w):
        return f.getlength(w) + tracking * len(w)

    lines = []
    for para in markup.split("\n"):
        cur, cur_w = [], 0.0
        for w, acc in _tokens(para):
            ww = length(afont if acc else font, w)
            add = ww if not cur else space + ww
            if max_w and cur and cur_w + add > max_w:
                lines.append((cur, cur_w))
                cur, cur_w = [(w, acc, ww)], ww
            else:
                cur.append((w, acc, ww))
                cur_w += add
        lines.append((cur, cur_w))
    asc, desc = font.getmetrics()
    line_h = int(size * lh)
    width = int(max(lw for _, lw in lines)) + 6
    height = line_h * (len(lines) - 1) + asc + desc + 6
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, (words, lw) in enumerate(lines):
        x = {"left": 0, "center": (width - lw) / 2, "right": width - lw}[align]
        for w, acc, ww in words:
            f = afont if acc else font
            if tracking:
                cx = x
                for ch in w:
                    d.text((cx, i * line_h), ch, font=f, fill=accent if acc else color)
                    cx += f.getlength(ch) + tracking
            else:
                d.text((x, i * line_h), w, font=f, fill=accent if acc else color)
            x += ww + space
    return img


def pill(text, size=28, weight=700, fg=C["navy"], bg=C["teal"], padx=22, pady=10, outline=None):
    caps = text.upper() == text and any(ch.isalpha() for ch in text)
    t = text_img(text, size, weight, color=fg, tracking=int(size * 0.08) if caps else 0)
    w, h = t.width + 2 * padx, int(size * 1.0) + 2 * pady + 6
    img = rrect(w, h, h // 2, fill=rgba(bg) if bg else None, outline=rgba(outline) if outline else None,
                ow=3 if outline else 0)
    img.alpha_composite(t, (padx, (h - t.height) // 2 + 1))
    return img


def card(w, h, fill=C["slate"], r=28, outline=C["line"], ow=2, accent=None):
    img = rrect(w, h, r, fill=rgba(fill), outline=rgba(outline, 140) if outline else None, ow=ow)
    if accent:
        bar = rrect(w, 14, 7, fill=rgba(accent))
        top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        top.paste(bar, (0, 0))
        mask = rrect(w, h, r, fill=(255, 255, 255, 255)).getchannel("A")
        clip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        clip.paste(top, (0, 0), mask)
        img.alpha_composite(clip.crop((0, 0, w, 8)), (0, 0))
    return img


def wordmark(size):
    font = F(size, 800)
    parts = [("To", C["teal"]), ("mo", C["gold"]), ("Club", C["crimson"])]
    w = int(sum(font.getlength(p) for p, _ in parts)) + 4
    asc, desc = font.getmetrics()
    img = Image.new("RGBA", (w, asc + desc + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 0
    for p, c in parts:
        d.text((x, 0), p, font=font, fill=c)
        x += font.getlength(p)
    return img


def stamp(text, color=C["crimson"], size=44, angle=-6):
    t = text_img(text, size, 800, color=color, align="center")
    w, h = t.width + 60, t.height + 36
    img = rrect(w, h, 16, fill=rgba(C["navy"], 235), outline=rgba(color), ow=5)
    img.alpha_composite(t, (30, 18))
    return img.rotate(angle, expand=True, resample=Image.BICUBIC)


def note_block(w, h, color, r=8):
    return rrect(w, h, r, fill=rgba(color))


def paste(frame, img, x, y, op=1.0):
    if op <= 0.003:
        return
    if op >= 0.997:
        frame.paste(img, (int(x), int(y)), img)
    else:
        a = img.getchannel("A").point(lambda v: int(v * op))
        frame.paste(img, (int(x), int(y)), a)


# ---------------------------------------------------------------- animation

class El:
    """A sprite that animates in at t0 and (optionally) out at t1."""

    def __init__(self, img, x, y, t0=0.0, t1=None, dur=0.55, dy=34, dx=0, anim="rise", pad=0,
                 fade=0.35, center=False):
        if isinstance(img, tuple):
            img, pad = img
        self.img, self.pad = img, pad
        if center:
            x -= (img.width - 2 * pad) / 2
        self.x, self.y = x, y
        self.t0, self.t1, self.dur, self.dy, self.dx = t0, t1, dur, dy, dx
        self.anim, self.fade = anim, fade

    def draw(self, frame, t):
        if t < self.t0:
            return
        p = (t - self.t0) / self.dur
        e = ease(p)
        op = min(1.0, max(0.0, p * 1.6))
        if self.t1 is not None and t > self.t1:
            op *= max(0.0, 1 - (t - self.t1) / self.fade)
        if op <= 0:
            return
        img = self.img
        x, y = self.x - self.pad, self.y - self.pad
        if self.anim == "rise":
            y += self.dy * (1 - e)
            x += self.dx * (1 - e)
        elif self.anim == "pop" and p < 1:
            s = max(0.05, 0.55 + 0.45 * ease_back(p))
            nw, nh = max(1, int(img.width * s)), max(1, int(img.height * s))
            x += (img.width - nw) / 2
            y += (img.height - nh) / 2
            img = img.resize((nw, nh), Image.BILINEAR)
        paste(frame, img, x, y, op)


class Dyn:
    """Per-frame callback element: fn(frame, t, op)."""

    def __init__(self, fn, t0=0.0, t1=None, fadein=0.4, fade=0.35):
        self.fn, self.t0, self.t1, self.fadein, self.fade = fn, t0, t1, fadein, fade

    def draw(self, frame, t):
        if t < self.t0:
            return
        op = min(1.0, (t - self.t0) / self.fadein) if self.fadein else 1.0
        if self.t1 is not None and t > self.t1:
            op *= max(0.0, 1 - (t - self.t1) / self.fade)
        if op > 0:
            self.fn(frame, t, op)


# ---------------------------------------------------------------- background

def background():
    import numpy as np
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    top, bot = np.array(C["bg0"], np.float32), np.array(C["navy"], np.float32)
    g = (yy / H)[..., None]
    img = top * (1 - g) + bot * g

    def glow(cx, cy, r, col, a):
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
        k = (np.clip(1 - d, 0, 1) ** 2 * a)[..., None]
        return k * (np.array(col, np.float32) - img)

    img += glow(1700, 80, 900, C["teal"], 0.16)
    img += glow(150, 1050, 800, C["crimson"], 0.12)
    img += glow(1000, 1150, 700, C["gold"], 0.04)
    # faint Song Maker grid
    grid = ((xx % 60) < 1.2) | ((yy % 60) < 1.2)
    img[grid] = img[grid] * 0.93 + 255 * 0.07 * 0.35
    return Image.fromarray(np.clip(img, 0, 255).astype("uint8"), "RGB")


def draw_symbol(d, xy, ch, size, fill):
    d.text(xy, ch, font=SYM(size), fill=fill)


def check_icon(d_px, color=C["teal"], fg=C["navy"]):
    img = circle(d_px, fill=rgba(color))
    ss = 4
    big = Image.new("RGBA", (d_px * ss, d_px * ss), (0, 0, 0, 0))
    dd = ImageDraw.Draw(big)
    s = d_px * ss
    dd.line([(s * 0.28, s * 0.52), (s * 0.44, s * 0.68), (s * 0.74, s * 0.34)], fill=rgba(fg), width=int(s * 0.1),
            joint="curve")
    img.alpha_composite(big.resize((d_px, d_px), Image.LANCZOS))
    return img


def lock_icon(size, color):
    ss = 4
    s = size * ss
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([s * 0.18, s * 0.45, s * 0.82, s * 0.95], s * 0.08, fill=rgba(color))
    d.arc([s * 0.3, s * 0.08, s * 0.7, s * 0.72], 180, 360, fill=rgba(color), width=int(s * 0.1))
    d.line([(s * 0.3, s * 0.42), (s * 0.3, s * 0.52)], fill=rgba(color), width=int(s * 0.1))
    d.line([(s * 0.7, s * 0.42), (s * 0.7, s * 0.52)], fill=rgba(color), width=int(s * 0.1))
    return img.resize((size, size), Image.LANCZOS)


def arc_ring(size, frac, color, track=C["slate2"], width=26):
    ss = 3
    s = size * ss
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = width * ss // 2 + 2
    d.ellipse([pad, pad, s - pad, s - pad], outline=rgba(track), width=width * ss)
    if frac > 0.001:
        d.arc([pad, pad, s - pad, s - pad], -90, -90 + 360 * frac, fill=rgba(color), width=width * ss)
    return img.resize((size, size), Image.LANCZOS)


def lerp(a, b, p):
    return a + (b - a) * p


def clamp01(x):
    return max(0.0, min(1.0, x))


__all__ = [n for n in dir() if not n.startswith("_")] + ["math"]
