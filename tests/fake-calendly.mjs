// A stand-in for the Calendly API, for tests of api/call.js. No request reaches Calendly.
// fakeCalendly(url, options) answers like Calendly would, or returns null for any other URL.
// The open times are on the next three days (tomorrow at 15:00 and 16:00 UTC, and so on), so they always exist.

export const calendly = {
  bookings: [],          // POST /invitees bodies
  failNextBooking: 0,    // status to answer the next POST /invitees with (0 = book it)
  takeOnFail: false,     // also drop that time from availability (a "just taken" time)
  seen: [],              // every URL asked for
  down: false,           // every availability request fails (Calendly unreachable)
  reset() { this.bookings = []; this.failNextBooking = 0; this.takeOnFail = false; this.down = false; this.seen = []; this.taken = new Set(); },
  taken: new Set(),
};

const EVENT = {
  uri: 'https://api.calendly.com/event_types/CALL1',
  scheduling_url: 'https://calendly.com/avinashtomo/tomoclub-call',
  duration: 20,
  locations: [{ kind: 'zoom_conference' }],
  custom_questions: [
    { name: 'Reason of the meeting', type: 'text', position: 0, enabled: true, required: true },
    { name: 'How did you land on this link?', type: 'single_select', position: 1, enabled: true, required: true,
      answer_choices: ['I shared personally', 'Email campaign', 'Social Media'], include_other: true },
  ],
};

export function openTimes() {
  const out = [];
  const d = new Date(); d.setUTCHours(0, 0, 0, 0);
  for (let i = 1; i <= 3; i++) {
    for (const h of [15, 16]) out.push(new Date(d.getTime() + i * 86400000 + h * 3600000).toISOString().replace('.000Z', 'Z'));
  }
  return out;
}

const reply = (status, body) => ({ ok: status < 300, status, json: async () => body });

export function fakeCalendly(url, o = {}) {
  if (!String(url).startsWith('https://api.calendly.com/')) return null;
  calendly.seen.push(String(url));
  const u = new URL(url);
  if (u.pathname === '/users/me') return reply(200, { resource: { uri: 'https://api.calendly.com/users/U1' } });
  if (u.pathname === '/event_types') {
    return reply(200, { collection: [{ uri: 'https://api.calendly.com/event_types/OTHER', scheduling_url: 'https://calendly.com/avinashtomo/other' }, EVENT], pagination: {} });
  }
  if (u.pathname === '/event_type_available_times') {
    if (calendly.down) return reply(503, { title: 'Unavailable' });
    const s = Date.parse(u.searchParams.get('start_time')), e = Date.parse(u.searchParams.get('end_time'));
    if (e - s > 7 * 86400000 + 1000) return reply(400, { title: 'Invalid Argument', message: 'range over 7 days' });
    const list = openTimes().filter((t) => !calendly.taken.has(t) && Date.parse(t) >= s && Date.parse(t) < e);
    return reply(200, { collection: list.map((t) => ({ status: 'available', start_time: t })) });
  }
  if (u.pathname === '/invitees' && o.method === 'POST') {
    const body = JSON.parse(o.body);
    if (calendly.failNextBooking) {
      const status = calendly.failNextBooking;
      calendly.failNextBooking = 0;
      if (calendly.takeOnFail) calendly.taken.add(new Date(body.start_time).toISOString().replace('.000Z', 'Z'));
      return reply(status, { title: 'Error', message: 'fake failure' });
    }
    calendly.bookings.push(body);
    return reply(201, { resource: { uri: 'https://api.calendly.com/scheduled_events/E1/invitees/INV' + calendly.bookings.length } });
  }
  return reply(404, { title: 'Not found' });
}
