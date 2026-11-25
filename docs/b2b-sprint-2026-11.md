# B2B website sprint (Nov 2026)

Last updated: 2026-11-25 (section B built on branch `site-tracking`; section C mostly done). Owner: Avinash Bansal (business decisions). Repo and go-live: Rohith.

**Goal:** tomoclub.org is a B2B-only site for school and district leaders, and each visitor can be traced from the first visit to a booked call. Every lead lands where someone acts on it, and the site's claims and privacy policy match reality.

**Decision (24 Nov):** PRs #15 and #17 will not be merged.
- **#15** (`b2b-only-site`, 17 Nov) was built on the site as it was before PR #16, so it is out of date.
- **#17** (`analytics-leads`, 23 Nov) skips parts of our setup. For example, it hand-edited 200 pages but did not update the article and blog generators, so new posts would have no tracking.

What's left is rebuilt on a fresh branch from `main`. Both PRs, and the `b2b-site` branch, are used only as references.

---

## 1. Achieved through PR #16 (merged and live 19 Nov)

**The site is now B2B-only**
- [x] The new B2B homepage is at `/`, built from `pages/home.html` with its own `assets/css/home.css` and `assets/js/home.js`. It tells the story step by step, from the first call to the classroom, and falls back to a stacked layout on phones and when reduced motion is on.
- [x] The shared nav, call to action, floating button and footer now point to "Book a 20-minute call". "For Parents" links and "Request a Pilot" buttons are gone.
- [x] The parents site is archived in `archive/b2c-2026-11/`, which is not deployed: the parents homepage, `/ai-lab`, `/life-skills`, `/both-programs`, `parents-site.js`, and `api/book`, `slots`, `collect` and `geo`.
- [x] The old `/schools` page is archived. `/contact-us` is archived too, and its links are removed.
- [x] 301 redirects to `/` for `/schools`, `/ai-lab`, `/life-skills`, `/both-programs`, `/parents/*` and `/contact-us` (also `/contact-form`, `/schedule` and `/contact-us.html`).

**Copy fixes**
- [x] The approved figure "33 districts / 10k+ students" is used everywhere. The 15,000+, 5,000+ teachers and 12+ or 14+ states figures are removed.
- [x] Results: the Amity figure is corrected to 40 educators trained, 28 survey responses. The unsourced "97% engagement" and "85% referral reduction" cards are removed, and so is "saves 8+ hours" on the PD page.
- [x] The expired "E-book going live May 1st" banner is removed from every page.
- [x] The About page photo with the "Grok" watermark is replaced with the real 2018 XPRIZE photo.

**Leads**
- [x] The home form posts to `/api/lead`. It has spam checks (hidden honeypot field, minimum fill time, link count, origin, rate limit), saves a row to the "School leads" tab through the Apps Script, and alerts Slack.
- [x] "Book a call" links open a Calendly pop-up (`assets/js/calendly.js`). A completed booking is read from Calendly and saved to the Sheet the same way.
- [x] The security policy (CSP) allows Calendly.

**Fits our setup**
- [x] Built through `_partials/` and `pages/` with `scripts/build_pages.py`.
- [x] The article and blog generators (`add_article.py`, `add_blog_post.py`) are updated, so new posts get the same nav and scripts.
- [x] The sitemap is rebuilt (198 URLs).

---

## 2. What's left

Source key: **15** = PR #15, **17** = PR #17, **B** = the `b2b-site` notes (`docs/b2b-site-2026-11.md` on that branch).

### A. Scope decisions (decided by Rohith, 24 Nov)

- [x] **Unfinished-form leads (17): not now.** The forms keep their current look. GA4's `form_abandon` event shows how many people start a form and leave, which tells us whether this is worth adding later.
- [x] **`/admin` dashboard (17): not now.** GA4 covers visitors, sources and conversions. Leads stay in the Sheet, which gets a "Follow-up status" column.
- [x] **Email alerts (17): no.** Alerts stay on Slack only, as they are today.
- [x] **Instantly (15, 17): not in this sprint.** Moved to the "Later" list below.
- [x] **Phone field (17): no.** The forms stay as they are.
- [x] **Old parent URLs (15): no change.** They all keep redirecting to `/`.
- [x] **The whole site is in scope, including tracking on Build With Us.** Two things on `/build-with-us` must not change:
  - **Its form flow:** it posts straight to its own Apps Script, then redirects to `/build-with-us/thank-you`.
  - **Its book-a-call buttons,** including "get on a call right now" in the thank-you message: they open Calendly in a new tab.

The rebuild is therefore: GA4 tracking across the whole site, plus fixes to forms and spam protection (not the Build With Us form). Nothing changes visually on the site.

**Tracking goes into `assets/js/analytics.js`,** which every page already loads, so there is one file and no new script tag. All tracking only watches: it never cancels or changes a click or a submit.

On Build With Us:
- `book_call_click` and `cta_click` on its buttons;
- `form_view`, `form_start` and `form_abandon` on `#project-form`;
- `generate_lead` when the thank-you page loads (the page is reached only after a successful send).

