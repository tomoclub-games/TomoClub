# SEL hook video pipeline

These scripts produced the videos and thumbnails in the parent folder. Keep them for re-cuts or future session videos.

1. `transcribe.py v1|v2`: faster-whisper transcript with word timestamps (`audio/<v>.json`). Used to pick quotes and time captions.
2. `proc.py clips.json <clip>`: privacy pass on one source segment, written to `proc/<clip>.mp4`.
   - Detects faces with YuNet and matches them against the coach with SFace (`models/vk_refs.npy`). Every face that is not the coach gets an oval blur, held for ±10 frames.
   - OCR (RapidOCR) every 3rd frame. Any text that matches a student name is blurred (scoreboards, in-game tags, lobby lists).
   - Static blur boxes from `clips.json` cover the Zoom name labels and the student thumbnail strip during screen share.
3. `render.py v|h`: builds the 9:16 or 16:9 edit: layouts, word-by-word captions, headlines, end card, ducked music, and loudness normalised to -14 LUFS.
4. `thumbs.py`: Reel cover and LinkedIn thumbnail.

Models (not committed): `face_detection_yunet_2023mar.onnx` and `face_recognition_sface_2021dec.onnx` from opencv_zoo.
Fonts: Outfit (Google Fonts). Music: "Upbeat Forever", Kevin MacLeod (incompetech.com), CC BY 4.0.
Python deps: `opencv-python-headless numpy pillow rapidocr_onnxruntime faster-whisper`, plus ffmpeg.
Source videos are not committed. They live in Google Drive.
