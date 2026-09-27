#!/usr/bin/env bash
# Rebuild the short end-to-end (narration -> frames -> soundtrack -> MP4).
# Needs: ffmpeg, the Noto Color Emoji font (fonts-noto-color-emoji), libegl1 for
# skia, and `pip install -r requirements.txt`. Run prepare_voice_model.py once first.
set -euo pipefail
cd "$(dirname "$0")"
OUT=build
mkdir -p "$OUT"

python3 narration.py "$OUT/vo"
python3 render.py "$OUT/vo" "$OUT/video_silent.mp4"
python3 audio.py "$OUT/vo" "$OUT/cues.json" "$OUT/mix.wav"

# two-pass loudness normalisation to -14 LUFS (YouTube / Instagram target), then mux
STATS=$(ffmpeg -hide_banner -i "$OUT/mix.wav" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 \
  | sed -n '/^{/,/^}/p')
LN=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print('measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s' % (d['input_i'], d['input_tp'], d['input_lra'], d['input_thresh'], d['target_offset']))" "$STATS")
ffmpeg -loglevel error -y -i "$OUT/video_silent.mp4" -i "$OUT/mix.wav" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:$LN:linear=true,aresample=48000" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
  ../magic-flipping-arrow-short.mp4

python3 render.py "$OUT/vo" --cover ../cover.jpg
python3 render.py "$OUT/vo" --srt ../captions.srt
echo "done: ../magic-flipping-arrow-short.mp4"
