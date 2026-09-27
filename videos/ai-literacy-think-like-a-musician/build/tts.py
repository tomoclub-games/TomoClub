"""Generate narration lines with Kokoro (local, open-weight TTS).

usage: python tts.py <kokoro-v1.0.onnx> <voices-v1.0.bin> <workdir>
Writes <workdir>/vo/<id>.wav (24 kHz mono) and <workdir>/vo/durations.json.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

from script_data import SCENES

VOICE = "af_heart"
SPEED = 1.04


def trim(samples, sr, thresh=0.01, pad=0.04):
    idx = np.where(np.abs(samples) > thresh)[0]
    if len(idx) == 0:
        return samples
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(samples), idx[-1] + int(pad * sr))
    return samples[a:b]


def main():
    model, voices, work = sys.argv[1:4]
    out = os.path.join(work, "vo")
    os.makedirs(out, exist_ok=True)
    k = Kokoro(model, voices)
    durations = {}
    for scene in SCENES:
        for item in scene["items"]:
            if item[0] != "vo":
                continue
            _, vid, text, _ = item
            samples, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us")
            samples = trim(samples, sr)
            sf.write(os.path.join(out, f"{vid}.wav"), samples, sr)
            durations[vid] = len(samples) / sr
            print(f"{vid}: {durations[vid]:.2f}s")
    with open(os.path.join(out, "durations.json"), "w") as f:
        json.dump(durations, f, indent=1)
    print("total narration", sum(durations.values()))


if __name__ == "__main__":
    main()
