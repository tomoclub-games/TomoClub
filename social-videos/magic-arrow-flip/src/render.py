"""Render "The Magic Flipping Arrow" vertical short (1080x1920, 30 fps).

usage:
  python render.py VO_DIR out.mp4            # full silent video + cues.json
  python render.py VO_DIR out.mp4 --cues-only
  python render.py VO_DIR --cover cover.jpg  # thumbnail / Reels cover
  python render.py VO_DIR --srt captions.srt # closed captions for upload
  python render.py VO_DIR --stills 1.2 20.5  # PNG stills for review

The timeline is driven by the narration timings in VO_DIR/timings.json
(produced by narration.py) so visuals land on the spoken words.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
import skia

from engine import *  # noqa: F401,F403  (drawing toolkit)
from engine import W, H, FPS

VO_DIR = sys.argv[1]
TIM = json.load(open(os.path.join(VO_DIR, "timings.json")))

# ====================================================================== timeline
S = {}  # narration line -> start time (s)


def dur(line):
    return TIM[line]["dur"]


def end(line):
    return S[line] + dur(line)


def word(line, sub, nth=0):
    """Absolute start time of the nth word in `line` containing `sub`."""
    hits = [w for w in TIM[line]["words"] if sub in w[0].lower()]
    return S[line] + hits[nth][1]


S["hook"] = 0.30
S["secret"] = end("hook") + 0.40
S["materials"] = end("secret") + 0.45
S["step1"] = end("materials") + 0.60
DRAW0 = word("step1", "draw") + 0.15
DRAW_D = 1.7
S["step2"] = max(end("step1") + 0.35, DRAW0 + DRAW_D + 0.35)
CUP_IN = word("step2", "empty") - 0.1
S["step3"] = end("step2") + 0.40
POUR0 = word("step3", "pour") - 0.05
POUR_D = 2.9


def level_frac(t):
    p = prog(t, POUR0, POUR_D)
    return 1 - (1 - p) ** 2  # pour slows down as the cup fills


def level_y(t):
    return lerp(CUP_EMPTY_Y, CUP_FULL_Y, level_frac(t))


# moment the water fully covers the arrow
_arrow_top = ARROW["cy"] - ARROW["spread"] - ARROW["width"] / 2 - 4
FLIP_DONE = next(POUR0 + i / 300 * POUR_D for i in range(301) if level_y(POUR0 + i / 300 * POUR_D) <= _arrow_top)
S["whoa"] = max(end("step3") + 0.15, FLIP_DONE - 0.05)
S["spy"] = end("whoa") + 1.0
SPY_IN = word("spy", "water") - 0.15
S["light"] = end("spy") + 1.1
S["refract"] = end("light") + 0.35
S["lens"] = end("refract") + 0.9
S["flips"] = end("lens") + 0.30
S["eye"] = end("flips") + 1.1
S["cta"] = end("eye") + 0.8
END = end("cta") + 2.4
HOOK_SLIDE = word("hook", "turned") - 0.40
TRANS = 0.34

CUES = []  # sound-effect cues for audio.py


def cue(kind, t, **kw):
    CUES.append(dict(kind=kind, t=round(t, 3), **kw))


# ====================================================================== shared bits
def paper_arrow(frac=1.0):
    return lambda c: draw_paper(c, lambda cc: draw_arrow(cc, frac))


def title_block(c, t, t0, tag, tag_bg, head, tag_fg=WHITE, head_color=NAVY, head_size=74, y=270, banner=False):
    s = pop_scale(t, t0, 0.35)
    if s <= 0:
        return
    s2 = pop_scale(t, t0 + 0.08, 0.4)
    if s2 > 0:
        hy = y + 100 + (12 if banner else 0)
        with scaled(c, W / 2, hy, s2, rot=-3 if banner else 0):
            if banner:
                bw = text_w(head, head_size, 900) + 90
                bh = head_size + 56
                soft_shadow(c, W / 2 - bw / 2, hy - bh / 2, bw, bh, 26, alpha=0.25)
                rrect(c, W / 2 - bw / 2, hy - bh / 2, bw, bh, 26, rgb(GOLD))
                draw_text(c, head, W / 2, hy, head_size, 900, head_color)
            else:
                draw_text(c, head, W / 2, hy, head_size, 900, head_color, stroke=WHITE, stroke_w=12, shadow=1)
    with scaled(c, W / 2, y, s):
        pill(c, tag, W / 2, y, 40, tag_bg, tag_fg, 900)


def direction_chip(c, t, t0, txt, bg, fg=WHITE, y=1195):
    s = pop_scale(t, t0, 0.35)
    if s > 0:
        with scaled(c, W / 2, y, s):
            pill(c, txt, W / 2, y, 46, bg, fg, 900)


def room_with_arrow_and_cup(c, t, cup_x, lvl, arrow_frac=1.0, content=None, wobble=0.0):
    bg_room(c)
    behind = content or paper_arrow(arrow_frac)
    behind(c)
    if cup_x is not None:
        draw_cup(c, cup_x, lvl, behind, t=t, wobble=wobble)


# ====================================================================== scenes
def scene_hook(c, t):
    x = lerp(1400, CUP["cx"], ease_back(prog(t, HOOK_SLIDE, 0.55), 1.2))
    room_with_arrow_and_cup(c, t, x, CUP_FULL_Y)
    landed = HOOK_SLIDE + 0.45
    if t < landed:
        title_block(c, t, -1.0, "GRADE 4 SCIENCE 🔬", TEAL, "WATCH THE ARROW 👀")
        direction_chip(c, t, -1.0, "Points LEFT ⬅️", ARROW_RED)
    else:
        title_block(c, t, landed, "NO HANDS!", CRIMSON, "NOBODY TOUCHED IT! 🤯", head_size=76, banner=True)
        direction_chip(c, t, landed, "Now RIGHT ➡️", TEAL)
        sparkles(c, CUP["cx"], 800, t, landed, n=12, radius=330)


def scene_secret(c, t):
    bg_burst(c, t)
    t0 = S["secret"]
    s = pop_scale(t, t0 - 0.25, 0.5)
    bob = math.sin(t * 5) * 18
    if s > 0:
        draw_drop(c, W / 2, 800 + bob, 1.25 * s * (1 + 0.03 * math.sin(t * 10)), t)
    tq = word("secret", "secret")
    s1 = pop_scale(t, tq, 0.4)
    if s1 > 0:
        with scaled(c, W / 2, 360, s1):
            draw_text(c, "THE SECRET?", W / 2, 360, 104, 900, WHITE, stroke=NAVY, stroke_w=16, shadow=1)
    tw = word("secret", "water")
    s2 = pop_scale(t, tw, 0.45)
    if s2 > 0:
        with scaled(c, W / 2, 1120, s2, rot=-4):
            pill(c, "JUST WATER! 💧", W / 2, 1120, 88, GOLD, NAVY, 900, pad_x=50, pad_y=30)
    sparkles(c, W / 2, 800, t, tw, n=12, radius=380, color=WHITE)


MAT_CARDS = [("Paper", "paper"), ("Marker", "marker"), ("Clear cup", "cup,"), ("Water", "water")]


def scene_materials(c, t):
    c.drawRect(skia.Rect.MakeWH(W, H), paint(0, shader=lin(0, 0, 0, H, [rgb("#FFF8E6"), rgb("#FFE9B8")])))
    dot = paint(rgb(GOLD, 0.25))
    for j, y in enumerate(range(40, H, 80)):
        for x in range(40 if j % 2 else 0, W + 40, 80):
            c.drawCircle(x, y, 6, dot)
    s = pop_scale(t, S["materials"] - 0.2, 0.4)
    if s > 0:
        with scaled(c, W / 2, 330, s):
            draw_text(c, "YOU NEED:", W / 2, 330, 104, 900, NAVY, stroke=WHITE, stroke_w=14, shadow=1)
    cw, ch = 420, 330
    for i, (label, key) in enumerate(MAT_CARDS):
        tx = word("materials", key)
        k = pop_scale(t, tx - 0.08, 0.4)
        if k <= 0:
            continue
        col, row = i % 2, i // 2
        x = 100 + col * (cw + 40)
        y = 450 + row * (ch + 36)
        cx, cy = x + cw / 2, y + ch / 2
        with scaled(c, cx, cy, k, rot=(-3 if col == 0 else 3) * (1 - k)):
            card(c, x, y, cw, ch, 40)
            c.drawCircle(x + 46, y + 46, 30, paint(rgb(TEAL)))
            draw_text(c, str(i + 1), x + 46, y + 46, 38, 900, WHITE)
            draw_text(c, label, cx, y + ch - 50, 50, 800, NAVY)
            icon_y = y + 135
            if key == "paper":
                with scaled(c, cx, icon_y, 1.0, rot=-6):
                    rrect(c, cx - 80, icon_y - 100, 160, 200, 10, rgb("#F4F7FB"))
                    rrect(c, cx - 80, icon_y - 100, 160, 200, 10, rgb("#C9D6E6"), style="stroke", sw=4)
                    for yy in range(int(icon_y - 60), int(icon_y + 80), 30):
                        c.drawLine(cx - 55, yy, cx + 55, yy, paint(rgb(SKY, 0.8), "stroke", 4))
            elif key == "marker":
                draw_marker(c, cx - 110, icon_y + 70)
            elif key == "cup,":
                sc = 0.42
                c.save()
                c.translate(cx - CUP["cx"] * sc, icon_y - 855 * sc)
                c.scale(sc, sc)
                draw_cup(c, CUP["cx"], CUP_EMPTY_Y)
                c.restore()
            else:
                draw_jug(c, cx - 110, icon_y - 110, 0, 0.8, scale=0.72)
    tn = word("materials", "water") + 0.5
    k = pop_scale(t, tn, 0.4)
    if k > 0:
        with scaled(c, W / 2, 1210, k):
            pill(c, "💡 Tip: a PLASTIC cup is safest!", W / 2, 1210, 40, NAVY, WHITE, 800)


def scene_experiment(c, t):
    # --- cup position / water
    cup_x = None
    drop = 0.0
    if t >= CUP_IN:
        p = prog(t, CUP_IN, 0.55)
        drop = lerp(-1150, 0, ease_back(p, 1.1))
        cup_x = CUP["cx"]
    lvl = level_y(t)
    frac = ease_io(prog(t, DRAW0, DRAW_D))
    bg_room(c)
    behind = paper_arrow(frac)
    behind(c)
    # marker drawing the arrow
    m_in = S["step1"] - 0.1
    if t >= m_in and t < DRAW0 + DRAW_D + 0.7:
        pen = _pen_pos(frac)
        a_in = ease_out(prog(t, m_in, 0.45))
        a_out = ease_in(prog(t, DRAW0 + DRAW_D + 0.1, 0.5))
        x = pen[0] + (1 - a_in) * 500 + a_out * 600
        y = pen[1] - (1 - a_in) * 200 - a_out * 300
        draw_marker(c, x, y)
    if cup_x is not None:
        c.save()
        c.translate(0, drop)
        pouring = POUR0 <= t <= POUR0 + POUR_D
        draw_cup(c, cup_x, lvl, behind, t=t, wobble=6 if pouring else 2 * max(0, 1 - (t - POUR0 - POUR_D)))
        c.restore()
    # jug + stream
    jug_in = S["step3"] - 0.05
    if t >= jug_in and t < POUR0 + POUR_D + 1.2:
        tilt = ease_io(prog(t, POUR0 - 0.4, 0.4)) - ease_io(prog(t, POUR0 + POUR_D, 0.4))
        enter = ease_out(prog(t, jug_in, 0.5))
        leave = ease_in(prog(t, POUR0 + POUR_D + 0.35, 0.6))
        sx = CUP["cx"] + 70 + (1 - enter) * 600 + leave * 700
        sy = 588 - (1 - enter) * 350 - leave * 400
        if POUR0 <= t <= POUR0 + POUR_D + 0.15:
            k_end = prog(t, POUR0 + POUR_D - 0.05, 0.2)
            top_y = sy + 10 + k_end * (lvl - sy)
            wig = 4 * math.sin(t * 30)
            path = skia.Path()
            path.moveTo(sx + 4, top_y)
            path.quadTo(sx - 6 + wig, (top_y + lvl) / 2, sx - 4, lvl)
            c.drawPath(path, paint(rgb(WATER, 0.75), "stroke", 22))
            c.drawPath(path, paint(rgb(WHITE, 0.55), "stroke", 6))
            rng = np.random.default_rng(int(t * FPS))
            for _ in range(6):
                ang = rng.uniform(math.pi * 1.05, math.pi * 1.95)
                r = rng.uniform(10, 60)
                c.drawCircle(sx - 4 + r * math.cos(ang), lvl + r * math.sin(ang) * 0.6, rng.uniform(4, 9),
                             paint(rgb(SKY, 0.8)))
        draw_jug(c, sx, sy, -58 * tilt, 1 - 0.8 * level_frac(t), scale=0.8)
    # bubbles after pouring
    if t > POUR0 + 0.3 and cup_x is not None:
        for i in range(7):
            ph = (t * 0.6 + i * 0.37) % 1.0
            bx = CUP["cx"] - 140 + i * 45 + 10 * math.sin(t * 3 + i)
            by = lerp(CUP["bottom"] - 50, lvl + 20, ph)
            if by > lvl + 15:
                c.drawCircle(bx, by, 5 + (i % 3) * 2, paint(rgb(WHITE, 0.5 * (1 - ph)), "stroke", 3))
    # --- titles
    if t < S["step2"] - 0.15:
        title_block(c, t, S["step1"] - 0.2, "STEP 1", TEAL, "Draw an arrow ⬅️")
    elif t < S["step3"] - 0.15:
        title_block(c, t, S["step2"] - 0.15, "STEP 2", GOLD, "Add an EMPTY cup", tag_fg=NAVY)
        k = pop_scale(t, CUP_IN + 0.6, 0.35)
        if k > 0:
            with scaled(c, W / 2, 452, k):
                pill(c, "📏 Paper 10–15 cm behind the cup", W / 2, 452, 34, WHITE, NAVY, 800)
    elif t < FLIP_DONE:
        title_block(c, t, S["step3"] - 0.15, "STEP 3", CRIMSON, "Pour in water SLOWLY 💧", head_size=64)
    else:
        title_block(c, t, FLIP_DONE, "WOW!", CRIMSON, "IT FLIPPED! 🤯", head_size=96, banner=True)
        sparkles(c, CUP["cx"], 800, t, FLIP_DONE, n=14, radius=340)
    # --- direction chip
    if t >= FLIP_DONE:
        direction_chip(c, t, FLIP_DONE, "Now RIGHT ➡️", TEAL)
    elif t >= word("step2", "nothing"):
        direction_chip(c, t, word("step2", "nothing"), "Still LEFT… 🤔", ARROW_RED)
    elif t >= DRAW0 + DRAW_D:
        direction_chip(c, t, DRAW0 + DRAW_D, "Points LEFT ⬅️", ARROW_RED)


def _pen_pos(frac):
    strokes = arrow_pts(-1)
    lens = [poly_len(s) for s in strokes]
    left = sum(lens) * frac
    pen = strokes[0][0]
    for s, L in zip(strokes, lens):
        if left <= 0:
            break
        _, pen = poly_partial(s, left / L)
        left -= L
    return pen


SPY_WORD = "SPY"
_spy_size = 170
while text_w(SPY_WORD, _spy_size, 900) * 1.25 > 360:
    _spy_size -= 2


def spy_paper(c):
    def content(cc):
        cc.save()
        cc.translate(ARROW["cx"], 0)
        cc.scale(-1, 1)
        cc.translate(-ARROW["cx"], 0)
        draw_text(cc, SPY_WORD, ARROW["cx"], ARROW["cy"] - 6, _spy_size, 900, INK)
        cc.restore()
    draw_paper(c, content)


def scene_spy(c, t):
    x = None
    if t >= SPY_IN:
        x = lerp(1400, CUP["cx"], ease_back(prog(t, SPY_IN, 0.55), 1.2))
    room_with_arrow_and_cup(c, t, x, CUP_FULL_Y, content=spy_paper)
    landed = SPY_IN + 0.45
    if t < landed:
        title_block(c, t, S["spy"] - 0.2, "SPY TRICK 🕵️", NAVY, "Write it BACKWARDS", tag_fg=GOLD)
        k = pop_scale(t, word("spy", "backwards") + 0.3, 0.35)
        if k > 0:
            with scaled(c, W / 2, 452, k):
                pill(c, "✏️ Tip: write, flip the paper, trace it!", W / 2, 452, 32, WHITE, NAVY, 800)
        direction_chip(c, t, S["spy"] + 0.3, "Secret message? 🤔", INK)
    else:
        title_block(c, t, landed, "SPY TRICK 🕵️", NAVY, "DECODED! ✅", tag_fg=GOLD, head_size=96, banner=True)
        direction_chip(c, t, landed, "It says: SPY! 🕵️", TEAL)
        sparkles(c, CUP["cx"], 800, t, landed, n=14, radius=340)


# --- light bends in water ------------------------------------------------------
SURF_Y = 860
ENTRY = (560.0, SURF_Y)
INC = math.radians(50)
REF = math.asin(math.sin(INC) / 1.33)
TORCH = (ENTRY[0] - 520 * math.sin(INC), ENTRY[1] - 520 * math.cos(INC))
EXIT_BENT = (ENTRY[0] + 420 * math.sin(REF), ENTRY[1] + 420 * math.cos(REF))
EXIT_STRAIGHT = (ENTRY[0] + 300 * math.sin(INC), ENTRY[1] + 300 * math.cos(INC))


def glow_line(c, a, b, frac=1.0, color=GOLD, width=10):
    if frac <= 0:
        return
    e = (lerp(a[0], b[0], frac), lerp(a[1], b[1], frac))
    c.drawLine(*a, *e, paint(rgb(color, 0.35), "stroke", width * 3.2, blur=10))
    c.drawLine(*a, *e, paint(rgb(color), "stroke", width))
    c.drawLine(*a, *e, paint(rgb("#FFFBE6"), "stroke", width * 0.4))


def scene_light(c, t):
    bg_science(c, t)
    t0 = S["light"]
    # tank of water
    tank = skia.Rect.MakeLTRB(110, SURF_Y, 970, 1250)
    c.drawRect(tank, paint(0, shader=lin(0, SURF_Y, 0, 1250, [rgb(WATER, 0.55), rgb(WATER_D, 0.75)])))
    c.drawLine(110, SURF_Y, 970, SURF_Y, paint(rgb("#BFE6FF"), "stroke", 6))
    pill(c, "AIR", 205, 760, 36, WHITE, NAVY, 900, shadow=False, alpha=0.9)
    pill(c, "WATER", 235, 1190, 36, "#BFE6FF", NAVY, 900, shadow=False, alpha=0.95)
    # torch
    k = pop_scale(t, t0 - 0.2, 0.4)
    if k > 0:
        with scaled(c, TORCH[0], TORCH[1], k, rot=90 - math.degrees(INC)):
            c.save()
            c.translate(*TORCH)
            rrect(c, -190, -34, 160, 68, 18, rgb("#475569"))
            rrect(c, -150, -34, 18, 68, 4, rgb(GOLD))
            path = skia.Path()
            path.moveTo(-40, -34)
            path.lineTo(0, -52)
            path.lineTo(0, 52)
            path.lineTo(-40, 34)
            path.close()
            c.drawPath(path, paint(rgb("#94A3B8")))
            c.drawOval(skia.Rect.MakeLTRB(-8, -50, 8, 50), paint(rgb("#FFF6C8")))
            c.restore()
    # beam in air, then bent in water
    t_air = word("light", "travels") - 0.1
    glow_line(c, TORCH, ENTRY, ease_io(prog(t, t_air, 1.3)))
    t_bend = word("light", "bends") - 0.15
    t_ghost = t_bend + 0.7
    if t >= t_ghost:
        ga = prog(t, t_ghost, 0.4)
        e = (lerp(ENTRY[0], EXIT_STRAIGHT[0], ga), lerp(ENTRY[1], EXIT_STRAIGHT[1], ga))
        c.drawLine(*ENTRY, *e, paint(rgb(WHITE, 0.5), "stroke", 5, dash=[16, 14]))
        k2 = pop_scale(t, t_ghost + 0.3, 0.35)
        if k2 > 0:
            with scaled(c, 880, 1100, k2):
                draw_text(c, "if it didn't bend", 880, 1100, 30, 700, WHITE, alpha=0.75)
    if t >= t_bend:
        c.drawLine(ENTRY[0], SURF_Y - 150, ENTRY[0], SURF_Y + 190,
                   paint(rgb(WHITE, 0.25), "stroke", 3, dash=[10, 10]))
    glow_line(c, ENTRY, EXIT_BENT, ease_out(prog(t, t_bend, 0.55)))
    if t >= t_bend + 0.2:
        k3 = pop_scale(t, t_bend + 0.2, 0.4)
        with scaled(c, ENTRY[0] - 190, SURF_Y + 80, k3):
            pill(c, "it BENDS! ↘️", ENTRY[0] - 190, SURF_Y + 80, 36, GOLD, NAVY, 900)
    # headline
    if t < S["refract"] - 0.1:
        k = pop_scale(t, t0 - 0.1, 0.35)
        if k > 0:
            with scaled(c, W / 2, 330, k):
                draw_text(c, "How does it work? 🤔", W / 2, 330, 72, 900, WHITE, shadow=1)
        k = pop_scale(t, t_air, 0.35)
        if k > 0 and t < t_bend:
            with scaled(c, W / 2, 425, k):
                draw_text(c, "Light travels in straight lines", W / 2, 425, 42, 700, "#BFE6FF")
        k = pop_scale(t, t_bend, 0.35)
        if k > 0:
            with scaled(c, W / 2, 425, k):
                draw_text(c, "…but it BENDS going into water!", W / 2, 425, 42, 800, GOLD)
    else:
        tr = S["refract"] - 0.1
        k = pop_scale(t, tr, 0.45)
        c.drawCircle(W / 2, 340, 260, paint(0, shader=rad(W / 2, 340, 260, [rgb(GOLD, 0.35 * k), rgb(GOLD, 0)])))
        with scaled(c, W / 2, 330, k):
            draw_text(c, "REFRACTION!", W / 2, 330, 112, 900, GOLD, stroke=NAVY, stroke_w=10, shadow=1)
        k = pop_scale(t, tr + 0.25, 0.35)
        if k > 0:
            with scaled(c, W / 2, 440, k):
                draw_text(c, "= light bending 🌈", W / 2, 440, 50, 800, WHITE)
        sparkles(c, W / 2, 330, t, tr, n=12, radius=420)


# --- how the round cup flips it (top view) --------------------------------------
LX, LY, LR = 540.0, 760.0, 80.0
PAPER_LINE_Y = 480.0
N_WATER = 1.33
TIP, TAIL = (390.0, PAPER_LINE_Y), (690.0, PAPER_LINE_Y)
IMG_Y = 1139.0


def _refract(d, n, n1, n2):
    """Snell's law in vector form. d, n unit vectors; n points against d."""
    cosi = -(d[0] * n[0] + d[1] * n[1])
    r = n1 / n2
    k = 1 - r * r * (1 - cosi * cosi)
    if k < 0:
        return None
    ct = math.sqrt(k)
    return (r * d[0] + (r * cosi - ct) * n[0], r * d[1] + (r * cosi - ct) * n[1])


