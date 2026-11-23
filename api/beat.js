// Vercel serverless function: POST /api/beat
// First-party site activity for the /admin dashboard: page views, button clicks and form steps, sent in small
// batches by assets/js/tc-forms.js (navigator.sendBeacon). Saved to the "Website events" tab of the form Sheet.
// (Named "beat" rather than "event" or "collect" so common ad blockers do not drop it.)
//
// Privacy: no names, emails, phone numbers or form contents are accepted. The visitor and session IDs are random
// values made in the browser. Labels are scrubbed of anything that looks like an email or a phone number, and
// URLs lose query parameters that could carry personal details. Known bots are ignored.

import { originAllowed, clientIp, tooMany, clean, readBody, scrubPII, redactUrl, cleanId, saveToSheet } from './_lead-core.js';

export const EVENTS = new Set([
  'page_view', 'cta_click', 'book_call_click', 'book_call_open', 'book_call_scheduled',
  'form_view', 'form_start', 'form_submit', 'form_success', 'form_error', 'form_abandon', 'partial_saved',
  'resource_download', 'file_download', 'contact_click', 'outbound_click', 'faq_open', 'video_play',
  'scroll_depth', 'story_step_view',
]);
const DEVICES = new Set(['mobile', 'tablet', 'desktop']);
const BOT = /bot|crawl|spider|slurp|headless|lighthouse|pingdom|uptime|monitor|preview|facebookexternalhit|bingpreview/i;

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();
  if (!originAllowed(req)) return res.status(403).end();
  if (BOT.test(String(req.headers['user-agent'] || ''))) return res.status(204).end();
  if (tooMany(clientIp(req), 300, undefined, 'beat')) return res.status(429).end();

  const b = readBody(req);
  const visitor = cleanId(b.visitor_id);
  const session = cleanId(b.session_id);
  if (!visitor) return res.status(400).end();
  const device = DEVICES.has(b.device) ? b.device : '';
  const country = /^[A-Z]{2}$/.test(String(req.headers['x-vercel-ip-country'] || '')) ? req.headers['x-vercel-ip-country'] : '';
  const src = scrubPII(clean(b.source, 80)).toLowerCase();

  const rows = (Array.isArray(b.events) ? b.events.slice(0, 30) : [])
    .filter((e) => e && EVENTS.has(e.name))
    .map((e) => ({
      sheet: 'Website events',
      data: {
        timestamp: /^\d{4}-\d\d-\d\dT[\d:.]+Z$/.test(String(e.ts)) ? e.ts : new Date().toISOString(),
        visitor_id: visitor,
        session_id: session,
        event: e.name,
        label: scrubPII(clean(e.label, 120)),
        form: /^[a-z0-9_]{2,40}$/.test(String(e.form || '')) ? e.form : '',
        page: redactUrl(clean(e.page, 160)).split('?')[0],
        source: src || 'direct',
        medium: scrubPII(clean(b.medium, 60)).toLowerCase(),
        campaign: scrubPII(clean(b.campaign, 80)),
        device,
        country,
      },
    }));
  if (!rows.length) return res.status(204).end();
  const ok = await saveToSheet(rows);
  return res.status(ok ? 200 : 502).json({ ok });
}
