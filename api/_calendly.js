// Calendly helpers for api/call.js. Files whose names start with "_" are not deployed as their own Vercel functions.
//
// Env var: CALENDLY_TOKEN  personal access token of the Calendly account that owns the call event
//                          (scopes: users:read, event_types:read, availability:read, scheduled_events:write).
// The event is found by its booking link (calendly.com/<user>/<CALL_SLUG>), so no event ID needs to be configured.

const API = 'https://api.calendly.com';
export const CALL_SLUG = 'tomoclub-call';
export const CALL_PAGE = 'https://calendly.com/avinashtomo/' + CALL_SLUG;

const headers = (token, extra) => ({ Authorization: 'Bearer ' + token, ...(extra || {}) });

export async function getJson(url, token) {
  const r = await fetch(url, { headers: headers(token), signal: AbortSignal.timeout(8000) });
  const body = await r.json().catch(() => null);
  return { ok: r.ok, status: r.status, body };
}

// The event type rarely changes, so keep it for a few minutes per warm server instance.
let cache = { at: 0, ev: null };
export function clearEventCache() { cache = { at: 0, ev: null }; }

export async function callEventType(token) {
  if (cache.ev && Date.now() - cache.at < 10 * 60 * 1000) return cache.ev;
  const me = await getJson(API + '/users/me', token);
  const user = me.body && me.body.resource && me.body.resource.uri;
  if (!me.ok || !user) throw new Error('Calendly users/me failed: ' + me.status + ' ' + JSON.stringify(me.body));
  let url = API + '/event_types?' + new URLSearchParams({ user, count: '100' });
  while (url) {
    const page = await getJson(url, token);
    if (!page.ok || !page.body || !Array.isArray(page.body.collection)) {
      throw new Error('Calendly event_types failed: ' + page.status + ' ' + JSON.stringify(page.body));
    }
    const ev = page.body.collection.find((e) => String(e.scheduling_url || '').replace(/\/+$/, '').split('/').pop() === CALL_SLUG);
    if (ev) {
      cache = { at: Date.now(), ev };
      return ev;
    }
    url = page.body.pagination && page.body.pagination.next_page;
  }
  throw new Error('No Calendly event with the link /' + CALL_SLUG + ' on this account');
}

// Open start times (ISO strings) for the next `days` days. Calendly limits each request to a week,
// so the range is asked for in 7-day pieces.
export async function availableTimes(token, eventUri, days) {
  const first = Date.now() + 60 * 1000;
  const end = first + days * 24 * 60 * 60 * 1000;
  const week = 7 * 24 * 60 * 60 * 1000;
  const ranges = [];
  for (let s = first; s < end; s += week) ranges.push([s, Math.min(s + week, end)]);
  const pages = await Promise.all(ranges.map(([s, e]) => getJson(API + '/event_type_available_times?' + new URLSearchParams({
    event_type: eventUri, start_time: new Date(s).toISOString(), end_time: new Date(e).toISOString(),
  }), token)));
  const bad = pages.find((p) => !p.ok || !p.body || !Array.isArray(p.body.collection));
  if (bad) throw new Error('Calendly available times failed: ' + bad.status + ' ' + JSON.stringify(bad.body));
  const out = new Set();
  pages.forEach((p) => p.body.collection.forEach((s) => { if (s && s.status === 'available' && s.start_time) out.add(s.start_time); }));
  return [...out].sort();
}

export async function createInvitee(token, payload) {
  const r = await fetch(API + '/invitees', {
    method: 'POST', headers: headers(token, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload), signal: AbortSignal.timeout(15000),
  });
  const body = await r.json().catch(() => null);
  return { status: r.status, body };
}

// The meeting place the event uses (Zoom, Google Meet...). Calendly wants it repeated on API bookings.
export function locationFor(ev) {
  const l = Array.isArray(ev.locations) && ev.locations[0];
  if (!l || !l.kind) return null;
  const out = { kind: l.kind };
  if (l.location) out.location = l.location;
  return out;
}

// Answers for the event's own questions, matched by what the question asks, so a reworded question still works.
// A choice question only accepts one of its choices, or any text when it has an "Other" box.
const norm = (s) => String(s || '').toLowerCase().replace(/[‘’]/g, "'").replace(/\s+/g, ' ').trim();
export function buildAnswers(ev, v) {
  const out = [];
  (ev.custom_questions || []).forEach((q) => {
    if (!q || q.enabled === false || q.type === 'phone_number') return;
    const n = norm(q.name);
    let answer;
    if (/how did you|land on|hear about|find us/.test(n)) answer = 'Website (tomoclub.org)';
    else if (/reason|agenda|discuss|purpose|topic/.test(n)) answer = v.reason;
    if (!answer) return;
    if (Array.isArray(q.answer_choices) && q.answer_choices.length) {
      const a = norm(answer);
      const choice = q.answer_choices.find((c) => norm(c) === a) || q.answer_choices.find((c) => /website/.test(norm(c)));
      if (choice) answer = choice;
      else if (!q.include_other) return;
    }
    out.push({ question: q.name, answer: String(answer), position: q.position });
  });
  return out;
}
