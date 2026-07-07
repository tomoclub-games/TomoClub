---
name: add-podcast
description: Add a new episode of The Learning Shift Podcast to the TomoClub website. Use when the user wants to upload, add, or publish a new podcast episode, or mentions the "semi-automated" podcast process. Needs a YouTube URL, speaker name, and release date from the user.
tools: Bash, Read, Edit, Grep
---

# Add Podcast Episode

Adds one new podcast episode to the site using `add_podcast_episode.py` at the repo root, a hardened helper script that replaced the guide's original multi-script pipeline after it hit real bugs in production (see "Why not the old pipeline" below).

## Steps

1. **Collect inputs** if not already given: YouTube URL, speaker name, release date (format `"Month DD, YYYY"`, e.g. `"July 26, 2026"`). Ask the user for whatever is missing.

2. **Run the script** from the repo root:
   ```bash
   python add_podcast_episode.py --url "https://youtu.be/VIDEO_ID?si=..." --speaker "Full Name" --date "July 26, 2026"
   ```
   This single call:
   - Extracts the video ID from the URL.
   - Fetches the real title + duration for **just that one video** from YouTube (not the whole back-catalog — fetching all ~100 videos at once triggers 429 rate limits).
   - Adds the entry to `podcasts_data.js` (used by `podcast-player.html`).
   - Adds/refreshes the entry in `podcast_data.json` (metadata cache).
   - Appends the URL to `generate_html.py`'s `urls` list and the tuple to `update_js_metadata.py`'s `new_podcasts` list (kept as historical records only — see below).
   - Inserts a new card at the **top** of the `#podcast-grid` in `index.html`, using the same template as the live cards.
   - All steps are duplicate-safe: re-running with the same URL is a no-op that reports "already has an entry, skipping" for each file.

3. **Verify the diff is minimal and sane**:
   ```bash
   git diff --stat
   ```
   Expect small, additive diffs only: `index.html` (~16 lines), `podcasts_data.js` (~8 lines), `podcast_data.json` (~6 lines), `generate_html.py` (~1 line), `update_js_metadata.py` (~1 line). If any file shows hundreds of changed lines, stop — something went wrong (see Troubleshooting).

4. **Preview locally before committing.** Check if a local server is already running on port 8000:
   ```bash
   netstat -ano | grep ":8000.*LISTENING"
   ```
   If nothing is listening, start one from the repo root: `python -m http.server 8000` (run in background). If something IS listening, check how many PIDs — if more than one process is bound to the same port, kill all of them first (`taskkill //PID <pid> //F`) and start a single fresh instance. Two processes silently bound to the same port is what caused stale content to be served during the first episode upload.

   Have the user open (or open via WebFetch/browser) `http://localhost:8000/index.html#podcast` and `http://localhost:8000/podcast-player.html?id=VIDEO_ID` to confirm the new episode shows with the correct title, speaker, date, and duration. Tell them to hard-refresh (Ctrl+Shift+R) since browsers cache aggressively.

5. **Ask before committing/pushing.** Don't `git add`/`git commit`/`git push` without explicit confirmation — publishing is a user decision. If they confirm, stage only the files touched by this workflow (never `git add -A` blindly — check `git status` first for unrelated in-progress work).

## Why not the old pipeline

The original guide (`TomoClub Content Management & GitHub Publishing Guide new.pdf`) documents running `update_all.py`, which calls `fetch_podcasts.py` (re-fetches metadata for **every** video in `generate_html.py`'s URL list) and `generate_html.py` (rebuilds the grid with generic placeholder titles like "Podcast Episode N", losing the real titles/descriptions the site actually uses), then merges the result into `index.html` via a lazy regex (`<div class="grid-3" id="podcast-grid">.*?</div>`) that only matches up to the *first* nested `</div>` — not the true closing tag — which duplicated the entire podcast grid instead of replacing it.

`add_podcast_episode.py` avoids both problems: it fetches metadata for one video only, and it inserts a single new card via a direct string-index splice instead of a regex match, so the diff is always minimal and predictable.

## Troubleshooting

- **Large/unexpected diff after running the script**: revert (`git checkout -- <file>`) and re-run; check the printed output for which step ran vs. skipped.
- **YouTube fetch fails with 429**: wait a few minutes before retrying; the script already retries 3x with backoff, but the whole back-catalog scripts (`fetch_podcasts.py`, `update_all.py`) should not be run to work around it.
- **Local preview shows stale content**: check for duplicate processes on port 8000 (see step 4) and hard-refresh the browser.
- **Duplicate keys in `podcasts_data.js`**: verify with `node -e "new Function(require('fs').readFileSync('podcasts_data.js','utf-8')+'; return podcastsData;')()"` — should not throw and should have no repeated keys.
