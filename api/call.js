// Vercel serverless function: the "Book a 20-minute call" pop-up (assets/js/calendly.js).
//   GET  /api/call  -> { ok, slots: [ISO start times], minutes }   open times for the next 4 weeks, live from Calendly
//   POST /api/call  -> { ok, start }                                 books the call in Calendly
// Calendly sends the invite, the meeting link and the reminder emails, exactly as a booking on the Calendly page.
// A confirmed booking is saved as a "call_booked" row in the "School leads" tab (Code.gs posts the Slack alert).
// A booking that fails for any reason other than "time just taken" is saved as "call_failed", so the team can follow up.
//
// Env vars: CALENDLY_TOKEN (see _calendly.js) and SHEET_WEBHOOK (see _lead-core.js).

import { originAllowed, clientIp, tooMany, spamReason, clean, isEmail, isThrowaway, emailType, attribution, saveToSheet, readBody } from './_lead-core.js';
import { callEventType, availableTimes, createInvitee, locationFor, buildAnswers } from './_calendly.js';

const DAYS = 28;

async function slots(req, res, token) {
  try {
    const ev = await callEventType(token);
    const list = await availableTimes(token, ev.uri, DAYS);
    // Short cache: protects the Calendly rate limit. A time taken in the meantime is caught when booking.
    res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=60');
    return res.status(200).json({ ok: true, slots: list, minutes: ev.duration || 20 });
  } catch (error) {
    console.error('call slots error:', error);
    return res.status(502).json({ ok: false, error: 'Could not load available times' });
  }
}

async function book(req, res, token) {
  if (!originAllowed(req)) return res.status(403).json({ ok: false, error: 'Not allowed' });
  if (tooMany(clientIp(req), 6)) {
    return res.status(429).json({ ok: false, code: 'too_many', error: 'Too many attempts. Please try again later.' });
  }
  const b = readBody(req);
  // Honeypot and link checks only: a visitor told "booked" when nothing was booked would be the worst outcome,
  // so the too-fast check (which a quick visitor with autofill could trip) is not used here.
  const reason = spamReason({ ...b, form_loaded_at: 0 });
  if (reason) {
    console.warn('call booking rejected as spam:', reason);
    return res.status(200).json({ ok: true });
  }

  const name = clean(b.name, 120);
  const email = clean(b.email, 200).toLowerCase();
  const why = clean(b.reason, 2000);
  const timezone = clean(b.timezone, 60) || 'UTC';
  const guests = (Array.isArray(b.guests) ? b.guests : String(b.guests || '').split(/[\s,;]+/))
    .map((g) => clean(g, 200).toLowerCase()).filter(Boolean);
  const startMs = Date.parse(b.start);

  const problems = [];
  if (!name) problems.push('name');
  if (!isEmail(email)) problems.push('email');
  if (!why) problems.push('reason for the meeting');
  if (guests.length > 10 || guests.some((g) => !isEmail(g))) problems.push('guest emails');
  if (!(startMs > Date.now())) problems.push('time');
  if (problems.length) return res.status(400).json({ ok: false, code: 'invalid', error: 'Please check: ' + problems.join(', ') + '.' });
  if (isThrowaway(email)) return res.status(400).json({ ok: false, code: 'invalid', error: 'Please use a permanent email address.' });
  const startIso = new Date(startMs).toISOString();

  const row = (type, message, extra) => ({
    timestamp: new Date().toISOString(), type, name, email, email_type: emailType(email), organization: '', role: '', state: '',
    offer_interest: '', message, meeting_start: startIso, page: clean(b.page, 120), ...attribution(b), ...(extra || {}),
  });
  const said = why + (guests.length ? ' | Guests: ' + guests.join(', ') : '');
  async function saveFailure(code) {
    const ok = await saveToSheet([{ sheet: 'School leads', data: row('call_failed', 'Booking did not go through (' + code + '). ' + said, { submission_id: clean(b.submission_id, 64).replace(/[^\w-]/g, '') }) }]);
    if (!ok) console.error('Failed call booking could not be saved to the sheet:', code, email);
  }

  let ev;
  try {
    ev = await callEventType(token);
  } catch (error) {
    console.error('call event lookup error:', error);
    await saveFailure('calendly_unreachable');
    return res.status(502).json({ ok: false, code: 'booking_failed', error: 'Could not reach the booking service' });
  }

  const payload = { event_type: ev.uri, start_time: startIso, invitee: { name, email, timezone } };
  const location = locationFor(ev);
  if (location) payload.location = location;
  const answers = buildAnswers(ev, { reason: why });
  if (answers.length) payload.questions_and_answers = answers;
  if (guests.length) payload.event_guests = guests;
  const tracking = {};
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach((k) => { const v = clean(b[k], 120); if (v) tracking[k] = v; });
  if (Object.keys(tracking).length) payload.tracking = tracking;

  try {
    const up = await createInvitee(token, payload);
    if (up.status === 201 && up.body && up.body.resource) {
      const invitee = String(up.body.resource.uri || '');
      const saved = await saveToSheet([{ sheet: 'School leads', data: row('call_booked', said, { submission_id: invitee.split('/').pop().replace(/[^\w-]/g, '').slice(0, 64) }) }]);
      if (!saved) console.error('Call booked in Calendly but the sheet row was not saved:', invitee);
      return res.status(200).json({ ok: true, start: startIso });
    }
    console.error('Calendly call booking failed:', up.status, JSON.stringify(up.body));

    // A client error after our own checks passed is most often "that time was just taken": check live availability.
    if (up.status === 400 || up.status === 409) {
      const live = await availableTimes(token, ev.uri, 1 + Math.ceil((startMs - Date.now()) / 86400000)).catch(() => null);
      if (live && !live.some((s) => Date.parse(s) === startMs)) {
        return res.status(409).json({ ok: false, code: 'slot_taken', error: 'That time was just taken. Please pick another.' });
      }
    }
    await saveFailure('calendly_' + up.status);
    return res.status(502).json({ ok: false, code: 'booking_failed', error: 'Could not complete the booking' });
  } catch (error) {
    console.error('call booking error:', error);
    await saveFailure('calendly_unreachable');
    return res.status(502).json({ ok: false, code: 'booking_failed', error: 'Could not reach the booking service' });
  }
}

export default async function handler(req, res) {
  const token = process.env.CALENDLY_TOKEN;
  if (!token) {
    console.error('CALENDLY_TOKEN env var is not set');
    return res.status(500).json({ ok: false, error: 'Booking is not configured' });
  }
  if (req.method === 'GET') return slots(req, res, token);
  if (req.method === 'POST') return book(req, res, token);
  return res.status(405).json({ ok: false, error: 'Method not allowed' });
}
