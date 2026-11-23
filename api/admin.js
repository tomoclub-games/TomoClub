// Vercel serverless function: /api/admin  (the internal dashboard at /admin uses it)
//
//   POST ?action=login    { password }            sets a signed, HttpOnly session cookie for 12 hours
//   POST ?action=logout                           clears it
//   GET  ?action=session                          { ok } when signed in
//   GET  ?action=data&from=YYYY-MM-DD&to=YYYY-MM-DD   dashboard numbers and leads for that range
//   POST ?action=status   { lead_id, status, note, by }   saves a follow-up status
//
// Env vars: ADMIN_PASSWORD (the team's dashboard password, at least 12 characters), SHEET_WEBHOOK, SHEET_SECRET.
// Responses are never cached. Writes must come from the site's own origin (SameSite=Strict cookie + Origin check).

import crypto from 'node:crypto';
import { originAllowed, clientIp, tooMany, readBody, callSheet, clean } from './_lead-core.js';
import { computeDashboard, STATUSES } from './_admin-metrics.js';

const COOKIE = '__Host-tc_admin';
const TTL = 12 * 3600;

function key() {
  const pw = process.env.ADMIN_PASSWORD || '';
  // Changing the password signs everyone out.
  return crypto.createHash('sha256').update('tc-admin|' + pw + '|' + (process.env.SHEET_SECRET || '')).digest();
}
function sign(exp) { return exp + '.' + crypto.createHmac('sha256', key()).update(String(exp)).digest('base64url'); }
function valid(token) {
  const [exp, mac] = String(token || '').split('.');
  if (!exp || !mac || Number(exp) < Date.now() / 1000) return false;
  const good = sign(exp).split('.')[1];
  return good.length === mac.length && crypto.timingSafeEqual(Buffer.from(good), Buffer.from(mac));
}
function readCookie(req) {
  const m = String(req.headers.cookie || '').match(new RegExp('(?:^|;\\s*)' + COOKIE.replace(/[-_]/g, '\\$&') + '=([^;]+)'));
  return m ? decodeURIComponent(m[1]) : '';
}
function sameText(a, b) {
  const x = crypto.createHash('sha256').update(String(a)).digest();
  const y = crypto.createHash('sha256').update(String(b)).digest();
  return crypto.timingSafeEqual(x, y);
}
const isoDay = (v) => (/^\d{4}-\d\d-\d\d$/.test(String(v || '')) ? String(v) : '');

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Robots-Tag', 'noindex, nofollow');
  const action = String((req.query && req.query.action) || '');
  const pw = process.env.ADMIN_PASSWORD || '';
  if (pw.length < 12) return res.status(503).json({ ok: false, error: 'Set ADMIN_PASSWORD (12+ characters) in Vercel first.' });

  if (req.method === 'POST' && !originAllowed(req)) return res.status(403).json({ ok: false });

  if (action === 'login' && req.method === 'POST') {
    if (tooMany(clientIp(req), 8, 15 * 60 * 1000, 'login')) return res.status(429).json({ ok: false, error: 'Too many attempts. Wait 15 minutes.' });
    const b = readBody(req);
    if (!sameText(b.password || '', pw)) return res.status(401).json({ ok: false, error: 'Wrong password' });
    const exp = Math.floor(Date.now() / 1000) + TTL;
    res.setHeader('Set-Cookie', `${COOKIE}=${encodeURIComponent(sign(exp))}; Path=/; Max-Age=${TTL}; HttpOnly; Secure; SameSite=Strict`);
    return res.status(200).json({ ok: true });
  }
  if (action === 'logout') {
    res.setHeader('Set-Cookie', `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict`);
    return res.status(200).json({ ok: true });
  }

  if (!valid(readCookie(req))) return res.status(401).json({ ok: false, error: 'Sign in' });
  if (action === 'session') return res.status(200).json({ ok: true });

  if (action === 'data' && req.method === 'GET') {
    const today = new Date().toISOString().slice(0, 10);
    const to = isoDay(req.query.to) || today;
    const from = isoDay(req.query.from) || new Date(Date.now() - 29 * 864e5).toISOString().slice(0, 10);
    if (from > to) return res.status(400).json({ ok: false, error: 'from is after to' });
    const tabs = ['Website events', 'School leads', 'E-book requests', 'Toolkit downloads', 'Partial leads'];
    // Lead status is read in full so older leads keep their status.
    const [r1, r2] = await Promise.all([
      callSheet({ action: 'read', tabs, since: from }, 25000),
      callSheet({ action: 'read', tabs: ['Lead status'], since: '' }, 25000),
    ]);
    if (!r1 || !r2) return res.status(502).json({ ok: false, error: 'Could not read the Sheet. Check SHEET_WEBHOOK and SHEET_SECRET.' });
    const out = computeDashboard({ ...r1.tabs, ...r2.tabs }, { from, to });
    return res.status(200).json({ ok: true, generated_at: new Date().toISOString(), ...out });
  }

  if (action === 'status' && req.method === 'POST') {
    const b = readBody(req);
    if (!STATUSES.includes(b.status)) return res.status(400).json({ ok: false, error: 'Unknown status' });
    const r = await callSheet({ action: 'set_status', data: { lead_id: clean(b.lead_id, 120), status: b.status, note: clean(b.note, 500), by: clean(b.by, 60) } });
    return res.status(r ? 200 : 502).json(r ? { ok: true, saved: r.saved } : { ok: false, error: 'Could not save' });
  }

  return res.status(404).json({ ok: false });
}
