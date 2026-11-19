// Vercel serverless function: POST /api/book
// Books a free trial class in Calendly (Scheduling API). Calendly sends the invite and meeting link.
// The browser then saves the Sheet row once this returns { ok: true }.
//
// Env vars:
//   CALENDLY_TOKEN           personal access token (scopes: availability:read, scheduled_events:write, event_types:read)
//   CALENDLY_EVENT_TYPE_URI  the trial class event type, e.g. https://api.calendly.com/event_types/XXXXXXXX
//   CALENDLY_LOCATION_KIND   optional, e.g. google_conference. Set only if Calendly rejects bookings without it.
//   SHEET_WEBHOOK            the Apps Script Web app URL; the "Trial bookings" row is written here after Calendly confirms.
//
// Booking answers: the event type's questions are read from Calendly, and an answer is sent for every
// question whose name matches one of the ANSWERS below. Add or remove questions in the Calendly dashboard
// and this follows, with no code change. Questions with other names are left unanswered.

const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?tomoclub\.org$/,
  /^https:\/\/tomoclub-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];

const PROGRAMS = { life_skills: 'Tomo Life Skills', ai_lab: 'Tomo AI Lab' };

// Question name (as on the Calendly event type) -> the answer to send. Names are matched ignoring case.
const norm = (s) => String(s || '').toLowerCase().replace(/[‘’]/g, "'").replace(/\s+/g, ' ').trim();
function answerFor(name, v) {
  const map = {
    'what organisation do you work with?': 'Parent',
    'program': PROGRAMS[v.program],
    'class': PROGRAMS[v.program],
    "child's grade": 'Grade ' + v.grade,
    'grade': 'Grade ' + v.grade,
    'whatsapp number': v.whatsapp || 'Not provided',
    'country': v.country,
    'city': v.city,
  };
  return map[norm(name)];
}

// The event type's questions rarely change, so keep them for a few minutes per warm server instance.
let questionCache = { at: 0, list: null };
async function getQuestions(eventType, headers) {
  if (questionCache.list && Date.now() - questionCache.at < 5 * 60 * 1000) return questionCache.list;
  try {
    const r = await fetch(eventType, { headers });
    const body = await r.json().catch(() => null);
    const list = body && body.resource && Array.isArray(body.resource.custom_questions) ? body.resource.custom_questions : null;
    if (r.ok && list) { questionCache = { at: Date.now(), list }; return list; }
    console.error('Could not read event type questions:', r.status, JSON.stringify(body));
  } catch (error) {
    console.error('Event type lookup error:', error);
  }
  return [];
}

// Build the booking answers. A dropdown question only accepts one of its own choices, so match one.
function buildAnswers(questions, v) {
  const out = [];
  questions.forEach((q) => {
    if (!q || q.enabled === false || q.type === 'phone_number') return;
    let answer = answerFor(q.name, v);
    if (answer === undefined || answer === '') return;
    if (Array.isArray(q.answer_choices) && q.answer_choices.length) {
      const a = norm(answer);
      const choice = q.answer_choices.find((c) => norm(c) === a) || q.answer_choices.find((c) => norm(c).includes(a) || a.includes(norm(c)));
      if (!choice) return;
      answer = choice;
    }
    out.push({ question: q.name, answer: String(answer), position: q.position });
  });
  return out;
}

// Best-effort limit per warm server instance: this endpoint creates real bookings and sends real emails.
const hits = new Map();
function tooMany(ip) {
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter((t) => now - t < 10 * 60 * 1000);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 500) hits.clear();
  return recent.length > 5;
}

const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);

