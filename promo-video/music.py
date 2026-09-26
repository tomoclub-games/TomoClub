"""Synthesizes the promo soundtrack: a 120 BPM pop-electronic bed plus 8-bit game SFX.

Every SFX is placed from cues.json, which render.mjs exports from the animation
timeline, so the audio stays in sync with the visuals.

    python3 promo-video/music.py            # -> promo-video/soundtrack.wav
Requires numpy + scipy.
"""
import json
import os
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
BPM = 120
BEAT = 60 / BPM
DUR = 46.0
N = int(SR * (DUR + 0.5))
rng = np.random.default_rng(11)

L = np.zeros(N)
R = np.zeros(N)
bus = {k: np.zeros((2, N)) for k in ('drums', 'bass', 'music', 'sfx', 'verb')}


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(d):
    return np.arange(int(d * SR)) / SR


def place(name, t0, sig, gain=1.0, pan=0.0, verb=0.0):
    """Add a mono/stereo signal to a bus at time t0 (seconds)."""
    i = int(round(t0 * SR))
    if sig.ndim == 1:
        lg, rg = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.vstack([sig * lg * 1.414, sig * rg * 1.414])
    if i < 0:
        sig, i = sig[:, -i:], 0
    n = min(sig.shape[1], N - i)
    if n <= 0:
        return
    bus[name][:, i:i + n] += sig[:, :n] * gain
    if verb:
        bus['verb'][:, i:i + n] += sig[:, :n] * gain * verb


def filt(x, kind, f, order=2):
    sos = butter(order, f, btype=kind, fs=SR, output='sos')
    return sosfilt(sos, x)


def env(n, a=0.002, d=0.2, curve=1.0):
    t = np.arange(n) / SR
    e = np.exp(-t / d) ** curve
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def noise(d):
    return rng.standard_normal(int(d * SR))


# ---------------------------------------------------------------- oscillators
def saw_bl(f, d, fc=6000.0, phase=0.0):
    """Band-limited saw by additive synthesis with a soft low-pass roll-off at fc."""
    t = tt(d)
    out = np.zeros_like(t)
    kmax = int(min(SR / 2 * 0.9, fc * 3) / f)
    for k in range(1, max(2, kmax + 1)):
        w = 1.0 / k / (1 + (k * f / fc) ** 4)
        if w < 1e-4:
            break
        out += w * np.sin(2 * np.pi * k * f * t + phase * k)
    return out * 0.6


def supersaw(f, d, fc=4000.0, voices=5, detune=0.14):
    l = np.zeros(int(d * SR))
    r = np.zeros_like(l)
    for v in range(voices):
        cents = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune * 100 if voices > 1 else 0
        s = saw_bl(f * 2 ** (cents / 1200), d, fc, phase=rng.uniform(0, 6.28))
        pan = (v - (voices - 1) / 2) / max(1, (voices - 1) / 2)
        l += s * (1 - pan) / 2
        r += s * (1 + pan) / 2
    return np.vstack([l, r]) / voices * 1.8


def square(f, d, duty=0.5):
    t = tt(d)
    return np.where((t * f) % 1.0 < duty, 1.0, -1.0)


def sine(f, d):
    return np.sin(2 * np.pi * f * tt(d))


def sweep_sine(f0, f1, d, k=30.0):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t * k)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


# ---------------------------------------------------------------- drums
def kick(gain=1.0):
    d = 0.45
    s = sweep_sine(150, 44, d, k=28) * env(int(d * SR), 0.001, 0.16, 1)
    click = filt(noise(0.006), 'highpass', 2000) * 0.25
    s[:len(click)] += click
    return np.tanh(s * 1.6) * gain


def clap():
    d = 0.3
    n = noise(d)
    n = filt(n, 'bandpass', [900, 3500])
    e = np.zeros(len(n))
    for o in (0.0, 0.011, 0.022):
        i = int(o * SR)
        e[i:] += env(len(n) - i, 0.0005, 0.012)
    e += env(len(n), 0.03, 0.09) * 0.7
    return n * e * 0.6


def hat(open_=False):
    d = 0.25 if open_ else 0.05
    n = filt(noise(d), 'highpass', 7500)
    return n * env(len(n), 0.0005, 0.07 if open_ else 0.014) * (0.35 if open_ else 0.3)


