"""Instagram Reel cut: 1080x1920 (9:16), ~75 s, captions burned in.

  python reel.py tts     <kokoro.onnx> <voices.bin> <workdir>
  python reel.py audio   <session.mp4> <workdir>
  python reel.py preview <session.mp4> <workdir> <scene_id> <t> [<t> ...]
  python reel.py scenes  <session.mp4> <workdir>
  python reel.py final   <session.mp4> <workdir> <out.mp4>
  python reel.py cover   <out.jpg>

Layout keeps everything important inside Instagram's Reels safe zone: nothing essential in the
top ~250 px (header), the bottom ~420 px (caption/username), or the right ~140 px from mid-height
down (like/comment/share buttons).
"""
import functools
import json
import multiprocessing
import os
import re
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

import audio as A
import scenes as LS
from gfx import (C, F, PITCH, Dyn, El, arc_ring, background, card, check_icon, circle, clamp01, ease, lock_icon,
                 note_block, paste, pill, rgba, rrect, shadowed, stamp, text_img, wordmark)
from timeline import Cues, build

RW, RH = 1080, 1920
FPS = 30
X0 = 80                     # left margin
VIS_Y = 690                 # top of the illustration area
CAP_Y, CAP_CX, CAP_W = 1300, 500, 780   # burned-in captions (kept left of the action buttons)
CLIP_SIZE = (920, 518)
VOICE, SPEED = "af_heart", 1.1

CLIPS = {"clipA": [(35.5, 41.35)], "clipB": [(49.85, 55.25)]}
CLIP_CAPTIONS = [
    (35.6, 37.35, "I like the gap in between"),
    (37.35, 38.6, "where it plays"),
    (38.6, 40.6, "and gives something to anticipate as well."),
    (40.65, 41.3, "Well done."),
    (49.95, 50.9, "I love this."),
    (51.0, 53.4, "Yeah, that's how you experiment."),
    (53.85, 55.2, "That's how you experiment."),
]
CAPTION_FIXES = {"Tomo Club": "TomoClub", "thirty seconds": "30 seconds"}

SCENES = [
    {"id": "hook", "lead": 1.95, "tail": 0.3, "items": [
        ("vo", "rh1", "What note comes next?", 0.9),
        ("vo", "rh2", "You just predicted it. That's how AI works too.", 0.3),
        ("vo", "rh3", "Here are five moves to stay smarter than the machine.", 0.2),
    ]},
    {"id": "m1", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r1a", "One: guess the next note.", 0.25),
        ("clip", "clipA"),
        ("vo", "r1b", "Anticipating is exactly what AI does. It picks the most likely next word, so it plays it safe.",
         0.3),
        ("vo", "r1c", "Want something original? Pick the surprising note yourself.", 0.2),
    ]},
    {"id": "m2", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r2a", "Two: play it twice.", 0.2),
        ("vo", "r2b", "Ask the same question in a brand-new chat. If the facts change, it was guessing.", 0.2),
    ]},
    {"id": "m3", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r3a", "Three: flip the key.", 0.2),
        ("vo", "r3b", "Ask why morning study is better. Then, in a new chat, ask why night study is better. "
                      "If it agrees both times, it's just following your lead.", 0.2),
    ]},
    {"id": "m4", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r4a", "Four: find the sheet music.", 0.2),
        ("vo", "r4b", "Before you repeat an AI fact, find it in a real source yourself. No receipt? Don't repeat it.",
         0.2),
    ]},
    {"id": "m5", "lead": 0.3, "tail": 0.4, "items": [
        ("vo", "r5a", "Five: play it by ear.", 0.2),
        ("vo", "r5b", "Close the tab, and explain it out loud in thirty seconds. "
                      "Where you get stuck is what you still need to learn.", 0.2),
    ]},
    {"id": "clipB", "lead": 0.2, "tail": 0.3, "items": [
        ("clip", "clipB"),
    ]},
    {"id": "challenge", "lead": 0.3, "tail": 0.5, "items": [
        ("vo", "rc1", "Your turn. Can you make an AI flip?", 0.3),
        ("vo", "rc2", "Ask an approved AI tool why cats are better. Then, in a new chat, ask why dogs are better.", 0.3),
        ("vo", "rc3", "Did it flip, or hold its ground? Comment flipped or held. "
                      "And please, no names or personal details.", 0.2),
    ]},
    {"id": "outro", "lead": 0.3, "tail": 1.7, "items": [
        ("vo", "ro1", "Oh, and this voice? Made by AI. Now you know how to question it.", 0.3),
        ("vo", "ro2", "Follow Tomo Club for more.", 0.0),
    ]},
]


