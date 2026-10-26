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
| `#blog` | `/blog` becomes a real page built from the `#blog` section. (Corrected 2026-10-26: `blog/index.html` is a redirect stub to `/#blog`, not a real page) |
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
- `education-hall/index.html`, `podcast/index.html` and `blog/index.html` are meta-refresh stubs to `/#...` (blog checked 2026-10-26).
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
- Done in Phase E: add-* skills point at `pages/`; `archive/` is excluded from the check because `.vercelignore` keeps it off the site.
- Rohith to decide: delete `add_brad_article.py` and `add_shane_article.py`? They are one-offs with paths to another computer (`c:\Users\JANMEJAY\...`) and cannot run here. Their links were fixed in Phase E.
- `pages/index.html` (home body) still uses relative asset paths (`assets/...`). They work because `/` is at the root. Make them root-absolute if the home body is ever reused elsewhere.
- After Phase C: consider moving other pages with their own navbar copy (`parents.html`, `leaders-of-tomorrow/`, articles, podcast pages, blog) onto the shared partials, so the navbar is edited in one place.
- `site.webmanifest` points to `/android-chrome-192x192.png` and `/android-chrome-512x512.png`, which do not exist. Every page logs a 404 for it. This is older than the project (since the initial commit). Fix in Phase I or separately.
- The pilot modal and the video modal in `_partials/modals.html` have no trigger on any page. Consider removing them to cut page weight (about 20 KB per page).
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

---

## 12. Task spec: Phase C

**Goal:** every route except `#home` gets its own real page at its own URL, built from the shared partials, with its own static SEO tags. `/` keeps working exactly as today until Phase D.

**Why `/` stays as it is in this phase:** old `/#pd` links rely on the hash router on `/`. Phase D slims `/` to the home section only, removes the router and adds the hash shim, all in one step. Splitting that work would leave old links broken in between.

**Inputs:** `pages/index.html` (11 route divs), `seoData` in `script.js` (titles and descriptions), the URL map in `01-refactor-plan.md`, decisions Q3 (www host).

**Steps:**

1. Update the partials (changes `index.html`, but not how it looks):
   - asset paths become root-absolute (`/styles.css`, `/script.js`, `/assets/...`, `/favicon-32x32.png`), so pages in subfolders load them;
   - add `og:url` = `{{canonical}}`;
   - remove the empty leftover OG/Twitter comments and the duplicate font preconnects;
   - add `<!-- Generated by build_pages.py from pages/<name>.html. Do not edit. -->` after the doctype;
   - nav and footer links point to the new URLs (`/ai-literacy`, `/professional-development`, ...; logo to `/`). Links inside page bodies are Phase E.
