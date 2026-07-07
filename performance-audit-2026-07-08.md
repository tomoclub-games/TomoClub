# Performance & Bandwidth Audit — 2026-07-08

## Background

The site was reported as slow, and Vercel showed 1GB of outgoing "Fast Data Transfer" in 24 hours despite an estimated ~10 visitors. Investigation and fixes were done in this session; this report captures what was found, what was changed, and the measured impact.

## Root causes found

1. **No lazy loading anywhere.** The homepage alone had 218 `<img>` tags, all eager-loaded, with zero use of `loading="lazy"`. Only 2 of ~140 tracked HTML pages sitewide used it at all.
2. **Unoptimized, oversized images.** 30 blog "hero" PNGs embedded in the homepage's blog carousel were ~1.7–2MB each (53.6MB total), at 1672×941 resolution, displayed at a fraction of that size. No build step or image pipeline exists (no package.json, no ImageMagick/cwebp installed) — images are served exactly as exported.
3. **No caching headers for static assets.** `vercel.json` only set security headers; every image/CSS/JS response came back `Cache-Control: public, max-age=0, must-revalidate`, forcing a revalidation round-trip on every request.
4. **Two abandoned 8K source images** (`tomo AI LAB.jpg`, `tomo LIFE SKILLS.jpg`, ~32MB combined) sitting in the repo root, unreferenced anywhere — dead weight in every deploy.
5. **A stray `tom/` folder** — a full duplicate of `index.html`, `parents.html`, `styles.css`, and various scripts — had been accidentally committed on 2026-05-27 (commit `1321308`, "Fix Amanda Traylor image") and was live and publicly crawlable at `tomoclub.org/tom/`. Git history showed it was being silently kept in sync by recursive site-wide patch scripts (`patch_*.py`, `do_updates.py`) that glob over all HTML files without excluding it.

## Changes made (commit `851e065`, "Optimization 1")

- Added `Cache-Control` headers to `vercel.json` for images (1 day, stale-while-revalidate 1 week) and CSS/JS/fonts (1 hour, stale-while-revalidate 1 day). Kept moderate (not a 1-year immutable cache) because content images get overwritten in place by the site's Python content-update scripts without filename changes.
- Deleted the two unused 8K source images.
- Deleted the stray `tom/` folder.
- Added `loading="lazy"` to below-the-fold images: 195 on the homepage (25 kept eager — nav logos, partner-district marquee, first content photo), plus 33 more across `leaders-of-tomorrow/index.html`, `parents.html`, and 6 article pages (first image on each of those kept eager as the effective hero/cover).

## Measured impact

Method: Lighthouse (headless Chrome) run against two local static servers — one serving the pre-optimization commit (`3075942`), one serving the current code (`851e065`) — both using a small custom server that replays the actual `vercel.json` header rules, so the audit reflects real deployed behavior rather than a generic file server's defaults.

| Metric | Before | After | Change |
|---|---|---|---|
| Total page weight (homepage) | 98.5 MB | 10.7 MB | **−89%** |
| Largest Contentful Paint (throttled) | 102.6 s | 46.9 s | 2.2× faster |
| Network requests | 1,139 | 967 | −172 |
| Remaining "defer offscreen images" savings | 4.1 MB | 0.57 MB | most slack absorbed |

**Caveats on reading these numbers:**
- Absolute LCP times are inflated by Lighthouse's default throttled-mobile simulation profile (~1.6 Mbps, 4x CPU slowdown) — treat as relative, not real-world; a broadband visitor sees single-digit seconds, not a minute-plus.
- The Lighthouse Performance score stayed at 55 in both runs. Both LCP values are far past the "good" threshold (2.5s), so the scoring curve is saturated in both cases and doesn't distinguish "bad" from "less bad." The byte-weight and LCP-seconds numbers are the meaningful ones here.
- The 98.5MB → 10.7MB figure is a direct byte-weight measurement, not throttling-dependent — this is the number that answers the original Vercel bandwidth question. A visitor who doesn't scroll the entire homepage now pulls roughly 9x less data than before.

## New findings from the audit (not yet acted on)

- The largest remaining resources on the homepage are now **third-party embed scripts loading unconditionally**, not images: a Google Drive file-viewer bundle (~1.8MB combined), YouTube embedded-player scripts (~1.15MB), and Substack's embed JS (~386KB).
- A few **partner-district logo PNGs kept eager are surprisingly heavy** for simple logo icons: `waseca_bluejays.png` (445 KiB), `media__1777109413492.png` (424 KiB), `media__1777109413531.png` (204 KiB).

## Image compression (second pass)