def fix(text):
    for k, v in CAPTION_FIXES.items():
        text = text.replace(k, v)
    return text


def timeline(work):
    return build(work, SCENES, CLIPS)


# ---------------------------------------------------------------- narration

def tts(model, voices, work):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    from tts import trim
    out = os.path.join(work, "vo")
    os.makedirs(out, exist_ok=True)
    k = Kokoro(model, voices)
    durations = {}
    for sc in SCENES:
        for it in sc["items"]:
            if it[0] == "vo":
                samples, sr = k.create(it[2], voice=VOICE, speed=SPEED, lang="en-us")
                samples = trim(samples, sr)
                sf.write(os.path.join(out, it[1] + ".wav"), samples, sr)
                durations[it[1]] = len(samples) / sr
                print(f"{it[1]}: {durations[it[1]]:.2f}s")
    with open(os.path.join(out, "durations.json"), "w") as f:
        json.dump(durations, f, indent=1)


# ---------------------------------------------------------------- soundtrack

def soundtrack(src, work):
    SR = A.SR
    tl = timeline(work)
    total = tl[-1]["start"] + tl[-1]["dur"]
    N = int(round(total * SR))
    vo, clips, fx = (np.zeros((N, 2), np.float32) for _ in range(3))
    vo_active, clip_active = np.zeros(N, np.float32), np.zeros(N, np.float32)
    for sc in tl:
        for it in sc["items"]:
            t0 = sc["start"] + it["start"]
            i = int(t0 * SR)
            if it["kind"] == "vo":
                x = A.ff_read(["-i", os.path.join(work, "vo", it["id"] + ".wav"), "-ar", str(SR), "-ac", "1"])
                A.add(vo, x, t0)
                vo_active[i:i + len(x)] = 1
            else:
                off = 0.0
                for a, b in it["segs"]:
                    x = A.ff_read(["-ss", f"{a}", "-t", f"{b - a}", "-i", src, "-vn", "-ar", str(SR), "-ac", "2"])
                    x = x.reshape(-1, 2).copy()
                    fl = int(0.05 * SR)
                    ramp = np.linspace(0, 1, fl, dtype=np.float32)[:, None]
                    x[:fl] *= ramp
                    x[-fl:] *= ramp[::-1]
                    A.add(clips, x, t0 + off)
                    off += b - a
                clip_active[i:i + int(it["dur"] * SR)] = 1
    by = {s["id"]: s for s in tl}
    for k, n in enumerate([72, 76, 79] * 2 + [72, 76]):
        A.add(fx, A.pluck(A.midi(n), 1.4), 0.15 + k * 0.22, 0.30, pan=-0.2 + 0.05 * k)
    t_res = Cues(by["hook"])("rh2")
    A.add(fx, A.pluck(A.midi(79), 2.0), t_res, 0.34)
    A.add(fx, A.pluck(A.midi(91), 2.0, 0.4), t_res + 0.02, 0.10)
    for sid, vid in (("m1", "r1a"), ("m2", "r2a"), ("m3", "r3a"), ("m4", "r4a"), ("m5", "r5a"),
                     ("challenge", "rc1")):
        t = by[sid]["start"] + Cues(by[sid])(vid) - 0.2
        A.add(fx, A.pluck(A.midi(79), 1.2), t, 0.13, pan=-0.2)
        A.add(fx, A.pluck(A.midi(84), 1.4), t + 0.1, 0.13, pan=0.2)
    bed = A.music_bed(total, bpm=108)
    bed = np.pad(bed, ((0, max(0, N - len(bed))), (0, 0)))[:N]
    g = np.zeros(N, np.float32)
    si = int(t_res * SR)
    g[si:] = 1.0
    g *= A.smooth(np.where(vo_active > 0, 0.55, 1.0).astype(np.float32), 0.5)
    g *= 1 - A.smooth(clip_active, 0.6)
    g *= np.clip((np.arange(N) - si) / (1.0 * SR), 0, 1).astype(np.float32)
    tail = int((total - 2.0) * SR)
    g[tail:] *= np.linspace(1, 0, N - tail, dtype=np.float32)
    bed *= g[:, None]
    mix = (vo * 10 ** ((-16.0 - A.lufs(vo)) / 20) + clips * 10 ** ((-16.5 - A.lufs(clips)) / 20)
           + bed * 10 ** ((-31.0 - A.lufs(bed)) / 20) + fx * 10 ** ((-26.0 - A.lufs(fx)) / 20))
    raw = os.path.join(work, "mix_raw.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", raw], input=mix.astype(np.float32).tobytes(), check=True)
    p = subprocess.run(["ffmpeg", "-v", "info", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True)
    js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode()).group(0))
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le",
                    os.path.join(work, "soundtrack.wav")], check=True)
    print("soundtrack", total)


