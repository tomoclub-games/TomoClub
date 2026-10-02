"""All Things Classroom: "What Note Comes Next?" YouTube cut (16:9, 1920x1080).

  python long.py tts       <kokoro.onnx> <voices.bin> <workdir>
  python long.py audio     <session.mp4> <workdir>
  python long.py preview   <session.mp4> <workdir> <scene_id> <t> [<t> ...]
  python long.py scenes    <session.mp4> <workdir> [scene_id ...]
  python long.py final     <session.mp4> <workdir> <out.mp4>
  python long.py captions  <workdir> <out.srt>
  python long.py thumbnail <out.jpg>
  python long.py chapters  <workdir>

Audience: parents (ATC primary ICP). Voice: Varchas's register, but "we" for ATC since the
narrator is a synthetic voice. Spelling: British/Indian. No em dashes anywhere.
"""
import functools
import multiprocessing
import os
import re
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import atc_theme as T
from atc_theme import (BORDER, FOREST, INK, IVORY, LEAF, MIST, NOTE, SLATE, TEAL, TEAL_DEEP, WHITE, YELLOW, body,
                       button, card, check_icon, eyebrow, heading, line_icon, lockup, progress, tag, watermark)
from engine import (FPS, ClipPlayer, Cues, Dyn, El, add, arc_ring, build, circle, clamp01, ease, final_encode, midi,
                    mix_soundtrack, paste, pluck, render_scene_file, rgba, rrect, still, text_img, tts, wipe)

W, H = 1920, 1080
LX, RX, RW = 120, 1000, 800
CLIP_W, CLIP_H = 1536, 864
CLIP_X, CLIP_Y = (W - CLIP_W) // 2, 170
TITLE = "What Note Comes Next? 5 AI Habits to Try With Your Child"

CLIPS = {"clipA": [(28.4, 41.4)], "clipB": [(48.25, 59.4), (86.3, 99.6)]}
CLIP_CAPTIONS = [
    (35.0, 36.0, "Nice."), (36.0, 38.0, "I like the gap in between where it plays"),
    (38.0, 40.8, "and gives something to anticipate as well."), (40.8, 41.3, "Well done."),
    (48.7, 50.0, "Wow, wow. I love this."), (50.0, 54.0, "Yeah, that's how you experiment."),
    (54.0, 56.5, "That's how you experiment. Yes, I love it."), (56.5, 58.0, "Let's see how it would sound."),
    (86.5, 89.0, "I love the pattern in which you have coloured,"),
    (89.0, 91.0, "shows that you have gone for some pattern."),
    (91.0, 94.8, "This is like pressing all the keys on the keyboard together, so that's nice."),
    (94.8, 96.9, "Yeah, lovely."), (97.0, 98.4, "Like the experimentation."), (98.7, 99.6, "Wonderful team."),
]
SONG = {"clipA": [(28.4, 35.0)], "clipB": [(58.0, 59.4)]}
# Spoken form for the TTS -> written form for captions.
CAPTION_FIXES = {"Tomo Club": "TomoClub", "thirteen and up": "13 and up", "thirty seconds": "30 seconds",
                 "Class three": "Class 3", "Ten minutes": "10 minutes", "this or that": "this-or-that"}

