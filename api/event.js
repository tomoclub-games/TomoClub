// Vercel serverless function: POST /api/event
// Receives a small batch of site interactions from assets/js/b2b-events.js (sent with navigator.sendBeacon).
//
// Every batch is saved to the "Website events" tab of the form Sheet, anonymous or not, so the team can see
// what each account looked at. When the browser belongs to someone who already gave us their email through a
// form (proved by the signed token from api/lead.js or api/signup.js) and the batch has a high-intent event,
// the contact is also routed to Instantly under the "high_intent" intent (INSTANTLY_ROUTES), with the event
// in custom variables, so the follow-up email can refer to what they actually did.
//
// GA4, LinkedIn and Meta get the same events directly from the browser; this endpoint is the CRM copy.

import {
  originAllowed, clientIp, tooMany, clean, isEmail, saveToSheet, pushToInstantly, verifyLead, readBody,
} from './_lead-core.js';

// Events worth a follow-up when we know who the visitor is.
const HIGH_INTENT = new Set([
  'book_call_click', 'case_study_download', 'build_with_us_view', 'results_view', 'offer_view',
  'faq_cost_open', 'form_abandon',
]);
const NAME_OK = /^[a-z][a-z0-9_]{1,40}$/;

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false });
  if (!originAllowed(req)) return res.status(403).json({ ok: false });
  const ip = clientIp(req);
  if (tooMany(ip, 120)) return res.status(429).json({ ok: false });

  const b = readBody(req);
  const list = Array.isArray(b.events) ? b.events.slice(0, 25) : [];
  const visitor = clean(b.visitor_id, 64);
  const email = clean(b.email, 200).toLowerCase();
  const token = clean(b.token, 64);
  const hotLead = isEmail(email) && verifyLead(email, token, 'hot');
  const nurtureLead = isEmail(email) && !hotLead && verifyLead(email, token, 'nurture');
  const known = hotLead || nurtureLead;

  const events = list
    .map((e) => ({
      name: clean(e && e.name, 41),
      label: clean(e && e.label, 160),
      page: clean(e && e.page, 160),
      ts: clean(e && e.ts, 30),
    }))
    .filter((e) => NAME_OK.test(e.name));
  if (!events.length) return res.status(204).end();

  const rows = events.map((e) => ({
    sheet: 'Website events',
    data: {
      timestamp: e.ts || new Date().toISOString(),
      visitor_id: visitor,
      email: known ? email : '',
      event: e.name,
      label: e.label,
      page: e.page,
      utm_source: clean(b.utm_source, 120),
      utm_campaign: clean(b.utm_campaign, 120),
      landing_page: clean(b.landing_page, 300),
    },
  }));
  await saveToSheet(rows);

  // People who asked to talk are followed up by a person, so only download-only contacts are routed.
  const hot = nurtureLead && events.find((e) => HIGH_INTENT.has(e.name));
  if (hot) {
    await pushToInstantly('high_intent', {
      email,
      custom_variables: {
        intent: 'high_intent',
        last_event: hot.name,
        last_event_label: hot.label,
        last_event_page: hot.page,
        last_event_at: hot.ts,
      },
    });
  }
  return res.status(200).json({ ok: true });
}
