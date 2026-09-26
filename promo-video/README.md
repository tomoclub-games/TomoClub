# TomoClub promo video

A 46-second, 1080p motion-graphics promo: **AI Literacy + SEL through game-based learning**.
The whole video is framed as a game — it opens on *PRESS START*, an XP bar fills level by level,
and it ends on *LEVEL UP!* before the end card.

| Time | Beat |
| --- | --- |
| 0–4s | Hook — "PRESS START" → "AI is in their phones / homework / games / future." |
| 4–8s | The shift — "Using AI is easy. Using it wisely? That's a skill." → "AI-smart & human-strong." |
| 8–12s | Logo reveal — TomoClub · AI Literacy + SEL |
| 12–16s | Game wall (real TomoClub game art) — "Learning that feels like playing." |
| 16–22s | Skill tree 01: AI Literacy — a "Spot the myth" mini-game |
| 22–28s | Skill tree 02: Social-Emotional Learning — co-op mode, team sync |
| 28–30s | Play → Reflect → Apply |
| 30–36s | High scores — 93% / 80% / 94%, 10,000+ students, STEM.org badges |
| 36–40s | Educator testimonial |
| 40–46s | LEVEL UP! → "Play today. Lead tomorrow." → end card + tomoclub.org |

All stats and the testimonial are taken from the current homepage (`index.html`).

## Files

- `tomoclub-promo.mp4` — the finished video (H.264 + AAC, 1920×1080, 30 fps, ~18 MB, -14 LUFS audio).
- `poster.jpg` — end-card frame for thumbnails / video posters.
- `index.html` — the animation source. Open it through a local server to preview with sound
  (space = play/pause, ←/→ = seek, `?t=12` starts at 12s).
- `render.mjs` — renders the page frame by frame with Playwright and encodes with ffmpeg.
- `music.py` — synthesizes the soundtrack (120 BPM; every SFX is placed from `cues.json`).
- `cues.json` — sound cues exported from the animation timeline.
- `fonts/` — Outfit, Silkscreen and JetBrains Mono (SIL Open Font License).

## Re-rendering after an edit

```bash
# from the repo root
npx http-server -p 8080 .            # preview at http://localhost:8080/promo-video/
node promo-video/render.mjs --stills 12.5,19.3   # check frames -> promo-video/.stills/

node promo-video/render.mjs --cues   # only needed if you moved/added timed events
python3 promo-video/music.py         # -> soundtrack.wav (needs numpy + scipy)
# bring to about -14 LUFS (measure with ebur128; the current mix needs about -0.8 dB)
ffmpeg -i promo-video/soundtrack.wav -af "volume=-0.8dB,alimiter=limit=0.87:level=disabled" -c:a aac -b:a 192k promo-video/soundtrack.m4a
node promo-video/render.mjs --jobs 4 # -> promo-video/tomoclub-promo.mp4
```

Copy lives in `index.html`; each scene is a `<section class="scene">` block with its timing in the
matching `S1…S10` section of the script. Times are absolute seconds on a 120 BPM grid
(one beat = 0.5s), so keep big hits on half-second marks to stay on the music.
