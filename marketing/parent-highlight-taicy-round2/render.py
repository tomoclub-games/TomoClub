#!/usr/bin/env python3
"""Render the TAICY Round 2 parent highlight from the full Zoom recording.

    python3 render.py --source "source/TAICY Round 2.mp4"   # final video
    python3 render.py --placeholder                         # layout draft, no footage needed

Needs: Python 3.9+, Pillow, numpy, qrcode, and ffmpeg (on PATH, or
`pip install imageio-ffmpeg`). Output goes to out/ (video, .srt captions,
edit report).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import wave

import numpy as np
from PIL import Image

import graphics as g

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = json.load(open(os.path.join(HERE, "edl.json")))["output"]["fps"]
SR = 48000


def ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg not found: install it or `pip install imageio-ffmpeg`")


FF = ffmpeg_bin()


def run(args, quiet=True):
    cmd = [FF, "-hide_banner", "-y"] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(" ".join(cmd), file=sys.stderr)
        print(r.stderr[-4000:], file=sys.stderr)
        sys.exit("ffmpeg failed")
    return r.stderr


# ------------------------------------------------------------------ audio analysis

def load_audio_mono(src, rate=16000):
    """Whole source soundtrack as mono float32 (cached next to the source)."""
    cache = os.path.splitext(src)[0] + f".mono{rate}.npy"
    if os.path.exists(cache):
        return np.load(cache)
    raw = subprocess.run([FF, "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    np.save(cache, a)
    return a


def energy_db(audio, rate=16000, hop=0.01, win=0.03):
    h, w = int(rate * hop), int(rate * win)
    n = max(0, (len(audio) - w) // h)
    frames = np.lib.stride_tricks.as_strided(audio, (n, w), (audio.strides[0] * h, audio.strides[0]))
    return 10 * np.log10(np.mean(frames ** 2, axis=1) + 1e-10)


def snap(t, env, hop=0.01, window=0.6, kind="in"):
    """Move a cut to the quietest 120 ms within +/-window s, so no word is clipped.

    Ties go to the point closest to the planned time."""
    i0, i1 = int((t - window) / hop), int((t + window) / hop)
    i0, i1 = max(i0, 0), min(i1, len(env) - 12)
    if i1 <= i0:
        return t
    smooth = np.convolve(env, np.ones(12) / 12, mode="same")
    seg = smooth[i0:i1]
    floor = seg.min()
    quiet = np.where(seg <= floor + 3.0)[0] + i0
    centre = t / hop
    best = quiet[np.argmin(np.abs(quiet - centre))]
    # cut in the middle of the pause, nudged toward the speech side by 60 ms
    return round(best * hop + (0.06 if kind == "out" else -0.06), 3)


def measure_lufs(path):
    err = run(["-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = err[err.rfind("Summary:"):]
    for line in tail.splitlines():
        line = line.strip()
        if line.startswith("I:"):
            return float(line.split()[1])
    return float("nan")


def clip_loudness(src, t0, dur):
    err = run(["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", src, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    for line in reversed(err.splitlines()):
        line = line.strip()
        if line.startswith("I:") and "LUFS" in line:
            return float(line.split()[1])
    return -23.0


# ------------------------------------------------------------------ music bed

def music_bed(path, seconds):
    """Soft, royalty-free pad + arpeggio, synthesised here so there is no licensing to clear."""
    t = np.arange(int(seconds * SR)) / SR
    bpm = 92
    beat = 60 / bpm
    bar = beat * 4
    # Fmaj9 - Am7 - Dm9 - Bbmaj7 (MIDI note numbers)
    prog = [[53, 57, 60, 64, 67], [45, 57, 60, 64, 67], [50, 57, 60, 65, 69], [46, 58, 62, 65, 69]]
    out = np.zeros((len(t), 2), np.float32)

    def hz(m):
        return 440 * 2 ** ((m - 69) / 12)

    n_bars = int(np.ceil(seconds / bar)) + 1
    for b in range(n_bars):
        chord = prog[b % 4]
        s0, s1 = int(b * bar * SR), int((b + 1) * bar * SR + 1.5 * SR)
        s1 = min(s1, len(t))
        if s0 >= len(t):
            break
        tt = t[s0:s1] - b * bar
        env = np.minimum(tt / 1.2, 1) * np.clip((bar + 1.5 - tt) / 1.5, 0, 1)
        for k, m in enumerate(chord):
            for ch, det in ((0, -0.0012), (1, 0.0012)):
                f = hz(m) * (1 + det)
                wave_ = np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt) + 0.08 * np.sin(6 * np.pi * f * tt)
                out[s0:s1, ch] += 0.05 * env * wave_ * (0.8 if k == 0 else 0.55)
        # gentle eighth-note arpeggio over the top voices
        arp = chord[1:] + [chord[2] + 12]
        for i in range(8):
            m = arp[i % len(arp)] + 12
            a0 = int((b * bar + i * beat / 2) * SR)
            a1 = min(a0 + int(1.2 * SR), len(t))
            if a0 >= len(t):
                break
            ta = t[a0:a1] - (b * bar + i * beat / 2)
            e = np.exp(-ta * 4.5) * np.minimum(ta / 0.004, 1)
            p = np.sin(2 * np.pi * hz(m) * ta) + 0.15 * np.sin(4 * np.pi * hz(m) * ta)
            pan = 0.35 + 0.3 * (i % 2)
            out[a0:a1, 0] += 0.035 * e * p * (1 - pan)
            out[a0:a1, 1] += 0.035 * e * p * pan
    # normalise to -3 dBFS peak (a low-pass is applied when the bed is mixed)
    out *= 10 ** (-3 / 20) / (np.abs(out).max() + 1e-9)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ segments

VENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level:v", "4.1", "-g", str(FPS * 2), "-bf", "2",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-r", str(FPS)]
AENC_SEG = ["-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "2"]


def footage_chain(blur_regions):
    """Source video -> 1408x792 window (letterboxed if needed), with privacy blur applied first."""
    x, y, w, h = g.FOOT
    parts = [f"[0:v]setpts=PTS-STARTPTS,fps={FPS}[s0]"]
    base = "[s0]"
    for i, r in enumerate(blur_regions):
        parts.append(f"{base}split[k{i}][c{i}]")
        parts.append(f"[c{i}]crop={r['w']}:{r['h']}:{r['x']}:{r['y']},boxblur=luma_radius=10:luma_power=4:chroma_radius=5:chroma_power=4[bl{i}]")
        parts.append(f"[k{i}][bl{i}]overlay={r['x']}:{r['y']}[s{i + 1}]")
        base = f"[s{i + 1}]"
    parts.append(f"{base}scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
                 f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x0B1220,setsar=1,"
                 f"pad={g.W}:{g.H}:{x}:{y}:color=0x080D1B[foot]")
    return ";".join(parts)


def placeholder_frame(item):
    """Stand-in for footage in draft renders: shows which source moment belongs here."""
    from PIL import ImageDraw
    im = Image.new("RGB", (1280, 720), (36, 44, 60))
    d = ImageDraw.Draw(im)
    for i in range(0, 1280, 80):
        d.line([i, 0, i, 720], fill=(44, 54, 72))
    for j in range(0, 720, 80):
        d.line([0, j, 1280, j], fill=(44, 54, 72))
    m, sec = divmod(item["in"], 60)
    d.text((640, 300), "ZOOM FOOTAGE GOES HERE", font=g.font(700, 40), fill=(148, 163, 184), anchor="mm")
    d.text((640, 370), f"{item['id']}  ·  source {int(m // 60):02}:{int(m % 60):02}:{sec:05.2f}", font=g.font(600, 34), fill=(248, 250, 252), anchor="mm")
    return im


def render_clip(item, src, placeholder, gfx, seg_path, gain_db, blur):
    dur = item["out"] - item["in"]
    args = []
    if placeholder:
        ph = os.path.join(os.path.dirname(gfx["frame"]), f"ph_{item['id']}.png")
        placeholder_frame(item).save(ph)
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", ph,
                 "-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"sine=frequency=330:sample_rate={SR},volume=0.02"]
    else:
        # video can come from elsewhere in the recording (B-roll of the round being discussed)
        v_in = item.get("video_in", item["in"])
        args += ["-ss", f"{v_in:.3f}", "-t", f"{dur:.3f}", "-i", src,
                 "-ss", f"{item['in']:.3f}", "-t", f"{dur:.3f}", "-i", src]
    overlays = [gfx["frame"], gfx["side"][item["side_key"]]] + [c["png"] for c in item["caps"]]
    for p in overlays:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", p]
    aidx = 1
    first = 2
    fc = footage_chain(blur)
    cur = "[foot]"
    fc += f";{cur}[{first}:v]overlay=0:0[v1];[v1][{first + 1}:v]overlay=0:0[v2]"
    cur = "[v2]"
    for k, c in enumerate(item["caps"]):
        nxt = f"[c{k}]"
        fc += f";{cur}[{first + 2 + k}:v]overlay=0:0:enable='between(t,{c['t0']:.3f},{c['t1'] - 0.001:.3f})'{nxt}"
        cur = nxt
    fc += f";{cur}format=yuv420p[vout]"
    fade_out = max(dur - 0.05, 0)
    fc += (f";[{aidx}:a]asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo,"
           f"pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,"
           f"highpass=f=80,volume={gain_db:.2f}dB,"
           f"acompressor=threshold=-20dB:ratio=2.5:attack=8:release=180:makeup=1,"
           f"afade=t=in:d=0.03,afade=t=out:st={fade_out:.3f}:d=0.05[aout]")
    run(args + ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-t", f"{dur:.3f}"] + VENC + AENC_SEG + [seg_path])


def render_card(layers, dur, gfx_dir, seg_path, music_wav, music_offset, fade_out_all=0.25):
    args = []
    for p, _ in layers:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", os.path.join(gfx_dir, p)]
    args += ["-ss", f"{music_offset:.3f}", "-t", f"{dur:.3f}", "-i", music_wav]
    fc = "[0:v]format=rgba[l0]"
    cur = "[l0]"
    for k, (_, t_in) in enumerate(layers[1:], start=1):
        fc += f";[{k}:v]format=rgba,fade=t=in:st={t_in:.2f}:d=0.45:alpha=1[f{k}];{cur}[f{k}]overlay=0:0[m{k}]"
        cur = f"[m{k}]"
    fc += f";{cur}fade=t=in:st=0:d=0.25,fade=t=out:st={dur - fade_out_all:.3f}:d={fade_out_all:.3f},format=yuv420p[vout]"
    n = len(layers)
    fc += (f";[{n}:a]asetpts=PTS-STARTPTS,aresample={SR},lowpass=f=5000,volume=-17dB,"
           f"afade=t=in:d=0.35,afade=t=out:st={max(dur - 0.6, 0):.3f}:d=0.6[aout]")
    run(args + ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-t", f"{dur:.3f}"] + VENC + AENC_SEG + [seg_path])


# ------------------------------------------------------------------ main

def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="full Zoom recording (mp4)")
    ap.add_argument("--placeholder", action="store_true", help="draft with test-pattern footage")
    ap.add_argument("--out", default=None)
    ap.add_argument("--build", default=os.path.join(HERE, "build"))
    ap.add_argument("--only", help="comma-separated item ids to render (for quick checks)")
    a = ap.parse_args()
    if not a.source and not a.placeholder:
        ap.error("give --source or --placeholder")

    edl = json.load(open(os.path.join(HERE, "edl.json")))
    build = a.build
    gdir = os.path.join(build, "gfx")
    sdir = os.path.join(build, "segments")
    os.makedirs(gdir, exist_ok=True)
    os.makedirs(sdir, exist_ok=True)
    out = a.out or os.path.join(HERE, edl["output"]["file"])
    if a.placeholder:
        out = out.replace(".mp4", "_PLACEHOLDER-DRAFT.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    # 1. static graphics
    g.frame_overlay().save(os.path.join(gdir, "frame.png"))
    side = {}
    for k, ch in edl["chapters"].items():
        p = os.path.join(gdir, f"side_{k}.png")
        g.sidebar(ch).save(p)
        side[k] = p
    cards = {"title": g.card_title(gdir), "outcomes": g.card_outcomes(gdir), "endcard": g.card_end(gdir)}
    for k, ch in edl["chapters"].items():
        if ch.get("num"):
            cards[f"chapter:{k}"] = g.card_chapter(gdir, k, ch)
    gfx = {"frame": os.path.join(gdir, "frame.png"), "side": side}

    # 2. snap cuts to pauses and match clip loudness (real footage only)
    seq = edl["sequence"]
    report = []
    if a.source:
        audio = load_audio_mono(a.source)
        env = energy_db(audio)
        prev_out = None
        for it in seq:
            if it["type"] != "clip":
                continue
            it["in_planned"], it["out_planned"] = it["in"], it["out"]
            s = it.get("snap", "")
            if s in ("in", "both"):
                it["in"] = snap(it["in"], env, kind="in")
            if s in ("out", "both"):
                it["out"] = snap(it["out"], env, kind="out")
            if prev_out is not None and abs(it["in_planned"] - prev_out[1]) < 0.5:
                it["in"] = max(it["in"], prev_out[0])  # adjacent source ranges must not overlap
            prev_out = (it["out"], it["out_planned"])
            lufs = clip_loudness(a.source, it["in"], it["out"] - it["in"])
            it["gain_db"] = max(min(-18.0 - lufs, 12.0), -12.0)
            report.append(f"{it['id']:16} in {it['in_planned']:9.2f} -> {it['in']:9.2f}   out {it['out_planned']:9.2f} -> {it['out']:9.2f}   {lufs:6.1f} LUFS  gain {it['gain_db']:+5.1f} dB")

    # every segment must be a whole number of frames, or the concatenated video drifts off 30 fps CFR
    for it in seq:
        if it["type"] == "clip":
            it["out"] = round(it["in"] + round((it["out"] - it["in"]) * FPS) / FPS, 4)
        else:
            it["dur"] = round(it["dur"] * FPS) / FPS

    # 3. captions: chunk each clip's text; time chunks from caption_timing.json (align_captions.py)
    #    when it matches, otherwise spread them over the clip by length
    tpath = os.path.join(HERE, "caption_timing.json")
    timing = json.load(open(tpath)) if (a.source and os.path.exists(tpath)) else {}
    for it in seq:
        if it["type"] != "clip":
            continue
        it["side_key"] = str(it["chapter"])
        if "stat" in it:
            p = os.path.join(gdir, f"side_stat_{it['id']}.png")
            g.sidebar(edl["chapters"][it["side_key"]], stat=it["stat"]).save(p)
            side[f"stat_{it['id']}"] = p
            it["side_key"] = f"stat_{it['id']}"
        chunks = g.chunk_caption(it["text"])
        dur = it["out"] - it["in"]
        starts = timing.get(it["id"])
        if not starts or len(starts) != len(chunks):
            weights = [len(" ".join(c)) + 8 for c in chunks]
            starts = [dur * sum(weights[:k]) / sum(weights) for k in range(len(chunks))]
        caps = []
        for k, c in enumerate(chunks):
            p = os.path.join(gdir, f"cap_{it['id']}_{k}.png")
            g.caption_png(c, it["role"], it.get("speaker")).save(p)
            t1 = starts[k + 1] if k + 1 < len(chunks) else dur
            caps.append({"png": p, "t0": min(starts[k], dur), "t1": min(t1, dur), "lines": c})
        it["caps"] = caps

    # 4. music bed for cards
    music = os.path.join(build, "music_bed.wav")
    card_total = sum(it["dur"] for it in seq if it["type"] == "card")
    music_bed(music, card_total + 2)

    # 5. render segments
    only = set(a.only.split(",")) if a.only else None
    segs, srt, t_out, m_off = [], [], 0.0, 0.0
    for n, it in enumerate(seq):
        seg = os.path.join(sdir, f"{n:02d}_{it['id'].replace(':', '-')}.mov")
        if it["type"] == "card":
            dur = it["dur"]
            if not only or it["id"] in only:
                render_card(cards[it["graphic"]], dur, gdir, seg, music, m_off,
                            fade_out_all=0.6 if it["id"] == "endcard" else 0.25)
            m_off += dur
            srt.append((t_out, t_out + dur, "[soft music]"))
        else:
            dur = it["out"] - it["in"]
            blur = edl.get("privacy_blur", {}).get(it.get("layout", ""), [])
            if a.placeholder:
                blur = []
            if not only or it["id"] in only:
                render_clip(it, a.source, a.placeholder, gfx, seg, it.get("gain_db", 0.0), blur)
            for c in it["caps"]:
                srt.append((t_out + c["t0"], t_out + c["t1"], "\n".join(c["lines"])))
        print(f"  [{n + 1:2}/{len(seq)}] {it['id']:16} {dur:5.2f}s  @ {t_out:6.2f}s", flush=True)
        segs.append(seg)
        t_out += dur
    if only:
        return

    # 6. concat, master audio to -14 LUFS / -1 dBTP (two-pass loudnorm), mux
    lst = os.path.join(build, "concat.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")
    joined = os.path.join(build, "joined.mov")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    I, TP = edl["output"]["loudness_lufs"], edl["output"]["true_peak_db"]
    err = run(["-i", joined, "-vn", "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"])
    js = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    ln = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    mastered = os.path.join(build, "mastered.wav")
    run(["-i", joined, "-vn", "-af", ln + f",aresample={SR}", "-c:a", "pcm_s24le", mastered])
    # loudnorm falls back to dynamic mode when linear gain would break the peak ceiling; check and trim
    got = measure_lufs(mastered)
    if abs(got - I) > 0.5:
        fixed = os.path.join(build, "mastered_fix.wav")
        run(["-i", mastered, "-af", f"volume={I - got:.2f}dB,alimiter=limit={10 ** (TP / 20):.4f}:level=false",
             "-c:a", "pcm_s24le", fixed])
        mastered = fixed
    run(["-i", joined, "-i", mastered, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-movflags", "+faststart",
         "-metadata", f"title={edl['title']}", "-metadata", "copyright=© 2026 TomoClub", out])
    report.insert(0, f"master loudness {measure_lufs(out):.1f} LUFS (target {I})")

    with open(os.path.splitext(out)[0] + ".srt", "w") as f:
        for i, (t0, t1, txt) in enumerate(srt, 1):
            f.write(f"{i}\n{srt_time(t0)} --> {srt_time(t1)}\n{txt}\n\n")
    with open(os.path.splitext(out)[0] + ".edit-report.txt", "w") as f:
        f.write(f"duration {t_out:.2f}s\n" + "\n".join(report) + "\n")
    print(f"\n{out}  ({t_out:.1f}s)")


if __name__ == "__main__":
    main()
