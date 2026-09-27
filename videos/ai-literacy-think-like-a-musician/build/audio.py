"""Builds the soundtrack: narration + session-clip audio + an original synthesized music bed.

usage: python audio.py <session.mp4> <workdir>
Writes <workdir>/mix_raw.wav and <workdir>/soundtrack.wav (loudness-normalized to -14 LUFS).
All music and sound effects are generated here from scratch (no third-party audio).
"""
import json
import os
import re
import subprocess
import sys

import numpy as np

from timeline import Cues, build

SR = 48000


def ff_read(args):
    cmd = ["ffmpeg", "-v", "error"] + args + ["-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)


def lufs(x):
    """Integrated loudness of a stereo float array via ffmpeg's ebur128."""
    p = subprocess.run(
        ["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
         "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
        input=np.ascontiguousarray(x, dtype=np.float32).tobytes(), capture_output=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr.decode())
    return float(m[-1])


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def pluck(f, dur=1.6, bright=1.0):
    """Marimba-ish mallet tone (sine + inharmonic partials, fast decay)."""
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
    trem = 1 + 0.06 * np.sin(2 * np.pi * 0.21 * t)
    return (s * env * trem).astype(np.float32)


def add(buf, sig, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    if sig.ndim == 1:
        left, right = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        buf[i:i + len(sig), 0] += sig * gain * left * 1.414
        buf[i:i + len(sig), 1] += sig * gain * right * 1.414
    else:
        buf[i:i + len(sig)] += sig * gain


def music_bed(total):
    """Original I-vi-IV-V loop at 96 bpm: soft pad + gentle mallet arpeggio."""
    beat = 60 / 96
    bar = 4 * beat
    chords = [[48, 55, 64, 71], [45, 52, 60, 67], [41, 48, 57, 64], [43, 50, 59, 64]]
    buf = np.zeros((int(total * SR) + SR * 4, 2), np.float32)
    t = 0.0
    i = 0
    arp = [0, 1, 2, 3, 2, 1, 2, 3]
    while t < total:
        ch = chords[i % 4]
        for n in ch:
            add(buf, pad_note(midi(n), bar), t, 0.10, pan=(n - 55) / 40)
        for k, step in enumerate(arp):
            n = ch[step] + 12 + (12 if step == 3 and i % 2 else 0)
            add(buf, pluck(midi(n), 1.2, 0.6), t + k * beat / 2, 0.05 * (1.0 if k % 2 == 0 else 0.7),
                pan=0.35 if k % 2 else -0.35)
        t += bar
        i += 1
    return buf[: int(round(total * SR))]


def smooth(env, secs):
    n = max(1, int(secs * SR))
    k = np.ones(n, np.float32) / n
    return np.convolve(env, k, mode="same")


def main():
    src, work = sys.argv[1:3]
    tl = build(work)
    total = tl[-1]["start"] + tl[-1]["dur"]
    N = int(round(total * SR))
    vo = np.zeros((N, 2), np.float32)
    clips = np.zeros((N, 2), np.float32)
    fx = np.zeros((N, 2), np.float32)
    vo_active = np.zeros(N, np.float32)
    clip_active = np.zeros(N, np.float32)

    for sc in tl:
        for it in sc["items"]:
            t0 = sc["start"] + it["start"]
            if it["kind"] == "vo":
                x = ff_read(["-i", os.path.join(work, "vo", it["id"] + ".wav"), "-ar", str(SR), "-ac", "1"])
                add(vo, x, t0)
                i = int(t0 * SR)
                vo_active[i:i + len(x)] = 1
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
                i = int(t0 * SR)
                clip_active[i:i + int(it["dur"] * SR)] = 1

    # Sound design cues tied to the picture.
    by_id = {s["id"]: s for s in tl}
    hook = by_id["hook"]
    hc = Cues(hook)
    melody = [72, 76, 79] * 3 + [72, 76]
    for k, n in enumerate(melody):
        add(fx, pluck(midi(n), 1.6), hook["start"] + 0.4 + k * 0.32, 0.30, pan=-0.2 + 0.04 * k)
    t_res = hook["start"] + hc("h2")
    add(fx, pluck(midi(79), 2.0), t_res, 0.34)
    add(fx, pluck(midi(91), 2.0, 0.4), t_res + 0.02, 0.10)
    # Title sting: rolled C major chord.
    ts = by_id["title"]["start"]
    for k, n in enumerate([60, 64, 67, 72, 76]):
        add(fx, pluck(midi(n), 2.4), ts + 0.05 + k * 0.07, 0.16, pan=-0.4 + 0.2 * k)
    # Two-note "move" chime at each "Move N" line and at the challenge.
    for sid, vid in (("m1_intro", "m1a"), ("m2", "m2a"), ("m3", "m3a"), ("m4", "m4a"), ("m5", "m5a"), ("challenge", "c1")):
        s = by_id[sid]
        t = s["start"] + Cues(s)(vid) - 0.25
        add(fx, pluck(midi(79), 1.4), t, 0.13, pan=-0.2)
        add(fx, pluck(midi(84), 1.6), t + 0.11, 0.13, pan=0.2)

    # Music bed: starts with the hook's resolution, quieter under narration, off during clips.
    bed = music_bed(total)
    bed_gain = np.full(N, 0.0, np.float32)
    start_i = int(t_res * SR)
    bed_gain[start_i:] = 1.0
    auto = np.where(vo_active > 0, 0.55, 1.0).astype(np.float32)
    auto = smooth(auto, 0.6)
    bed_gain *= auto
    bed_gain *= 1 - smooth(clip_active, 0.8)
    fade_in = np.clip((np.arange(N) - start_i) / (1.5 * SR), 0, 1)
    bed_gain *= fade_in.astype(np.float32)
    tail = int((total - 2.5) * SR)
    bed_gain[tail:] *= np.linspace(1, 0, N - tail, dtype=np.float32)
    bed = np.pad(bed, ((0, max(0, N - len(bed))), (0, 0)))[:N] * bed_gain[:, None]

    # Balance stems by loudness: narration and clips at speech level, bed well underneath.
    g_vo = 10 ** ((-16.0 - lufs(vo)) / 20)
    g_clip = 10 ** ((-16.5 - lufs(clips)) / 20)
    g_bed = 10 ** ((-33.0 - lufs(bed)) / 20)
    g_fx = 10 ** ((-27.0 - lufs(fx)) / 20)
    print("gains", g_vo, g_clip, g_bed, g_fx)
    mix = vo * g_vo + clips * g_clip + bed * g_bed + fx * g_fx
    raw = os.path.join(work, "mix_raw.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", raw], input=mix.astype(np.float32).tobytes(), check=True)

    # Two-pass EBU R128 normalization to YouTube's -14 LUFS reference, -1 dBTP ceiling.
    p = subprocess.run(["ffmpeg", "-v", "info", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True)
    js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode()).group(0))
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}")
    out = os.path.join(work, "soundtrack.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le",
                    out], check=True)
    print("soundtrack", out, "duration", total)


if __name__ == "__main__":
    main()
