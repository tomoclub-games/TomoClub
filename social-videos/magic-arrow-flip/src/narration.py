"""Generate the voice-over with Kokoro (offline neural TTS) and word timings.

Outputs (in OUT dir):
  vo_<id>.wav      24 kHz mono clip per line (silence trimmed)
  timings.json     {id: {"dur": seconds, "words": [[word, start, end], ...]}}

Word timings come from forced alignment with pocketsphinx; if alignment
fails for a line we fall back to spreading words by character length.
"""
import json, os, re, subprocess, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from script_lines import LINES

MODEL = os.environ.get("KOKORO_MODEL", "kokoro-quantized.onnx")
VOICES = os.environ.get("KOKORO_VOICES", "voices.bin")
VOICE = os.environ.get("KOKORO_VOICE", "af_heart")
SPEED = float(os.environ.get("KOKORO_SPEED", "1.05"))
# Words missing from the default pocketsphinx dictionary.
EXTRA_WORDS = {"refraction": "R IH F R AE K SH AH N"}
OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
os.makedirs(OUT, exist_ok=True)


def trim(samples, sr, thresh=0.01, pad=0.04):
    idx = np.where(np.abs(samples) > thresh)[0]
    if len(idx) == 0:
        return samples
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(samples), idx[-1] + int(pad * sr))
    return samples[a:b]


def align(wav_path, text):
    from pocketsphinx import Decoder
    raw = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", wav_path, "-ar", "16000", "-ac", "1", "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    words = re.findall(r"[a-z']+", text.lower())
    d = Decoder(samprate=16000, bestpath=False, loglevel="FATAL")
    for w, phones in EXTRA_WORDS.items():
        if d.lookup_word(w) is None:
            d.add_word(w, phones, True)
    d.set_align_text(" ".join(words))
    d.start_utt()
    d.process_raw(raw, full_utt=True)
    d.end_utt()
    segs = [(s.word, s.start_frame / 100.0, (s.end_frame + 1) / 100.0) for s in d.seg()
            if s.word not in ("<s>", "</s>", "<sil>", "[NOISE]") and not s.word.startswith("+")]
    return segs


def fallback(text, dur):
    words = text.split()
    weights = [len(w) + (3 if re.search(r"[.!?,:]$", w) else 0) for w in words]
    tot = sum(weights)
    t, out = 0.0, []
    for w, wt in zip(words, weights):
        d = dur * wt / tot
        out.append([w, t, t + d])
        t += d
    return out


def main():
    k = Kokoro(MODEL, VOICES)
    timings = {}
    for lid, text in LINES:
        s, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us")
        s = trim(np.asarray(s, dtype=np.float32), sr)
        path = os.path.join(OUT, f"vo_{lid}.wav")
        sf.write(path, s, sr)
        dur = len(s) / sr
        display = text.split()
        try:
            segs = align(path, text)
            # Map aligned (lower-case) words back onto the display words 1:1.
            clean = [re.sub(r"[^a-z']", "", w.lower()) for w in display]
            aligned = [w.lower().split("(")[0] for w, _, _ in segs]
            if aligned != [c for c in clean if c]:
                raise ValueError(f"alignment mismatch {aligned} vs {clean}")
            words, j = [], 0
            for w, c in zip(display, clean):
                _, a, b = segs[j]
                words.append([w, round(a, 3), round(b, 3)])
                j += 1
            how = "aligned"
        except Exception as e:  # noqa: BLE001
            words = [[w, round(a, 3), round(b, 3)] for w, a, b in fallback(text, dur)]
            how = f"fallback ({e})"
        timings[lid] = {"text": text, "dur": round(dur, 3), "words": words}
        print(f"{lid:10s} {dur:5.2f}s  {how}")
    with open(os.path.join(OUT, "timings.json"), "w") as f:
        json.dump(timings, f, indent=1)
    print("total speech", round(sum(v["dur"] for v in timings.values()), 2), "s")


if __name__ == "__main__":
    main()
