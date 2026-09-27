"""Small drawing toolkit on top of skia-python for the vertical short.

Colours, easing, text (with colour-emoji fallback), shapes, and the
reusable props: paper, arrow, cup of water, marker, jug, water-drop mascot.
"""
import math
import os
from contextlib import contextmanager
from functools import lru_cache

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

# ---------------------------------------------------------------- colours
def rgb(h, a=1.0):
    h = h.lstrip("#")
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16),
                      int(round(255 * max(0.0, min(1.0, a)))))


# TomoClub brand
TEAL, GOLD, CRIMSON, NAVY, WHITE = "#2AB4B8", "#FDC62D", "#B34158", "#0F172A", "#FFFFFF"
# Scene palette
ARROW_RED = "#E5484D"
WATER = "#3FA9F5"
WATER_D = "#1E7FC8"
WOOD, WOOD_D, WOOD_L = "#F1CF9E", "#D9A86C", "#F7DDB6"
WALL_TOP, WALL_BOT = "#DDF4F5", "#FFF6DE"
INK = "#1E2A55"   # marker ink for the secret word
SKY = "#8FD3FF"


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, t0, d):
    """0..1 progress of t through [t0, t0+d]."""
    if d <= 0:
        return 1.0 if t >= t0 else 0.0
    return clamp((t - t0) / d)


def lerp(a, b, x):
    return a + (b - a) * x


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in(x):
    return x ** 3


def ease_io(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_back(x, s=1.9):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease_elastic(x):
    if x <= 0 or x >= 1:
        return clamp(x)
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def pop_scale(t, t0, d=0.35):
    """Scale for a 'pop-in' starting at t0 (0 before)."""
    return ease_back(prog(t, t0, d)) if t >= t0 else 0.0


# ---------------------------------------------------------------- paints
def paint(color, style="fill", sw=0.0, shader=None, blur=0.0, dash=None, cap="round"):
    p = skia.Paint(AntiAlias=True, Color=color)
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(sw)
        p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if shader is not None:
        p.setColor(skia.ColorBLACK)  # shader colours are modulated by paint alpha
        p.setShader(shader)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    return p


def lin(x0, y0, x1, y1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], colors, pos)


def rad(cx, cy, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, colors, pos)


def rrect(c, x, y, w, h, r, color, **kw):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, paint(color, **kw))


def soft_shadow(c, x, y, w, h, r, alpha=0.18, dy=12, blur=18):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y + dy, w, h), r, r, paint(rgb(NAVY, alpha), blur=blur))


def card(c, x, y, w, h, r=36, color=WHITE, alpha=1.0, shadow=0.16):
    soft_shadow(c, x, y, w, h, r, alpha=shadow * alpha)
    rrect(c, x, y, w, h, r, rgb(color, alpha))


@contextmanager
def scaled(c, cx, cy, s, rot=0.0):
    c.save()
    c.translate(cx, cy)
    if rot:
        c.rotate(rot)
    c.scale(s, s)
    c.translate(-cx, -cy)
    try:
        yield
    finally:
        c.restore()


@contextmanager
def faded(c, alpha):
    if alpha >= 0.999:
        yield
        return
    c.saveLayerAlpha(None, int(255 * clamp(alpha)))
    try:
        yield
    finally:
        c.restore()


# ---------------------------------------------------------------- text
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(HERE, "fonts"))
EMOJI_FONT = os.environ.get("EMOJI_FONT", "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
TF = {w: skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, f"Outfit-{w}.ttf")) for w in (500, 700, 800, 900)}
EMOJI = skia.Typeface.MakeFromFile(EMOJI_FONT)
assert all(TF.values()) and EMOJI, "fonts missing"