2. Router guard in `script.js`: run `navigateFromHash` only when the page has more than one `.page` div. On the new single-section pages it does nothing. `seoData` stays until Phase D, because `/` still uses it.
3. Create `pages/<route>.html` for the 10 routes. Body = that route's div, unchanged except its class becomes `page active faded-in` so it shows without the router. Front matter:
   - `title` and `description` from `seoData`;
   - `canonical` = `https://www.tomoclub.org/<route>` with no trailing slash (matches today's `trailingSlash: false`; final style is decided in Phase F);
   - `social_description` = `description`; `social_image` = today's `og-image.jpg`;
   - `keywords`: today's site keywords, trimmed to the page's topic.

   | Route | Output |
   |---|---|
   | `#ai-literacy` | `ai-literacy/index.html` |
   | `#future-ready` | `future-ready/index.html` |
   | `#pd` | `professional-development/index.html` |
   | `#guides` | `guides/index.html` |
   | `#education-hall` | `education-hall/index.html` (replaces stub) |
   | `#podcast` | `podcast/index.html` (replaces stub) |
   | `#results` | `results/index.html` |
   | `#faqs` | `faqs/index.html` |
   | `#about` | `about/index.html` |
   | `#blog` | `blog/index.html` (replaces stub) |

4. One `<h1>` per page. Only `#blog` lacks one: its "TomoClub Blog" `<h2>` becomes `<h1>` in `pages/blog.html` (same styling).
5. JSON-LD per page: `FAQPage` on `/faqs` built from the visible questions; `PodcastSeries` on `/podcast`; the matching `Service` on `/ai-literacy`, `/future-ready`, `/professional-development`. `/` keeps its current JSON-LD until Phase D.
6. Build and check locally with `py -m http.server`: every URL returns 200, has the right `<title>`, canonical and one `<h1>`; headless Chrome screenshots at desktop and mobile width for each page; `/` and its `#` links still work; `py build_pages.py --check` passes.
7. Summary given; phase set to `waiting for review`.

**Output:** 10 new `pages/*.html`, 10 generated `<route>/index.html`, updated partials, router guard in `script.js`.

**Changed from the original plan (`01-refactor-plan.md` §2):**

- Deleting `seoData` moves to Phase D, with the router.
- "Load only the JS each page needs": no per-page data scripts exist, and every feature in `script.js` (636 lines) already checks that its elements exist. All pages keep the one shared `script.js`. The size win comes from each page carrying only its own section.

**Known gaps until later phases:** links inside page bodies still use `#` routes (Phase E). On a new page, such a link goes to `/<route>#x` and does nothing until Phase E rewrites it. The branch is not deployed to production before Phase I.

---

## 13. Task spec: Phase D

**Goal:** `/` becomes a normal single page with only the home section. The hash router and the `.page` show/hide system are removed. Old `/#route` links keep working through a small shim.

**Inputs:** Phase C pages; `script.js` router (`navigateFromHash`, `seoData`); `.page` CSS in `styles.css` (lines ~1032-1047 and the print rule ~1706); `.nav-item.active` CSS already exists.

**Steps:**

1. Slim `pages/index.html` to the home section. `/` JSON-LD keeps `Organization` and `WebSite`. `Service` and `FAQPage` are dropped there, because they now live on the program pages and `/faqs`, where the content is visible. The `WebSite` `SearchAction` is dropped too: the site has no search page, so `/?s=` is not a real search URL.
2. Remove the router: `seoData`, `navigateFromHash` and its listener in `script.js`; the `.page`, `.page.active`, `.page.faded-in` rules in `styles.css`; the `page active faded-in` classes on the page wrappers; the `id="page-title"`, `id="meta-description"`, `id="canonical-link"` attributes in `_partials/head.html`. The wrapper `<div id="<route>">` stays, so in-page anchors to it still work.
3. Hash shim in `_partials/head.html`, on every page, inline and before any rendering:
   - map: `#home` to `/`, `#ai-literacy`, `#future-ready`, `#pd` to `/professional-development`, `#guides`, `#education-hall`, `#podcast`, `#results`, `#faqs`, `#about`, `#blog`, `#ebook` to `/leaders-of-tomorrow`;
   - runs on load and on `hashchange`, using `location.replace` so the old URL does not stay in history;
   - does nothing when the target is the current page (so `/faqs#faqs` does not reload);
   - ignores every other hash (`#signup`, `#programs`, ...).
   Running it on every page also makes the remaining `#route` links inside page bodies work until Phase E rewrites them.
4. Nav current state: add `active` to the `.nav-item` whose link (or dropdown link) matches `location.pathname`, and `aria-current="page"` to that link.
5. Local check with `py -m http.server`: all 11 pages render with content visible; scroll animations, FAQ accordion, article and podcast filters, toolkit download modal, pilot modal, video modal, theme toggle and mobile menu work; each old `/#route` lands on its page; `/#signup` stays on `/`; record the new `/` size; `py build_pages.py --check` passes.
6. Summary given; phase set to `waiting for review`.

**Behaviour change to note:** today the browser title of `/` is set by JavaScript from `seoData` ("AI Literacy and Future-Ready Skills for K–12 Schools | TomoClub"). After this phase, the static title in the HTML is used ("AI Literacy & Future-Ready Skills for K–12 Schools | TomoClub Implementation Partner"). The static one is what Google indexes today, so search results do not change.

---

## 14. Task spec: Phase E

**Goal:** no route-style `#` link is left in anything that is deployed or that generates deployed pages. New content added by the add-* skills lands in `pages/` and is built, with real URLs.

**Inputs:** `inventory.py` (889 links in 160 files after Phase D): 45 blog posts, 25 articles, 70 podcast pages, 7 root files, `build-with-us/`, `leaders-of-tomorrow/`, `education-hall/`, `api/signup.js`, 7 generator scripts, 3 skills. Phase A open items (§9) on skills, `archive/` and one-off scripts.

**Link map** (same as the hash shim): `#home` to `/`; `#pd` to `/professional-development`; `#ebook` to `/leaders-of-tomorrow`; every other route `#x` to `/x`. Forms handled: `#x`, `/#x`, `../#x`, `../../#x`, `index.html#x`, `../index.html#x`, `https://(www.)tomoclub.org/#x` and `tomoclub.org#x`. Absolute links become `https://www.tomoclub.org/x`; all others become root-relative `/x`.

**Steps:**

1. Write `tools/seo-real-urls/rewrite_links.py`, reusing the patterns in `inventory.py`. Dry run by default; `--apply` writes. It skips generated files (it edits `pages/` and rebuilds instead), `archive/` (not deployed), `docs/` and `tools/`. A bare `#x` in a file that also has an element with `id="x"` might be an in-page anchor: the script lists these for review instead of changing them.
2. Apply to source HTML and `api/signup.js`. Run `py build_pages.py`.
3. Change apex `https://tomoclub.org/...` links to `https://www.tomoclub.org/...` (4 files).
4. Generators:
   - all 7 scripts (`add_article.py`, `add_blog_post.py`, `add_podcast_episode.py`, `generate_article_pages.py`, `fix_podcast_player.py`, `add_brad_article.py`, `add_shane_article.py`): link templates use real URLs;
   - `add_article.py` adds its card to `#articles-grid` in `pages/education-hall.html`; `add_blog_post.py` to the `#blog` grid in `pages/blog.html`; `add_podcast_episode.py` to `#podcast-grid` in `pages/podcast.html`. Card URLs are root-absolute (`/articles/<slug>/`). Each then runs `build_pages.py`.
   - `add_brad_article.py` and `add_shane_article.py` are one-offs with hard-coded paths to another computer (`c:\Users\JANMEJAY\...`). Only their links are fixed; deleting them is Rohith's call (logged in §9).
5. Skills: update file paths, section names (for example "top of `#blog`'s `grid-3` in `index.html`" becomes `pages/blog.html`), preview URLs (`http://localhost:8000/education-hall`) and add the build step.
6. Test each add-* script in a throwaway `git worktree` with sample input; check the card lands in the right `pages/` file, the build runs, and `inventory.py --check` stays at zero. Remove the worktree.
7. `inventory.py --check` excludes `archive/` and `sitemap.xml` (rebuilt in Phase G) and must report zero. `build_pages.py --check` passes. Crawl the 11 main pages locally; every internal link resolves.
8. Summary given; phase set to `waiting for review`.

**Not in this phase:** podcast cards still link to `podcast-player.html?id=X`. Phase F creates the missing `podcast-<id>/` pages, adds the redirect, and then points the cards at `/podcast-<id>`.
