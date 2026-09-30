"""Frame renderer for the ATC lava-lamp video.

usage: python3 render.py h|v [--preview t1,t2,...] [--out file]
Streams raw frames into ffmpeg (video only; audio muxed separately).
"""
import math
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import timeline as TL

FF = './ffmpeg'
FMT = sys.argv[1]
W, H = (1920, 1080) if FMT == 'h' else (1080, 1920)
FPS = 30
PREV = __import__('os').environ.get('PREV', 'prev')
SRC_FPS = 25
SW, SH = 960, 720

GREEN = (24, 94, 58)
DKGREEN = (10, 48, 28)
TEAL = (20, 176, 196)
YELLOW = (247, 187, 64)
LIME = (94, 166, 60)
PINK = (226, 38, 104)
WHITE = (255, 255, 255)

rng = np.random.default_rng(3)

# ------------------------------------------------------------------ fonts / text
_fonts = {}


def font(weight, size):
    k = (weight, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(f'fonts/Poppins-{weight}.ttf', size)
    return _fonts[k]


EMOJI = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
_emoji_cache = {}


def emoji_img(s, h):
    k = (s, h)
    if k not in _emoji_cache:
        im = Image.new('RGBA', (220, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), s, font=EMOJI, embedded_color=True)
        im = im.crop(im.getbbox())
        _emoji_cache[k] = im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)
    return _emoji_cache[k]


TOKEN = re.compile(r'\*([^*]+)\*|\{([^}]+)\}|~([^~]+)~|([^*{~]+)')


def parse(markup):
    out = []
    for m in TOKEN.finditer(markup):
        hl, em, sub, plain = m.groups()
        if hl is not None:
            # allow subscripts inside highlights
            for m2 in re.finditer(r'~([^~]+)~|([^~]+)', hl):
                if m2.group(1):
                    out.append(('hs', m2.group(1)))
                else:
                    out.append(('h', m2.group(2)))
        elif em is not None:
            out.append(('e', em))
        elif sub is not None:
            out.append(('s', sub))
        else:
            out.append(('n', plain))
    return out


