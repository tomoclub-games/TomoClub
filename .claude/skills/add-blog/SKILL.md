---
name: add-blog
description: Add a new post to the TomoClub Blog (distinct from the Education Hall -- see add-article for that). Use when the user wants to upload, add, or publish a new "blog" post, or mentions the TomoClub Blog specifically. Needs a title, category, and either a source document (PDF/doc) or content from the user, plus a cover image.
tools: Bash, Read, Edit, Grep
---

# Add Blog Post

Adds one new post to the TomoClub Blog using `add_blog_post.py` at the repo root. This is a **separate system from the Education Hall** (`add-article` skill) -- different URL space (`blog/<slug>/` vs `articles/<slug>/`), different template, different homepage grid, and no JS data registry. Don't reach for `add_article.py` for a "blog" request or vice versa; check with the user if it's ambiguous which one they mean.

## Key differences from Education Hall articles (don't copy those conventions here)

- **No publish date.** Dates were deliberately removed from every blog post and homepage card sitewide (commit `e6ed3d6`, "Remove dates from all blog posts and homepage cards"). Don't add one back to the template or the content.
- **No inline cover image.** The cover/hero image is used ONLY for the homepage card thumbnail and OG/Twitter meta tags -- verified against every live post as of 2026-07, none of them render the cover inside the article body. Don't add an `<img class="article-cover">` under the header by analogy with articles.
- **Cover lives inside the post's own folder** as `blog/<slug>/hero.<ext>`, not a shared `blog/images/` folder.
- **No Substack newsletter embed / no X.com footer link** -- those are an Education Hall convention only. Blog post footers are plain (logo, tagline, nav links, copyright).
- **Newest card goes at the TOP of the grid, not the end.** Unlike the Education Hall grid, the `#blog` `grid-3` has no JS sort/filter -- it's a static grid in DOM order, so the newest post must be FIRST in the DOM to display first on page load.
- **No JS/JSON data registry.** There's no `blog_data.js` equivalent to update -- the homepage card *is* the registration.

## Content fidelity to the source document

Convert the source as close to 1:1 as possible -- don't let normal editorial instincts (paraphrasing, restructuring, "improving" layout) creep in.

- **Never summarize or paraphrase the source body text. Use the exact wording, verbatim.** This is not "close enough" -- word choice, sentence order, and phrasing are the user's, not a first draft to be rewritten. The description/meta-teaser (which is explicitly asked for separately) is the one exception; the article/post body itself must match the doc word-for-word.
- **Preserve the source's line breaks.** A sentence-level line break in the doc is structural signal (a new beat, a deliberate pause, a new list item), not filler to merge into flowing prose. Don't silently reflow multiple source lines into one paragraph.
- **Every bold span in the source needs an explicit `<strong>` in the output.** Do a dedicated pass just for this -- skimming for bold while reading for content is how spans get missed (e.g. a bolded term like "AI literacy curriculum for schools" silently dropped to plain text). Check the source text specifically for bold runs before calling the content pass done.
- **Reproduce the source's actual layout for callouts/boxes** (e.g. `.reflect-box`), don't redesign it. If the doc has a callout as "label + one sentence," render it as label + one sentence -- not a bulleted/stacked reformat that "reads better." The user already specified the formatting by writing it that way; match the doc, not your own instinct for what looks better.
- **Replicate tables, not just prose.** If the source has a table, render it as a real `<table>` (`<thead>`/`<tbody>`, `<th>`/`<td>`) matching the source's rows and columns -- don't flatten it into a bulleted list or paragraph. There's no sitewide table CSS yet (only a `.table-responsive` overflow wrapper in `styles.css`), so wrap the table in `<div class="table-responsive">` and give the `<table>` inline styles matching the post's look (border, padding, header row background) -- check the most recently published post with a table for the convention if one exists, otherwise style it consistent with the surrounding `.article-content` typography.
- **Confirm rendering visually before calling a post done**, not just via a clean `git diff`. A clean diff proves the HTML is well-formed, not that it renders correctly -- CSS/template bugs (e.g. `<li>` text picking up a different color than sibling `<p>` text) only show up in an actual screenshot/browser render. Take one before the first "this is done" claim, not only after being told twice.

## Steps

