// Tests for api/call.js (the booking pop-up): open times, booking in Calendly, answers, guests, failures and spam.
// Calendly and the Google Sheet are never called: fetch is replaced with stubs (see fake-calendly.mjs).
// Run: npm test
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { calendly, fakeCalendly, openTimes } from './fake-calendly.mjs';

process.env.SHEET_WEBHOOK = 'https://sheet.test/exec';
process.env.CALENDLY_TOKEN = 'test-token';
let saved = [];
globalThis.fetch = async (url, o) => {
  const c = fakeCalendly(url, o);
  if (c) return c;
  assert.equal(url, process.env.SHEET_WEBHOOK);
  saved.push(...JSON.parse(o.body).rows);
  return { ok: true, json: async () => ({ ok: true }) };
};

const call = (await import('../api/call.js')).default;

let ip = 0;
async function run(method, body, { origin = 'https://www.tomoclub.org' } = {}) {
  saved = [];
  const out = { headers: {} };
  const res = {
    status(c) { out.code = c; return this; }, json(j) { out.body = j; return this; },
    setHeader(k, v) { out.headers[k.toLowerCase()] = v; },
  };
  const headers = { origin, 'x-forwarded-for': '10.1.' + Math.floor(ip / 250) + '.' + (ip++ % 250) };
  await call({ method, headers, body }, res);
  return { ...out, rows: saved };
}

const booking = (over) => ({ start: openTimes()[0], name: 'Jane Doe', email: 'Jane@District.org', reason: 'AI PD for 40 teachers',
  timezone: 'America/Chicago', page: '/', form_loaded_at: Date.now() - 60000, submission_id: 'sub-1', utm_source: 'linkedin', ...over });

beforeEach(() => calendly.reset());

test('GET: open times for the call event, asked for a week at a time', async () => {
  const r = await run('GET');
  assert.equal(r.code, 200);
  assert.deepEqual(r.body.slots, openTimes());
  assert.equal(r.body.minutes, 20);
  assert.match(r.headers['cache-control'], /s-maxage/);
  const ranges = calendly.seen.filter((u) => u.includes('available_times'));
  assert.equal(ranges.length, 4, '28 days in 7-day pieces');
  assert.ok(ranges.every((u) => u.includes('event_type=' + encodeURIComponent('https://api.calendly.com/event_types/CALL1'))));
});

test('POST: books in Calendly with Zoom, the answers and guests, and saves a call_booked row', async () => {
  const r = await run('POST', booking({ guests: ['sam@district.org', 'lee@district.org'] }));
  assert.equal(r.code, 200);
  assert.equal(r.body.ok, true);
  assert.equal(calendly.bookings.length, 1);
  const b = calendly.bookings[0];
  assert.equal(b.event_type, 'https://api.calendly.com/event_types/CALL1');
  assert.equal(Date.parse(b.start_time), Date.parse(openTimes()[0]));
  assert.deepEqual(b.invitee, { name: 'Jane Doe', email: 'jane@district.org', timezone: 'America/Chicago' });
  assert.deepEqual(b.location, { kind: 'zoom_conference' });
  assert.deepEqual(b.event_guests, ['sam@district.org', 'lee@district.org']);
  assert.deepEqual(b.questions_and_answers, [
    { question: 'Reason of the meeting', answer: 'AI PD for 40 teachers', position: 0 },
    { question: 'How did you land on this link?', answer: 'Website (tomoclub.org)', position: 1 },
  ]);
  assert.deepEqual(b.tracking, { utm_source: 'linkedin' });
  assert.equal(r.rows.length, 1);
  const row = r.rows[0];
  assert.equal(row.sheet, 'School leads');
  assert.equal(row.data.type, 'call_booked');
  assert.equal(row.data.email, 'jane@district.org');
  assert.equal(row.data.email_type, 'work');
  assert.equal(row.data.message, 'AI PD for 40 teachers | Guests: sam@district.org, lee@district.org');
  assert.equal(Date.parse(row.data.meeting_start), Date.parse(openTimes()[0]));
  assert.equal(row.data.submission_id, 'INV1');
  assert.equal(row.data.utm_source, 'linkedin');
});

test('POST: a time taken just before is reported as slot_taken, with no row', async () => {
  calendly.failNextBooking = 400; calendly.takeOnFail = true;
  const r = await run('POST', booking());
  assert.equal(r.code, 409);
  assert.equal(r.body.code, 'slot_taken');
  assert.equal(r.rows.length, 0);
});

test('POST: any other Calendly failure saves a call_failed row for follow-up', async () => {
  calendly.failNextBooking = 500;
  const r = await run('POST', booking());
  assert.equal(r.code, 502);
  assert.equal(r.body.code, 'booking_failed');
  assert.equal(r.rows.length, 1);
  assert.equal(r.rows[0].data.type, 'call_failed');
  assert.match(r.rows[0].data.message, /^Booking did not go through \(calendly_500\)\. AI PD/);
  assert.equal(r.rows[0].data.submission_id, 'sub-1');
});

test('POST: missing fields, bad guests, past times and throwaway emails are refused before Calendly', async () => {
  for (const over of [{ name: '' }, { email: 'nope' }, { reason: ' ' }, { guests: ['x'] }, { start: new Date(Date.now() - 1000).toISOString() }, { email: 'a@mailinator.com' }]) {
    const r = await run('POST', booking(over));
    assert.equal(r.code, 400, JSON.stringify(over));
    assert.equal(r.body.code, 'invalid');
  }
  assert.equal(calendly.bookings.length, 0);
});

test('POST: honeypot looks like success but books nothing; other origins are refused', async () => {
  const r = await run('POST', booking({ hp_company_website: 'x' }));
  assert.equal(r.code, 200);
  assert.equal(calendly.bookings.length, 0);
  assert.equal(r.rows.length, 0);
  const o = await run('POST', booking(), { origin: 'https://evil.example' });
  assert.equal(o.code, 403);
});
