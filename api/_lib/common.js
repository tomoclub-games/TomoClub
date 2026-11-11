// Shared helpers for the payment functions (api/order.js, api/verify.js, api/razorpay-webhook.js).
// Files in api/_lib are shared code, not routes.

export const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?tomoclub\.org$/,
  /^https:\/\/tomoclub-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];
export const originAllowed = (req) => ALLOWED_ORIGINS.some((re) => re.test(req.headers.origin || ''));

export const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);

export function clientIp(req) {
  return String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
}

export function detectedCountry(req) {
  const c = String(req.headers['x-vercel-ip-country'] || '').toUpperCase(); // set by Vercel, not by the browser
  return /^[A-Z]{2}$/.test(c) ? c : '';
}

// Best-effort rate limit per warm server instance.
export function makeLimiter(max, windowMs) {
  const hits = new Map();
  return function tooMany(key) {
    const now = Date.now();
    const recent = (hits.get(key) || []).filter((t) => now - t < windowMs);
    recent.push(now);
    hits.set(key, recent);
    if (hits.size > 500) hits.clear();
    return recent.length > max;
  };
}

// The JSON body, whether Vercel parsed it already or not.
export function jsonBody(req) {
  let b = req.body;
  if (typeof b === 'string') { try { b = JSON.parse(b); } catch (e) { b = null; } }
  return b && typeof b === 'object' ? b : {};
}

// Append rows to the Google Sheet through the Apps Script collector (data-capture/Code.gs).
export async function saveToSheet(rows) {
  const url = process.env.SHEET_WEBHOOK;
  if (!url) { console.error('SHEET_WEBHOOK env var is not set'); return false; }
  try {
    // Apps Script answers through a redirect, which fetch follows; the JSON body says whether it worked.
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: JSON.stringify({ rows }), signal: AbortSignal.timeout(8000) });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j || j.ok !== true) { console.error('Apps Script rejected the row:', r.status, JSON.stringify(j)); return false; }
    return true;
  } catch (error) {
    console.error('sheet write error:', error);
    return false;
  }
}

// ---------- Razorpay ----------
// Env vars: RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET (test keys on Preview, live keys on Production).
export function razorpayKeys() {
  const id = process.env.RAZORPAY_KEY_ID, secret = process.env.RAZORPAY_KEY_SECRET;
  return id && secret ? { id, secret } : null;
}

// Calls the Razorpay REST API. Returns { ok, status, body }.
export async function razorpay(method, path, payload) {
  const keys = razorpayKeys();
  if (!keys) return { ok: false, status: 0, body: { error: 'not configured' } };
  const r = await fetch('https://api.razorpay.com/v1' + path, {
    method,
    headers: { Authorization: 'Basic ' + Buffer.from(keys.id + ':' + keys.secret).toString('base64'), 'Content-Type': 'application/json' },
    body: payload ? JSON.stringify(payload) : undefined,
    signal: AbortSignal.timeout(10000),
  });
  const body = await r.json().catch(() => null);
  return { ok: r.ok, status: r.status, body };
}

// Order notes carry the enrolment details (Razorpay allows 15 notes of up to 256 characters each).
// The row written after payment is built from these notes, never from what the browser says later.
export function enrolmentRow(order, payment, status, extra) {
  const n = (order && order.notes) || {};
  let attr = {};
  try { attr = JSON.parse(n.attr || '{}'); } catch (e) { attr = {}; }
  const amount = order ? order.amount / 100 : '';
  const currency = order ? order.currency : '';
  return {
    timestamp: new Date().toISOString(),
    status,
    page: 'both-programs',
    program: 'bundle',
    parent_name: n.parent_name || '', email: n.email || '', whatsapp: n.whatsapp || '',
    country: n.country || '', city: n.city || '', grade: n.grade || '',
    life_skills_batch: n.life_skills_batch || '', ai_lab_batch: n.ai_lab_batch || '',
    payment_method: (payment && payment.method) || '',
    amount,
    amount_inr: currency === 'INR' ? amount : '',
    currency,
    transaction_id: (payment && payment.id) || '',
    order_id: (order && order.id) || '',
    whatsapp_reminders: n.whatsapp_reminders || '',
    session_id: n.session_id || '', visitor_id: n.visitor_id || '',
    utm_source: attr.us || '', utm_medium: attr.um || '', utm_campaign: attr.uc || '', utm_content: attr.ut || '', utm_term: attr.uk || '',
    gclid: attr.g || '', fbclid: attr.f || '', referrer: attr.r || '', landing_page: attr.l || '',
    detected_country: n.detected_country || '', language: n.language || '',
    ...(extra || {}),
  };
}

// Packs attribution into one note of at most 256 characters, shortening the longest values first.
export function packAttr(obj) {
  const o = {};
  Object.keys(obj).forEach((k) => { if (obj[k]) o[k] = String(obj[k]); });
  let s = JSON.stringify(o);
  while (s.length > 256) {
    const longest = Object.keys(o).sort((a, b) => o[b].length - o[a].length)[0];
    if (!longest) break;
    const cut = Math.max(0, o[longest].length - (s.length - 256) - 1);
    if (cut === 0) delete o[longest]; else o[longest] = o[longest].slice(0, cut);
    s = JSON.stringify(o);
  }
  return s;
}