Converted ~82 oversized, fully-opaque PNGs (blog heroes, article photos, team photos) to quality-82 JPEG, resized to sensible caps (1200px for blog heroes, 900px for portraits), and updated all ~202 references across 52 files (`<img>` src, `og:image`/`twitter:image` meta tags, `generate_article_pages.py`'s per-article cover mappings). Recompressed 5 already-JPEG files in place. Left the 17 broken placeholder files and 2 already-reasonable JPEGs untouched. Resized/re-compressed 12 of 13 partner-district logo PNGs in place (kept PNG — most have genuine transparency), reduced from 1.4MB to 203KB combined; `choice_charter.png` was locked by another process during the run and left as-is (40KB, low impact).

**Direct measurement:** the ~82 converted files dropped from 82.96MB to 5.81MB combined — a 93% reduction. Also discovered and removed ~40MB of additional unused duplicate images while investigating (9 root-level author photos, 15 root `blog post N.png` files, a whole unused `author photos/` folder) — same pattern as the `tomo AI LAB`/`LIFE SKILLS` files, confirmed unreferenced anywhere.

**Combined effect on the whole tracked repo: 229MB → 77MB (−66%).**

**Lighthouse re-run caveat:** a homepage-only, non-scrolling Lighthouse audit only fetches the ~25 still-eager images (nav logos, first content photo) — the 82 recompressed images are almost all below-the-fold and lazy-loaded, so they were *already excluded* from the previous audit's byte count and don't show up as a big delta in a repeat homepage-only run (10,732 KiB → 10,104 KiB, a modest 6% further drop, plus LCP improving from 46.9s → 28.1s). The real payoff from this step is: (a) anyone who actually scrolls the homepage now pulls a fraction of the data, (b) every other page that references these images (blog posts' `og:image`, article pages, `leaders-of-tomorrow`, `parents.html`) is directly lighter, and (c) the repo/deploy itself is 66% smaller.

## Browser verification (post-compression)

Served the site locally and drove it with headless Chrome (Puppeteer) across the homepage, a converted blog post, `leaders-of-tomorrow`, `parents.html`, the `#blog` route, the `#ai-literacy` program route, and one of the 6 known-broken articles.

**Found and fixed a real regression from the compression pass:** the reference-rewriting script matched filenames as substrings rather than exact matches. Since all 30 blog posts share the literal filename `hero.png`, the substring match also corrupted 3 unrelated references — `assets/ai-literacy-hero.png`, `assets/future-ready-hero.png`, `assets/ai-pd-hero.png` — to `.jpg`, even though those 3 files were correctly *left as PNG* (they have genuine transparency) and never actually converted. Result: 3 broken image references. Reverted all 3 references back to `.png` — the underlying files were never touched, so this was a reference-only fix.

**Found and fixed a second regression:** one of the 15 root-level `blog post N.png` duplicates deleted earlier (`blog post 3.png`) turned out to be genuinely referenced, via a URL-encoded path (`./blog%20post%203.png`) that an earlier grep check (matching a literal space) missed. Confirmed via git blob hash that this file was byte-identical to `blog/how-can-schools-cultivate-leadership-skills-in-students/hero.png`, and repointed the reference to that post's already-converted `hero.jpg` instead of restoring the dead duplicate.

Both fixes verified: the `#ai-literacy` route and the fixed blog card now load their images correctly (confirmed via `naturalWidth` checks and visual screenshots).

**Also discovered, not a bug:** `index.html` is a single-page app with client-side hash routing — sections like `#blog`, `#ai-literacy`, `#future-ready` are separate `.page` elements (`display:none` until navigated to). The 30 blog hero images live on the `#blog` route, not the default homepage view — meaning a plain homepage visit never fetches them at all (even better for bandwidth than "lazy-loaded below the fold," which was how this was described earlier). This also explains why an automated headless-browser scroll-through couldn't trigger their load without actually navigating to that route — not a lazy-loading defect.

**Remaining pre-existing gaps (not caused by this session's changes, not fixed):** 3 dangling references were already broken before any of today's work — `blog pictures/Why Schools Should Train Teachers in AI Literacy.png` (a stale reference to a folder that never existed), and two blog posts (`why-every-school-should-offer-ai-training-for-educators`, `how-teachers-use-ai-smarter-classrooms`) that never had a `hero.png` in git history at all.

All other spot-checked pages (homepage top, `leaders-of-tomorrow` team photos, `parents.html` program thumbnails, a converted blog post) render correctly with no visible compression artifacts.

## Correction: the 3 "transparent" hero files were never PNGs at all

The 3 files excluded from the original conversion pass (`assets/ai-literacy-hero.png`, `assets/future-ready-hero.png`, `assets/ai-pd-hero.png`) were skipped based on an alpha-channel check that reported real transparency (minAlpha=0). That check was wrong: the script grabbed `stats.channels[stats.channels.length - 1]` assuming the last channel is always alpha, but these files have only 3 channels — it was silently reading the **Blue channel** and misreporting it as alpha. Verified directly with `file`: all 3 are genuine JPEG bitstreams (1024×1024, 3 components) that happen to have a `.png` extension. There was never any transparency to preserve — the right-edge fade visible on these program pages comes entirely from a CSS `mask-image` rule (`styles.css` ~line 1930), which works on any image regardless of the source file's own transparency.

Fixed: re-encoded all 3 at the same quality-82 mozjpeg settings used elsewhere this session, renamed `.png` → `.jpg` to match actual content, updated the 3 references in `index.html`. Result: 720KB→112KB, 746KB→128KB, 769KB→132KB (~84-85% reduction). Verified via headless browser on all 3 routes (`#ai-literacy`, `#future-ready`, `#pd`) — images load correctly, edge fade still renders identically, no visual artifacts.

## Not yet done

- Lazy-loading the third-party iframe embeds (YouTube/Google Drive/Substack) noted above.
- Browser spot-check of pages after image compression.
- Separate task: fix the 17 broken article images (Vercel security-checkpoint placeholder files) across 6 articles — needs original source images/links.