SCENES = [
    {"id": "hook", "bg": "ivory", "lead": 0.4, "tail": 0.4, "items": [
        ("vo", "h1", "Quick one. Listen.", 0.2),
        ("pause", 3.9),
        ("vo", "h2", "What note comes next?", 0.8),
        ("vo", "h3", "Take a moment. Commit to an answer.", 1.0),
        ("vo", "h4", "You just did what AI does all day. It doesn't know the answer. It predicts it. "
                     "Sneaky, isn't it?", 0.5),
        ("vo", "h5", "With AI set to start from Class three in India this school year, parents keep asking us "
                     "one thing: what does my child actually need to know about it?", 0.4),
        ("vo", "h6", "Here are five habits to try at home. A phone. A curious kid. Ten minutes.", 0.3),
    ]},
    {"id": "title", "bg": "forest", "lead": 0.0, "tail": 0.0, "items": [("pause", 3.8)]},
    {"id": "rules", "bg": "mist", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "g1", "First, the ground rules.", 0.3),
        ("vo", "g2", "Most AI chat tools are built for ages thirteen and up. With younger kids, you hold the phone "
                     "and you type. They do the thinking.", 0.4),
        ("vo", "g3", "And play the billboard game together. If you wouldn't put it on a billboard outside school, "
                     "don't type it in. No full names, no addresses, no photos.", 0.3),
    ]},
    {"id": "m1_intro", "bg": "ivory", "lead": 0.5, "tail": 0.5, "items": [
        ("vo", "m1a", "One. Guess the next note.", 0.4),
        ("vo", "m1b", "This is a real class Varchas ran with Tomo Club, where kids built their own songs in "
                      "Chrome Music Lab's Song Maker. Listen to what he notices.", 0.2),
    ]},
    {"id": "clipA", "bg": "night", "lead": 0.0, "tail": 0.0, "items": [("clip", "clipA")]},
    {"id": "m1_body", "bg": "ivory", "lead": 0.4, "tail": 0.6, "items": [
        ("vo", "m1c", "Something to anticipate. That's the whole trick. An AI writes one small piece at a time, "
                      "always picking the most likely next one.", 0.4),
        ("vo", "m1d", "Try it at home. Open Song Maker together - it's free, in the browser - build three bars, "
                      "and let your child guess the fourth. Then swap.", 0.4),
        ("vo", "m1e", "AI goes for the safe note every time. Notice how often your child doesn't.", 0.3),
    ]},
    {"id": "m2", "bg": "night", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "m2a", "Two. Play it twice.", 0.4),
        ("vo", "m2b", "Musicians replay a tricky bit to check it holds up. Ask an AI a question, then open a "
                      "brand-new chat and ask it again.", 0.4),
        ("vo", "m2c", "If a name, a number or a date changes, it was guessing. Give your child a word for that: "
                      "a rumour, until you check it.", 0.3),
    ]},
    {"id": "m3", "bg": "mist", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "m3a", "Three. Flip the key.", 0.4),
        ("vo", "m3b", "Take a song from a major key to a minor key, and the whole mood changes. Questions work "
                      "the same way.", 0.4),
        ("vo", "m3c", "Ask: why is homework good for kids? Then, in a new chat: why is homework bad for kids?",
         0.4),
        ("vo", "m3d", "If it happily agrees both times, it's following your lead. Neutral questions get better "
                      "answers, like: what are the pros and cons?", 0.3),
    ]},
    {"id": "m4", "bg": "night", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "m4a", "Four. Find the sheet music.", 0.4),
        ("vo", "m4b", "Before your child repeats an AI fact - in a project, in class, at the dinner table - "
                      "find the receipt.", 0.4),
        ("vo", "m4c", "A real book or a site you trust, and the exact line that backs it up. No receipt? "
                      "Don't repeat it.", 0.3),
    ]},
    {"id": "m5", "bg": "ivory", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "m5a", "Five. Play it by ear.", 0.4),
        ("vo", "m5b", "A musician who can only play while reading the sheet hasn't learned the song yet.", 0.4),
        ("vo", "m5c", "So after AI helps with homework, close the tab and ask your child to explain it out loud "
                      "in thirty seconds.", 0.4),
        ("vo", "m5d", "Wherever they get stuck is the part they still need to learn.", 0.3),
    ]},
    {"id": "exp_intro", "bg": "night", "lead": 0.4, "tail": 0.3, "items": [
        ("vo", "e1", "Well, the kids in this class didn't aim for perfect. They experimented.", 0.2),
    ]},
    {"id": "clipB", "bg": "night", "lead": 0.0, "tail": 0.0, "items": [("clip", "clipB")]},
    {"id": "exp_outro", "bg": "ivory", "lead": 0.4, "tail": 0.6, "items": [
        ("vo", "e2", "That's the habit worth building. Treat AI like an instrument your child is learning, and "
                     "keep testing it.", 0.3),
    ]},
    {"id": "challenge", "bg": "mist", "lead": 0.6, "tail": 1.0, "items": [
        ("vo", "c1", "Now, your turn. Can your child make an AI flip?", 0.4),
        ("vo", "c2", "Pick a this or that together, like cats or dogs, or pizza or dosa.", 0.4),
        ("vo", "c3", "Ask an AI why the first one is better. Then open a brand-new chat, and ask why the second "
                     "one is better.", 0.4),
        ("vo", "c4", "Did it flip to agree both times, or hold its ground? Tell us in the comments: flipped or "
                     "held, and what your child said when they saw it.", 0.4),
        ("vo", "c5", "Just keep your child's name and school out of it.", 0.3),
    ]},
    {"id": "recap", "bg": "ivory", "lead": 0.4, "tail": 0.8, "items": [
        ("vo", "r0", "Quick recap.", 0.25), ("vo", "r1", "Guess the next note.", 0.2),
        ("vo", "r2", "Play it twice.", 0.2), ("vo", "r3", "Flip the key.", 0.2),
        ("vo", "r4", "Find the sheet music.", 0.2), ("vo", "r5", "And play it by ear.", 0.3),
    ]},
    {"id": "cta", "bg": "forest", "lead": 0.5, "tail": 1.4, "items": [
        ("vo", "a1", "If you'd like your child to learn this properly, that's what AI Labs at All Things "
                     "Classroom is for.", 0.4),
        ("vo", "a2", "Live online classes with a real teacher, the same one every week, built around making "
                     "things. Monthly, no lock-ins.", 0.4),
        ("vo", "a3", "Tap the link in the description, tell us about your child, tick AI Labs, and our team "
                     "will email you.", 0.3),
    ]},
    {"id": "outro", "bg": "forest", "lead": 0.4, "tail": 7.0, "items": [
        ("vo", "o1", "Oh, and one more thing. This voice was made with AI. Now you know how to question it.", 0.4),
        ("vo", "o2", "See you in the comments.", 0.0),
    ]},
]


def fix(text):
    for k, v in CAPTION_FIXES.items():
        text = text.replace(k, v)
    return text


def timeline(work):
    return build(work, SCENES, CLIPS)


# ---------------------------------------------------------------- shared layout

def header(n, title, dark):
    return [El(eyebrow(f"Habit {n} of 5", dark), LX, 104, 0.05),
            El(text_img(f"0{n}", 170, 800, "Manrope", YELLOW if dark else TEAL), LX - 8, 150, 0.1),
            El(heading(title, 84, dark, lh=1.04), LX, 372, 0.15)]


def chrome(n, dark):
    wm = watermark(dark)
    return [El(wm, W - 120 - wm.width, 104, 0.0, dy=0), El(progress(n, dark), LX, 1010, 0.0, dy=0)]


def principle(markup, dark, t0, t1=None):
    return El(body(markup, 40, dark, max_w=790, weight=500), LX, 612, t0, t1)


def try_card(markup, dark, t0, label="Try it at home"):
    c = card(800, 170, "forest" if dark else "white")
    c.alpha_composite(eyebrow(label, dark, 22), (32, 26))
    c.alpha_composite(body(markup, 32, dark, max_w=730, weight=600, color=WHITE if dark else INK), (32, 84))
    return El(c, LX, 790, t0)


def callout(text, dark, size=32):
    return tag(text, "yellow" if dark else "forest", size=size, padx=28, pady=16)


def chat(x, y, title, q, a, t0, dark, a_hl=None, t_hl=None, w=390, h=470, fs=26, type_dur=2.2):
    win = card(w, h, "white")
    d = ImageDraw.Draw(win)
    for i, col in enumerate((FOREST, TEAL, YELLOW)):
        d.ellipse([24 + i * 26, 26, 40 + i * 26, 42], fill=rgba(col))
    win.alpha_composite(text_img(title, 26, 600, "DMSans", SLATE), (112, 18))
    d.line([(2, 66), (w - 2, 66)], fill=rgba(BORDER), width=2)
    qt = text_img(q, fs, 600, "DMSans", WHITE, max_w=w - 110)
    qb = rrect(qt.width + 36, qt.height + 28, 14, fill=rgba(FOREST))
    qb.alpha_composite(qt, (18, 12))
    ay = 92 + qb.height + 22
    at = text_img(a, fs, 500, "DMSans", INK, max_w=w - 100)
    ab = rrect(at.width + 36, at.height + 28, 14, fill=rgba(MIST))
    els = [El(win, x, y, t0), El(qb, x + w - 20 - qb.width, y + 92, t0 + 0.3, dy=12),
           El(text_img("AI", 22, 700, "DMSans", SLATE), x + 24, y + ay, t0 + 0.8, dy=0),
           El(ab, x + 20, y + ay + 34, t0 + 0.8, dy=10)]
    ta = t0 + 1.0

    def typed(frame, t, op):
        paste(frame, wipe(at, (t - ta) / type_dur, int(fs * 1.16)), x + 38, y + ay + 46, op)

    els.append(Dyn(typed, ta, t_hl if a_hl else None, fadein=0.01, fade=0.2))
    if a_hl:
        els.append(El(text_img(a_hl, fs, 500, "DMSans", INK, TEAL_DEEP, max_w=w - 100, accent_weight=700),
                      x + 38, y + ay + 46, t_hl, dy=0, dur=0.25))
    return els


