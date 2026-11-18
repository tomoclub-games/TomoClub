# B2C parents site, archived 18 Nov 2026

TomoClub is B2B only from 17 Nov 2026 (decisions log). The parents pages and their booking code moved here
unchanged so they can be restored. `archive/` is listed in `.vercelignore`, so nothing here is deployed.

| Was | Now |
|---|---|
| `index.html` (parents home page) | `pages/home-parents.html` |
| `ai-lab/`, `life-skills/`, `both-programs/` | `pages/...` |
| `assets/js/parents-site.js` | `parents-site.js` |
| `api/book.js`, `api/slots.js`, `api/collect.js`, `api/geo.js` | `api/` |

The old URLs 301-redirect to `/` (see `vercel.json`). Images in `assets/parents/` stay because the new home page
uses the partner school logos from that folder.

Vercel env vars only these functions used (safe to remove once you are sure): `CALENDLY_EVENT_TYPE_URI`,
`CALENDLY_LOCATION_KIND`. Keep `CALENDLY_TOKEN` and `SHEET_WEBHOOK`: the B2B lead API uses them.
