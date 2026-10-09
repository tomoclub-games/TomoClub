#!/usr/bin/env python3
"""Images for the Substack wrap-up post (written to substack/images/, not committed).

    python3 substack/make_images.py

Stills come from face-free moments of the Round 1 demo video, a judging card is drawn with the
promo graphics, and the Round 2 still is a frame from a privacy-blurred clip made by sanitize.py.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PROMO = os.path.join(HERE, "..", "..", "taicy-social-promo")
sys.path.insert(0, PROMO)
import promo  # noqa: E402
import sanitize  # noqa: E402
from promo import g  # noqa: E402

OUT = os.path.join(HERE, "images")
DEMO = sanitize.SOURCES["eco"]["path"]


def frame(path, t):
    raw = subprocess.run([promo.FF, "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-f", "image2pipe",
                          "-c:v", "png", "-"], capture_output=True, check=True).stdout
    from io import BytesIO
    return Image.open(BytesIO(raw)).convert("RGB")


def cover():
    fmt = {"W": 1456, "H": 816, "wordmark": (300, 70, 40)}
    img = promo.background(fmt, hexes=False)
    # two tall photo panels on the right: wet (green) and e-waste (orange)
    for i, t in enumerate((64.5, 101.5)):
        ph = frame(DEMO, t).crop((150, 330, 930, 1630)).resize((330, 550), Image.LANCZOS)
        x, y = 760 + i * 350, 150 + i * 50
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([x + 10, y + 16, x + 340, y + 566], 28, fill=(0, 0, 0, 160))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
        mask = Image.new("L", ph.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, ph.width, ph.height], 28, fill=255)
        img.paste(ph, (x, y), mask)
    st = promo.taicy_sticker(380)
    img.alpha_composite(st, (90, 150))
    d = ImageDraw.Draw(img)
    f1, f2 = g.font(800, 66), g.font(600, 32)
    d.text((110, 420), "TAICY 2026", font=f1, fill=g.WHITE)
    d.text((110, 500), "The wrap-up", font=f1, fill=g.GOLD)
    d.text((112, 600), "A smart dustbin, a live team round,", font=f2, fill=(203, 213, 225))
    d.text((112, 644), "and what to let AI control.", font=f2, fill=(203, 213, 225))
    img.convert("RGB").save(os.path.join(OUT, "00-cover.jpg"), quality=90)


def stills():
    frame(DEMO, 64.5).crop((0, 250, 1080, 1600)).save(os.path.join(OUT, "01-drop-in-wet.jpg"), quality=90)
    frame(DEMO, 68.8).crop((0, 560, 1080, 1910)).save(os.path.join(OUT, "03-arrow-and-bins.jpg"), quality=90)


def judging():
    fmt = promo.FORMATS["linkedin"]
    tmp = os.path.join(OUT, "_cards")
    os.makedirs(tmp, exist_ok=True)
    layers = promo.card_layers(fmt, "rubric", tmp, {})
    img = Image.open(os.path.join(tmp, layers[0][0])).convert("RGBA")
    for p, _ in layers[1:]:
        img.alpha_composite(Image.open(os.path.join(tmp, p)))
    img.convert("RGB").save(os.path.join(OUT, "02-judging.jpg"), quality=90)
    for p, _ in layers:
        os.remove(os.path.join(tmp, p))
    os.rmdir(tmp)


def round2():
    """A gallery frame of Round 2 with every student tile blurred (the coach stays sharp)."""
    clip = os.path.join(OUT, "_r2.mov")
    sanitize.sanitize("r2", 168.6, 0.5, clip)
    assert not sanitize.face_check("r2", clip), "a face outside the coach's tile is visible"
    frame(clip, 0.2).resize((1280, 720), Image.LANCZOS).save(os.path.join(OUT, "04-round-2-live.jpg"), quality=90)
    os.remove(clip)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cover()
    stills()
    judging()
    round2()
    print("\n".join(sorted(os.listdir(OUT))))
