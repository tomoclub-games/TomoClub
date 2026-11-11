// Vercel serverless function: POST /api/order
// Creates a Razorpay order for the both-programs plan (first month) and returns what the checkout window needs.
// The amount and currency are decided here, never by the browser. The enrolment details ride along as order
// notes, so the Sheet row written after payment (api/verify.js or api/razorpay-webhook.js) comes from Razorpay.
//
// Env vars: RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET (test keys on Preview, live keys on Production).

import { originAllowed, clean, clientIp, detectedCountry, makeLimiter, jsonBody, razorpay, razorpayKeys, packAttr } from './_lib/common.js';
import { BOTH_PRICES, currencyForCountry, toMinor } from './_lib/pricing.js';

const LS = ['Mon 5:00 PM', 'Wed 6:00 PM', 'Sat 11:30 AM'];
const AI = ['Tue 6:00 PM', 'Thu 5:00 PM', 'Sat 4:00 PM'];
const tooMany = makeLimiter(10, 10 * 60 * 1000);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Method not allowed' });
  if (!originAllowed(req)) return res.status(403).json({ ok: false, error: 'Not allowed' });
  res.setHeader('Cache-Control', 'no-store');

  const keys = razorpayKeys();
  if (!keys) {
    console.error('RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET env var is not set');
    return res.status(500).json({ ok: false, code: 'not_configured', error: 'Payments are not set up yet' });
  }
  if (tooMany(clientIp(req))) return res.status(429).json({ ok: false, code: 'too_many', error: 'Too many attempts. Please try again later.' });

  const b = jsonBody(req);
  const name = clean(b.name, 120);
  const email = clean(b.email, 200);
  const whatsapp = clean(b.whatsapp, 30);
  const country = clean(b.country, 60);
  const city = clean(b.city, 80);
  const grade = parseInt(b.grade, 10);
  const ls = clean(b.life_skills_batch, 30);
  const ai = clean(b.ai_lab_batch, 30);

  const problems = [];
  if (!name) problems.push('name');
  if (!/^\S+@\S+\.\S+$/.test(email)) problems.push('email');
  if (!country) problems.push('country');
  if (!city) problems.push('city');
  if (!(grade >= 6 && grade <= 12)) problems.push('grade');
  if (!LS.includes(ls)) problems.push('life_skills_batch');
  if (!AI.includes(ai)) problems.push('ai_lab_batch');
  if (b.terms !== true) problems.push('terms');
  if (problems.length) return res.status(400).json({ ok: false, code: 'invalid', error: 'Please check: ' + problems.join(', ') });

  // Currency follows where the visitor is (Vercel's IP lookup). Only if Vercel cannot tell is the
  // currency the page showed accepted, and only one of ours. The amount always comes from BOTH_PRICES.
  const detected = detectedCountry(req);
  const asked = clean(b.currency, 3).toUpperCase();
  const currency = currencyForCountry(detected) || (BOTH_PRICES[asked] ? asked : 'INR');
  const amount = BOTH_PRICES[currency];

  const ctx = b.context && typeof b.context === 'object' ? b.context : {};
  const c = (k, max) => clean(ctx[k], max || 256);
  const notes = {
    parent_name: name, email, whatsapp, country, city, grade: String(grade),
    life_skills_batch: ls, ai_lab_batch: ai, whatsapp_reminders: b.whatsapp_reminders === 'yes' ? 'yes' : 'no',
    session_id: c('session_id', 60), visitor_id: c('visitor_id', 60), detected_country: detected, language: c('language', 20),
    attr: packAttr({ us: c('utm_source'), um: c('utm_medium'), uc: c('utm_campaign'), ut: c('utm_content'), uk: c('utm_term'), g: c('gclid'), f: c('fbclid'), r: c('referrer'), l: c('landing_page') }),
  };

  try {
    const r = await razorpay('POST', '/orders', {
      amount: toMinor(amount),
      currency,
      receipt: 'both-' + Date.now().toString(36),
      notes,
    });
    if (!r.ok || !r.body || !r.body.id) {
      console.error('Razorpay order failed:', r.status, JSON.stringify(r.body));
      return res.status(502).json({ ok: false, code: 'order_failed', error: 'Could not start the payment' });
    }
    return res.status(200).json({ ok: true, key_id: keys.id, order_id: r.body.id, amount: r.body.amount, currency: r.body.currency, display_amount: amount });
  } catch (error) {
    console.error('order error:', error);
    return res.status(502).json({ ok: false, code: 'order_failed', error: 'Could not reach the payment service' });
  }
}
