"""Renders the video.

  python render.py preview <session.mp4> <workdir> <scene_id> <t> [<t> ...]   -> PNG stills for checking
  python render.py scenes  <session.mp4> <workdir>                          -> one mp4 per scene
  python render.py final   <session.mp4> <workdir> <out.mp4>                -> concat + soundtrack, YouTube spec
"""
import functools
import multiprocessing
import os
import subprocess
import sys
import time

from PIL import Image, ImageEnhance, ImageFilter

import scenes
from gfx import FPS, H, W, Dyn, background
from script_data import CLIPS
from timeline import Cues, build


@functools.lru_cache(maxsize=None)
def ctx_for(src):
    bg = background()
    rainbow = scenes.still(src, 70.0, (W, H)).filter(ImageFilter.GaussianBlur(28))
    rainbow = ImageEnhance.Brightness(rainbow).enhance(0.55)
    return {
        "src": src,
        "clips": CLIPS,
        "bg": bg,
        "bg_exp": Image.blend(bg, rainbow, 0.33),
        "still_a": scenes.still(src, 33.0, (800, 450)),
    }


def elements(sc, src):
    ctx = ctx_for(src)
    els = scenes.BUILDERS[sc["id"]](sc, Cues(sc), ctx)
    for e in els:
        if e.t1 is None:
            e.t1 = sc["dur"] - 0.38
            e.fade = 0.32
    bg = ctx["bg_exp"] if sc["id"] == "exp_intro" else ctx["bg"]
    return bg, els


def frame_at(bg, els, t):
    f = bg.copy()
    for e in els:
        e.draw(f, t)
    return f


def render_scene(args):
    i, sc, src, work = args
    out = os.path.join(work, "scenes", f"{i:02d}_{sc['id']}.mp4")
    bg, els = elements(sc, src)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "10",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    t0 = time.time()
    for n in range(sc["frames"]):
        p.stdin.write(frame_at(bg, els, n / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return f"{sc['id']}: {sc['frames']} frames in {time.time() - t0:.0f}s"


def main():
    mode, src, work = sys.argv[1:4]
    tl = build(work)
    if mode == "preview":
        sid = sys.argv[4]
        sc = next(s for s in tl if s["id"] == sid)
        os.makedirs(os.path.join(work, "preview"), exist_ok=True)
        times = [float(x) for x in sys.argv[5:]]
        # clip scenes stream frames in order, so render sequentially up to each requested time
        bg, els = elements(sc, src)
        stream = any(isinstance(e, Dyn) and "video" in e.fn.__name__ for e in els)
        for t in sorted(times):
            if t < 0:
                t = sc["dur"] + t
            if stream:
                for n in range(int(t * FPS)):
                    frame_at(bg, els, n / FPS)
            t0 = time.time()
            f = frame_at(bg, els, t)
            path = os.path.join(work, "preview", f"{sid}_{t:05.2f}.png")
            f.save(path)
            print(path, f"{(time.time() - t0) * 1000:.0f} ms")
    elif mode == "scenes":
        os.makedirs(os.path.join(work, "scenes"), exist_ok=True)
        only = set(sys.argv[4:])
        jobs = [(i, s, src, work) for i, s in enumerate(tl) if not only or s["id"] in only]
        jobs.sort(key=lambda j: -j[1]["frames"])
        with multiprocessing.Pool(4) as pool:
            for msg in pool.imap_unordered(render_scene, jobs):
                print(msg, flush=True)
    elif mode == "final":
        out = sys.argv[4]
        lst = os.path.join(work, "scenes", "list.txt")
        with open(lst, "w") as f:
            for i, s in enumerate(tl):
                f.write(f"file '{i:02d}_{s['id']}.mp4'\n")
        # YouTube recommended upload settings: H.264 High, 4:2:0, closed GOP of half the frame
        # rate, AAC-LC 48 kHz stereo, moov atom at the front.
        subprocess.run(["ffmpeg", "-v", "error", "-stats", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-i", os.path.join(work, "soundtrack.wav"),
                        "-map", "0:v", "-map", "1:a",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.1",
                        "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS // 2), "-bf", "2",
                        "-x264-params", "open-gop=0", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-colorspace", "bt709",
                        "-c:a", "aac", "-b:a", "384k", "-ar", "48000", "-ac", "2",
                        "-movflags", "+faststart", "-shortest",
                        "-metadata", "title=Think Like a Musician: 5 AI Literacy Moves for Students",
                        "-metadata", "artist=TomoClub", out], check=True)
        print("wrote", out)


if __name__ == "__main__":
    main()