def snare(g=1.0):
    d = 0.2
    n = filt(noise(d), 'bandpass', [1200, 7000]) * env(int(d * SR), 0.0005, 0.05)
    tone = sine(190, d) * env(int(d * SR), 0.0005, 0.04) * 0.5
    return (n * 0.6 + tone) * g


def crash(d=2.2):
    n = filt(noise(d), 'highpass', 4500)
    return n * env(len(n), 0.001, 0.55) * 0.35


def riser(d, f0=300, f1=7000):
    n = noise(d)
    out = np.zeros_like(n)
    blk = 1024
    for i in range(0, len(n), blk):
        p = i / len(n)
        fc = f0 * (f1 / f0) ** p
        seg = filt(n[max(0, i - 2048):i + blk], 'bandpass', [fc * 0.7, min(fc * 1.4, 20000)])
        out[i:i + blk] = seg[-len(n[i:i + blk]):]
    ramp = np.linspace(0, 1, len(n)) ** 2.2
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(200, 1400, len(n))) / SR) * 0.12
    return (out * 0.5 + tone) * ramp


# ---------------------------------------------------------------- harmony
CH = {
    'Am': ([57, 60, 64], 45),
    'F': ([57, 60, 65], 41),
    'C': ([55, 60, 64], 36),
    'G': ([55, 59, 62], 43),
}
PROG = ['Am', 'F', 'C', 'G']


