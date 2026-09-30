"""Original 128 BPM hype track + SFX stem, synthesized from scratch (royalty-free).

Writes music.wav (stereo, 44.1k) and sfx.wav. Structure is bar-locked to the edit:
bar n starts at (n-1)*BAR seconds.
"""
import numpy as np
from scipy import signal
import wave

SR = 44100
BPM = 128
BEAT = 60 / BPM
BAR = 4 * BEAT
S16 = BEAT / 4
TOTAL = 63.0
N = int(TOTAL * SR)
rng = np.random.default_rng(7)


def bar_t(bar, beat=0.0):
    return (bar - 1) * BAR + beat * BEAT


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def buf():
    return np.zeros((N, 2), dtype=np.float64)


def place(dst, x, t, gain=1.0, pan=0.0):
    """Add mono or stereo x into dst at time t."""
    i = int(round(t * SR))
    if i >= N:
        return
    if x.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        x = np.stack([x * l * 1.414, x * r * 1.414], axis=1)
    n = min(len(x), N - i)
    if i < 0:
        x = x[-i:]
        n = min(len(x), N)
        i = 0
    dst[i:i + n] += x[:n] * gain


def env_adsr(n, a=0.005, d=0.1, s=0.7, r=0.1, hold=None):
    a_n = max(1, int(a * SR)); d_n = max(1, int(d * SR)); r_n = max(1, int(r * SR))
    hold_n = n if hold is None else int(hold * SR)
    e = np.ones(hold_n + r_n) * s
    e[:a_n] = np.linspace(0, 1, a_n)
    if a_n + d_n < hold_n:
        e[a_n:a_n + d_n] = np.linspace(1, s, d_n)
    else:
        e[a_n:hold_n] = np.linspace(1, s, max(0, hold_n - a_n))
    e[hold_n:] = np.linspace(e[hold_n - 1] if hold_n > 0 else s, 0, r_n)
    if len(e) < n:
        e = np.concatenate([e, np.zeros(n - len(e))])
    return e[:n]


def polyblep_saw(freq, n, phase0=0.0):
    dt = freq / SR
    ph = (phase0 + np.arange(n) * dt) % 1.0
    y = 2 * ph - 1
    m1 = ph < dt
    t = ph[m1] / dt
    y[m1] -= t + t - t * t - 1
    m2 = ph > 1 - dt
    t = (ph[m2] - 1) / dt
    y[m2] -= t * t + t + t + 1
    return y


def lp(x, fc, q=0.707):
    sos = signal.butter(2, min(fc, SR * 0.45), 'low', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def hp(x, fc):
    sos = signal.butter(2, fc, 'high', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def bp(x, lo, hi):
    sos = signal.butter(2, [lo, hi], 'band', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def sweep_lp(x, fc_curve, block=512):
    """Time-varying lowpass (block-wise biquad with carried state)."""
    x = np.atleast_2d(x.T).T if x.ndim == 1 else x
    out = np.zeros_like(x)
    zi = None
    for s in range(0, len(x), block):
        fc = float(np.clip(fc_curve[min(s, len(fc_curve) - 1)], 30, SR * 0.45))
        sos = signal.butter(2, fc, 'low', fs=SR, output='sos')
        if zi is None:
            zi = np.zeros((sos.shape[0], 2, x.shape[1]))
        out[s:s + block], zi = signal.sosfilt(sos, x[s:s + block], axis=0, zi=zi)
    return out


# ---------------------------------------------------------------- instruments
def kick():
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 46 + 120 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.26)
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t / 0.004) * 0.35
    return np.tanh(1.6 * (body + click)) * 0.95


def clap():
    n = int(0.35 * SR); t = np.arange(n) / SR
    noise = bp(rng.standard_normal(n), 900, 4200)
    e = np.zeros(n)
    for k, off in enumerate([0, 0.011, 0.022]):
        i = int(off * SR)
        e[i:] += np.exp(-(t[:n - i]) / (0.006 if k < 2 else 0.13)) * (0.7 if k < 2 else 1.0)
    return noise * e * 0.55


def snare(v=1.0):
    n = int(0.25 * SR); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.045) * 0.5
    noise = bp(rng.standard_normal(n), 1200, 8000) * np.exp(-t / 0.09)
    return (tone + noise) * 0.45 * v


def hat(open_=False):
    n = int((0.3 if open_ else 0.07) * SR); t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 7500) * np.exp(-t / (0.11 if open_ else 0.018))
    return x * (0.22 if open_ else 0.2)