def _hit_circle(o, d, inside=False):
    ox, oy = o[0] - LX, o[1] - LY
    b = ox * d[0] + oy * d[1]
    cc = ox * ox + oy * oy - LR * LR
    disc = b * b - cc
    if disc < 0:
        return None
    s = -b + math.sqrt(disc) if inside else -b - math.sqrt(disc)
    return (o[0] + s * d[0], o[1] + s * d[1])


def trace(src, offset):
    """Ray from src aimed past the lens centre by `offset` px; returns polyline."""
    dx, dy = LX - src[0], LY - src[1]
    L = math.hypot(dx, dy)
    d = (dx / L, dy / L)
    perp = (-d[1], d[0])
    aim = (LX + perp[0] * offset, LY + perp[1] * offset)
    dx, dy = aim[0] - src[0], aim[1] - src[1]
    L = math.hypot(dx, dy)
    d = (dx / L, dy / L)
    p1 = _hit_circle(src, d)
    n1 = ((p1[0] - LX) / LR, (p1[1] - LY) / LR)
    d2 = _refract(d, n1, 1.0, N_WATER)
    p2 = _hit_circle(p1, d2, inside=True)
    n2 = (-(p2[0] - LX) / LR, -(p2[1] - LY) / LR)
    d3 = _refract(d2, n2, N_WATER, 1.0)
    s = (IMG_Y + 70 - p2[1]) / d3[1]
    p3 = (p2[0] + s * d3[0], p2[1] + s * d3[1])
    return [src, p1, p2, p3]


