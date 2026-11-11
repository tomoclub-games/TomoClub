// Vercel serverless function: POST /api/collect
// The parents site sends form rows here ({ rows: [{ sheet, data }] }) and this forwards them to the
// Google Apps Script collector (data-capture/Code.gs), so the Apps Script URL stays out of the page source.
// "Trial bookings" rows are not accepted from the browser: api/book.js writes those after Calendly confirms.
// "Enrolments" rows are accepted only as payment_cancelled (the parent closed the checkout window): paid and
// failed rows are written by api/verify.js and api/razorpay-webhook.js after Razorpay confirms.
//
// Env var:
//   SHEET_WEBHOOK   the Apps Script Web app URL (ends in /exec)

const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?tomoclub\.org$/,
  /^https:\/\/tomoclub-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];
const SHEETS = ['Leads', 'Enrolments', 'Events'];
const MAX_ROWS = 25;

// Best-effort limit per warm server instance.
const hits = new Map();
function tooMany(ip) {
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter((t) => now - t < 10 * 60 * 1000);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 500) hits.clear();
  return recent.length > 120;
}

function cleanValue(v) {
  if (v === undefined || v === null) return '';
  if (typeof v === 'number' || typeof v === 'boolean') return v;
  return (typeof v === 'object' ? JSON.stringify(v) : String(v)).replace(/[\u0000-\u001f]/g, ' ').slice(0, 500);
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }
  if (!ALLOWED_ORIGINS.some((re) => re.test(req.headers.origin || ''))) {
    return res.status(403).json({ ok: false, error: 'Not allowed' });
  }

  const webhook = process.env.SHEET_WEBHOOK;
  if (!webhook) {
    console.error('SHEET_WEBHOOK env var is not set');
    return res.status(500).json({ ok: false, error: 'Not configured' });
  }

  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  if (tooMany(ip)) return res.status(429).json({ ok: false, error: 'Too many requests' });

  // The browser sends text/plain (so sendBeacon works while a page closes); accept JSON too.
  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch (e) { body = null; }
  }
  const input = body && Array.isArray(body.rows) ? body.rows : null;
  if (!input) return res.status(400).json({ ok: false, error: 'No rows' });

  // The visitor's country as seen by Vercel (an IP lookup, not something the browser can set).
  const detected = String(req.headers['x-vercel-ip-country'] || '').toUpperCase();
  const detectedCountry = /^[A-Z]{2}$/.test(detected) ? detected : '';

  const rows = input.slice(0, MAX_ROWS)
    .filter((r) => r && SHEETS.includes(r.sheet) && r.data && typeof r.data === 'object')
    .filter((r) => r.sheet !== 'Enrolments' || r.data.status === 'payment_cancelled')
    .map((r) => {
      const data = {};
      Object.keys(r.data).slice(0, 40).forEach((k) => { data[String(k).slice(0, 40)] = cleanValue(r.data[k]); });
      data.detected_country = detectedCountry;
      if (r.sheet === 'Enrolments') { data.transaction_id = ''; data.order_id = ''; } // never a payment from the browser
      return { sheet: r.sheet, data };
    });
  if (!rows.length) return res.status(400).json({ ok: false, error: 'No valid rows' });

  try {
    // Apps Script always answers through a redirect, so redirects must be followed (fetch does by default).
    const upstream = await fetch(webhook, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ rows }),
      signal: AbortSignal.timeout(8000),
    });
    const result = await upstream.json().catch(() => null);
    if (!upstream.ok || !result || result.ok !== true) {
      console.error('Apps Script rejected rows:', upstream.status, JSON.stringify(result));
      return res.status(502).json({ ok: false, error: 'Could not save' });
    }
    return res.status(200).json({ ok: true, saved: rows.length });
  } catch (error) {
    console.error('collect proxy error:', error);
    return res.status(502).json({ ok: false, error: 'Could not reach the sheet' });
  }
}
