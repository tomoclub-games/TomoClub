# SEO Real URLs: Status

This is the single source of truth for progress. Claude Code reads it at the start of every session and updates it after every completed step.

**Last updated:** 2026-10-26 by Claude Code

---

## Current position

- **Current phase:** E. Rewrite links
- **Current step:** E9 done; phase waiting for review
- **Waiting on:** Rohith: review and approve Phase E; decide whether to delete `add_brad_article.py` and `add_shane_article.py`
- **Next action:** on approval, commit Phase E and run `seo-next` to start Phase F (Vercel config)

---

## Phases

Status values: `not started` · `in progress` · `waiting for review` · `approved` · `blocked`

| Phase | Status | Output | Approved by / date |
|---|---|---|---|
| A. Baseline | approved | `baseline/` folder, Q1 + Q2 + Q3 decided | Rohith, 2026-10-26 |
| B. Shared layout | approved | `_partials/`, `build_pages.py` | Rohith, 2026-10-26 |
| C. Split `index.html` | approved | `<route>/index.html` pages | Rohith, 2026-10-26 |
| D. Remove router | approved | Router-free `script.js`, hash shim | Rohith, 2026-10-26 |
| E. Rewrite links | waiting for review | Zero route `#` links; updated generators and skills | |
| F. Vercel config | not started | Updated `vercel.json` | |
| G. Sitemap, robots, canonicals | not started | `build_sitemap.py`, new `sitemap.xml` | |
| H. Analytics | not started | GA + Clarity check | |
| I. Verify before merge | not started | Preview check report; merge | |
| J. After launch | not started | Search Console submission, monitoring notes | |

---

## Current phase checklist: E. Rewrite links

Task spec: `00-context.md` section 14.

- [x] E1. Plan shown to Rohith and accepted
- [x] E2. `tools/seo-real-urls/rewrite_links.py` written; dry run reviewed. Bare `#x` is only rewritten inside `href=` (the hash shim's JS map is left alone); `.md` files only under `.claude/skills/`; `images.json` skipped (not UTF-8, no links). No links flagged for review
- [x] E3. 859 links rewritten in 157 files (source HTML, `api/signup.js`, generator templates, skills); generated pages rebuilt
- [x] E4. Apex `https://tomoclub.org/...` links changed to `https://www.tomoclub.org/...` (Q3)
- [x] E5. Generators updated: link templates in all 7 scripts; `add_article.py`, `add_blog_post.py`, `add_podcast_episode.py` edit `pages/<route>.html` with root-absolute card URLs and run `build_pages.py`. Also fixed `add_article.py`'s grid marker, broken since commit `f4262c4` (2026-10-23, before this project)
- [x] E6. Skills `add-article`, `add-blog`, `add-podcast` updated (files, sections, preview URLs, build step)
- [x] E7. Each add-* script tested in a throwaway git worktree (podcast YouTube fetch stubbed): card lands in the right `pages/` file and position (article last, blog and podcast first), build runs, no `#` links emitted; worktree removed
- [x] E8. `inventory.py --check` reports zero (excluding `archive/` and `sitemap.xml`); `build_pages.py --check` passes; 219 internal URLs on the 11 main pages all resolve locally (after the `/guides` toolkit fix below)
- [x] E9. Summary given; phase set to `waiting for review`

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