RAYS_TIP = [trace(TIP, o) for o in (-26, 0, 26)]
RAYS_TAIL = [trace(TAIL, o) for o in (-26, 0, 26)]


def _img_x(rays):
    """Where the ray bundle converges (x at IMG_Y) - the flipped image point."""
    xs = []
    for r in rays:
        a, b = r[2], r[3]
        k = (IMG_Y - a[1]) / (b[1] - a[1])
        xs.append(lerp(a[0], b[0], k))
    return sum(xs) / len(xs)


IMG_TIP_X, IMG_TAIL_X = _img_x(RAYS_TIP), _img_x(RAYS_TAIL)


def ray_bundle(c, rays, frac, color):
    for r in rays:
        pts, _ = poly_partial(r, frac)
        draw_poly(c, pts, paint(rgb(color, 0.35), "stroke", 14, blur=6))
        draw_poly(c, pts, paint(rgb(color), "stroke", 5))


def two_tone_arrow(c, x_tip, x_tail, y, alpha=1.0, width=26):
    """Arrow with a gold tip-half and teal tail-half (so you can track each side)."""
    mid = (x_tip + x_tail) / 2
    d = 1 if x_tail > x_tip else -1
    c.drawLine(mid, y, x_tail, y, paint(rgb(TEAL, alpha), "stroke", width))
    c.drawLine(x_tip + d * 10, y, mid, y, paint(rgb(GOLD, alpha), "stroke", width))
    path = skia.Path()
    path.moveTo(x_tip - d * 8, y)
    path.lineTo(x_tip + d * 62, y - 42)
    path.lineTo(x_tip + d * 62, y + 42)
    path.close()
    c.drawPath(path, paint(rgb(GOLD, alpha)))


