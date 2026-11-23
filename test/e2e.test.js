// End-to-end test: fixture district websites -> crawl -> index -> ask -> cite,
// plus uploads, district isolation, lead capture, admin auth and safety checks.
// Run: python3 test/make_fixtures.py && npm test
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { startStub, calls } from './anthropic-stub.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const FIX = path.join(here, 'fixtures');
const NOT_FOUND = "I couldn't find this information in the available district resources.";
const results = [];
const check = async (name, fn) => {
  try {
    await fn();
    results.push(['PASS', name]);
    console.log('PASS', name);
  } catch (e) {
    results.push(['FAIL', name, e.message]);
    console.log('FAIL', name, '\n   ', e.message);
  }
};

function staticSite(dir, port) {
  const server = http.createServer((req, res) => {
    const origin = `http://127.0.0.1:${port}`;
    let p = decodeURIComponent(new URL(req.url, origin).pathname);
    let file = path.join(FIX, dir, p);
    if (p.endsWith('/')) file = path.join(file, 'index.html');
    if (!file.startsWith(path.join(FIX, dir)) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404, { 'content-type': 'text/html' });
      return res.end('<h1>Not found</h1>');
    }
    const ext = path.extname(file);
    const type = { '.html': 'text/html; charset=utf-8', '.pdf': 'application/pdf', '.xml': 'application/xml', '.txt': 'text/plain' }[ext] || 'application/octet-stream';
    let body = fs.readFileSync(file);
    if (ext === '.xml') body = Buffer.from(body.toString().replaceAll('__ORIGIN__', origin));
    res.writeHead(200, { 'content-type': type });
    res.end(body);
  });
  return new Promise((r) => server.listen(port, '127.0.0.1', () => r(server)));
}

function startApp(port, env) {
  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'da-'));
  const child = spawn(process.execPath, ['--disable-warning=ExperimentalWarning', 'src/server.js'], {
    cwd: path.join(here, '..'),
    env: { ...process.env, PORT: String(port), DATA_DIR: dataDir, CRAWL_DELAY_MS: '0', MIN_FORM_SECONDS: '1', ...env },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let log = '';
  child.stdout.on('data', (d) => (log += d));
  child.stderr.on('data', (d) => (log += d));
  return new Promise((resolve, reject) => {
    const t0 = Date.now();
    const tick = async () => {
      try {
        const r = await fetch(`http://127.0.0.1:${port}/api/health`);
        if (r.ok) return resolve({ child, base: `http://127.0.0.1:${port}`, log: () => log });
      } catch {
        /* not up yet */
      }
      if (Date.now() - t0 > 15000) return reject(new Error(`app did not start:\n${log}`));
      setTimeout(tick, 200);
    };
    tick();
  });
}

const j = async (res) => ({ status: res.status, body: await res.json().catch(() => ({})) });
const post = (base, p, body) => fetch(base + p, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) }).then(j);
const get = (base, p, headers = {}) => fetch(base + p, { headers }).then(j);

