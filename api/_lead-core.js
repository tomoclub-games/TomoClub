// Shared helpers for api/lead.js. Files whose names start with "_" are not deployed as their own Vercel functions.
//
// Env vars (Vercel > Settings > Environment Variables):
//   SHEET_WEBHOOK   Apps Script Web app URL (data-capture/Code.gs). Every lead is saved here; Code.gs posts the Slack alert.

export const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?tomoclub\.org$/,
  /^https:\/\/tomoclub-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];

export const ATTRIBUTION_FIELDS = {
  utm_source: 120, utm_medium: 120, utm_campaign: 120, utm_content: 120, utm_term: 120,
  gclid: 200, fbclid: 200, referrer: 300, landing_page: 300,
};

export const clean = (v, max = 300) =>
  String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);

export const isEmail = (v) => /^[^\s@]{1,64}@[^\s@]{1,190}\.[a-z]{2,}$/i.test(v || '');

const FREE_MAIL = /@(gmail|yahoo|hotmail|outlook|live|aol|icloud|me|proton(mail)?|gmx|mail|yandex|zoho)\./i;
export const emailType = (email) => (FREE_MAIL.test(email) ? 'personal' : 'work');

export function originAllowed(req) {
  return ALLOWED_ORIGINS.some((re) => re.test(req.headers.origin || ''));
}

export function clientIp(req) {
  return String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
}

// Best-effort rate limit per warm server instance.
const hits = new Map();
export function tooMany(ip, limit = 20, windowMs = 10 * 60 * 1000) {
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter((t) => now - t < windowMs);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 1000) hits.clear();
  return recent.length > limit;
}

// Spam checks. The form carries two hidden fields:
//   hp_company_website  a honeypot people never see; bots fill it in
//   form_loaded_at      when the form appeared; a real person takes more than a few seconds
// Returns '' when the submission looks human, or a short reason when it does not.
export function spamReason(b) {
  if (clean(b.hp_company_website)) return 'honeypot';
  const loaded = Number(b.form_loaded_at);
  if (loaded && Date.now() - loaded < 3000) return 'too_fast';
  const text = [b.goal, b.message, b.name].map((x) => clean(x, 3000)).join(' ');
  if ((text.match(/https?:\/\//gi) || []).length > 2) return 'links';
  return '';
}

export function attribution(b) {
  const out = {};
  Object.keys(ATTRIBUTION_FIELDS).forEach((k) => { out[k] = clean(b[k], ATTRIBUTION_FIELDS[k]); });
  return out;
}

// Append rows to the Google Sheet through the Apps Script collector.
export async function saveToSheet(rows) {
  const url = process.env.SHEET_WEBHOOK;
  if (!url) { console.error('SHEET_WEBHOOK env var is not set'); return false; }
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ rows }),
      signal: AbortSignal.timeout(8000),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j || j.ok !== true) { console.error('Apps Script rejected the rows:', r.status, JSON.stringify(j)); return false; }
    return true;
  } catch (error) {
    console.error('sheet write error:', error);
    return false;
  }
}

export function readBody(req) {
  const b = req.body;
  if (b && typeof b === 'object') return b;
  if (typeof b === 'string') { try { return JSON.parse(b); } catch (e) { return {}; } }
  return {};
}
