"""Brand-neutral video engine: sprites, animation, timeline, session-clip handling, audio synthesis.

Everything brand-specific (palette, type, components, layouts) lives in atc_theme.py and the
scene modules.
"""
import functools
import json
import math
import os
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30
SR = 48000
FONT_DIR = os.environ.get("FONT_DIR", "fonts")


# ---------------------------------------------------------------- type and sprites

@functools.lru_cache(maxsize=None)
def F(size, weight=700, fam="Manrope"):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"{fam}-{weight}.ttf"), int(size))


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def ease(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def clamp01(x):
    return max(0.0, min(1.0, x))


def rrect(w, h, r, fill=None, outline=None, ow=0, ss=3):
    w, h = int(w), int(h)
    img = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], r * ss, fill=fill, outline=outline,
                                          width=int(ow * ss))
    return img.resize((w, h), Image.LANCZOS)


def circle(d, fill=None, outline=None, ow=0, ss=3):
    d = int(d)
    img = Image.new("RGBA", (d * ss, d * ss), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([0, 0, d * ss - 1, d * ss - 1], fill=fill, outline=outline, width=int(ow * ss))
    return img.resize((d, d), Image.LANCZOS)


def _tokens(markup):
    out = []
    for i, part in enumerate(re.split(r"\*", markup)):
        for w in part.split(" "):
            if w:
                out.append((w, i % 2 == 1))
    return out


def text_img(markup, size, weight=700, fam="Manrope", color=(0, 0, 0), accent=None, max_w=None, lh=1.16,
             align="left", tracking=0, accent_weight=None, accent_fam=None):
    """Wrapped text sprite. '\\n' breaks lines; *words* use the accent colour."""
    font = F(size, weight, fam)
    afont = F(size, accent_weight or weight, accent_fam or fam)
    accent = accent or color
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
    img = Image.new("RGBA", (max(1, width), height), (0, 0, 0, 0))
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


def paste(frame, img, x, y, op=1.0):
    if op <= 0.003:
        return
    if op >= 0.997:
        frame.paste(img, (int(x), int(y)), img)
    else:
        frame.paste(img, (int(x), int(y)), img.getchannel("A").point(lambda v: int(v * op)))


def wipe(img, p, line_h):
    """Reveal a text sprite line by line, left to right (typing effect)."""
    p = clamp01(p)
    if p >= 1:
        return img
    lines = max(1, round(img.height / line_h))
    k = p * lines
    full = int(k)
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    if full:
        d.rectangle([0, 0, img.width, full * line_h], fill=255)
    d.rectangle([0, full * line_h, int(img.width * (k - full)), (full + 1) * line_h], fill=255)
    out = img.copy()
    out.putalpha(Image.composite(img.getchannel("A"), mask, mask))
    return out


def arc_ring(size, frac, color, track, width=26):
    ss = 3
    s = size * ss
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = width * ss // 2 + 2
    d.ellipse([pad, pad, s - pad, s - pad], outline=rgba(track), width=width * ss)
    if frac > 0.001:
        d.arc([pad, pad, s - pad, s - pad], -90, -90 + 360 * frac, fill=rgba(color), width=width * ss)
    return img.resize((size, size), Image.LANCZOS)


class El:
    """A sprite that enters at t0 (calm upward / left-to-right move) and leaves at t1."""

    def __init__(self, img, x, y, t0=0.0, t1=None, dur=0.35, dy=24, dx=0, fade=0.3, center=False):
        self.img = img
        if center:
            x -= img.width / 2
        self.x, self.y, self.t0, self.t1, self.dur, self.dy, self.dx, self.fade = x, y, t0, t1, dur, dy, dx, fade

    def draw(self, frame, t):
        if t < self.t0:
            return
        p = (t - self.t0) / self.dur
        e = ease(p)
        op = clamp01(p * 1.4)
        if self.t1 is not None and t > self.t1:
            op *= max(0.0, 1 - (t - self.t1) / self.fade)
        if op > 0:
            paste(frame, self.img, self.x - self.dx * (1 - e), self.y + self.dy * (1 - e), op)


class Dyn:
    """Per-frame callback element: fn(frame, t, op)."""

    def __init__(self, fn, t0=0.0, t1=None, fadein=0.3, fade=0.3):
        self.fn, self.t0, self.t1, self.fadein, self.fade = fn, t0, t1, fadein, fade

    def draw(self, frame, t):
        if t < self.t0:
            return
        op = min(1.0, (t - self.t0) / self.fadein) if self.fadein else 1.0
        if self.t1 is not None and t > self.t1:
            op *= max(0.0, 1 - (t - self.t1) / self.fade)
        if op > 0:
            self.fn(frame, t, op)


# ---------------------------------------------------------------- timeline

def build(work, scenes, clips):
    with open(os.path.join(work, "vo", "durations.json")) as f:
        durations = json.load(f)
    t, out = 0.0, []
    for sc in scenes:
        cues, items, local = {}, [], sc["lead"]
        for it in sc["items"]:
            if it[0] == "vo":
                _, vid, text, gap = it
                d = durations[vid]
                cues[vid] = (local, d, text)
                items.append(dict(kind="vo", id=vid, start=local, dur=d, text=text))
                local += d + gap
            elif it[0] == "pause":
                local += it[1]
            elif it[0] == "clip":
                segs = clips[it[1]]
                d = sum(b - a for a, b in segs)
                items.append(dict(kind="clip", id=it[1], start=local, dur=d, segs=segs))
                local += d
        local += sc["tail"]
        n = math.ceil(local * FPS - 1e-6)
        out.append(dict(id=sc["id"], start=t, dur=n / FPS, frames=n, cues=cues, items=items,
                        bg=sc.get("bg", "ivory")))
        t += n / FPS
    return out


class Cues:
    """When (scene-local seconds) a narration line, or a phrase inside it, is spoken."""

    def __init__(self, scene):
        self.c = scene["cues"]

    def __call__(self, vid, sub=None):
        start, d, text = self.c[vid]
        if sub is None:
            return start
        i = text.find(sub)
        if i < 0:
            raise KeyError(f"{sub!r} not in {vid}")
        return start + d * i / len(text)

    def end(self, vid):
        start, d, _ = self.c[vid]
        return start + d


# ---------------------------------------------------------------- session clips

# Student video tiles in the session recording (source pixels). Already blurred in the source;
# blurred again here so no student can be recognised.
STUDENT_TILES = (1556, 222, 364, 858)


def _blur_filter(size):
    x, y, w, h = STUDENT_TILES
    return (f"[0:v]fps={FPS},split[m][s];[s]crop={w}:{h}:{x}:{y},boxblur=24:3[b];"
            f"[m][b]overlay={x}:{y},scale={size[0]}:{size[1]}:flags=lanczos,format=rgb24")


def clip_frames(src, segs, size):
    fs = size[0] * size[1] * 3
    last = None
    for a, b in segs:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a}", "-i", src, "-t", f"{b - a}",
                              "-filter_complex", _blur_filter(size), "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        for _ in range(round((b - a) * FPS)):
            buf = p.stdout.read(fs)
            if len(buf) == fs:
                last = Image.frombuffer("RGB", size, buf)
            yield last
        p.stdout.close()
        p.wait()