The existing Build With Us pieces stay: `lead_submitted` on submit (it also fires when validation fails, so `generate_lead` is the accurate count) and the Meta `Lead` on the thank-you page. Its new-tab Calendly links can't report `book_call_scheduled`; only the pop-up can.

**In scope:**
- `assets/js/analytics.js`;
- the 12 pages built from `pages/` with `scripts/build_pages.py`, and the shared `_partials/`;
- the 107 podcast episode pages;
- `/leaders-of-tomorrow` and its ebook form;
- articles and blog posts, together with their generators;
- `/build-with-us`, for tracking only;
- `api/lead.js`, `api/signup.js` and `data-capture/Code.gs`.

### B. Build (branch `site-tracking`, from `main`; done 25 Nov, not yet pushed)

**Tracking**
- [x] **New tracking in `assets/js/analytics.js`** (section 7), so every page gets it with no new script tag. It only watches clicks, forms and Calendly messages; it never changes what they do. GA4 events, with emails and phone numbers stripped from every value:
  - `cta_click` with a fixed `cta_name` (Book a call, Tell us your problem, Explore AI PD, See results, Build With Us, Guides, ...), now also for buttons outside `data-track` sections;
  - `book_call_click { cta_location }` and `book_call_scheduled`;
  - `form_view`, `form_start`, `form_abandon` for the home form, the guide pop-up, both ebook forms and Build With Us. The pop-up counts as viewed when it opens;
  - `generate_lead` (home form after the server saved it; Build With Us thank-you page, once per session), `resource_download`, `faq_open`, `contact_click`;
  - `window.tomoTrack`, so the home page's `story_step_view` events now arrive. (17, B)
  - No custom `file_download`: GA4's enhanced measurement already logs PDF clicks (check it is on, C).
- [x] Page-address redaction is done with GA4's own setting instead of code (C), because the page view is sent by the inline head snippet before `analytics.js` runs. (17)
- [x] Booking events: the tracking listens to Calendly's own messages. `calendly.js` is not changed. (B, 17)
- [x] Kept as they were: the Build With Us `lead_submitted` and Meta `Lead`, the Tally listener, `section_view`, the WhatsApp `Contact`. No click is counted twice (tested).

**Forms and spam protection**
- [x] Home form: `generate_lead` and the Meta `Lead` are sent only after `/api/lead` returns success. (B, 17)
- [x] The same spam checks on the guide-download pop-up and the `/leaders-of-tomorrow` ebook forms: hidden honeypot field, 3-second minimum, link count. Spam gets a normal reply and is not saved; the download still starts. `api/signup.js` now uses the shared helpers in `api/_lead-core.js`. (15, 17)
- [x] Throwaway email domains (mailinator, yopmail, guerrillamail, 10minutemail, temp-mail, trashmail, sharklasers) are refused by `/api/lead` with "Please use a permanent email address", and silently not saved by `/api/signup`. (15)
- [x] Guide-download pop-up now says "Your download starts right away." instead of claiming marketing consent. (17)
- [x] A submission ID on every form. `Code.gs` skips a row whose ID it saved in the last 6 hours (no row, no Slack alert). Calendly bookings use Calendly's own booking ID. (17)
- [x] "Submission ID" and "Follow-up status" columns at the end of "School leads"; "Submission ID" at the end of "E-book requests" and "Toolkit downloads". `Code.gs` writes the new titles into the existing header rows. (replaces the dashboard)

