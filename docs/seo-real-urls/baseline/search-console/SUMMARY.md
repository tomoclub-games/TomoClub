# Search Console baseline

Exported by Rohith on 2026-10-26. Raw CSVs are in `performance/` and `indexing/`.

## Headline numbers

| Metric | Value | Period |
|---|---|---|
| Indexed pages | 139 | as of 2026-10-12 |
| Not indexed pages | 462 | as of 2026-10-12 (down from 630 in Aug) |
| Clicks | 545 | 2026-07-25 to 2026-10-12 (80 days) |
| Impressions | 18,437 | same |
| Queries with impressions | about 540 | same |
| Pages with impressions | 165 | same |
| Desktop / mobile clicks | 310 / 232 | same |
| Desktop / mobile avg position | 16.1 / 8.5 | same |

## Why pages are not indexed

| Reason | Pages |
|---|---|
| Not found (404) | 195 |
| Page with redirect | 122 |
| Duplicate without user-selected canonical | 91 |
| Crawled, currently not indexed | 18 |
| Blocked due to access forbidden (403) | 17 |
| Discovered, currently not indexed | 7 |
| Alternative page with proper canonical tag | 6 |
| Excluded by `noindex` | 5 |
| Other 4xx | 1 |

## Top pages by clicks

| Page | Clicks | Impressions | Position |
|---|---|---|---|
| `/` | 338 | 4,011 | 6.5 |
| `/articles/serve-first-how-dr-ronnie-tarchichi-rebuilds-school-districts` | 23 | 516 | 6.2 |
| `/blog/school-cell-phone-bans-2026-parents-guide` | 15 | 773 | 9.0 |
| `/articles/piper-bognar-van-dyke-leadership` | 13 | 357 | 6.9 |
| `/leaders-of-tomorrow` | 11 | 735 | 14.1 |

Branded queries (`tomoclub`, `tomo club`) give 253 of the 545 clicks (46%).

## Findings that affect later phases

1. **Hash routes count as `/`.** `/#blog`, `/#education-hall`, `/#guides` and `/#podcast` all show the same 270 impressions at position 3.41. Google shows them only as sitelinks of the homepage, not as their own pages. This is the problem the project fixes.
2. **www vs apex host.** Most URLs use `https://www.tomoclub.org/`, but 5 pages also appear on `https://tomoclub.org/`. Example: `/` gets 4,011 impressions on www and 839 on apex. Phase F and I: make sure the apex host 301-redirects to www and that every canonical uses www.
3. **Trailing-slash duplicates.** Some pages appear both with and without `/` at the end. Example: the Tarchichi article. Phase F: pick one style (open decision in plan §5).
4. **`podcast-player.html?id=...` URLs get impressions.** They duplicate the `podcast-<id>/` pages. Phase F or G: canonical or redirect them to the episode page.
5. **195 URLs return 404 and 122 redirect.** Phase I link check should list which of these are old internal links we can fix.
