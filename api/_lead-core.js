import crypto from 'node:crypto';

// Shared helpers for the B2B lead endpoints (api/lead.js, api/signup.js, api/event.js).
// Files whose names start with "_" are not deployed as their own Vercel functions.
//
// Env vars (Vercel > Settings > Environment Variables):
//   SHEET_WEBHOOK          Apps Script Web app URL (data-capture/Code.gs). Every lead and event is saved here first.
//   INSTANTLY_API_KEY      Instantly API v2 key with the leads:create scope.
//   INSTANTLY_ROUTES       JSON map from intent to an Instantly target, for example
//                          {"discovery_request":"list:UUID","call_booked":"list:UUID","guide_download":"campaign:UUID",
//                           "ebook_download":"campaign:UUID","newsletter":"campaign:UUID","high_intent":"campaign:UUID"}
//                          "list:" adds the contact to a lead list (no emails go out). "campaign:" adds them to a
//                          campaign, so its sequence starts. Intents not in the map go to INSTANTLY_DEFAULT_LIST_ID.
//   INSTANTLY_DEFAULT_LIST_ID  Fallback lead list (UUID). If neither is set, Instantly is skipped and only the Sheet is written.
//   TURNSTILE_SECRET_KEY   Optional. When set, every form must carry a valid Cloudflare Turnstile token.

export const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?tomoclub\.org$/,
  /^https:\/\/tomoclub-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];

export const ATTRIBUTION_FIELDS = {
  utm_source: 120, utm_medium: 120, utm_campaign: 120, utm_content: 120, utm_term: 120,
  gclid: 200, fbclid: 200, li_fat_id: 200, referrer: 300, landing_page: 300,
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

// Spam checks. The page adds two hidden fields to every form (assets/js/b2b-events.js):
//   hp_company_website  a honeypot people never see; bots fill it in
//   form_loaded_at      when the form appeared; a real person takes more than a few seconds
// Returns '' when the submission looks human, or a short reason when it does not.
export async function spamReason(b, ip) {
  if (clean(b.hp_company_website)) return 'honeypot';
  const loaded = Number(b.form_loaded_at);
  if (loaded && Date.now() - loaded < 3000) return 'too_fast';
  const text = [b.goal, b.message, b.name, b.firstName].map((x) => clean(x, 3000)).join(' ');
  if ((text.match(/https?:\/\//gi) || []).length > 2) return 'links';
  const secret = process.env.TURNSTILE_SECRET_KEY;
  if (secret) {
    const token = clean(b['cf-turnstile-response'], 2048);
    if (!token) return 'no_turnstile';
    try {
      const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        body: new URLSearchParams({ secret, response: token, remoteip: ip }),
        signal: AbortSignal.timeout(6000),
      });
      const j = await r.json().catch(() => null);
      if (!j || j.success !== true) return 'turnstile_failed';
    } catch (e) {
      console.error('Turnstile check failed to run:', e);
      // Fail open: a Cloudflare outage should not lose real leads. Honeypot and timing still apply.
    }
  }
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

function routeFor(intent) {
  let routes = {};
  try { routes = JSON.parse(process.env.INSTANTLY_ROUTES || '{}'); } catch (e) { console.error('INSTANTLY_ROUTES is not valid JSON'); }
  const target = routes[intent] || (process.env.INSTANTLY_DEFAULT_LIST_ID ? 'list:' + process.env.INSTANTLY_DEFAULT_LIST_ID : '');
  const m = /^(list|campaign):([0-9a-f-]{36})$/i.exec(target || '');
  return m ? { kind: m[1].toLowerCase(), id: m[2] } : null;
}

// Add one contact to Instantly (POST /api/v2/leads/add). Returns { ok, status, detail }.
// Custom variable values must be strings, numbers, booleans or null.
export async function pushToInstantly(intent, lead) {
  const key = process.env.INSTANTLY_API_KEY;
  const route = routeFor(intent);
  if (!key || !route) return { ok: false, status: 'skipped', detail: !key ? 'no INSTANTLY_API_KEY' : 'no route for ' + intent };
  if (!isEmail(lead.email)) return { ok: false, status: 'skipped', detail: 'no email' };

  const custom = {};
  Object.entries(lead.custom_variables || {}).forEach(([k, v]) => {
    if (v === undefined || v === '') return;
    custom[k] = typeof v === 'string' ? v.slice(0, 500) : v;
  });
  const item = {
    email: lead.email,
    first_name: lead.first_name || null,
    last_name: lead.last_name || null,
    company_name: lead.company_name || null,
    job_title: lead.job_title || null,
    website: lead.website || null,
    custom_variables: custom,
  };
  const body = {
    leads: [item],
    // A person is only ever in one campaign at a time, so two sequences never email them together.
    skip_if_in_campaign: route.kind === 'campaign',
    skip_if_in_list: false,
    verify_leads_on_import: false,
    idempotency_key: (intent + ':' + lead.email + ':' + new Date().toISOString().slice(0, 13)).slice(0, 128),
  };
  body[route.kind === 'campaign' ? 'campaign_id' : 'list_id'] = route.id;
  try {
    const r = await fetch('https://api.instantly.ai/api/v2/leads/add', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(8000),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok) {
      console.error('Instantly add failed:', r.status, JSON.stringify(j));
      return { ok: false, status: 'error', detail: 'HTTP ' + r.status };
    }
    const added = j && Number(j.leads_uploaded) > 0;
    return { ok: true, status: added ? route.kind + '_added' : 'already_there', detail: j ? 'skipped ' + (j.skipped_count || 0) : '' };
  } catch (e) {
    console.error('Instantly request error:', e);
    return { ok: false, status: 'error', detail: String(e).slice(0, 120) };
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

// A signed token for a contact who has submitted a form, so later activity from the same browser can be tied to
// them (api/event.js) without letting anyone add an arbitrary email address to a sequence.
//   LEAD_TOKEN_SECRET  any long random string. Without it no tokens are issued and activity stays anonymous.
// scope "hot": the person asked us to talk (discovery form, booked call). A co-founder follows up by hand, so
//   later site activity is logged but never starts an automated sequence.
// scope "nurture": the person downloaded a guide or the ebook; high-intent activity may route them to a campaign.
export function signLead(email, scope = 'nurture') {
  const secret = process.env.LEAD_TOKEN_SECRET;
  if (!secret || !isEmail(email)) return '';
  return crypto.createHmac('sha256', secret).update(scope + '|' + email.toLowerCase()).digest('base64url').slice(0, 32);
}

export function verifyLead(email, token, scope = 'nurture') {
  const good = signLead(email, scope);
  if (!good || typeof token !== 'string' || token.length !== good.length) return false;
  return crypto.timingSafeEqual(Buffer.from(good), Buffer.from(token));
}
