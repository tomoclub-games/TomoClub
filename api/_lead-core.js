// Shared helpers for the API functions. Files whose names start with "_" are not deployed as their own functions.
//
// Env vars (Vercel > Settings > Environment Variables):
//   SHEET_WEBHOOK      Apps Script Web app URL (data-capture/Code.gs). Every lead and event is saved there, and
//                      Code.gs sends the Slack and email alerts (once per lead).
//   SHEET_SECRET       The same value as the SHEET_SECRET script property in Code.gs. Needed for partial leads and
//                      the /admin dashboard; once it is set in Code.gs, every write must carry it.
//   INSTANTLY_API_KEY  Optional. Instantly API v2 key (leads:create). Only contacts who ticked "Send me occasional
//                      emails" are ever sent to Instantly.
//   INSTANTLY_ROUTES   Optional JSON, intent -> target: {"discovery_request":"list:UUID","build_with_us":"list:UUID",
//                      "guide_download":"campaign:UUID","ebook_download":"campaign:UUID","partial_lead":"list:UUID"}
//   INSTANTLY_DEFAULT_LIST_ID  Optional fallback list for intents not in INSTANTLY_ROUTES.

import crypto from 'node:crypto';

export const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?tomoclub\.org$/,
  /^https:\/\/tomoclub-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];

export const ATTRIBUTION_FIELDS = {
  utm_source: 120, utm_medium: 120, utm_campaign: 120, utm_content: 120, utm_term: 120,
  gclid: 200, fbclid: 200, referrer: 300, landing_page: 300,
};

// Query parameters that could carry a person's details; their values are never stored or sent to analytics.
const PII_PARAMS = /([?&](?:email|e|mail|name|first_name|last_name|fname|lname|phone|tel|mobile)=)[^&#]*/gi;
export const redactUrl = (u) => String(u || '').replace(PII_PARAMS, '$1redacted');

// Removes anything that looks like an email address or a phone number from free text meant for analytics.
export const scrubPII = (t) => String(t || '')
  .replace(/[^\s@<>()]+@[^\s@<>()]+\.[a-z]{2,}/gi, '[email]')
  .replace(/\+?\d[\d\s().-]{7,}\d/g, '[number]');

export const isPhone = (v) => (String(v || '').match(/\d/g) || []).length >= 7 && /^[+\d\s().-]{7,25}$/.test(String(v || '').trim());
export const yes = (v) => v === true || v === 'yes' || v === 'on' || v === 'true';
export const newId = (prefix) => prefix + '-' + crypto.randomBytes(9).toString('base64url');
export const cleanId = (v) => (/^[A-Za-z0-9_-]{8,64}$/.test(String(v || '')) ? String(v) : '');
export const hashId = (prefix, text) => prefix + '-' + crypto.createHash('sha256').update(String(text)).digest('base64url').slice(0, 16);

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

// Best-effort rate limit per warm server instance. bucket keeps each endpoint's count separate.
const hits = new Map();
export function tooMany(ip, limit = 20, windowMs = 10 * 60 * 1000, bucket = '') {
  const now = Date.now();
  const k = bucket + ':' + ip;
  const recent = (hits.get(k) || []).filter((t) => now - t < windowMs);
  recent.push(now);
  hits.set(k, recent);
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
  out.landing_page = redactUrl(out.landing_page);
  out.referrer = redactUrl(out.referrer);
  return out;
}

// Sends one request to the Apps Script collector. Returns its JSON answer, or null on failure.
export async function callSheet(payload, timeoutMs = 9000) {
  const url = process.env.SHEET_WEBHOOK;
  if (!url) { console.error('SHEET_WEBHOOK env var is not set'); return null; }
  try {
    const body = { ...payload };
    if (process.env.SHEET_SECRET) body.secret = process.env.SHEET_SECRET;
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j || j.ok !== true) { console.error('Apps Script refused:', r.status, j && j.error); return null; }
    return j;
  } catch (error) {
    console.error('sheet request error:', error && error.message);
    return null;
  }
}

// Append rows to the Google Sheet through the Apps Script collector.
export async function saveToSheet(rows) {
  return !!(await callSheet({ rows }));
}

// Adds a contact to Instantly. Call it ONLY for people who ticked the marketing-emails box.
// Returns a short status for the sheet ("list_added", "campaign_added", "already_there", "skipped: ...", "error").
export async function pushToInstantly(intent, lead) {
  const key = process.env.INSTANTLY_API_KEY;
  let routes = {};
  try { routes = JSON.parse(process.env.INSTANTLY_ROUTES || '{}'); } catch (e) { console.error('INSTANTLY_ROUTES is not valid JSON'); }
  const target = routes[intent] || (process.env.INSTANTLY_DEFAULT_LIST_ID ? 'list:' + process.env.INSTANTLY_DEFAULT_LIST_ID : '');
  const m = /^(list|campaign):([0-9a-f-]{36})$/i.exec(target || '');
  if (!key || !m) return 'skipped: not configured';
  if (!isEmail(lead.email)) return 'skipped: no email';
  const custom = {};
  Object.entries(lead.custom_variables || {}).forEach(([k, v]) => { if (v !== undefined && v !== '') custom[k] = typeof v === 'string' ? v.slice(0, 300) : v; });
  const body = {
    leads: [{
      email: lead.email,
      first_name: lead.first_name || null,
      last_name: lead.last_name || null,
      company_name: lead.company_name || null,
      job_title: lead.job_title || null,
      phone: lead.phone || null,
      custom_variables: custom,
    }],
    skip_if_in_campaign: m[1].toLowerCase() === 'campaign',
    skip_if_in_list: false,
    idempotency_key: (intent + ':' + lead.email + ':' + new Date().toISOString().slice(0, 13)).slice(0, 128),
  };
  body[m[1].toLowerCase() === 'campaign' ? 'campaign_id' : 'list_id'] = m[2];
  try {
    const r = await fetch('https://api.instantly.ai/api/v2/leads/add', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(8000),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok) { console.error('Instantly add failed:', r.status); return 'error: HTTP ' + r.status; }
    return j && Number(j.leads_uploaded) > 0 ? m[1].toLowerCase() + '_added' : 'already_there';
  } catch (e) {
    console.error('Instantly request error:', e && e.message);
    return 'error';
  }
}

export function splitName(full) {
  const parts = clean(full, 120).split(/\s+/).filter(Boolean);
  return { first_name: parts[0] || '', last_name: parts.slice(1).join(' ') };
}

export function readBody(req) {
  const b = req.body;
  if (b && typeof b === 'object') return b;
  if (typeof b === 'string') { try { return JSON.parse(b); } catch (e) { return {}; } }
  return {};
}