def text_line(markup, size, weight='Black', fill=WHITE, hl=YELLOW, stroke=None, stroke_fill=DKGREEN):
    f = font(weight, size)
    fs = font(weight, int(size * 0.6))
    sw = int(size * 0.085) if stroke is None else stroke
    asc, desc = f.getmetrics()
    pieces = []
    x = 0.0
    for kind, s in parse(markup):
        if kind == 'e':
            em = emoji_img(s, int(size * 0.95))
            x += size * 0.06
            pieces.append((kind, em, x))
            x += em.width + size * 0.06
        elif kind in ('s', 'hs'):
            pieces.append((kind, s, x))
            x += fs.getlength(s)
        else:
            pieces.append((kind, s, x))
            x += f.getlength(s)
    pad = sw + 4
    img = Image.new('RGBA', (int(x + 2 * pad), asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base = pad + asc
    for rnd in ('stroke', 'fill'):
        for kind, s, px in pieces:
            if kind == 'e':
                if rnd == 'fill':
                    img.alpha_composite(s, (int(px + pad), int(base - size * 0.38 - s.height / 2)))
                continue
            ff = fs if kind in ('s', 'hs') else f
            yoff = size * 0.12 if kind in ('s', 'hs') else 0
            col = hl if kind in ('h', 'hs') else fill
            if rnd == 'stroke' and sw > 0:
                d.text((px + pad, base + yoff), s, font=ff, fill=stroke_fill, stroke_width=sw,
                       stroke_fill=stroke_fill, anchor='ls')
            elif rnd == 'fill':
                d.text((px + pad, base + yoff), s, font=ff, fill=col, anchor='ls')
    bb = img.getbbox()
    return img.crop(bb) if bb else img


def stack(imgs, align='c', gap=0):
    w = max(i.width for i in imgs)
    h = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    y = 0
    for i in imgs:
        x = 0 if align == 'l' else (w - i.width) // 2
        out.alpha_composite(i, (x, y))
        y += i.height + gap
    return out


def shadow(img, radius, offset, opacity=0.6):
    pad = radius * 3 + abs(offset)
    out = Image.new('RGBA', (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    a = img.getchannel('A').point(lambda v: int(v * opacity))
    sh = Image.new('RGBA', img.size, (0, 0, 0, 255))
    sh.putalpha(a)
    out.alpha_composite(sh, (pad, pad + offset))
    out = out.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(img, (pad, pad))
    return out


def fit(img, maxw):
    if maxw and img.width > maxw:
        img = img.resize((maxw, round(img.height * maxw / img.width)), Image.LANCZOS)
    return img


def rounded(size, radius, fill):
    im = Image.new('RGBA', size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=fill)
    return im


COLORS = {'teal': (TEAL, WHITE, YELLOW), 'green': (GREEN, WHITE, YELLOW), 'yellow': (YELLOW, DKGREEN, GREEN),
          'pink': (PINK, WHITE, YELLOW), 'white': (WHITE, GREEN, TEAL)}


def chip(markup, size, color='teal', weight='ExtraBold'):
    bg, fg, hl = COLORS[color]
    t = text_line(markup, size, weight=weight, fill=fg, hl=hl, stroke=0)
    px, py = int(size * 0.62), int(size * 0.38)
    c = rounded((t.width + 2 * px, t.height + 2 * py), (t.height + 2 * py) // 2, bg + (255,))
    c.alpha_composite(t, (px, py))
    return shadow(c, int(size * 0.18), int(size * 0.1), 0.45)


# ------------------------------------------------------------------ logo assets
def load_logo():
    src = Image.open('logo_src.png').convert('RGB')
    a = np.asarray(src).astype(np.float32)
    alpha = np.clip((255 - a).max(axis=2) / 255 * 1.08, 0, 1)
    col = np.where(alpha[..., None] > 1e-3, (a - 255 * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3), 0)
    rgba = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    full = Image.fromarray(rgba, 'RGBA').crop((200, 320, 1720, 1712))
    mark = Image.fromarray(rgba, 'RGBA').crop((210, 330, 1710, 962))
    card_src = src.crop((150, 270, 1770, 1760))
    return full, mark, card_src


LOGO_FULL, LOGO_MARK, LOGO_CARD_SRC = load_logo()


def logo_card(size):
    im = LOGO_CARD_SRC.resize((size, round(size * LOGO_CARD_SRC.height / LOGO_CARD_SRC.width)), Image.LANCZOS)
    card = rounded((im.width, im.height), int(size * 0.08), (255, 255, 255, 255))
    mask = card.getchannel('A')
    card.paste(im, (0, 0), mask)
    border = rounded((im.width + 16, im.height + 16), int(size * 0.08) + 8, YELLOW + (255,))
    border.alpha_composite(card, (8, 8))
    return shadow(border, 22, 14, 0.55)


def watermark():
    h = 64 if FMT == 'h' else 70
    m = LOGO_MARK.resize((round(LOGO_MARK.width * h / LOGO_MARK.height), h), Image.LANCZOS)
    px, py = 18, 12
    pill = rounded((m.width + 2 * px, h + 2 * py), 20, (255, 255, 255, 235))
    pill.alpha_composite(m, (px, py))
    return shadow(pill, 8, 4, 0.35)


WM = watermark()


# ------------------------------------------------------------------ elements
def ease_out_back(u, s=1.9):
    u = min(max(u, 0), 1) - 1
    return 1 + (s + 1) * u ** 3 + s * u ** 2


def ease_out_cubic(u):
    u = min(max(u, 0), 1)
    return 1 - (1 - u) ** 3


class El:
    def __init__(self, img, t0, t1, x, y, anchor='c', anim='pop', delay=0.0, src_anchor=None):
        self.img, self.t0, self.t1 = img, t0 + delay, t1
        self.x, self.y, self.anchor, self.anim = x, y, anchor, anim
        self.src_anchor = src_anchor

    def draw(self, frame, t, cam=None):
        if not (self.t0 <= t < self.t1):
            return
        lt = t - self.t0
        rem = self.t1 - t
        s, a, dx, dy = 1.0, 1.0, 0.0, 0.0
        if self.anim == 'pop':
            u = lt / 0.3
            s = 0.3 + 0.7 * ease_out_back(u)
            a = min(1, lt / 0.08)
        elif self.anim == 'slam':
            u = ease_out_cubic(lt / 0.16)
            s = 1.9 - 0.9 * u
            a = min(1, lt / 0.06)
            if lt > 0.16:
                k = math.exp(-(lt - 0.16) / 0.08)
                dx, dy = 10 * k * math.sin(lt * 90), 8 * k * math.cos(lt * 77)
        elif self.anim == 'slide':
            u = ease_out_cubic(lt / 0.28)
            dy = (1 - u) * 60
            a = min(1, lt / 0.15)
        elif self.anim == 'settle':
            s = 1.08 - 0.08 * ease_out_cubic(lt / 0.6)
        if rem < 0.1 and self.anim != 'settle':
            a *= rem / 0.1
            s *= 0.94 + 0.06 * rem / 0.1
        img = self.img
        if abs(s - 1) > 1e-3:
            img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.BILINEAR)
        if a < 0.999:
            img = img.copy()
            img.putalpha(img.getchannel('A').point(lambda v: int(v * a)))
        x, y = self.x, self.y
        if self.src_anchor is not None and cam is not None:
            x, y = cam(*self.src_anchor)
            y -= img.height / 2 - 6
        if self.anchor == 'l':
            px = x - (img.width - self.img.width) / 2
        else:
            px = x - img.width / 2
        py = y - img.height / 2
        frame.paste(img, (int(px + dx), int(py + dy)), img)


def card(title, body, size, width):
    tl = text_line(title, size, weight='Black', fill=WHITE, hl=YELLOW, stroke=0)
    tl = fit(tl, width - int(size * 1.2))
    bf = font('SemiBold', int(size * 0.7))
    words, lines, cur = body.split(), [], ''
    maxw = width - int(size * 1.2)
    for w_ in words:
        cand = (cur + ' ' + w_).strip()
        if bf.getlength(cand) > maxw and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = cand
    lines.append(cur)
    lh = int(size * 0.7 * 1.32)
    padx, pady = int(size * 0.6), int(size * 0.45)
    h = pady * 2 + tl.height + int(size * 0.3) + lh * len(lines)
    c = rounded((width, h), int(size * 0.45), DKGREEN + (238,))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, int(size * 0.22), h - 1], radius=int(size * 0.11), fill=TEAL + (255,))
    c.alpha_composite(tl, (padx, pady))
    y = pady + tl.height + int(size * 0.3)
    for ln in lines:
        d.text((padx, y), ln, font=bf, fill=(235, 245, 240))
        y += lh
    return shadow(c, 18, 10, 0.5)


def label(text, size, color):
    c = chip(text, size, color=color, weight='Black')
    # pointer triangle underneath
    bg = COLORS[color][0]
    tri = Image.new('RGBA', (c.width, c.height + int(size * 0.35)), (0, 0, 0, 0))
    tri.alpha_composite(c, (0, 0))
    d = ImageDraw.Draw(tri)
    cx = c.width // 2
    top = c.height - int(size * 0.55)
    d.polygon([(cx - size * 0.3, top), (cx + size * 0.3, top), (cx, top + size * 0.55)], fill=bg + (255,))
    return tri


def item_chip(num, text, size):
    badge_d = int(size * 1.5)
    badge = Image.new('RGBA', (badge_d, badge_d), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse([0, 0, badge_d - 1, badge_d - 1], fill=YELLOW + (255,), outline=WHITE + (255,), width=int(size * 0.08))
    bd.text((badge_d / 2, badge_d / 2), str(num), font=font('Black', int(size * 0.85)), fill=DKGREEN, anchor='mm')
    t = text_line(text, size, weight='Black', fill=WHITE, stroke=0)
    px = int(size * 0.55)
    pill_h = int(size * 1.3)
    pill = rounded((t.width + 2 * px + badge_d // 2, pill_h), pill_h // 2, TEAL + (255,))
    pill.alpha_composite(t, (px + badge_d // 2, (pill_h - t.height) // 2))
    out = Image.new('RGBA', (pill.width + badge_d // 2, badge_d), (0, 0, 0, 0))
    out.alpha_composite(pill, (badge_d // 2, (badge_d - pill_h) // 2))
    out.alpha_composite(badge, (0, 0))
    cnt = text_line(f'{num}/6', int(size * 0.42), weight='Bold', fill=WHITE, stroke=0)
    out2 = stack([out, cnt], gap=8)
    return shadow(out2, 14, 8, 0.5)


def step_pill(num, size):
    t = text_line(f'STEP {num}', size, weight='Black', fill=DKGREEN, stroke=0)
    px, py = int(size * 0.6), int(size * 0.3)
    c = rounded((t.width + 2 * px, t.height + 2 * py), int(size * 0.3), YELLOW + (255,))
    c.alpha_composite(t, (px, py))
    c = c.rotate(3, resample=Image.BICUBIC, expand=True)
    return shadow(c, 12, 8, 0.5)


def build_elements():
    els, specials = [], []
    for e in TL.T:
        k = e['kind']
        size = e.get('size', {}).get(FMT)
        pos = e.get('pos', {}).get(FMT)
        anchor = pos[2] if pos and len(pos) > 2 else 'c'
        if k in ('hype', 'count'):
            weight = 'BlackItalic' if e.get('italic') else 'Black'
            align = e.get('align', {}).get(FMT, 'c')
            if k == 'count':
                lines = [text_line(m, int(size * mult), weight=weight, fill=YELLOW, hl=YELLOW,
                                   stroke=int(size * 0.06)) for m, mult in e['lines'][FMT]]
            else:
                lines = [text_line(m, int(size * mult), weight=weight) for m, mult in e['lines'][FMT]]
            img = stack(lines, align=align, gap=int(size * -0.02))
            img = fit(img, e['maxw'][FMT])
            img = shadow(img, int(size * 0.07), int(size * 0.05), 0.65)
            x, y = pos[0], pos[1]
            els.append(El(img, e['t0'], e['t1'], x, y, anchor, e['anim'], e.get('delay', 0)))
        elif k == 'chip':
            img = chip(e['text'], size, e['color'])
            els.append(El(img, e['t0'], e['t1'], pos[0], pos[1], anchor, e['anim']))
        elif k == 'item':
            img = item_chip(e['num'], e['text'], size)
            els.append(El(img, e['t0'], e['t1'], pos[0], pos[1], 'c', e['anim']))
        elif k == 'step':
            img = step_pill(e['num'], size)
            els.append(El(img, e['t0'], e['t1'], pos[0], pos[1], anchor, e['anim']))
        elif k == 'logocard':
            img = logo_card(size)
            els.append(El(img, e['t0'], e['t1'], pos[0], pos[1], 'c', e['anim']))
        elif k == 'card':
            img = card(e['title'], e['body'], size, e['width'][FMT])
            els.append(El(img, e['t0'], e['t1'], pos[0], pos[1] , 'c', e['anim']))
        elif k == 'label':
            img = label(e['text'], size, e['color'])
            els.append(El(img, e['t0'], e['t1'], 0, 0, 'c', e['anim'], src_anchor=e['anchor_src']))  # tip-anchored
        elif k == 'co2':
            specials.append(e)
    return els, specials


# CO2 bubble sprites
def co2_sprite(d):
    im = Image.new('RGBA', (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([2, 2, d - 3, d - 3], fill=(20, 176, 196, 110), outline=(255, 255, 255, 245), width=max(3, d // 18))
    dr.ellipse([d * 0.22, d * 0.18, d * 0.38, d * 0.32], fill=(255, 255, 255, 200))
    t = text_line('CO~2~', int(d * 0.3), weight='Black', fill=WHITE, stroke=max(2, d // 30))
    im.alpha_composite(t, ((d - t.width) // 2, (d - t.height) // 2 + d // 20))
    return im


CO2 = [co2_sprite(d) for d in (110, 130, 150, 175)]


def draw_co2(frame, t, e, cam):
    if not (e['t0'] <= t < e['t1']):
        return
    x0, y0, x1, y1 = e['region_src']
    lt = t - e['t0']
    for i in range(7):
        period = 1.6 + 0.3 * (i % 3)
        ph = (lt / period + i * 0.37) % 1.0
        if lt < i * 0.12:
            continue
        sx = x0 + (x1 - x0) * ((i * 0.618) % 1.0) + 12 * math.sin(lt * 3 + i)
        sy = y1 - (y1 - y0) * ph
        X, Y = cam(sx, sy)
        spr = CO2[i % 4]
        sc = (W / 1920 if FMT == 'h' else 1.0) * (0.8 + 0.4 * ph)
        spr = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
        a = min(1, ph * 6, (1 - ph) * 5, (e['t1'] - t) / 0.15)
        if a < 1:
            spr = spr.copy()
            spr.putalpha(spr.getchannel('A').point(lambda v: int(v * max(a, 0))))
        frame.paste(spr, (int(X - spr.width / 2), int(Y - spr.height / 2)), spr)


# ------------------------------------------------------------------ video
def load_clip(src, dur):
    cmd = [FF, '-v', 'error', '-ss', f'{src:.3f}', '-i', 'source.mp4', '-t', f'{dur + 0.3:.3f}',
           '-vf', 'crop=960:720:160:0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, SH, SW, 3)


def grade(a, kind):
    x = a.astype(np.float32) / 255
    lum = x @ np.array([0.299, 0.587, 0.114], np.float32)
    sat, con = (1.22, 1.08) if kind == 'day' else (1.35, 1.12)
    x = lum[..., None] + (x - lum[..., None]) * sat
    x = np.clip(0.5 + (x - 0.5) * con, 0, 1)
    if kind == 'day':
        x[..., 0] *= 1.02
        x[..., 2] *= 0.97
    else:
        lum2 = x @ np.array([0.299, 0.587, 0.114], np.float32)
        bright = (np.clip((lum2 - 0.5) / 0.5, 0, 1) ** 1.5)[..., None] * x
        bi = Image.fromarray((bright * 255).astype(np.uint8)).resize((SW // 3, SH // 3), Image.BILINEAR)
        bi = bi.filter(ImageFilter.GaussianBlur(9)).resize((SW, SH), Image.BILINEAR)
        bloom = np.asarray(bi).astype(np.float32) / 255
        x = 1 - (1 - np.clip(x, 0, 1)) * (1 - 0.75 * bloom)
    return Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))


def make_vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.414
    v = 1 - 0.38 * np.clip((r - 0.45) / 0.55, 0, 1) ** 1.6
    v = (v * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([v, v, v]))


VIG = make_vignette()


def make_gradient(c0, c1):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = np.clip((xx / W + yy / H) / 2, 0, 1)[..., None]
    g = np.array(c0, np.float32) * (1 - u) + np.array(c1, np.float32) * u
    return Image.fromarray(g.astype(np.uint8))


BRAND_GRAD = make_gradient(GREEN, TEAL)
KICKS = [TL.bt(b, k) for b in range(17, 25) for k in range(4)]


class Camera:
    def __init__(self, shot, t):
        u = (t - shot['t0']) / (shot['t1'] - shot['t0'])
        z0, z1 = shot['z']
        z = z0 + (z1 - z0) * (u * u * (3 - 2 * u) * 0.5 + u * 0.5)
        if shot.get('punch'):
            for kt in KICKS:
                if 0 <= t - kt < 0.3:
                    z *= 1 + 0.045 * math.exp(-(t - kt) / 0.09)
        fx, fy = shot['f']
        for st, sd, amp in TL.SHAKES:
            if 0 <= t - st < sd:
                k = (1 - (t - st) / sd) ** 2 * amp * (SW / W)
                fx += k * math.sin((t - st) * 85)
                fy += k * math.cos((t - st) * 71)
        if FMT == 'h':
            cw = SW / z
            ch = cw * 9 / 16
        else:
            ch = SH / z
            cw = ch * 9 / 16
        x0 = min(max(fx - cw / 2, 0), SW - cw)
        y0 = min(max(fy - ch / 2, 0), SH - ch)
        self.box = (x0, y0, x0 + cw, y0 + ch)

    def __call__(self, sx, sy):
        x0, y0, x1, y1 = self.box
        return (sx - x0) / (x1 - x0) * W, (sy - y0) / (y1 - y0) * H


class ShotPlayer:
    def __init__(self):
        self.cur = None
        self.frames = None
        self.cache = {}

    def frame(self, shot, t):
        if self.cur is not shot:
            self.cur = shot
            self.cache = {}
            dur = (shot['t1'] - shot['t0']) * shot.get('speed', 1.0)
            self.frames = load_clip(shot['src'], dur)
        idx = int((t - shot['t0']) * shot.get('speed', 1.0) * SRC_FPS + 1e-6)
        idx = min(idx, len(self.frames) - 1)
        if idx not in self.cache:
            self.cache[idx] = grade(self.frames[idx], shot['grade'])
        cam = Camera(shot, t)
        img = self.cache[idx].resize((W, H), Image.LANCZOS, box=cam.box)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=55, threshold=2))
        if shot.get('blur'):
            img = img.filter(ImageFilter.GaussianBlur(shot['blur']))
        if shot.get('tint'):
            img = Image.blend(img, BRAND_GRAD, shot['tint'])
        if shot.get('dim'):
            img = Image.eval(img, lambda v, d=shot['dim']: int(v * d))
        img = ImageChops.multiply(img, VIG)
        return img, cam


# ------------------------------------------------------------------ end card
END_BG = None


def make_halo():
    halo = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(halo)
    if FMT == 'h':
        d.ellipse([W / 2 - 520, 60, W / 2 + 520, 1060], fill=(255, 255, 255, 235))
    else:
        d.ellipse([20, 300, W - 20, 1560], fill=(255, 255, 255, 235))
    return halo.filter(ImageFilter.GaussianBlur(60))


END_HALO = make_halo()
BUBBLES = [dict(x=rng.random(), r=rng.uniform(14, 60) * (W / 1920 if FMT == 'h' else 1.1), sp=rng.uniform(0.12, 0.32),
                ph=rng.random(), c=[TEAL, YELLOW, LIME, GREEN][i % 4], a=int(rng.uniform(70, 150)))
           for i in range(26)]


def endcard(t, t0):
    global END_BG
    if END_BG is None:
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        c0 = np.array([255, 255, 255], np.float32)
        c1 = np.array([222, 245, 248], np.float32)
        END_BG = Image.fromarray(np.broadcast_to(c0 * (1 - yy) + c1 * yy, (H, W, 3)).astype(np.uint8))
    lt = t - t0
    frame = END_BG.copy().convert('RGBA')
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for b in BUBBLES:
        y = H + b['r'] - ((b['ph'] + lt * b['sp']) % 1.0) * (H + 2 * b['r'])
        x = b['x'] * W + 18 * math.sin(lt * 2 + b['ph'] * 6)
        d.ellipse([x - b['r'], y - b['r'], x + b['r'], y + b['r']], fill=b['c'] + (b['a'],))
    frame.alpha_composite(layer)
    frame.alpha_composite(END_HALO)
    frame = frame.convert('RGB')
    # logo pop
    lw = 700 if FMT == 'h' else 900
    s = 0.2 + 0.8 * ease_out_back(lt / 0.45, 1.6)
    logo = LOGO_FULL.resize((max(1, int(lw * s)), max(1, int(lw * s * LOGO_FULL.height / LOGO_FULL.width))), Image.LANCZOS)
    cy = 450 if FMT == 'h' else 800
    frame.paste(logo, (int(W / 2 - logo.width / 2), int(cy - logo.height / 2)), logo)
    return frame


END_TEXT = None


def endcard_text(frame, t, t0):
    global END_TEXT
    if END_TEXT is None:
        if FMT == 'h':
            img = text_line('Follow for more experiments! {🔬}', 64, weight='ExtraBold', fill=GREEN, hl=TEAL, stroke=0)
        else:
            img = stack([text_line('Follow for more', 70, weight='ExtraBold', fill=GREEN, stroke=0),
                         text_line('*experiments!* {🔬}', 70, weight='ExtraBold', fill=GREEN, hl=TEAL, stroke=0)])
        END_TEXT = El(img, t0 + TL.B * 2, TL.END + 1, W / 2, 960 if FMT == 'h' else 1400, 'c', 'slide')
    END_TEXT.draw(frame, t)


# ------------------------------------------------------------------ main loop
def shot_at(t):
    for s in TL.SHOTS:
        if s['t0'] <= t < s['t1']:
            return s
    return TL.SHOTS[-1]


def render_frame(t, player, els, specials):
    shot = shot_at(t)
    cam = None
    if shot.get('black'):
        frame = Image.new('RGB', (W, H), (0, 0, 0))
    elif shot.get('endcard'):
        frame = endcard(t, shot['t0'])
    else:
        frame, cam = player.frame(shot, t)
    # flashes
    for ft, fd, fa in TL.FLASHES:
        if 0 <= t - ft < fd:
            a = fa * (1 - (t - ft) / fd) ** 1.5
            frame = Image.blend(frame, Image.new('RGB', (W, H), WHITE), a)
    for e in specials:
        if e['kind'] == 'co2' and cam is not None:
            draw_co2(frame, t, e, cam)
    for el in els:
        el.draw(frame, t, cam)
    if shot.get('endcard'):
        endcard_text(frame, t, shot['t0'])
    w0, w1 = TL.WATERMARK
    if w0 <= t < w1:
        a = min(1, (t - w0) / 0.3, (w1 - t) / 0.2)
        wm = WM
        if a < 1:
            wm = WM.copy()
            wm.putalpha(WM.getchannel('A').point(lambda v: int(v * a)))
        if FMT == 'h':
            frame.paste(wm, (W - wm.width - 24, 18), wm)
        else:
            frame.paste(wm, (W - wm.width - 24, 140), wm)
    return frame


def main():
    args = sys.argv[2:]
    els, specials = build_elements()
    player = ShotPlayer()
    if args and args[0] == '--preview':
        times = [float(x) for x in args[1].split(',')]
        for t in times:
            p = ShotPlayer()
            render_frame(t, p, els, specials).save(f'{PREV}/{FMT}_{t:06.2f}.jpg', quality=88)
        return
    out = args[1] if len(args) > 1 and args[0] == '--out' else f'video_{FMT}.mp4'
    nframes = int(TL.END * FPS)
    enc = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(nframes):
        t = i / FPS
        f = render_frame(t, player, els, specials)
        enc.stdin.write(f.tobytes())
        if i % 150 == 0:
            print(FMT, i, '/', nframes, flush=True)
    enc.stdin.close()
    enc.wait()
    print('done', out)


if __name__ == '__main__':
    main()
