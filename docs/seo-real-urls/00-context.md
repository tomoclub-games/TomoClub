# SEO Real URLs: Project Context for Claude Code

This file holds the full context of SEO Real URLs. Read it before you do any work on this project.

**Files in this folder (`docs/seo-real-urls/`):**

| File | Content | Status |
|---|---|---|
| `00-context.md` (this file) | Goal, decisions, architecture, plan, task specs | Current |
| `STATUS.md` | Current phase and step, checklist, decision log, open questions, change log | Updated after every step |
| `01-refactor-plan.md` | Original refactor plan (2026-10-24): problem, target URL map, detailed phase notes | Reference. Phase details below point to its sections |

---

## 1. Goal

Replace the `#` hash routes in `index.html` with real, crawlable URLs (`/ai-literacy`, `/podcast`, etc.), each with its own static title, meta, canonical and structured data. Old `/#x` links must keep working, and the sitemap must list every real page.

---

## 2. Key principles

1. Vercel stays a static host with no build step. Generated HTML is committed.
2. Old links never break. Every old `/#route` lands on its new page.
3. In-page anchors (`#signup`, `#programs`) are not routes. Leave them alone.
4. No visual or behavioural change to pages, except the URL. Navbar, modals, forms, podcast player and animations work as before.
5. Measure before and after. Phase A records the baseline; Phase I compares against it.
6. Work happens on branch `seo-real-urls`. Merge to `main` only after Phase I passes on a Vercel preview.

---

## 3. Decisions made

Stable decisions that shape the design. The dated history is the decision log in `STATUS.md`.

| Decision | Detail |
|---|---|
| URL map | As in `01-refactor-plan.md` "Target URL map" |
| `#pd` | Becomes `/professional-development`. `/pd` 301-redirects to it in `vercel.json` |
| `#ebook` | Merges into existing `/leaders-of-tomorrow`. Section and `seoData` entry already removed from `index.html` / `script.js` (staged on this branch) |
| `#blog` | Uses existing `blog/index.html`. Duplicate section in `index.html` is removed |
| Shared layout | `build_pages.py` combines `_partials/` with page bodies. Not hand-copied (Q2, 2026-10-26) |
| Canonical host | `https://www.tomoclub.org`. All canonicals, sitemap entries and internal absolute links use it (Q3, 2026-10-26) |
| Podcast URLs | Keep `podcast-<id>/`. No move to `/podcast/<slug>`. `podcast-player.html?id=X` 301-redirects to `/podcast-X`; missing episode pages are created first (Q1, 2026-10-26) |
| Old-link handling | A JS shim on `/` maps `location.hash` to the new path. Server 301 is impossible because fragments never reach the server |

---

## 4. Domain facts

Checked against the code on 2026-10-24 (plan author) unless marked.

- `index.html` is ~594 KB and holds 12 `.page` divs toggled by `navigateFromHash` in `script.js` (~lines 71-121).
- `seoData` in `script.js` sets per-page title/meta at runtime.
- `sitemap.xml` has 15 entries, 7 of them `#` URLs. Missing: ~45 blog posts, ~70 podcast pages, `/parents`.
- `education-hall/index.html` and `podcast/index.html` are meta-refresh stubs to `/#...`.
- ~140 HTML files link to route-style `#` URLs.
- Generators that emit `#` links: `add_article.py`, `add_blog_post.py`, `add_podcast_episode.py`, `generate_article_pages.py`, `fix_podcast_player.py`. Skills: `.claude/skills/add-article`, `add-blog`, `add-podcast`.
- `vercel.json` (checked 2026-10-26): `cleanUrls: false`, `trailingSlash: false`, manual `rewrites` list. `ignoreCommand` skips deploys only for `.claude`-only changes, so `docs/` commits trigger a preview build.
- `analytics.js` sends `location.pathname`.
- Hosts (checked 2026-10-26 with `curl -I`): `https://tomoclub.org/` 308-redirects to `https://www.tomoclub.org/`; `http://` 308-redirects to `https://`. All 15 sitemap URLs and all existing canonicals use `www`.
- Only 5 HTML files have a `rel="canonical"` tag (`index.html`, `parents.html`, `leaders-of-tomorrow/`, `taicy/`, `archive/parents-legacy.html`). Articles, blog posts and podcast pages have none. This matches the 91 "Duplicate without user-selected canonical" pages in Search Console.
- `podcast-player.html` has no canonical or `noindex`. Of the 24 player URLs with Search Console impressions, 16 have a matching `podcast-<id>/` page and 8 do not.
- Inventory (2026-10-26, `baseline/inventory.md`): `index.html` is 571 KB with 11 route divs (`#ebook` already gone). `#podcast` alone is ~200 KB and `#blog` ~95 KB. There are 903 route-style `#` links in 162 files. 145 indexable pages are missing from the sitemap: 70 podcast, 45 blog, 19 articles, 11 other.
- 4 HTML files link to `https://tomoclub.org/...` (apex) instead of www: `build-with-us/index.html`, `build-with-us/thank-you.html`, and 2 blog posts.