def still(src, t, size):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", src, "-filter_complex", _blur_filter(size),
                          "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return Image.frombuffer("RGB", size, raw)


class ClipPlayer:
    def __init__(self, src, segs, size):
        self.gen = clip_frames(src, segs, size)
        self.idx, self.cur = -1, None

    def at(self, t):
        want = int(round(t * FPS))
        while self.idx < want:
            try:
                self.cur = next(self.gen)
            except StopIteration:
                pass
            self.idx += 1
        return self.cur


# ---------------------------------------------------------------- narration

def tts(model, voices, scenes, work, voice="af_heart", speed=1.04):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    out = os.path.join(work, "vo")
    os.makedirs(out, exist_ok=True)
    k = Kokoro(model, voices)
    durations = {}
    for sc in scenes:
        for it in sc["items"]:
            if it[0] != "vo":
                continue
            spoken = it[2].replace(" - ", ", ")   # spaced hyphens are visual pauses; speak them as commas
            samples, sr = k.create(spoken, voice=voice, speed=speed, lang="en-us")
            idx = np.where(np.abs(samples) > 0.01)[0]
            if len(idx):
                samples = samples[max(0, idx[0] - int(0.04 * sr)): idx[-1] + int(0.04 * sr)]
            sf.write(os.path.join(out, it[1] + ".wav"), samples, sr)
            durations[it[1]] = len(samples) / sr
            print(f"{it[1]}: {durations[it[1]]:.2f}s")
    with open(os.path.join(out, "durations.json"), "w") as f:
        json.dump(durations, f, indent=1)


# ---------------------------------------------------------------- audio

def ff_read(args):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error"] + args + ["-f", "f32le", "-"],
                                        capture_output=True, check=True).stdout, dtype=np.float32)


def lufs(x):
    p = subprocess.run(["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       input=np.ascontiguousarray(x, dtype=np.float32).tobytes(), capture_output=True)
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr.decode())[-1])


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def pluck(f, dur=1.6, bright=1.0):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 4.0)
         + bright * 0.30 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t * 14)
         + bright * 0.08 * np.sin(2 * np.pi * 9.2 * f * t) * np.exp(-t * 30))
    return (s * np.minimum(1, t / 0.004)).astype(np.float32)


def pad_note(f, dur, attack=0.9, release=1.4):
    t = np.arange(int((dur + release) * SR)) / SR
    s = np.zeros_like(t)
    for k, detune in ((1, 0.0), (1, 0.7), (2, 0.3), (3, 0.0), (4, 0.4), (5, 0.0)):
        s += (1 / k ** 1.7) * np.sin(2 * np.pi * (f * k + detune) * t + k)
    env = np.minimum(1, t / attack)
    rel = t > dur
    env[rel] *= np.exp(-(t[rel] - dur) / (release / 3))
    return (s * env * (1 + 0.06 * np.sin(2 * np.pi * 0.21 * t))).astype(np.float32)


