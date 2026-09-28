#!/usr/bin/env python3
"""Render the TAICY Round 2 Instagram Reel (1080x1920, 9:16) from the Zoom recording.

    python3 reel.py --source "../parent-highlight-taicy-round2/source/TAICY Round 2.mp4"

Word timings for the pop captions come from faster-whisper and are cached in
reel_words.json (delete it after changing a shot's a_in/a_out or text).
Output: out/ (Reel, a no-music version for adding an in-app sound, cover image).
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "parent-highlight-taicy-round2"))
import graphics as g  # noqa: E402  (brand fonts, colours, wordmark)
from render import FF, measure_lufs, run  # noqa: E402

import music  # noqa: E402

W, H = 1080, 1920
FY = 490            # footage square: y 490..1570
HEAD_Y = 236        # headline band: y 236..476
CAP_Y = 1236        # caption band top
PILL_Y = 1172
SR = 48000

EDL = json.load(open(os.path.join(HERE, "reel.json")))
FPS = EDL["output"]["fps"]

# Zoom layout of the recording (2560x1440): three 1280x720 tiles.
SQUARE = {"vk": (1593, 0), "vedant": (229, 0), "sudeep": (947, 720)}   # 720x720 face crops
BANDS = [(1280, 100), (0, 82), (640, 921)]                              # 1280x294 bands: VK, Vedant, Sudeep
BAND_H = 248  # three bands fill the top 744 px of the square, so captions never cover a face
WHO = {
    "coach": ("COACH VK", g.GOLD, g.NAVY),
    "vedant": ("VEDANT", g.TEAL, g.NAVY),
    "sudeep": ("SUDEEP", g.TEAL, g.NAVY),
    "student": ("STUDENT", g.TEAL, g.NAVY),
    "play": ("LIVE GAMEPLAY", g.SLATE, g.WHITE),
}


# ------------------------------------------------------------------ graphics

def vbackground():
    img = Image.new("RGBA", (W, H))
    grad = Image.new("RGBA", (1, H))
    for y in range(H):
        t = y / (H - 1)
        grad.putpixel((0, y), tuple(int(g.DEEP[i] + (g.NAVY[i] - g.DEEP[i]) * t) for i in range(3)) + (255,))
    img = grad.resize((W, H))
    img.alpha_composite(g.radial_glow((W, H), (120, 140), 520, g.TEAL, 60))
    img.alpha_composite(g.radial_glow((W, H), (1000, 1800), 560, g.GOLD, 40))
    img.alpha_composite(g.radial_glow((W, H), (1080, 420), 380, g.CRIMSON, 40))
    hexes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(hexes)
    for cx, cy, r, a in [(980, 1760, 170, 16), (90, 1700, 120, 12), (1040, 130, 90, 12), (40, 330, 70, 10)]:
        d.polygon(g.hexagon(cx, cy, r), outline=(255, 255, 255, a), width=3)
    img.alpha_composite(hexes)
    d = ImageDraw.Draw(img)
    g.wordmark(d, (W // 2, 176), 46, anchor="mt")
    return img


def frame_overlay():
    """Soft edges and a caption scrim over the footage square (transparent elsewhere)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scrim = Image.new("L", (1, 1080))
    for y in range(1080):
        t = (y - 600) / 480
        scrim.putpixel((0, y), int(200 * max(0, min(1, t)) ** 1.3))
    black = Image.new("RGBA", (W, 1080), (8, 13, 27, 255))
    black.putalpha(scrim.resize((W, 1080)))
    img.alpha_composite(black, (0, FY))
    d = ImageDraw.Draw(img)
    d.line([0, FY, W, FY], fill=g.TEAL + (200,), width=4)
    return img


def rich_words(text):
    """'a *b c*' -> [('a', False), ('b', True), ('c', True)]."""
    out, gold = [], False
    for tok in text.split():
        start = tok.startswith("*")
        end = tok.endswith("*")
        if start:
            gold = True
        out.append((tok.strip("*"), gold))
        if end:
            gold = False
    return out


