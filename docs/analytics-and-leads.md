# Analytics and lead tracking (Nov 2026)

Branch: `analytics-leads`. Built on the live site (main after PR #16). Nothing changes for visitors except two
unticked boxes on each lead form.

## What it does

| Need | How |
|---|---|
| Visitors, page views, sources, devices | GA4 (G-FEGGQ2ZDMT, already on every page) plus a first-party copy for the dashboard: `assets/js/tc-forms.js` sends page views to `/api/beat`, saved in the "Website events" tab with a random visitor ID, session ID, source (UTM or referrer), device type and country. Bots are ignored. |
| Button clicks | Every button-style link and button. Important ones get fixed names: Book a call, Tell us your problem, Build With Us, Contact us, Explore AI PD / AI Literacy / Future-Ready Skills, See results. GA4 event `cta_click` (param `cta_name`) or `book_call_click`. |
| Form steps | `form_view` (on screen or pop-up opened), `form_start` (first typing), `form_submit` (pressed send), `form_success` (server saved it; GA4 `generate_lead`), `form_abandon` (started, left without sending). Forms: home page, Build With Us, ebook (2), guide download pop-up. |
| Incomplete leads | Only when the visitor ticks "Save my details if I don't finish, so TomoClub can follow up." Then name, email, school or district, phone and role (never the message) are saved to "Partial leads" when they pause or leave. Unticking erases them. Finishing the form marks the partial lead "converted". |
| Notifications | Slack (existing `SLACK_WEBHOOK_URL`) and email (`NOTIFY_EMAILS`). Finished forms: one alert per submission (a retry with the same submission ID is saved and alerted once). Partial leads: checked every 10 minutes; alerted once, 20 minutes after the last change, and never if the person finished a form meanwhile. Every alert is logged in the "Notifications" tab. |
| Dashboard | `https://www.tomoclub.org/admin` (password, not indexed, no tracking). KPIs, visitors per day, conversion rates, sources, buttons, devices, top pages, form funnel, Completed and Incomplete leads with follow-up status and notes, CSV export of each. Works on a phone. |
| Conversions | GA4 key events to mark: `generate_lead`, `book_call_scheduled` (confirmed Calendly booking), `resource_download`. Bookings are also saved as leads with the meeting time (`/api/lead`, type `call_booked`). |
| Instantly | Only for people who ticked "Send me occasional emails from TomoClub." (a separate box). Routed by intent with `INSTANTLY_ROUTES`. Calendly bookings never go to Instantly. |
| No personal data in GA4 | Events carry only event names, form names and button names. Labels are scrubbed of anything that looks like an email or phone number. `page_location` has the values of email/name/phone query parameters replaced with "redacted" on every page. Tested: no name, email or school name reached GA4. |

## Files

- `assets/js/tc-forms.js` events, consent boxes, partial capture (loaded on every page next to analytics.js)
- `api/beat.js` events, `api/partial.js` partial leads, `api/lead.js` + `api/signup.js` (consent, phone, submission IDs, Instantly), `api/admin.js` + `api/_admin-metrics.js` dashboard
- `admin/index.html` dashboard page
- `data-capture/Code.gs` new tabs (Partial leads, Website events, Lead status, Notifications), secret, deduplicated alerts, 10-minute partial check, dashboard reads
- `build-with-us/index.html` form now posts to `/api/lead` (old Apps Script endpoint kept as fallback)
- Download pop-ups: "By downloading, you agree to receive future updates" replaced with "Your download starts right away. We only send you emails if you tick the box above."
- `tests/` Apps Script tests (`node tests/gas.test.mjs`), local server (`node tests/e2e-server.mjs 8100`) and browser test (`python3 tests/e2e_browser.py`, 45 checks)

## Go-live steps (owner or Rohith)

1. **Apps Script** (the script behind the form Sheet): paste `data-capture/Code.gs`, Save. Script properties:
   - `SHEET_SECRET` = a long random string (password manager, 32+ characters)
   - `NOTIFY_EMAILS` = who gets lead emails, comma-separated
   - optional `ADMIN_URL`, `PARTIAL_WAIT_MINUTES` (default 20)
   Then Deploy > Manage deployments > Edit > New version (same URL). Run `installTriggers` once (authorises email + the 10-minute check). Optionally run `testNotifications`.
2. **Vercel** env vars (Production; Preview only if you want previews to write to the same Sheet):
   - `SHEET_SECRET` (same value as step 1)
   - `ADMIN_PASSWORD` (12+ characters; share with the team privately)
   - optional `INSTANTLY_API_KEY`, `INSTANTLY_ROUTES`, `INSTANTLY_DEFAULT_LIST_ID`
   - existing `SHEET_WEBHOOK`, `CALENDLY_TOKEN` stay (token needs `scheduled_events:read`)
   Order matters: set the Apps Script secret and the Vercel secret, then merge, so writes never fail.
3. **GA4**: Admin > Events, mark `generate_lead`, `book_call_scheduled`, `resource_download` as key events. Admin > Data streams > web > Redact data: turn on email and query-parameter redaction (belt and braces).
4. **Meta pixel**: keep automatic advanced matching off (it would hash form fields). **Clarity**: keep masking on "Balanced" or "Strict".
5. **Privacy policy**: add a short paragraph (suggested text below).
6. Merge, then send one test from each form and check: rows in the Sheet, one Slack + email alert, the dashboard numbers.

### Suggested privacy-policy paragraph

> **Forms you start but do not send.** Our contact and download forms include an optional box, "Save my details if I don't finish." If you tick it, we keep the name, email address, school or district, phone number and role you typed, even if you leave without sending the form, so our team can follow up once. Untick it before you leave and we erase what was saved. We never keep what you typed in the message box unless you send the form. **Marketing emails.** We add you to our email list only if you tick "Send me occasional emails from TomoClub." You can unsubscribe at any time. **Analytics.** We use Google Analytics and our own first-party counts (a random ID stored in your browser) to see how the site is used. We do not send your name, email or phone number to Google Analytics.

## Notes

- Visitor counts in the dashboard are first-party and can differ from GA4 (ad blockers, consent tools). GA4 remains the full picture.
- "Visitor to lead" can read above 100% in short ranges because Calendly bookings and leads from blocked browsers have no tracked visit.
- The Website events tab grows by roughly a few hundred rows a day at current traffic. Archive it to a new sheet once a year.
- Not tracked inside third-party frames: the Substack newsletter embeds and the Tally "share your story" form.
