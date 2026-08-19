---
name: add-article
description: Add a new Education Hall article to the TomoClub website. Use when the user wants to upload, add, or publish a new article, story, or "innovation hall" / "education hall" piece, or mentions the "semi-automated" article process. Needs a title, category, release date, cover image, and the article body content from the user.
tools: Bash, Read, Edit, Grep
---

# Add Education Hall Article

Adds one new Education Hall article using `add_article.py` at the repo root, a hardened helper script built after the original guide's pipeline (`generate_article_pages.py`) was found to only track 8 of the ~19 articles actually live on the site — most had been added by hand directly into `articles/<slug>/` without ever being registered in `articles_data.js` or `article_metadata`.

## Content fidelity to the source document

Convert the source as close to 1:1 as possible -- don't let normal editorial instincts (paraphrasing, restructuring, "improving" layout) creep in.

- **Never summarize or paraphrase the source body text. Use the exact wording, verbatim.** This is not "close enough" -- word choice, sentence order, and phrasing are the user's, not a first draft to be rewritten. The description/meta-teaser (which is explicitly asked for separately) is the one exception; the article/post body itself must match the doc word-for-word.
- **Preserve the source's line breaks.** A sentence-level line break in the doc is structural signal (a new beat, a deliberate pause, a new list item), not filler to merge into flowing prose. Don't silently reflow multiple source lines into one paragraph.
- **Every bold span in the source needs an explicit `<strong>` in the output.** Do a dedicated pass just for this -- skimming for bold while reading for content is how spans get missed (e.g. a bolded term like "AI literacy curriculum for schools" silently dropped to plain text). Check the source text specifically for bold runs before calling the content pass done.
- **Reproduce the source's actual layout for callouts/boxes**, don't redesign it. If the doc has a callout as "label + one sentence," render it as label + one sentence -- not a bulleted/stacked reformat that "reads better." The user already specified the formatting by writing it that way; match the doc, not your own instinct for what looks better.
- **Replicate tables, not just prose.** If the source has a table, render it as a real `<table>` (`<thead>`/`<tbody>`, `<th>`/`<td>`) matching the source's rows and columns -- don't flatten it into a bulleted list or paragraph. There's no sitewide table CSS yet (only a `.table-responsive` overflow wrapper in `styles.css`), so wrap the table in `<div class="table-responsive">` and give the `<table>` inline styles matching the article's look (border, padding, header row background) -- check the most recently published article with a table for the convention if one exists, otherwise style it consistent with the surrounding `.article-content` typography.
- **Confirm rendering visually before calling an article done**, not just via a clean `git diff`. A clean diff proves the HTML is well-formed, not that it renders correctly -- CSS/template bugs (e.g. `<li>` text picking up a different color than sibling `<p>` text) only show up in an actual screenshot/browser render. Take one before the first "this is done" claim, not only after being told twice.

## Steps

1. **Collect inputs** from the user if not already given:
   - Title
   - Category (e.g. "Leadership", "Innovation", "Equity")
   - Release date, format `"Month D, YYYY"` (e.g. `"July 6, 2026"`)
   - Cover image — a URL or a local file path
   - The article's source content. **Prefer asking "do you have a source document (PDF, doc, text) for this article?" over handing the user a blank template to fill in.** If they have a PDF/doc, read it yourself and write the `<div class="article-content">` HTML directly — matching the site's format (`<h3>` section headers, `<p>` paragraphs, `<ul><li>` lists, centered image blocks like `<div style="text-align: center; margin: 2rem 0;"><img src="..." style="max-width: 100%; border-radius: 8px;" /></div>`) — by copying the structure of an existing article that shares the same style (see `articles/lauren-bolack-leadership/index.html` or `articles/chris-parker-technology-leadership/index.html` for the two current conventions). Only fall back to producing a blank fill-in-the-blank template when the user has no source document and wants to write from scratch themselves.
   - **If the source is a PDF with embedded infographics/diagrams, extract them and embed them at the appropriate points instead of describing them in prose only.** Run the shared helper:
     ```bash
     python pdf_image_utils.py path/to/source.pdf /path/to/scratch/dir
     ```
     This dumps every embedded image as `page<N>-img<i>.<ext>` with page numbers and dimensions (requires `pip install pymupdf` — install it if missing). **Review each one with the Read tool before using it** — not every embedded image is real content (some are logos, textures, or decorative elements). Rename the useful ones descriptively in the same directory, then reference them in your content HTML with a bare filename (e.g. `<img src="the-5-cs-of-screen-time.jpeg" .../>`) in one of the centered image blocks above. `add_article.py` resolves bare filenames against the directory `--content-file` lives in, so keep the content file and the chosen images in the same folder.
   - **If the source is a PDF, also extract its hyperlinks — don't let them get silently dropped.** PDFs (especially Google Docs exports) commonly carry hyperlinked citations, article references, and CTAs as link annotations that read as ordinary black text once flattened to plain text or a rendered image — easy to transcribe as prose and lose entirely. Pull them with PyMuPDF:
     ```python
     import fitz
     doc = fitz.open("path/to/source.pdf")
     for pno in range(len(doc)):
         for l in doc[pno].get_links():
             rect = l.get("from")
             text = doc[pno].get_textbox(rect) if rect else ""
             print(pno + 1, repr(text.strip()), "->", l.get("uri"))
     ```
     Match each anchor text to where it lands in your content and wrap it in `<a href="...">`. For links to another page on this same site (e.g. another `tomoclub.org/articles/<slug>`), use a relative path (`../<slug>/`) instead of the absolute URL.
   - **Body links need to visibly stand out, not just be clickable.** The site's global `a` rule (`styles.css`) sets link color equal to body text with no underline, so an in-content `<a>` is invisible against surrounding `<p>` text unless overridden. `add_article.py`'s `HTML_TEMPLATE` ships a `.article-content a` rule (teal, underlined, bold, navy on hover) for exactly this reason — don't remove it. If hand-editing an already-rendered `articles/<slug>/index.html` instead of going through the script, confirm that rule is present in its inline `<style>` block; add it if missing (e.g. the article predates this fix).
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

