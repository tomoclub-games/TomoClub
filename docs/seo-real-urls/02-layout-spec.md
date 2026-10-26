# Layout spec: partials and `build_pages.py`

Status: **draft, waiting for Rohith's approval.** No code is written before approval.

Phase B, step B2. Task spec: `00-context.md` §11.

---

## 1. Goal

Split `index.html` into shared partials plus one page file, and add a build script that joins them again. In Phase B the output must be **byte-identical** to today's `index.html`. Phase C adds one page file per route and reuses the same partials.

---

## 2. Folder layout

```
_partials/            shared fragments (not deployed)
  layout.html         the page skeleton: doctype, <html>, <head>, <body>, includes
  head.html           shared <head> content with {{vars}}
  nav.html            announcement banner + <nav>
  footer.html         <footer>
  modals.html         floating CTA, pilot, video, article and download modals
  scripts.html        closing <script> tags
pages/                one source file per output page (not deployed)
  index.html          front matter + body of today's index.html (all 11 route divs)
build_pages.py        repo root, next to the other generator scripts
index.html            generated output, committed (Vercel has no build step)
```

`_partials/` and `pages/` go in `.vercelignore`. They are never deployed, so Google can never index a fragment.

From Phase C: `pages/ai-literacy.html` builds to `ai-literacy/index.html`, and so on.

---

## 3. Partial boundaries in today's `index.html`

Line numbers are from `index.html` on 2026-10-26. The extraction cuts at these points exactly.

| Partial | Lines | Content |
|---|---|---|
| `head.html` | 4-214 | Everything inside `<head>`. Per-page values become `{{vars}}` (section 4) |
| `nav.html` | 217-284 | Announcement banner and `<nav>` |
| page body | 285-5704 | The 11 route divs, unchanged. Goes to `pages/index.html` |
| `footer.html` | 5705-5766 | `<!-- Footer -->` and `<footer>` |
| `modals.html` | 5767-6149 | Floating CTA, pilot, video, article and download modals |
| `scripts.html` | 6150-6153 | DOMPurify, Lucide, `script.js?v=23` |
| `layout.html` | 1-3, 215-216, 6154-6155 | Doctype, `<html>`, `<head>`/`</head>`, `<body>`/`</body>`, `</html>`, and the include lines |

The exact line breaks between pieces are kept, so the joined output matches byte for byte.

---

## 4. Shared and per-page `<head>` items

| Item | Today | In the partial |
|---|---|---|
| charset, viewport, author, favicons, theme-color | shared | literal |
| Google Fonts, GA tag, `styles.css`, inline `<style>`, `analytics.js` | shared | literal |
| `<title id="page-title">` | per page | `{{title}}` |
| `<meta name="description" id="meta-description">` | per page | `{{description}}` |
| `<meta name="keywords">` | per page | `{{keywords}}` |
| `<link rel="canonical" id="canonical-link">` | per page | `{{canonical}}` |
| `og:title`, `twitter:title` | per page | `{{title}}` |
| `og:description`, `twitter:description` | per page (shorter than meta description) | `{{social_description}}` |
| `og:image`, `twitter:image` | per page | `{{social_image}}` |
| JSON-LD `<script type="application/ld+json">` | per page | `{{block:head_jsonld}}` |

The `id="page-title"`, `id="meta-description"` and `id="canonical-link"` attributes stay for now. `script.js` uses them for `seoData`. Phase C deletes `seoData` and these ids.

Not changed in Phase B, because the output must stay identical. Logged for Phase C:

- Today's head has no `og:url`. Phase C adds `og:url` = `{{canonical}}`.
- Today's head has empty leftover `<!-- Open Graph / Facebook -->` and `<!-- Twitter -->` comments, two copies of the Google Fonts preconnect, and two font stylesheets. Phase C cleans these up.
- Asset paths are relative (`styles.css`, `assets/logo.webp`, `script.js`, `favicon-32x32.png`). They break on `/ai-literacy/`. Phase C changes them to root-absolute (`/styles.css`). This changes `index.html`, but not how it looks.

---

## 5. Page file format

Each `pages/*.html` file starts with a front-matter comment, then optional named blocks, then the body.

```html
<!--
output: index.html
title: AI Literacy & Future-Ready Skills for K–12 Schools | TomoClub Implementation Partner
description: TomoClub is the K–12 implementation partner for ...
keywords: AI Literacy, K-12 Education, ...
canonical: https://www.tomoclub.org/
social_description: TomoClub is the K–12 implementation partner for AI literacy and future-ready skills.
social_image: https://www.tomoclub.org/assets/og-image.jpg
-->
<!-- block:head_jsonld -->
    <script type="application/ld+json">
    ...
    </script>
<!-- endblock -->
    <!-- PAGE: HOME -->
    <div id="home" class="page active faded-in">
    ...
```

Rules:

- One `key: value` per line. The value is everything after the first `: `. Values are inserted as written, with no escaping, so they must already be valid HTML (`&` is fine; `"` is not allowed in values used inside attributes).
- `output` is required. It is the path of the file to write, relative to the repo root.
- Everything after the front matter and the blocks is the body. It goes where `layout.html` says `{{content}}`.

---

## 6. Template syntax

| Syntax | Meaning |
|---|---|
| `{{> name}}` | Insert `_partials/name.html` |
| `{{name}}` | Insert the front-matter value `name` |
| `{{block:name}}` | Insert the block `name` from the page file |
| `{{content}}` | Insert the page body |

Partials can include other partials. The build fails with a clear message, naming the page and the line, when:

- a partial does not exist;
- a `{{name}}` or `{{block:name}}` has no value in the page;
- a page has no `output`;
- a partial includes itself (directly or through another).

No conditionals and no loops. If a page needs something different, it gets its own value or block.

---

## 7. `build_pages.py`

- Python 3, standard library only. Run from the repo root: `py build_pages.py`.
- Builds every file in `pages/`. Writes UTF-8 with `\n` line endings and no BOM, the same as today's `index.html`.
- Prints one line per page written.
- `py build_pages.py --check` builds in memory and exits with code 1 if any output file differs from what is committed. Phase I and the add-* skills use it to catch hand edits to generated files.
- Each generated file starts with no extra banner comment in Phase B (output must stay identical). Phase C adds `<!-- Generated by build_pages.py from pages/<name>.html. Do not edit. -->` after the doctype.

---

## 8. Editing content after this change

Once `index.html` is generated, editing it by hand is wrong: the next build overwrites the edit.

- To change a page: edit `pages/<name>.html`, then run `py build_pages.py`.
- To change the navbar, footer or modals: edit the file in `_partials/`, then run `py build_pages.py`.
- The add-* skills and scripts (`add_article.py`, `add_blog_post.py`, `add_podcast_episode.py`) still edit `index.html` directly. They are updated in Phase E to edit `pages/` and run the build. Until then, do not run them on this branch.
- Content added to `index.html` on `main` during the project is copied into `pages/index.html` when `main` is merged into this branch.

---

## 9. Acceptance

1. `py build_pages.py` then `git diff index.html` shows no change.
2. `py build_pages.py --check` exits 0.
3. Changing one word in `_partials/footer.html` and rebuilding changes only that word in `index.html` (then revert).
4. `.vercelignore` lists `_partials/` and `pages/`.
5. A local browser check of `/` passes: navbar, dropdowns, theme toggle, mobile menu, route switching, modals, podcast player.
