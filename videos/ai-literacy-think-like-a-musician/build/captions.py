"""Writes a YouTube-ready .srt caption file that matches the rendered timeline.

usage: python captions.py <workdir> <out.srt>
"""
import re
import sys

from script_data import CLIP_CAPTIONS, caption_text
from timeline import build

MAX_LINE = 42
SONG = {"clipA": [(28.4, 35.0)], "clipB": [(58.0, 59.4)]}


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap(text):
    if MAX_LINE < len(text) <= 2 * MAX_LINE:
        # two balanced lines read better than a long line plus a stray word
        spaces = [i for i, ch in enumerate(text) if ch == " "]
        best = min(spaces, key=lambda i: max(i, len(text) - i - 1))
        if max(best, len(text) - best - 1) <= MAX_LINE:
            return [text[:best], text[best + 1:]]
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > MAX_LINE:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    return lines


def chunks(text):
    """Split narration into caption-sized pieces (max two lines of 42 chars)."""
    parts = re.split(r"(?<=[.?!])\s+", text)
    out = []
    for p in parts:
        while len(wrap(p)) > 2:
            lines = wrap(p)
            head = " ".join(lines[:2])
            cut = max(head.rfind(", "), head.rfind(": "))
            if cut < 20:
                cut = len(lines[0]) + 1 + len(lines[1])
                out.append(p[:cut].strip())
                p = p[cut:].strip()
            else:
                out.append(p[:cut + 1].strip())
                p = p[cut + 1:].strip()
        if p:
            out.append(p)
    return out


def main():
    work, out = sys.argv[1:3]
    cues = []
    for sc in build(work):
        for it in sc["items"]:
            base = sc["start"] + it["start"]
            if it["kind"] == "vo":
                pieces = chunks(caption_text(it["text"]))
                total = sum(len(p) for p in pieces)
                t = base
                for p in pieces:
                    d = it["dur"] * len(p) / total
                    cues.append((t, t + d, p))
                    t += d
                continue
            off = 0.0
            first = True
            for a, b in it["segs"]:
                events = [(s, e, txt) for s, e, txt in CLIP_CAPTIONS]
                events += [(s, e, "[Student's song plays]") for s, e in SONG[it["id"]]]
                for s, e, txt in sorted(events):
                    if s < b and e > a:
                        if first and not txt.startswith("["):
                            txt = "[Facilitator] " + txt
                            first = False
                        cues.append((base + off + max(s, a) - a, base + off + min(e, b) - a, txt))
                off += b - a
    cues.sort()
    with open(out, "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b - 0.02)}\n" + "\n".join(wrap(txt)) + "\n\n")
    print(f"{len(cues)} captions -> {out}")


if __name__ == "__main__":
    main()