---

## 5. Architecture

Target state:

- `_partials/` holds shared `<head>` boilerplate, navbar, footer and modals (if Open question 2 picks the build script).
- `pages/<route>.html` holds each page body.
- `build_pages.py` combines partials and bodies into `<route>/index.html`. Output is committed.
- `build_sitemap.py` scans real pages and writes `sitemap.xml`. The add-* scripts call it.
- `script.js` has no router. Nav "current" state comes from `location.pathname`. A small hash shim on `/` redirects old links.

Terms: **route** = one of the 12 old `#` pages. **anchor** = an in-page `#id` that is not a route.

---

## 6. The plan

Phase letters map to the numbered sections of `01-refactor-plan.md` (A = §0, B = §1, ...). Read that section for the detailed steps.

| Phase | What | Exit check |
|---|---|---|
| A. Baseline (§0) | Branch, Search Console snapshot, Lighthouse baseline, inventory of routes/links/sitemap. No site code changes | Baseline files saved in `docs/seo-real-urls/baseline/`; layout decision (Q2) made |
| B. Shared layout (§1) | Extract head/navbar/footer/modals into partials; write `build_pages.py` | Rebuilding `/` from partials gives a page that looks and behaves the same as today |
| C. Split `index.html` (§2) | One `<route>/index.html` per route with static title, meta, canonical, OG, one `<h1>`, JSON-LD; replace redirect stubs; per-page JS | Every route URL serves its own page locally; `seoData` deleted; `/` well below 594 KB |
| D. Remove router (§3) | Delete hash routing and `.page` toggling; nav state from pathname; hash shim on `/` | No `navigateFromHash`; `/#pd` etc. land on new pages; animations work |
| E. Rewrite links (§4) | Script rewrites route `#` links in all HTML; update generators and add-* skills | grep finds zero route-style `#` links |
| F. Vercel config (§5) | `cleanUrls: true`, drop manual rewrites, `/pd` 301, settle trailing slash; create missing `podcast-<id>/` pages, then 301 `podcast-player.html?id=X` to `/podcast-X` | Local `vercel dev` or preview serves all URLs with one slash style; every player URL lands on an episode page |
| G. Sitemap, robots, canonicals (§6) | `build_sitemap.py`, hooked into add-* scripts; robots.txt check; self-referencing canonical on every article, blog post and podcast page (generators updated too) | Sitemap lists every real page, no `#` URLs, no scratch/archive; every indexable page has one canonical |
| H. Analytics (§7) | Confirm GA and Clarity fire per real URL | Page_view events seen per path on the preview |
| I. Verify before merge (§8) | 200s, titles, canonicals, link check, old-link shim, Lighthouse vs baseline, visual pass desktop + mobile | All checks pass on the Vercel preview; Rohith approves merge |
| J. After launch (§9) | Submit sitemap, request indexing, update external `/#` links, watch coverage 2-4 weeks | Search Console shows new URLs indexed, no coverage errors spike |

### Kill criteria

- Phase B cannot rebuild `/` identically from partials without a build step on Vercel: stop and revisit the layout decision.
- Phase I Lighthouse SEO or performance on `/` is worse than baseline and the cause is not fixable: do not merge.
- Search Console shows a large drop in indexed pages or clicks within 2 weeks of launch: investigate before further changes; consider rollback.

---

## 7. Current status

Progress, the current step, the decision log and open questions are in **`STATUS.md`**. Read it at the start of every session. Do not track status in this file.

---

## 8. Working agreement

- Read `STATUS.md` at the start of every session.
- After every completed step, run the `seo-checkpoint` skill (update STATUS.md, log decisions, update other docs if needed).
- When Rohith approves a phase, run the `seo-next` skill. New task specs are added to this file as "Task spec: Phase X".
- Never mark a phase as approved yourself.
- Use plan mode for each phase. Show the plan before you implement.
- Ask Rohith when intent, thresholds or schema choices are not clear. Do not guess.
- Put docs in `docs/seo-real-urls/` and scripts in `tools/seo-real-urls/`. Exception: `build_pages.py` and `build_sitemap.py` go at the repo root next to the other generators, because the add-* scripts call them.
- Approve specs before code: a schema, catalog or design doc is approved before its implementation starts.
- After each phase, give a short summary: what was done, what is uncertain, what is next.
- Write docs in simple, clear technical English: short sentences, active voice, one idea per sentence.

---

## 9. Open items (not for the current phase, but do not forget)

