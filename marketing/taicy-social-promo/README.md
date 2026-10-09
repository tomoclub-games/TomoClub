# TAICY 2026 hype videos: Instagram Reel + LinkedIn

Two promos for TAICY 2026 (TomoClub's AI Innovation Challenge for Youth), timed for the winners and prizes
announcement. Both end on a lead-generating CTA. They're cut from three session recordings:

| Key | Recording | Used for |
|---|---|---|
| `oct04` | A student shows the game he built with AI, then a live River Taxi session | AI build, "no rules", "challenging on purpose", 10/10 |
| `sep20` | Hex battle, maze rounds, the After-Action Review slides, wrap-up | Collaboration, 3 min → about 1 min, debrief, kids' verdicts |
| `r2` | TAICY Round 2 (same file as `../parent-highlight-taicy-round2`) | Kids live on their mics |

| Output (in `out/`, not committed) | Format | Length |
|---|---|---|
| `TomoClub_TAICY_Reel_9x16.mp4` (+ `_no-music`, `_cover.jpg`) | 1080×1920, 25 fps | 66.6 s |
| `TomoClub_TAICY_LinkedIn_1x1.mp4` (+ `_no-music`) | 1080×1080, 25 fps | 87.7 s |

Post copy: `instagram-caption.txt` and `linkedin-post.txt`.

## Story

**Instagram Reel** (marketing, for parents scrolling): hook → proof → hype → prizes → book.

1. "A student built a game *with AI*." The student's own words over the game: "I've made a game that I was making on
   Claude" / "for my English test" / "I've also put some questions to answer." Coach: "But it looks pretty solid."
2. TAICY title card: Real problems. Real solutions. · Round 1: build with AI · Round 2: win as a team, live.
3. "No rulebook. *Figure it out together.*" Then kids live on their mics ("Yep, level one!"), "it's not confusing,
   it's challenging, because that's how you learn", and the payoff: same level, 3 minutes down to about 1, because
   "we were talking to each other."
4. Grit: "once I had gone down to last place… I recovered back to second place." Shown over live hex-battle
   gameplay from the same session (the game's end screen reads DEFEAT, so it isn't used).
5. Kids' verdict: "a good 10 out of 10" / "10 out of 10 out of 10."
6. Prizes card (winners announced soon) → CTA: *Want your child in the next one? One live, coach-led session.
   Free. Join a free session · Link in bio · Follow @tomoclub_edu for the winners.*

**LinkedIn** (parents and educators): the method, with proof.

1. "We give kids *no rulebook.* On purpose." Coach VK explains why over a live hex battle.
2. TAICY explainer card: Round 1 · Create and Round 2 · Lead.
3. "Kids don't just use AI. They *build* with it." The same AI-built game.
4. "Collaboration isn't lectured. It's *practised.*" "What made you win this time?" → "Because we were working
   together." Then the 3 min → about 1 min payoff.
5. "Every game ends with an *After-Action Review.*" Over the debrief slides: "It's okay to make mistakes. What is
   important is, can somebody correct it?"
6. "Skills that *compound,* week after week." Then the kids in their own words.
7. Prizes card → two-route CTA with QR codes: **Parents:** join a free live session (the Tally sign-up form,
   `FREE_SESSION` in `promo.py`). **Educators & schools:** bring TAICY to your school (tomoclub.org/contact-us).
   Both QR codes carry `utm_source=linkedin&utm_medium=video&utm_campaign=taicy_hype`.

## Privacy

`sanitize.py` makes every clip before any graphics go on:

- Each frame is classified as Zoom gallery or screen share (Zoom paints pure black around gallery tiles).
- In gallery view every student's tile is blurred heavily (sigma 46), including the Zoom name label. Coach VK's tile
  stays sharp.
- In screen share the small webcam strip in the top-right corner is blurred.
- The blur windows are widened by 3 frames around every view switch.
- An OpenCV face check then flags any face found outside VK's tile. The results are in
  `build/<edl>/privacy_report.json`.
- The oct04 crops leave out the browser bar (tab title, URL and account name) and the AI tool's chat panel. Only
  the student's game panel is shown.
- Player names inside the games are left as they are, as agreed.
- No caption, label or kept audio contains a student's name. Students are labelled STUDENT, and cuts stop before any
  name is spoken. The cuts were checked against word timestamps and the audio energy.

## Compliance checklist

- [ ] **Consent (blocking):** written parent or guardian consent for every student who is heard or shown, even
      blurred. Also get VK's consent.
- [x] Faces and Zoom names of students blurred; no student names in captions or audio (checked by running speech
      recognition on the finished audio).
- [x] No "DEFEAT" screen is shown. Face-check hits were reviewed by eye: the hex board's dot pattern and a cartoon
      on a debrief slide, both false positives.
- [x] Every caption is what was said. "3 minutes → about 1" is the coach's own statement on camera. No participant
      numbers are published.
- [x] No claim that a particular child entered or won TAICY; the AI-build student is presented as a TomoClub student.
- [x] The offer is one free live session (Tally form). No fake urgency.
- [x] Original music (`../instagram-reel-taicy-round2/music.py`), so there's nothing to license and nothing for
      platforms to mute.
- [ ] Put the free-session link in the Instagram bio before posting.
- [ ] Consider limiting comments on Instagram, since the Reel features minors.

## Render

```bash
pip install pillow numpy scipy "qrcode[pil]" imageio-ffmpeg faster-whisper "opencv-python-headless<5"
# put the recordings in source/ (sep20.mp4, oct04.mp4) and ../parent-highlight-taicy-round2/source/
python3 promo.py insta.json
python3 promo.py linkedin.json
```

- `insta.json` / `linkedin.json` are the edit lists. `a_in`/`a_out` are the words in seconds of the source; `v_in`
  takes the picture from another moment; `view` is `vk`, `game`, `project`, `slide` or `gallery`; `head` is the
  kinetic headline (`*gold*`, `|` = line break); `joined` continues the previous shot's sentence after a cut pause.
- Word timings for the pop captions are cached in `<edl>_words.json`.
- Each render writes a with-music and a `_no-music` master at −14 LUFS / −1 dBTP.
