# Analytics setup: how it is wired today

Status: draft started 2026-11-03. Items marked **TO FILL** need someone to read them from the Google Analytics or tool dashboards. Code facts come from this repo.

## 1. What runs on the site

All of it loads on every page.

| Tool | ID | Where in code | Added | By (git) |
|---|---|---|---|---|
| GA4 (Google tag) | `G-FEGGQ2ZDMT` | `_partials/head.html` lines 41-47, plus a guarded duplicate block in `assets/js/analytics.js` (skips itself when the head tag exists) | 2026-05-10, commit `9e7d9bd` | JANMEJAY |
| LinkedIn Insight Tag | partner `8364153` | `assets/js/analytics.js` | 2026-09-14 / 09-15, `ff4314f`, `c1f29fb` | Avinash Bansal |
| Microsoft Clarity | project `yibamjl9lq` | `assets/js/analytics.js` | 2026-09-14 / 09-15, `ff4314f`, `054fdde` | Avinash Bansal |
| Leadsy.ai | pid `Er26IyzOijeMy17O` | `assets/js/analytics.js` | 2026-09-20, `12855b3` | tomoclub-games |
| Meta Pixel | `1805331960518408` | `assets/js/analytics.js` | 2026-10-16, `59b27c5` | tomoclub-games |

Custom GA4 events sent from `assets/js/analytics.js`: `section_view`, `cta_click` (only inside elements with `data-track`, which exist only on `build-with-us`), `lead_submitted` (Build With Us form).

## 2. Google Analytics: properties and destinations

The page sends to one tag, `G-FEGGQ2ZDMT`. Inside Google's tag settings that tag has two destinations, so every page view lands in two properties.

| Destination name | Measurement ID | Destination added | Created by |
|---|---|---|---|
| TomoClub (stream `www.tomoclub.org`) | `G-FEGGQ2ZDMT` | 2026-05-09 | `shreyas@tomoclub.org` (property created 2026-05-09) |
| TomoClub Web (property "Visitor tracking") | `G-TEEDDHTK84` | 2026-10-16 | `shreyas@tomoclub.org` (property created 2026-10-16) |

All accounts and properties visible to the signed-in admin (listed 2026-11-03). The "App name" shown in the account selector is the property name.

| # | Account (ID) | Property (ID) | Measurement ID / stream | Created | Data in last 28 days | Decision |
|---|---|---|---|---|---|---|
| 1 | Tomo Club (215762110) | Tomo website (297483445) | 3 streams: "Tomo Club" `G-934GDPPWT6` (inactive), "MonsterInsights - https://tomoclub.org" `G-N454VWKJ71` (inactive), "SubStack" `G-614H9ZRHBH` (active, receives data). None is `G-FEGGQ2ZDMT` or `G-TEEDDHTK84`, and none appears in this repo or the live site | Property created on or before 2025-03-06. A Google Ads link (customer 2776706568, ads personalization on) was created that day by `info@tomoclub.org` | 44 active users, 37 new users, 138 page_view, 64 session_start (2026-10-06 to 2026-11-02). Only the Substack stream is active | Keep for now: it carries the Substack newsletter analytics. The two inactive streams (old WordPress/MonsterInsights era) can be deleted |
| 2 | TomoClub (394111675) | TomoClub Website (536894823) | 1 stream: "TomoClub" `G-FEGGQ2ZDMT` (active). This is the tag in the site code | 2026-05-09 22:40 IST by `shreyas@tomoclub.org` (account change history) | 2k active users, 2.1k new users, 3.5k page_view, 2.4k session_start, 256 section_view, 29 click (28 days, to 2026-11-02) | Main property. Keep |
| 3 | TomoClub Website (412267601) | Visitor Tracking (559250512) | 1 stream: "TomoClub Web" `G-TEEDDHTK84` (active). Not in site code; receives hits forwarded from `G-FEGGQ2ZDMT`'s Google tag | 2026-10-16 11:41 IST by `shreyas@tomoclub.org` | 1.2k active users, 1.2k new users, 2.5k page_view, 1.4k session_start, 185 section_view, 25 click (28-day view, but data only since 2026-10-16) | Reportedly created as the analytics property for the new tomoclub.org website (told by Rohith, not yet confirmed with Shreyas). Gets the same hits as property 2 through a destination in the shared Google tag. **Decision open: which of properties 2 and 3 is canonical** |

