"""Build the soundtrack: narration + synthesized background music + sound effects.

usage: python audio.py VO_DIR CUES_JSON out.wav

Everything is generated here (no stock audio), so the track is royalty-free.
The music ducks under the voice; ffmpeg loudnorm is applied afterwards.
"""
import json
import os
import subprocess
import sys

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
RNG = np.random.default_rng(7)

VO_DIR, CUES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
info = json.load(open(CUES))
N = int((info["end"] + 0.5) * SR)


def db(x):
    return 10 ** (x / 20)


def tvec(d):
    return np.arange(int(d * SR)) / SR


def env(d, a=0.005, r=0.2):
    t = tvec(d)
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def add(buf, x, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    if x.ndim == 1 and buf.ndim == 2:
        x = np.stack([x, x], 1)
    buf[i:i + len(x)] += x * gain


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------------ narration
def load_vo(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ar", str(SR), "-ac", "1",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    x = hp(x, 80)
    rms = np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2))
    return x * (db(-18) / rms)


vo = np.zeros(N)
for line, t0 in info["lines"].items():
    add(vo, load_vo(os.path.join(VO_DIR, f"vo_{line}.wav")), t0)

# ------------------------------------------------------------------ music
BPM = 104
BEAT = 60 / BPM
BAR = 4 * BEAT
# C - G - Am - F  (I - V - vi - IV)
CHORDS = [[48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48]]


def marimba(f, d=0.5):
    t = tvec(d)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.28)
    x += 0.2 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.05)
    x += 0.12 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / 0.015)
    return x * np.minimum(1, t / 0.003)


def bass(f, d=0.5):
    t = tvec(d)
    x = np.tanh(1.6 * np.sin(2 * np.pi * f * t)) * np.exp(-t / 0.32)
    return lp(x * np.minimum(1, t / 0.01), 600)


def kick():
    t = tvec(0.25)
    f = 45 + 90 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)


def snap():
    return bp(RNG.standard_normal(int(0.12 * SR)), 1200, 5000) * env(0.12, 0.001, 0.04)


def shaker():
    return hp(RNG.standard_normal(int(0.05 * SR)), 6000) * env(0.05, 0.004, 0.015)


def pad(notes, d):
    t = tvec(d)
    x = np.zeros_like(t)
    for n in notes:
        for det in (-0.12, 0.0, 0.12):
            x += np.sin(2 * np.pi * midi(n + 12 + det) * t)
    x = lp(x, 1400)
    fade = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4)
    return x * fade / (3 * len(notes))


music = np.zeros((N, 2))
L = info["lines"]
calm = (L["light"] - 0.6, L["cta"] - 0.4)   # lighter texture during the explanation
bar_i, t = 0, 0.0
while t < info["end"]:
    ch = CHORDS[bar_i % 4]
    in_calm = calm[0] <= t < calm[1]
    add(music, pad(ch, BAR + 0.4), t, 0.10 if in_calm else 0.07)
    add(music, bass(midi(ch[0] - 12)), t, 0.30)
    add(music, bass(midi(ch[0] - 12)), t + 2 * BEAT, 0.22)
    arp = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24, ch[0] + 36, ch[2] + 24, ch[1] + 24, ch[2] + 24]
    for k, n in enumerate(arp):
        if in_calm and k % 2:
            continue
        pan = 0.35 * (1 if k % 2 else -1)
        m = marimba(midi(n)) * (0.16 if k % 2 == 0 else 0.11)
        add(music, np.stack([m * (1 - pan), m * (1 + pan)], 1), t + k * BEAT / 2)
    if not in_calm:
        for b in range(4):
            if b in (0, 2):
                add(music, kick(), t + b * BEAT, 0.45)
            else:
                add(music, snap(), t + b * BEAT, 0.12)
            add(music, shaker(), t + b * BEAT + BEAT / 2, 0.08)
    t += BAR
    bar_i += 1
# gentle fade in / out
fade = np.ones(N)
fi, fo = int(0.25 * SR), int(1.8 * SR)
fade[:fi] = np.linspace(0, 1, fi)
end_i = int(info["end"] * SR)
fade[end_i - fo:end_i] = np.linspace(1, 0, fo)
fade[end_i:] = 0
music *= fade[:, None]