// Append rows to the Google Sheet through the Apps Script collector (data-capture/Code.gs).
async function saveToSheet(rows) {
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

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const origin = req.headers.origin || '';
  if (!ALLOWED_ORIGINS.some((re) => re.test(origin))) {
    return res.status(403).json({ ok: false, error: 'Not allowed' });
  }

  const token = process.env.CALENDLY_TOKEN;
  const eventType = process.env.CALENDLY_EVENT_TYPE_URI;
  if (!token || !eventType) {
    console.error('CALENDLY_TOKEN or CALENDLY_EVENT_TYPE_URI env var is not set');
    return res.status(500).json({ ok: false, error: 'Booking is not configured' });
  }

  const b = req.body && typeof req.body === 'object' ? req.body : {};

  // Honeypot: real visitors never fill this hidden field. Pretend success so bots learn nothing.
  if (b.website) return res.status(200).json({ ok: true });

  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  if (tooMany(ip)) {
    return res.status(429).json({ ok: false, code: 'too_many', error: 'Too many attempts. Please try again later.' });
  }

  const name = clean(b.name, 120);
  const email = clean(b.email, 200);
  const program = clean(b.program, 20);
  const grade = parseInt(b.grade, 10);
  const country = clean(b.country, 60);
  const city = clean(b.city, 80);
  const whatsapp = clean(b.whatsapp, 30);
  const timezone = clean(b.timezone, 60);
  const startMs = Date.parse(b.start);

  const problems = [];
  if (!name) problems.push('name');
  if (!/^\S+@\S+\.\S+$/.test(email)) problems.push('email');
  if (!PROGRAMS[program]) problems.push('program');
  if (!(grade >= 3 && grade <= 12)) problems.push('grade');
  if (!country) problems.push('country');
  if (!city) problems.push('city');
  if (!timezone) problems.push('timezone');
  if (!(startMs > Date.now())) problems.push('start');
  if (problems.length) {
    return res.status(400).json({ ok: false, code: 'invalid', error: 'Please check: ' + problems.join(', ') });
  }
  const startIso = new Date(startMs).toISOString();

  const payload = {
    event_type: eventType,
    start_time: startIso,
    invitee: { name, email, timezone },
  };
  if (process.env.CALENDLY_LOCATION_KIND) payload.location = { kind: process.env.CALENDLY_LOCATION_KIND };
  const tracking = {};
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach((k) => {
    const v = clean(b[k], 120);
    if (v) tracking[k] = v;
  });
  if (Object.keys(tracking).length) payload.tracking = tracking;

  const headers = { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' };

  const answers = buildAnswers(await getQuestions(eventType, headers), { program, grade, whatsapp, country, city });
  if (answers.length) payload.questions_and_answers = answers;

  // Fields shared by the "Trial bookings" row (success) and the "Failed bookings" row (failure).
  const ctx = b.context && typeof b.context === 'object' ? b.context : {};
  const c = (k, max) => clean(ctx[k], max || 300);
  const detected = String(req.headers['x-vercel-ip-country'] || '').toUpperCase(); // set by Vercel, not by the browser
  const rowBase = {
    timestamp: new Date().toISOString(), page: c('page', 40), program, parent_name: name, email, whatsapp, country, city,
    grade: String(grade), class_date: clean(b.class_date, 40), class_time: clean(b.class_time, 20), time_zone: timezone,
    whatsapp_reminders: b.whatsapp_reminders === 'yes' ? 'yes' : 'no', session_id: c('session_id', 60), visitor_id: c('visitor_id', 60),
    utm_source: c('utm_source', 120), utm_medium: c('utm_medium', 120), utm_campaign: c('utm_campaign', 120), utm_content: c('utm_content', 120),
    utm_term: c('utm_term', 120), gclid: c('gclid'), fbclid: c('fbclid'), referrer: c('referrer'), landing_page: c('landing_page'),
    class_start_utc: startIso, detected_country: /^[A-Z]{2}$/.test(detected) ? detected : '', language: c('language', 20), currency: '',
  };
  // A booking that did not go through is saved too, so the team can follow up (the sheet script alerts Slack).
  async function saveFailure(reason) {
    const saved = await saveToSheet([{ sheet: 'Failed bookings', data: { ...rowBase, reason } }]);
    if (!saved) console.error('Failed booking could not be saved to the sheet:', reason);
  }

  try {
    const upstream = await fetch('https://api.calendly.com/invitees', { method: 'POST', headers, body: JSON.stringify(payload) });
    const body = await upstream.json().catch(() => null);

    if (upstream.status === 201 && body && body.resource) {
      const invitee = body.resource.uri || '';
      // Calendly has confirmed, so write the "Trial bookings" row here (it survives a closed tab or ad blocker).
      // A sheet problem never fails the booking: it is logged, and Calendly still holds the booking.
      const saved = await saveToSheet([{ sheet: 'Trial bookings', data: { ...rowBase, calendly_booking: invitee } }]);
      if (!saved) console.error('Booking confirmed in Calendly but the sheet row was not saved:', invitee);
      return res.status(200).json({ ok: true, invitee, start: startIso, sheet: saved });
    }

    console.error('Calendly booking failed:', upstream.status, JSON.stringify(body));

    // A client error right after our own validation passed is most often "that time was just taken".
    // Check against Calendly's live availability so the visitor gets the right message.
    if (upstream.status === 400 || upstream.status === 409) {
      const check = 'https://api.calendly.com/event_type_available_times?' + new URLSearchParams({
        event_type: eventType,
        start_time: new Date(Math.max(Date.now() + 60000, startMs - 60 * 60 * 1000)).toISOString(),
        end_time: new Date(startMs + 60 * 60 * 1000).toISOString(),
      });
      const live = await fetch(check, { headers }).then((r) => r.json()).catch(() => null);
      if (live && Array.isArray(live.collection) && !live.collection.some((s) => Date.parse(s.start_time) === startMs)) {
        await saveFailure('slot_taken');
        return res.status(409).json({ ok: false, code: 'slot_taken', error: 'That time was just taken. Please pick another.' });
      }
    }
    await saveFailure('booking_failed');
    return res.status(502).json({ ok: false, code: 'booking_failed', error: 'Could not complete the booking' });
  } catch (error) {
    console.error('book proxy error:', error);
    await saveFailure('booking_failed');
    return res.status(502).json({ ok: false, code: 'booking_failed', error: 'Could not reach the booking service' });
  }
}
