# Refactor plan: real URLs instead of `#` routes (SEO)

Date: 2026-10-24

## Problem

- `index.html` (594 KB) holds 12 "pages" (`#home`, `#ai-literacy`, `#future-ready`, `#pd`, `#guides`, `#education-hall`, `#podcast`, `#results`, `#faqs`, `#ebook`, `#about`, `#blog`) toggled by the hash router in `script.js` (`navigateFromHash`, ~lines 71-121).
- Google ignores everything after `#`. All 12 count as one URL (`/`) with mixed topics. Per-page title/meta from `seoData` are set by JS after load, so crawlers mostly miss them.
- `sitemap.xml` lists 7 `#` URLs (treated as duplicates of `/`). It has only 15 entries and is missing ~45 blog posts, ~70 podcast pages, and `/parents`.
- `education-hall/index.html` and `podcast/index.html` are meta-refresh stubs that redirect to `/#...`, wasting good URLs.
- ~140 HTML files link to `../#podcast`, `../#blog`, `../#home`, etc. Generator scripts and `.claude/skills` also emit `#` links.

## Target URL map

| Old | New |
|---|---|
| `/#home` | `/` |
| `/#ai-literacy` | `/ai-literacy` |
| `/#future-ready` | `/future-ready` |
| `/#pd` | `/professional-development` (`/pd` 301-redirects to it) |
| `/#guides` | `/guides` |
| `/#education-hall` | `/education-hall` |
| `/#podcast` | `/podcast` |
| `/#results` | `/results` |
| `/#faqs` | `/faqs` |
| `/#ebook` | `/leaders-of-tomorrow` (section already removed from `index.html`; shim maps `#ebook` to it) |
| `/#about` | `/about` |
| `/#blog` | `/blog` (already exists as `blog/index.html`; remove the duplicate section from `index.html`) |

In-page anchors such as `#signup` and `#programs` stay. They are normal anchors, not routes.

## Phases

### 0. Baseline
- Create branch `seo-real-urls`.
- Record Search Console data: indexed pages and top queries.
- Run Lighthouse SEO on `/` as the baseline.

### 1. Shared layout
- Extract navbar, footer, `<head>` boilerplate, and modals from `index.html` into partials (e.g. `_partials/header.html`).
- Add a small `build_pages.py` that combines partials with page bodies and writes `<route>/index.html`. This matches the existing Python generator approach.
- Commit the generated output. Vercel stays a static host with no build step.

### 2. Split `index.html`
- Move each `<div id="X" class="page">` body into `pages/X.html`, then build `X/index.html`.
- Give each page a unique static `<title>`, meta description, canonical, OG/Twitter tags, and exactly one `<h1>`. Move the copy from `seoData` into these tags, then delete `seoData`.
- Add JSON-LD: `Organization` on `/`, `FAQPage` on `/faqs`, `PodcastSeries` on `/podcast`.
- Replace the `education-hall/` and `podcast/` redirect stubs with the real pages.
- Load only the JS each page needs (podcast/article data scripts only where used). `/` should shrink well below 594 KB, improving LCP.

### 3. Remove the router
- Delete the hash routing in `script.js` and the `.page` / `.active` CSS toggling. Keep `.animate-on-scroll` fade-in working.
- Set the nav "current" state from `location.pathname`.
- Keep a tiny shim on `/` so old shared links still work. Fragments never reach the server, so a server-side 301 is not possible:

  ```js
  const map = {'#ai-literacy':'/ai-literacy', '#pd':'/professional-development', /* ... */};
  if (map[location.hash]) location.replace(map[location.hash]);
  ```

### 4. Rewrite links site-wide
- Run one script that rewrites `href="../#x"`, `href="/#x"`, `href="#x"` (route ids only), and `tomoclub.org/#x` to the new paths across ~140 HTML files.
- Update generators: `add_article.py`, `add_blog_post.py`, `add_podcast_episode.py`, `generate_article_pages.py`, `fix_podcast_player.py`, and any `articles_data.js` consumers.
- Update `.claude/skills/add-article`, `add-blog`, `add-podcast`. Example: "append card to `#articles-grid` in `index.html`" becomes `pages/education-hall.html`, and the preview URL `index.html#education-hall` becomes `/education-hall`.
- Done when grep finds zero route-style `#` links.

### 5. Vercel config
- Set `cleanUrls: true` and delete the manual `rewrites` list. `/parents.html` then redirects to `/parents` automatically.
- Settle trailing slashes. Today `trailingSlash: false`, but the sitemap lists `/articles/x/`, which causes redirect hops. Pick one style and match the sitemap to it.
- Optional: move the ~70 root `podcast-<youtubeId>/` folders to `/podcast/<slug>`, with 301 `redirects` in `vercel.json`.

### 6. Sitemap and robots
- Add `build_sitemap.py`. It scans every `index.html` and real `.html` page, excludes `archive/`, `scratch/`, and form/thank-you pages, and uses git commit dates for `lastmod`.
- Call it from the add-* scripts so new content lands in the sitemap automatically.
- Confirm `robots.txt` references the sitemap and disallows `scratch/`, `archive/`, and `.py` files.

### 7. Analytics
- `analytics.js` already sends `location.pathname`, so real URLs give per-section page_views for free.
- Confirm GA and Clarity events still fire after the router is removed.

### 8. Verify before merge (Vercel preview)
- Every URL returns 200 with the correct `<title>` and canonical.
- A link checker finds zero 404s and zero route `#` links.
- Old `/#pd`-style links land on the new pages.
- Lighthouse SEO and performance per page, compared against the baseline.
- Visual pass at desktop and mobile widths: navbar, modals, forms (Brevo, Tally), podcast player.

### 9. After launch
- Submit the new sitemap in Search Console and request indexing for the top pages.
- Update external links that use `/#...` (LinkedIn, newsletters, email signatures).
- Watch Search Console coverage for 2-4 weeks.

## Decisions

1. Decided: `#pd` becomes `/professional-development`, with `/pd` as a 301 in `vercel.json`. `#ebook` merges into the existing `/leaders-of-tomorrow` page. The orphaned `#ebook` section and its `seoData` entry were already deleted from `index.html` and `script.js`.

## Open decisions

2. Move podcast pages to `/podcast/<slug>` now or later?
3. Shared layout: build script with partials, or navbar/footer copied into each page by hand? Hand-copying is simpler but drifts out of sync.

## Before starting

Nothing pending. The earlier `parents.html` and `styles.css` changes are already committed.
