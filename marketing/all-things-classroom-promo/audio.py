"""Original soundtrack + SFX for the All Things Classroom promo.

120 BPM, D major (D - A - Bm - G, one chord per 2 beats). Section layout mirrors the
animation's beat grid; one-shot SFX come from events.json exported by the page.
"""
import json, sys
import numpy as np
import scipy.signal as sg
from scipy.ndimage import maximum_filter1d, minimum_filter1d

SR = 44100
SPB = 0.5
DUR = 26.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
bt = lambda beat: beat * SPB
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)

EVENTS = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'events.json'))

# ─── buses (stereo) ────────────────────────────────────────────────────────────
drums = np.zeros((N, 2)); bass = np.zeros((N, 2)); music = np.zeros((N, 2)); sfx = np.zeros((N, 2)); send = np.zeros((N, 2))


def to_st(x, pan=0.0):
    if x.ndim == 2:
        return x
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * np.sqrt(2)


def add(buf, x, t, gain=1.0, pan=0.0, rev=0.0):
    x = to_st(x, pan)
    i = int(round(t * SR))
    if i >= N or i + len(x) <= 0:
        return
    s0 = max(0, -i)
    j = min(N, i + len(x))
    buf[max(i, 0):j] += x[s0:s0 + j - max(i, 0)] * gain
    if rev:
        send[max(i, 0):j] += x[s0:s0 + j - max(i, 0)] * gain * rev


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def filt(x, kind, fc, order=2):
    sos = sg.butter(order, fc, kind, fs=SR, output='sos')
    return sg.sosfilt(sos, x, axis=0)


def tv_filter(x, fc_of_t, kind='low', block=128):
    if x.ndim == 2:
        return np.stack([tv_filter(x[:, c], fc_of_t, kind, block) for c in range(x.shape[1])], axis=1)
    y = np.zeros_like(x); zi = None
    for s in range(0, len(x), block):
        fc = float(np.clip(fc_of_t((s + block / 2) / SR), 40, SR * 0.45))
        sos = sg.butter(2, fc, kind, fs=SR, output='sos')
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        y[s:s + block], zi = sg.sosfilt(sos, x[s:s + block], zi=zi)
    return y


def tv_band(x, fc_of_t, q=1.2, block=128):
    y = np.zeros_like(x); zi = None
    for s in range(0, len(x), block):
        fc = float(np.clip(fc_of_t((s + block / 2) / SR), 60, SR * 0.4))
        lo, hi = fc / (1 + 0.5 / q), fc * (1 + 0.5 / q)
        sos = sg.butter(1, [lo, min(hi, SR * 0.45)], 'band', fs=SR, output='sos')
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        y[s:s + block], zi = sg.sosfilt(sos, x[s:s + block], zi=zi)
    return y


def saw(freq, n, phase0=None):
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    ph = ((rng.random() if phase0 is None else phase0) + np.cumsum(f) / SR) % 1.0
    dt = f / SR
    y = 2 * ph - 1
    m = ph < dt; x = ph[m] / dt[m]; y[m] -= x + x - x * x - 1
    m = ph > 1 - dt; x = (ph[m] - 1) / dt[m]; y[m] -= x * x + x + x + 1
    return y


def sine(freq, n, phase0=0.0):
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    return np.sin(2 * np.pi * (phase0 + np.cumsum(f) / SR))


def noise(n, st=False):
    return rng.standard_normal((n, 2) if st else n)


# ─── drums ─────────────────────────────────────────────────────────────────────
def kick(big=False):
    t = tt(0.55 if big else 0.42)
    f = 46 + 150 * np.exp(-t * 30) + 60 * np.exp(-t * 220)
    body = sine(f, len(t)) * np.exp(-t * (5 if big else 8))
    click = filt(noise(len(t)), 'high', 1800) * np.exp(-t * 420) * 0.35
    return np.tanh((body + click) * 1.8) * 0.95


def clap():
    t = tt(0.45)
    env = np.zeros_like(t)
    for d in (0, 0.011, 0.023):
        env += np.where(t >= d, np.exp(-(t - d) * 260), 0)
    env += np.where(t >= 0.03, np.exp(-(t - 0.03) * 16) * 0.55, 0)
    return filt(noise(len(t)), 'band', [900, 4200]) * env * 1.1


def snare(v=1.0):
    t = tt(0.22)
    tone = sine(185 + 60 * np.exp(-t * 40), len(t)) * np.exp(-t * 28) * 0.5
    nz = filt(noise(len(t)), 'band', [1200, 7000]) * np.exp(-t * 32)
    return (tone + nz) * v


