"""Generates the reel's soundtrack: an original music bed plus sound effects
timed to the animation in video.html. Everything is synthesized here, so
there are no licensing questions.

Usage (from this folder):
    python3 soundtrack.py ../video/soundtrack.wav
Needs numpy and scipy. Keep the timings below in sync with video.html.
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
DUR = 44.0
N = int(SR * DUR)
rng = np.random.default_rng(7)

# ---- timings from video.html -------------------------------------------
SCENE_CUTS = [4.8, 10.4, 15.6, 21.4, 27.0, 32.0, 37.8]
IMPACT_BIG = [2.3]                       # "Cheating."
POPS = [11.5, 40.2]                      # "Train the teachers first.", CTA
TYPE_START, TYPE_RATE, TYPE_WORDS = 6.3, 0.16, 12
TICKETS = [5.8, 29.2, 33.1, 34.6]        # exit tickets sliding in
LIST_ITEMS = [16.9, 17.6, 18.3]
COUNTERS = [(12.8, 40), (21.8, 87)]      # (start, target) count-ups, 1.3s ease-out

# ---- music: 100 BPM, one chord per bar, A minor to C major ----------------
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
PROG = [  # (root midi, chord tones as midi)
    (45, [57, 60, 64]),      # Am
    (41, [57, 60, 65]),      # F
    (48, [55, 60, 64]),      # C
    (43, [55, 59, 62]),      # G
]
END_AT = 37.8                # drums drop, harmony resolves to C for the close
DRUMS_IN = 10.4
ARP_IN = 4.8


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def t_axis(n):
    return np.arange(n) / SR


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)


def place(buf, sig, at, gain=1.0, pan=0.0):
    """Mix a mono signal into the stereo buffer at time `at` with equal-power pan."""
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + len(sig)] += sig * gain * l
    buf[1, i:i + len(sig)] += sig * gain * r


def chord_at(t):
    if t >= END_AT:
        return None
    return PROG[int(t // BAR) % len(PROG)]


def saw(f, n, detune=0.0, harmonics=7):
    t = t_axis(n)
    out = np.zeros(n)
    for h in range(1, harmonics + 1):
        if f * h > 9000:
            break
        out += np.sin(2 * np.pi * f * h * (1 + detune) * t + rng.uniform(0, 6.28)) / h
    return out


def pad_layer(bright):
    out = np.zeros((2, N))
    bars = int(np.ceil(END_AT / BAR))
    for b in range(bars):
        start = b * BAR
        root, tones = PROG[b % len(PROG)]
        length = min(BAR + 0.9, END_AT + 0.6 - start)
        n = int(length * SR)
        env = np.minimum(1, t_axis(n) / 0.7) * np.minimum(1, (length - t_axis(n)) / 0.9)
        for side, det in ((0, -0.004), (1, 0.004)):
            v = sum(saw(hz(m), n, det) for m in tones) * env / len(tones)
            v = lp(v, 2000 if bright else 700, order=4)
            out[side, int(start * SR):int(start * SR) + n] += v[: N - int(start * SR)]
    # closing chord: C major 9, rings to the end
    start = END_AT
    n = N - int(start * SR)
    env = np.minimum(1, t_axis(n) / 0.5) * np.clip((DUR - start - t_axis(n)) / 3.0, 0, 1)
    for side, det in ((0, -0.004), (1, 0.004)):
        v = sum(saw(hz(m), n, det) for m in [48, 55, 60, 64, 67, 74]) * env / 6
        out[side, int(start * SR):] += lp(v, 2000 if bright else 700, order=4)
    return out


def pluck(f, length=1.4, vel=1.0):
    n = int(length * SR)
    t = t_axis(n)
    tone = np.zeros(n)
    for h, a, d in ((1, 1.0, 1.6), (2, 0.45, 3.0), (3, 0.2, 5.0), (4, 0.1, 7.0)):
        tone += a * np.exp(-d * t) * np.sin(2 * np.pi * f * h * t)
    return tone * np.minimum(1, t / 0.004) * vel


def kick():
    n = int(0.35 * SR)
    t = t_axis(n)
    f = 50 + 70 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12) * np.minimum(1, t / 0.002)


def shaker():
    n = int(0.06 * SR)
    t = t_axis(n)
    return hp(rng.standard_normal(n), 6500) * np.exp(-t / 0.015)


def reverb_ir(seconds=2.2):
    n = int(seconds * SR)
    t = t_axis(n)
    ir = np.stack([lp(rng.standard_normal(n), 5000) * np.exp(-t / (seconds / 5)) for _ in range(2)])
    return ir / np.abs(ir).sum(axis=1, keepdims=True) * 12


def whoosh(length=0.7):
    n = int(length * SR)
    t = t_axis(n)
    noise = rng.standard_normal(n)
    # rising band, peak just before the cut
    out = np.zeros(n)
    for k, (lo, hi) in enumerate([(300, 900), (700, 2000), (1500, 4500)]):
        seg = bp(noise, lo, hi)
        w = np.clip(t / length * 3 - k, 0, 1) ** 2
        out += seg * w
    env = (t / length) ** 2.2 * np.clip((length - t) / 0.08, 0, 1)
    return out * env


def impact():
    n = int(1.6 * SR)
    t = t_axis(n)
    boom = np.sin(2 * np.pi * (45 + 40 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.45)
    hit = lp(rng.standard_normal(n), 1800) * np.exp(-t / 0.08)
    return boom * 0.9 + hit * 0.35


def pop(f=880):
    n = int(0.5 * SR)
    t = t_axis(n)
    sweep = f * (1 + 0.5 * np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * np.exp(-t / 0.09)


def key_click():
    n = int(0.03 * SR)
    t = t_axis(n)
    return bp(rng.standard_normal(n), 1800, 5000) * np.exp(-t / 0.006)


def paper():
    n = int(0.35 * SR)
    t = t_axis(n)
    return bp(rng.standard_normal(n), 1200, 6000) * np.sin(np.pi * t / 0.35) ** 2


def tick():
    n = int(0.04 * SR)
    t = t_axis(n)
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.008)


def ease_inv(y):
    # inverse of 1-(1-x)^3
    return 1 - (1 - y) ** (1 / 3)


def build():
    music = np.zeros((2, N))
    t = t_axis(N)

    # pads: dark at the start, opening up once the students appear
    dark, bright = pad_layer(False), pad_layer(True)
    open_curve = np.clip((t - 4.8) / 6.0, 0, 1) * 0.8 + np.clip((t - 21.4) / 4.0, 0, 1) * 0.2
    music += dark * (1 - open_curve) * 0.55 + bright * open_curve * 0.42

    # arpeggio
    pattern = [0, 1, 2, 1, 0, 2, 1, 2]
    beat = ARP_IN
    step = BEAT / 2
    k = 0
    while beat < END_AT - 0.05:
        ch = chord_at(beat)
        if ch:
            root, tones = ch
            m = tones[pattern[k % 8]] + 12 + (12 if (beat > 21.4 and k % 8 == 5) else 0)
            vel = (0.75 if k % 2 else 1.0) * rng.uniform(0.85, 1.0)
            place(music, pluck(hz(m), vel=vel), beat + rng.uniform(-0.006, 0.006), 0.16,
                  pan=0.25 if k % 2 else -0.25)
        beat += step
        k += 1
    # last arpeggio phrase up a C major 9 as the page settles
    for i, m in enumerate([72, 76, 79, 83, 86]):
        place(music, pluck(hz(m), length=2.5, vel=0.8), END_AT + 0.4 + i * 0.3, 0.14, pan=-0.3 + i * 0.15)

    # bass
    b = DRUMS_IN - (DRUMS_IN % BAR)
    while b < END_AT:
        ch = chord_at(b)
        if ch and b >= DRUMS_IN - 0.01:
            n = int(BAR * 0.95 * SR)
            tt = t_axis(n)
            f = hz(ch[0])
            s = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt / 1.6) * np.minimum(1, tt / 0.01)
            place(music, s, b, 0.30)
        b += BAR
    place(music, np.sin(2 * np.pi * hz(36) * t_axis(int(6 * SR))) * np.exp(-t_axis(int(6 * SR)) / 2.0), END_AT, 0.28)

    ir = reverb_ir()
    wet = np.stack([fftconvolve(music[c], ir[c])[:N] for c in range(2)])
    music = music * 0.8 + wet * 0.35
    music *= 0.5 + 0.5 * np.clip((t - 4.8) / 5.6, 0, 1)

    drums = np.zeros((2, N))
    beat = DRUMS_IN
    while beat < END_AT - 0.05:
        idx = round((beat - DRUMS_IN) / BEAT)
        if idx % 2 == 0:
            place(drums, kick(), beat, 0.55)
        place(drums, shaker(), beat + BEAT / 2, 0.06 * rng.uniform(0.7, 1.0), pan=0.3)
        beat += BEAT

    sfx = np.zeros((2, N))
    for c in SCENE_CUTS:
        place(sfx, whoosh(), c - 0.62, 0.10, pan=rng.uniform(-0.3, 0.3))
    for a in IMPACT_BIG:
        place(sfx, impact(), a, 0.55)
    for a in POPS:
        place(sfx, pop(660), a, 0.14)
    for i in range(TYPE_WORDS):
        place(sfx, key_click(), TYPE_START + i * TYPE_RATE, 0.12, pan=rng.uniform(-0.2, 0.2))
    for a in TICKETS:
        place(sfx, paper(), a, 0.07)
    for a in LIST_ITEMS:
        place(sfx, pop(1320), a, 0.07)
    for start, target in COUNTERS:
        for v in range(1, target + 1, max(1, target // 12)):
            place(sfx, tick(), start + 1.3 * ease_inv(v / target), 0.035)

    mix = music + drums + sfx
    mix *= np.clip((DUR - t) / 2.5, 0, 1)
    mix /= np.abs(mix).max()
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)   # gentle peak rounding
    mix *= 0.89
    return mix


def write_wav(path, stereo):
    data = (np.clip(stereo.T, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '../video/soundtrack.wav'
    write_wav(out, build())
    print('wrote', out)
