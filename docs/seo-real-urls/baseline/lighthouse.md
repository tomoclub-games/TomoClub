# Lighthouse baseline

Run on 2026-10-26 against production `https://www.tomoclub.org/` with `lighthouse@12.6.0` and local Chrome, headless. Full reports are in `lighthouse/` (`.report.html` opens in a browser).

Command (mobile is the default; desktop adds `--preset=desktop`):

```
npx -y lighthouse@12.6.0 https://www.tomoclub.org/ --only-categories=performance,seo,accessibility,best-practices --output=json --output=html --output-path=docs/seo-real-urls/baseline/lighthouse/home-mobile --chrome-flags="--headless=new"
```

## Scores

| Category | Mobile | Desktop |
|---|---|---|
| Performance | 63 | 92 |
| Accessibility | 90 | 90 |
| Best practices | 75 | 74 |
| SEO | 100 | 100 |

## Metrics

| Metric | Mobile | Desktop |
|---|---|---|
| First Contentful Paint | 2.9 s | 0.9 s |
| Largest Contentful Paint | 11.4 s | 1.5 s |
| Total Blocking Time | 130 ms | 0 ms |
| Cumulative Layout Shift | 0 | 0 |
| Speed Index | 6.5 s | 1.7 s |
| Total transfer size | 1,573 KiB | 5,490 KiB |
| DOM elements | 5,215 | 5,215 |

## Notes

- Each number is a single run. Performance can vary by about ±5 points between runs. Phase I should run the same command 3 times and compare the median.
- SEO is already 100. Lighthouse SEO checks only basic tags on the one URL it loads, so it does not see the hash-route problem. Judge the project's SEO result by Search Console, not by this score.
- The numbers to beat are mobile LCP (11.4 s) and DOM size (5,215 elements). Both come from all 11 routes living in one `index.html`. Phase C should cut both on `/`.