def grid_card(cols, rows, cell, pad=24, bar=3):
    gw, gh = cols * cell + 2 * pad, rows * cell + 2 * pad
    g = rrect(gw, gh, 22, fill=rgba(WHITE), outline=rgba(BORDER), ow=2)
    d = ImageDraw.Draw(g)
    for c in range(cols + 1):
        strong = c % bar == 0
        d.line([(pad + c * cell, pad), (pad + c * cell, pad + rows * cell)], fill=(196, 208, 202) if strong else
               (230, 236, 233), width=2 if strong else 1)
    for r in range(rows + 1):
        d.line([(pad, pad + r * cell), (pad + cols * cell, pad + r * cell)], fill=(230, 236, 233), width=1)
    return g


def note(cell, color, r=8, inset=8):
    return rrect(cell - inset, cell - inset, r, fill=rgba(color))


# ---------------------------------------------------------------- scenes

def s_hook(sc, q, ctx):
    t_mel = q.end("h1") + 0.25
    t2, t3, t4, t5, t6 = q("h2"), q("h3"), q("h4"), q("h5"), q("h6")
    els = [El(watermark(False), W - 120 - watermark(False).width, 104, 0.0, dy=0)]
    els.append(El(eyebrow("Listen", False, 28), W / 2 - 40, 120, 0.2, t2 - 0.35, fade=0.25))
    heads = [("What note comes next?", t2, t3), ("Take a moment. *Commit to an answer.*", t3, t4),
             ("It doesn't know. It *predicts.*", t4, t5)]
    for txt, a, b in heads:
        els.append(El(heading(txt, 80, align="center"), W / 2, 118, a, b - 0.4, center=True, fade=0.25))
    cell, cols, rows, pad = 64, 12, 8, 24
    g = grid_card(cols, rows, cell, pad)
    gx, gy = (W - g.width) // 2, 270
    els.append(El(g, gx, gy, 0.1, t5 - 0.1))
    ox, oy = gx + pad, gy + pad
    ph = Image.new("RGBA", (cell, rows * cell), rgba(TEAL, 46))

    def playhead(frame, t, op):
        k = (t - t_mel) / 0.32
        if -0.5 <= k <= 11.5:
            paste(frame, ph, ox + k * cell, oy, op)

    els.append(Dyn(playhead, t_mel - 0.2, t_mel + 3.9, fadein=0.2))
    rows_of = [7, 5, 3]
    for k in range(11):
        r = rows_of[k % 3]
        els.append(El(note(cell, NOTE[r]), ox + k * cell + 4, oy + r * cell + 4, t_mel + k * 0.32, t5 - 0.1,
                      dur=0.2, dy=12))
    qcol = Image.new("RGBA", (cell, rows * cell), rgba(YELLOW, 70))
    qmark = heading("?", 110)

    def question(frame, t, op):
        pulse = 0.7 + 0.3 * abs(((t * 1.4) % 2) - 1)
        paste(frame, qcol, ox + 11 * cell, oy, op * pulse)
        paste(frame, qmark, ox + 11 * cell + (cell - qmark.width) / 2 + 2, oy + 0.4 * cell, op)

    els.append(Dyn(question, t_mel + 11 * 0.32, t4 - 0.05, fadein=0.25, fade=0.2))
    els.append(El(note(cell, YELLOW), ox + 11 * cell + 4, oy + 3 * cell + 4, t4, t5 - 0.1, dur=0.25, dy=12))
    lab = tag("Most likely next note", "forest", 28)
    els.append(El(lab, gx + g.width + 24, oy + 3 * cell, t4 + 0.25, t5 - 0.1, dx=20, dy=0))
    # h5: school + the parent question; h6: five habits
    els.append(El(eyebrow("AI is coming into school", False, 28), W / 2 - 230, 300, t5 + 0.1, t6 - 0.3))
    els.append(El(heading("What does my child actually\nneed to *know* about it?", 84, align="center"), W / 2, 390,
                  t5 + 0.6, t6 - 0.3, center=True))
    els.append(El(heading("*5 habits* to try at home", 104, align="center"), W / 2, 300, t6 + 0.05, center=True))
    x = None
    chips = [tag(s, "outline", 34) for s in ("A phone", "A curious kid", "10 minutes")]
    total = sum(c.width for c in chips) + 2 * 24
    x = (W - total) / 2
    for c, sub in zip(chips, ("A phone", "A curious kid", "Ten minutes")):
        els.append(El(c, x, 520, q("h6", sub), dx=20, dy=0))
        x += c.width + 24
    return els


def s_title(sc, q, ctx):
    els = [El(lockup(64, True), W / 2, 150, 0.05, center=True)]
    els.append(El(rrect(64, 6, 3, fill=rgba(YELLOW)), W / 2 - 32, 460, 0.15, dy=0))
    els.append(El(heading("What Note Comes Next?", 120, True, align="center"), W / 2, 490, 0.2, center=True))
    els.append(El(body("5 AI habits to try with your child", 52, True, weight=500, align="center"), W / 2, 650, 0.35,
                  center=True))
    els.append(El(body("Narration: AI-generated voice", 26, True, align="center"), W / 2, 1000, 0.6, center=True))
    return els


