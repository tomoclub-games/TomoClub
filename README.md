# AI School District Parent & Policy Assistant

A TomoClub Build With Us prototype. Enter a US school district website. The app reads the district's public pages and PDFs, then answers questions from parents and staff using only that district's content, with a link to the exact page or PDF page for every fact. A lead form ("Request a Demo") stores requests for the TomoClub team.

**Status (23 Nov 2026):** built and passing 34 automated end-to-end checks against two fictional test district sites. It has **not** yet been run against a real district website or the real Claude API, because the build environment blocks outside websites and has no API key. See "Before showing it to a superintendent" below.

## Flow

Enter district URL → read robots.txt and sitemap → read up to 40 relevant pages and 15 PDFs → extract text (PDF page numbers kept) → index → ask → search this district's index only → Claude answers from the retrieved passages with [n] citations → answer shown with clickable sources → Request a Demo.

## What works and what needs setup

| Feature | Status |
| --- | --- |
| Website reading: robots.txt respected, sitemap plus link discovery, priority on handbooks, calendars, attendance, enrollment, transportation, policies, FAQs | Working (tested on fixture sites) |
| PDF text extraction with page numbers, from the site or uploaded | Working (tested) |
| Clear "not read" list with reasons: robots.txt block, HTTP errors, JavaScript-only pages, scanned PDFs, Google Drive or BoardDocs links, oversized files | Working (tested) |
| District name, website, categories found, sources list | Working (tested) |
| Answers only from the district's own content, exact fallback when not found, no mixing of districts | Working with a test stand-in for Claude; needs a real API key to run live |
| Lead form with spam checks, stored in SQLite, team-only admin page and CSV export | Working (tested) |
| Forward each lead to an existing intake (Apps Script, Zapier, Slack) | Needs `LEAD_WEBHOOK_URL` |
| Adding leads to an Instantly list | Not built. Use the webhook to reach the existing website intake, or add later |
| Text recognition (OCR) for scanned PDFs | Not built. Scanned PDFs are flagged as not read |
| Pages that need JavaScript to show content | Not read. Flagged as not read |

## Run locally

Requires Node 22.13 or newer (uses the built-in SQLite module).

```bash
npm install
cp .env.example .env   # fill in ANTHROPIC_API_KEY and ADMIN_PASSWORD
export $(grep -v '^#' .env | xargs) && npm start
# open http://localhost:3000, leads at http://localhost:3000/admin
```

Tests (no API key needed; they use fictional districts and a local stand-in for the Claude API):

```bash
python3 -m pip install reportlab pillow   # only to build the test PDFs
python3 test/make_fixtures.py
npm test
```

## Deploy (about 15 minutes)

It needs one always-on Node server with a small persistent disk, because reading a website takes 2 to 4 minutes and the database is a file. Vercel serverless functions are not a good fit for that.

**Render (blueprint included):** the app lives on the `district-assistant` branch of `tomoclub-games/TomoClub` (Vercel deployments are turned off for this branch in `vercel.json`).
1. Render: New > Blueprint > connect GitHub > pick `tomoclub-games/TomoClub`, branch `district-assistant`. It reads `render.yaml` (Docker, Starter instance, 1 GB disk at `/data`).
2. Paste `ANTHROPIC_API_KEY` and choose an `ADMIN_PASSWORD` when asked, then Apply.
3. Test on the `onrender.com` link. Then Settings > Custom Domains > add `assistant.tomoclub.org`, and in Cloudflare add a CNAME `assistant` pointing to the `onrender.com` host, proxy off (DNS only).

**Railway or Fly.io:** deploy the Dockerfile, attach a volume at `/data`, set the same variables.

Environment variables are listed in `.env.example`. The API key is only read on the server and never sent to the browser.

## Costs

- Hosting: one small instance plus a 1 GB disk. Check the provider's current pricing.
- Claude: each question makes one short call to the fast model (search words) and one call to the answer model with about 3,000 to 5,000 input tokens and up to 700 output tokens. Reading a website makes no AI calls.
- Limits that keep costs down (per IP per hour): 6 websites, 60 questions, 5 leads. A website read in the last 7 days is reused instead of read again.

## Privacy and safety

- Reads public pages only. Never signs in, never bypasses robots.txt, CAPTCHAs or bot protection. Identifies itself with a TomoClub user agent.
- Refuses private network addresses, so visitors cannot point the server at internal systems.
- Questions are not stored. The page asks visitors not to type student names or personal information.
- Leads are stored with a hashed IP address and are visible only at `/admin` with the admin password.
- District text is treated as data. The model is told never to follow instructions found inside it.

## Before showing it to a superintendent

1. Deploy and set the API key.
2. Read two or three real district websites (for example a TomoClub partner district) and ask 8 to 10 questions each: calendar, attendance, enrollment, buses, cell phones, meals, immunizations, closings.
3. Open each cited source and confirm the answer is there. Note any district whose site could not be read and why.
4. Submit one test lead and check `/admin` (and the webhook, if set).

## Files

- `src/crawler.js`: website reading, robots.txt, sitemap, link ranking, status per page
- `src/extract.js`: HTML and PDF text extraction, chunking
- `src/assistant.js`: search, prompt, citation checks, fallback answer
- `src/server.js`: API, uploads, leads, admin
- `public/`: the interface
- `test/`: fixture districts, Claude stand-in, end-to-end tests