def scene_lens(c, t):
    bg_science(c, t)
    t0 = S["lens"]
    k = pop_scale(t, t0 - 0.3, 0.35)
    if k > 0:
        with scaled(c, W / 2, 290, k):
            draw_text(c, "How the cup flips it", W / 2, 290, 70, 900, WHITE, shadow=1)
        with scaled(c, W / 2, 370, k):
            pill(c, "👆 View from ABOVE", W / 2, 370, 32, "#1E2B55", "#BFE6FF", 800, shadow=False)
    # paper + arrow (top view)
    c.drawLine(170, PAPER_LINE_Y - 26, 910, PAPER_LINE_Y - 26, paint(rgb(WHITE, 0.9), "stroke", 10))
    draw_text(c, "paper", 930, PAPER_LINE_Y - 26, 30, 700, WHITE, align="left", alpha=0.7)
    two_tone_arrow(c, TIP[0], TAIL[0], PAPER_LINE_Y)
    draw_text(c, "left", TIP[0] - 20, PAPER_LINE_Y + 56, 30, 800, GOLD, align="center")
    draw_text(c, "right", TAIL[0] + 10, PAPER_LINE_Y + 56, 30, 800, TEAL, align="center")
    # rays
    t_left = word("lens", "left") - 0.35
    t_right = word("lens", "right", 1) - 0.35
    ray_bundle(c, RAYS_TIP, ease_io(prog(t, t_left, 1.5)), GOLD)
    ray_bundle(c, RAYS_TAIL, ease_io(prog(t, t_right, 1.4)), TEAL)
    # the cup of water (circle from above)
    pulse = 1 + 0.06 * math.sin(max(0, t - t0) * 8) * (1 - prog(t, t0 + 2.4, 0.5))
    c.drawCircle(LX, LY, LR * pulse + 28, paint(0, shader=rad(LX, LY, LR + 40, [rgb(WATER, 0.45), rgb(WATER, 0)])))
    c.drawCircle(LX, LY, LR * pulse, paint(rgb(WATER, 0.55)))
    c.drawCircle(LX, LY, LR * pulse, paint(rgb("#BFE6FF"), "stroke", 6))
    c.drawCircle(LX - 26, LY - 26, 16, paint(rgb(WHITE, 0.6)))
    k = pop_scale(t, word("lens", "lens") - 0.1, 0.35)
    if k > 0:
        with scaled(c, 820, LY, k):
            pill(c, "= a LENS 🔍", 820, LY, 38, GOLD, NAVY, 900)
    k = pop_scale(t, t0 - 0.1, 0.35)
    if k > 0:
        with scaled(c, 250, LY, k):
            pill(c, "cup of water", 250, LY, 32, "#1E2B55", WHITE, 800, shadow=False)
    # crossing highlight
    k = pop_scale(t, word("lens", "crosses") + 0.2, 0.35)
    if k > 0:
        cx_, cy_ = LX, LY + LR + 120
        with scaled(c, 830, cy_ + 10, k):
            pill(c, "rays CROSS ✖️", 830, cy_ + 10, 34, CRIMSON, WHITE, 900)
    # flipped image + eye
    tf = S["flips"] - 0.1
    k = pop_scale(t, tf, 0.45)
    if k > 0:
        c.save()
        c.translate(LX, IMG_Y)
        c.scale(k, k)
        c.translate(-LX, -IMG_Y)
        two_tone_arrow(c, IMG_TIP_X, IMG_TAIL_X, IMG_Y, width=30)
        c.restore()
        with scaled(c, W / 2, IMG_Y + 95, k):
            pill(c, "What you see: FLIPPED! ↔️", W / 2, IMG_Y + 95, 40, GOLD, NAVY, 900)
        sparkles(c, LX, IMG_Y, t, tf, n=12, radius=320)
    else:
        draw_text(c, "👁️ you", W / 2, IMG_Y + 95, 44, 800, WHITE, alpha=0.85)