def s_rules(sc, q, ctx):
    els = [El(eyebrow("Before you start"), LX, 104, 0.1), El(heading("Ground rules", 96), LX, 150, 0.15),
           El(watermark(False), W - 120 - watermark(False).width, 104, 0.0, dy=0)]
    specs = [(q("g2"), "badge", "Most AI tools: 13+", "Check the age rules of any tool before you start."),
             (q("g2", "With younger kids"), "phone", "Under 13? You type.", "You hold the phone. Your child does the "
                                                                              "thinking."),
             (q("g3"), "billboard", "The billboard test", "Wouldn't put it on a billboard outside school? Don't type "
                                                          "it in.")]
    cw, ch = 530, 420
    for i, (t0, icon, head, txt) in enumerate(specs):
        c = card(cw, ch, "white")
        if icon == "badge":
            b = circle(112, fill=rgba(FOREST))
            tx = text_img("13+", 42, 800, "Manrope", WHITE)
            b.alpha_composite(tx, ((112 - tx.width) // 2, (112 - tx.height) // 2 + 2))
        else:
            b = line_icon(icon, 112, FOREST)
        c.alpha_composite(b, (40, 46))
        c.alpha_composite(heading(head, 40), (40, 196))
        c.alpha_composite(body(txt, 30, max_w=450), (40, 258))
        els.append(El(c, LX + i * (cw + 45), 330, t0))
    x = LX
    for s, sub in (("No full names", "No full names"), ("No addresses", "no addresses"), ("No photos", "no photos")):
        tg = tag(s, "outline", 30)
        els.append(El(tg, x, 800, q("g3", sub), dx=20, dy=0))
        x += tg.width + 20
    return els


def s_m1_intro(sc, q, ctx):
    els = header(1, "Guess the\nNext Note", False) + chrome(1, False)
    els.append(principle("AI writes by predicting *what comes next.*", False, q("m1a") + 0.6))
    t = q("m1b")
    els.append(El(eyebrow("Live class"), RX, 196, t))
    img = ctx["still_a"]
    mask = rrect(img.width, img.height, 20, fill=(255, 255, 255, 255))
    framed = Image.new("RGBA", img.size, (0, 0, 0, 0))
    framed.paste(img, (0, 0), mask)
    els.append(El(framed, RX, 262, t + 0.15))
    play = circle(120, fill=rgba(FOREST))
    ImageDraw.Draw(play).polygon([(48, 34), (48, 86), (92, 60)], fill=rgba(WHITE))
    els.append(El(play, RX + (img.width - 120) / 2, 262 + (img.height - 120) / 2, t + 0.5, dy=0))
    els.append(El(heading("Chrome Music Lab · Song Maker", 34), RX, 262 + img.height + 26, t + 0.3))
    els.append(El(body("Varchas, live with TomoClub students", 28), RX, 262 + img.height + 76, t + 0.4))
    row = Image.new("RGBA", (600, 34), (0, 0, 0, 0))
    row.alpha_composite(line_icon("lock", 28, SLATE), (0, 2))
    row.alpha_composite(body("Student faces and names blurred", 24), (40, 0))
    els.append(El(row, RX, 262 + img.height + 124, t + 0.5))
    return els


def clip_scene(sc, ctx, segs, callouts):
    D = sc["dur"]
    player = ClipPlayer(ctx["src"], segs, (CLIP_W, CLIP_H))
    mask = rrect(CLIP_W, CLIP_H, 20, fill=(255, 255, 255, 255)).getchannel("A")

    def video(frame, t, op):
        f = player.at(t)
        if f is not None:
            frame.paste(f, (CLIP_X, CLIP_Y), mask if op >= 0.997 else mask.point(lambda v: int(v * op)))

    els = [Dyn(video, 0.0, D - 0.3, fadein=0.3, fade=0.3),
           El(eyebrow("Live class · Chrome Music Lab", True), CLIP_X, 62, 0.0, dy=0)]
    row = Image.new("RGBA", (720, 34), (0, 0, 0, 0))
    row.alpha_composite(line_icon("lock", 28, IVORY), (0, 2))
    tx = body("Varchas with TomoClub students · faces and names blurred", 24, True)
    row.alpha_composite(tx, (40, 0))
    els.append(El(row.crop((0, 0, 40 + tx.width, 34)), CLIP_X + CLIP_W - 40 - tx.width, 88, 0.1, dy=0))
    for t0, t1, text in callouts:
        els.append(El(callout(text, True, 34), CLIP_X + 36, CLIP_Y + 36, t0, t1, dx=24, dy=0))
    return els


def s_clipA(sc, q, ctx):
    return clip_scene(sc, ctx, CLIPS["clipA"], [(9.7, 12.6, "Anticipate = predict what comes next")])


def s_clipB(sc, q, ctx):
    return clip_scene(sc, ctx, CLIPS["clipB"], [(1.95, 6.35, "Experimenting is how you learn"),
                                                (11.95, 17.15, "Spotting patterns is an AI literacy skill")])


def s_m1_body(sc, q, ctx):
    tc, td, te = q("m1c"), q("m1d"), q("m1e")
    els = header(1, "Guess the\nNext Note", False) + chrome(1, False)
    els.append(principle("AI picks the *most likely* next piece.", False, tc, te - 0.1))
    els.append(principle("The *surprising* note is your child's.", False, te + 0.15))
    els.append(try_card("Build 3 bars in Song Maker. Your child guesses *bar 4.* Then swap.", False, q("m1d", "Open")))
    # phase 1: prediction bars
    els.append(El(eyebrow("How AI writes"), RX, 196, tc, td - 0.15))
    pc = card(RW, 500, "white")
    pc.alpha_composite(heading("Twinkle, twinkle, little ___", 52), (48, 44))
    rows = [("star", 1.0, TEAL, "most likely"), ("light", 0.46, FOREST, "possible"),
            ("pickle", 0.12, YELLOW, "surprising")]
    for i, (w_, _, _, lab) in enumerate(rows):
        pc.alpha_composite(heading(w_, 44), (48, 168 + i * 106))
        pc.alpha_composite(body(lab, 24, weight=600), (250, 222 + i * 106))
    els.append(El(pc, RX, 262, tc + 0.1, td - 0.15))
    t_bars = q("m1c", "An AI writes")

    def bars(frame, t, op):
        for i, (_, frac, col, _) in enumerate(rows):
            p = ease((t - t_bars - i * 0.35) / 0.9)
            if p > 0:
                paste(frame, rrect(max(12, int(470 * frac * p)), 40, 10, fill=rgba(col)), RX + 250,
                      262 + 176 + i * 106, op)

    els.append(Dyn(bars, t_bars, td - 0.15, fadein=0.01))
    # phase 2: 4-bar grid
    cell, cols, nrows, pad = 46, 16, 8, 24
    g = grid_card(cols, nrows, cell, pad, bar=4)
    gx, gy = RX + (RW - g.width) // 2, 270
    t_grid = td + 0.1
    els.append(El(eyebrow("Try it in Song Maker"), RX, 196, t_grid))
    els.append(El(g, gx, gy, t_grid))
    ox, oy = gx + pad, gy + pad
    for k, r in enumerate([7, 5, 3, 5, 6, 4, 2, 4, 5, 3, 1, 3]):
        els.append(El(note(cell, NOTE[r], 6, 6), ox + k * cell + 3, oy + r * cell + 3, t_grid + 0.4 + k * 0.08,
                      dur=0.2, dy=10))
    t_q, t_safe, t_sur = q("m1d", "let your child guess"), q("m1e"), q("m1e", "Notice how often")
    els.append(El(Image.new("RGBA", (4 * cell, nrows * cell), rgba(YELLOW, 55)), ox + 12 * cell, oy, t_q, t_sur,
                  dy=0))
    qm = heading("?", 90)
    els.append(El(qm, ox + 14 * cell - qm.width / 2, oy + (nrows * cell - qm.height) / 2, t_q, t_safe, dy=0))
    ghost = rrect(cell - 6, cell - 6, 6, outline=rgba(SLATE), ow=3)
    for k, r in enumerate([4, 2, 0, 2]):
        els.append(El(ghost, ox + (12 + k) * cell + 3, oy + r * cell + 3, t_safe + k * 0.1, t_sur, dur=0.2, dy=8))
    for k, r in enumerate([0, 6, 1, 7]):
        els.append(El(note(cell, YELLOW, 6, 6), ox + (12 + k) * cell + 3, oy + r * cell + 3, t_sur + k * 0.12,
                      dur=0.25, dy=10))
    ly = gy + g.height + 30
    els.append(El(tag("Bar 4: your child guesses", "outline", 28), RX, ly, t_q, t_safe - 0.1))
    els.append(El(tag("The safe, expected guess", "outline", 28), RX, ly, t_safe, t_sur - 0.1))
    els.append(El(tag("Your child's surprising choice", "forest", 28), RX, ly, t_sur + 0.2))
    return els


def s_m2(sc, q, ctx):
    els = header(2, "Play It\nTwice", True) + chrome(2, True)
    els.append(principle("Same question. *Brand-new chat.* Compare.", True, q("m2b")))
    els.append(try_card("Facts changed? It's a *rumour* until checked.", True, q("m2c", "Give your child")))
    qn = "When did our town's library first open?"
    t_hl = q("m2c", "If a name")
    els += chat(RX, 196, "Chat 1", qn, "Our town's library first opened in 1962.", q("m2b") + 0.3, True,
                "Our town's library first opened in *1962.*", t_hl)
    els += chat(RX + 410, 196, "New chat", qn, "It opened its doors in 1958, after a local fundraiser.",
                q("m2b", "open a"), True, "It opened its doors in *1958,* after a local fundraiser.", t_hl)
    els.append(El(tag("Same answer twice? Good sign.", "white", 30), RX, 700, q("m2c"), t_hl - 0.1))
    els.append(El(callout("The year changed. It was guessing.", True), RX, 700, t_hl + 0.1))
    return els


def s_m3(sc, q, ctx):
    els = header(3, "Flip the\nKey", False) + chrome(3, False)
    tb, tcq, td = q("m3b"), q("m3c"), q("m3d")
    els.append(principle("The way you ask *changes* the answer.", False, q("m3b", "Questions work"), td - 0.1))
    els.append(principle("Agrees with both sides? It's *following your lead.*", False, td + 0.1))
    els.append(try_card("Ask it neutrally: “What are the pros and cons of homework?”", False,
                        q("m3d", "Neutral"), label="Ask it this way"))
    pc = card(RW, 470, "white")
    for j, (name, mood, col, ys) in enumerate((("MAJOR", "bright", YELLOW, [110, 168, 226]),
                                               ("MINOR", "moody", TEAL_DEEP, [110, 186, 226]))):
        bx = 90 + j * 400
        pc.alpha_composite(text_img(name, 30, 600, "DMSans", TEAL_DEEP, tracking=3), (bx, 44))
        for y_ in ys:
            pc.alpha_composite(rrect(220, 34, 8, fill=rgba(col)), (bx, y_))
        pc.alpha_composite(heading(mood, 40), (bx, 300))
    pc.alpha_composite(line_icon("swap", 80, FOREST), (340, 150))
    pc.alpha_composite(body("Same notes, one flip, a whole new mood.", 30), (90, 390))
    els.append(El(eyebrow("Same notes, one flip"), RX, 196, tb, tcq - 0.15))
    els.append(El(pc, RX, 262, tb + 0.1, tcq - 0.15))
    els += chat(RX, 196, "Chat 1", "Why is homework good for kids?",
                "Great question! Homework is good because it builds routine and practice...", tcq + 0.1, False)
    els += chat(RX + 410, 196, "New chat", "Why is homework bad for kids?",
                "Great question! Homework is bad because it eats into play and sleep...", q("m3c", "Then, in a new"),
                False)
    els.append(El(callout("It agreed both times", False), RX, 700, td + 0.3))
    return els


def s_m4(sc, q, ctx):
    els = header(4, "Find the\nSheet Music", True) + chrome(4, True)
    els.append(principle("Before your child repeats it, *find the receipt.*", True, q("m4b")))
    els.append(try_card("No receipt? *Don't repeat it.*", True, q("m4c", "No receipt"), label="The rule"))
    rw, rh = 560, 600
    r = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    rd = ImageDraw.Draw(r)
    zig = 18
    pts = [(0, 0), (rw, 0), (rw, rh - zig)] + [(i * zig, rh - (zig if i % 2 == 0 else 0))
                                                for i in range(rw // zig, -1, -1)]
    rd.polygon(pts, fill=rgba(WHITE))
    hd = text_img("FACT  RECEIPT", 40, 800, "Manrope", FOREST, tracking=2)
    r.alpha_composite(hd, ((rw - hd.width) // 2, 40))
    for xx in range(40, rw - 40, 18):
        rd.line([(xx, 118), (xx + 9, 118)], fill=BORDER, width=3)
    r.alpha_composite(body("Before we repeat this fact, we...", 26, weight=600), (40, 140))
    items = ["Opened a real source", "A book or a site we trust", "Found the exact line"]
    for i, it in enumerate(items):
        y = 214 + i * 92
        rd.rounded_rectangle([40, y, 84, y + 44], 8, outline=(150, 165, 158), width=3)
        r.alpha_composite(text_img(it, 30, 600, "DMSans", INK), (104, y + 4))
    for xx in range(40, rw - 40, 18):
        rd.line([(xx, 498), (xx + 9, 498)], fill=BORDER, width=3)
    r.alpha_composite(text_img("TOTAL: 1 CHECKED FACT", 28, 800, "Manrope", FOREST), (40, 520))
    rx0, ry = RX + 120, 196
    els.append(El(r, rx0, ry, q("m4b") + 0.2))
    for i, sub in enumerate(("A real book", "a site you trust", "the exact line")):
        els.append(El(check_icon(52), rx0 + 36, ry + 210 + i * 92, q("m4c", sub), dur=0.25, dy=8))
    els.append(El(callout("Receipt found", True, 34), rx0 + 300, ry + 560, q("m4c", "No receipt") - 0.3))
    return els


def s_m5(sc, q, ctx):
    els = header(5, "Play It\nBy Ear", False) + chrome(5, False)
    tb, tc, td = q("m5b"), q("m5c"), q("m5d")
    els.append(principle("Can they play it *without the sheet?*", False, tb, td - 0.1))
    els.append(principle("Where they get stuck is *what to learn next.*", False, td + 0.1))
    els.append(try_card("Close the tab. Explain it out loud in *30 seconds.*", False, q("m5c", "close the tab")))
    sh = card(720, 400, "white")
    sd = ImageDraw.Draw(sh)
    for i in range(5):
        sd.line([(50, 120 + i * 30), (670, 120 + i * 30)], fill=(150, 165, 158), width=3)
    for x, k in [(110, 4), (190, 3), (270, 2), (350, 3), (430, 1), (510, 2), (590, 0)]:
        y = 120 + k * 30 + 15
        sd.ellipse([x - 20, y - 14, x + 20, y + 14], fill=FOREST)
        sd.line([(x + 18, y), (x + 18, y - 95)], fill=FOREST, width=5)
    sh.alpha_composite(body("Reading along isn't the same as knowing it.", 30), (50, 320))
    els.append(El(sh, RX + 40, 300, tb + 0.1, tc - 0.15))
    ring = 400
    rx, ry = RX + (RW - ring) // 2, 170
    t0r, t1r = q("m5c", "explain it out loud"), sc["dur"] - 0.5

    def timer(frame, t, op):
        p = clamp01((t - t0r) / (t1r - t0r))
        paste(frame, arc_ring(ring, 1 - p, YELLOW if t >= td else TEAL, BORDER), rx, ry, op)
        txt = heading(f"0:{int(round(30 * (1 - p))):02d}", 96)
        paste(frame, txt, rx + (ring - txt.width) / 2, ry + (ring - txt.height) / 2 - 6, op)

    els.append(Dyn(timer, tc, fadein=0.3))
    lab = heading("Explain it out loud", 44)
    els.append(El(lab, RX + (RW - lab.width) / 2, 610, q("m5c", "explain it out loud")))
    st = callout("Stuck? That's what to learn next.", False)
    els.append(El(st, RX + (RW - st.width) / 2, 700, td + 0.1))
    return els


def s_exp_intro(sc, q, ctx):
    return [El(heading("They didn't aim for perfect.", 76, True, align="center"), W / 2, 380, q("e1"), center=True),
            El(heading("They *experimented.*", 120, True, align="center"), W / 2, 500, q("e1", "They experimented"),
               center=True)]


def s_exp_outro(sc, q, ctx):
    els = [El(eyebrow("The habit"), W / 2 - 80, 250, q("e2")),
           El(heading("Treat AI like an instrument\nyour child is *learning.*", 84, align="center"), W / 2, 320,
              q("e2", "Treat"), center=True)]
    x0 = W / 2 - 12 * 84 / 2
    for i, r in enumerate([7, 6, 5, 5, 4, 3, 3, 2, 1, 1, 0, 0]):
        els.append(El(note(64, NOTE[r], 10, 0), x0 + i * 84 + 10, 640 + r * 22, q("e2", "and keep") + i * 0.05,
                      dur=0.25, dy=12))
    return els


def s_challenge(sc, q, ctx):
    els = [El(eyebrow("Your turn"), LX, 100, max(0.05, q("c1") - 0.3)),
           El(heading("Can your child make an AI *flip?*", 84), LX, 150, q("c1") + 0.2),
           El(watermark(False), W - 120 - watermark(False).width, 104, 0.0, dy=0)]

    def step(n, head, h, extra=None):
        c = card(900, h, "white")
        b = circle(64, fill=rgba(FOREST))
        num = text_img(str(n), 36, 800, "Manrope", WHITE)
        b.alpha_composite(num, ((64 - num.width) // 2, (64 - num.height) // 2 + 1))
        c.alpha_composite(b, (28, 26))
        c.alpha_composite(heading(head, 34, max_w=760), (116, 38))
        if extra:
            x = 116
            for e in extra:
                c.alpha_composite(e, (x, 100))
                x += e.width + 14
        return c

    ex = [tag(s, "outline", 24, padx=16, pady=8) for s in ("cats or dogs", "pizza or dosa")]
    els.append(El(step(1, "Pick a this-or-that together", 170, ex), LX, 300, q("c2")))
    els.append(El(step(2, "Chat 1: “Why is the first one better?”", 116), LX, 492, q("c3")))
    els.append(El(step(3, "New chat: “Why is the second one better?”", 116), LX, 630, q("c3", "Then open")))
    cx = 1110
    els.append(El(heading("Flipped or held?", 44), cx, 300, q("c4")))
    fl, hd = tag("FLIPPED", "forest", 40, padx=30, pady=14), tag("HELD", "teal", 40, padx=30, pady=14)
    els.append(El(fl, cx, 372, q("c4", "flip to agree"), dy=12))
    els.append(El(hd, cx + fl.width + 24, 372, q("c4", "hold its ground"), dy=12))
    cm = card(690, 270, "white")
    cm.alpha_composite(body("Your comment", 26, weight=600), (32, 26))
    ImageDraw.Draw(cm).line([(32, 72), (658, 72)], fill=rgba(BORDER), width=2)
    cm.alpha_composite(tag("Comment", "forest", 24, padx=18, pady=8), (528, 196))
    t_cm = q("c4", "Tell us")
    els.append(El(cm, cx, 500, t_cm - 0.3))
    typed_txt = text_img("FLIPPED · cats or dogs.\nWe both laughed when it agreed twice.", 32, 600, "DMSans",
                         INK, lh=1.3)

    def typing(frame, t, op):
        paste(frame, wipe(typed_txt, (t - t_cm) / 2.4, int(32 * 1.3)), cx + 32, 500 + 92, op)

    els.append(Dyn(typing, t_cm, fadein=0.01))
    ban = card(1680, 92, "white")
    ban.alpha_composite(line_icon("lock", 40, FOREST), (34, 26))
    ban.alpha_composite(heading("Keep your child's name and school out of the comments.", 34), (96, 24))
    els.append(El(ban, LX, 880, q("c5")))
    return els


def s_recap(sc, q, ctx):
    els = [El(heading("Quick recap", 88, align="center"), W / 2, 80, q("r0"), center=True)]
    names = ["Guess the next note", "Play it twice", "Flip the key", "Find the sheet music", "Play it by ear"]
    cols = [(FOREST, WHITE), (TEAL_DEEP, WHITE), (YELLOW, FOREST), (LEAF, FOREST), (TEAL, FOREST)]
    for i, n in enumerate(names):
        b = rrect(100, 100, 16, fill=rgba(cols[i][0]))
        num = text_img(str(i + 1), 56, 800, "Manrope", cols[i][1])
        b.alpha_composite(num, ((100 - num.width) // 2, 10))
        y = 240 + i * 144
        els.append(El(b, 560, y, q(f"r{i + 1}"), dx=20, dy=0))
        els.append(El(heading(n, 62), 700, y + 12, q(f"r{i + 1}") + 0.05, dx=30, dy=0))
    return els


def form_mock(ctx_t):
    """A faithful, simplified picture of the real ATC contact form (tally.so/r/GxGdEQ)."""
    t_tick, t_send = ctx_t
    fw, fh = 700, 760
    f = card(fw, fh, "white")
    f.alpha_composite(heading("Let's talk", 48), (44, 40))
    f.alpha_composite(body("Tell us about your child. Our team will email you.", 24, max_w=600), (44, 108))
    y = 170
    for lab in ("Parent contact details", "Child's grade (AY 26-27)"):
        f.alpha_composite(body(lab, 22, weight=600, color=INK), (44, y))
        f.alpha_composite(rrect(612, 52, 10, fill=rgba(WHITE), outline=rgba(BORDER), ow=2), (44, y + 34))
        y += 104
    f.alpha_composite(body("Program interested in", 22, weight=600, color=INK), (44, y))
    opts = ["AI Labs (AI Literacy)", "Game Based Learning", "Fun with Coding", "Fun with Math"]
    boxes = []
    for i, o in enumerate(opts):
        oy = y + 40 + i * 52
        f.alpha_composite(rrect(34, 34, 8, fill=rgba(WHITE), outline=rgba(SLATE), ow=2), (44, oy))
        f.alpha_composite(body(o, 26, weight=600 if i == 0 else 500, color=INK if i == 0 else SLATE), (94, oy))
        boxes.append(oy)
    return f, boxes[0], (fw, fh)


def s_cta(sc, q, ctx):
    els = [El(eyebrow("AI Labs at All Things Classroom", True), LX, 120, q("a1")),
           El(heading("Don't just use AI.\n*Understand it.*", 92, True, lh=1.04), LX, 180, q("a1") + 0.15)]
    pts = [("Live online classes", q("a2")), ("The same teacher every week", q("a2", "the same one")),
           ("Built around making things", q("a2", "built around")), ("Monthly, no lock-ins", q("a2", "Monthly"))]
    for i, (p, t0) in enumerate(pts):
        row = Image.new("RGBA", (760, 56), (0, 0, 0, 0))
        row.alpha_composite(circle(18, fill=rgba(LEAF)), (0, 16))
        row.alpha_composite(body(p, 38, True, weight=600, color=WHITE), (40, 0))
        els.append(El(row, LX, 440 + i * 76, t0, dx=20, dy=0))
    els.append(El(body("STEM.org Accredited · Google for Education Certified Educator", 26, True), LX, 780,
                  q("a2", "Monthly") + 0.4))
    t_form, t_tick, t_send = q("a3"), q("a3", "tick AI Labs"), q("a3", "and our team")
    f, box_y, (fw, fh) = form_mock((t_tick, t_send))
    fx, fy = 1080, 140
    els.append(El(f, fx, fy, t_form - 0.6))
    els.append(El(check_icon(34, FOREST), fx + 44, fy + box_y, t_tick, dur=0.2, dy=6))
    send_up = button("Send my Request", False, 30)
    send_dn = tag("Send my Request", "night", 30, padx=34, pady=18)
    els.append(El(send_up, fx + 44, fy + fh - 120, t_form - 0.4, t_send, fade=0.1))
    els.append(El(send_dn, fx + 44, fy + fh - 120, t_send, dy=0, dur=0.1))
    ok = tag("We'll email you", "yellow", 26, padx=18, pady=10)
    els.append(El(ok, fx + 44 + send_up.width + 20, fy + fh - 112, t_send + 0.3, dx=16, dy=0))
    els.append(El(body("Form link in the description · allthingsclassroom.com", 28, True), fx, fy + fh + 30,
                  t_form))
    return els


def s_outro(sc, q, ctx):
    D, t2 = sc["dur"], q("o2")
    els = [El(eyebrow("One more thing", True), W / 2 - 110, 250, q("o1"), t2 - 0.3),
           El(heading("This voice was made with *AI.*", 88, True, align="center"), W / 2, 320, q("o1", "This voice"),
              t2 - 0.3, center=True),
           El(body("Now you know how to question it.", 48, True, align="center"), W / 2, 460, q("o1", "Now you know"),
              t2 - 0.3, center=True),
           El(lockup(110, True), W / 2, 230, t2, D - 0.8, center=True, fade=0.8),
           El(body("allthingsclassroom.com", 40, True, weight=600, align="center"), W / 2, 640, t2 + 0.3, D - 0.8,
              center=True, fade=0.8),
           El(body("Form link in the description", 30, True, align="center"), W / 2, 700, t2 + 0.5, D - 0.8,
              center=True, fade=0.8)]
    return els


BUILDERS = {"hook": s_hook, "title": s_title, "rules": s_rules, "m1_intro": s_m1_intro, "clipA": s_clipA,
            "m1_body": s_m1_body, "m2": s_m2, "m3": s_m3, "m4": s_m4, "m5": s_m5, "exp_intro": s_exp_intro,
            "clipB": s_clipB, "exp_outro": s_exp_outro, "challenge": s_challenge, "recap": s_recap, "cta": s_cta,
            "outro": s_outro}


# ---------------------------------------------------------------- render plumbing

@functools.lru_cache(maxsize=None)
def ctx_for(src):
    rainbow = still(src, 70.0, (W, H)).filter(ImageFilter.GaussianBlur(28))
    rainbow = ImageEnhance.Brightness(rainbow).enhance(0.6)
    night = T.bg_image("night", W, H)
    return {"src": src, "still_a": still(src, 33.0, (800, 450)), "bg_exp": Image.blend(night, rainbow, 0.25)}


def elements(sc, src):
    ctx = ctx_for(src)
    els = BUILDERS[sc["id"]](sc, Cues(sc), ctx)
    for e in els:
        if e.t1 is None:
            e.t1, e.fade = sc["dur"] - 0.35, 0.3
    bg = ctx["bg_exp"] if sc["id"] == "exp_intro" else T.bg_image(sc["bg"], W, H)
    return bg, els


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
    render_scene_file(os.path.join(work, "scenes", f"{i:02d}_{sc['id']}.mp4"), (W, H), sc["frames"],
                      frame_fn(bg, els))
    return sc["id"]


def cue_fx(fx, tl):
    by = {s["id"]: s for s in tl}
    hook = by["hook"]
    q = Cues(hook)
    t_mel = q.end("h1") + 0.25
    for k, n in enumerate([72, 76, 79] * 3 + [72, 76]):
        add(fx, pluck(midi(n), 1.6), hook["start"] + t_mel + k * 0.32, 0.30, pan=-0.2 + 0.04 * k)
    t_res = hook["start"] + q("h4")
    add(fx, pluck(midi(79), 2.0), t_res, 0.34)
    add(fx, pluck(midi(91), 2.0, 0.4), t_res + 0.02, 0.10)
    ts = by["title"]["start"]
    for k, n in enumerate([55, 59, 62, 67, 71]):
        add(fx, pluck(midi(n), 2.4), ts + 0.05 + k * 0.07, 0.16, pan=-0.4 + 0.2 * k)
    for sid, vid in (("m1_intro", "m1a"), ("m2", "m2a"), ("m3", "m3a"), ("m4", "m4a"), ("m5", "m5a"),
                     ("challenge", "c1"), ("cta", "a1")):
        t = by[sid]["start"] + Cues(by[sid])(vid) - 0.25
        add(fx, pluck(midi(79), 1.4), t, 0.13, pan=-0.2)
        add(fx, pluck(midi(83), 1.6), t + 0.11, 0.13, pan=0.2)
    return t_res


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap2(text, n=42):
    if len(text) <= n:
        return [text]
    sp = [i for i, ch in enumerate(text) if ch == " "]
    best = min(sp, key=lambda i: max(i, len(text) - i - 1))
    return [text[:best], text[best + 1:]]


def captions(work, out):
    cues = []
    for sc in timeline(work):
        for it in sc["items"]:
            base = sc["start"] + it["start"]
            if it["kind"] == "vo":
                parts = []
                for sent in re.split(r"(?<=[.?!])\s+", fix(it["text"])):
                    while len(sent) > 84:
                        cut = sent.rfind(", ", 0, 84)
                        cut = cut if cut > 20 else sent.rfind(" ", 0, 84)
                        parts.append(sent[:cut + 1].strip())
                        sent = sent[cut + 1:].strip()
                    parts.append(sent)
                total = sum(len(p) for p in parts)
                t = base
                for p in parts:
                    d = it["dur"] * len(p) / total
                    cues.append((t, t + d, p))
                    t += d
            else:
                off, first = 0.0, True
                events = CLIP_CAPTIONS + [(s, e, "[Student's song plays]") for s, e in SONG[it["id"]]]
                for a, b in it["segs"]:
                    for s, e, txt in sorted(events):
                        if s < b and e > a:
                            if first and not txt.startswith("["):
                                txt, first = "[Varchas] " + txt, False
                            cues.append((base + off + max(s, a) - a, base + off + min(e, b) - a, txt))
                    off += b - a
    cues.sort()
    with open(out, "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b - 0.02)}\n" + "\n".join(wrap2(txt)) + "\n\n")
    print(len(cues), "captions")


def thumbnail(out):
    tw, th = 1280, 720
    img = T.bg_image("ivory", tw, th).convert("RGBA")
    img.alpha_composite(watermark(False, 28), (56, 44))
    cell, cols, rows, pad = 52, 8, 7, 18
    g = grid_card(cols, rows, cell, pad)
    for k, r in enumerate([6, 4, 2, 6, 4, 2, 6]):
        g.alpha_composite(note(cell, NOTE[r + 1], 8, 8), (pad + k * cell + 4, pad + r * cell + 4))
    g.alpha_composite(Image.new("RGBA", (cell, rows * cell), rgba(YELLOW, 110)), (pad + 7 * cell, pad))
    qm = heading("?", 110)
    g.alpha_composite(qm, (pad + 7 * cell + (cell - qm.width) // 2, pad + 60))
    img.alpha_composite(g, (tw - g.width - 64, 160))
    img.alpha_composite(heading("What note\ncomes *next?*", 96, lh=1.0), (52, 150))
    img.alpha_composite(body("5 AI habits to try\nwith your child", 44, weight=600, color=INK), (56, 400))
    img.alpha_composite(tag("For parents", "forest", 30), (56, 560))
    img.convert("RGB").save(out, quality=92)


def main():
    mode = sys.argv[1]
    if mode == "tts":
        return tts(*sys.argv[2:4], SCENES, sys.argv[4])
    if mode == "thumbnail":
        return thumbnail(sys.argv[2])
    if mode == "captions":
        return captions(sys.argv[2], sys.argv[3])
    if mode == "chapters":
        for s in timeline(sys.argv[2]):
            print(f"{int(s['start'] // 60)}:{int(s['start'] % 60):02d} {s['id']}")
        return
    src, work = sys.argv[2:4]
    tl = timeline(work)
    if mode == "audio":
        print("soundtrack", mix_soundtrack(tl, src, work, cue_fx, bpm=100, bed_lufs=-32.0))
    elif mode == "preview":
        sc = next(s for s in tl if s["id"] == sys.argv[4])
        os.makedirs(os.path.join(work, "preview"), exist_ok=True)
        bg, els = elements(sc, src)
        f = frame_fn(bg, els)
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
        only = set(sys.argv[4:])
        jobs = sorted([(i, s, src, work) for i, s in enumerate(tl) if not only or s["id"] in only],
                      key=lambda j: -j[1]["frames"])
        with multiprocessing.Pool(4) as pool:
            for sid in pool.imap_unordered(render_job, jobs):
                print("rendered", sid, flush=True)
    elif mode == "final":
        final_encode(tl, work, sys.argv[4], crf=18, title=TITLE)
        print("wrote", sys.argv[4])


if __name__ == "__main__":
    main()
