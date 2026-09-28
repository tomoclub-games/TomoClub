# Instagram Reel: "This is what screen time SHOULD look like" (TAICY 2026, Round 2)

A roughly 70-second vertical Reel (1080×1920, 9:16, 25 fps) cut from the same 65-minute Zoom recording as the
16:9 parent highlight (`../parent-highlight-taicy-round2`). It's built to stop parents mid-scroll, show their child
the game-based session they're missing, and send them to book a free trial.

| File (in `out/`) | What it is |
|---|---|
| `TomoClub_TAICY-R2_Reel_9x16.mp4` | The Reel, with the original music bed |
| `TomoClub_TAICY-R2_Reel_9x16_no-music.mp4` | Voices only, if you'd rather add a sound in the Instagram app |
| `TomoClub_TAICY-R2_Reel_9x16_cover.jpg` | Cover frame (hook headline over the three faces) |
| `../instagram-caption.txt` | Post caption with CTA and hashtags |

## Story (every line is real audio from the session)

| Beat | Heard | On-screen headline |
|---|---|---|
| Hook, 0 s | Coach VK: "This isn't like your PUBG or other games, right? This is more strategy and thinking game." Picture: a live 3-way battle | This is what screen time **SHOULD** look like |
| Setup | "We don't give you any rules." / "You have to talk to each other and figure it out." | No rules. **No answers.** |
| Teamwork montage | Kids live on their mics: "someone needs to be at this button over here" / "Yep, level one!" / "I'll just be at the button, unlocking the doors you explore" / "I got the last chip. Now we need to go to the platform." | They crack the rules… **together.** → Level 1: **cleared.** → They split the roles. **They plan.** |
| Thinking | "How are you doing it so fast?" → "Because we remember where all the circuit pieces are, and exactly what we should do at which time." | The coach asks. **The kids think.** |
| Payoff | "Oh, I can't see any light." → "But it's the same map. Can you remember?" → "45 seconds. You've completed it. Pretty cool." | Now the lights go **OFF** for the kids. → Same level. Cleared in **45 seconds.** |
| Resilience | Sudeep: "And I didn't understand what was happening." → "No problem. That's the part of learning, right?" → "You can always bounce back… Sudeep, I saw you doing it. So, good job." | Stuck? That's where **learning starts.** → Bounce back. **Every time.** |
| Kids' words | Vedant: "Usually in other games you're competing against someone, but here you're actually working together for a certain goal." / "Communication is key." | In their **own words.** |
| Emotion | "So this is what game-based learning looks like." / "And I'm so proud of you." | Game-based learning, **the TomoClub way.** |
| CTA, 8 s | Music up | Want this for **your child?** · Their first class is **FREE** · **Book a free trial** · Link in bio · tomoclub.org/parents · Live · Coach-led · Grades 3–8 |

## Design

- The footage sits in a 1080×1080 square: the game (centre of the screen share), a speaker close-up cropped from
  their Zoom tile, or all three faces stacked. It slowly pushes in on every shot.
- **Pop captions** show the current word in gold, timed from word-level speech recognition (`reel_words.json`).
  A pill names who's speaking (COACH VK, VEDANT, SUDEEP, STUDENT).
- The kinetic headline slides in whenever the story beat changes.
- Text stays inside Instagram's Reels safe zone (clear of the top bar, the right-hand buttons and the bottom caption area).
- **Music** (`music.py`) is an original 120 BPM track synthesised from scratch (no samples), so there is no licence to
  clear and Instagram won't mute it. It drops to a breakdown under the "stuck" section, rises into the CTA, and
  ducks automatically whenever someone speaks. Master: −14 LUFS, −1 dBTP.

## Compliance checklist

- [ ] **Consent (blocking):** get written parental or guardian consent for both students before posting, and don't post
      the caption's "shared with their families' permission" line until you have it. Get VK's consent too.
- [x] First names only. The Zoom name labels are cropped out. No school, city, surname or contact details.
- [x] No student is shown losing: the Game 1 debrief plays over gameplay from the same round, not the "DEFEAT" screen.
- [x] Nothing is invented. Every caption is what was said (clean verbatim). "45 seconds" is the coach's statement on
      camera. The lights-off round shows the coach's view of the map, so the text says the lights were off *for the kids*.
- [x] No fake urgency or scarcity. The offer matches tomoclub.org/parents ("Trial is free · No commitment", Grades 3–8).
- [x] Original music. Social platforms are named in text only.
- [ ] The hook quotes the coach naming another game ("PUBG"). That's fine as an organic post. If you boost it as a
      paid ad, consider starting at "This is more strategy and thinking game" to keep a third-party brand out of the ad.
- [ ] Make sure the link in your Instagram bio points to tomoclub.org/parents before posting.
- [ ] In the Instagram app: choose the supplied cover, and consider limiting comments, since the Reel features minors.

## Render

```bash
pip install pillow numpy scipy "qrcode[pil]" imageio-ffmpeg faster-whisper
python3 reel.py --source "../parent-highlight-taicy-round2/source/TAICY Round 2.mp4"
```

Edit shots, headlines and captions in `reel.json`. `--only id1,id2` re-renders single shots for a quick look.
