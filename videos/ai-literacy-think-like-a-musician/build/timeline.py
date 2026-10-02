"""Turns the scene plan + narration durations into an absolute, frame-aligned timeline."""
import json
import math
import os

from script_data import CLIPS, SCENES

FPS = 30


def build(work, scenes=None, clips=None):
    scenes = SCENES if scenes is None else scenes
    clips = CLIPS if clips is None else clips
    with open(os.path.join(work, "vo", "durations.json")) as f:
        durations = json.load(f)
    t = 0.0
    out = []
    for sc in scenes:
        cues = {}
        items = []
        local = sc["lead"]
        for it in sc["items"]:
            if it[0] == "vo":
                _, vid, text, gap = it
                d = durations[vid]
                cues[vid] = (local, d, text)
                items.append(dict(kind="vo", id=vid, start=local, dur=d, text=text))
                local += d + gap
            elif it[0] == "pause":
                local += it[1]
            elif it[0] == "clip":
                segs = clips[it[1]]
                d = sum(b - a for a, b in segs)
                items.append(dict(kind="clip", id=it[1], start=local, dur=d, segs=segs))
                local += d
        local += sc["tail"]
        n = math.ceil(local * FPS - 1e-6)
        out.append(dict(id=sc["id"], start=t, dur=n / FPS, frames=n, cues=cues, items=items))
        t += n / FPS
    return out


class Cues:
    """Look up when (scene-local seconds) a narration line, or a phrase inside it, is spoken."""

    def __init__(self, scene):
        self.c = scene["cues"]
        self.dur = scene["dur"]

    def __call__(self, vid, sub=None, frac=None):
        start, d, text = self.c[vid]
        if sub is not None:
            i = text.find(sub)
            if i < 0:
                raise KeyError(f"{sub!r} not in {vid}")
            return start + d * i / len(text)
        if frac is not None:
            return start + d * frac
        return start

    def end(self, vid):
        start, d, _ = self.c[vid]
        return start + d


if __name__ == "__main__":
    import sys
    tl = build(sys.argv[1])
    for s in tl:
        print(f"{s['id']:12s} start {s['start']:7.2f}  dur {s['dur']:6.2f}")
    print("total", tl[-1]["start"] + tl[-1]["dur"])
