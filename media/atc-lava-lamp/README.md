# All Things Classroom — DIY Lava Lamp (hype edit)

A ~62-second, beat-synced science-experiment video cut from the class recording
*Science Group 1 – Lava Lamp – 1 Dec 2025*. It comes in two formats:

| File | Format | Use |
| --- | --- | --- |
| `ATC_Lava_Lamp_16x9.mp4` | 1920×1080, 30 fps | YouTube, website, LinkedIn |
| `ATC_Lava_Lamp_9x16.mp4` | 1080×1920, 30 fps | Reels, Shorts, TikTok, WhatsApp status |
| `cover_16x9.jpg`, `cover_9x16.jpg` | Thumbnails | YouTube thumbnail / Reels cover |

The MP4s are not stored in the repo, so the website stays small. They were delivered
separately. To regenerate them, see "Rebuilding" below.

## Running order

| Time | Section | On screen |
| --- | --- | --- |
| 0:00 | Hook | "Can you make a LAVA LAMP with stuff from your KITCHEN?!" over the glowing lamp |
| 0:04 | Title | ATC logo card, "DIY LAVA LAMP", "Science Experiment" |
| 0:08 | You'll need | Glass, baking soda, vegetable oil, vinegar, food colour, torch (1/6 … 6/6) |
| 0:15 | Steps 1–6 | Baking soda → oil → vinegar → food colour → pour in → place on torch |
| 0:26 | Countdown | The teacher's own "3, 2, 1… lights off!" with synced numbers |
| 0:30 | The drop | The lamp lights up: "WHOA!!", "It's glowing!", "Watch the blobs rise", "It's fizzing!" |
| 0:45 | The science | Oil and vinegar don't mix (labelled layers) · Vinegar + baking soda = CO₂ gas (animated bubbles) · Bubbles carry the colour up, then it sinks back down |
| 0:56 | Outro | "Try it at home! Ask a grown-up & wear gloves" |
| 0:58 | End card | ATC logo, "Learn · Create · Explore", "Follow for more experiments!" |

## Notes

- **Music and sound effects** are original. They were synthesised in code by `pipeline/music.py`
  (128 BPM, A minor), so there's nothing to license and no Content ID claims. The cuts,
  zoom punches and flashes land on the beat.
- **Voice**: the only speech is the teacher's countdown, taken from the recording. The music ducks under it.
- **Privacy**: no student faces, names or voices appear. The edit uses only the teacher's
  experiment camera, from 12:45 to 26:30 of the recording.
- **Brand**: colours come from the logo (green `#185E3A`, teal `#14B0C4`, yellow `#F7BB40`,
  lime `#5EA63C`). Type is Poppins.

## Rebuilding

`pipeline/` contains the full edit: `timeline.py` (the edit decision list: shots, text,
SFX), `render.py` (frames), `music.py` (score and SFX), `mix.py` (voice and ducking) and
`cover.py` (thumbnails). Put the source recording (`source.mp4`), the logo (`logo_src.png`)
and the Poppins fonts (`fonts/`) next to the scripts, then run `pipeline/build.sh`.
To change a caption or timing, edit `timeline.py` and rebuild.