def add(buf, sig, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    if sig.ndim == 1:
        buf[i:i + len(sig), 0] += sig * gain * np.sqrt(0.5 * (1 - pan)) * 1.414
        buf[i:i + len(sig), 1] += sig * gain * np.sqrt(0.5 * (1 + pan)) * 1.414
    else:
        buf[i:i + len(sig)] += sig * gain


def smooth(env, secs):
    n = max(1, int(secs * SR))
    return np.convolve(env, np.ones(n, np.float32) / n, mode="same")


# Original I-V-vi-IV loop in G (different from the TomoClub cut on purpose).
CHORDS_G = [[43, 50, 59, 62], [50, 57, 62, 66], [40, 52, 59, 67], [36, 48, 55, 64]]


def music_bed(total, bpm=100, chords=CHORDS_G):
    beat = 60 / bpm
    bar = 4 * beat
    N = int(round(total * SR))
    buf = np.zeros((N + SR * 4, 2), np.float32)
    t, i = 0.0, 0
    arp = [0, 1, 2, 3, 2, 1, 2, 3]
    while t < total:
        ch = chords[i % len(chords)]
        for n in ch:
            add(buf, pad_note(midi(n), bar), t, 0.10, pan=(n - 55) / 40)
        for k, step in enumerate(arp):
            add(buf, pluck(midi(ch[step] + 12), 1.2, 0.6), t + k * beat / 2, 0.05 * (1.0 if k % 2 == 0 else 0.7),
                pan=0.35 if k % 2 else -0.35)
        t += bar
        i += 1
    return buf[:N]


def mix_soundtrack(tl, src, work, cue_fx, bpm=100, bed_lufs=-32.0):
    """Narration + session-clip audio + music bed (ducked under speech, off during clips) + cue sounds.
    cue_fx(fx_buffer, timeline) adds scene-specific sound effects and returns the bed start time."""
    total = tl[-1]["start"] + tl[-1]["dur"]
    N = int(round(total * SR))
    vo, clips, fx = (np.zeros((N, 2), np.float32) for _ in range(3))
    vo_on, clip_on = np.zeros(N, np.float32), np.zeros(N, np.float32)
    for sc in tl:
        for it in sc["items"]:
            t0 = sc["start"] + it["start"]
            i = int(t0 * SR)
            if it["kind"] == "vo":
                x = ff_read(["-i", os.path.join(work, "vo", it["id"] + ".wav"), "-ar", str(SR), "-ac", "1"])
                add(vo, x, t0)
                vo_on[i:i + len(x)] = 1
            else:
                off = 0.0
                for a, b in it["segs"]:
                    x = ff_read(["-ss", f"{a}", "-t", f"{b - a}", "-i", src, "-vn", "-ar", str(SR), "-ac", "2"])
                    x = x.reshape(-1, 2).copy()
                    fl = int(0.05 * SR)
                    ramp = np.linspace(0, 1, fl, dtype=np.float32)[:, None]
                    x[:fl] *= ramp
                    x[-fl:] *= ramp[::-1]
                    add(clips, x, t0 + off)
                    off += b - a
                clip_on[i:i + int(it["dur"] * SR)] = 1
    bed_start = cue_fx(fx, tl)
    bed = music_bed(total, bpm)
    bed = np.pad(bed, ((0, max(0, N - len(bed))), (0, 0)))[:N]
    g = np.zeros(N, np.float32)
    si = int(bed_start * SR)
    g[si:] = 1.0
    g *= smooth(np.where(vo_on > 0, 0.55, 1.0).astype(np.float32), 0.6)
    g *= 1 - smooth(clip_on, 0.8)
    g *= np.clip((np.arange(N) - si) / (1.5 * SR), 0, 1).astype(np.float32)
    tail = int((total - 2.5) * SR)
    g[tail:] *= np.linspace(1, 0, N - tail, dtype=np.float32)
    bed *= g[:, None]
    mix = (vo * 10 ** ((-16.0 - lufs(vo)) / 20) + clips * 10 ** ((-16.5 - lufs(clips)) / 20)
           + bed * 10 ** ((bed_lufs - lufs(bed)) / 20) + fx * 10 ** ((-27.0 - lufs(fx)) / 20))
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
    return total


# ---------------------------------------------------------------- rendering

def render_scene_file(out, size, frames, frame_fn):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                          f"{size[0]}x{size[1]}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "10", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in range(frames):
        p.stdin.write(frame_fn(n / FPS).tobytes())
    p.stdin.close()
    p.wait()


def final_encode(tl, work, out, crf=18, gop=FPS // 2, title=None):
    lst = os.path.join(work, "scenes", "list.txt")
    with open(lst, "w") as f:
        for i, s in enumerate(tl):
            f.write(f"file '{i:02d}_{s['id']}.mp4'\n")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
           "-i", os.path.join(work, "soundtrack.wav"), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-maxrate", "12M", "-bufsize", "24M",
           "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(gop), "-bf", "2",
           "-x264-params", "open-gop=0", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-shortest"]
    if title:
        cmd += ["-metadata", f"title={title}", "-metadata", "artist=All Things Classroom"]
    subprocess.run(cmd + [out], check=True)