**Fit our setup** (the #17 lesson)
- [x] Edited `_partials/` and `pages/` only, then ran both build scripts; `--check` passes for both. `script.js` is now `?v=28`, `home.js` `?v=3`.
- [x] No page or generator needed a new script tag. The article and blog generators needed no change.
- [x] `build-with-us/` is unchanged against `main`. In the browser test its Calendly links still open in a new tab, and its form still posts to its own Apps Script and redirects to the thank-you page.
- [x] No URLs changed, so no sitemap rebuild.
- [x] Tests: `npm test` runs 27 checks locally with no real Sheet, Slack, GA4 or Calendly (`tests/`, not deployed). The API and `Code.gs` behaviour, plus a headless-Chrome run of home, `/faqs`, `/guides`, a podcast page, an article, `/leaders-of-tomorrow` and `/build-with-us`, checking each event fires once with no personal data in it.
- Known trade-off: a person whose browser autofills the guide pop-up and who clicks within 3 seconds still gets the download, but no row is saved.

### C. Set up (accounts only Rohith or Avinash can reach)

- [x] **Sheet:** (checked by Rohith, 2026-11-25: no extra columns) before pasting the new `Code.gs`, check that nobody added their own column to the right of "Landing page" in "School leads", "E-book requests" or "Toolkit downloads". If they did, move it first, or the new columns would land in it.
- [x] **Apps Script:** (deployed by Rohith, 2026-11-25) paste the updated `Code.gs` (Submission ID and Follow-up status columns, duplicate check) and deploy a new version of the existing deployment (same URL). Either order with the site deploy is safe.
- [x] **Vercel:** (done by Rohith, 2026-11-25) new `CALENDLY_TOKEN` "TomoClub website – bookings (Vercel)" with `scheduled_events:read`, plus `availability:read`, `scheduled_events:write`, `event_types:read` and `users:read` for the future booking calendar. Revoke the old token after the go-live test booking works.
- [x] **GA4:** (done by Rohith, 2026-11-25, in property G-FEGGQ2ZDMT, also 7 event-scoped custom dimensions: form_name, cta_location, cta_name, section_name, resource_name, question, method) mark `generate_lead`, `book_call_scheduled` and `resource_download` as key events. Turn on email and query-parameter redaction for the web data stream. Confirm enhanced measurement "File downloads" is on.
- [ ] **GA4:** decide what to do with the second property `G-TEEDDHTK84`, which gets a copy of every page view. The options are in `docs/analytics/SETUP.md` on the `analytics-audit` branch.
- [ ] **LinkedIn:** create conversions and send their IDs. **Meta Pixel:** keep automatic advanced matching off. **Clarity:** keep text masking on Balanced or Strict.

### D. Go live and test

- [ ] Set the secrets (C) before merging, so form saves never fail.
- [ ] Merge, then send one test through the home form, the guide-download pop-up and the ebook form, and book one test call.
- [ ] For each test, check the Sheet rows and that exactly one Slack alert arrived.
- [ ] GA4 DebugView: the events arrive, with no names, emails or school names in them.
- [ ] Not yet confirmed: was a real test form sent and a test call booked on the live site after PR #16?

### E. Content and legal (mostly Avinash)

- [ ] **Privacy policy:** list the tools in use (GA4, Clarity, Meta, LinkedIn, Leadsy, Calendly, Google Sheets, Slack). Remove Brevo.
- [ ] Two partner logos (sl_m, sl_panther) are labelled "Partner school". What are their names? Are Edgewater Park, Garden School, Elite Academy and NYSkool still current partners? (B)
- [ ] Are the project status labels right: New Mexico and Pennsylvania (In development), Florida and Cedars (Prototype)? (B)
- [ ] Is the anonymised Massachusetts example OK? (B)
- [ ] Can the site say "Two districts used our prototypes in grant applications" and "Approved on Utah Fits All (two programs)"? (B)
- [ ] Newsletter: keep the Substack embed, or replace it with a signup that feeds Instantly? (B)
- [ ] Three parent-focused blog posts (phone bans, screen time, AI skills for children): keep them for search traffic, or archive them? (B)
- [ ] TAICY page (dates passed): keep, update or archive? (B)
- [ ] Real classroom photos (with consent) to replace the AI-generated hero images on the program pages. (B)
- [ ] Edgewater Park PD results (26 educators, 32% to 75%): publish a case study? (B)

### F. Housekeeping

- [ ] Close PRs #15 and #17 with a note that this rebuild replaces them. Keep their branches until the rebuild is merged, then delete `b2b-site`, `b2b-only-site` and `analytics-leads`.
- [ ] SEO coverage checks on 25 Nov and 9 Dec. Expect changes to `/` and the redirected URLs. Update the J4 note in `docs/seo-real-urls/STATUS.md`, which still says the B2B homepage is "not yet merged".
- [ ] Request indexing for `/` in Search Console.

---

## 3. Later (not this sprint)

- [ ] **Instantly.** Decide who goes in: only people who tick an opt-in box (17, safer on consent) or every email (15). Then:
  - create the lists and campaigns, and write the emails before turning the campaigns on;
  - add the routing to `/api/lead` and `/api/signup`;
  - add `INSTANTLY_API_KEY` and the routing settings in Vercel;
  - update the privacy policy.
  - Also decide whether the Substack signup should feed Instantly (section E).
- [ ] **Unfinished-form leads** with a consent box. Revisit if GA4's `form_abandon` numbers are high. (17)
- [ ] **An `/admin` dashboard.** Revisit if the team finds GA4 and the Sheet are not enough. (17)
- [ ] **Email alerts** in addition to Slack. (17)
- [ ] **Booking calendar on the site,** replacing the Calendly pop-up: our own slot picker and form, with the booking made on the server. The `CALENDLY_TOKEN` already has the scopes (25 Nov). Reuse `archive/b2c-2026-11/api/slots.js` and `book.js`, and point `CALENDLY_EVENT_TYPE_URI` at the B2B "book a call" event. Needs a paid Calendly plan.
- [ ] **Cloudflare Turnstile,** an optional bot check that shows a small widget on forms. Moved here by Rohith on 24 Nov, because so far spam has only hit the Build With Us form. (15, B)
- [ ] **The Build With Us form flow, only if Rohith decides to revisit it.** Known issues:
  - its Apps Script address is visible in the page source and gets bot submissions;
  - it has no spam checks;
  - its `lead_submitted` event fires before the server accepts the form. (15, 17)
