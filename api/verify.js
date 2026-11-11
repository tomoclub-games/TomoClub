// Vercel serverless function: POST /api/verify
// Called by the page after Razorpay's checkout says the payment succeeded. Checks Razorpay's signature,
// confirms the payment with Razorpay (amount, currency, status), then writes the "paid" Enrolments row
// (the sheet script sends the Slack alert). api/razorpay-webhook.js writes the same row if this never runs,
// and the sheet script skips a second row for the same transaction.
//
// Env vars: RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, SHEET_WEBHOOK.

import crypto from 'node:crypto';
import { originAllowed, clean, clientIp, makeLimiter, jsonBody, razorpay, razorpayKeys, saveToSheet, enrolmentRow } from './_lib/common.js';

const tooMany = makeLimiter(20, 10 * 60 * 1000);

function signatureOk(orderId, paymentId, signature, secret) {
  const expected = crypto.createHmac('sha256', secret).update(orderId + '|' + paymentId).digest('hex');
  const a = Buffer.from(expected), b = Buffer.from(String(signature));
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Method not allowed' });
  if (!originAllowed(req)) return res.status(403).json({ ok: false, error: 'Not allowed' });
  res.setHeader('Cache-Control', 'no-store');

  const keys = razorpayKeys();
  if (!keys) return res.status(500).json({ ok: false, code: 'not_configured', error: 'Payments are not set up yet' });
  if (tooMany(clientIp(req))) return res.status(429).json({ ok: false, code: 'too_many', error: 'Too many attempts' });

  const b = jsonBody(req);
  const orderId = clean(b.razorpay_order_id, 40);
  const paymentId = clean(b.razorpay_payment_id, 40);
  const signature = clean(b.razorpay_signature, 128);
  if (!/^order_\w+$/.test(orderId) || !/^pay_\w+$/.test(paymentId) || !signatureOk(orderId, paymentId, signature, keys.secret)) {
    console.error('Payment signature check failed:', orderId, paymentId);
    return res.status(400).json({ ok: false, code: 'bad_signature', error: 'Payment could not be confirmed' });
  }

  try {
    const [o, p] = await Promise.all([razorpay('GET', '/orders/' + orderId), razorpay('GET', '/payments/' + paymentId)]);
    if (!o.ok || !p.ok) {
      console.error('Razorpay lookup failed:', o.status, p.status, JSON.stringify(o.body), JSON.stringify(p.body));
      return res.status(502).json({ ok: false, code: 'lookup_failed', error: 'Could not confirm the payment yet' });
    }
    let order = o.body, payment = p.body;
    if (payment.order_id !== order.id || payment.amount !== order.amount || payment.currency !== order.currency) {
      console.error('Payment does not match its order:', JSON.stringify({ order: order.id, payment: payment.id }));
      return res.status(400).json({ ok: false, code: 'mismatch', error: 'Payment could not be confirmed' });
    }
    // Auto-capture is on in the dashboard; capture here as well in case the payment is only authorised.
    if (payment.status === 'authorized') {
      const cap = await razorpay('POST', '/payments/' + paymentId + '/capture', { amount: payment.amount, currency: payment.currency });
      if (cap.ok && cap.body) payment = cap.body;
      else console.error('Capture failed (auto-capture may still take it):', cap.status, JSON.stringify(cap.body));
    }
    if (payment.status !== 'captured' && payment.status !== 'authorized') {
      return res.status(400).json({ ok: false, code: 'not_paid', error: 'Payment did not go through' });
    }

    const saved = await saveToSheet([{ sheet: 'Enrolments', data: enrolmentRow(order, payment, 'paid') }]);
    if (!saved) console.error('Payment confirmed but the sheet row was not saved (the webhook will retry):', paymentId);
    return res.status(200).json({ ok: true, payment_id: payment.id, amount: payment.amount / 100, currency: payment.currency, method: payment.method || '' });
  } catch (error) {
    console.error('verify error:', error);
    return res.status(502).json({ ok: false, code: 'lookup_failed', error: 'Could not confirm the payment yet' });
  }
}