def chord_at(t):
    # finale cadence: level-up on C, then Am - F - G - C button
    if t >= 42.5:
        return 'C'
    if t >= 42.0:
        return 'G'
    if t >= 41.5:
        return 'F'
    if t >= 41.0:
        return 'Am'
    if t >= 40.0:
        return 'C'
    if t >= 38.0:
        return 'G'
    if t >= 36.0:
        return 'F'
    return PROG[int(t // 2) % 4]


def sections():
    """(start, end, flags) for the arrangement."""
    return [
        (1.0, 4.0, {'pad': 900, 'pluck': True}),
        (4.0, 8.0, {'pad': 1600, 'kick': 'build', 'bass': 'soft', 'hat8': True, 'pluck': True}),
        (8.0, 12.0, {'pad': 2400, 'kick': True, 'clap': True, 'hats': True, 'bass': True, 'stab': True}),
        (12.0, 16.0, {'pad': 2400, 'kick': True, 'clap': True, 'hats': True, 'bass': True, 'stab': True, 'arp': True}),
        (16.0, 21.5, {'pad': 2000, 'kick': True, 'clap': True, 'hats': True, 'bass': True, 'arp': True}),
        (21.5, 22.0, {'pad': 2000, 'bass': True}),
        (22.0, 28.0, {'pad': 2200, 'kick': True, 'clap': True, 'hats': True, 'bass': True, 'stab': True}),
        (28.0, 30.0, {'pad': 2600, 'kick': True, 'bass': True, 'hats': True}),
        (30.0, 36.0, {'pad': 2400, 'kick': True, 'clap': True, 'hats': True, 'bass': True, 'stab': True, 'arp': True}),
        (36.0, 40.0, {'pad': 1100, 'pluck': True}),
        (40.0, 42.5, {'pad': 3000, 'kick': True, 'clap': True, 'hats': True, 'bass': True, 'stab': True, 'arp': True}),
    ]


def build_music():
    kicks = []
    for (a, b, fl) in sections():
        # --- pads: one note-set per chord segment
        if fl.get('pad'):
            t = a
            while t < b - 1e-6:
                c = chord_at(t)
                nxt = min(b, (np.floor(t / 0.5) + 1) * 0.5)
                while nxt < b and chord_at(nxt) == c:
                    nxt += 0.5
                d = nxt - t
                notes, _ = CH[c]
                for m in notes:
                    s = supersaw(mtof(m), d + 0.35, fc=fl['pad'], voices=5, detune=0.12)
                    n = s.shape[1]
                    e = np.minimum(1, np.arange(n) / (0.06 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.35 * SR))
                    place('music', t, s * e, gain=0.06, verb=0.35)
                t = nxt
        # --- beat grid
        nb = int(round((b - a) / (BEAT / 4)))
        for i in range(nb):
            t = a + i * BEAT / 4
            step = int(round(t / (BEAT / 4))) % 16  # 16ths in a bar
            beat_on = step % 4 == 0
            c = chord_at(t)
            notes, root = CH[c]
            k = fl.get('kick')
            if k and beat_on:
                g = 0.55 + 0.45 * (t - a) / (b - a) if k == 'build' else 1.0
                place('drums', t, kick(g), gain=0.9)
                kicks.append(t)
            if fl.get('clap') and step in (4, 12):
                place('drums', t, clap(), gain=0.55, verb=0.25)
            if fl.get('hats'):
                if step % 4 == 2:
                    place('drums', t, hat(True), gain=0.5, pan=0.25)
                else:
                    place('drums', t, hat(False), gain=0.35 if step % 2 else 0.2, pan=-0.2)
            if fl.get('hat8') and step % 2 == 0:
                place('drums', t, hat(False), gain=0.12 + 0.25 * (t - a) / (b - a), pan=-0.2)
            # --- bass: 8ths, octave bounce
            bm = fl.get('bass')
            if bm and step % 2 == 0:
                pat = [0, 0, 12, 0, 0, 12, 0, 12]
                m = root + pat[(step // 2) % 8]
                d = BEAT / 2 * 0.9
                s = saw_bl(mtof(m), d, fc=380 if bm == 'soft' else 700) + 0.6 * sine(mtof(m), d)
                s *= env(len(s), 0.004, 0.18)
                place('bass', t, s, gain=0.32 if bm == 'soft' else 0.42)
            # --- offbeat chord stabs
            if fl.get('stab') and step % 4 == 2:
                for m in notes:
                    s = supersaw(mtof(m + 12), 0.2, fc=3500, voices=3, detune=0.1)
                    s *= env(s.shape[1], 0.003, 0.07)
                    place('music', t, s, gain=0.09, verb=0.3)
            # --- 8-bit arp lead (16ths)
            if fl.get('arp'):
                seq = [0, 1, 2, 3, 2, 1, 2, 3]
                tones = notes + [notes[0] + 12]
                m = tones[seq[step % 8]] + 12
                s = square(mtof(m), 0.11, duty=0.25) * env(int(0.11 * SR), 0.002, 0.05)
                place('music', t, s, gain=0.05, pan=0.35 if step % 2 else -0.35, verb=0.2)
            # --- soft pluck arp (intro / breakdown)
            if fl.get('pluck') and step % 2 == 0:
                seq = [0, 2, 1, 2, 0, 2, 1, 3]
                tones = notes + [notes[0] + 12]
                m = tones[seq[(step // 2) % 8]] + 12
                s = (sine(mtof(m), 0.45) + 0.3 * sine(mtof(m) * 2, 0.45)) * env(int(0.45 * SR), 0.002, 0.12)
                place('music', t, s, gain=0.09, pan=0.3 if (step // 2) % 2 else -0.3, verb=0.5)

    # snare rolls + risers into the big moments
    for (a, b, g) in [(7.0, 8.0, 0.5), (29.0, 30.0, 0.45), (39.0, 40.0, 0.55)]:
        t = a
        while t < b - 1e-6:
            p = (t - a) / (b - a)
            place('drums', t, snare(0.25 + 0.75 * p), gain=g, verb=0.2)
            t += BEAT / 2 if p < 0.5 else BEAT / 4
    for (a, b) in [(6.0, 8.0), (28.6, 30.0), (38.0, 40.0)]:
        place('music', a, riser(b - a), gain=0.35, verb=0.3)
    for t in (1.0, 8.0, 16.0, 30.0, 40.0):
        place('drums', t, crash(), gain=0.6, verb=0.3)
    return kicks


# ---------------------------------------------------------------- SFX
def sfx_sound(c):
    ty = c['type']
    if ty == 'blip':
        return square(880, 0.07, 0.5) * env(int(0.07 * SR), 0.001, 0.05) * 0.16, 0.0, 0.1
    if ty == 'select':
        a = square(660, 0.05, 0.5) * env(int(0.05 * SR), 0.001, 0.04)
        b = square(990, 0.12, 0.5) * env(int(0.12 * SR), 0.001, 0.06)
        return np.concatenate([a, b]) * 0.16, 0.0, 0.1
    if ty in ('impact', 'impact2', 'drop', 'final'):
        big = ty in ('impact', 'drop', 'final')
        d = 1.8 if big else 0.9
        boom = sweep_sine(90, 32, d, k=6) * env(int(d * SR), 0.001, 0.5 if big else 0.25)
        nz = filt(noise(0.5), 'lowpass', 3000) * env(int(0.5 * SR), 0.001, 0.08)
        s = boom.copy()
        s[:len(nz)] += nz * 0.6
        s = np.tanh(s * 1.4) * (0.6 if big else 0.38)
        return s, 0.0, 0.25
    if ty == 'hit':
        s = kick(0.8)[:int(0.3 * SR)] * 0.7
        cl = clap()
        s[:len(cl)] += cl[:len(s)] * 0.8
        return s * 0.6, 0.0, 0.25
    if ty == 'tick':
        d = 0.06
        s = sine(1900, d) * env(int(d * SR), 0.0005, 0.012) + filt(noise(d), 'highpass', 5000) * env(int(d * SR), 0.0005, 0.006) * 0.6
        return s * 0.3, 0.0, 0.1
    if ty == 'whoosh':
        d = 0.5
        n = noise(d)
        out = np.zeros_like(n)
        blk = 512
        for i in range(0, len(n), blk):
            p = i / len(n)
            fc = 400 * (8000 / 400) ** p
            seg = filt(n[max(0, i - 1024):i + blk], 'bandpass', [fc * 0.6, min(fc * 1.6, 20000)])
            out[i:i + blk] = seg[-len(n[i:i + blk]):]
        e = np.sin(np.linspace(0, np.pi, len(n))) ** 1.5
        return out * e * 0.5, 0.0, 0.2
    if ty == 'pop':
        d = 0.09
        s = np.sin(2 * np.pi * np.cumsum(np.linspace(380, 1100, int(d * SR))) / SR)
        return s * env(len(s), 0.001, 0.03) * 0.28, 0.0, 0.15
    if ty == 'blip2':
        return square(1320, 0.05, 0.25) * env(int(0.05 * SR), 0.001, 0.025) * 0.1, 0.0, 0.1
    if ty in ('coin', 'coin2'):
        a = square(988, 0.06, 0.5) * env(int(0.06 * SR), 0.001, 0.2)
        b = square(1319, 0.28 if ty == 'coin2' else 0.18, 0.5) * env(int((0.28 if ty == 'coin2' else 0.18) * SR), 0.001, 0.09)
        return np.concatenate([a, b]) * (0.11 if ty == 'coin2' else 0.06), 0.0, 0.15
    if ty == 'lvl':
        parts = [square(mtof(m), 0.045, 0.25) * env(int(0.045 * SR), 0.001, 0.03) for m in (84, 88, 91)]
        return np.concatenate(parts) * 0.07, 0.0, 0.2
    if ty == 'card':
        d = 0.12
        s = filt(noise(d), 'bandpass', [1500, 5000]) * np.sin(np.linspace(0, np.pi, int(d * SR)))
        return s * 0.35, -0.3, 0.1
    if ty == 'count':
        d = c.get('dur', 1.2)
        out = np.zeros(int((d + 0.1) * SR))
        for i in range(12):
            p = 1 - (1 - i / 12) ** 2  # ease-out spacing
            tk = square(mtof(84 + i), 0.03, 0.5) * env(int(0.03 * SR), 0.0005, 0.012)
            j = int(p * d * SR)
            out[j:j + len(tk)] += tk
        return out * 0.05, 0.0, 0.1
    if ty == 'type':
        d = c.get('dur', 1.1)
        out = np.zeros(int((d + 0.1) * SR))
        t = 0.0
        while t < d:
            ck = filt(noise(0.02), 'bandpass', [2500, 8000]) * env(int(0.02 * SR), 0.0003, 0.004)
            j = int(t * SR)
            out[j:j + len(ck)] += ck * rng.uniform(0.5, 1)
            t += rng.uniform(0.045, 0.08)
        return out * 0.18, 0.2, 0.05
    if ty == 'click':
        d = 0.03
        s = sine(2200, d) * env(int(d * SR), 0.0003, 0.005) + filt(noise(d), 'highpass', 3000) * env(int(d * SR), 0.0003, 0.003)
        return s * 0.3, 0.2, 0.05
    if ty == 'buzz':
        d = 0.32
        s = (square(110, d, 0.5) + square(116.5, d, 0.5)) * 0.5
        s = filt(s, 'lowpass', 1800) * env(int(d * SR), 0.002, 0.5)
        s[int(0.14 * SR):int(0.17 * SR)] *= 0.2
        return s * 0.16, 0.1, 0.1
    if ty == 'stamp':
        d = 0.35
        s = sweep_sine(160, 60, d, k=20) * env(int(d * SR), 0.001, 0.08)
        nz = filt(noise(0.08), 'lowpass', 2500) * env(int(0.08 * SR), 0.0005, 0.02)
        s[:len(nz)] += nz * 0.8
        return np.tanh(s * 1.5) * 0.45, 0.0, 0.2
    if ty == 'levelup':
        notes = [72, 76, 79, 84, 88, 91]
        step = 0.06
        out = np.zeros(int(1.4 * SR))
        for i, m in enumerate(notes):
            d = 0.9 if i == len(notes) - 1 else step * 1.5
            s = square(mtof(m), d, 0.25) * env(int(d * SR), 0.002, 0.3 if i == len(notes) - 1 else 0.05)
            if i == len(notes) - 1:
                vib = 1 + 0.004 * np.sin(2 * np.pi * 6 * tt(d))
                s = np.where((np.cumsum(mtof(m) * vib) / SR) % 1 < 0.25, 1.0, -1.0) * env(int(d * SR), 0.002, 0.3)
            j = int(i * step * SR)
            out[j:j + len(s)] += s[:len(out) - j]
        return out * 0.12, 0.0, 0.3
    return None, 0, 0


def main():
    cues = json.load(open(os.path.join(HERE, 'cues.json')))['cues']
    kicks = build_music()

    # "final" button: resolved C-major chord ringing out under the logo
    for m in (48, 55, 60, 64, 67, 72):
        s = supersaw(mtof(m), 3.4, fc=2600, voices=5, detune=0.12)
        n = s.shape[1]
        e = np.exp(-np.arange(n) / SR / 1.3)
        place('music', 42.5, s * e, gain=0.075, verb=0.5)
    place('bass', 42.5, (saw_bl(mtof(36), 2.5, fc=500) + sine(mtof(36), 2.5)) * env(int(2.5 * SR), 0.003, 0.9), gain=0.4)
    place('drums', 42.5, kick(1.0), gain=0.9)
    place('drums', 42.5, crash(3.0), gain=0.6, verb=0.4)
    # sparkle arp tail under the end card
    for i, m in enumerate([72, 76, 79, 84, 79, 76, 72, 67] * 2):
        t = 43.0 + i * 0.125
        s = (sine(mtof(m + 12), 0.3) * env(int(0.3 * SR), 0.002, 0.1))
        place('music', t, s, gain=0.05 * (1 - i / 16), pan=0.4 if i % 2 else -0.4, verb=0.6)

    for c in cues:
        s, pan, vb = sfx_sound(c)
        if s is not None:
            place('sfx', c['t'], s, pan=pan, verb=vb)

    # sidechain: duck bass + music under each kick
    duck = np.ones(N)
    shape = 1 - 0.75 * np.exp(-np.arange(int(0.25 * SR)) / SR / 0.07)
    for t in kicks:
        i = int(t * SR)
        n = min(len(shape), N - i)
        duck[i:i + n] = np.minimum(duck[i:i + n], shape[:n])
    bus['bass'] *= duck
    bus['music'] *= 0.35 + 0.65 * duck

    # reverb send (stereo decaying-noise impulse)
    ir_len = int(2.2 * SR)
    tir = np.arange(ir_len) / SR
    irs = [filt(rng.standard_normal(ir_len), 'lowpass', 6000) * np.exp(-tir / 0.55) for _ in range(2)]
    send = np.vstack([filt(bus['verb'][k], 'highpass', 220) for k in range(2)])  # keep lows out of the tail
    verb = np.vstack([fftconvolve(send[k], irs[k])[:N] for k in range(2)]) * 0.12

    mix = bus['drums'] + bus['bass'] + bus['music'] + bus['sfx'] * 1.1 + verb
    mix[0] = filt(mix[0], 'highpass', 28)
    mix[1] = filt(mix[1], 'highpass', 28)
    # gentle glue: soft clip then fade the tail
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / peak * 1.1) / np.tanh(1.1)
    fade = np.ones(N)
    f0, f1 = int(44.8 * SR), int(DUR * SR)
    fade[f0:f1] = np.linspace(1, 0, f1 - f0) ** 1.5
    fade[f1:] = 0
    mix *= fade
    mix = mix[:, :int(DUR * SR)]
    mix *= 0.89 / np.max(np.abs(mix))

    out = os.path.join(HERE, 'soundtrack.wav')
    pcm = (mix.T * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', out)


if __name__ == '__main__':
    main()