def crash():
    n = int(2.2 * SR); t = np.arange(n) / SR
    x = hp(rng.standard_normal((n, 2)), 4500) * np.exp(-t / 0.7)[:, None]
    return x * 0.22


def boom():
    n = int(2.0 * SR); t = np.arange(n) / SR
    f = 32 + 70 * np.exp(-t / 0.08)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7)
    nz = lp(rng.standard_normal(n), 900) * np.exp(-t / 0.18) * 0.5
    return np.tanh(1.3 * (sub + nz)) * 0.9


def riser(dur, f0=300, f1=9000):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal((n, 2))
    fc = f0 * (f1 / f0) ** (t / dur)
    y = sweep_lp(hp(x, 200), fc)
    amp = (t / dur) ** 2.2
    tone_f = 200 * (8) ** (t / dur)
    tone = np.sin(2 * np.pi * np.cumsum(tone_f) / SR) * amp * 0.15
    return y * amp[:, None] * 0.5 + tone[:, None]


def whoosh(dur=0.6, up=True):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal((n, 2))
    u = t / dur
    fc = (400 * (12 ** u)) if up else (5000 * (0.08 ** u))
    y = sweep_lp(hp(x, 150), fc)
    amp = np.sin(np.pi * u) ** 1.5
    return y * amp[:, None] * 0.45


def pop():
    n = int(0.09 * SR); t = np.arange(n) / SR
    f = 1100 * np.exp(-t / 0.02) + 350
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.03) * 0.35


def tom(freq=110):
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = freq * (1 + 0.6 * np.exp(-t / 0.03))
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18) * 1.4) * 0.6


def supersaw(midi_notes, dur, cutoff=3500, voices=7, detune=0.22, rel=0.25, attack=0.01):
    n = int((dur + rel) * SR)
    out = np.zeros((n, 2))
    offs = np.linspace(-detune, detune, voices)
    for m in midi_notes:
        for k, o in enumerate(offs):
            f = midi_hz(m + o)
            s = polyblep_saw(f, n, rng.random())
            pan = (k / (voices - 1)) * 2 - 1
            out[:, 0] += s * np.cos((pan * 0.8 + 1) * np.pi / 4)
            out[:, 1] += s * np.sin((pan * 0.8 + 1) * np.pi / 4)
    out /= (voices * len(midi_notes)) ** 0.5 * 2.2
    e = env_adsr(n, a=attack, d=0.2, s=0.8, r=rel, hold=dur)[:n]
    return lp(out * e[:, None], cutoff)


def pluck(m, dur=0.18, cutoff=5000):
    n = int((dur + 0.05) * SR); t = np.arange(n) / SR
    f = midi_hz(m)
    s = polyblep_saw(f, n) * 0.6 + np.sign(np.sin(2 * np.pi * f * 2 * t)) * 0.15
    e = np.exp(-t / (dur * 0.45))
    return lp(s * e, cutoff) * 0.35


def bass_note(m, dur):
    n = int((dur + 0.02) * SR); t = np.arange(n) / SR
    f = midi_hz(m)
    s = polyblep_saw(f, n) * 0.5 + np.sin(2 * np.pi * f * t) * 0.9
    e = env_adsr(n, a=0.004, d=0.08, s=0.8, r=0.02, hold=dur)[:n]
    return lp(s * e, 520) * 0.55


def lead_note(m, dur):
    n = int((dur + 0.12) * SR); t = np.arange(n) / SR
    f = midi_hz(m)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.12) / 0.1, 0, 1)
    ph = np.cumsum(f * vib) / SR
    s = (2 * (ph % 1) - 1) * 0.5 + np.sign(np.sin(2 * np.pi * ph)) * 0.25
    s2 = (2 * ((ph * 1.004 + 0.3) % 1) - 1) * 0.35
    e = env_adsr(n, a=0.006, d=0.12, s=0.75, r=0.1, hold=dur)[:n]
    return lp((s + s2) * e, 4200) * 0.3


def make_ir(dur=2.2, decay=0.55, bright=6000):
    n = int(dur * SR); t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t / decay)[:, None]
    ir = lp(ir, bright)
    ir[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def reverb(x, ir):
    y = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], axis=1)
    return y


def delay(x, time, fb=0.35, mix=0.3):
    d = int(time * SR)
    y = x.copy()
    tap = x.copy()
    for k in range(1, 5):
        tap = np.roll(tap, d, axis=0); tap[:d] = 0
        tap = tap * fb
        # ping-pong
        y[:, (k % 2)] += tap[:, 0] * mix * 2
    return y


