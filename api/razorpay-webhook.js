// Vercel serverless function: POST /api/razorpay-webhook
// Razorpay calls this for every payment, even when the parent closed the page before api/verify.js ran.
//   payment.captured -> "paid" Enrolments row (the sheet script skips it if api/verify.js already wrote it)
//   payment.failed   -> "payment_failed" Enrolments row
// Set up in the Razorpay dashboard (Settings > Webhooks): URL https://www.tomoclub.org/api/razorpay-webhook,
// events payment.captured and payment.failed, and a secret, which goes in Vercel as RAZORPAY_WEBHOOK_SECRET.
// Answers 500 when the row could not be saved, so Razorpay retries.
//
// Env vars: RAZORPAY_WEBHOOK_SECRET, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, SHEET_WEBHOOK.

import crypto from 'node:crypto';
import { razorpay, saveToSheet, enrolmentRow } from './_lib/common.js';

// The signature is over the exact bytes Razorpay sent, so read the raw body ourselves.
export const config = { api: { bodyParser: false } };

async function rawBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  return Buffer.concat(chunks).toString('utf8');
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false });
  const secret = process.env.RAZORPAY_WEBHOOK_SECRET;
  if (!secret) { console.error('RAZORPAY_WEBHOOK_SECRET env var is not set'); return res.status(500).json({ ok: false }); }

  const raw = await rawBody(req);
  const given = String(req.headers['x-razorpay-signature'] || '');
  const expected = crypto.createHmac('sha256', secret).update(raw).digest('hex');
  const a = Buffer.from(expected), b = Buffer.from(given);
  if (!raw || a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
    console.error('Webhook signature check failed (body length ' + raw.length + ')');
    return res.status(400).json({ ok: false });
  }

  let event;
  try { event = JSON.parse(raw); } catch (e) { return res.status(400).json({ ok: false }); }
  const payment = event && event.payload && event.payload.payment && event.payload.payment.entity;
  const kind = event && event.event;
  if (!payment || (kind !== 'payment.captured' && kind !== 'payment.failed')) return res.status(200).json({ ok: true, ignored: true });
  if (!payment.order_id) return res.status(200).json({ ok: true, ignored: true }); // not from our checkout

  const o = await razorpay('GET', '/orders/' + payment.order_id).catch(() => ({ ok: false }));
  if (!o.ok || !o.body) { console.error('Webhook: order lookup failed', payment.order_id); return res.status(500).json({ ok: false }); }
  const order = o.body;
  // Only our both-programs orders carry these notes; anything else (payment links, other tools) is left alone.
  if (!order.notes || !order.notes.life_skills_batch) return res.status(200).json({ ok: true, ignored: true });

  const row = kind === 'payment.captured'
    ? enrolmentRow(order, payment, 'paid')
    : enrolmentRow(order, payment, 'payment_failed', { failure_reason: [payment.error_reason, payment.error_description].filter(Boolean).join(': ').slice(0, 300) });
  const saved = await saveToSheet([{ sheet: 'Enrolments', data: row }]);
  if (!saved) return res.status(500).json({ ok: false });
  return res.status(200).json({ ok: true });
}
