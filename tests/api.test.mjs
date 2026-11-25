// Tests for api/lead.js and api/signup.js: spam checks, throwaway emails, submission IDs, origin and rate limits.
// The Google Sheet is never called: fetch is replaced with a stub that records the rows.
// Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';

process.env.SHEET_WEBHOOK = 'https://sheet.test/exec';
let saved = [];
globalThis.fetch = async (url, o) => {
  assert.equal(url, process.env.SHEET_WEBHOOK);
  saved.push(...JSON.parse(o.body).rows);
  return { ok: true, json: async () => ({ ok: true }) };
};

const lead = (await import('../api/lead.js')).default;
const signup = (await import('../api/signup.js')).default;

let ip = 0;
async function call(handler, body, { origin = 'https://www.tomoclub.org', sameIp } = {}) {
  saved = [];
  const out = {};
  const res = { status(c) { out.code = c; return this; }, json(j) { out.body = j; return this; } };
  const headers = { origin, 'x-forwarded-for': sameIp || '10.0.' + Math.floor(ip / 250) + '.' + (ip++ % 250) };
  await handler({ method: 'POST', headers, body }, res);
  return { ...out, rows: saved };
}

const minuteAgo = () => Date.now() - 60000;
const home = () => ({ type: 'discovery_request', name: 'Jane Doe', email: 'jane@district.org', district: 'X ISD',
  goal: 'Help', form_loaded_at: minuteAgo(), submission_id: 'abc-123' });
const kit = () => ({ type: 'resource', firstName: 'Jane', email: 'jane@school.org', toolkitName: 'guide.pdf',
  form_loaded_at: minuteAgo(), submission_id: 'kit-1' });
const ebook = () => ({ type: 'ebook_request', firstName: 'Jane', email: 'jane@school.org', role: 'Principal',
  form_loaded_at: minuteAgo(), submission_id: 'eb-1' });

test('home form: a valid lead saves one row with its submission ID', async () => {
  const r = await call(lead, home());
  assert.equal(r.code, 200);
  assert.equal(r.body.ok, true);
  assert.equal(r.rows.length, 1);
  assert.equal(r.rows[0].sheet, 'School leads');
  assert.equal(r.rows[0].data.submission_id, 'abc-123');
});

test('home form: honeypot and too-fast submissions look successful but save nothing', async () => {
  for (const b of [{ ...home(), hp_company_website: 'x' }, { ...home(), form_loaded_at: Date.now() }]) {
    const r = await call(lead, b);
    assert.equal(r.code, 200);
    assert.equal(r.rows.length, 0);
  }
});

test('home form: throwaway emails are refused with a message', async () => {
  for (const email of ['a@mailinator.com', 'a@x.yopmail.com', 'a@guerrillamail.net', 'a@temp-mail.org']) {
    const r = await call(lead, { ...home(), email });
    assert.equal(r.code, 400, email);
    assert.equal(r.body.error, 'Please use a permanent email address');
    assert.equal(r.rows.length, 0);
  }
});

test('home form: normal personal email is accepted', async () => {
  const r = await call(lead, { ...home(), email: 'jane@gmail.com' });
  assert.equal(r.rows.length, 1);
  assert.equal(r.rows[0].data.email_type, 'personal');
});

test('submission IDs are cleaned to letters, digits, _ and -', async () => {
  const r = await call(lead, { ...home(), submission_id: 'a<b>"c' + 'x'.repeat(100) });
  assert.match(r.rows[0].data.submission_id, /^[\w-]{1,64}$/);
});

test('origin and rate limits still apply', async () => {
  assert.equal((await call(lead, home(), { origin: 'https://evil.example' })).code, 403);
  assert.equal((await call(signup, kit(), { origin: 'https://evil.example' })).code, 403);
  let last;
  for (let i = 0; i < 16; i++) last = await call(lead, home(), { sameIp: '9.9.9.9' });
  assert.equal(last.code, 429);
  for (let i = 0; i < 31; i++) last = await call(signup, kit(), { sameIp: '8.8.8.8' });
  assert.equal(last.code, 429);
});

test('downloads: a valid guide request saves one Toolkit row with its submission ID', async () => {
  const r = await call(signup, kit());
  assert.equal(r.code, 200);
  assert.equal(r.rows.length, 1);
  assert.equal(r.rows[0].sheet, 'Toolkit downloads');
  assert.equal(r.rows[0].data.toolkit, 'guide.pdf');
  assert.equal(r.rows[0].data.submission_id, 'kit-1');
});

test('downloads: a valid ebook request saves one E-book row, also from a string body', async () => {
  let r = await call(signup, ebook());
  assert.equal(r.rows[0].sheet, 'E-book requests');
  assert.equal(r.rows[0].data.role, 'Principal');
  r = await call(signup, JSON.stringify(ebook()));
  assert.equal(r.rows.length, 1);
});

test('downloads: spam and throwaway emails look successful but save nothing', async () => {
  const cases = [
    { ...kit(), hp_company_website: 'x' },
    { ...kit(), form_loaded_at: Date.now() },
    { ...kit(), email: 'j@mailinator.com' },
    { ...kit(), firstName: 'http://a http://b http://c' },
    { ...ebook(), hp_company_website: 'x' },
  ];
  for (const b of cases) {
    const r = await call(signup, b);
    assert.equal(r.code, 200);
    assert.equal(r.rows.length, 0);
  }
});

test('downloads: a missing email or unknown type is refused', async () => {
  assert.equal((await call(signup, { ...kit(), email: 'nope' })).code, 400);
  assert.equal((await call(signup, { ...kit(), type: 'other' })).code, 400);
});