# --------------------------------------------------------------- arrangement
CHORDS = {  # voicing, bass root
    'Am': ([57, 60, 64, 69], 33),
    'F': ([53, 57, 60, 65], 29),
    'C': ([55, 60, 64, 67], 36),
    'G': ([55, 59, 62, 67], 31),
}
PROG = ['Am', 'F', 'C', 'G']


def chord_of(bar):
    return PROG[(bar - 1) % 4]


MELODY = [  # (slot16, len16, midi) per bar, 4-bar phrase
    [(0, 3, 76), (3, 1, 76), (4, 2, 74), (6, 2, 72), (8, 2, 74), (10, 4, 76), (14, 2, 69)],
    [(0, 3, 77), (3, 1, 76), (4, 2, 74), (6, 2, 72), (8, 4, 69), (12, 2, 72), (14, 2, 74)],
    [(0, 3, 76), (3, 1, 76), (4, 2, 79), (6, 2, 76), (8, 2, 74), (10, 4, 72), (14, 2, 74)],
    [(0, 3, 74), (3, 1, 71), (4, 4, 67), (8, 2, 71), (10, 2, 74), (12, 4, 79)],
]

drums = buf(); bass = buf(); chords = buf(); lead = buf(); arp = buf(); fx = buf(); pad = buf()
kick_times = []

K = kick(); CL = clap(); HC = hat(); HO = hat(True); CR = crash(); BO = boom()

# section helpers
INTRO = range(1, 3); TITLE = range(3, 5); NEED = range(5, 9); STEPS = range(9, 15)
BUILD = range(15, 17); DROP = range(17, 25); SCI = range(25, 31); OUT = range(31, 33)


def groove(bar, clap_on=True, hats=True, open_hats=True, kick_on=True, hat_gain=1.0):
    for b in range(4):
        t = bar_t(bar, b)
        if kick_on:
            place(drums, K, t, 1.0); kick_times.append(t)
        if clap_on and b in (1, 3):
            place(drums, CL, t, 0.9, pan=0.05)
        if hats:
            for s in range(4):
                v = [0.55, 0.35, 1.0, 0.4][s] * hat_gain
                if open_hats and s == 2:
                    place(drums, HO, t + s * S16, 0.9 * hat_gain, pan=0.25)
                else:
                    place(drums, HC, t + s * S16, v, pan=0.3 if s % 2 else -0.2)


def bass_offbeat(bar, gain=1.0):
    root = CHORDS[chord_of(bar)][1] + 12
    for b in range(4):
        place(bass, bass_note(root, BEAT / 2 * 0.9), bar_t(bar, b + 0.5), gain)


def bass_rolling(bar, gain=1.0):
    root = CHORDS[chord_of(bar)][1] + 12
    for s in range(16):
        if s % 4 == 0:
            continue
        m = root + (12 if s % 4 == 2 else 0)
        place(bass, bass_note(m, S16 * 0.85), bar_t(bar) + s * S16, gain * (1.0 if s % 4 == 2 else 0.8))


def arp_bar(bar, gain=1.0, cutoff=5000):
    notes = CHORDS[chord_of(bar)][0]
    seq = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[3] + 12, notes[2] + 12, notes[1] + 12, notes[3] + 12, notes[2] + 12] * 2
    for s in range(16):
        place(arp, pluck(seq[s], cutoff=cutoff), bar_t(bar) + s * S16, gain * (1.0 if s % 2 == 0 else 0.7),
              pan=-0.3 if s % 2 else 0.3)


def chord_hold(bar, gain=1.0, cutoff=4000, beats=4):
    notes = CHORDS[chord_of(bar)][0]
    place(chords, supersaw(notes + [notes[0] + 12], beats * BEAT * 0.98, cutoff=cutoff), bar_t(bar), gain)


def chord_stabs(bar, gain=1.0, cutoff=3200):
    notes = CHORDS[chord_of(bar)][0]
    for slot in (0, 3, 6, 10, 12):
        place(chords, supersaw(notes, S16 * 1.6, cutoff=cutoff, rel=0.08), bar_t(bar) + slot * S16, gain)


def pad_bar(bar, gain=1.0, cutoff=1800):
    notes = CHORDS[chord_of(bar)][0]
    place(pad, supersaw([m - 12 for m in notes[:3]] + notes[:3], BAR, cutoff=cutoff, voices=5, detune=0.12, attack=0.15, rel=0.4), bar_t(bar), gain)