def headline_png(text):
    """Headline in up to two centred lines; '|' forces a line break, *word* is gold."""
    img = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for size in (74, 68, 62, 56):
        f = g.font(800, size)
        lines = []
        for part in text.split("|"):
            cur = []
            for w in rich_words(part):
                trial = cur + [w]
                if d.textlength(" ".join(x for x, _ in trial), font=f) <= 960 or not cur:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = [w]
            lines.append(cur)
        if len(lines) <= 2:
            break
    lh = int(size * 1.12)
    y = (240 - lh * len(lines)) // 2
    for line in lines:
        tw = d.textlength(" ".join(x for x, _ in line), font=f)
        x = (W - tw) / 2
        for word, gold in line:
            d.text((x, y), word, font=f, fill=g.GOLD if gold else g.WHITE, stroke_width=3, stroke_fill=g.DEEP)
            x += d.textlength(word + " ", font=f)
        y += lh
    return img


def pill_png(who):
    label, fill, fg = WHO[who]
    img = Image.new("RGBA", (W, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    g.pill(d, W / 2, 8, label, fill, fg, size=22, pad_x=20, h=44, anchor="m")
    return img


CAP_FONT = (800, 66)
CAP_W = 940


def chunk_words(words):
    """Group words into 1-2 line pop-caption chunks."""
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    f = g.font(*CAP_FONT)
    chunks, cur = [], []
    for i, w in enumerate(words):
        trial = cur + [w]
        if cur and not two_lines(d, [x["w"] for x in trial], f):
            chunks.append(cur)
            trial = [w]
        cur = trial
        if (w["w"][-1] in ".?!" and len(cur) >= 2) or len(cur) >= 6:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def two_lines(d, ws, f):
    s = " ".join(ws)
    if d.textlength(s, font=f) <= CAP_W:
        return [ws]
    for i in range(len(ws) - 1, 0, -1):
        a, b = ws[:i], ws[i:]
        if d.textlength(" ".join(a), font=f) <= CAP_W and d.textlength(" ".join(b), font=f) <= CAP_W:
            # balance: move words down while the top stays longer
            while len(a) > 1 and d.textlength(" ".join(a[:-1]), font=f) >= d.textlength(" ".join([a[-1]] + b), font=f):
                a, b = a[:-1], [a[-1]] + b
            return [a, b]
    return None


def caption_png(chunk, hi):
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    f = g.font(*CAP_FONT)
    lines = two_lines(d0, [w["w"] for w in chunk], f) or [[w["w"] for w in chunk]]
    img = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 8 if len(lines) == 2 else 48
    k = 0
    for line in lines:
        tw = d.textlength(" ".join(line), font=f)
        x = (W - tw) / 2
        for word in line:
            col = g.GOLD if k == hi else g.WHITE
            d.text((x, y), word, font=f, fill=col, stroke_width=7, stroke_fill=(8, 13, 27))
            x += d.textlength(word + " ", font=f)
            k += 1
        y += 82
    return img


def cta_layers(out):
    base = vbackground()
    base.save(f"{out}/cta_0.png")
    layers = [("cta_0.png", 0.0)]

    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    d.text((W / 2, 470), "Want this for", font=g.font(800, 96), fill=g.WHITE, anchor="mt")
    d.text((W / 2, 580), "your child?", font=g.font(800, 96), fill=g.GOLD, anchor="mt")
    l.save(f"{out}/cta_1.png"); layers.append(("cta_1.png", 0.1))

    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    f = g.font(700, 58)
    a, b = "Their first class is ", "FREE"
    tw = d.textlength(a + b, font=f)
    x = (W - tw) / 2
    d.text((x, 760), a, font=f, fill=g.WHITE)
    d.text((x + d.textlength(a, font=f), 760), b, font=f, fill=g.GOLD)
    l.save(f"{out}/cta_2.png"); layers.append(("cta_2.png", 0.6))

    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    bw, bh = 820, 132
    bx, by = (W - bw) // 2, 890
    d.rounded_rectangle([bx, by + 8, bx + bw, by + bh + 8], bh // 2, fill=(150, 110, 10, 255))
    d.rounded_rectangle([bx, by, bx + bw, by + bh], bh // 2, fill=g.GOLD)
    fc = g.font(800, 56)
    label = "Book a free trial"
    tw = d.textlength(label, font=fc)
    tx = bx + (bw - tw - 56) / 2
    d.text((tx, by + bh / 2 + 2), label, font=fc, fill=g.NAVY, anchor="lm")
    ax, ay = tx + tw + 24, by + bh / 2 + 2
    d.line([ax, ay, ax + 32, ay], fill=g.NAVY, width=7)
    d.line([ax + 18, ay - 14, ax + 33, ay, ax + 18, ay + 14], fill=g.NAVY, width=7, joint="curve")
    l.save(f"{out}/cta_3.png"); layers.append(("cta_3.png", 1.0))

    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    d.text((W / 2, 1090), "Link in bio", font=g.font(800, 50), fill=g.WHITE, anchor="mt")
    d.text((W / 2, 1162), "tomoclub.org/parents", font=g.font(700, 46), fill=g.TEAL_TEXT, anchor="mt")
    l.save(f"{out}/cta_4.png"); layers.append(("cta_4.png", 1.4))

    l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    d.text((W / 2, 1282), "Live · Coach-led · Grades 3–8", font=g.font(600, 38), fill=(203, 213, 225), anchor="mt")
    d.text((W / 2, 1340), "Trial is free · No commitment", font=g.font(600, 36), fill=g.TEAL_TEXT, anchor="mt")
    d.text((W / 2, 1420), "info@tomoclub.org  ·  +1 650 547-8082", font=g.font(400, 32), fill=g.MUTED, anchor="mt")
    l.save(f"{out}/cta_5.png"); layers.append(("cta_5.png", 1.8))
    return layers


# ------------------------------------------------------------------ word timing

def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def word_timings(shots, audio):
    """Caption words with start times (seconds from the shot start), cached in reel_words.json."""
    cache_p = os.path.join(HERE, "reel_words.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    model = None
    for s in shots:
        if "card" in s:
            continue
        key = f"{s['id']}|{s['a_in']}|{s['a_out']}|{s['text']}"
        if key in cache:
            s["words"] = cache[key]
            continue
        if model is None:
            from faster_whisper import WhisperModel
            model = WhisperModel("medium.en", device="cpu", compute_type="int8")
        seg = audio[int(s["a_in"] * 16000):int(s["a_out"] * 16000)]
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
        for i in range(1, len(times)):  # interpolate unmatched words
            if times[i] is None or times[i] <= times[i - 1]:
                nxt = next((t for t in times[i + 1:] if t is not None and t > times[i - 1]), dur)
                gap = next((j for j in range(i + 1, len(times)) if times[j] is not None and times[j] > times[i - 1]), len(times))
                times[i] = times[i - 1] + (nxt - times[i - 1]) / (gap - i + 1)
        s["words"] = [{"w": w, "t": round(float(t), 3)} for w, t in zip(cap, times)]
        cache[key] = s["words"]
        print(f"  timed {s['id']}: " + " ".join(f"{w['w']}@{w['t']:.2f}" for w in s["words"]))
    json.dump(cache, open(cache_p, "w"), indent=0)


# ------------------------------------------------------------------ rendering

VENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-level:v", "4.1", "-g", str(FPS * 2), "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-r", str(FPS)]


def footage_filter(s, dur):
    """Source frames -> 1080x1080 square for the shot's view, with a slow punch-in zoom."""
    zoom = f"scale=w='trunc(1080*(1+0.07*t/{dur:.3f})/2)*2':h=-2:eval=frame:flags=bicubic,crop=1080:1080"
    if s["view"] == "grid":
        parts = ["[0:v]setpts=PTS-STARTPTS,fps=%d,split=3[g0][g1][g2]" % FPS]
        for i, (x, y) in enumerate(BANDS):
            parts.append(f"[g{i}]crop=1280:294:{x}:{y},scale=1080:{BAND_H}:flags=lanczos[b{i}]")
        parts.append(f"[b0][b1][b2]vstack=inputs=3,pad=1080:1080:0:0:color=0x080D1B[foot]")
        return ";".join(parts)
    if s["view"] == "game":
        cx = s.get("cx", 1280)
        crop = f"crop=1440:1440:{cx - 720}:0"
    else:
        x, y = SQUARE[s["view"]]
        crop = f"crop=720:720:{x}:{y}"
    return f"[0:v]setpts=PTS-STARTPTS,fps={FPS},{crop},scale=1080:1080:flags=lanczos,{zoom}[foot]"


def render_shot(s, src, gdir, seg, head_png, head_new, pill_png_path, caps):
    dur = s["a_out"] - s["a_in"]
    v_in = s.get("v_in", s["a_in"])
    args = ["-ss", f"{v_in:.3f}", "-t", f"{dur:.3f}", "-i", src]
    imgs = [os.path.join(gdir, "bg.png"), os.path.join(gdir, "frame.png"), head_png, pill_png_path] + [c["png"] for c in caps]
    for p in imgs:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", p]
    fc = footage_filter(s, dur)
    fc += f";[1:v][foot]overlay=0:{FY}[a0];[a0][2:v]overlay=0:0[a1]"
    if head_new:
        fc += (f";[3:v]format=rgba,fade=t=in:st=0:d=0.22:alpha=1[hd];"
               f"[a1][hd]overlay=0:'{HEAD_Y}+34*max(0,1-t/0.22)'[a2]")
    else:
        fc += f";[a1][3:v]overlay=0:{HEAD_Y}[a2]"
    grid = s["view"] == "grid"  # grid faces fill the top 744 px: pill and captions sit just below them
    pill_y, cap_y = (FY + 3 * BAND_H + 10, FY + 3 * BAND_H + 62) if grid else (PILL_Y, CAP_Y)
    fc += f";[a2][4:v]overlay=0:{pill_y}[a3]"
    cur = "[a3]"
    for k, c in enumerate(caps):
        nxt = f"[c{k}]"
        fc += f";{cur}[{5 + k}:v]overlay=0:{cap_y}:enable='between(t,{c['t0']:.3f},{c['t1'] - 0.001:.3f})'{nxt}"
        cur = nxt
    fc += f";{cur}format=yuv420p[vout]"
    run(args + ["-filter_complex", fc, "-map", "[vout]", "-an", "-t", f"{dur:.3f}"] + VENC + [seg])


def render_card(layers, dur, gdir, seg):
    args = []
    for p, _ in layers:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", os.path.join(gdir, p)]
    fc = "[0:v]format=rgba[l0]"
    cur = "[l0]"
    for k, (_, t_in) in enumerate(layers[1:], start=1):
        fc += (f";[{k}:v]format=rgba,fade=t=in:st={t_in:.2f}:d=0.3:alpha=1[f{k}];"
               f"{cur}[f{k}]overlay=0:'30*max(0,1-(t-{t_in:.2f})/0.3)*gte(t,{t_in:.2f})'[m{k}]")
        cur = f"[m{k}]"
    fc += f";{cur}fade=t=out:st={dur - 0.5:.3f}:d=0.5,format=yuv420p[vout]"
    run(args + ["-filter_complex", fc, "-map", "[vout]", "-t", f"{dur:.3f}"] + VENC + [seg])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--build", default=os.path.join(HERE, "build"))
    ap.add_argument("--only", help="comma-separated shot ids (quick checks)")
    ap.add_argument("--keep", action="store_true", help="reuse segments that already exist in the build folder")
    a = ap.parse_args()
    shots = EDL["shots"]
    gdir, sdir = os.path.join(a.build, "gfx"), os.path.join(a.build, "segments")
    os.makedirs(gdir, exist_ok=True)
    os.makedirs(sdir, exist_ok=True)
    out = os.path.join(HERE, EDL["output"]["file"])
    os.makedirs(os.path.dirname(out), exist_ok=True)

    # whole-frame durations keep the concatenated video at a constant frame rate
    for s in shots:
        if "card" in s:
            s["dur"] = round(s["dur"] * FPS) / FPS
        else:
            s["a_out"] = round(s["a_in"] + round((s["a_out"] - s["a_in"]) * FPS) / FPS, 4)

    npy = os.path.splitext(a.source)[0] + ".mono16000.npy"
    if os.path.exists(npy):
        audio = np.load(npy)
    else:
        raw = subprocess.run([FF, "-v", "error", "-i", a.source, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                             capture_output=True, check=True).stdout
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
        np.save(npy, audio)
    word_timings(shots, audio)

    vbackground().save(os.path.join(gdir, "bg.png"))
    frame_overlay().save(os.path.join(gdir, "frame.png"))
    cta = cta_layers(gdir)

    only = set(a.only.split(",")) if a.only else None
    segs, t, head, head_png = [], 0.0, None, None
    marks = {}
    for n, s in enumerate(shots):
        seg = os.path.join(sdir, f"{n:02d}_{s['id']}.mov")
        if "card" in s:
            if (not only or s["id"] in only) and not (a.keep and os.path.exists(seg)):
                render_card(cta, s["dur"], gdir, seg)
            marks["cta"] = t
            t += s["dur"]
            segs.append(seg)
            continue
        dur = s["a_out"] - s["a_in"]
        head_new = bool(s.get("head")) and s.get("head") != head
        if s.get("head"):
            head = s["head"]
            head_png = os.path.join(gdir, f"head_{n:02d}.png")
            headline_png(head).save(head_png)
        pp = os.path.join(gdir, f"pill_{s['who']}.png")
        pill_png(s["who"]).save(pp)
        caps = []
        for ci, chunk in enumerate(chunk_words(s["words"])):
            nxt_chunk_t = None
            idx = s["words"].index(chunk[-1]) + 1
            if idx < len(s["words"]):
                nxt_chunk_t = s["words"][idx]["t"]
            for wi, w in enumerate(chunk):
                t0 = 0.0 if (ci == 0 and wi == 0) else w["t"]
                t1 = chunk[wi + 1]["t"] if wi + 1 < len(chunk) else (nxt_chunk_t if nxt_chunk_t is not None else dur)
                p = os.path.join(gdir, f"cap_{n:02d}_{ci}_{wi}.png")
                caption_png(chunk, wi).save(p)
                caps.append({"png": p, "t0": t0, "t1": min(t1, dur)})
        if s["id"] == "stuck-1":
            marks["break0"] = t
        if s["id"] == "voice-1":
            marks["break1"] = t
        if (not only or s["id"] in only) and not (a.keep and os.path.exists(seg)):
            render_shot(s, a.source, gdir, seg, head_png, head_new, pp, caps)
        print(f"  [{n + 1:2}/{len(shots)}] {s['id']:10} {dur:5.2f}s @ {t:6.2f}s", flush=True)
        segs.append(seg)
        t += dur
    total = t
    if only:
        return

    # video
    lst = os.path.join(a.build, "concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in segs)
    video = os.path.join(a.build, "video.mov")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    # voices: each shot's words, loudness-matched, on the same timeline
    parts = []
    for s in shots:
        if "card" in s:
            continue
        dur = s["a_out"] - s["a_in"]
        if s.get("joined"):  # continues the previous shot's sentence: same gain, no fades at the join
            gain = prev["_gain"]
            prev["_fo"] = 0
        else:
            lufs = measure_lufs_range(a.source, s["a_in"], dur)
            gain = max(min(-18.0 - lufs, 12.0), -12.0)
        fo = s.get("fade_out", 0.03)
        s["_fi"] = 0 if s.get("joined") else 0.02
        prev = s
        parts += ["-ss", f"{s['a_in']:.3f}", "-t", f"{dur:.3f}", "-i", a.source]
        s["_gain"], s["_fo"], s["_dur"] = gain, fo, dur
    chains, labels, idx = [], [], 0
    for k, s in enumerate(shots):
        if "card" in s:
            chains.append(f"anullsrc=r={SR}:cl=stereo,atrim=0:{s['dur']:.4f},asetpts=PTS-STARTPTS[v{k}]")
        else:
            chains.append(f"[{idx}:a]asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo,"
                          f"pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,highpass=f=90,volume={s['_gain']:.2f}dB,"
                          f"acompressor=threshold=-20dB:ratio=3:attack=5:release=150:makeup=1.5,"
                          + (f"afade=t=in:d={s['_fi']}," if s["_fi"] else "")
                          + (f"afade=t=out:st={s['_dur'] - s['_fo']:.3f}:d={s['_fo']:.3f}," if s["_fo"] else "")
                          + f"apad=whole_dur={s['_dur']:.4f},atrim=0:{s['_dur']:.4f}[v{k}]")
            idx += 1
        labels.append(f"[v{k}]")
    voice = os.path.join(a.build, "voice.wav")
    run(parts + ["-filter_complex", ";".join(chains) + ";" + "".join(labels) + f"concat=n={len(shots)}:v=0:a=1[vo]",
                 "-map", "[vo]", "-c:a", "pcm_s16le", voice])

    # music, arranged to the edit: breakdown under "stuck", riser into the CTA
    mus = os.path.join(a.build, "music.wav")
    music.make_track(mus, total, marks["cta"], breakdown=(marks["break0"], marks["break1"]))

    I, TP = EDL["output"]["loudness_lufs"], EDL["output"]["true_peak_db"]
    for variant, with_music in (("", True), ("_no-music", False)):
        mix = os.path.join(a.build, f"mix{variant}.wav")
        if with_music:
            fc = (f"[1:a]volume=-9dB,highshelf=f=6000:g=2[m];[0:a]asplit=2[vo][sc];"
                  f"[m][sc]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=350:makeup=1[md];"
                  f"[vo][md]amix=inputs=2:duration=first:normalize=0[mx]")
            run(["-i", voice, "-i", mus, "-filter_complex", fc, "-map", "[mx]", "-c:a", "pcm_s24le", mix])
        else:
            run(["-i", voice, "-c:a", "pcm_s24le", mix])
        err = run(["-i", mix, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"])
        js = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
        ln = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
              f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
        mastered = os.path.join(a.build, f"master{variant}.wav")
        run(["-i", mix, "-af", ln + f",aresample={SR}", "-c:a", "pcm_s24le", mastered])
        got = measure_lufs(mastered)
        if abs(got - I) > 0.5:
            fixed = mastered.replace(".wav", "_fix.wav")
            run(["-i", mastered, "-af", f"volume={I - got:.2f}dB,alimiter=limit={10 ** (TP / 20):.4f}:level=false",
                 "-c:a", "pcm_s24le", fixed])
            mastered = fixed
        dst = out.replace(".mp4", f"{variant}.mp4")
        run(["-i", video, "-i", mastered, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-ar", str(SR), "-movflags", "+faststart", "-metadata", f"title={EDL['title']}",
             "-metadata", "copyright=© 2026 TomoClub", dst])
        print(f"{dst}  {total:.1f}s  {measure_lufs(dst):.1f} LUFS")

    cover(a.source, gdir, out.replace(".mp4", "_cover.jpg"))


def measure_lufs_range(src, t0, dur):
    err = run(["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", src, "-vn", "-af", "ebur128", "-f", "null", "-"])
    tail = err[err.rfind("Summary:"):]
    for line in tail.splitlines():
        if line.strip().startswith("I:"):
            v = float(line.split()[1])
            return v if v > -70 else -23.0
    return -23.0


def cover(src, gdir, path):
    """Reel cover: the three faces, the hook headline and the wordmark."""
    tmp = os.path.join(gdir, "cover_src.png")
    run(["-ss", "178.9", "-i", src, "-frames:v", "1", tmp])
    fr = Image.open(tmp).convert("RGB")
    bands = [fr.crop((x, y, x + 1280, y + 294)).resize((1080, BAND_H), Image.LANCZOS) for x, y in BANDS]
    img = Image.open(os.path.join(gdir, "bg.png")).convert("RGBA")
    img.paste((8, 13, 27), (0, FY, W, FY + 1080))
    for i, b in enumerate(bands):
        img.paste(b, (0, FY + i * BAND_H))
    img.alpha_composite(Image.open(os.path.join(gdir, "frame.png")))
    img.alpha_composite(headline_png("This is what screen time *SHOULD* look like"), (0, HEAD_Y))
    d = ImageDraw.Draw(img)
    d.text((W / 2, CAP_Y + 30), "Inside a live TomoClub session", font=g.font(800, 60), fill=g.WHITE,
           anchor="mt", stroke_width=7, stroke_fill=(8, 13, 27))
    img.convert("RGB").save(path, quality=92)


if __name__ == "__main__":
    main()
