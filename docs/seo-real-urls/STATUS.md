# SEO Real URLs: Status

This is the single source of truth for progress. Claude Code reads it at the start of every session and updates it after every completed step.

**Last updated:** 2026-10-26 by Claude Code

---

## Current position

- **Current phase:** H. Analytics
- **Current step:** H5 (optional)
- **Waiting on:** Rohith: do the optional GA4 Realtime check, or skip it; then review Phase H
- **Next action:** on approval, run `seo-next` to start Phase I (verify before merge)

---

## Phases

Status values: `not started` · `in progress` · `waiting for review` · `approved` · `blocked`

| Phase | Status | Output | Approved by / date |
|---|---|---|---|
| A. Baseline | approved | `baseline/` folder, Q1 + Q2 + Q3 decided | Rohith, 2026-10-26 |
| B. Shared layout | approved | `_partials/`, `build_pages.py` | Rohith, 2026-10-26 |
| C. Split `index.html` | approved | `<route>/index.html` pages | Rohith, 2026-10-26 |
| D. Remove router | approved | Router-free `script.js`, hash shim | Rohith, 2026-10-26 |
| E. Rewrite links | approved | Zero route `#` links; updated generators and skills | Rohith, 2026-10-26 |
| F. Vercel config and podcast pages | approved | Updated `vercel.json`; 107 generated episode pages; player redirect | Rohith, 2026-10-26 |
| G. Sitemap, robots, canonicals, deploy clean-up | approved | `build_sitemap.py`, new `sitemap.xml`, canonicals on every indexable page, `.vercelignore` allowlist | Rohith, 2026-10-26 |
| H. Analytics | in progress | GA + Clarity check | |
| I. Verify before merge | not started | Preview check report; merge | |
| J. After launch | not started | Search Console submission, monitoring notes | |

---

## Current phase checklist: H. Analytics

Task spec: `00-context.md` section 17.

- [x] H1. Plan shown to Rohith and accepted
- [x] H2. Coverage audit (2026-10-26): all 196 deployed pages load `analytics.js` exactly once; GA4 is configured once per page (123 pages have the inline GA tag and `analytics.js` skips its own; 73 get GA from `analytics.js`). Tracked sections (`data-track`) exist only on `build-with-us/` and its thank-you page
- [x] H3. Build With Us form sends people to `/build-with-us/thank-you` directly (today `thank-you.html`, which costs a redirect hop)
- [x] H4. Preview `tomoclub-website-54iz8yty6` (commit `fab1d62`), headless Chrome, bypass token sent only to the preview host: on `/`, `/ai-literacy`, an article, a blog post, an episode, `/build-with-us` and `/#pd`, each load sends exactly one `page_view` to `G-FEGGQ2ZDMT` with the real URL; `/#pd` records only `/professional-development` (the shim redirects before GA fires); Clarity, LinkedIn and Meta fire on every page; no page errors. `section_view` (needs scrolling) not exercised
- [ ] H5. Rohith confirms in GA4 Realtime that page paths like `/ai-literacy` and `/podcast-<id>` appear while the preview is opened (optional; GA may filter preview hostnames)
- [ ] H6. Summary given; phase set to `waiting for review`

---

## Completed phases

Each approved phase moves here with a one-line result and its full checklist.

### A. Baseline (approved by Rohith, 2026-10-26)

Result: Search Console, Lighthouse and inventory baselines saved in `baseline/`; Q1 (keep podcast URLs), Q2 (build script) and Q3 (www host) decided.

- [x] A1. Plan shown to Rohith and accepted
- [x] A2. Branch `seo-real-urls` created; staged `#ebook` removal and plan doc carried over
- [x] A3. Search Console export saved (Rohith); summary in `baseline/search-console/SUMMARY.md`
- [x] A4. Lighthouse baseline saved (`baseline/lighthouse.md`)
- [x] A5. Inventory script run; `baseline/inventory.md` saved
- [x] A6. Q1, Q2 and Q3 answered by Rohith and logged
- [x] A7. Summary given; phase set to `waiting for review`

