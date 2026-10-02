# All Things Classroom: "What Note Comes Next?"

The AI literacy video rebuilt for All Things Classroom (ATC). It's for **parents** (ATC's primary ICP),
uses the **ATC brand system**, follows **Varchas's voice**, and ends on the **AI Labs call to action**,
which points to ATC's contact form.

| File | What it is |
| --- | --- |
| `atc-what-note-comes-next.mp4` | YouTube cut. 1920×1080, 4:41, −14 LUFS |
| `thumbnail.jpg` | 1280×720 YouTube thumbnail |
| `captions.en.srt` | English captions for YouTube |
| `youtube-upload.md` | Title, description (in Varchas's voice), chapters, pinned comment, settings |
| `instagram/atc-what-note-comes-next-reel.mp4` | Instagram Reel. 1080×1920, 1:26, captions burned in |
| `instagram/reel-cover.jpg` | Reel cover |
| `instagram/instagram-post.md` | Caption, pinned comment, posting settings |
| `script.md` | Narration for both cuts, with timestamps |
| `build/` | Source: `engine.py` (rendering), `atc_theme.py` (brand), `long.py` and `reel.py` (the two cuts) |

## How it maps to the ICP

- **Who it talks to:** parents of K–12 children, in India and abroad. The tips are things a parent does
  *with* their child. For under-13s the parent holds the phone and types, which also keeps families
  within the age rules of most AI tools.
- **The pain points it answers:**
  - Future anxiety: "what does my child actually need to know about AI?", with the Class 3 AI curriculum
    as the topical hook.
  - Screen-time guilt: Song Maker and AI as tools the child uses actively.
  - Edtech fatigue: "the same teacher every week", "monthly, no lock-ins".
- **The CTA follows the real form** (tally.so/r/GxGdEQ). The YouTube cut shows a simplified copy of the
  form: Parent contact details, Child's grade (AY 26-27), Program interested in with **AI Labs (AI Literacy)**
  ticked, then "Send my Request" and "We'll email you", which is what the form's thank-you page promises.
  The voiceover says: "Tap the link in the description, tell us about your child, tick AI Labs, and our
  team will email you." The Reel says "Link in bio".
- **Proof:** a real class clip, STEM.org Accredited and Google for Education Certified Educator on the
  CTA screen, and "Don't just use AI. Understand it." (ATC's AI Labs line) as the CTA headline.
- **Engagement:** the Flip Challenge ("cats or dogs, pizza or dosa"). Parents comment "flipped" or "held"
  and what their child said, without names or schools.

## How it applies the brand system

- **Colours:** the ATC tokens only. Forest leads, Teal for display accents and icons, Yellow kept to small
  sparks (highlight words on dark, callouts, the "most likely next note"), and Leaf for bullet dots.
- **Backgrounds:** scenes alternate light and dark the way ATC pages do: Ivory, Pale Digital Blue,
  Forest Night, and Forest for the final CTA.
- **Type:** Manrope 800 for headings, DM Sans for body and labels. Labels are uppercase and tracked, in
  Teal-deep on light and Teal on dark. Each section intro has a short rule above it, Teal on light and
  Yellow on dark.
- **Components:** buttons are Forest with White text, or Yellow with Forest text on dark. Corners are
  rounded rectangles: no pill shapes, gradients, glows or drop shadows.
- **Motion:** entrances are short (about 0.35 s) and move upward or left to right. Nothing bounces.
- **Music:** an original synthesized bed in G, so it's different from the TomoClub cut. No licensed audio.
- **Logo:** I used only the typographic lockup (All Things / CLASSROOM / LEARN. CREATE. EXPLORE.). The PNG
  on allthingsclassroom.com is the old badge (lightbulb, book, atom, stars), which §2.6 of the guidelines
  rules out. The new A+T+C monogram has no vector master yet, and §12 says not to redraw it. When the
  vector is ready, add it to `lockup()` in `build/atc_theme.py` and re-render.
- The Beacon House guidelines weren't used. They're a different brand.

## Voice

The narration follows `Varchas_Voice.md`:
- Short lines, with a named tool (Chrome Music Lab) in the first lines.
- "Take a moment. Commit to an answer."
- One "Well," and one "isn't it?".
- One fragment run: "A phone. A curious kid. 10 minutes."
- British spelling ("rumour") and spaced hyphens instead of em dashes.
- Nothing from his never-use list.
- It ends on something concrete (the comments and the form), not a slogan.

The narrator says "we" (ATC), not "I". It's a synthetic voice, so it shouldn't speak as Varchas.
Varchas is only heard in the real class clips.

## Before publishing, please check

- [ ] **The facilitator "VK" is Varchas.** The clips are labelled "Varchas with TomoClub students" and the
      voiceover says "a real class Varchas ran with TomoClub". If that's wrong, change those two strings in
      `build/long.py` and `build/reel.py`, then re-render.
- [ ] TomoClub and the students' parents are fine with these clips being used for ATC marketing (faces and
      names are blurred).
- [ ] "The same teacher every week" and "monthly, no lock-ins" are accurate for AI Labs as sold today.
- [ ] The Instagram bio link goes to the contact form.

## Rebuilding

Requirements: Python 3 with `pillow numpy kokoro-onnx soundfile`, `ffmpeg`, the Manrope (500–800) and
DM Sans (400–700) font files in `$FONT_DIR`, the Kokoro v1.0 model, and the session recording.

```bash
cd build
export FONT_DIR=/path/to/fonts      # Manrope-800.ttf, DMSans-500.ttf, ...
SRC="/path/to/TomoClub - Chrome Music Lab.mp4"; L=/path/to/work_long; R=/path/to/work_reel
python long.py tts kokoro-v1.0.onnx voices-v1.0.bin $L
python long.py audio "$SRC" $L && python long.py scenes "$SRC" $L && python long.py final "$SRC" $L out.mp4
python long.py captions $L captions.en.srt && python long.py thumbnail thumbnail.jpg
python reel.py tts kokoro-v1.0.onnx voices-v1.0.bin $R
python reel.py audio "$SRC" $R && python reel.py scenes "$SRC" $R && python reel.py final "$SRC" $R reel.mp4
python reel.py cover reel-cover.jpg
```