# --- fun fact: your eye ----------------------------------------------------------
EYE_C, EYE_R = (650.0, 830.0), 230.0
LENS_X = 470.0
TREE = (170.0, 830.0)
TREE_H = 75.0
RETINA_X = 840.0


def scene_eye(c, t):
    c.drawRect(skia.Rect.MakeWH(W, H), paint(0, shader=lin(0, 0, 0, H, [rgb("#FDECF1"), rgb("#FFF6DE")])))
    dot = paint(rgb(CRIMSON, 0.07))
    for j, y in enumerate(range(40, H, 90)):
        for x in range(45 if j % 2 else 0, W + 45, 90):
            c.drawCircle(x, y, 7, dot)
    t0 = S["eye"]
    t_brain = word("eye", "brain") - 0.1
    if t < t_brain:
        title_block(c, t, t0 - 0.2, "FUN FACT 🧠", CRIMSON, "Your eye has a lens too!", head_size=66)
    else:
        title_block(c, t, t_brain, "FUN FACT 🧠", CRIMSON, "Your BRAIN flips it back!", head_size=66)
    # eyeball (side view, looking left at the tree)
    ex, ey = EYE_C
    c.drawCircle(ex, ey + 14, EYE_R, paint(rgb(NAVY, 0.15), blur=16))
    c.drawCircle(ex, ey, EYE_R, paint(rgb(WHITE)))
    c.drawCircle(ex, ey, EYE_R, paint(rgb("#FFD6DE"), "stroke", 18))
    c.drawCircle(ex, ey, EYE_R, paint(rgb(NAVY), "stroke", 6))
    retina = skia.Path()
    retina.addArc(skia.Rect.MakeLTRB(ex - EYE_R + 16, ey - EYE_R + 16, ex + EYE_R - 16, ey + EYE_R - 16), -60, 120)
    c.drawPath(retina, paint(rgb("#F0708A"), "stroke", 14))
    rrect(c, ex + EYE_R - 12, ey - 26, 170, 52, 24, rgb("#F7B267"))
    draw_text(c, "retina", ex + EYE_R - 60, ey - EYE_R + 20, 30, 800, CRIMSON)
    # cornea / iris / lens at the front (left side)
    c.drawArc(skia.Rect.MakeLTRB(ex - EYE_R - 28, ey - 110, ex - EYE_R + 60, ey + 110), 110, 140, False,
              paint(rgb("#BFE6FF"), "stroke", 10))
    c.drawLine(LENS_X - 18, ey - 118, LENS_X - 18, ey - 42, paint(rgb(TEAL), "stroke", 22))
    c.drawLine(LENS_X - 18, ey + 42, LENS_X - 18, ey + 118, paint(rgb(TEAL), "stroke", 22))
    c.drawOval(skia.Rect.MakeLTRB(LENS_X - 30, ey - 66, LENS_X + 30, ey + 66), paint(rgb(SKY, 0.85)))
    c.drawOval(skia.Rect.MakeLTRB(LENS_X - 30, ey - 66, LENS_X + 30, ey + 66), paint(rgb(WATER_D), "stroke", 4))
    draw_text(c, "lens", LENS_X, ey + 170, 32, 800, WATER_D)
    # the tree it's looking at
    draw_text(c, "🌳", TREE[0], TREE[1], 170, 800)
    # rays through the lens centre
    t_r = word("eye", "lens") - 0.1
    k = ease_io(prog(t, t_r, 1.3))
    top = (TREE[0], TREE[1] - TREE_H)
    bot = (TREE[0], TREE[1] + TREE_H)
    for src, col in ((top, GOLD), (bot, TEAL)):
        dx, dy = LENS_X - src[0], ey - src[1]
        s = (RETINA_X - 10 - src[0]) / dx
        dst = (src[0] + s * dx, src[1] + s * dy)
        pts, _ = poly_partial([src, (LENS_X, ey), dst], k)
        draw_poly(c, pts, paint(rgb(col, 0.35), "stroke", 14, blur=6))
        draw_poly(c, pts, paint(rgb(col), "stroke", 6))
    # upside-down picture on the retina
    t_ud = word("eye", "upside") - 0.1
    k2 = pop_scale(t, t_ud, 0.4)
    if k2 > 0:
        with scaled(c, RETINA_X - 70, ey, k2, rot=180):
            draw_text(c, "🌳", RETINA_X - 70, ey, 150, 800)
        label = "Upside down! 🙃" if t < t_brain else "Brain sees it upright ✅"
        with scaled(c, W / 2, 1140, k2 if t < t_brain else pop_scale(t, t_brain, 0.4)):
            pill(c, label, W / 2, 1140, 42, NAVY if t < t_brain else TEAL, WHITE, 900)
    # brain (at the end of the optic nerve) flips it back
    k3 = pop_scale(t, t_brain, 0.45)
    if k3 > 0:
        with scaled(c, 975, 700, k3):
            draw_text(c, "🧠", 975, 700, 120, 800)
        for i, (bx, by, br) in enumerate(((945, 630, 10), (925, 598, 15))):
            if pop_scale(t, t_brain + 0.1 + i * 0.08, 0.3) > 0:
                c.drawCircle(bx, by, br, paint(rgb(WHITE)))
                c.drawCircle(bx, by, br, paint(rgb(CRIMSON), "stroke", 4))
        kb = pop_scale(t, t_brain + 0.3, 0.4)
        if kb > 0:
            with scaled(c, 850, 520, kb):
                c.drawCircle(850, 520, 70, paint(rgb(WHITE)))
                c.drawCircle(850, 520, 70, paint(rgb(CRIMSON), "stroke", 5))
                draw_text(c, "🌳", 850, 515, 80, 800)
        sparkles(c, 850, 520, t, t_brain + 0.3, n=10, radius=160)


