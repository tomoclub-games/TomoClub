#!/usr/bin/env bash
# Rebuilds both cuts of the ATC DIY Lava Lamp video from the class recording.
# Run from a working folder containing: source.mp4 (the Drive recording), logo_src.png (ATC logo),
# fonts/Poppins-{Black,BlackItalic,ExtraBold,Bold,SemiBold}.ttf, and these scripts.
# Needs: python3 with pillow numpy scipy imageio-ffmpeg; Noto Color Emoji font installed.
set -euo pipefail
ln -sf "$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" ./ffmpeg
python3 -c "import json, timeline; json.dump(timeline.SFX, open('sfx_events.json', 'w'))"
python3 music.py
./ffmpeg -v error -y -ss 1174.35 -to 1177.98 -i source.mp4 -vn -ac 1 -ar 44100 voice_raw.wav
python3 mix.py
python3 render.py h & python3 render.py v & wait
./ffmpeg -v error -y -i video_h.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af volume=-2.1dB \
  -c:a aac -b:a 192k -shortest -movflags +faststart ATC_Lava_Lamp_16x9.mp4
./ffmpeg -v error -y -i video_v.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af volume=-2.1dB \
  -c:a aac -b:a 192k -shortest -movflags +faststart ATC_Lava_Lamp_9x16.mp4
python3 cover.py h
python3 cover.py v