# duck under the voice
presence = (np.abs(vo) > 0.003).astype(float)
k = int(0.35 * SR)
cs = np.concatenate([[0.0], np.cumsum(presence)])
avg = np.zeros(N)
avg[k // 2:k // 2 + N - k + 1] = (cs[k:] - cs[:-k]) / k  # centred moving average
presence = avg > 0.02
g = np.where(presence, db(-9), 1.0)
g = lp(g, 4)  # smooth attack/release
music *= np.clip(g, db(-9), 1.0)[:, None]


# ------------------------------------------------------------------ sound effects
def whoosh(d=0.38, lo=300, hi=3500, gain=1.0):
    n = RNG.standard_normal(int(d * SR))
    t = tvec(d)
    x = np.zeros_like(n)
    bands = 8
    for b in range(bands):
        f0 = lo + (hi - lo) * b / bands
        seg = bp(n, f0, f0 * 1.6)
        center = b / bands
        x += seg * np.exp(-((t / d - center) ** 2) / 0.02)
    return x * np.sin(np.pi * t / d) * gain * 0.6


def pop():
    t = tvec(0.09)
    f = 320 + 700 * np.exp(-t / 0.018)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(0.09, 0.002, 0.03)


def bell(f, d=0.6):
    t = tvec(d)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.08)) \
        * np.exp(-t / 0.22) * np.minimum(1, t / 0.002)


def sparkle():
    x = np.zeros(int(0.9 * SR))
    for i, n in enumerate([84, 88, 91, 96, 100]):
        b = bell(midi(n)) * (0.5 - i * 0.05)
        s = int(i * 0.055 * SR)
        x[s:s + len(b)] += b[: len(x) - s]
    return x


def thud():
    t = tvec(0.22)
    f = 55 + 60 * np.exp(-t / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.07)
    x += 0.3 * bp(RNG.standard_normal(len(t)), 1500, 4000) * np.exp(-t / 0.01)
    return x


def scribble(d):
    t = tvec(d)
    n = bp(RNG.standard_normal(len(t)), 2500, 6000)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * 7 * t + 2 * np.sin(2 * np.pi * 1.3 * t))
    return n * am * np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.08) * 0.5


def pour(d):
    t = tvec(d + 0.3)
    n = RNG.standard_normal(len(t))
    # pouring into a cup: the resonance rises as the air column gets shorter
    x = np.zeros_like(n)
    blk = 1024
    for i in range(0, len(n), blk):
        k = min(1.0, (i / SR) / d)
        f0 = 350 + 900 * k
        x[i:i + blk] = bp(n[max(0, i - 4096):i + blk], f0, f0 * 1.5)[-len(n[i:i + blk]):]
    x = 0.6 * x + 0.25 * lp(n, 900)
    # bubbly droplets
    for _ in range(int(14 * d)):
        s = RNG.uniform(0, d)
        dd = RNG.uniform(0.02, 0.05)
        tt = tvec(dd)
        f = RNG.uniform(500, 1100) * (1 + 1.5 * tt / dd)
        blip = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / dd) * 0.5
        add(x, blip, s)
    shape = np.minimum(1, t / 0.08) * np.clip((d + 0.3 - t) / 0.3, 0, 1)
    return x * shape * 0.8


def zap():
    t = tvec(0.6)
    f = 700 + 500 * t / 0.6 + 25 * np.sin(2 * np.pi * 9 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.6) * 0.35


sfx = np.zeros(N)
GAIN = dict(whoosh=0.30, slide=0.35, pop=0.26, sparkle=0.20, thud=0.55, scribble=0.07, pour=0.28, zap=0.22)
for cue in info["cues"]:
    kind, t0 = cue["kind"], cue["t"]
    if kind == "whoosh":
        x = whoosh()
    elif kind == "slide":
        x = whoosh(0.5, 200, 1800)
    elif kind == "pop":
        x = pop()
    elif kind == "sparkle":
        x = sparkle()
    elif kind == "thud":
        x = thud()
    elif kind == "scribble":
        x = scribble(cue["d"])
    elif kind == "pour":
        x = pour(cue["d"])
    elif kind == "zap":
        x = zap()
    else:
        continue
    add(sfx, x / (np.max(np.abs(x)) + 1e-9), t0, GAIN[kind])

# keep effects out of the way of the words: duck them and trim the
# consonant band (2-6 kHz) while the narrator is speaking
duck = lp(np.where(presence, 1.0, 0.0), 6)
sfx_dip = bp(sfx, 2000, 6000)
sfx = (sfx - 0.6 * duck * sfx_dip) * (1 - duck * (1 - db(-8)))

# ------------------------------------------------------------------ mix
mix = music * 0.40 + np.stack([vo, vo], 1) + np.stack([sfx, sfx], 1) * 0.8
peak = np.max(np.abs(mix))
mix = mix / peak * db(-3)
import soundfile as sf  # noqa: E402

sf.write(OUT, mix.astype(np.float32), SR, subtype="FLOAT")
print("wrote", OUT, round(len(mix) / SR, 2), "s")
