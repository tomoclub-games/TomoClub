---
name: add-article
description: Add a new Education Hall article to the TomoClub website. Use when the user wants to upload, add, or publish a new article, story, or "innovation hall" / "education hall" piece, or mentions the "semi-automated" article process. Needs a title, category, release date, cover image, and the article body content from the user.
tools: Bash, Read, Edit, Grep
---

# Add Education Hall Article

Adds one new Education Hall article using `add_article.py` at the repo root, a hardened helper script built after the original guide's pipeline (`generate_article_pages.py`) was found to only track 8 of the ~19 articles actually live on the site — most had been added by hand directly into `articles/<slug>/` without ever being registered in `articles_data.js` or `article_metadata`.

## Steps

1. **Collect inputs** from the user if not already given:
   - Title
   - Category (e.g. "Leadership", "Innovation", "Equity")
   - Release date, format `"Month D, YYYY"` (e.g. `"July 6, 2026"`)
   - Cover image — a URL or a local file path
   - The article's source content. **Prefer asking "do you have a source document (PDF, doc, text) for this article?" over handing the user a blank template to fill in.** If they have a PDF/doc, read it yourself and write the `<div class="article-content">` HTML directly — matching the site's format (`<h3>` section headers, `<p>` paragraphs, `<ul><li>` lists, centered image blocks like `<div style="text-align: center; margin: 2rem 0;"><img src="..." style="max-width: 100%; border-radius: 8px;" /></div>`) — by copying the structure of an existing article that shares the same style (see `articles/lauren-bolack-leadership/index.html` or `articles/chris-parker-technology-leadership/index.html` for the two current conventions). Only fall back to producing a blank fill-in-the-blank template when the user has no source document and wants to write from scratch themselves.
   - Optional: `--slug` (auto-derived from title if omitted), `--alt` (image alt text, defaults to title), `--gradient` (teal/gold/crimson/slate homepage card background; auto-rotates if omitted).

2. **Write the content to a file** (e.g. `new_article_content.html` in the repo root, or the scratchpad directory), then run:
   ```bash
   python add_article.py --title "How X Did Y" --date "July 6, 2026" --category "Leadership" \
     --cover "https://example.com/cover.jpg" --content-file /path/to/content.html
   ```
   This single call:
   - Downloads the cover image (URL or copies a local file) into `articles/images/<slug>-cover.<ext>`.
   - Localizes any external `<img>` URLs found in the content into `articles/images/<slug>-img-N.ext`.
   - Renders `articles/<slug>/index.html` using the site's real article template.
   - Adds a `article_N` entry to `articlesData` in `articles_data.js` (auto-numbered, JSON-escaped so embedded quotes/newlines don't break the JS).
   - Adds the matching metadata block to `article_metadata` in `generate_article_pages.py` (kept as a historical record only — this script does **not** invoke `generate_article_pages.py`'s full-batch regeneration, which would touch every previously-generated article folder at once).
   - Appends a new card at the **end** of `#articles-grid` in `index.html`.
   - Includes the Substack newsletter embed section (before the footer) and the X.com footer link (`https://x.com/TomoClub_edu`) — every article page on the site has both as of July 2026, and `HTML_TEMPLATE` renders them by default.

3. **Why "end of grid", not "top"**: unlike the podcast grid, `script.js` sorts Education Hall cards by DOM position (`data-timestamp` = index in the DOM at load time), and "Newest First" is the default selected sort option. So the newest article must be the *last* child in the DOM to display first on page load. `add_article.py` already does this correctly — don't move the insertion point to the top by analogy with the podcast skill.

4. **Verify the diff is minimal**: `git diff --stat` should show small additive changes only (`index.html` ~12 lines, `articles_data.js` ~1 line, `generate_article_pages.py` ~7 lines) plus new files under `articles/<slug>/` and `articles/images/`. If a slug collides with an existing directory, the script aborts before writing anything — pick a different `--slug`.

5. **Preview locally before committing** — same local-server routine as the podcast skill: check `netstat -ano | grep ":8000.*LISTENING"` for stray/duplicate processes first (kill any and start one fresh instance if needed), then have the user open `http://localhost:8000/index.html#education-hall` (hard-refresh) and `http://localhost:8000/articles/<slug>/` to confirm the card and full article render correctly.

6. **Ask before committing/pushing.** Don't `git add`/`git commit`/`git push` without explicit confirmation. Stage only the files this workflow touched — check `git status` first for unrelated in-progress work, never `git add -A` blindly.

## Troubleshooting

- **Cover/content image download fails**: the script shells out to `curl.exe` with a browser User-Agent (some hosts reject bare `urllib` requests). If a URL still fails, ask the user for a local file path instead — the script accepts either.
- **"already exists" abort**: the target `articles/<slug>/` directory is already present. Either the article was already added, or the slug collides with something else — check `articles/` and pick a different slug if needed. If you need to regenerate (e.g. after fixing the template), `rm -rf articles/<slug>` first — the registry entries in `articles_data.js`/`generate_article_pages.py` are already dedup-safe, but re-running after deleting the directory will still try to add them; if they're already present it'll correctly skip. **Never re-run against a slug whose registry entries were already committed without first checking** — `next_article_key()` picks the next unclaimed `article_N` number regardless of slug, so re-running for an already-registered slug creates a duplicate `article_N` entry with the same content under a new key. If that happens, `git diff` the two blocks, confirm they're identical, and revert the newer one.
- **Validate `articles_data.js` after edits**: `node -e "new Function(require('fs').readFileSync('articles_data.js','utf-8')+'; return articlesData;')()"` should not throw.
- **The embedded HTML_TEMPLATE in `add_article.py` can go stale.** It was copied from `generate_article_pages.py`, but the live site's article template evolves over time (e.g. the "Contact Us" nav link was dropped in favor of "Request a Pilot"; as of July 2026 every article carries a Substack newsletter section and an X.com footer link, both now baked into `HTML_TEMPLATE`). Before trusting the template, diff it against the *most recently added* article (check `git log --diff-filter=A -- 'articles/*/index.html'` for the latest one), not just any existing article — older ones may reflect older conventions. If it's drifted, fix `HTML_TEMPLATE` in `add_article.py` first, then regenerate.
- **A handful of older articles were missing the newsletter section / X.com link entirely** (added by hand before those blocks existed on the site) and were backfilled in bulk on 2026-07-06. If you spot another article missing either block, insert them right before `</article>`→`<footer>` and inside the footer's `<div class="container text-center">` respectively — copy the exact markup from a recent article like `chris-parker-technology-leadership/index.html`.