# --- call to action --------------------------------------------------------------
def scene_cta(c, t):
    bg_burst(c, t * 0.5, TEAL, "#45C3C6")
    t0 = S["cta"]
    # logo
    k = pop_scale(t, t0 - 0.3, 0.4)
    if k > 0:
        with scaled(c, W / 2, 270, k):
            tw = text_w("TomoClub", 70, 800)
            rrect(c, W / 2 - tw / 2 - 40, 270 - 55, tw + 80, 110, 55, rgb(NAVY))
            x = W / 2 - tw / 2
            for part, col in (("To", TEAL), ("mo", GOLD), ("Club", "#E0607A")):
                x += draw_text(c, part, x, 270, 70, 800, col, align="left")
    k = pop_scale(t, t0 - 0.15, 0.4)
    if k > 0:
        with scaled(c, W / 2, 400, k):
            draw_text(c, "TRY IT AT HOME! 🏠", W / 2, 400, 86, 900, WHITE, stroke=NAVY, stroke_w=14, shadow=1)
    # mini looping demo in a card
    k = pop_scale(t, t0, 0.45)
    if k > 0:
        cx0, cy0, cw, chh = 150, 470, 780, 500
        with scaled(c, W / 2, cy0 + chh / 2, k):
            card(c, cx0, cy0, cw, chh, 40, shadow=0.3)
            c.save()
            clip = skia.Path()
            clip.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx0 + 12, cy0 + 12, cw - 24, chh - 24), 30, 30))
            c.clipPath(clip, skia.ClipOp.kIntersect, True)
            sc = (cw - 24) / 1000
            c.translate(cx0 + 12 - 40 * sc, cy0 + 12 - 520 * sc)
            c.scale(sc, sc)
            ph = (t - t0) % 3.0
            slide_in = ease_io(prog(ph, 0.3, 0.6))
            slide_out = ease_io(prog(ph, 2.2, 0.6))
            cupx = lerp(1350, CUP["cx"], slide_in) + slide_out * (-900)
            room_with_arrow_and_cup(c, t, cupx, CUP_FULL_Y)
            c.restore()
    tc = word("cta", "challenge")
    k = pop_scale(t, tc, 0.4)
    if k > 0:
        with scaled(c, W / 2, 1050, k, rot=-2):
            pill(c, "Challenge a friend! 🕵️", W / 2, 1050, 54, GOLD, NAVY, 900)
    k = pop_scale(t, tc + 0.4, 0.4)
    if k > 0:
        with scaled(c, W / 2, 1150, k):
            items = ["✅ Plastic cup", "✅ Grown-up nearby", "✅ Wipe spills"]
            ws = [text_w(s, 30, 800) + 40 for s in items]
            x = W / 2 - (sum(ws) + 20 * (len(ws) - 1)) / 2
            for s, wdt in zip(items, ws):
                pill(c, s, x + wdt / 2, 1150, 30, WHITE, NAVY, 800, pad_x=20, pad_y=12, shadow=False)
                x += wdt + 20
    tf = word("cta", "follow")
    k = pop_scale(t, tf, 0.4)
    if k > 0:
        with scaled(c, W / 2, 1245, k):
            draw_text(c, "Follow for more science magic ✨", W / 2, 1245, 50, 900, WHITE, stroke=NAVY, stroke_w=10)