5. **Set up a local preview and hand the user a link.** Check `netstat -ano | grep ":8000.*LISTENING"` for stray/duplicate processes first (kill any and start one fresh instance if needed), then give the user both links directly: `http://localhost:8000/index.html#education-hall` and `http://localhost:8000/articles/<slug>/` (mention they may need to hard-refresh).

6. **Ask if the preview looks good or needs changes.** Don't move past this until the user confirms. Loop back to editing the content/template/card as needed — re-run `add_article.py` is only safe if nothing was staged yet (see Troubleshooting for re-run hazards); for small tweaks after the fact, edit `articles/<slug>/index.html`, `articles_data.js`, and the card in `index.html` directly instead of re-running the script.

7. **Once the user is satisfied, clean up.** Kill the local server process you started (`taskkill //F //PID <pid>` on Windows) and delete any scratch content file you wrote (e.g. `new_article_content.html` in the scratchpad dir). Also delete the staging source files: the source PDF/doc (e.g. `articles/documents/<Name>.pdf`) and the original uploaded cover image (e.g. `articles/images/<Name>.png`) — `add_article.py` already copied the cover into `articles/images/<slug>-cover.<ext>`, so the original upload is redundant. Don't delete the generated `articles/<slug>/` folder or the `-cover.*` file.

8. **Verify the diff is minimal** (see step 4 above), then stage only the files this workflow touched — check `git status` first for unrelated in-progress work, never `git add -A` blindly.

9. **Commit with a simple message matching the site's convention**: `Added new article <Author Name>` (e.g. `Added new article Sharon Pepukayi`) — check `git log --oneline` for recent examples of this exact style. No body needed.

10. **Ask the user if they want to push the commit — explain that pushing is what makes the change go live on the actual website**, not just this local commit. Don't push without explicit confirmation. If they confirm, `git push` (to the current branch's tracked remote — check `git status`/`git branch -vv` first if it's not already tracking one).

## Troubleshooting

- **Cover/content image download fails**: the script shells out to `curl.exe` with a browser User-Agent (some hosts reject bare `urllib` requests). If a URL still fails, ask the user for a local file path instead — the script accepts either.
- **"already exists" abort**: the target `articles/<slug>/` directory is already present. Either the article was already added, or the slug collides with something else — check `articles/` and pick a different slug if needed. If you need to regenerate (e.g. after fixing the template), `rm -rf articles/<slug>` first — the registry entries in `articles_data.js`/`generate_article_pages.py` are already dedup-safe, but re-running after deleting the directory will still try to add them; if they're already present it'll correctly skip. **Never re-run against a slug whose registry entries were already committed without first checking** — `next_article_key()` picks the next unclaimed `article_N` number regardless of slug, so re-running for an already-registered slug creates a duplicate `article_N` entry with the same content under a new key. If that happens, `git diff` the two blocks, confirm they're identical, and revert the newer one.
- **Validate `articles_data.js` after edits**: `node -e "new Function(require('fs').readFileSync('articles_data.js','utf-8')+'; return articlesData;')()"` should not throw.
- **PDF has no extractable images**: `pdf_image_utils.py` only pulls images embedded as PDF XObjects — a PDF where a "graphic" is actually vector/text content won't yield anything. Nothing to extract in that case; describe it in prose or ask the user for the original graphic file.
- **A local image reference in content doesn't get picked up**: `add_article.py` only auto-resolves *bare filenames* (no `http://`, no `/`) that exist next to `--content-file`. If the content HTML references a path with a slash, or the image lives elsewhere, move it next to the content file or fix the path before running the script.
- **The embedded HTML_TEMPLATE in `add_article.py` can go stale.** It was copied from `generate_article_pages.py`, but the live site's article template evolves over time (e.g. the "Contact Us" nav link was dropped in favor of "Request a Pilot"; as of July 2026 every article carries a Substack newsletter section and an X.com footer link, both now baked into `HTML_TEMPLATE`). Before trusting the template, diff it against the *most recently added* article (check `git log --diff-filter=A -- 'articles/*/index.html'` for the latest one), not just any existing article — older ones may reflect older conventions. If it's drifted, fix `HTML_TEMPLATE` in `add_article.py` first, then regenerate.
- **A handful of older articles were missing the newsletter section / X.com link entirely** (added by hand before those blocks existed on the site) and were backfilled in bulk on 2026-07-06. If you spot another article missing either block, insert them right before `</article>`→`<footer>` and inside the footer's `<div class="container text-center">` respectively — copy the exact markup from a recent article like `chris-parker-technology-leadership/index.html`.
- **Body links rendered but look identical to plain text**: means `.article-content a` is missing from that article's inline `<style>` block — add it (see the collect-inputs step above) rather than styling each `<a>` individually.
