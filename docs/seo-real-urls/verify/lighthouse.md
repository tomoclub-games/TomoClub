# Lighthouse: preview vs baseline

Run on 2026-10-26 against the Vercel preview `tomoclub-website-9cteh9t13` (branch `seo-real-urls`) with Lighthouse 12.6.0, the same version as the Phase A baseline. Chrome reused a profile holding Vercel's bypass cookie; the HTTP cache was cleared before every run. Raw numbers: `lighthouse-summary.json`.

## Home page `/` (median of 3 runs)

| Metric | Baseline mobile (production, Phase A) | Preview mobile | Baseline desktop | Preview desktop |
|---|---|---|---|---|
| Performance | 63 | **73** | 92 | **99** |
| Accessibility | 90 | 90 | 90 | 90 |
| Best practices | 75 | 75 | 74 | 74 |
| SEO | 100 | 69 (see note) | 100 | 69 (see note) |
| Largest Contentful Paint | 11.4 s | **4.8 s** | 1.5 s | **0.8 s** |
| First Contentful Paint | 2.9 s | 2.7 s | 0.9 s | 0.6 s |
| Total Blocking Time | 130 ms | 206 ms | 0 ms | 0 ms |
| DOM elements | 5,215 | **729** | 5,215 | **729** |
| Transfer size | 1,573 KiB | 1,266 KiB | 5,490 KiB | 5,169 KiB |

Mobile runs: performance 73, 77, 70; LCP 5.9 s, 4.4 s, 4.8 s.

**SEO note:** every preview page fails exactly one SEO check, `is-crawlable`, because Vercel adds `X-Robots-Tag: noindex` to all preview deployments. Production does not send this header. No other SEO check fails, so production pages should score 100.

## Other pages (single run each)

| Page | Mobile perf | Mobile LCP | Desktop perf | DOM |
|---|---|---|---|---|
| `/ai-literacy` | 86 | 3.4 s | 100 | 735 |
| `/future-ready` | 93 | 2.9 s | 98 | 542 |
| `/professional-development` | 85 | 3.6 s | 99 | 698 |
| `/guides` | 85 | 3.8 s | 99 | 353 |
| `/education-hall` | 90 | 3.2 s | 98 | 572 |
| `/podcast` | 74 | 7.4 s | 97 | 2,136 |
| `/results` | 87 | 3.6 s | 99 | 491 |
| `/faqs` | 85 | 3.7 s | 99 | 378 |
| `/about` | 83 | 4.0 s | 99 | 735 |
| `/blog` | 76 | 6.4 s | 95 | 787 |
| `/articles/jeff-court-leadership` | 56 | 10.9 s | 99 | 109 |
| `/blog/ai-implementation-in-k12-schools` | 92 | 2.8 s | 100 | 127 |
| `/podcast-WH0IP_TGK4Q` | 88 | 3.4 s | 99 | 344 |

Before this project, all of the first 10 pages were the same 5,215-element home page.

**Article page:** `/articles/jeff-court-leadership` is slow on mobile. Production scores the same or worse (2 runs: performance 55, LCP 21.7 s), so this is not a regression. The article template loads about 3 MB, mostly third-party scripts (several Google tag containers). Logged as an open item.

## Production after merge (2026-10-26)

Same method (Lighthouse 12.6.0, cache cleared before each run), 3 runs each, mobile:

| Page | Runs | Median | LCP median |
|---|---|---|---|
| `/` | 69, 74, 88 | 74 | 7.6 s |
| `/ai-literacy` | 83, 85, 88 | 85 | 3.7 s |

SEO is 100 on `/`, `/ai-literacy` and `/podcast-WH0IP_TGK4Q` (production sends no `X-Robots-Tag`). `/` varies a lot between runs; compare medians. Single CLI runs straight after the deploy, before Vercel's edge cache was warm, scored lower (65 and 58) and are not used.