1. **Collect inputs** from the user if not already given:
   - Title
   - Category (e.g. "Parenting", "AI in Education", "Teacher Support", "Leadership", "SEL" -- freeform, no fixed list)
   - Description -- one or two sentences; used as the meta description, the homepage card teaser, and the lead paragraph. Ask for it, or draft one from the source content and confirm it with the user.
   - Cover image -- a URL or a local file path
   - The post's source content, same preference as add-article: **ask "do you have a source document (PDF, doc, text) for this post?" before offering a blank template.**
   - Optional: `--slug` (auto-derived from title if omitted), `--gradient` (`gold`/`teal`/`slate`; auto-rotates if omitted).

2. **If the source is a PDF, extract its embedded images before writing content.** PDFs like infographic-heavy tip sheets often have inline graphics that belong in the post. Use the shared helper:
   ```bash
   python pdf_image_utils.py path/to/source.pdf /path/to/scratch/dir
   ```
   This dumps every embedded image as `page<N>-img<i>.<ext>` and prints their page numbers and dimensions. **Review each one with the Read tool** (view it) before using it -- not every embedded image is worth keeping (some PDFs embed background textures, logos, or decorative elements as separate XObjects). Only reference the ones that are genuinely content (e.g. an infographic that supports the text). Rename the useful ones to something descriptive in the same directory (e.g. `the-5-cs-of-screen-time.jpeg`) so the content HTML and the final published filename stay readable.

3. **If the source is a PDF, extract its hyperlinks too, not just its images.** PDFs (especially ones drafted in Google Docs) commonly carry hyperlinked citations, article references, and CTAs as link annotations that don't show up as visibly different text when the PDF is just read/rendered as an image -- they're easy to miss and drop silently. Pull them with PyMuPDF:
   ```python
   import fitz
   doc = fitz.open("path/to/source.pdf")
   for pno in range(len(doc)):
       for l in doc[pno].get_links():
           rect = l.get("from")
           text = doc[pno].get_textbox(rect) if rect else ""
           print(pno + 1, repr(text.strip()), "->", l.get("uri"))
   ```
   Match each returned anchor text to where it appears in your content and wrap it in `<a href="...">`. For links to `tomoclub.org/articles/<slug>` or other pages on this same site, use a relative path (`../../articles/<slug>/`) instead of the absolute URL so it doesn't leave the site unnecessarily.

4. **Write the content to a file** in the same directory as any extracted images (so bare-filename `<img src="...">` references resolve), matching the site's format: `<h2>` section headers, `<p>` paragraphs, `<ul><li>` lists, and centered image blocks:
   ```html
   <div style="text-align: center; margin: 2rem 0;">
       <img src="the-5-cs-of-screen-time.jpeg" style="max-width: 100%; border-radius: 8px;" alt="..." />
       <p style="font-size: 0.9rem; color: var(--text-muted); margin-top: 0.75rem;">Caption text</p>
   </div>
   ```
   Copy the structure of the most recently published post (check `git log --diff-filter=A --oneline -- 'blog/*/index.html'` for the latest) for exact conventions -- e.g. `blog/ai-implementation-in-k12-schools/index.html` had a "Back to Blog" nav link above the header, an FAQ section at the end, and a `<p class="lead">` intro. The template also ships a `.reflect-box` CSS class (a highlighted callout box) useful for "pause and reflect" / pull-quote style callouts if the content calls for it.
   - **Body links need to visibly stand out, not just be clickable.** The site's global `a` rule (`styles.css`) sets link color equal to body text with no underline, so an in-content `<a>` is invisible against surrounding `<p>` text unless overridden. `add_blog_post.py`'s `HTML_TEMPLATE` already ships a `.article-content a` rule (teal, underlined, bold, navy on hover) for exactly this reason -- don't remove it. If you're hand-editing an already-rendered `blog/<slug>/index.html` instead of going through the script, confirm that rule is present in its inline `<style>` block; if it's missing (e.g. the post predates this fix), add it.

5. **Run the script**:
   ```bash
   python add_blog_post.py --title "Healthy Screen-Time Habits for Kids" \
     --category "Parenting" \
     --description "Healthy screen-time habits require much more than setting time limits..." \
     --cover /path/to/hero.jpeg \
     --content-file /path/to/content.html
   ```
   This single call:
   - Saves the cover as `blog/<slug>/hero.<ext>`.
   - Localizes any `<img>` in the content: external URLs get downloaded and renamed `<slug>-img-N.ext`; bare local filenames (e.g. extracted PDF images) get copied in from next to `--content-file`.
   - Renders `blog/<slug>/index.html` from the current template.
   - Inserts a new card at the **top** of `#blog`'s `grid-3` in `index.html`, auto-rotating the gradient/category-badge color between gold (`#D97706`), teal (`var(--teal)`), and slate (`var(--navy)`) based on how many blog cards already exist.
   - Is duplicate-safe: aborts before writing anything if `blog/<slug>/` already exists; re-running with a slug that already has a homepage card skips that step.

