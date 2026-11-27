// Tests for adding leads to Instantly (api/_lead-core.js addToInstantly, used by lead.js, signup.js and call.js).
// Instantly, Calendly and the Google Sheet are never called: fetch is replaced with stubs.
// Run: npm test
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { calendly, fakeCalendly, openTimes } from './fake-calendly.mjs';

const LISTS = {
  INSTANTLY_LIST_HOME_FORM: '11111111-1111-1111-1111-111111111111',
  INSTANTLY_LIST_BOOKED_CALLS: '22222222-2222-2222-2222-222222222222',
  INSTANTLY_LIST_EBOOK: '33333333-3333-3333-3333-333333333333',
  INSTANTLY_LIST_TOOLKITS: '44444444-4444-4444-4444-444444444444',
};
process.env.SHEET_WEBHOOK = 'https://sheet.test/exec';
process.env.CALENDLY_TOKEN = 'test-token';

let rows = [], sent = [], instantlyReply;
globalThis.fetch = async (url, o) => {
  const c = fakeCalendly(url, o);
  if (c) return c;
  if (url === 'https://api.instantly.ai/api/v2/leads/add') {
    assert.equal(o.headers.Authorization, 'Bearer test-key');
    sent.push(JSON.parse(o.body));
    return instantlyReply();
  }
  assert.equal(url, process.env.SHEET_WEBHOOK);
  rows.push(...JSON.parse(o.body).rows);
  return { ok: true, json: async () => ({ ok: true }) };
};

const lead = (await import('../api/lead.js')).default;
const signup = (await import('../api/signup.js')).default;
const call = (await import('../api/call.js')).default;

beforeEach(() => {
  Object.assign(process.env, LISTS, { INSTANTLY_API_KEY: 'test-key' });
  rows = []; sent = [];
  instantlyReply = () => ({ ok: true, status: 200, json: async () => ({ leads_uploaded: 1 }) });
  calendly.reset();
});

let ip = 0;
async function post(handler, body) {
  const out = {};
  const res = { status(c) { out.code = c; return this; }, json(j) { out.body = j; return this; }, setHeader() {} };
  await handler({ method: 'POST', headers: { origin: 'https://www.tomoclub.org', 'x-forwarded-for': '10.9.0.' + (ip++ % 250) }, body }, res);
  return out;
}

const minuteAgo = () => Date.now() - 60000;
const home = () => ({ type: 'discovery_request', name: 'Jane Q Doe', email: 'Jane@District.org', district: 'X ISD', role: 'Principal or head of school',
  state: 'TX', goal: 'Help', form_loaded_at: minuteAgo(), submission_id: 'h-1', utm_source: 'linkedin' });

test('home form: the lead goes to the home form list with name, school and answers', async () => {
  const r = await post(lead, home());
  assert.equal(r.code, 200);
  assert.equal(rows.length, 1);
  assert.equal(sent.length, 1);
  const s = sent[0];
  assert.equal(s.list_id, LISTS.INSTANTLY_LIST_HOME_FORM);
  assert.equal(s.skip_if_in_list, false);
  assert.deepEqual(s.leads[0], {
    email: 'jane@district.org', first_name: 'Jane', last_name: 'Q Doe', company_name: 'X ISD',
    custom_variables: { role: 'Principal or head of school', state: 'TX', message: 'Help', source: 'linkedin' },
  });
});

test('downloads: e-book and toolkit requests go to their own lists', async () => {
  await post(signup, { type: 'ebook_request', firstName: 'Ann', email: 'ann@school.org', role: 'Teacher', form_loaded_at: minuteAgo() });
  await post(signup, { type: 'resource', firstName: 'Bo', email: 'bo@school.org', toolkitName: 'guide.pdf', form_loaded_at: minuteAgo() });
  assert.equal(sent.length, 2);
  assert.equal(sent[0].list_id, LISTS.INSTANTLY_LIST_EBOOK);
  assert.deepEqual(sent[0].leads[0].custom_variables, { role: 'Teacher' });
  assert.equal(sent[1].list_id, LISTS.INSTANTLY_LIST_TOOLKITS);
  assert.deepEqual(sent[1].leads[0].custom_variables, { toolkit: 'guide.pdf' });
});

test('booking pop-up: a booked call goes to the booked calls list; a failed one does not', async () => {
  const booking = { start: openTimes()[0], name: 'Jane Doe', email: 'jane@district.org', reason: 'AI PD', timezone: 'America/Chicago',
    page: '/', form_loaded_at: minuteAgo() };
  let r = await post(call, booking);
  assert.equal(r.code, 200);
  assert.equal(sent.length, 1);
  assert.equal(sent[0].list_id, LISTS.INSTANTLY_LIST_BOOKED_CALLS);
  assert.equal(Date.parse(sent[0].leads[0].custom_variables.meeting_start), Date.parse(booking.start));

  sent = [];
  calendly.failNextBooking = 500;
  r = await post(call, booking);
  assert.equal(r.code, 502);
  assert.equal(sent.length, 0);
});

test('spam is never sent to Instantly', async () => {
  await post(lead, { ...home(), hp_company_website: 'x' });
  await post(signup, { type: 'resource', firstName: 'Bo', email: 'bo@mailinator.com', form_loaded_at: minuteAgo() });
  assert.equal(sent.length, 0);
});

test('an Instantly error or timeout never fails the form', async () => {
  instantlyReply = () => ({ ok: false, status: 500, json: async () => ({ error: 'down' }) });
  assert.equal((await post(lead, home())).code, 200);
  instantlyReply = () => { throw new Error('timeout'); };
  assert.equal((await post(signup, { type: 'resource', firstName: 'Bo', email: 'bo@school.org', form_loaded_at: minuteAgo() })).code, 200);
  assert.equal(rows.length, 2);
});

test('nothing is sent when the key or the list ID is missing', async () => {
  delete process.env.INSTANTLY_API_KEY;
  await post(lead, home());
  process.env.INSTANTLY_API_KEY = 'test-key';
  delete process.env.INSTANTLY_LIST_EBOOK;
  await post(signup, { type: 'ebook_request', firstName: 'Ann', email: 'ann@school.org', form_loaded_at: minuteAgo() });
  assert.equal(sent.length, 0);
  assert.equal(rows.length, 2);
});
