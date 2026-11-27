// Shared helpers for api/lead.js, api/signup.js and api/call.js. Files whose names start with "_" are not deployed as their own Vercel functions.
//
// Env vars (Vercel > Settings > Environment Variables):
//   SHEET_WEBHOOK   Apps Script Web app URL (data-capture/Code.gs). Every lead is saved here; Code.gs posts the Slack alert.
//   INSTANTLY_API_KEY             Instantly API v2 key with the leads:create scope (key name: tomoclub-website-vercel).
//   INSTANTLY_LIST_HOME_FORM      Instantly list for the home page form.
//   INSTANTLY_LIST_BOOKED_CALLS   Instantly list for booked calls (booking pop-up and Calendly fallback).
//   INSTANTLY_LIST_EBOOK          Instantly list for e-book requests.
//   INSTANTLY_LIST_TOOLKITS       Instantly list for toolkit downloads.
// Every real lead is added to its form's Instantly list. A list does not send emails by itself.
// Nothing is sent to Instantly when the key or the form's list ID is missing.

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

// Disposable inboxes that bots and drive-by sign-ups use.
const THROWAWAY = /@(?:[^@]*\.)?(mailinator|guerrillamail|10minutemail|temp-?mail|yopmail|trashmail|sharklasers)\.[a-z.]+$/i;
export const isThrowaway = (email) => THROWAWAY.test(email || '');

// One ID per form fill, made in the browser. Code.gs uses it to drop a second copy of the same submission.
export const submissionId = (b) => String((b && b.submission_id) || '').replace(/[^\w-]/g, '').slice(0, 64);

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
  const text = [b.goal, b.message, b.name, b.firstName].map((x) => clean(x, 3000)).join(' ');
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

// Add one contact to an Instantly list. `list` is the env var name, e.g. 'INSTANTLY_LIST_HOME_FORM'.
// Returns 'added', 'already_there', 'not_configured' or 'failed'. Never throws: a form must not fail because of Instantly.
export async function addToInstantly(list, lead) {
  const key = process.env.INSTANTLY_API_KEY;
  const listId = String(process.env[list] || '').trim();
  if (!key || !/^[0-9a-f-]{36}$/i.test(listId)) return 'not_configured';
  if (!isEmail(lead.email)) return 'failed';
  const [first, ...rest] = clean(lead.name, 120).split(/\s+/);
  const custom = {};
  Object.entries(lead.custom || {}).forEach(([k, v]) => { const s = clean(v, 500); if (s) custom[k] = s; });
  try {
    const r = await fetch('https://api.instantly.ai/api/v2/leads/add', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        list_id: listId,
        // false lets one person be in several lists (e.g. downloaded a toolkit, then booked a call): true skips anyone
        // already in ANY list. Instantly still adds the same person to the same list only once (checked 27 Nov 2026).
        skip_if_in_list: false,
        leads: [{
          email: lead.email.toLowerCase(),
          first_name: first || null,
          last_name: rest.join(' ') || null,
          company_name: clean(lead.company, 160) || null,
          custom_variables: custom,
        }],
      }),
      signal: AbortSignal.timeout(8000),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j) { console.error('Instantly add failed:', list, r.status, JSON.stringify(j)); return 'failed'; }
    return Number(j.leads_uploaded) > 0 ? 'added' : 'already_there';
  } catch (error) {
    console.error('Instantly request error:', list, error && error.message);
    return 'failed';
  }
}

export function readBody(req) {
  const b = req.body;
  if (b && typeof b === 'object') return b;
  if (typeof b === 'string') { try { return JSON.parse(b); } catch (e) { return {}; } }
  return {};
}
