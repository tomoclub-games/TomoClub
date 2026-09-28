"""Original, royalty-free upbeat track for the Reel, synthesised from scratch.

120 BPM, C-G-Am-F, four-on-the-floor kick, offbeat chord stabs, pumping bass and
hats. The arrangement follows the edit: a breakdown (no drums) under the emotional
section, a riser into the CTA, and a hook melody that only plays on the CTA, so it
never fights the voices. Nothing is sampled, so there is no licence to clear and
Instagram will not mute it.
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
PROG = [[48, 52, 55, 60, 64], [43, 50, 55, 59, 62], [45, 52, 57, 60, 64], [41, 53, 57, 60, 65]]  # C G Am F
ROOTS = [36, 43, 45, 41]
HOOK = [  # (eighth-note step, midi) over 4 bars: catchy, pentatonic-leaning
    (0, 76), (2, 79), (4, 81), (5, 79), (6, 76), (8, 74), (10, 79), (12, 71), (13, 74),
    (16, 72), (18, 76), (20, 81), (21, 79), (22, 76), (24, 77), (26, 76), (28, 72),
]
rng = np.random.default_rng(7)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output="sos"), x)


def _phase(f, t):
    """Phase for a fixed or time-varying (vibrato) frequency."""
    if np.ndim(f):
        return 2 * np.pi * np.cumsum(f) / SR, float(np.mean(f))
    return 2 * np.pi * f * t, f


def saw(f, t, bright=1.0):
    """Band-limited saw (additive), harmonics up to ~9 kHz."""
    ph, f0 = _phase(f, t)
    out = np.zeros_like(t)
    for k in range(1, max(1, int(9000 * bright / f0)) + 1):
        out += np.sin(k * ph) / k
    return out * (2 / np.pi)


def square(f, t):
    ph, f0 = _phase(f, t)
    out = np.zeros_like(t)
    for k in range(1, max(2, int(7000 / f0)), 2):
        out += np.sin(k * ph) / k
    return out * (4 / np.pi)


def add(buf, start, sig, gain=1.0, pan=0.0):
    i = int(round(start * SR))
    if i >= len(buf) or i + len(sig) <= 0:
        return
    j0 = max(0, -i)
    sig = sig[j0:]
    i = max(i, 0)
    n = min(len(sig), len(buf) - i)
    buf[i:i + n, 0] += sig[:n] * gain * (1 - max(pan, 0))
    buf[i:i + n, 1] += sig[:n] * gain * (1 + min(pan, 0))


def kick():
    t = np.arange(int(0.42 * SR)) / SR
    phase = 2 * np.pi * (46 * t + 95 / 28 * (1 - np.exp(-28 * t)))
    body = np.sin(phase) * np.exp(-t * 7.5)
    click = filt(rng.standard_normal(len(t)), "highpass", 2500) * np.exp(-t * 260) * 0.25
    return np.tanh(1.6 * (body + click))


def clap():
    t = np.arange(int(0.35 * SR)) / SR
    n = rng.standard_normal(len(t))
    env = np.zeros_like(t)
    for d in (0, 0.011, 0.022):
        env += (t >= d) * np.exp(-np.clip(t - d, 0, None) * 90)
    env += (t >= 0.03) * np.exp(-np.clip(t - 0.03, 0, None) * 18) * 0.6
    return filt(filt(n, "highpass", 900), "lowpass", 6000) * env


def hat(open_=False):
    t = np.arange(int((0.25 if open_ else 0.06) * SR)) / SR
    return filt(rng.standard_normal(len(t)), "highpass", 7500, 4) * np.exp(-t * (14 if open_ else 70))


def stab(chord):
    t = np.arange(int(0.26 * SR)) / SR
    env = np.minimum(t / 0.004, 1) * np.exp(-t * 11)
    sig = np.zeros_like(t)
    for m in chord[1:]:
        for det in (-0.004, 0.0, 0.004):
            sig += saw(hz(m + 12) * (1 + det), t, 0.8)
    return filt(sig * env, "lowpass", 6500) / 9


def bass_note(m, length):
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(t / 0.003, 1) * np.exp(-t * 7)
    sig = saw(hz(m), t, 0.35) + 0.6 * np.sin(2 * np.pi * hz(m) * t)
    return filt(sig * env, "lowpass", 520) * 0.9


def lead_note(m, length):
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(t / 0.006, 1) * np.exp(-t * 4.5)
    vib = 1 + 0.003 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(t / 0.2, 1)
    sig = 0.6 * square(hz(m) * vib, t) + 0.4 * saw(hz(m) * 1.003, t, 0.7)
    return filt(sig * env, "lowpass", 7000) * 0.5


def pad(chord, length):
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(t / 0.6, 1) * np.clip((length - t) / 0.6, 0, 1)
    sig = np.zeros_like(t)
    for m in chord[1:]:
        for det in (-0.006, 0.006):
            sig += np.sin(2 * np.pi * hz(m) * (1 + det) * t) + 0.3 * np.sin(4 * np.pi * hz(m) * (1 + det) * t)
    return filt(sig * env, "lowpass", 4000) / 10


def reverb(x, secs=1.3, mix=0.18):
    t = np.arange(int(secs * SR)) / SR
    ir = filt(rng.standard_normal(len(t)), "lowpass", 5000) * np.exp(-t * 4.2)
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = np.stack([fftconvolve(x[:, c], ir)[:len(x)] for c in range(2)], axis=1)
    return x + wet * mix


def make_track(path, total, cta_start, breakdown=(None, None)):
    """Render the track. The bar grid is aligned so a bar starts exactly on the CTA."""
    n = int(total * SR)
    drums = np.zeros((n, 2))
    music = np.zeros((n, 2))
    lead = np.zeros((n, 2))
    origin = cta_start - np.ceil(cta_start / BAR) * BAR  # first bar starts at or before 0
    bd0, bd1 = breakdown
    k, cl, h_c, h_o = kick(), clap(), hat(), hat(True)
    bar_i = 0
    while origin + bar_i * BAR < total:
        b0 = origin + bar_i * BAR
        chord_i = bar_i % 4
        chord, root = PROG[chord_i], ROOTS[chord_i]
        in_break = bd0 is not None and bd0 <= b0 < bd1
        in_cta = b0 >= cta_start - 1e-6
        riser_bar = cta_start - BAR - 1e-6 <= b0 < cta_start - 1e-6
        for beat in range(4):
            tb = b0 + beat * BEAT
            if not in_break and not (riser_bar and beat == 3):
                add(drums, tb, k, 0.8)
            if not in_break and beat in (1, 3):
                add(drums, tb, cl, 0.55, 0.1)
            if not in_break:
                add(drums, tb + BEAT / 2, h_o if beat == 3 else h_c, 0.3 if beat == 3 else 0.4, -0.3)
                add(drums, tb + BEAT / 4, h_c, 0.16, 0.3)
                add(drums, tb + 3 * BEAT / 4, h_c, 0.16, 0.3)
            # offbeat stabs, pumping against the kick
            add(music, tb + BEAT / 2, stab(chord), 1.0 if not in_break else 0.5, 0.25 if beat % 2 else -0.25)
            if not in_break:
                for e in range(2):
                    m = root + (12 if e else 0)
                    add(music, tb + e * BEAT / 2 + 0.03, bass_note(m, BEAT / 2 - 0.03), 0.55)
        if in_break or in_cta:
            add(music, b0, pad(chord, BAR + 0.3), 0.8)
        if in_cta:
            for step, m in HOOK:
                bar_of_step = step // 8
                if bar_of_step == (bar_i - int(round((cta_start - origin) / BAR))) % 4:
                    add(lead, b0 + (step % 8) * BEAT / 2, lead_note(m, 0.45), 0.8)
        bar_i += 1
    # riser into the CTA: noise swept up over one bar, plus an impact on the downbeat
    r_len = BAR
    t = np.arange(int(r_len * SR)) / SR
    noise = rng.standard_normal(len(t))
    riser = np.zeros_like(noise)
    for s in range(8):
        seg = slice(int(s * len(t) / 8), int((s + 1) * len(t) / 8))
        riser[seg] = filt(noise, "bandpass", [400 + s * 900, 1200 + s * 1600])[seg]
    riser *= (t / r_len) ** 2
    add(music, cta_start - r_len, riser, 0.22)
    t = np.arange(int(2.5 * SR)) / SR
    crash = filt(rng.standard_normal(len(t)), "highpass", 4000) * np.exp(-t * 2.2)
    add(drums, cta_start, crash, 0.18)
    add(drums, cta_start, k, 1.0)
    mix = reverb(music, mix=0.16) + drums + reverb(lead, 1.6, 0.25)
    # gentle fade-out on the last bar, then limit to -1 dBFS
    fade = int(min(1.5, total) * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.4) / np.tanh(1.4) * 10 ** (-1 / 20)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    make_track("music_test.wav", 30.0, 20.0, breakdown=(8.0, 14.0))