### B. Shared layout (approved by Rohith, 2026-10-26)

Result: `index.html` is generated from `_partials/` and `pages/index.html` by `build_pages.py`, byte-identical to before. Commit `8cb9700`.

- [x] B1. Plan shown to Rohith and accepted
- [x] B2. Layout spec `02-layout-spec.md` approved by Rohith (**no code before this**)
- [x] B3. Partials extracted from `index.html` into `_partials/` (6 files); page body moved to `pages/index.html`
- [x] B4. `build_pages.py` written (stdlib only); error cases tested (missing value, missing partial, self-include)
- [x] B5. `py build_pages.py` regenerates `index.html` byte-identical to the original (`cmp` and `git diff` empty); `--check` exits 0; footer edit flows through and `--check` flags it
- [x] B6. `_partials/` and `pages/` added to `.vercelignore`. Browser smoke test not run: output is byte-identical to the committed `index.html`, so the page cannot behave differently
- [x] B7. Summary given; phase set to `waiting for review`

### C. Split `index.html` (approved by Rohith, 2026-10-26)

Result: 10 route pages with static SEO tags and JSON-LD; redirect stubs replaced; `/` unchanged apart from partials. Commit `cfd7b99`.

- [x] C1. Plan shown to Rohith and accepted
- [x] C2. Partials updated: root-absolute asset paths, `og:url`, head cleanup, generated-file comment, nav and footer links point to the new URLs. Shared "Global CTA" section moved to `_partials/cta.html` and included on every page
- [x] C3. Router guard in `script.js`: hash routing runs only on pages with more than one `.page` div. Toolkit download URL made root-absolute. `script.js?v=24`
- [x] C4. 10 page files in `pages/` with unique title, description, canonical, social tags and one `<h1>`; built to `<route>/index.html`. Relative `src`/`href`/`data-file` paths in their bodies made root-absolute
- [x] C5. JSON-LD added: `FAQPage` on `/faqs`, `PodcastSeries` on `/podcast`, `Service` on the three program pages
- [x] C6. Redirect stubs `education-hall/`, `podcast/`, `blog/` replaced by the real pages
- [x] C7. Local check: every new URL returns 200 with the right title, canonical and one `<h1>`; desktop and mobile screenshots of each page; `/` still works with `#` links; `build_pages.py --check` passes. Note: headless Chrome mobile shots are clipped on the right on every page including the unchanged `/`, so they are a tool limit, not a regression; a real-device mobile pass is in Phase I
- [x] C8. Summary given; phase set to `waiting for review`

### D. Remove router (approved by Rohith, 2026-10-26)

Result: `/` is home only (82 KB); router, `seoData` and `.page` CSS removed; hash shim on every page; nav marks the current page. Commit `29e1597`.

- [x] D1. Plan shown to Rohith and accepted
- [x] D2. `pages/index.html` slimmed to the home section; `/` JSON-LD trimmed to `Organization` + `WebSite` (`SearchAction` dropped). `/` is now 82 KB (was 571 KB)
- [x] D3. Hash router, `seoData` and the `.page` show/hide system removed (`script.js`, `styles.css`, page wrappers, head ids)
- [x] D4. Hash shim on every page: `#<route>` on load or on `hashchange` goes to the real URL; in-page anchors untouched
- [x] D5. Nav "current" state set from `location.pathname`
- [x] D6. Local check (puppeteer-core + local Chrome): all 11 pages render; scroll animations, FAQ accordion, article and podcast filters, download modal, theme toggle and mobile menu work; all 12 old `/#route` links land on their page; in-page `#pd` link navigates; `/#signup` stays on `/`; `--check` passes. Pilot and video modals have no trigger on any page, so they were not exercised. Mobile menu matches production
- [x] D7. Summary given; phase set to `waiting for review`

