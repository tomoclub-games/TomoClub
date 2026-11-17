// Vercel serverless function: POST /api/lead
// Receives the Build With Us project form (and any other B2B "talk to us" form), checks it for spam,
// saves it to the Build With Us leads sheet and adds the contact to the Instantly lead list.
//
// Env vars:
//   BWU_SHEET_WEBHOOK      Apps Script web app URL of the "TomoClub - Build With Us leads (v2)" sheet.
//                          Until it is set, the current deployment URL below is used, so nothing breaks.
//   INSTANTLY_API_KEY      Instantly API v2 key with the leads:create scope (optional)
//   INSTANTLY_LIST_ID      the Instantly lead list that website leads go to (optional)
//   TURNSTILE_SECRET_KEY   Cloudflare Turnstile secret (optional; see api/_lib/guard.js)
import {
  clean, clientIp, originAllowed, readBody, tooMany, checkHuman, validEmail, addToInstantly,
} from './_lib/guard.js';

// The deployment URL that used to sit in the page source. Replace it with a new deployment in
// BWU_SHEET_WEBHOOK and switch this one off in Apps Script, so bots that copied it stop reaching the sheet.
const LEGACY_BWU_WEBHOOK = 'https://script.google.com/macros/s/AKfycbyGlm2ilFpQAtfNRVcJhPFaiwOHmc0UqKZSu01vctDfSK-efmJjBJSVZ35jRqwNpbI/exec';

const ATTRIBUTION = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'referrer', 'landing_page'];

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Method not allowed' });
  if (!originAllowed(req)) return res.status(403).json({ ok: false, error: 'Not allowed' });

  const ip = clientIp(req);
  if (tooMany(ip, 10)) return res.status(429).json({ ok: false, error: 'Too many requests' });

  const b = readBody(req);
  const verdict = await checkHuman(b, ip);
  if (verdict === 'silent-drop') return res.status(200).json({ ok: true });
  if (verdict === 'reject') return res.status(400).json({ ok: false, error: 'Please complete the verification and try again.' });

  const lead = {
    name: clean(b.name, 120),
    organization: clean(b.district || b.organization, 200),
    role: clean(b.role, 120),
    email: clean(b.email, 200).toLowerCase(),
    goal: clean(b.goal, 3000),
    page: clean(b.page, 120) || 'build-with-us',
    form: clean(b.form, 60) || 'build-with-us',
  };
  ATTRIBUTION.forEach((k) => { lead[k] = clean(b[k], 300); });

  if (!lead.name || !lead.organization || !lead.goal || !validEmail(lead.email)) {
    return res.status(400).json({ ok: false, error: 'We need your name, school or district, a work email, and what is on your mind.' });
  }

  // The sheet keeps the column names the original page sent, so existing rows and formulas still line up.
  const row = {
    name: lead.name, district: lead.organization, email: lead.email, role: lead.role, goal: lead.goal,
    page: lead.page, submitted: new Date().toISOString(),
  };
  ATTRIBUTION.forEach((k) => { row[k] = lead[k]; });

  const [saved, instantly] = await Promise.all([
    saveBwu(row),
    addToInstantly(lead),
  ]);
  if (!saved && instantly !== 'added' && instantly !== 'skipped') {
    return res.status(502).json({ ok: false, error: 'Could not save. Please email avinash@tomoclub.org.' });
  }
  return res.status(200).json({ ok: true });
}

// The Build With Us script takes a form-encoded POST (it was written for the page's no-cors fetch).
async function saveBwu(row) {
  const url = process.env.BWU_SHEET_WEBHOOK || LEGACY_BWU_WEBHOOK;
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(row),
      redirect: 'follow',
      signal: AbortSignal.timeout(8000),
    });
    if (!r.ok) { console.error('BWU sheet write failed:', r.status); return false; }
    return true;
  } catch (e) {
    console.error('BWU sheet write error:', e);
    return false;
  }
}