6. **Verify the diff is minimal**: `git diff --stat` should show `index.html` (~11-13 lines) plus new files under `blog/<slug>/`. If `index.html` shows hundreds of changed lines, stop -- something went wrong (e.g. the `id="blog"` marker moved and the insertion landed in the wrong section).

7. **Set up a local preview and hand the user a link.** Check `netstat -ano | grep ":8000.*LISTENING"` for stray/duplicate processes first (kill and restart a single instance if needed), then give the user both links directly: `http://localhost:8000/index.html#blog` and `http://localhost:8000/blog/<slug>/` (mention they may need to hard-refresh).

8. **Ask if the preview looks good or needs changes.** Don't move past this until the user confirms. Loop back to editing the content/card as needed.

9. **Once the user is satisfied, clean up.** Kill the local server process you started and delete any scratch content file you wrote. Also clean up staging files: if the user dropped the source PDF/image into `blog/documents/` or `blog/images/` before this workflow ran, those are staging/inbox locations, not the published location -- the real assets now live in `blog/<slug>/`. Leaving the originals behind creates orphaned clutter (this already happened once: `blog/images/ai-trust-gap.png` was left behind after an early post's hero image was swapped out, and is unused as of 2026-07). Delete the now-duplicated staging copies.

10. **Stage only the files this workflow touched** -- check `git status` first for unrelated in-progress work, never `git add -A` blindly.

11. **Commit with a simple message matching the site's convention**: `Added new blog <Title>` (e.g. `Added new blog AI Policies in K12 schools`) -- check `git log --oneline` for recent examples of this exact style. No body needed.

12. **Ask the user if they want to push the commit -- explain that pushing is what makes the change go live on the actual website**, not just this local commit. Don't push without explicit confirmation. If they confirm, `git push` (to the current branch's tracked remote -- check `git status`/`git branch -vv` first if it's not already tracking one).

## Troubleshooting

- **Cover/content image download fails**: same as add-article -- the script shells out to `curl.exe` with a browser User-Agent since some hosts reject bare `urllib` requests. Fall back to a local file path if a URL keeps failing.
- **"already exists" abort**: `blog/<slug>/` is already present. Check whether the post was already added, or pick a different `--slug`. If regenerating, `rm -rf blog/<slug>` first.
- **A local image reference in content doesn't get picked up**: the script only auto-resolves *bare filenames* (no `http://`, no `/`) that exist next to `--content-file`. If the content HTML references a path with a slash, or the image lives somewhere else, either move the image next to the content file or fix the path manually before running the script.
- **Card lands in the wrong spot / wrong section**: `update_index_html_card()` finds the FIRST `<div class="grid-3">` after `id="blog"` in `index.html`. If a homepage redesign adds another `grid-3` before the blog one, or nests the blog cards differently, the insertion point in `add_blog_post.py` will need updating.
- **PDF has no extractable images**: `pdf_image_utils.py` only pulls images embedded as PDF XObjects. A PDF where a "graphic" is actually rendered from vector/text content won't yield anything -- there's nothing to extract in that case; describe it in prose instead or ask the user for the original graphic file.
- **`pip install pymupdf` fails or isn't wanted**: PDF image extraction is optional -- if it's unavailable, just read the PDF's text content (the Read tool already handles that) and write text-only content; skip embedded images.
- **Multiple `python`/`pip` installs on the same machine resolve to different interpreters**: if `pip install pymupdf` silently no-ops or installs into an environment `python` doesn't see, check `(Get-Command python).Source` vs `(Get-Command pip).Source` (PowerShell) -- if they point at different install directories, either use that specific interpreter directly (e.g. `py -3.11 script.py`) or `python -m pip install pymupdf` so the install target matches the interpreter that will run the script.
- **Body links rendered but look identical to plain text**: means `.article-content a` is missing from that post's inline `<style>` block (see step 4) -- add it rather than adding `style="color: ..."` to each individual `<a>`, so hover state and future edits stay consistent.