SCENES = [
    (scene_hook, 0.0),
    (scene_secret, S["secret"] - 0.25),
    (scene_materials, S["materials"] - 0.3),
    (scene_experiment, S["step1"] - 0.3),
    (scene_spy, S["spy"] - 0.3),
    (scene_light, S["light"] - 0.35),
    (scene_lens, S["lens"] - 0.35),
    (scene_eye, S["eye"] - 0.35),
    (scene_cta, S["cta"] - 0.35),
]

# ====================================================================== captions
CAPTION_Y = 1395


def build_chunks():
    chunks = []
    for line, t0 in sorted(S.items(), key=lambda kv: kv[1]):
        words = [(w, t0 + a, t0 + b) for w, a, b in TIM[line]["words"]]
        cur = []
        for i, wd in enumerate(words):
            cur.append(wd)
            txt = " ".join(x[0] for x in cur)
            brk = (len(cur) >= 3 or len(txt) >= 15 or wd[0][-1] in ".,!?:"
                   or (i + 1 < len(words) and words[i + 1][1] - wd[2] > 0.25))
            if brk:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        start = ch[0][1] - 0.05
        nxt = chunks[i + 1][0][1] - 0.05 if i + 1 < len(chunks) else 1e9
        stop = min(nxt, ch[-1][2] + 0.6)
        out.append((start, stop, ch))
    return out


CHUNKS = build_chunks()


def draw_captions(c, t):
    for start, stop, ch in CHUNKS:
        if start <= t < stop:
            k = ease_back(prog(t, start, 0.14), 2.2)
            size = 70
            words = [w for w, _, _ in ch]
            widths = [text_w(w, size, 900) for w in words]
            space = size * 0.28
            total = sum(widths) + space * (len(words) - 1)
            x = W / 2 - total / 2
            with scaled(c, W / 2, CAPTION_Y, 0.85 + 0.15 * k):
                for (w, a, b), wd in zip(ch, widths):
                    active = a - 0.03 <= t
                    col = GOLD if (a - 0.03 <= t < b + 0.05) else WHITE
                    draw_text(c, w, x, CAPTION_Y, size, 900, col, align="left", stroke=NAVY, stroke_w=14,
                              alpha=1.0 if active else 0.92, shadow=1)
                    x += wd + space
            return


