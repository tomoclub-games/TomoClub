# Think Like a Musician: 5 AI Literacy Moves for Students

A 4:48 YouTube video (16:9, 1920×1080, 30 fps) teaching students five practical AI literacy moves,
using clips from a real TomoClub Chrome Music Lab (Song Maker) session. It ends with one challenge
that students try themselves and report in the comments.

| File | What it is |
| --- | --- |
| `ai-literacy-think-like-a-musician.mp4` | Final video. H.264 High, AAC 48 kHz stereo, −14 LUFS, faststart |
| `thumbnail.jpg` | 1280×720 YouTube thumbnail |
| `captions.en.srt` | English closed captions, timed to the video (upload them in YouTube Studio) |
| `youtube-upload.md` | Title, description, chapters, tags, pinned comment and upload settings |
| `script.md` | Full narration script and the on-screen text |
| `build/` | Source used to generate everything above (see below) |

## The five moves

1. **Guess the Next Note.** AI predicts the most likely next piece, so surprise is your job.
2. **Play It Twice.** Ask the same question in a brand-new chat. If the facts change, treat them as a rumor.
3. **Flip the Key.** A leading question gets a leading answer, so ask neutral questions.
4. **Find the Sheet Music.** No receipt? Don't repeat it.
5. **Play It By Ear.** Close the tab and explain it out loud in 30 seconds.

**Comment challenge:** *The Flip Challenge.* Ask "Why is X better?" and then, in a new chat, "Why is Y
better?". Comment **FLIPPED** or **HELD** plus the pair you tested.

## Privacy and compliance steps built into the video

- The session clips are cut so that no student name is spoken or shown. Student video tiles get a
  second, heavy blur on top of the blur already in the recording.
- The video is aimed at students aged 13 and up, and it tells them to use only approved AI tools
  and to follow each tool's age rules.
- The comment prompt asks for no names, schools or personal details.
- The narration voice is AI-generated. This is said on screen at the start and in the voiceover
  at the end.
- All music and sound effects were synthesized for this video, so there is no third-party audio.
  The typeface is Outfit (SIL Open Font License), the same one the TomoClub website uses.

## Rebuilding

Requirements: Python 3 with `pillow numpy kokoro-onnx soundfile`, `ffmpeg`, the Outfit font files
(weights 400–800), the Kokoro v1.0 model files, and the original session recording
(`TomoClub - Chrome Music Lab.mp4`). The recording is not committed to the repo.

```bash
cd build
export FONT_DIR=/path/to/outfit-fonts        # Outfit-400.ttf ... Outfit-800.ttf
W=/path/to/workdir; SRC="/path/to/TomoClub - Chrome Music Lab.mp4"
python tts.py kokoro-v1.0.onnx voices-v1.0.bin $W   # narration (voice af_heart)
python audio.py "$SRC" $W                           # soundtrack, normalized to -14 LUFS
python render.py scenes "$SRC" $W                   # animated scenes
python render.py final "$SRC" $W out.mp4            # final encode
python captions.py $W captions.en.srt
python thumbnail.py thumbnail.jpg
```

To change the wording, edit `build/script_data.py` and re-run all the steps. The scene timings
follow the new narration automatically.