@lru_cache(maxsize=None)
def _font(weight, size, emoji):
    f = skia.Font(EMOJI if emoji else TF[weight], size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


@lru_cache(maxsize=4096)
def _runs(s):
    out, cur, cur_e = [], "", None
    for ch in s:
        o = ord(ch)
        e = (o >= 0x1F000 or o in (0xFE0F, 0x200D, 0x20E3)
             or TF[800].unicharToGlyph(o) == 0)
        if cur and e != cur_e:
            out.append((cur, cur_e))
            cur = ""
        cur += ch
        cur_e = e
    if cur:
        out.append((cur, cur_e))
    return tuple(out)


def _fsize(size, emoji):
    return round(size * (0.86 if emoji else 1.0), 1)


def text_w(s, size, w=800):
    return sum(_font(w, _fsize(size, e), e).measureText(r) for r, e in _runs(s))


def draw_text(c, s, x, y, size, w=800, color=NAVY, align="center", stroke=None,
              stroke_w=0.0, alpha=1.0, shadow=0.0):
    """Draw text vertically centred on y. Returns the drawn width."""
    width = text_w(s, size, w)
    x0 = x - width / 2 if align == "center" else x - width if align == "right" else x
    base = y + size * 0.35
    passes = []
    if shadow:
        passes.append(("shadow", None))
    if stroke:
        passes.append(("stroke", None))
    passes.append(("fill", None))
    for kind, _ in passes:
        cx = x0
        for run, emoji in _runs(s):
            f = _font(w, _fsize(size, emoji), emoji)
            adv = f.measureText(run)
            if kind == "shadow":
                if not emoji:
                    c.drawString(run, cx, base + size * 0.07, f,
                                 paint(rgb(NAVY, 0.28 * alpha * shadow), blur=size * 0.06))
            elif kind == "stroke":
                if not emoji:
                    c.drawString(run, cx, base, f, paint(rgb(stroke, alpha), "stroke", stroke_w))
            else:
                p = paint(rgb(color, alpha))
                if emoji:
                    p.setAlphaf(alpha)
                c.drawString(run, cx, base + (size * 0.04 if emoji else 0), f, p)
            cx += adv
    return width


def pill(c, s, x, y, size, bg, fg=WHITE, w=800, alpha=1.0, pad_x=None, pad_y=None, shadow=True):
    """Rounded 'chip' with text centred at (x, y)."""
    tw = text_w(s, size, w)
    px = pad_x if pad_x is not None else size * 0.7
    py = pad_y if pad_y is not None else size * 0.42
    bw, bh = tw + 2 * px, size + 2 * py
    if shadow:
        soft_shadow(c, x - bw / 2, y - bh / 2, bw, bh, bh / 2, alpha=0.2 * alpha, dy=8, blur=12)
    rrect(c, x - bw / 2, y - bh / 2, bw, bh, bh / 2, rgb(bg, alpha))
    draw_text(c, s, x, y, size, w, fg, alpha=alpha)
    return bw, bh


# ---------------------------------------------------------------- polyline helpers
def poly_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def poly_partial(pts, frac):
    """Points of the first `frac` (0..1) of a polyline, plus the pen position."""
    total = poly_len(pts)
    target = total * clamp(frac)
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if acc + seg >= target:
            k = (target - acc) / seg if seg else 0
            p = (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
            out.append(p)
            return out, p
        out.append(b)
        acc += seg
    return out, pts[-1]


def draw_poly(c, pts, p):
    if len(pts) < 2:
        return
    path = skia.Path()
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    c.drawPath(path, p)


# ---------------------------------------------------------------- backgrounds
TABLE_Y = 990


def bg_room(c):
    """Soft wall + wooden table used for the hands-on scenes."""
    c.drawRect(skia.Rect.MakeWH(W, TABLE_Y), paint(0, shader=lin(0, 0, 0, TABLE_Y, [rgb(WALL_TOP), rgb(WALL_BOT)])))
    dot = paint(rgb(TEAL, 0.07))
    for j, y in enumerate(range(60, TABLE_Y, 90)):
        for x in range(45 if j % 2 else 0, W + 45, 90):
            c.drawCircle(x, y, 7, dot)
    c.drawRect(skia.Rect.MakeXYWH(0, TABLE_Y, W, H - TABLE_Y),
               paint(0, shader=lin(0, TABLE_Y, 0, H, [rgb(WOOD_L), rgb(WOOD), rgb(WOOD_D)], [0, 0.45, 1])))
    grain = paint(rgb("#B9834A", 0.10), "stroke", 3)
    for i, y in enumerate(range(TABLE_Y + 40, H, 70)):
        path = skia.Path()
        path.moveTo(0, y)
        for x in range(0, W + 60, 60):
            path.lineTo(x, y + 6 * math.sin(x / 140 + i * 1.7))
        c.drawPath(path, grain)
    c.drawRect(skia.Rect.MakeXYWH(0, TABLE_Y - 3, W, 8), paint(rgb("#C9955A", 0.55)))


def bg_science(c, t):
    """Deep navy 'science mode' background with a faint grid."""
    c.drawRect(skia.Rect.MakeWH(W, H), paint(0, shader=lin(0, 0, 0, H, [rgb("#101B3D"), rgb("#0B1230")])))
    g = paint(rgb("#FFFFFF", 0.045), "stroke", 2)
    off = (t * 12) % 60
    for x in range(0, W + 60, 60):
        c.drawLine(x, 0, x, H, g)
    for y in range(-60, H + 60, 60):
        c.drawLine(0, y + off, W, y + off, g)
    c.drawCircle(W / 2, 760, 700, paint(0, shader=rad(W / 2, 760, 700, [rgb(TEAL, 0.16), rgb(TEAL, 0)])))


def bg_burst(c, t, c1=TEAL, c2="#5FD0D3"):
    c.drawRect(skia.Rect.MakeWH(W, H), paint(rgb(c1)))
    c.save()
    c.translate(W / 2, 800)
    c.rotate(t * 12)
    ray = paint(rgb(c2, 0.55))
    for i in range(16):
        path = skia.Path()
        path.moveTo(0, 0)
        a0, a1 = math.radians(i * 22.5), math.radians(i * 22.5 + 11)
        path.lineTo(1800 * math.cos(a0), 1800 * math.sin(a0))
        path.lineTo(1800 * math.cos(a1), 1800 * math.sin(a1))
        path.close()
        c.drawPath(path, ray)
    c.restore()
    c.drawRect(skia.Rect.MakeWH(W, H), paint(0, shader=rad(W / 2, 800, 1100, [rgb(WHITE, 0.0), rgb(NAVY, 0.25)])))


# ---------------------------------------------------------------- props
PAPER = dict(x=190, y=500, w=700, h=490)
ARROW = dict(cx=540, cy=800, half=150, head=92, spread=70, width=34)
CUP = dict(cx=540, top=600, bottom=1110, w=400, ry=24)
CUP_FULL_Y, CUP_EMPTY_Y = 665, CUP["bottom"] - 26


def draw_paper(c, content=None, alpha=1.0):
    x, y, w, h = PAPER["x"], PAPER["y"], PAPER["w"], PAPER["h"]
    soft_shadow(c, x, y, w, h, 14, alpha=0.18 * alpha, dy=10, blur=16)
    rrect(c, x, y, w, h, 14, rgb(WHITE, alpha))
    # faint ruled lines so it reads as paper
    ln = paint(rgb(SKY, 0.25 * alpha), "stroke", 2)
    for yy in range(y + 70, y + h - 20, 56):
        c.drawLine(x + 24, yy, x + w - 24, yy, ln)
    # tape at the top corners
    for tx, rot in ((x + 40, -18), (x + w - 40, 18)):
        with scaled(c, tx, y + 4, 1.0, rot):
            rrect(c, tx - 55, y - 16, 110, 40, 6, rgb("#FFE08A", 0.85 * alpha))
    if content:
        content(c)


def arrow_pts(direction=-1, cy=None):
    """Hand-drawn arrow as 3 strokes. direction=-1 points left."""
    cx, half, head, spread = ARROW["cx"], ARROW["half"], ARROW["head"], ARROW["spread"]
    cy = ARROW["cy"] if cy is None else cy
    tip = (cx + direction * half, cy)
    tail = (cx - direction * half, cy)
    back = tip[0] - direction * head
    return [tail, tip], [tip, (back, cy - spread)], [tip, (back, cy + spread)]


def draw_arrow(c, frac=1.0, direction=-1, color=ARROW_RED, alpha=1.0, cy=None):
    """Draw the arrow; frac animates it being drawn. Returns pen position."""
    strokes = arrow_pts(direction, cy)
    lens = [poly_len(s) for s in strokes]
    total = sum(lens)
    left = total * clamp(frac)
    pen = strokes[0][0]
    p = paint(rgb(color, alpha), "stroke", ARROW["width"])
    for s, L in zip(strokes, lens):
        if left <= 0:
            break
        pts, pen = poly_partial(s, left / L)
        draw_poly(c, pts, p)
        left -= L
    return pen


def draw_marker(c, x, y, alpha=1.0):
    """Felt-tip marker whose tip sits at (x, y)."""
    with faded(c, alpha):
        c.save()
        c.translate(x, y)
        c.rotate(-35)
        soft_shadow(c, 8, -24, 240, 48, 20, alpha=0.2, dy=14, blur=12)
        path = skia.Path()
        path.moveTo(0, 0)
        path.lineTo(26, -12)
        path.lineTo(26, 12)
        path.close()
        c.drawPath(path, paint(rgb(ARROW_RED)))
        rrect(c, 22, -18, 40, 36, 8, rgb("#D9DEE8"))
        rrect(c, 56, -24, 190, 48, 20, rgb(WHITE))
        rrect(c, 56, -24, 190, 48, 20, rgb(NAVY), style="stroke", sw=4)
        rrect(c, 170, -24, 76, 48, 20, rgb(ARROW_RED))
        rrect(c, 90, -10, 60, 8, 4, rgb(ARROW_RED, 0.6))
        c.restore()


def cup_paths(cx, level_y, top=None, bottom=None, w=None, ry=None):
    top = CUP["top"] if top is None else top
    bottom = CUP["bottom"] if bottom is None else bottom
    w = CUP["w"] if w is None else w
    ry = CUP["ry"] if ry is None else ry
    x0, x1 = cx - w / 2, cx + w / 2
    body = skia.Path()
    body.moveTo(x0, top)
    body.lineTo(x0, bottom)
    body.arcTo(skia.Rect.MakeLTRB(x0, bottom - ry, x1, bottom + ry), 180, -180, False)
    body.lineTo(x1, top)
    body.arcTo(skia.Rect.MakeLTRB(x0, top - ry, x1, top + ry), 0, -180, False)
    body.close()
    water = None
    if level_y < bottom - 4:
        water = skia.Path()
        water.moveTo(x0 + 3, level_y)
        water.lineTo(x0 + 3, bottom)
        water.arcTo(skia.Rect.MakeLTRB(x0 + 3, bottom - ry, x1 - 3, bottom + ry), 180, -180, False)
        water.lineTo(x1 - 3, level_y)
        water.arcTo(skia.Rect.MakeLTRB(x0 + 3, level_y - ry, x1 - 3, level_y + ry), 0, -180, False)
        water.close()
    return body, water


def draw_cup(c, cx, level_y, behind=None, mag=1.25, t=0.0, wobble=0.0):
    """Clear cylindrical cup. `behind(c)` redraws what is behind the cup so it
    can be shown mirrored (and a little magnified) through the water."""
    top, bottom, w, ry = CUP["top"], CUP["bottom"], CUP["w"], CUP["ry"]
    x0, x1 = cx - w / 2, cx + w / 2
    body, water = cup_paths(cx, level_y)
    # shadow on the table
    c.drawOval(skia.Rect.MakeLTRB(x0 - 10, bottom - 10, x1 + 30, bottom + 40), paint(rgb(NAVY, 0.20), blur=14))
    # glass tint
    c.drawPath(body, paint(rgb(WHITE, 0.10)))
    if water is not None:
        # what you see through the water: the scene behind, flipped left<->right
        if behind is not None:
            c.save()
            c.clipPath(water, skia.ClipOp.kIntersect, True)
            c.translate(cx, 0)
            c.scale(-mag, 1)
            c.translate(-cx, 0)
            behind(c)
            c.restore()
        # cylinder shading: darker/bluer at the edges
        c.drawPath(water, paint(0, shader=lin(x0, 0, x1, 0,
                   [rgb(WATER_D, 0.55), rgb(WATER, 0.16), rgb(WATER, 0.10), rgb(WATER, 0.16), rgb(WATER_D, 0.55)],
                   [0, 0.22, 0.5, 0.78, 1])))
        # water surface
        wob = wobble * math.sin(t * 9)
        surf = skia.Rect.MakeLTRB(x0 + 4, level_y - ry + wob, x1 - 4, level_y + ry - wob)
        c.drawOval(surf, paint(rgb("#BFE6FF", 0.55)))
        c.drawOval(surf, paint(rgb(WHITE, 0.8), "stroke", 3))
    # glass base
    base = skia.Path()
    base.moveTo(x0, bottom - 34)
    base.arcTo(skia.Rect.MakeLTRB(x0, bottom - 34 - ry, x1, bottom - 34 + ry), 180, -180, False)
    base.lineTo(x1, bottom)
    base.arcTo(skia.Rect.MakeLTRB(x0, bottom - ry, x1, bottom + ry), 0, 180, False)
    base.close()
    c.drawPath(base, paint(rgb("#E6F6FF", 0.55)))
    # highlights
    rrect(c, x0 + 26, top + 50, 16, bottom - top - 120, 8, rgb(WHITE, 0.55))
    rrect(c, x0 + 54, top + 70, 7, bottom - top - 170, 4, rgb(WHITE, 0.4))
    rrect(c, x1 - 40, top + 60, 10, bottom - top - 140, 5, rgb(WHITE, 0.3))
    # outline + rim
    c.drawPath(body, paint(rgb("#9DD7F2", 0.9), "stroke", 7))
    c.drawPath(body, paint(rgb(WHITE, 0.95), "stroke", 3))
    c.drawOval(skia.Rect.MakeLTRB(x0, top - ry, x1, top + ry), paint(rgb(WHITE, 0.95), "stroke", 5))


def draw_jug(c, x, y, rot, water_frac=1.0, scale=1.0):
    """Pitcher with its spout tip at local (0, 0); body hangs to the right."""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(scale, scale)
    body = skia.Path()
    body.moveTo(0, 0)
    body.lineTo(40, 20)
    body.lineTo(40, 250)
    body.quadTo(40, 290, 80, 290)
    body.lineTo(200, 290)
    body.quadTo(240, 290, 240, 250)
    body.lineTo(240, 10)
    body.lineTo(26, 10)
    body.close()
    soft_shadow(c, 40, 10, 200, 280, 30, alpha=0.18, dy=14, blur=14)
    c.drawPath(body, paint(rgb("#F4FBFF", 0.92)))
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    wy = lerp(290, 60, clamp(water_frac))
    c.drawRect(skia.Rect.MakeLTRB(0, wy, 260, 300), paint(rgb(WATER, 0.55)))
    c.restore()
    c.drawPath(body, paint(rgb("#7CC6EA"), "stroke", 7))
    handle = skia.Path()
    handle.moveTo(240, 60)
    handle.cubicTo(330, 60, 330, 220, 240, 220)
    c.drawPath(handle, paint(rgb("#7CC6EA"), "stroke", 22))
    rrect(c, 60, 40, 14, 200, 7, rgb(WHITE, 0.7))
    c.restore()


def draw_drop(c, cx, cy, s=1.0, t=0.0, face=True):
    """Friendly water-drop mascot."""
    c.save()
    c.translate(cx, cy)
    c.scale(s, s)
    path = skia.Path()
    path.moveTo(0, -170)
    path.cubicTo(40, -100, 120, -20, 120, 50)
    path.cubicTo(120, 120, 66, 170, 0, 170)
    path.cubicTo(-66, 170, -120, 120, -120, 50)
    path.cubicTo(-120, -20, -40, -100, 0, -170)
    path.close()
    c.drawOval(skia.Rect.MakeLTRB(-100, 175, 100, 205), paint(rgb(NAVY, 0.18), blur=10))
    c.drawPath(path, paint(0, shader=lin(-120, -170, 120, 170, [rgb("#8FDBFF"), rgb(WATER), rgb(WATER_D)])))
    c.drawPath(path, paint(rgb(WHITE, 0.9), "stroke", 6))
    hl = skia.Path()
    hl.moveTo(-70, 30)
    hl.cubicTo(-72, -10, -50, -50, -30, -80)
    c.drawPath(hl, paint(rgb(WHITE, 0.75), "stroke", 16))
    if face:
        blink = 1.0 if (t % 2.6) > 0.12 else 0.15
        for ex in (-40, 40):
            c.drawOval(skia.Rect.MakeLTRB(ex - 16, 40 - 22 * blink, ex + 16, 40 + 22 * blink), paint(rgb(NAVY)))
            c.drawCircle(ex + 5, 32, 6 * blink, paint(rgb(WHITE)))
        smile = skia.Path()
        smile.moveTo(-34, 92)
        smile.quadTo(0, 128, 34, 92)
        c.drawPath(smile, paint(rgb(NAVY), "stroke", 9))
        for bx in (-78, 78):
            c.drawOval(skia.Rect.MakeLTRB(bx - 18, 78, bx + 18, 96), paint(rgb("#FF8FA3", 0.55)))
    c.restore()


def sparkles(c, cx, cy, t, t0, n=10, radius=260, color=GOLD, dur=0.9, seed=1):
    """Burst of star sparkles starting at t0."""
    k = prog(t, t0, dur)
    if k <= 0 or k >= 1:
        return
    a = 1 - k
    for i in range(n):
        ang = (i / n) * math.tau + seed
        r = radius * ease_out(k) * (0.7 + 0.3 * ((i * 7 + seed) % 3) / 2)
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        s = 22 * (1 - k * 0.6) * (1.2 if i % 2 else 0.8)
        star(c, x, y, s, rgb(color if i % 3 else WHITE, a))


def star(c, x, y, s, color):
    path = skia.Path()
    for i in range(8):
        r = s if i % 2 == 0 else s * 0.38
        ang = i * math.pi / 4 - math.pi / 2
        px, py = x + r * math.cos(ang), y + r * math.sin(ang)
        path.moveTo(px, py) if i == 0 else path.lineTo(px, py)
    path.close()
    c.drawPath(path, paint(color))


def starburst(c, cx, cy, r, color, alpha=1.0, spikes=14, rot=0.0):
    path = skia.Path()
    for i in range(spikes * 2):
        rr = r if i % 2 == 0 else r * 0.78
        ang = i * math.pi / spikes + math.radians(rot)
        px, py = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        path.moveTo(px, py) if i == 0 else path.lineTo(px, py)
    path.close()
    c.drawPath(path, paint(rgb(color, alpha)))
