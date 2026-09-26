#!/usr/bin/env bash
# Rebuilds the All Things Classroom 9:16 promo from source.
# Needs: node 18+, python 3.10+, Chromium via Playwright (npm i -g playwright).
set -euo pipefail
cd "$(dirname "$0")"

npm install --silent
pip install --quiet imageio-ffmpeg numpy scipy pyloudnorm
export FFMPEG="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"

mkdir -p fonts
cp node_modules/@fontsource/unbounded/files/unbounded-latin-{700,800,900}-normal.woff2 fonts/
cp node_modules/@fontsource/space-grotesk/files/space-grotesk-latin-{500,600,700}-normal.woff2 fonts/
node build_icons.js

node render.js video 60          # -> video_noaudio.mp4 (60 fps) + events.json (audio cue sheet)
python3 audio.py events.json     # -> soundtrack.wav

# Mux the soundtrack and encode for social (60 fps, ~10 Mbps, web-optimised).
"$FFMPEG" -y -loglevel error -i video_noaudio.mp4 -i soundtrack.wav \
  -c:v libx264 -profile:v high -level 4.2 -preset slow -crf 20 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -g 120 \
  -c:a aac -b:a 192k -ar 44100 -movflags +faststart -shortest \
  all-things-classroom-promo-9x16.mp4

node render.js stills 6.3 && python3 -c "from PIL import Image; Image.open('stills/t_6.30.png').convert('RGB').save('cover.jpg', quality=90)"
echo "done: all-things-classroom-promo-9x16.mp4"