# ====================================================================== frame
def draw_scene(c, t, idx):
    fn, t_start = SCENES[idx]
    fn(c, max(t, t_start - 0.2))


def draw_frame(c, t):
    idx = max(i for i, (_, st) in enumerate(SCENES) if st <= t)
    # push transition in a window centred on each scene boundary b
    for j in range(1, len(SCENES)):
        b = SCENES[j][1]
        if b - TRANS / 2 <= t < b + TRANS / 2:
            p = ease_io(prog(t, b - TRANS / 2, TRANS))
            for k, off in ((j - 1, -W * p), (j, W * (1 - p))):
                c.save()
                c.translate(off, 0)
                c.clipRect(skia.Rect.MakeWH(W, H))
                draw_scene(c, t, k)
                c.restore()
            c.drawRect(skia.Rect.MakeXYWH(W * (1 - p) - 14, 0, 14, H), paint(rgb(GOLD)))
            break
    else:
        draw_scene(c, t, idx)
    draw_captions(c, t)


def build_cues():
    """Sound-effect cues. Effects are placed just before or after words (not on
    top of them) so they never mask the narration."""
    for j in range(1, len(SCENES)):
        cue("whoosh", SCENES[j][1] - TRANS / 2)
    cue("slide", HOOK_SLIDE)
    cue("sparkle", HOOK_SLIDE + 0.45)
    cue("pop", word("secret", "secret") - 0.15)
    cue("sparkle", end("secret") - 0.05)
    for _, key in MAT_CARDS:
        cue("pop", word("materials", key) - 0.15)
    cue("scribble", DRAW0, d=DRAW_D)
    cue("thud", CUP_IN + 0.35)
    cue("pour", POUR0, d=POUR_D)
    cue("sparkle", min(FLIP_DONE, S["whoa"]) - 0.3)
    cue("slide", SPY_IN)
    cue("sparkle", end("spy") + 0.05)
    cue("zap", word("light", "bends") - 0.15)
    cue("sparkle", end("refract") + 0.02)
    cue("pop", word("lens", "lens") - 0.15)
    cue("sparkle", end("flips") + 0.02)
    cue("sparkle", end("eye") + 0.02)
    cue("pop", word("cta", "challenge") - 0.15)
    cue("pop", word("cta", "follow") - 0.15)


def write_cues(path):
    build_cues()
    with open(path, "w") as f:
        json.dump(dict(end=END, lines=S, cues=CUES), f, indent=1)


def draw_cover(c):
    """Thumbnail / Reels cover: two arrows, only the one behind the water flips."""
    c.drawRect(skia.Rect.MakeWH(W, H), paint(rgb(WALL_TOP)))
    c.save()
    c.translate(0, 150)
    bg_room(c)
    def two_arrows(cc):
        draw_paper(cc, lambda k: (draw_arrow(k, cy=655), draw_arrow(k, cy=880)))
    two_arrows(c)
    draw_cup(c, CUP["cx"], 770, two_arrows)
    c.restore()
    pill(c, "GRADE 4 SCIENCE 🔬", W / 2, 230, 42, TEAL, WHITE, 900)
    draw_text(c, "The Magic", W / 2, 350, 104, 900, NAVY, stroke=WHITE, stroke_w=14, shadow=1)
    with scaled(c, W / 2, 480, 1.0, rot=-3):
        bw = text_w("FLIPPING ARROW 🤯", 92, 900) + 90
        soft_shadow(c, W / 2 - bw / 2, 480 - 74, bw, 148, 30, alpha=0.25)
        rrect(c, W / 2 - bw / 2, 480 - 74, bw, 148, 30, rgb(GOLD))
        draw_text(c, "FLIPPING ARROW 🤯", W / 2, 480, 92, 900, NAVY)
    pill(c, "Only water! 💧 Try it at home", W / 2, 1390, 50, CRIMSON, WHITE, 900)
    tw = text_w("TomoClub", 56, 800)
    rrect(c, W / 2 - tw / 2 - 32, 1520 - 44, tw + 64, 88, 44, rgb(NAVY))
    x = W / 2 - tw / 2
    for part, col in (("To", TEAL), ("mo", GOLD), ("Club", "#E0607A")):
        x += draw_text(c, part, x, 1520, 56, 800, col, align="left")


def main():
    surface = skia.Surface(W, H)
    c = surface.getCanvas()
    if "--srt" in sys.argv:
        def ts(x):
            ms = int(round(x * 1000))
            return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
        with open(sys.argv[sys.argv.index("--srt") + 1], "w") as f:
            for i, (a, b, ch) in enumerate(CHUNKS, 1):
                f.write(f"{i}\n{ts(max(0, a))} --> {ts(b)}\n{' '.join(w for w, _, _ in ch)}\n\n")
        return
    if "--cover" in sys.argv:
        c.clear(skia.ColorWHITE)
        draw_cover(c)
        img = surface.makeImageSnapshot()
        out = sys.argv[sys.argv.index("--cover") + 1]
        img.save(out, skia.kJPEG, 92)
        return
    if "--stills" in sys.argv:
        times = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:]]
        outdir = os.environ.get("STILLS_DIR", ".")
        for t in times:
            c.clear(skia.ColorWHITE)
            draw_frame(c, t)
            surface.makeImageSnapshot().save(os.path.join(outdir, f"still_{t:05.2f}.png"), skia.kPNG)
        print("timeline:", {k: round(v, 2) for k, v in S.items()}, "END", round(END, 2),
              "FLIP_DONE", round(FLIP_DONE, 2))
        return
    out = sys.argv[2]
    write_cues(os.path.join(os.path.dirname(os.path.abspath(out)), "cues.json"))
    if "--cues-only" in sys.argv:
        return
    n = int(math.ceil(END * FPS))
    ff = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        c.clear(skia.ColorWHITE)
        draw_frame(c, t)
        ff.stdin.write(surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        if i % 150 == 0:
            print(f"frame {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("done", out, round(END, 2), "s")


if __name__ == "__main__":
    main()