def melody_bar(bar, gain=1.0, octave=0):
    phrase = MELODY[(bar - 1) % 4]
    for slot, ln, m in phrase:
        place(lead, lead_note(m + octave, ln * S16 * 0.92), bar_t(bar) + slot * S16, gain)


# INTRO (hook) --------------------------------------------------------------
for bar in INTRO:
    arp_bar(bar, 0.8, cutoff=2500 if bar == 1 else 4000)
    pad_bar(bar, 0.9, cutoff=900 if bar == 1 else 1500)
    for b in range(4):
        t = bar_t(bar, b)
        place(drums, lp(K, 800), t, 0.8); kick_times.append(t)
# snare roll bar 2
for s in range(16):
    place(drums, snare(0.3 + 0.7 * s / 15), bar_t(2) + s * S16, 0.9)
place(fx, riser(BAR * 2 - 0.05, 400, 8000), bar_t(1), 0.6)
place(fx, BO, 0.0, 0.55)  # opening thump on the hook

# TITLE ---------------------------------------------------------------------
place(fx, BO, bar_t(3), 1.0); place(drums, CR, bar_t(3), 1.0)
for bar in TITLE:
    groove(bar, clap_on=True, open_hats=False)
    bass_offbeat(bar)
    chord_hold(bar, 0.7, cutoff=2500)
    arp_bar(bar, 0.5)

# YOU'LL NEED ---------------------------------------------------------------
place(drums, CR, bar_t(5), 0.6)
for bar in NEED:
    groove(bar)
    bass_offbeat(bar)
    arp_bar(bar, 0.85)
    pad_bar(bar, 0.6)

# STEPS ---------------------------------------------------------------------
place(drums, CR, bar_t(9), 0.8)
for bar in STEPS:
    groove(bar)
    bass_offbeat(bar)
    arp_bar(bar, 0.7)
    chord_stabs(bar, 0.55 if bar < 11 else 0.7)
    pad_bar(bar, 0.45)

# BUILD (voice countdown sits on top) --------------------------------------
place(drums, CR, bar_t(15), 0.5)
groove(15, clap_on=False, open_hats=False)
bass_offbeat(15, 0.8)
pad_bar(15, 0.7, cutoff=2500)
pad_bar(16, 0.7, cutoff=3500)
for s in range(8):
    place(drums, snare(0.35 + 0.3 * s / 7), bar_t(15) + s * 2 * S16, 0.8)
for s in range(16):
    place(drums, snare(0.55 + 0.45 * s / 15), bar_t(16) + s * S16, 0.85)
# 32nd roll over the last two beats
for s in range(16):
    place(drums, snare(0.7 + 0.3 * s / 15), bar_t(16, 2) + s * S16 / 2, 0.6)
place(fx, riser(BAR * 2 - 0.2, 300, 12000), bar_t(15), 0.9)

# DROP ----------------------------------------------------------------------
place(fx, BO, bar_t(17), 1.1); place(drums, CR, bar_t(17), 1.2); place(drums, CR, bar_t(21), 0.9)
for bar in DROP:
    groove(bar)
    bass_rolling(bar, 0.95)
    chord_hold(bar, 0.85, cutoff=5500)
    melody_bar(bar, 1.0)
    arp_bar(bar, 0.45, cutoff=6000)
for s in range(8):  # fill into science
    place(drums, snare(0.5 + 0.5 * s / 7), bar_t(24, 2) + s * S16, 0.7)

# SCIENCE -------------------------------------------------------------------
place(drums, CR, bar_t(25), 0.8)
for bar in SCI:
    groove(bar, open_hats=bar >= 27, hat_gain=0.8)
    bass_offbeat(bar, 0.85)
    arp_bar(bar, 0.75, cutoff=3500)
    pad_bar(bar, 0.7, cutoff=2200)
place(fx, riser(BAR * 2 - 0.1, 400, 9000), bar_t(29), 0.55)

# OUTRO ---------------------------------------------------------------------
place(fx, BO, bar_t(31), 0.9); place(drums, CR, bar_t(31), 1.0)
for bar in OUT:
    groove(bar)
    bass_rolling(bar, 0.9)
    chord_hold(bar, 0.8, cutoff=5000)
    melody_bar(bar + 2, 0.9)  # bars 3-4 of the phrase: resolves nicely into the final hit