# ---------------------------------------------------------------- captions

def caption_chunks(text, max_chars=42):
    """Sentence-aware chunks of roughly equal length, so no chunk is a lone trailing word."""
    out = []
    for sent in re.split(r"(?<=[.?!])\s+", text):
        words = sent.split()
        n = -(-len(sent) // max_chars)
        target = len(sent) / n
        cur = ""
        for i, w in enumerate(words):
            rest = len(words) - i
            if cur and len(cur) + 1 + len(w) > target + 6 and len(out) < 99 and rest >= 2:
                out.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            out.append(cur)
    return out


def caption_sprite(text, color=C["text"]):
    font, max_w = F(52, 800), CAP_W - 56
    if font.getlength(text) > max_w:
        # two lines of similar width instead of a long line and a stray word
        words = text.split()
        best = min(range(1, len(words)), key=lambda i: max(font.getlength(" ".join(words[:i])),
                                                            font.getlength(" ".join(words[i:]))))
        text = " ".join(words[:best]) + "\n" + " ".join(words[best:])
    t = text_img(text, 52, 800, color=color, align="center", lh=1.12)
    box = rrect(t.width + 56, t.height + 30, 22, fill=(8, 13, 28, 215))
    box.alpha_composite(t, (28, 13))
    return box


def caption_elements(sc):
    """Burned-in captions for everything spoken in this scene (narration and facilitator)."""
    cues = []
    for it in sc["items"]:
        if it["kind"] == "vo":
            parts = caption_chunks(fix(it["text"]))
            total = sum(len(p) for p in parts)
            t = it["start"]
            for p in parts:
                d = it["dur"] * len(p) / total
                cues.append((t, t + d, p, C["text"]))
                t += d
        else:
            off = 0.0
            for a, b in it["segs"]:
                for s, e, txt in CLIP_CAPTIONS:
                    if s < b and e > a:
                        cues.append((it["start"] + off + max(s, a) - a, it["start"] + off + min(e, b) - a, txt,
                                     C["gold"]))
                off += b - a
    els = []
    for i, (a, b, txt, col) in enumerate(cues):
        nxt = cues[i + 1][0] if i + 1 < len(cues) else None
        t1 = b + 0.25 if nxt is None or nxt - b > 0.35 else nxt
        img = caption_sprite(txt, col)
        els.append(El(img, CAP_CX - img.width / 2, CAP_Y, a, min(t1, sc["dur"] - 0.3), dur=0.12, dy=10, fade=0.1))
    return els


# ---------------------------------------------------------------- shared layout

def top_bar(n=None):
    els = [El(wordmark(40), X0, 262, -1, dy=0)]
    if n:
        bars = Image.new("RGBA", (5 * 52 + 4 * 10, 10), (0, 0, 0, 0))
        for i in range(5):
            col = C["teal"] if i < n - 1 else C["gold"] if i == n - 1 else C["slate2"]
            bars.alpha_composite(rrect(52, 10, 5, fill=rgba(col)), (i * 62, 0))
        els.append(El(bars, RW - X0 - bars.width, 280, -1, dy=0))
    return els


def header(label, title, label_bg=C["teal"], t0=0.0, size=100):
    return [El(pill(label, 28, 800, fg=C["navy"], bg=label_bg), X0, 332, t0),
            El(text_img(title, size, 800, lh=1.02, max_w=920), X0, 402, t0 + 0.08)]


def chat(x, y, title, q, a, t0, hl=None, t_hl=None, w=440, h=470, type_dur=1.6):
    fs = 32
    win = card(w, h, fill=C["slate"], r=26)
    d = ImageDraw.Draw(win)
    for i, col in enumerate((C["crimson"], C["gold"], C["teal"])):
        d.ellipse([26 + i * 28, 28, 44 + i * 28, 46], fill=rgba(col))
    win.alpha_composite(text_img(title, 28, 700, color=C["muted"]), (122, 20))
    d.line([(0, 72), (w, 72)], fill=rgba(C["line"], 160), width=2)
    qt = text_img(q, fs, 600, color=C["navy"], max_w=w - 100)
    qb = rrect(qt.width + 40, qt.height + 30, 22, fill=rgba(C["teal"]))
    qb.alpha_composite(qt, (20, 13))
    ay = 98 + qb.height + 22
    at = text_img(a, fs, 500, color=C["text"], max_w=w - 90)
    ab = rrect(at.width + 40, at.height + 30, 22, fill=rgba(C["slate2"]))
    els = [El(shadowed(win, blur=18, alpha=0.45), x, y, t0),
           El(qb, x + w - 22 - qb.width, y + 98, t0 + 0.25, dy=14),
           El(text_img("AI", 24, 800, color=C["muted"]), x + 24, y + ay, t0 + 0.6, dy=0),
           El(ab, x + 20, y + ay + 36, t0 + 0.6, dy=10)]
    ta = t0 + 0.75

    def typed(frame, t, op):
        paste(frame, LS.wipe(at, (t - ta) / type_dur, int(fs * 1.16)), x + 40, y + ay + 49, op)

    els.append(Dyn(typed, ta, t_hl if hl else None, fadein=0.01, fade=0.2))
    if hl:
        els.append(El(text_img(hl, fs, 500, color=C["text"], accent=C["pink"], max_w=w - 90), x + 40, y + ay + 49,
                      t_hl, dy=0, dur=0.25))
    return els


def clip_elements(src, segs, t_start, x=X0, y=VIS_Y):
    player = LS.ClipPlayer(src, segs, CLIP_SIZE)
    dur = sum(b - a for a, b in segs)
    mask = rrect(*CLIP_SIZE, 24, fill=(255, 255, 255, 255)).getchannel("A")
    border = rrect(CLIP_SIZE[0] + 6, CLIP_SIZE[1] + 6, 27, outline=rgba(C["line"]), ow=3)

    def video(frame, t, op):
        f = player.at(min(t - t_start, dur - 1 / FPS))
        if f is None:
            return
        m = mask if op >= 0.997 else mask.point(lambda v: int(v * op))
        frame.paste(f, (x, y), m)
        paste(frame, border, x - 3, y - 3, op)

    tag = pill("Real TomoClub session", 26, 800, fg=C["navy"], bg=C["teal"])
    note = text_img("Student faces & names blurred", 26, 600, color=C["muted"])
    row = Image.new("RGBA", (40 + note.width, 34), (0, 0, 0, 0))
    row.alpha_composite(lock_icon(28, C["muted"]), (0, 2))
    row.alpha_composite(note, (40, 0))
    return [Dyn(video, t_start, t_start + dur, fadein=0.2, fade=0.3),
            El(tag, x + 20, y + 20, t_start + 0.1, t_start + dur, dy=0),
            El(row, x, y + CLIP_SIZE[1] + 22, t_start + 0.1, t_start + dur, dy=0)]


# ---------------------------------------------------------------- scenes

def s_hook(sc, q, src):
    t2, t3 = q("rh2"), q("rh3")
    els = top_bar()
    els.append(El(text_img("What note\ncomes next?", 110, 800, align="center", lh=1.02), RW / 2, 360, -1, t2 - 0.35,
                  center=True, fade=0.25))
    els.append(El(text_img("You just\n*predicted* it.", 110, 800, align="center", lh=1.02), RW / 2, 360, t2, t3 - 0.35,
                  center=True, fade=0.25))
    els.append(El(text_img("*5 moves* to\nout-think AI", 110, 800, align="center", lh=1.02), RW / 2, 360, t3,
                  center=True))
    cell, cols, rows, pad = 96, 9, 5, 24
    gw, gh = cols * cell + 2 * pad, rows * cell + 2 * pad
    gx, gy = (RW - gw) // 2, VIS_Y
    grid = rrect(gw, gh, 28, fill=rgba(C["white"]))
    d = ImageDraw.Draw(grid)
    for c in range(cols + 1):
        col = (200, 206, 214) if c % 3 == 0 else (232, 235, 240)
        d.line([(pad + c * cell, pad), (pad + c * cell, pad + rows * cell)], fill=col, width=2 if c % 3 == 0 else 1)
    for r in range(rows + 1):
        d.line([(pad, pad + r * cell), (pad + cols * cell, pad + r * cell)], fill=(232, 235, 240), width=1)
    els.append(El(shadowed(grid), gx, gy, -1, t3 - 0.1))
    ox, oy = gx + pad, gy + pad
    ph = Image.new("RGBA", (cell, rows * cell), rgba(C["teal"], 46))

    def playhead(frame, t, op):
        k = (t - 0.15) / 0.22
        if -0.5 <= k <= 8.3:
            paste(frame, ph, ox + k * cell, oy, op)

    els.append(Dyn(playhead, 0.0, 2.0, fadein=0.05, fade=0.2))
    rows_of = {72: 4, 76: 2, 79: 0}
    pitch_col = {4: PITCH[7], 2: PITCH[5], 0: PITCH[3]}
    for k, n in enumerate([72, 76, 79] * 2 + [72, 76]):
        r = rows_of[n]
        els.append(El(note_block(cell - 12, cell - 12, pitch_col[r], r=10), ox + k * cell + 6, oy + r * cell + 6,
                      0.15 + k * 0.22, t3 - 0.1, dur=0.22, anim="pop"))
    qcol = Image.new("RGBA", (cell, rows * cell), rgba(C["gold"], 70))
    qmark = text_img("?", 130, 800, color=C["gold"])

    def question(frame, t, op):
        pulse = 0.75 + 0.25 * abs(((t * 1.6) % 2) - 1)
        paste(frame, qcol, ox + 8 * cell, oy, op * pulse)
        paste(frame, qmark, ox + 8 * cell + (cell - qmark.width) / 2 + 2, oy + 1.2 * cell, op)

    els.append(Dyn(question, 1.85, t2 - 0.05, fadein=0.2, fade=0.2))
    g = note_block(cell - 12, cell - 12, PITCH[3], r=10)
    els.append(El(shadowed(g, blur=12, off=(0, 0), alpha=1.0, pad=24, color=C["gold"]), ox + 8 * cell + 6, oy + 6,
                  t2, t3 - 0.1, dur=0.3, anim="pop"))
    lab = pill("Most likely next note", 32, 800, fg=C["navy"], bg=C["gold"])
    els.append(El(lab, gx + gw - lab.width, gy - lab.height - 14, t2 + 0.2, t3 - 0.1))
    cols5 = [C["teal"], C["gold"], C["crimson"], C["violet"], (52, 152, 219)]
    for i in range(5):
        b = note_block(150, 150, cols5[i], r=22)
        num = text_img(str(i + 1), 84, 800, color=C["navy"])
        b.alpha_composite(num, ((150 - num.width) // 2, 16))
        els.append(El(b, RW / 2 - (5 * 150 + 4 * 28) / 2 + i * 178, 800 + (i % 2) * 60, t3 + 0.2 + i * 0.1,
                      anim="pop"))
    return els


def s_m1(sc, q, src):
    clip = next(it for it in sc["items"] if it["kind"] == "clip")
    tc, tb, tcc = clip["start"], q("r1b"), q("r1c")
    els = top_bar(1) + header("MOVE 1 OF 5", "Guess the\nNext Note")
    els += clip_elements(src, clip["segs"], tc)
    callout = pill("Anticipate = predict", 40, 800, fg=C["navy"], bg=C["gold"], padx=30, pady=14)
    els.append(El(shadowed(callout, blur=14, alpha=0.5, pad=30), RW - X0 - callout.width - 20, VIS_Y + 410,
                  tc + 3.7, tc + clip["dur"], dy=0, dx=30))
    pc = card(920, 520, fill=C["slate"])
    pc.alpha_composite(text_img("Twinkle, twinkle, little ___", 56, 700), (48, 44))
    rows = [("star", 1.0, C["teal"], "most likely"), ("light", 0.46, C["gold"], "possible"),
            ("pickle", 0.12, C["crimson"], "surprising")]
    for i, (w_, _, _, tag) in enumerate(rows):
        pc.alpha_composite(text_img(w_, 48, 700), (48, 168 + i * 110))
        pc.alpha_composite(text_img(tag, 28, 600, color=C["muted"]), (270, 226 + i * 110))
    els.append(El(shadowed(pc, alpha=0.45), X0, VIS_Y, tb))
    t_bars = q("r1b", "It picks")

    def bars(frame, t, op):
        for i, (_, frac, col, _) in enumerate(rows):
            p = ease((t - t_bars - i * 0.3) / 0.8)
            if p > 0:
                paste(frame, rrect(max(12, int(560 * frac * p)), 44, 12, fill=rgba(col)), X0 + 270,
                      VIS_Y + 176 + i * 110, op)

    els.append(Dyn(bars, t_bars, fadein=0.01))
    els.append(El(stamp("SURPRISE IS YOUR JOB", C["gold"], 46), X0 + 400, VIS_Y + 352, q("r1c", "Pick the") - 0.1,
                  anim="pop", dur=0.4))
    return els + caption_elements(sc)


def s_m2(sc, q, src):
    tb = q("r2b")
    t_new, t_hl = q("r2b", "in a brand-new"), q("r2b", "If the facts")
    qn = "When did our town's library open?"
    els = top_bar(2) + header("MOVE 2 OF 5", "Play It\nTwice")
    els += chat(X0, VIS_Y, "Chat 1", qn, "It opened in 1962.", tb + 0.1, "It opened in *1962.*", t_hl)
    els += chat(X0 + 480, VIS_Y, "New chat", qn, "It first opened in 1958.", t_new, "It first opened in *1958.*", t_hl)
    els.append(El(stamp("FACTS CHANGED = GUESSING", C["pink"], 44), RW / 2 - 330, VIS_Y + 420, t_hl + 0.1,
                  anim="pop", dur=0.4))
    return els + caption_elements(sc)


def s_m3(sc, q, src):
    tb = q("r3b")
    t2, td = q("r3b", "Then, in a new chat"), q("r3b", "If it agrees")
    els = top_bar(3) + header("MOVE 3 OF 5", "Flip the\nKey")
    els += chat(X0, VIS_Y, "Chat 1", "Why is morning study better?", "Great question! Morning is better because...",
                tb + 0.1)
    els += chat(X0 + 480, VIS_Y, "New chat", "Why is night study better?", "Great question! Night is better because...",
                t2)
    els.append(El(stamp("IT AGREED BOTH TIMES", C["pink"], 46), RW / 2 - 300, VIS_Y + 420, td + 0.1, anim="pop",
                  dur=0.4))
    return els + caption_elements(sc)


def s_m4(sc, q, src):
    tb = q("r4b")
    els = top_bar(4) + header("MOVE 4 OF 5", "Find the\nSheet Music")
    rw, rh = 680, 470
    r = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    rd = ImageDraw.Draw(r)
    zig = 20
    pts = [(0, 0), (rw, 0), (rw, rh - zig)] + [(i * zig, rh - (zig if i % 2 == 0 else 0)) for i in
                                                range(rw // zig, -1, -1)]
    rd.polygon(pts, fill=rgba(C["paper"]))
    head = text_img("FACT  RECEIPT", 50, 800, color=C["ink"])
    r.alpha_composite(head, ((rw - head.width) // 2, 36))
    for xx in range(44, rw - 44, 20):
        rd.line([(xx, 122), (xx + 10, 122)], fill=(160, 166, 176), width=3)
    items = ["Found a real source", "Opened it myself", "Saw the exact line"]
    for i, it in enumerate(items):
        y = 150 + i * 92
        rd.rounded_rectangle([44, y, 96, y + 52], 10, outline=(120, 130, 145), width=4)
        r.alpha_composite(text_img(it, 36, 600, color=C["ink"]), (120, y + 6))
    rx, ry = (RW - rw) // 2, VIS_Y
    els.append(El(shadowed(r, alpha=0.5), rx, ry, tb))
    for i, sub in enumerate(("find it in a real", "source yourself", "No receipt")):
        els.append(El(check_icon(60, C["teal"], C["white"]), rx + 40, ry + 146 + i * 92, q("r4b", sub) - 0.2,
                      anim="pop", dur=0.3))
    rule = pill("No receipt? Don't repeat it.", 38, 800, fg=C["white"], bg=C["crimson"], padx=28, pady=12)
    els.append(El(rule, RW / 2 - rule.width / 2, ry + rh + 22, q("r4b", "No receipt"), anim="pop", dur=0.35))
    return els + caption_elements(sc)


def s_m5(sc, q, src):
    t_run0 = q("r5b", "explain it")
    t_stuck = q("r5b", "Where you get stuck")
    t_run1 = sc["dur"] - 0.4
    els = top_bar(5) + header("MOVE 5 OF 5", "Play It\nBy Ear")
    ring = 440
    rx, ry = (RW - ring) // 2, VIS_Y

    def timer(frame, t, op):
        p = clamp01((t - t_run0) / (t_run1 - t_run0))
        col = C["gold"] if t >= t_stuck else C["teal"]
        paste(frame, arc_ring(ring, 1 - p, col, width=28), rx, ry, op)
        txt = text_img(f"0:{int(round(30 * (1 - p))):02d}", 110, 800)
        paste(frame, txt, rx + (ring - txt.width) / 2, ry + (ring - txt.height) / 2 - 8, op)

    els.append(Dyn(timer, q("r5b"), fadein=0.3))
    a = pill("Close the tab. Explain it out loud.", 34, 800, fg=C["text"], bg=None, outline=C["teal"])
    els.append(El(a, RW / 2 - a.width / 2, ry + ring + 30, q("r5b") + 0.2, t_stuck - 0.1))
    b = pill("Stuck? That's what to learn next.", 34, 800, fg=C["navy"], bg=C["gold"])
    els.append(El(b, RW / 2 - b.width / 2, ry + ring + 30, t_stuck + 0.1))
    return els + caption_elements(sc)


def s_clipB(sc, q, src):
    clip = sc["items"][0]
    els = top_bar() + header("EXPERIMENT LIKE THIS", "That's how you\n*experiment.*", t0=0.0, size=96)
    els += clip_elements(src, clip["segs"], clip["start"])
    return els + caption_elements(sc)


def s_challenge(sc, q, src):
    els = top_bar() + header("YOUR TURN", "Can you make\nan AI *flip?*", label_bg=C["gold"])

    def step(n, text, extra=None):
        c = card(920, 120 if not extra else 190, fill=C["slate"])
        b = circle(68, fill=rgba(C["gold"]))
        num = text_img(str(n), 40, 800, color=C["navy"])
        b.alpha_composite(num, ((68 - num.width) // 2, (68 - num.height) // 2 + 1))
        c.alpha_composite(b, (26, 26))
        c.alpha_composite(text_img(text, 38, 700, max_w=780), (118, 34))
        if extra:
            x = 118
            for e in extra:
                c.alpha_composite(e, (x, 106))
                x += e.width + 18
        return shadowed(c, blur=16, alpha=0.4)

    fl = pill("FLIPPED", 36, 800, fg=C["white"], bg=C["crimson"], padx=24, pady=10)
    hd = pill("HELD", 36, 800, fg=C["navy"], bg=C["teal"], padx=24, pady=10)
    els.append(El(step(1, "Chat 1: “Why are cats better?”"), X0, VIS_Y + 10, q("rc2")))
    els.append(El(step(2, "New chat: “Why are dogs better?”"), X0, VIS_Y + 150, q("rc2", "Then, in a new")))
    els.append(El(step(3, "Comment your result", [fl, hd]), X0, VIS_Y + 290, q("rc3", "Comment")))
    banner = rrect(920, 84, 22, fill=rgba(C["slate"]), outline=rgba(C["crimson"]), ow=3)
    banner.alpha_composite(lock_icon(38, C["pink"]), (30, 22))
    banner.alpha_composite(text_img("No names or personal details", 36, 700), (88, 18))
    els.append(El(banner, X0, VIS_Y + 506, q("rc3", "no names")))
    foot = text_img("13+  ·  Use AI tools your school or guardian approved", 26, 600, color=C["muted"])
    els.append(El(foot, X0, 640, q("rc2"), dy=0))
    return els + caption_elements(sc)


def s_outro(sc, q, src):
    t2 = q("ro2")
    D = sc["dur"]
    els = top_bar()
    els.append(El(pill("BY THE WAY", 30, 800, fg=C["navy"], bg=C["gold"]), RW / 2, 520, q("ro1"), t2 - 0.3,
                  center=True))
    els.append(El(text_img("This voice was\nmade by *AI.*", 104, 800, align="center", lh=1.04), RW / 2, 610,
                  q("ro1", "Made by"), t2 - 0.3, center=True))
    els.append(El(text_img("Now you know how\nto question it.", 56, 700, color=C["teal"], align="center"), RW / 2, 880,
                  q("ro1", "Now you know"), t2 - 0.3, center=True))
    els.append(El(wordmark(150), RW / 2, 640, t2, D - 0.5, center=True, fade=0.5))
    els.append(El(text_img("Follow for more\nAI literacy moves", 60, 800, align="center"), RW / 2, 860, t2 + 0.2,
                  D - 0.5, center=True, fade=0.5))
    els.append(El(text_img("tomoclub.org", 42, 600, color=C["muted"]), RW / 2, 1040, t2 + 0.4, D - 0.5, center=True,
                  fade=0.5))
    return els + caption_elements(sc)


BUILDERS = {"hook": s_hook, "m1": s_m1, "m2": s_m2, "m3": s_m3, "m4": s_m4, "m5": s_m5, "clipB": s_clipB,
            "challenge": s_challenge, "outro": s_outro}


# ---------------------------------------------------------------- render

@functools.lru_cache(maxsize=None)
def bg():
    return background(RW, RH)


def elements(sc, src):
    els = BUILDERS[sc["id"]](sc, Cues(sc), src)
    if sc["id"] == "hook":
        els += caption_elements(sc)
    for e in els:
        if e.t1 is None:
            e.t1, e.fade = sc["dur"] - 0.3, 0.26
    return els


def frame_at(els, t):
    f = bg().copy()
    for e in els:
        e.draw(f, t)
    return f


def render_scene(args):
    i, sc, src, work = args
    out = os.path.join(work, "scenes", f"{i:02d}_{sc['id']}.mp4")
    els = elements(sc, src)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "10",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    t0 = time.time()
    for n in range(sc["frames"]):
        p.stdin.write(frame_at(els, n / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return f"{sc['id']}: {sc['frames']} frames in {time.time() - t0:.0f}s"


def cover(out):
    img = bg().copy().convert("RGBA")
    img.alpha_composite(wordmark(56), ((RW - wordmark(56).width) // 2, 330))
    t = text_img("*5 AI MOVES*\nto out-think\nthe machine", 128, 800, align="center", lh=1.02)
    img.alpha_composite(t, ((RW - t.width) // 2, 440))
    cell, cols, rows, pad = 80, 9, 5, 20
    gw, gh = cols * cell + 2 * pad, rows * cell + 2 * pad
    grid = rrect(gw, gh, 24, fill=rgba(C["white"]))
    d = ImageDraw.Draw(grid)
    for c in range(cols + 1):
        d.line([(pad + c * cell, pad), (pad + c * cell, pad + rows * cell)], fill=(226, 230, 236), width=2)
    for r in range(rows + 1):
        d.line([(pad, pad + r * cell), (pad + cols * cell, pad + r * cell)], fill=(226, 230, 236), width=1)
    pitch_col = {4: PITCH[7], 2: PITCH[5], 0: PITCH[3]}
    for k, r in enumerate([4, 2, 0, 4, 2, 0, 4, 2]):
        grid.alpha_composite(note_block(cell - 10, cell - 10, pitch_col[r], r=9), (pad + k * cell + 5, pad + r * cell + 5))
    grid.alpha_composite(Image.new("RGBA", (cell, rows * cell), rgba(C["gold"], 90)), (pad + 8 * cell, pad))
    q = text_img("?", 110, 800, color=C["gold"])
    grid.alpha_composite(q, (pad + 8 * cell + (cell - q.width) // 2, pad + int(1.1 * cell)))
    sg, p = shadowed(grid, blur=24, alpha=0.6)
    gx, gy = (RW - gw) // 2, 900
    img.alpha_composite(sg, (gx - p, gy - p))
    tag = pill("Think like a musician", 44, 800, fg=C["navy"], bg=C["teal"], padx=34, pady=16)
    img.alpha_composite(tag, ((RW - tag.width) // 2, 1430))
    img.convert("RGB").save(out, quality=92)


def main():
    mode = sys.argv[1]
    if mode == "tts":
        return tts(*sys.argv[2:5])
    if mode == "cover":
        return cover(sys.argv[2])
    src, work = sys.argv[2:4]
    if mode == "audio":
        return soundtrack(src, work)
    tl = timeline(work)
    if mode == "preview":
        sc = next(s for s in tl if s["id"] == sys.argv[4])
        os.makedirs(os.path.join(work, "preview"), exist_ok=True)
        els = elements(sc, src)
        last = 0
        for t in sorted(float(x) for x in sys.argv[5:]):
            for n in range(last, int(t * FPS)):   # clips stream frames in order
                frame_at(els, n / FPS)
            last = int(t * FPS)
            path = os.path.join(work, "preview", f"{sc['id']}_{t:05.2f}.png")
            frame_at(els, t).save(path)
            print(path)
    elif mode == "scenes":
        os.makedirs(os.path.join(work, "scenes"), exist_ok=True)
        only = set(sys.argv[4:])
        jobs = [(i, s, src, work) for i, s in enumerate(tl) if not only or s["id"] in only]
        jobs.sort(key=lambda j: -j[1]["frames"])
        with multiprocessing.Pool(4) as pool:
            for msg in pool.imap_unordered(render_scene, jobs):
                print(msg, flush=True)
    elif mode == "final":
        out = sys.argv[4]
        lst = os.path.join(work, "scenes", "list.txt")
        with open(lst, "w") as f:
            for i, s in enumerate(tl):
                f.write(f"file '{i:02d}_{s['id']}.mp4'\n")
        # Instagram Reels: H.264 High, 1080x1920, 30 fps, AAC 48 kHz stereo, faststart.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-i", os.path.join(work, "soundtrack.wav"), "-map", "0:v", "-map", "1:a",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "8M", "-bufsize", "16M",
                        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "60",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
                        "-shortest", out], check=True)
        print("wrote", out)


if __name__ == "__main__":
    main()