def hat(open_=False):
    t = tt(0.3 if open_ else 0.06)
    return filt(noise(len(t)), 'high', 7500) * np.exp(-t * (11 if open_ else 95))


def crash(dur=2.6):
    t = tt(dur)
    nz = filt(noise(len(t), st=True), 'high', 3200)
    metal = sum(sine(rng.uniform(3000, 9000), len(t)) for _ in range(6))[:, None] * 0.08
    return (nz + metal) * np.exp(-t * 2.0)[:, None] * 0.55


def impact():
    t = tt(2.2)
    sub = sine(58 * np.exp(-t * 0.6) + 22, len(t)) * np.exp(-t * 2.2)
    thud = filt(noise(len(t)), 'low', 350) * np.exp(-t * 9) * 1.6
    return np.tanh((sub + thud) * 1.5) * 0.9


# ─── tonal instruments ─────────────────────────────────────────────────────────
CHORDS = [  # (bass midi, chord tones midi) — D, A, Bm, G
    (38, [62, 66, 69, 74]),
    (33, [61, 64, 69, 73]),
    (35, [59, 62, 66, 71]),
    (31, [59, 62, 67, 71]),
]
chord_at = lambda beat: CHORDS[int(beat // 2) % 4]


def supersaw(midis, dur, detune=0.14, voices=5):
    n = int(dur * SR)
    out = np.zeros((n, 2))
    for m in midis:
        for v in range(voices):
            d = (v - (voices - 1) / 2) / ((voices - 1) / 2)  # -1..1
            f = mtof(m + d * detune)
            out += to_st(saw(f, n), pan=d * 0.8) / voices
    return out / max(1, len(midis))


def stab(midis, dur=0.32, bright=6500, decay=9.0):
    t = tt(dur)
    x = supersaw(midis, dur)
    x = tv_filter(x, lambda s: 600 + bright * np.exp(-s * 14))
    return x * (np.exp(-t * decay) * (1 - np.exp(-t * 400)))[:, None]


def pluck(m, dur=0.22):
    t = tt(dur)
    x = saw(mtof(m), len(t)) * 0.7 + np.sign(sine(mtof(m + 12), len(t))) * 0.15
    x = tv_filter(x, lambda s: 500 + 5500 * np.exp(-s * 26))
    return x * np.exp(-t * 14) * (1 - np.exp(-t * 600))


def pad(midis, dur, fc=2200):
    t = tt(dur)
    x = supersaw(midis, dur, detune=0.18, voices=6)
    x = filt(x, 'low', fc)
    a = np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / 0.05).clip(0, 1)
    return x * a[:, None]


def bass_note(m, dur, sub=True):
    t = tt(dur)
    f = mtof(m)
    x = filt(saw(f, len(t)) * 0.8 + saw(f * 1.005, len(t)) * 0.4, 'low', 900)
    if sub:
        x = x * 0.55 + sine(f, len(t)) * 0.8
    env = np.minimum(1, t / 0.004) * np.minimum(1, (dur - t) / 0.02).clip(0, 1)
    return np.tanh(x * 1.4) * env


# ─── fx ────────────────────────────────────────────────────────────────────────
def riser(dur, soft=False):
    t = tt(dur)
    p = t / dur
    nz = tv_band(noise(len(t)), lambda s: 400 * (22 ** (s / dur)), q=1.5)
    tone = filt(saw(mtof(50) * 2 ** (2 * p), len(t)) + saw(mtof(57) * 2 ** (2 * p), len(t)), 'low', 3000) * 0.18
    y = (nz * 1.6 + tone) * (p ** 2.2)
    return y * (0.45 if soft else 0.8)


def whoosh(pre=0.38, post=0.25, soft=False):
    t = tt(pre + post)
    env = np.where(t < pre, (t / pre) ** 2.5, np.exp(-(t - pre) * 14))
    y = tv_band(noise(len(t)), lambda s: 350 + 4200 * min(1, s / pre) ** 1.5, q=0.9) * env * 2.0
    return y * (0.45 if soft else 0.8), pre


def suck(dur=0.55):
    t = tt(dur)
    y = tv_band(noise(len(t)), lambda s: 5000 * (0.08 ** (s / dur)), q=1.0)
    return y * np.sin(np.pi * t / dur) ** 1.2 * 1.6 + sine(900 * np.exp(-t * 5), len(t)) * 0.12 * np.exp(-t * 4)


def pop(big=False):
    t = tt(0.16 if big else 0.1)
    f = (300 if big else 500) + (900 if big else 1200) * (1 - np.exp(-t * 60))
    return sine(f, len(t)) * np.exp(-t * (26 if big else 40)) * (0.9 if big else 0.6)


def blip(m):
    t = tt(0.09)
    return sine(mtof(m), len(t)) * np.exp(-t * 45) * 0.35


def ding(hi=False):
    t = tt(0.8)
    f0 = mtof(88 if hi else 85)
    y = sine(f0, len(t)) * np.exp(-t * 6) + sine(f0 * 2.76, len(t)) * np.exp(-t * 14) * 0.3
    t2 = tt(0.8)
    y2 = sine(f0 * 1.335, len(t2)) * np.exp(-t2 * 6)
    out = np.zeros(len(t) + int(0.09 * SR)); out[:len(t)] += y; out[int(0.09 * SR):] += y2
    return out * 0.28


def tick():
    t = tt(0.07)
    return (sine(1900, len(t)) * np.exp(-t * 90) + filt(noise(len(t)), 'band', [2000, 6000]) * np.exp(-t * 300) * 0.4) * 0.5


def key_click():
    t = tt(0.05)
    c = filt(noise(len(t)), 'band', [1800, 6500]) * np.exp(-t * 500) * rng.uniform(0.7, 1.0)
    th = sine(rng.uniform(170, 240), len(t)) * np.exp(-t * 110) * 0.5
    return (c + th) * 0.55


def sparkle(n=7, spread=0.05, base=0):
    notes = [86, 88, 90, 93, 95, 98, 100, 102]
    out = np.zeros(int((n * spread + 0.6) * SR))
    for k in range(n):
        m = notes[min(len(notes) - 1, k + base)] if spread < 0.06 else notes[rng.integers(0, len(notes))]
        t = tt(0.5)
        y = sine(mtof(m), len(t)) * np.exp(-t * 9) * 0.25 + sine(mtof(m) * 2, len(t)) * np.exp(-t * 16) * 0.08
        i = int(k * spread * SR)
        out[i:i + len(y)] += y
    return out


# ─── arrangement ───────────────────────────────────────────────────────────────
kicks = []


def K(beat, big=False, g=1.0):
    add(drums, kick(big), bt(beat), 0.72 * g); kicks.append(bt(beat))


def groove(b0, b1, clap_on=True, hats16=True, open_hats=True, kick_on=True, g=1.0):
    for k in np.arange(b0, b1, 1.0):
        if kick_on: K(k, g=g)
        if clap_on and int(k) % 2 == 1: add(drums, clap(), bt(k), 0.8 * g, rev=0.18)
        for i in range(4 if hats16 else 2):
            v = [0.32, 0.14, 0.42, 0.14][i] if hats16 else 0.3
            add(drums, hat(), bt(k + i / (4 if hats16 else 2)) + rng.uniform(0, 0.004), v * g, pan=0.25)
        if open_hats: add(drums, hat(True), bt(k + 0.5), 0.16 * g, pan=-0.2)


def bassline(b0, b1, g=1.0):
    for k in np.arange(b0, b1, 0.5):
        root = chord_at(k)[0]
        on_beat = abs(k - round(k)) < 1e-6
        add(bass, bass_note(root, 0.2 if on_beat else 0.23, sub=True), bt(k), (0.5 if on_beat else 0.75) * g)


def pads(b0, b1, fc=2400, g=1.0):
    for k in np.arange(b0, b1, 2.0):
        _, tones = chord_at(k)
        add(music, pad([tones[0] - 12] + tones, bt(min(2, b1 - k)), fc), bt(k), 0.4 * g, rev=0.25)


def arp(b0, b1, g=1.0, oct_=12):
    pat = [0, 1, 2, 3, 2, 1, 3, 2]
    for s, k in enumerate(np.arange(b0, b1, 0.25)):
        _, tones = chord_at(k)
        m = tones[pat[s % 8]] + oct_
        add(music, pluck(m), bt(k), 0.17 * g, pan=0.35 if s % 2 else -0.35, rev=0.3)
        add(music, pluck(m), bt(k) + 0.375, 0.05 * g, pan=-0.5 if s % 2 else 0.5)  # dotted-8th echo


def roll(b0, b1, step, v0=0.25, v1=0.8):
    ks = np.arange(b0, b1 - 1e-9, step)
    for i, k in enumerate(ks):
        add(drums, snare(), bt(k), v0 + (v1 - v0) * i / max(1, len(ks) - 1), rev=0.12)


# Hook (0–4): four punchy kick+stab hits, ticking hats
for i in range(4):
    K(i, g=0.9)
    add(music, stab(CHORDS[i][1], 0.45), bt(i), 0.55, rev=0.3)
for k in np.arange(0, 4, 0.5):
    add(drums, hat(), bt(k + 0.5), 0.18, pan=0.2)
# Chaos (4–6)
groove(4, 6)
bassline(4, 6, g=0.9)
add(music, pad([50, 62, 66, 69], bt(2), fc=1500), bt(4), 0.3, rev=0.2)
add(drums, crash(1.6), bt(5), 0.5)
# Build (6–8)
roll(6, 7, 0.5, 0.2, 0.4); roll(7, 7.5, 0.25, 0.4, 0.6); roll(7.5, 7.875, 0.125, 0.6, 0.85)
# Drop (8–16)
groove(8, 16); bassline(8, 16); pads(8, 16); arp(10, 16, g=0.8)
add(drums, crash(), bt(8), 0.7)
# Subject cuts (16–24)
groove(16, 23); bassline(16, 23); pads(16, 24); arp(16, 24)
add(drums, crash(), bt(16), 0.55)
roll(22, 23, 0.25, 0.25, 0.55); roll(23, 24, 0.125, 0.5, 0.9)
# Hub (24–28)
groove(24, 28); bassline(24, 28); pads(24, 28); arp(24, 28)
add(drums, crash(), bt(24), 0.6)
# Search breakdown (28–36): half-time, filtered
for k in (28, 30, 32, 33.5, 34):
    K(k, g=0.75)
for k in np.arange(28, 35, 0.5):
    add(drums, hat(), bt(k + 0.5), 0.14, pan=0.2)
for k in (29, 31, 33):
    add(drums, clap(), bt(k), 0.3, rev=0.3)
pads(28, 36, fc=900, g=1.15)
arp(28, 34, g=0.55, oct_=0)
for k in np.arange(28, 36, 2.0):
    add(bass, bass_note(chord_at(k)[0], bt(2) - 0.02), bt(k), 0.45)
roll(35, 35.5, 0.25, 0.3, 0.5); roll(35.5, 36, 0.125, 0.5, 0.85)
# Slams (36–40)
for i, k in enumerate((36, 37, 38)):
    K(k, big=True)
    add(drums, clap(), bt(k), 0.6, rev=0.25)
    add(music, stab([t + 12 * (i == 2) for t in CHORDS[[0, 1, 0][i]][1]], 0.6, decay=5), bt(k), 0.6, rev=0.35)
    add(drums, crash(1.4 if i < 2 else 2.2), bt(k), 0.35 + 0.15 * i)
groove(38, 39.5, clap_on=True); bassline(38, 39.5)
roll(39, 39.5, 0.125, 0.4, 0.7)
# Final drop (40–48)
groove(40, 48); bassline(40, 48); pads(40, 48); arp(40, 48)
add(drums, crash(), bt(40), 0.75); add(drums, crash(), bt(44), 0.35)
roll(47, 47.5, 0.25, 0.3, 0.5); roll(47.5, 48, 0.125, 0.5, 0.8)
# Outro hit (48): ring out
K(48, big=True)
add(drums, crash(3.8), bt(48), 0.7)
add(music, stab([62, 66, 69, 74, 78], 4.0, bright=5000, decay=1.3), bt(48), 0.65, rev=0.5)
add(music, pad([50, 62, 66, 69, 74], 3.8, fc=1800), bt(48), 0.25, rev=0.4)
add(bass, bass_note(38, 2.5), bt(48), 0.55)
add(sfx, impact(), bt(48), 0.45)

# ─── one-shot SFX from the animation's cue list ───────────────────────────────
cut_n = 0
for e in EVENTS:
    t, ty = e['t'], e['type']
    if ty == 'pop':
        add(sfx, pop(e.get('big')), t, 0.5, rev=0.2)
    elif ty == 'blip':
        add(sfx, blip([86, 88, 90, 93, 95][e['k'] % 5] + 12), t, 0.5, pan=rng.uniform(-.7, .7), rev=0.2)
    elif ty == 'ding':
        add(sfx, ding(e.get('hi')), t, 0.7, pan=0.2 if e.get('hi') else -0.2, rev=0.25)
    elif ty == 'slam':
        add(sfx, impact(), t, 0.35)
    elif ty == 'suck':
        add(sfx, suck(), t, 0.55)
    elif ty == 'riser':
        dur = e['end'] - t
        add(sfx, riser(dur, e.get('soft')), t, 0.7, rev=0.2)
    elif ty == 'impact':
        add(sfx, impact(), t, 0.85 if not e.get('final') else 0.8)
    elif ty == 'whoosh':
        w, pre = whoosh(soft=e.get('soft'))
        add(sfx, w, t - pre, 0.6, rev=0.15)
    elif ty == 'cut':
        _, tones = chord_at(e['t'] / SPB)
        add(music, stab([m + 12 for m in tones[:3]], 0.2, decay=16), t, 0.32, rev=0.2)
        w, pre = whoosh(0.12, 0.1, soft=True)
        add(sfx, w, t - pre, 0.4, pan=-0.4 if cut_n % 2 else 0.4)
        cut_n += 1
    elif ty == 'tick':
        add(sfx, tick(), t, 0.6, rev=0.2)
    elif ty == 'key':
        add(sfx, key_click(), t + rng.uniform(-0.01, 0.01), 0.75, pan=rng.uniform(-.3, .3))
    elif ty == 'enter':
        add(sfx, key_click(), t, 1.0); add(sfx, pop(True), t + 0.02, 0.45, rev=0.2)
    elif ty == 'card':
        w, pre = whoosh(0.1, 0.12, soft=True)
        add(sfx, w, t - pre, 0.35); add(sfx, blip(81 + 4 * e['i'] + 12), t, 0.5, rev=0.25)
    elif ty == 'tap':
        add(sfx, pop(True), t, 0.6, rev=0.2)
    elif ty == 'sparkle':
        add(sfx, sparkle(8, 0.045), t, 0.55, rev=0.45)
    elif ty == 'confetti':
        pp = filt(noise(int(0.25 * SR)), 'band', [800, 5000]) * np.exp(-tt(0.25) * 25)
        add(sfx, pp, t, 0.5); add(sfx, sparkle(10, 0.035, 0), t + 0.05, 0.5, rev=0.5)
    elif ty == 'shine':
        add(sfx, sparkle(6, 0.06, 2), t, 0.35, rev=0.5)
    elif ty == 'stab':
        pass  # hook stabs are part of the arrangement above

# ─── mix ───────────────────────────────────────────────────────────────────────
tk = np.array(sorted(kicks))
tax = np.arange(N) / SR
idx = np.searchsorted(tk, tax, side='right') - 1
since = np.where(idx >= 0, tax - tk[np.clip(idx, 0, None)], 10.0)
duck = 1 - 0.72 * np.exp(-since / 0.085)
duck_soft = 1 - 0.45 * np.exp(-since / 0.07)

bass_d = bass * duck[:, None]
music_d = music * duck_soft[:, None]

ir_t = tt(1.8)
ir = filt(noise(len(ir_t), st=True), 'low', 6500) * np.exp(-ir_t * 3.4)[:, None]
ir[:int(0.012 * SR)] = 0
ir /= np.sqrt((ir ** 2).sum(axis=0))
wet = np.stack([sg.fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
wet = filt(wet, 'high', 250) * duck_soft[:, None]

mix = drums * 1.0 + bass_d * 0.5 + music_d * 1.9 + sfx * 1.1 + wet * 0.7
mix = filt(mix, 'high', 28)
mix = mix + 0.3 * filt(mix, 'band', [2200, 7000])  # presence lift for phone speakers

# fade the last half-second
fade = np.ones(N); fl = int(0.6 * SR); fade[-fl:] = np.linspace(1, 0, fl) ** 2
mix *= fade[:, None]

try:
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(mix)
    mix *= 10 ** ((-13.0 - lufs) / 20)
    print(f'integrated loudness before: {lufs:.1f} LUFS -> target -13')
except ImportError:
    mix *= 0.3 / np.sqrt((mix ** 2).mean())

# look-ahead peak limiter at -1 dBFS
thr = 10 ** (-1.0 / 20)
pk = maximum_filter1d(np.abs(mix).max(axis=1), size=int(0.004 * SR))
gain = np.minimum(1.0, thr / np.maximum(pk, 1e-9))
gain = minimum_filter1d(gain, size=int(0.008 * SR))
b_, a_ = sg.butter(1, 30, fs=SR)
gain = np.minimum(gain, sg.filtfilt(b_, a_, gain))
mix = np.clip(mix * gain[:, None], -thr, thr)

try:
    import pyloudnorm as pyln
    print(f'final loudness: {pyln.Meter(SR).integrated_loudness(mix):.1f} LUFS, peak {20*np.log10(np.abs(mix).max()):.2f} dBFS')
except ImportError:
    pass

from scipy.io import wavfile
wavfile.write('soundtrack.wav', SR, (mix * 32767).astype(np.int16))
print('wrote soundtrack.wav', mix.shape)