# final hit (Am) at bar 33
final_t = bar_t(33)
notes = CHORDS['Am'][0]
place(chords, supersaw(notes + [notes[0] + 12, notes[0] - 12], 2.2, cutoff=5000, rel=0.8), final_t, 1.0)
_b = bass_note(33 + 12, 1.8); place(bass, _b * np.exp(-np.arange(len(_b)) / SR / 0.9), final_t, 1.0)
place(fx, BO, final_t, 1.1); place(drums, CR, final_t, 1.2); place(drums, K, final_t, 1.0)
_l = lead_note(81, 1.2); place(lead, _l * np.exp(-np.arange(len(_l)) / SR / 0.6), final_t, 0.7)

# ------------------------------------------------------------------- mixing
# sidechain
sc = np.ones(N)
dur_sc = int(0.22 * SR)
shape = 1 - 0.75 * np.exp(-np.arange(dur_sc) / SR / 0.07) * (1 - np.exp(-np.arange(dur_sc) / SR / 0.003))
shape = np.minimum(shape, 1.0)
shape[:int(0.004 * SR)] = np.linspace(1, shape[int(0.004 * SR)], int(0.004 * SR))
for t in kick_times:
    i = int(t * SR)
    n = min(dur_sc, N - i)
    sc[i:i + n] = np.minimum(sc[i:i + n], shape[:n])
sc2 = sc[:, None]

ir_big = make_ir(2.4, 0.6)
ir_small = make_ir(1.0, 0.25)

lead_d = delay(lead, BEAT * 0.75, fb=0.4, mix=0.25)
G = dict(drums=0.5, bass=1.35, chords=1.7, pad=1.7, arp=2.4, lead=2.8, fx=0.7)
mix = (
    drums * G['drums']
    + reverb(drums * 0.06, ir_small) * 0.5
    + bass * sc2 * G['bass']
    + chords * sc2 * G['chords']
    + pad * sc2 * G['pad']
    + arp * sc2 * G['arp']
    + lead_d * G['lead']
    + reverb(chords * 0.35 + lead * 0.9 + arp * 0.6 + pad * 0.4, ir_big) * sc2 * 0.9
    + fx * G['fx']
    + reverb(fx * 0.25, ir_big)
)


def _r(x, b0, b1):
    seg = x[int(bar_t(b0) * SR):int(bar_t(b1) * SR)]
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)


for nm, st in [('drums', drums * G['drums']), ('bass', bass * sc2 * G['bass']), ('chords', chords * sc2 * G['chords']),
               ('pad', pad * sc2 * G['pad']), ('arp', arp * sc2 * G['arp']), ('lead', lead_d * G['lead']), ('fx', fx * G['fx'])]:
    print(f"{nm:7s} steps {_r(st, 9, 15):6.1f}  drop {_r(st, 17, 25):6.1f}  sci {_r(st, 25, 31):6.1f}")

# section dynamics (drop + outro hit hardest)
auto_pts = [(0, 0.78), (bar_t(3), 0.95), (bar_t(5), 0.8), (bar_t(9), 0.84), (bar_t(15), 0.84), (bar_t(17) - 0.01, 0.95),
            (bar_t(17), 1.0), (bar_t(25) - 0.01, 1.0), (bar_t(25), 0.8), (bar_t(29), 0.8), (bar_t(31) - 0.01, 0.9),
            (bar_t(31), 1.0), (TOTAL, 1.0)]
tt = np.arange(N) / SR
master = np.interp(tt, [p[0] for p in auto_pts], [p[1] for p in auto_pts])
mix *= master[:, None]
mix = hp(mix, 28)
# tail fade
fade_start = int((final_t + 1.8) * SR)
mix[fade_start:] *= np.linspace(1, 0, N - fade_start)[:, None] ** 2

# gentle glue + limiter
mix *= 0.9 / (np.percentile(np.abs(mix), 99.9) + 1e-9)
mix = np.tanh(mix * 1.25) / np.tanh(1.25)
mix *= 0.89 / np.max(np.abs(mix))


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()


write_wav('music.wav', mix)

# ------------------------------------------------------------------ SFX stem
import json
sfx = buf()
ev = json.load(open('sfx_events.json'))
bank = {'pop': lambda: pop(), 'whoosh': lambda: whoosh(0.55), 'whoosh_down': lambda: whoosh(0.7, up=False),
        'tom': lambda: tom(95), 'tom_hi': lambda: tom(130), 'tom_lo': lambda: tom(75)}
for e in ev:
    x = bank[e['type']]()
    place(sfx, x, e['t'] - (0.3 if e['type'].startswith('whoosh') else 0.0), e.get('gain', 1.0))
sfx = sfx + reverb(sfx * 0.15, ir_small)
write_wav('sfx.wav', sfx * 0.8)
print('ok', TOTAL, 'final hit at', final_t)
