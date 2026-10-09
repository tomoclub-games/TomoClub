# TAICY 2026 wrap-up: Instagram Reel, LinkedIn video, Substack post

The close of TAICY 2026 (the TomoClub AI Innovation Challenge for Youth), across both rounds. It congratulates the
winners and every entrant as a group and sends parents to one free live session.

| Output | Format | Length |
|---|---|---|
| `out/TomoClub_TAICY-Wrap_Reel_9x16.mp4` (+ `_no-music`) | 1080×1920, 25 fps | 61.8 s |
| `out/TomoClub_TAICY-Wrap_Reel_9x16_cover.jpg` | 1080×1920 Reel cover (key content in the centre 3:4 for the profile grid) | |
| `out/TomoClub_TAICY-Wrap_LinkedIn_1x1.mp4` (+ `_no-music`) | 1080×1080, 25 fps | 82.1 s |
| `substack/taicy-2026-wrap-up.md` / `.html` + `substack/images/` | The Learning Shift newsletter post | about 1,100 words |
| `instagram-caption.txt`, `linkedin-post.txt` | Post copy with CTAs | |

`out/`, `build/`, `source/` and `substack/images/` are not committed.

## Sources

| Key | What | Used for |
|---|---|---|
| `eco` | A Round 1 entry's demo video (EcoSense smart dustbin), filmed on a phone | The hook and the "what to let AI control" line |
| `r2` | The TAICY Round 2 recording (`../parent-highlight-taicy-round2/source/`) | Live team play and Coach VK |

Put the demo in `source/sudeep_submission.mp4` (Drive: TAICY submissions shared with tomoclub07).

## Story

**Reel** (show the result first):
1. "A student built a dustbin that *thinks.*" The tablet turns green, blue and orange as the student says what it
   sorted: "it classifies the tomato as a wet waste…", "the paper as dry waste", "the mouse as electronic waste".
2. Card: ROUND 1 · CREATE: Spot a real problem. Build the fix with AI.
3. "The best part? Deciding what AI should *NOT* do." "One of the things that I had to identify while making the
   app was what to let AI control and to not control." (Music drops to a breakdown here.)
4. Card: ROUND 2 · LEAD: Then: win as a team. Live.
5. VK: "We don't give you any rules. You have to talk to each other and figure it out." Kids live: "Yep, level one!"
   VK: "How are you doing it so fast?" Student: "Because we remember where all the circuit pieces are…" Lights off:
   "45 seconds. You've completed it." Student: "here you're actually working together for a certain goal."
   VK: "And I'm so proud of you."
6. Wrap card: TAICY 2026 is a wrap! Congratulations to our winners and to every young innovator who took on the
   challenge. → CTA: Want your child to build like this? One live, coach-led session. Free. Join a free session ·
   Link in bio.

**LinkedIn** (parents and educators): the same arc with the problem statement first ("it is not always obvious which
trash bin to throw it into"), the student's "I use AI in the app only for categorizing the waste", a judging card
(Problem 25% · Solution 25% · Prototype & AI use 30% · Pitch 20%, plus the AI Use Log), then Round 2 and "So this is
what game-based learning looks like." The CTA has two QR codes: the free session form for parents and
tomoclub.org/contact-us for schools (both tagged `utm_campaign=taicy_wrap`).

**Substack**: the full story of both rounds: the challenge design, the smart dustbin and the judgment behind it, the
live round, four takeaways, congratulations, and the CTA.

## Privacy and claims

- **No student names** anywhere: captions say STUDENT, the demo's first 7 s (where the student says their name) are
  never used, and the finished audio was run through speech recognition to confirm no name is heard.
- **No student faces.** The demo's picture only comes from face-free stretches (hands, tablet, bins); `v_in` moves the
  picture there while the student's words play. In Round 2 every student tile is blurred by `sanitize.py`. The face
  check found nothing outside VK's tile (`build/*/privacy_report.json`). Coach VK's name and face are used, as agreed.
- **No participant numbers.** Winners aren't named; winners and entrants are congratulated together.
- Round 2 is described as what happened (live team strategy games, no rulebook), not the website's planned format.
- The judging weights and AI Use Log questions are from tomoclub.org/taicy. The line about choosing a simpler design
  than the AI proposed is from the Round 1 judges' notes.
- Copy avoids gendered pronouns for the student ("a student", "they").
- [ ] **Consent (blocking):** written consent from the family of every student whose work, voice or (blurred) image
      appears, including the demo video. Also VK's.
- [ ] Put the free-session link (https://tally.so/r/gDgLeN) in the Instagram bio.

## Render

```bash
python3 ../taicy-social-promo/promo.py reel.json
python3 ../taicy-social-promo/promo.py linkedin.json
python3 make_cover.py                # Reel cover: hook headline over the wet / dry / e-waste screens
python3 substack/make_images.py      # cover + stills for the post
python3 substack/build_html.py       # paste-ready page from the Markdown draft
```

The edit lists use the same schema as `../taicy-social-promo` (see its README). Extra views used here: `crop` (a fixed
source rectangle, for the portrait demo in the square Reel window) and `fitv` (a portrait crop shown whole over a
blurred fill, for the 16:9 LinkedIn window). Card kinds: `round`, `rubric`, `wrap`, plus `cta` with text overrides.

## Posting the Substack draft

1. Open `substack/taicy-2026-wrap-up.html` in a browser, select all, copy, and paste into a new Substack post.
   Headings, quotes, lists and links carry over.
2. Images don't paste from a local file: delete each image placeholder and upload the file from `substack/images/`
   in its place (01 → after the opening quote, 02 → after the Round 2 paragraph, 03 → after the demo list, 04 → after
   the 45 seconds paragraph). Use `00-cover.jpg` as the post's cover / social image.
3. Optional: upload the LinkedIn video into the post, right after the opening section.
4. Title: *TAICY 2026: what to let AI control, and what not to*. Subtitle: *Our AI Innovation Challenge for Youth is a
   wrap. A smart dustbin, a live team round with no rulebook, and what both taught us about kids and AI.*
