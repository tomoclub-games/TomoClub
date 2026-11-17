// Shared spam protection and lead routing for the website's form endpoints.
// Files under api/_lib are not routes (Vercel skips paths that start with an underscore).
//
// Spam protection, in order (every check is server side, so a bot posting directly to the API meets them too):
//   1. Origin must be tomoclub.org, a tomoclub-website Vercel preview, or localhost.
//   2. Rate limit per IP (best effort per warm instance).
//   3. Honeypot: the hidden "website" field must be empty.
//   4. Time trap: the form must have been on screen at least MIN_FILL_MS before it was sent (field "t0").
//   5. Cloudflare Turnstile, only when TURNSTILE_SECRET_KEY is set (the page shows the widget only when
//      TURNSTILE_SITE_KEY is set; /api/form-config tells the page).
//   6. Email shape check and a short list of throwaway-domain blocks.
// A request that fails 3 or 4 gets a normal-looking success reply and is dropped, so bots learn nothing.
//
// Instantly: when INSTANTLY_API_KEY and INSTANTLY_LIST_ID are set, every real lead with an email is added to
// that Instantly lead list (POST https://api.instantly.ai/api/v2/leads/add, skip_if_in_workspace).
// The key needs the leads:create scope. Nothing is sent to Instantly when either variable is missing.

export const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?tomoclub\.org$/,
  /^https:\/\/tomoclub-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];

const MIN_FILL_MS = 3000;
const THROWAWAY = /@(mailinator|guerrillamail|10minutemail|tempmail|yopmail|trashmail|sharklasers)\./i;

export const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);

const hits = new Map();
export function tooMany(ip, limit) {
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter((t) => now - t < 10 * 60 * 1000);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 500) hits.clear();
  return recent.length > limit;
}

export function clientIp(req) {
  return String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
}

export function originAllowed(req) {
  return ALLOWED_ORIGINS.some((re) => re.test(req.headers.origin || ''));
}

export function readBody(req) {
  let b = req.body;
  if (typeof b === 'string') {
    try { b = JSON.parse(b); } catch (e) { b = null; }
  }
  return b && typeof b === 'object' ? b : {};
}

// Returns 'ok', 'silent-drop' (looks like a bot: answer success, save nothing) or 'reject' (answer 400).
export async function checkHuman(b, ip) {
  if (clean(b.website, 200)) return 'silent-drop';
  const t0 = Number(b.t0);
  if (!t0 || Date.now() - t0 < MIN_FILL_MS || Date.now() - t0 > 24 * 60 * 60 * 1000) return 'silent-drop';

  const secret = process.env.TURNSTILE_SECRET_KEY;
  if (secret) {
    const token = clean(b.turnstileToken || b['cf-turnstile-response'], 2048);
    if (!token) return 'reject';
    try {
      const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ secret, response: token, remoteip: ip }),
        signal: AbortSignal.timeout(6000),
      });
      const j = await r.json().catch(() => null);
      if (!j || j.success !== true) return 'reject';
    } catch (e) {
      console.error('Turnstile verify error:', e);
      return 'reject';
    }
  }
  return 'ok';
}

export function validEmail(email) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email) && !THROWAWAY.test(email);
}

// Append one row to a Google Sheet through an Apps Script web app.
export async function saveToSheet(url, sheet, data) {
  if (!url) { console.error('Sheet webhook is not set'); return false; }
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ rows: [{ sheet, data }] }),
      signal: AbortSignal.timeout(8000),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j || j.ok !== true) { console.error('Apps Script rejected the row:', r.status, JSON.stringify(j)); return false; }
    return true;
  } catch (error) {
    console.error('sheet write error:', error);
    return false;
  }
}

// Add one lead to the Instantly lead list. Returns 'added', 'skipped' (already in workspace or blocklisted),
// 'off' (not configured) or 'failed'. Never throws.
export async function addToInstantly(lead) {
  const key = process.env.INSTANTLY_API_KEY;
  const listId = process.env.INSTANTLY_LIST_ID;
  if (!key || !listId || !lead.email) return 'off';
  const name = clean(lead.name, 120);
  const [first, ...rest] = name.split(/\s+/);
  const item = {
    email: lead.email,
    first_name: lead.first_name || first || '',
    last_name: lead.last_name || rest.join(' '),
    company_name: clean(lead.organization, 200),
    job_title: clean(lead.role, 120),
    custom_variables: {
      source_form: clean(lead.form, 60),
      source_page: clean(lead.page, 120),
      utm_source: clean(lead.utm_source, 120),
      utm_medium: clean(lead.utm_medium, 120),
      utm_campaign: clean(lead.utm_campaign, 120),
      captured_at: new Date().toISOString(),
    },
  };
  try {
    const r = await fetch('https://api.instantly.ai/api/v2/leads/add', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ list_id: listId, leads: [item], skip_if_in_workspace: true }),
      signal: AbortSignal.timeout(8000),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j) { console.error('Instantly add failed:', r.status, JSON.stringify(j)); return 'failed'; }
    return j.leads_uploaded > 0 ? 'added' : 'skipped';
  } catch (e) {
    console.error('Instantly add error:', e);
    return 'failed';
  }
}