Which of these three holds `G-FEGGQ2ZDMT` and which holds `G-TEEDDHTK84`: **TO FILL**.

Who has Administrator on each property: **TO FILL**.

## 3. Key events in `G-FEGGQ2ZDMT` (checked 2026-11-03)

| Event | Fired by this repo? | Data in last 28 days | Note |
|---|---|---|---|
| `calendly_click` | No | Yes (stream TomoClub) | Not in code or git history. Probably a GA4 "Create event" rule or an enhanced-measurement outbound click rule. **TO FILL**: Admin → Data display → Events → Create event |
| `lead_submitted` | Yes, Build With Us form | None | Either no submissions, or the event does not arrive. Test in DebugView |
| `close_convert_lead` | No | None | Google lead-lifecycle template event. Unused |
| `qualify_lead` | No | None | Same |
| `purchase` | No | None | Not starred. Unused |

## 4. Other dashboards to record

| Tool | Account owner | Who has access | Used by whom, how often |
|---|---|---|---|
| Search Console linked to GA4 | **TO FILL** | **TO FILL** | **TO FILL** |
| Clarity project | **TO FILL** | **TO FILL** | **TO FILL** |
| LinkedIn Campaign Manager | **TO FILL** | **TO FILL** | **TO FILL** |
| Meta Events Manager | **TO FILL** | **TO FILL** | **TO FILL** |
| Leadsy | **TO FILL** | **TO FILL** | **TO FILL** |

## 5. Cleanup decisions (open)

1. Which property is the main one? Default proposal: `G-FEGGQ2ZDMT` (history since May).
2. Keep or remove the `G-TEEDDHTK84` destination after asking its creator.
3. Archive properties with no data. Archiving can be undone for 35 days.
4. Remove unused key events: `close_convert_lead`, `qualify_lead`, `purchase`.
5. Rename the surviving property and stream so the name says what it is.
6. Remove tools nobody uses (see the measurement plan).

## 6. Next steps (resume here)

Order matters: fulfil the measurement purposes first, then remove unused tools.

1. **Check property 3 (`559250512`)** to decide the canonical property: Admin → Product links (Search Console, Google Ads, BigQuery), Key events, any Looker Studio report, and who has access. Links or reports that property 2 lacks point to making property 3 canonical.
2. **Confirm with Shreyas** (`shreyas@tomoclub.org`, created properties 2 and 3) why property 3 exists and whether anything depends on it.
3. **Choose one:**
   - Option A: keep property 2 (history since May). Remove the `G-TEEDDHTK84` destination (property 2, Admin → Data streams → stream → Configure tag settings → Manage connected site tags) and archive property 3. No code change.
   - Option B: make property 3 canonical. Point `_partials/head.html` and `assets/js/analytics.js` at `G-TEEDDHTK84`, remove `G-FEGGQ2ZDMT`, archive property 2. Old data stays in property 2.
4. **Clean property 1:** delete the two inactive streams (`G-934GDPPWT6`, `G-N454VWKJ71`), rename it to something like "TomoClub: Substack". Ask whether the linked Google Ads account (customer 2776706568) is in use, unlink if not.
5. **Rename the surviving property and stream** to say what they are.
6. **Fix and extend tracking** (purposes first): test `lead_submitted` in DebugView (no data in 28 days); find the rule behind `calendly_click` (Admin → Data display → Events); add `generate_lead` on the newsletter, resource, contact and Share Your Story forms; add `episode_play` for podcast; remove unused key events (`close_convert_lead`, `qualify_lead`, `purchase`); link Search Console to the surviving property.
7. **Then prune tools:** remove the duplicate GA4 block in `assets/js/analytics.js` (the head snippet already loads it), the LinkedIn `conversion_id: null` no-op, and any of Leadsy, LinkedIn Insight and Meta Pixel that nobody uses. Leadsy has the highest privacy risk.
8. **Privacy policy:** it names only Google Analytics and Meta Pixel. Update it to list exactly the tools that remain (Clarity, LinkedIn, Leadsy are missing today). Add a consent banner if EU or UK visitors matter.
9. **Open question for the team:** does anyone read Clarity, LinkedIn Campaign Manager, Meta Events Manager or Leadsy?
