#!/usr/bin/env python3
"""Privacy pass for the TAICY promo footage: blur every student's face and name.

For each requested time range of a source recording this writes a clip in which
  * every student's Zoom tile is heavily blurred in gallery view (this also covers
    the Zoom name label at the bottom of the tile), and
  * the webcam/name strip in the top-right corner is blurred during screen share.
The facilitator's tile stays sharp. In-game player names are left as they are.

Gallery vs screen share is decided per frame (Zoom paints pure black around the
gallery tiles), so a view switch mid-shot is still covered. Around a switch both
blurs are applied for a few frames. A face check (OpenCV) then flags any face that
is visible outside the facilitator's tile.
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "parent-highlight-taicy-round2"))
from render import FF, run  # noqa: E402

ROOT = os.path.join(HERE, "..")
SOURCES = {
    # 3-tile gallery: student (top-left), VK (top-right), student (bottom-centre)
    "r2": {"path": os.path.join(ROOT, "parent-highlight-taicy-round2", "source", "TAICY Round 2.mp4"),
           "size": (2560, 1440), "gallery_black": [(40, 760, 600, 1400), (1960, 760, 2520, 1400)],
           "kid_tiles": [(0, 0, 1280, 720), (640, 720, 1280, 720)], "vk_tile": (1280, 0, 1280, 720),
           "strip": (2310, 0, 250, 412)},
    "sep20": {"path": os.path.join(HERE, "source", "sep20.mp4"),
              "size": (2560, 1440), "gallery_black": [(40, 760, 600, 1400), (1960, 760, 2520, 1400)],
              "kid_tiles": [(0, 0, 1280, 720), (640, 720, 1280, 720)], "vk_tile": (1280, 0, 1280, 720),
              "strip": (2310, 0, 250, 412)},
    # 2-tile gallery: student (left), VK (right), black bands above and below
    "oct04": {"path": os.path.join(HERE, "source", "oct04.mp4"),
              "size": (2560, 1318), "gallery_black": [(0, 20, 2560, 280), (0, 1040, 2560, 1300)],
              "kid_tiles": [(0, 298, 1280, 720)], "vk_tile": (1280, 298, 1280, 720),
              "strip": (2310, 0, 250, 278)},
    # Round 1 demo video filmed on a phone (portrait once rotated). Only face-free stretches are used, so
    # nothing is blurred; with no facilitator tile, the face check flags any face at all.
    "eco": {"path": os.path.join(ROOT, "taicy-wrapup", "source", "sudeep_submission.mp4"),
            "size": (1080, 2400), "gallery_black": [], "kid_tiles": [], "vk_tile": (0, 0, 0, 0), "strip": None},
}
SMALL_W = 256


def classify(src, t0, dur, fps=25):
    """Per-frame 'g' (gallery) or 's' (screen share)."""
    cfg = SOURCES[src]
    w, h = cfg["size"]
    sh = int(round(h * SMALL_W / w))
    raw = subprocess.run([FF, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", cfg["path"],
                          "-vf", f"fps={fps},scale={SMALL_W}:{sh}:flags=area,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, sh, SMALL_W)
    k = SMALL_W / w
    modes = []
    for f in frames:
        black = bool(cfg["gallery_black"]) and all(f[int(y0 * k):int(y1 * k), int(x0 * k):int(x1 * k)].mean() < 3
                                                   for x0, y0, x1, y1 in cfg["gallery_black"])
        modes.append("g" if black else "s")
    return modes


def windows(modes, want, fps=25, pad=3):
    """Time windows (s) where mode == want, widened by `pad` frames on each side."""
    on = np.array([m == want for m in modes])
    if pad:
        grown = on.copy()
        for d in range(1, pad + 1):
            grown[d:] |= on[:-d]
            grown[:-d] |= on[d:]
        on = grown
    out, start = [], None
    for i, v in enumerate(list(on) + [False]):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start / fps, i / fps))
            start = None
    return out


def enable_expr(wins):
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in wins) or "0"


def sanitize(src, t0, dur, out_path, fps=25):
    """Write a privacy-safe clip of src[t0:t0+dur] (video only, native resolution)."""
    cfg = SOURCES[src]
    modes = classify(src, t0, dur, fps)
    g_win, s_win = windows(modes, "g", fps), windows(modes, "s", fps)
    regions = [(r, g_win, 46) for r in cfg["kid_tiles"]] + ([(cfg["strip"], s_win, 22)] if cfg["strip"] else [])
    parts = [f"[0:v]setpts=PTS-STARTPTS,fps={fps}[s0]"]
    base = "[s0]"
    n = 0
    for (x, y, w, h), wins, sigma in regions:
        if not wins:
            continue
        parts.append(f"{base}split[k{n}][c{n}]")
        parts.append(f"[c{n}]crop={w}:{h}:{x}:{y},gblur=sigma={sigma}:steps=3,eq=brightness=-0.04:saturation=0.7[b{n}]")
        parts.append(f"[k{n}][b{n}]overlay={x}:{y}:enable='{enable_expr(wins)}'[s{n + 1}]")
        base = f"[s{n + 1}]"
        n += 1
    parts.append(f"{base}format=yuv420p[v]")
    run(["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", cfg["path"], "-filter_complex", ";".join(parts),
         "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-r", str(fps), out_path])
    return {"modes": "".join(modes), "gallery": g_win, "share": s_win}


def face_check(src, clip, every=0.2):
    """Return (time, box) for faces found outside the facilitator's tile."""
    import cv2
    cfg = SOURCES[src]
    det = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    cap = cv2.VideoCapture(clip)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(1, int(round(every * fps)))
    vx, vy, vw, vh = cfg["vk_tile"]
    hits, i = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            small = cv2.resize(frame, (frame.shape[1] // 2, frame.shape[0] // 2))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            for (x, y, w, h) in det.detectMultiScale(gray, 1.1, 6, minSize=(28, 28)):
                cx, cy = (x + w / 2) * 2, (y + h / 2) * 2
                in_vk = vx <= cx <= vx + vw and vy <= cy <= vy + vh
                if not in_vk:
                    hits.append((round(i / fps, 2), [int(v * 2) for v in (x, y, w, h)]))
        i += 1
    return hits


if __name__ == "__main__":
    src, t0, dur, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    info = sanitize(src, t0, dur, out)
    print(json.dumps({k: v for k, v in info.items() if k != "modes"}), info["modes"][:200])
    print("faces outside VK tile:", face_check(src, out))