- Update external `/#...` links (LinkedIn, newsletters, email signatures) in Phase J.
- Phase E: the add-* skills also refer to sections by id (for example "top of `#blog`'s `grid-3`"). The inventory does not count these as links, so update them by hand when the sections move to `pages/`.
- Phase E: decide whether to rewrite links in `archive/` too (16 links in `archive/parents-legacy.html`) or exclude `archive/` from the `--check`.
- Phase E: one-off scripts (`add_brad_article.py`, `add_shane_article.py`) contain route links. Decide whether to update or delete them.
- After Phase C: consider moving other pages with their own navbar copy (`parents.html`, `leaders-of-tomorrow/`, articles, podcast pages, blog) onto the shared partials, so the navbar is edited in one place.
- Consider adding `docs/` to the Vercel `ignoreCommand` so doc-only commits skip deploys.

---

## 10. Task spec: Phase A

**Goal:** record where the site stands before any change, so Phase I can compare. Settle the decision that blocks Phase B.

**No site code changes in this phase.** The staged `#ebook` removal in `index.html` / `script.js` was done before setup and is already decided.

**Steps:**

1. Create branch `seo-real-urls` and carry the staged changes over. (Done at setup.)
2. Search Console snapshot. Rohith exports: indexed pages count, the Pages report, and top 50 queries and pages (last 3 months). Save to `docs/seo-real-urls/baseline/search-console/`.
3. Lighthouse baseline. Run Lighthouse (SEO + performance, mobile and desktop) on production `https://tomoclub.org/`. Save JSON and a summary table to `docs/seo-real-urls/baseline/lighthouse.md`.
4. Inventory. Write a script in `tools/seo-real-urls/inventory.py` that records:
   - the 12 routes and their `.page` div sizes in `index.html`;
   - every route-style `#` link, by file (the list Phase E must reach zero);
   - current `sitemap.xml` entries and the real pages missing from it;
   - every generator and skill that emits `#` links.
   Save the output to `docs/seo-real-urls/baseline/inventory.md`.
5. Decisions: Rohith answers Q1 (podcast URL move now or later) and Q2 (build script vs hand-copied layout). Q2 blocks Phase B.
6. Summary given; phase set to `waiting for review`.

**Output:** `docs/seo-real-urls/baseline/` with Search Console export, Lighthouse results, inventory; Q1 and Q2 logged as decisions.

---

## 11. Task spec: Phase B

**Goal:** move the shared parts of `index.html` (head boilerplate, banner and navbar, footer, modals, closing scripts) into partials, and add `build_pages.py`, which rebuilds `index.html` from them. Phase C then uses the same partials for every new route page.

**No visible change in this phase.** The rebuilt `index.html` must be byte-identical to the current one. Nav links stay `#` routes until Phase D/E.

**Inputs:** `index.html` structure (checked 2026-10-26): `<head>` lines 3-215 (meta, JSON-LD, fonts, GA, `styles.css`, an inline `<style>`, duplicated OG/Twitter blocks, `analytics.js`); banner and `<nav>` lines 217-284; 11 route divs lines 286-5704; `<footer>` lines 5706-5766; 4 modals (`pilot-modal`, `video-modal`, `article-modal`, `download-modal`) lines 5768-6149; scripts lines 6150-6153.

**Steps:**

1. Write `docs/seo-real-urls/02-layout-spec.md` for Rohith to approve. It defines:
   - the partial files and their exact boundaries in `index.html`;
   - which `<head>` items are shared and which are per page (title, description, canonical, OG/Twitter, JSON-LD);
   - the template syntax: `{{> partial}}` includes and `{{var}}` values, with per-page values in a front-matter comment at the top of each `pages/*.html` file;
   - the folder layout: `_partials/`, `pages/`, `build_pages.py` at the repo root, output `<route>/index.html` (only `index.html` in this phase);
   - how the add-* skills and scripts must work once `index.html` is generated (they edit `pages/`, then run the build). They are updated in Phase E; until then, nobody runs them on this branch.
   **No code before Rohith approves the spec.**
2. Extract the partials into `_partials/` and move the body (all 11 route divs, unchanged) into `pages/index.html` with its front matter.
3. Write `build_pages.py`: Python stdlib only, no Vercel build step. Fails loudly on an unknown partial or a missing value.
4. Run `py build_pages.py` and confirm `git diff index.html` is empty.
5. Add `_partials/` and `pages/` to `.vercelignore` so the source fragments are never deployed or indexed. Smoke test `/` in a local browser: navbar, dropdowns, theme toggle, mobile menu, route switching, modals, podcast player.
6. Summary given; phase set to `waiting for review`.

**Output:** `02-layout-spec.md` (approved), `_partials/`, `pages/index.html`, `build_pages.py`, updated `.vercelignore`, unchanged `index.html`.

**Risks:**

- Content added to `index.html` on `main` during the project (new articles, podcasts, blog posts) will not reach this branch automatically. Each merge from `main` must move those edits into `pages/` and rebuild. The build script makes this a copy, not a rewrite.
- Other pages (`parents.html`, `leaders-of-tomorrow/`, articles, podcast pages) have their own navbar copies. Moving them onto the partials is out of scope for Phase B; logged in §9.