### E. Rewrite links (approved by Rohith, 2026-10-26)

Result: 859 route links rewritten; add-* scripts and skills work on `pages/` + build; `/guides` toolkit downloads fixed. Commit `9914ddf`.

- [x] E1. Plan shown to Rohith and accepted
- [x] E2. `tools/seo-real-urls/rewrite_links.py` written; dry run reviewed. Bare `#x` is only rewritten inside `href=` (the hash shim's JS map is left alone); `.md` files only under `.claude/skills/`; `images.json` skipped (not UTF-8, no links). No links flagged for review
- [x] E3. 859 links rewritten in 157 files (source HTML, `api/signup.js`, generator templates, skills); generated pages rebuilt
- [x] E4. Apex `https://tomoclub.org/...` links changed to `https://www.tomoclub.org/...` (Q3)
- [x] E5. Generators updated: link templates in all 7 scripts; `add_article.py`, `add_blog_post.py`, `add_podcast_episode.py` edit `pages/<route>.html` with root-absolute card URLs and run `build_pages.py`. Also fixed `add_article.py`'s grid marker, broken since commit `f4262c4` (2026-10-23, before this project)
- [x] E6. Skills `add-article`, `add-blog`, `add-podcast` updated (files, sections, preview URLs, build step)
- [x] E7. Each add-* script tested in a throwaway git worktree (podcast YouTube fetch stubbed): card lands in the right `pages/` file and position (article last, blog and podcast first), build runs, no `#` links emitted; worktree removed
- [x] E8. `inventory.py --check` reports zero (excluding `archive/` and `sitemap.xml`); `build_pages.py --check` passes; 219 internal URLs on the 11 main pages all resolve locally (after the `/guides` toolkit fix below)
- [x] E9. Summary given; phase set to `waiting for review`

### F. Vercel config and podcast pages (approved by Rohith, 2026-10-26)

Result: 107 generated episode pages; clean, no-slash URLs; 301 redirects for `/pd` and the podcast player; tested on the Vercel preview. Commits `d629d91`, `36819c8`.

- [x] F1. Plan shown to Rohith and accepted
- [x] F2. Episode page spec (content, title and description rules, JSON-LD) approved by Rohith (**no code before this**)
- [x] F3. `build_podcast_pages.py` generates all 107 `podcast-<id>/index.html` from `podcasts_data.js` with the shared layout; `--check` mode. 107 unique titles and descriptions; valid JSON-LD; desktop and mobile screenshots checked (mobile hero and card padding fixed)
- [x] F4. Podcast cards and all other internal links to `podcast-player.html?id=X` point to `/podcast-<id>`; `add_podcast_episode.py` and the add-podcast skill generate the episode page
- [x] F5. Trailing slash settled: no trailing slash. 205 absolute and 103 relative folder links rewritten (relative `../x/` links were already broken on production because Vercel serves these pages without the slash); generator templates updated
- [x] F6. `vercel.json`: `cleanUrls: true`, manual `rewrites` removed, 301 `/pd` to `/professional-development`, 301 `/podcast-player.html?id=X` to `/podcast-X`, 301 `/podcast-player.html` (no id) to `/podcast`
- [x] F7. Local check: episode pages render (title, h1, video, meta); link crawl of all 199 deployable pages (6,273 internal links) finds no broken links except one missing image that predates the project; `build_pages.py --check`, `build_podcast_pages.py --check` and `inventory.py --check` pass
- [x] F8. Vercel preview, pushed with Rohith's OK and tested with Rohith's automation bypass token (kept in `C:\Users\rohit\.vercel-bypass`, never printed): 18 pages return 200; `/pd` 301 to `/professional-development`; `.html`, trailing-slash and `/index.html` URLs 308 to the clean URL; unknown URL 404; `/podcast-player.html?id=X` reaches `/podcast-X` in 2 hops (308 clean URL, then 301) with `?id=X` left on the URL. The episode canonical is clean, so Google consolidates to `/podcast-X`
- [x] F9. Summary given; phase set to `waiting for review`

### G. Sitemap, robots, canonicals, deploy clean-up (approved by Rohith, 2026-10-26)

Result: 194-URL sitemap from `build_sitemap.py`; canonicals on every indexable page; internal files, orphan pages and source PDFs off the site; one-off scripts and `articles_data.js` retired; AI implementation post graphics restored. Commits `69098ae` to `5cc3a18`.

- [x] G1. Plan shown to Rohith and accepted (internal file list and orphan pages decided)
- [x] G2. `.vercelignore` keeps internal files off the site: `docs/`, `tools/`, `.claude/`, `*.py`, `*.md`, `*.docx`, and the 8 internal root files; every file the site uses still deploys
- [x] G3. Orphan pages `contact-form.html`, `schedule.html`, `waitlist-form.html` moved to `archive/` with 301 redirects (`/contact-form` and `/schedule` to `/contact-us`, `/waitlist-form` to `/parents`); `build-with-us/thank-you.html` marked `noindex, follow`
- [x] G4. Self-referencing `www`, no-slash canonical and `og:url` on every indexable page: 75 pages updated (25 articles, 44 blog posts, `contact-us.html`, `privacy-policy.html`, `terms-and-conditions.html`, `build-with-us/index.html`, plus `og:url` on `parents.html` and `leaders-of-tomorrow/`); templates in `add_article.py`, `add_blog_post.py`, `generate_article_pages.py` emit them
- [x] G5. `build_sitemap.py` writes `sitemap.xml` (194 URLs: 17 main and root pages, 25 articles, 44 blog posts plus `/blog`, 107 episodes; no `#`, no `noindex`, no-slash `www`, `lastmod` from git); the 3 add_* scripts run it; `--check` mode. Only the player redirect and the `noindex` thank-you page are left out
- [x] G6. `robots.txt` checked: `Allow: /` and the sitemap line; no change needed
- [x] G7. Preview `tomoclub-website-gpexthpsz` (commit `a431110`): all 194 sitemap URLs return 200 with canonical = sitemap URL and no `noindex`; 19 internal files return 404 (`docs/`, `tools/`, `.claude/`, `.py`, `.md`, the 8 root files, `articles_data.js`, `_partials/`, `pages/`); `/contact-form`, `/schedule`, `/waitlist-form`, `/pd` return 301 to the right page; site assets still load; thank-you page is `noindex`. Local link crawl clean (only the known missing image)
- [x] G8. Summary given; phase set to `waiting for review`

---

## Decision log

Add one line for every decision. Newest at the bottom. Never delete a line; if a decision changes, add a new line that replaces it.

| Date | Decision | Source |
|---|---|---|
| 2026-10-24 | `#pd` becomes `/professional-development`; `/pd` 301 in `vercel.json` | Rohith (plan doc) |
| 2026-10-24 | `#ebook` merges into `/leaders-of-tomorrow`; orphaned section and `seoData` entry deleted | Rohith (plan doc) |
| 2026-10-26 | Project set up with the phased-project workflow on branch `seo-real-urls` | Rohith |
| 2026-10-26 | Plan doc moved to `docs/seo-real-urls/01-refactor-plan.md`; plan phases §0-§9 map to A-J | Claude Code (setup) |
| 2026-10-26 | Phase A plan accepted | Rohith |
| 2026-10-26 | Search Console access via Rohith's account | Rohith |
| 2026-10-26 | Q2: shared layout uses `build_pages.py` with partials (not hand-copied) | Rohith |
| 2026-10-26 | Phase G scope added: every article, blog post and `podcast-<id>/` page gets a self-referencing `www` canonical tag | Rohith |
| 2026-10-26 | Q3: canonical host is `https://www.tomoclub.org`. Apex already 308-redirects to www; keep it | Rohith |
| 2026-10-26 | Q1: keep `podcast-<id>/` URLs (no move to `/podcast/<slug>`). In Phase F, 301 `podcast-player.html?id=X` to `/podcast-X`, and first create the missing `podcast-<id>/` pages for player-only episodes (8 seen in Search Console) | Rohith |
| 2026-10-26 | Phase A approved | Rohith |
| 2026-10-26 | Phase B plan accepted | Rohith |
| 2026-10-26 | Layout spec `02-layout-spec.md` approved | Rohith |
| 2026-10-26 | Phase B approved | Rohith |
| 2026-10-26 | Phase C plan accepted | Rohith |
| 2026-10-26 | `/blog` built from the `#blog` section; `blog/index.html` was a redirect stub, not a real page | Claude Code (fact correction) |
| 2026-10-26 | New page titles where `seoData` was missing or outdated: `/podcast` = "The Learning Shift Podcast \| TomoClub" (seoData said "The TomoClub Podcast \| Play & Learn"); `/results` = "Results and Case Studies \| TomoClub" (no seoData entry). Needs Rohith's confirmation | Claude Code |
| 2026-10-26 | Phase C approved, including the `/podcast` and `/results` titles and the Educational Hall link change | Rohith |
| 2026-10-26 | Phase D plan accepted | Rohith |
| 2026-10-26 | Hash shim runs on every page (not only `/`), so leftover `#route` links in page bodies work until Phase E | Claude Code |
| 2026-10-26 | Phase D approved | Rohith |
| 2026-10-26 | Phase E plan accepted | Rohith |
| 2026-10-26 | Bug from Phase C fixed: the path converter turned `/guides` toolkit `data-file="SEL_new.pdf"` into `"/SEL_new.pdf"`, so `script.js` stopped adding `toolkits/` and downloads would 404. Now `data-file="/toolkits/SEL_new.pdf"` (all 4 guides). Found by the E8 link crawl | Claude Code |
| 2026-10-26 | `inventory.py` no longer writes the baseline by default (`--write` needed), so `docs/seo-real-urls/baseline/inventory.md` stays the Phase A record | Claude Code |
| 2026-10-26 | Phase E approved. Deleting `add_brad_article.py` / `add_shane_article.py` still open | Rohith |
| 2026-10-26 | Q1 revised: the 68 existing `podcast-<id>/` pages are empty shells (blank title and h1, "January 01, 1970", 0:00). Phase F generates all 107 episode pages from `podcasts_data.js` with the shared layout, then redirects the player to them | Rohith |
| 2026-10-26 | Trailing slash: none. Matches today's `trailingSlash: false` and the canonicals set in Phase C | Claude Code (in the Phase F plan) |
| 2026-10-26 | Phase F plan accepted | Rohith |
| 2026-10-26 | Episode page spec `03-episode-page-spec.md` approved | Rohith |
| 2026-10-26 | Episode speakers stored as "Feat. Name" are shown as "Name" | Claude Code |
| 2026-10-26 | E4 was incomplete: it only changed apex links that carried a route hash. 13 plain `https://tomoclub.org/...` links (in `build-with-us/` and 2 blog posts) changed to www in Phase F | Claude Code |
| 2026-10-26 | `leaders-of-tomorrow/index.html` linked to `leaders-of-tomorrow.html`, which does not exist (banner button and breadcrumb JSON-LD); now `/leaders-of-tomorrow` | Claude Code |
| 2026-10-26 | Phase F committed (`d629d91`) and branch `seo-real-urls` pushed to GitHub with Rohith's OK. Preview `https://tomoclub-website-fbrzicbpe-tomo-club.vercel.app` built, but Vercel Deployment Protection (SSO) blocks unauthenticated requests | Rohith / Claude Code |
| 2026-10-26 | Player redirect accepted as is: 2 hops and a leftover `?id=` query; the target canonical is clean. Revisit only if Search Console flags it | Claude Code |
| 2026-10-26 | Revoke the Vercel automation bypass token and delete `C:\Users\rohit\.vercel-bypass` after Phase I | Claude Code |
| 2026-10-26 | Phase F approved | Rohith |
| 2026-10-26 | `add_brad_article.py` and `add_shane_article.py` deleted (one-off scripts with paths to JANMEJAY's computer; their articles stay) | Rohith |
| 2026-10-26 | Missing image on `/blog/ai-implementation-in-k12-schools` stays broken until Rohith supplies the picture | Rohith |
| 2026-10-26 | Found: production serves internal files publicly (all `.py` scripts, `.claude/` skills, `*.md`, `Website Feedback.pdf`, `Updated feedback.pdf`, the publishing guide PDF, `*.txt`, `images.json`, `podcast_data.json`). This branch would add `docs/` (Search Console export) and `tools/`. A quick scan found no secrets. Phase G adds a `.vercelignore` clean-up | Claude Code |
| 2026-10-26 | Hide the 8 internal root files from the deploy: `Website Feedback.pdf`, `Updated feedback.pdf`, `TomoClub Content Management & GitHub Publishing Guide new.pdf`, `images.json`, `podcast_data.json`, `patch_steps.txt`, `podcast_html.txt`, `newsletter_google_script.js` (none is linked or loaded by any page) | Rohith |
| 2026-10-26 | Orphan pages (no incoming links since at least 2026-09-29): archive `contact-form.html`, `schedule.html`, `waitlist-form.html` with 301 redirects to `/contact-us`, `/contact-us` and `/parents`. `build-with-us/thank-you.html` stays (the form needs it) and gets `noindex` | Rohith |
| 2026-10-26 | Phase G plan accepted | Rohith |
| 2026-10-26 | Found, not fixed: `generate_article_pages.py` does not compile since 2026-10-23, because `add_article.py` wrote a raw Windows cover path into it. Nothing runs that file (historical record). Logged in §9 | Claude Code |
| 2026-10-26 | `generate_article_pages.py` retired (deleted): one-off May 2026 migration script; re-running it would overwrite all 25 article pages. `add_article.py` no longer writes to it. Fixes the logged syntax-error item | Rohith |
| 2026-10-26 | `articles_data.js` retired (deleted) with `check_count.py`, `patch_piper.py`, `update_articles_images.py`: pop-up-era text store, loaded by no page, held 15 of 25 articles. `add_article.py` no longer writes to it | Rohith |
| 2026-10-26 | OK to push Phase G to the preview | Rohith |
| 2026-10-26 | Missing image on `/blog/ai-implementation-in-k12-schools` fixed: the "AI Readiness Pyramid" extracted from the source PDF (`articles/AI Implementation In K12.pdf`, page 2), saved as `blog/ai-implementation-in-k12-schools/ai-readiness-pyramid.webp` (34 KB). The PDF itself is not committed | Rohith |
| 2026-10-26 | All 4 graphics from the source PDF placed in `/blog/ai-implementation-in-k12-schools` at their PDF positions, with captions (add-blog image-block format) | Rohith |
| 2026-10-26 | Article source documents deleted: `articles/documents/Brad Jhonshon.pdf`, `Dave_Eastin.pdf`, `Wade_Stanford.pdf` (git history keeps them) and the uncommitted `articles/AI Implementation In K12.pdf` (moved to the Windows Recycle Bin) | Rohith |
| 2026-10-26 | Captions removed from the 4 post graphics: content must match the source document one-to-one, and the PDF has none | Rohith |
| 2026-10-26 | Hide `educational hall/` and `policy and terms/` (3 unlinked source PDFs) via `.vercelignore`; they stay in the repo | Rohith |
| 2026-10-26 | Phase G approved. Ebook PDF stays public at its direct URL (not gated) | Rohith |
| 2026-10-26 | Phase H plan accepted | Rohith |
| 2026-10-26 | Found: every page view is also sent to a second GA4 property, `G-TEEDDHTK84`, linked inside the Google tag settings for `G-FEGGQ2ZDMT` (not in site code). Production does the same today. Not a duplicate within one property; Rohith to confirm whether the second property is wanted | Claude Code |
| 2026-10-26 | Nav "Educational Hall" link no longer opens in a new tab (`target="_blank"` removed) | Claude Code |
| 2026-10-26 | Canonicals have no trailing slash (`https://www.tomoclub.org/ai-literacy`), matching `trailingSlash: false`; final style in Phase F | Claude Code |
| 2026-10-26 | `build_pages.py` reads CRLF or LF input and always writes LF (Git on Windows checks out CRLF) | Claude Code |

---

## Open questions

| # | Question | Raised in | Status |
|---|---|---|---|

---

## Document change log

| Date | File | Change |
|---|---|---|
| 2026-10-26 | `00-context.md`, `STATUS.md` | Created |
| 2026-10-26 | `01-refactor-plan.md` | Moved from repo root `seo-url-refactor-plan-2026-10-24.md` |
| 2026-10-26 | `baseline/search-console/` | Search Console export added; `SUMMARY.md` written |
| 2026-10-26 | `00-context.md` | Added Q1/Q2/Q3 decisions, host and canonical facts, Phase F and G scope |
| 2026-10-26 | `baseline/lighthouse.md`, `baseline/lighthouse/` | Lighthouse baseline (mobile + desktop) added |
| 2026-10-26 | `baseline/inventory.md`, `tools/seo-real-urls/inventory.py` | Inventory script and output added |
| 2026-10-26 | `00-context.md` | Added inventory facts to §4 and Phase E notes to §9 |
| 2026-10-26 | `STATUS.md`, `00-context.md` | Phase A closed; Phase B checklist and task spec (§11) added |
| 2026-10-26 | `02-layout-spec.md` | Created (draft, waiting for approval) |
| 2026-10-26 | `02-layout-spec.md` | Status set to approved |
| 2026-10-26 | `STATUS.md`, `00-context.md` | Phase B closed; Phase C checklist and task spec (§12) added; corrected `blog/` fact |
| 2026-10-26 | `02-layout-spec.md` | Added `cta.html` partial and `{{source}}` value |
| 2026-10-26 | `STATUS.md`, `00-context.md` | Phase C closed; Phase D checklist and task spec (§13) added |
| 2026-10-26 | `00-context.md` | Added open items: missing `android-chrome-*.png` icons, unused pilot and video modals |
| 2026-10-26 | `STATUS.md`, `00-context.md` | Phase D closed; Phase E checklist and task spec (§14) added |
| 2026-10-26 | `00-context.md` | Updated §9 open items after Phase E |
| 2026-10-26 | `STATUS.md`, `00-context.md` | Phase E closed; Phase F checklist and task spec (§15) added |
| 2026-10-26 | `03-episode-page-spec.md` | Created (draft, waiting for approval) |
| 2026-10-26 | `00-context.md` | Corrected thumbnail fact: all thumbnails match their own id |
| 2026-10-26 | `03-episode-page-spec.md` | Status set to approved |
| 2026-10-26 | `00-context.md` | Added open item: missing `blog pictures/` image |
| 2026-10-26 | `STATUS.md`, `00-context.md` | Phase F closed; Phase G checklist and task spec (§16) added |
| 2026-10-26 | `00-context.md` | §16 updated with the confirmed file list, orphan archive and redirects |
| 2026-10-26 | `00-context.md` | Added open item: `generate_article_pages.py` syntax error |
| 2026-10-26 | `STATUS.md`, `00-context.md` | Phase G closed; Phase H checklist and task spec (§17) added |
