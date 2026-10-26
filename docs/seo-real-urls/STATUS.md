# SEO Real URLs: Status

This is the single source of truth for progress. Claude Code reads it at the start of every session and updates it after every completed step.

**Last updated:** 2026-10-26 by Claude Code

---

## Current position

- **Current phase:** B. Shared layout
- **Current step:** B2
- **Waiting on:** Rohith: approve `02-layout-spec.md`
- **Next action:** on approval, extract partials (B3)

---

## Phases

Status values: `not started` · `in progress` · `waiting for review` · `approved` · `blocked`

| Phase | Status | Output | Approved by / date |
|---|---|---|---|
| A. Baseline | approved | `baseline/` folder, Q1 + Q2 + Q3 decided | Rohith, 2026-10-26 |
| B. Shared layout | in progress | `_partials/`, `build_pages.py` | |
| C. Split `index.html` | not started | `<route>/index.html` pages | |
| D. Remove router | not started | Router-free `script.js`, hash shim | |
| E. Rewrite links | not started | Zero route `#` links; updated generators and skills | |
| F. Vercel config | not started | Updated `vercel.json` | |
| G. Sitemap, robots, canonicals | not started | `build_sitemap.py`, new `sitemap.xml` | |
| H. Analytics | not started | GA + Clarity check | |
| I. Verify before merge | not started | Preview check report; merge | |
| J. After launch | not started | Search Console submission, monitoring notes | |

---

## Current phase checklist: B. Shared layout

Task spec: `00-context.md` section 11.

- [x] B1. Plan shown to Rohith and accepted
- [ ] B2. Layout spec `02-layout-spec.md` approved by Rohith (**no code before this**)
- [ ] B3. Partials extracted from `index.html` into `_partials/`; page body moved to `pages/`
- [ ] B4. `build_pages.py` written (stdlib only)
- [ ] B5. `py build_pages.py` regenerates `index.html` identical to the original (`git diff` empty)
- [ ] B6. `_partials/` and `pages/` added to `.vercelignore`; local browser smoke test of `/` passes
- [ ] B7. Summary given; phase set to `waiting for review`

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
