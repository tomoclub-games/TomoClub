# All Things Classroom — 9:16 promo video

`all-things-classroom-promo-9x16.mp4` is a 26-second vertical promo (1080×1920, 60 fps, H.264 + AAC, about 8 Mbps)
for Reels, TikTok and YouTube Shorts. It's written for students. `cover.jpg` is a matching cover frame.

## Storyboard (120 BPM; every cut lands on the beat)

| Time | Scene | On screen |
|------|-------|-----------|
| 0–2s | Hook | "Math app." → "Science app." → "Coding app." → "Language app." (one per beat) |
| 2–3s | Overload | Screen floods with app tiles + red notification badges: **"Too many apps?!"** |
| 3–4s | Question | Tiles implode: **"What if it was all in ONE place?"** |
| 4–8s | Drop / reveal | Circle wipe → logo mark + **ALL THINGS CLASSROOM** → "All your learning tools. / One place." |
| 8–12s | Rapid-fire | TOOLS FOR: MATH · SCIENCE · CODING · LANGUAGES · READING · ART · MUSIC · HISTORY · EXAM PREP · ROBOTICS · & WAY MORE |
| 12–14s | The hub | 16 tools snap into one grid: **"One hub. Endless ways to learn."** |
| 14–18s | Search | "Find what works for YOU." — types *help with fractions* → results → tap |
| 18–20s | Payoff | **DISCOVER. EXPLORE. LEVEL UP.** with the right tools + confetti |
| 20–26s | End card | Logo, "Your learning toolbox.", CTA button **allthingsclassroom.com** |

Everything important stays inside the centre safe zone, clear of the platform UI at the top, bottom and right edge.

## Placeholders to swap

The allthingsclassroom.com website couldn't be reached while this was made. The **logo mark** (a cream tile with
four coloured shapes) and the **colour palette** are placeholders. Swap in the real brand assets here:

- Colours: the `C` object at the top of `main.js`
- Logo mark: `makeMark()` in `main.js` (replace it with an `<img>` of the real logo if you like)
- Copy: every on-screen line is a plain string in `main.js`

## Rebuild

```bash
./build.sh
```

The pipeline works like this. `index.html` and `main.js` hold a GSAP timeline that `render.js` seeks frame by frame
in headless Chromium at 60 fps. The page also exports an audio
cue sheet (`events.json`). `audio.py` uses it to synthesise the original soundtrack and SFX (a D-major pop track plus
whooshes, typing and pops), so music and cuts stay in sync. Then ffmpeg muxes and encodes the result.

For a quick look in a browser, serve the folder and open `index.html?play`.

Everything is original or openly licensed: the fonts are Unbounded and Space Grotesk (SIL OFL), the icons are
Lucide (ISC), the animation uses GSAP, and the music is synthesised from scratch.
