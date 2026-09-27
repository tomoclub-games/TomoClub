#!/usr/bin/env python3
"""Time each on-screen caption to the moment its first word is spoken.

    python3 align_captions.py --source "source/TAICY Round 2.mp4"

Transcribes every clip in edl.json with faster-whisper (word timestamps), matches
the caption words to the recognised words, and writes caption_timing.json:
{clip_id: [start offset of each caption chunk, seconds from the clip's in-point]}.
render.py uses it when present; otherwise captions are spread by length.
"""
import argparse
import difflib
import json
import os
import re
import subprocess

import numpy as np

import graphics as g
from render import FF, HERE


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--model", default="small.en")
    a = ap.parse_args()
    from faster_whisper import WhisperModel

    raw = subprocess.run([FF, "-v", "error", "-i", a.source, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    edl = json.load(open(os.path.join(HERE, "edl.json")))
    timing = {}
    for it in edl["sequence"]:
        if it["type"] != "clip":
            continue
        seg = audio[int(it["in"] * 16000):int(it["out"] * 16000)]
        segs, _ = model.transcribe(seg, language="en", word_timestamps=True, beam_size=5,
                                   condition_on_previous_text=False)
        heard = [(norm(w.word), w.start) for s in segs for w in s.words if norm(w.word)]
        chunks = g.chunk_caption(it["text"])
        cap_words = [norm(w) for c in chunks for w in " ".join(c).split()]
        firsts, k = [], 0
        for c in chunks:
            firsts.append(k)
            k += len(" ".join(c).split())
        sm = difflib.SequenceMatcher(a=cap_words, b=[h[0] for h in heard], autojunk=False)
        cap_to_heard = {}
        for blk in sm.get_matching_blocks():
            for j in range(blk.size):
                cap_to_heard[blk.a + j] = blk.b + j
        starts = []
        for n, fi in enumerate(firsts):
            # first matched word at or after the chunk start (within the chunk)
            end = firsts[n + 1] if n + 1 < len(firsts) else len(cap_words)
            t = next((heard[cap_to_heard[i]][1] for i in range(fi, end) if i in cap_to_heard), None)
            starts.append(t)
        # fill gaps by interpolation, keep order, first chunk always from 0
        dur = it["out"] - it["in"]
        starts[0] = 0.0
        for n in range(1, len(starts)):
            if starts[n] is None or starts[n] <= starts[n - 1] + 0.8:
                nxt = next((s for s in starts[n + 1:] if s is not None), dur)
                starts[n] = starts[n - 1] + (nxt - starts[n - 1]) / 2 if starts[n] is None else starts[n - 1] + 0.8
            starts[n] = round(max(starts[n] - 0.1, 0), 3)  # appear a touch before the word
        timing[it["id"]] = starts
        print(f"{it['id']:16} {starts}")
    with open(os.path.join(HERE, "caption_timing.json"), "w") as f:
        json.dump(timing, f, indent=1)


if __name__ == "__main__":
    main()
