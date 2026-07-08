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

3. **Write the content to a file** in the same directory as any extracted images (so bare-filename `<img src="...">` references resolve), matching the site's format: `<h2>` section headers, `<p>` paragraphs, `<ul><li>` lists, and centered image blocks:
   ```html
   <div style="text-align: center; margin: 2rem 0;">
       <img src="the-5-cs-of-screen-time.jpeg" style="max-width: 100%; border-radius: 8px;" alt="..." />
       <p style="font-size: 0.9rem; color: var(--text-muted); margin-top: 0.75rem;">Caption text</p>
   </div>
   ```
   Copy the structure of the most recently published post (check `git log --diff-filter=A --oneline -- 'blog/*/index.html'` for the latest) for exact conventions -- e.g. `blog/ai-implementation-in-k12-schools/index.html` had a "Back to Blog" nav link above the header, an FAQ section at the end, and a `<p class="lead">` intro. The template also ships a `.reflect-box` CSS class (a highlighted callout box) useful for "pause and reflect" / pull-quote style callouts if the content calls for it.

4. **Run the script**:
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

5. **Clean up staging files.** If the user dropped the source PDF/image into `blog/documents/` or `blog/images/` before this workflow ran, those are staging/inbox locations, not the published location -- the real assets now live in `blog/<slug>/`. Leaving the originals behind creates orphaned clutter (this already happened once: `blog/images/ai-trust-gap.png` was left behind after an early post's hero image was swapped out, and is unused as of 2026-07). **Ask the user before deleting** (per the standing rule about destructive actions), but recommend removing the now-duplicated staging copies.

6. **Verify the diff is minimal**: `git diff --stat` should show `index.html` (~11-13 lines) plus new files under `blog/<slug>/`. If `index.html` shows hundreds of changed lines, stop -- something went wrong (e.g. the `id="blog"` marker moved and the insertion landed in the wrong section).

7. **Preview locally before committing** -- same routine as the other content skills: check `netstat -ano | grep ":8000.*LISTENING"` for stray/duplicate processes first (kill and restart a single instance if needed), then open `http://localhost:8000/index.html#blog` (hard-refresh) and `http://localhost:8000/blog/<slug>/` to confirm the card and full post render correctly, including any embedded images.

8. **Ask before committing/pushing.** Don't `git add`/`git commit`/`git push` without explicit confirmation. Stage only the files this workflow touched -- check `git status` first for unrelated in-progress work, never `git add -A` blindly.

## Troubleshooting

- **Cover/content image download fails**: same as add-article -- the script shells out to `curl.exe` with a browser User-Agent since some hosts reject bare `urllib` requests. Fall back to a local file path if a URL keeps failing.
- **"already exists" abort**: `blog/<slug>/` is already present. Check whether the post was already added, or pick a different `--slug`. If regenerating, `rm -rf blog/<slug>` first.
- **A local image reference in content doesn't get picked up**: the script only auto-resolves *bare filenames* (no `http://`, no `/`) that exist next to `--content-file`. If the content HTML references a path with a slash, or the image lives somewhere else, either move the image next to the content file or fix the path manually before running the script.
- **Card lands in the wrong spot / wrong section**: `update_index_html_card()` finds the FIRST `<div class="grid-3">` after `id="blog"` in `index.html`. If a homepage redesign adds another `grid-3` before the blog one, or nests the blog cards differently, the insertion point in `add_blog_post.py` will need updating.
- **PDF has no extractable images**: `pdf_image_utils.py` only pulls images embedded as PDF XObjects. A PDF where a "graphic" is actually rendered from vector/text content won't yield anything -- there's nothing to extract in that case; describe it in prose instead or ask the user for the original graphic file.
- **`pip install pymupdf` fails or isn't wanted**: PDF image extraction is optional -- if it's unavailable, just read the PDF's text content (the Read tool already handles that) and write text-only content; skip embedded images.
