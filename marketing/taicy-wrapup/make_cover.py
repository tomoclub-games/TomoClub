#!/usr/bin/env python3
"""Instagram cover for the wrap-up Reel (writes out/TomoClub_TAICY-Wrap_Reel_9x16_cover.jpg, not committed).

    python3 make_cover.py

The hook headline over the three result screens from the Round 1 demo (tomato → wet, paper → dry,
mouse → e-waste). The tiles are tight crops of the tablet on the wall, so no person is in frame; a face
check on the finished image confirms it. Everything that matters sits inside the centre 1080×1440, the
part Instagram shows in the profile grid.
"""
import os
import subprocess
import sys
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "taicy-social-promo"))
import promo  # noqa: E402
import sanitize  # noqa: E402
from promo import g  # noqa: E402

OUT = os.path.join(HERE, "out", "TomoClub_TAICY-Wrap_Reel_9x16_cover.jpg")
DEMO = sanitize.SOURCES["eco"]["path"]
W, H = 1080, 1920
GRID = (240, 1680)  # rows Instagram keeps in the 3:4 profile-grid crop

# (time in the demo, tablet crop in source pixels, object, bin)
TILES = [
    (64.5, (345, 410, 865, 1230), "Tomato", "WET"),
    (82.0, (295, 515, 815, 1335), "Paper", "DRY"),
    (101.5, (335, 485, 855, 1305), "Mouse", "E-WASTE"),
]
TILE_W, TILE_H, GAP = 300, 473, 30
HEAD = [("A student built", False), ("a dustbin", False), ("that thinks.", True)]


def frame(t):
    raw = subprocess.run([promo.FF, "-v", "error", "-ss", f"{t:.3f}", "-i", DEMO, "-frames:v", "1", "-f", "image2pipe",
                          "-c:v", "png", "-"], capture_output=True, check=True).stdout
    return Image.open(BytesIO(raw)).convert("RGB")


def screen_colour(tile):
    """The tablet's result colour, sampled from the middle of the screen (used for the bin pill)."""
    a = np.asarray(tile).reshape(-1, 3)
    sat = a.max(axis=1).astype(int) - a.min(axis=1)
    return tuple(int(v) for v in np.median(a[sat > 90], axis=0))


def rounded(img, r):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], r, fill=255)
    return mask


def shadow(base, box, r, blur=18, alpha=170, dy=14):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 4, y0 + dy, x1 + 4, y1 + dy], r, fill=(0, 0, 0, alpha))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def main():
    fmt = dict(promo.FORMATS["reel"])
    img = promo.background(fmt)
    d = ImageDraw.Draw(img)

    # TAICY logo card
    st = promo.taicy_sticker(300)
    img.alpha_composite(st, ((W - st.width) // 2, 236))

    # hook headline, gold on the last line (as in the Reel's first shot)
    f = g.font(800, 116)
    y = 470
    for text, gold in HEAD:
        tw = d.textlength(text, font=f)
        d.text(((W - tw) / 2, y), text, font=f, fill=g.GOLD if gold else g.WHITE, stroke_width=4, stroke_fill=g.DEEP)
        y += 124

    # three result screens
    ty = 880
    x0 = (W - (3 * TILE_W + 2 * GAP)) // 2
    pf, lf = g.font(800, 34), g.font(600, 38)
    for i, (t, box, obj, bin_) in enumerate(TILES):
        tile = frame(t).crop(box).resize((TILE_W, TILE_H), Image.LANCZOS)
        x = x0 + i * (TILE_W + GAP)
        shadow(img, (x, ty, x + TILE_W, ty + TILE_H), 30)
        img.paste(tile, (x, ty), rounded(tile, 30))
        d.rounded_rectangle([x, ty, x + TILE_W - 1, ty + TILE_H - 1], 30, outline=(255, 255, 255, 60), width=2)
        cx = x + TILE_W / 2
        d.text((cx, ty + TILE_H + 26), obj, font=lf, fill=(203, 213, 225), anchor="mt")
        col = screen_colour(tile)
        pw = d.textlength(bin_, font=pf) + 52
        py = ty + TILE_H + 80
        d.rounded_rectangle([cx - pw / 2, py, cx + pw / 2, py + 58], 29, fill=col)
        d.text((cx, py + 29), bin_, font=pf, fill=g.WHITE, anchor="mm")

    # sign-off line
    f2 = g.font(800, 60)
    parts = [("TAICY 2026 is a ", g.WHITE), ("wrap!", g.GOLD)]
    tw = sum(d.textlength(s, font=f2) for s, _ in parts)
    x = (W - tw) / 2
    for s, c in parts:
        d.text((x, 1562), s, font=f2, fill=c)
        x += d.textlength(s, font=f2)

    out = img.convert("RGB")
    det = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    grey = cv2.cvtColor(np.asarray(out), cv2.COLOR_RGB2GRAY)
    assert len(det.detectMultiScale(grey, 1.1, 5, minSize=(40, 40))) == 0, "a face is visible on the cover"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT, quality=92)
    print(OUT)


if __name__ == "__main__":
    main()