async function waitReady(base, id) {
  for (let i = 0; i < 200; i++) {
    const { body } = await get(base, `/api/districts/${id}`);
    if (['ready', 'failed'].includes(body.district.status)) return body.district;
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error('crawl did not finish');
}

const riverbend = await staticSite('riverbend', 4599);
const lakeside = await staticSite('lakeside', 4598);
const stub = await startStub(4650);
const app = await startApp(4700, {
  ALLOW_PRIVATE_HOSTS: 'true',
  ANTHROPIC_API_KEY: 'test-key',
  ANTHROPIC_API_URL: 'http://127.0.0.1:4650',
  ADMIN_PASSWORD: 'test-admin-pass',
});
const B = app.base;
let rb, lk, up;

try {
  await check('crawl: Riverbend site is read and marked ready', async () => {
    const r = await post(B, '/api/districts', { url: 'http://127.0.0.1:4599/' });
    assert.equal(r.status, 202, JSON.stringify(r.body));
    rb = await waitReady(B, r.body.district.id);
    assert.equal(rb.status, 'ready', rb.message);
  });

  await check('crawl: district name comes from the site', async () => {
    assert.equal(rb.name, 'Riverbend Unified School District');
  });

  const src = (pred) => rb.sources.find(pred);
  await check('crawl: handbook PDF read with all 5 pages', async () => {
    const s = src((x) => x.url?.endsWith('student-handbook-2026-27.pdf'));
    assert.ok(s, 'handbook missing');
    assert.equal(s.status, 'ok');
    assert.equal(s.pages, 5);
    assert.match(s.title, /Student Handbook/);
  });
  await check('crawl: sitemap-only page found (medication)', async () => {
    assert.ok(src((x) => x.url?.includes('/health/medication-at-school/') && x.status === 'ok'));
  });
  await check('crawl: scanned PDF flagged, not indexed', async () => {
    const s = src((x) => x.url?.endsWith('immunization-requirements-scan.pdf'));
    assert.ok(s);
    assert.equal(s.status, 'failed');
    assert.match(s.reason, /Scanned PDF/);
  });
  await check('crawl: robots.txt-blocked page skipped and never fetched', async () => {
    const s = src((x) => x.url?.includes('/board/private/'));
    assert.ok(s, 'blocked page should be listed as not read');
    assert.equal(s.status, 'skipped');
    assert.match(s.reason, /robots\.txt/);
  });
  await check('crawl: JavaScript-only page flagged', async () => {
    const s = src((x) => x.url?.includes('/parent-portal-app/'));
    assert.ok(s);
    assert.equal(s.status, 'failed');
    assert.match(s.reason, /JavaScript/);
  });
  await check('crawl: broken link (404) flagged', async () => {
    const s = src((x) => x.url?.includes('/nutrition/'));
    assert.ok(s);
    assert.equal(s.status, 'failed');
    assert.match(s.reason, /404/);
  });
  await check('crawl: Google Drive document listed as not readable', async () => {
    const s = src((x) => x.url?.includes('drive.google.com'));
    assert.ok(s);
    assert.equal(s.status, 'skipped');
  });
  await check('categories: detected from real content', async () => {
    const keys = rb.categories.map((c) => c.key);
    for (const k of ['calendar', 'transportation', 'enrollment', 'attendance', 'handbook']) assert.ok(keys.includes(k), `missing ${k}: ${keys}`);
  });
  await check('suggested questions offered', async () => {
    assert.ok(rb.suggestedQuestions.length >= 3);
  });

  const ask = (id, question, history) => post(B, `/api/districts/${id}/ask`, { question, history });

  await check('answer: cell phone policy cites handbook page 3', async () => {
    const r = await ask(rb.id, 'What is the cell phone policy during class?');
    assert.equal(r.status, 200, JSON.stringify(r.body));
    assert.equal(r.body.found, true, JSON.stringify(r.body));
    assert.match(r.body.answer, /\[1\]/);
    const c = r.body.citations[0];
    assert.ok(c.url.endsWith('student-handbook-2026-27.pdf#page=3'), c.url);
    assert.equal(c.page, 3);
  });
  await check('answer: winter break cites the calendar page', async () => {
    const r = await ask(rb.id, 'When is winter break?');
    assert.equal(r.body.found, true, JSON.stringify(r.body));
    assert.match(r.body.answer, /December 21, 2026/);
    assert.ok(r.body.citations[0].url.includes('/calendar/'));
  });
  await check('answer: bus stop question cites transportation', async () => {
    const r = await ask(rb.id, 'How do I find my bus stop?');
    assert.equal(r.body.found, true, JSON.stringify(r.body));
    assert.ok(r.body.citations[0].url.includes('/transportation/'));
  });
  await check('answer: enrollment documents cites enrollment page', async () => {
    const r = await ask(rb.id, 'What proof of residency documents do I need to enroll?');
    assert.equal(r.body.found, true, JSON.stringify(r.body));
    assert.ok(r.body.citations[0].url.includes('/enrollment/'));
  });
  await check('answer: missing information gives the exact fallback', async () => {
    const r = await ask(rb.id, "What is the superintendent's salary?");
    assert.equal(r.body.found, false);
    assert.equal(r.body.answer, NOT_FOUND);
    assert.equal(r.body.citations.length, 0);
  });
  await check('answer: robots-blocked text never reaches the model', async () => {
    const before = calls.length;
    await ask(rb.id, 'What do the board policy drafts say?');
    const sent = calls.slice(before).map((c) => JSON.stringify(c)).join(' ');
    assert.ok(!/SECRET DRAFT/.test(sent));
  });
  await check('security: API key sent only server-side to the AI endpoint', async () => {
    assert.ok(calls.every((c) => c.key === 'test-key'));
    const html = await fetch(B + '/').then((r) => r.text());
    const js = await fetch(B + '/app.js').then((r) => r.text());
    assert.ok(!/test-key/.test(html + js));
  });

  await check('isolation: second district crawled separately', async () => {
    const r = await post(B, '/api/districts', { url: 'http://127.0.0.1:4598' });
    lk = await waitReady(B, r.body.district.id);
    assert.equal(lk.status, 'ready', lk.message);
    assert.notEqual(lk.id, rb.id);
  });
  await check('isolation: Lakeside answers from Lakeside only', async () => {
    const r = await ask(lk.id, 'When is winter recess?'); // the test stub matches words literally
    assert.equal(r.body.found, true, JSON.stringify(r.body));
    assert.match(r.body.answer, /December 18, 2026/);
    assert.ok(!/December 21/.test(r.body.answer));
    assert.ok(r.body.citations.every((c) => c.url.startsWith('http://127.0.0.1:4598')));
  });
  await check('isolation: Riverbend-only facts are not found for Lakeside', async () => {
    const r = await ask(lk.id, 'How do I find my bus stop with the Stop Finder app?');
    assert.equal(r.body.answer, NOT_FOUND);
  });
  await check('reuse: same website within 7 days reuses the index', async () => {
    const r = await post(B, '/api/districts', { url: 'http://127.0.0.1:4599/' });
    assert.equal(r.body.reused, true);
    assert.equal(r.body.district.id, rb.id);
  });

  await check('upload: PDF-only district answers with document name and page', async () => {
    const c = await post(B, '/api/districts/upload-only', { name: 'Hillcrest Schools' });
    up = c.body.district;
    const fd = new FormData();
    fd.append('files', new Blob([fs.readFileSync(path.join(FIX, 'upload-transport-guide.pdf'))], { type: 'application/pdf' }), 'Hillcrest Family Guide.pdf');
    const u = await fetch(`${B}/api/districts/${up.id}/documents`, { method: 'POST', body: fd }).then(j);
    assert.equal(u.status, 200, JSON.stringify(u.body));
    assert.equal(u.body.results[0].status, 'partial'); // page 1 is a short title page
    const r = await ask(up.id, 'Is school lunch free for every student?');
    assert.equal(r.body.found, true, JSON.stringify(r.body));
    assert.equal(r.body.citations[0].url, null);
    assert.equal(r.body.citations[0].title, 'Hillcrest Family Guide');
    assert.equal(r.body.citations[0].page, 2);
  });
  await check('upload: non-PDF rejected clearly', async () => {
    const fd = new FormData();
    fd.append('files', new Blob(['hello'], { type: 'application/pdf' }), 'fake.pdf');
    const u = await fetch(`${B}/api/districts/${up.id}/documents`, { method: 'POST', body: fd }).then(j);
    assert.equal(u.body.results[0].status, 'failed');
    assert.match(u.body.results[0].message, /not a PDF/);
  });

  const lead = {
    fullName: 'Test Person',
    workEmail: 'test.person@exampledistrict.org',
    jobTitle: 'Assistant Superintendent',
    district: 'Example District',
    problem: 'Families call the front office with the same calendar questions every week.',
    demoDistrict: 'Riverbend Unified School District',
  };
  await check('leads: submitted too fast is refused', async () => {
    const r = await post(B, '/api/leads', { ...lead, started_at: Date.now() });
    assert.equal(r.status, 400);
  });
  await check('leads: honeypot filled is silently dropped', async () => {
    const r = await post(B, '/api/leads', { ...lead, website_url: 'http://spam', started_at: Date.now() - 10000 });
    assert.equal(r.status, 200);
  });
  await check('leads: missing field refused', async () => {
    const r = await post(B, '/api/leads', { ...lead, jobTitle: '', started_at: Date.now() - 10000 });
    assert.equal(r.status, 400);
  });
  await check('leads: valid request stored', async () => {
    const r = await post(B, '/api/leads', { ...lead, started_at: Date.now() - 10000 });
    assert.equal(r.status, 201);
  });
  await check('admin: leads hidden without password', async () => {
    const r = await fetch(B + '/admin');
    assert.equal(r.status, 401);
    const c = await fetch(B + '/admin/leads.csv');
    assert.equal(c.status, 401);
  });
  await check('admin: leads visible with password, exactly one stored', async () => {
    const auth = { authorization: 'Basic ' + Buffer.from('tomoclub:test-admin-pass').toString('base64') };
    const html = await fetch(B + '/admin', { headers: auth }).then((r) => r.text());
    assert.match(html, /test\.person@exampledistrict\.org/);
    assert.ok(!/http:\/\/spam/.test(html));
    const csv = await fetch(B + '/admin/leads.csv', { headers: auth }).then((r) => r.text());
    assert.equal(csv.trim().split('\r\n').length, 2);
  });
} finally {
  app.child.kill();
}

// Second instance: production-like settings (no private hosts, no AI key)
const prod = await startApp(4701, { ALLOW_PRIVATE_HOSTS: 'false', ANTHROPIC_API_KEY: '' });
try {
  await check('safety: private network address refused', async () => {
    const r = await post(prod.base, '/api/districts', { url: 'http://127.0.0.1:4599/' });
    const d = await waitReady(prod.base, r.body.district.id);
    assert.equal(d.status, 'failed');
    assert.match(d.message, /Private network/);
  });
  await check('safety: invalid address gives a clear message', async () => {
    const r = await post(prod.base, '/api/districts', { url: 'ftp://example.org' });
    assert.equal(r.status, 400);
  });
  await check('errors: AI not configured reported clearly', async () => {
    const h = await get(prod.base, '/api/health');
    assert.equal(h.body.ai, false);
    const c = await post(prod.base, '/api/districts/upload-only', { name: 'Hillcrest Schools' });
    const fd = new FormData();
    fd.append('files', new Blob([fs.readFileSync(path.join(FIX, 'upload-transport-guide.pdf'))], { type: 'application/pdf' }), 'guide.pdf');
    await fetch(`${prod.base}/api/districts/${c.body.district.id}/documents`, { method: 'POST', body: fd });
    const r = await post(prod.base, `/api/districts/${c.body.district.id}/ask`, { question: 'Is lunch free?' });
    assert.equal(r.status, 503);
    assert.match(r.body.error, /not configured/);
  });
  await check('admin: turned off when no password is set', async () => {
    const r = await fetch(prod.base + '/admin');
    assert.equal(r.status, 503);
  });
} finally {
  prod.child.kill();
  riverbend.close();
  lakeside.close();
  stub.close();
}

const failed = results.filter((r) => r[0] === 'FAIL');
console.log(`\n${results.length - failed.length} passed, ${failed.length} failed`);
process.exit(failed.length ? 1 : 0);
