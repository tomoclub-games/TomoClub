// Browser check of the site's GA4 events, in headless Chrome, against the local files.
// - Serves the site the way scripts/serve.js does, and runs the real api/lead.js and api/signup.js for /api/*,
//   with the Google Sheet replaced by a stub that records the rows.
// - Every request to another site is blocked except fonts and the icon/script CDNs, so no test hit reaches
//   GA4, Meta, Clarity, LinkedIn, Leadsy, Calendly or the Build With Us Apps Script (that one gets a fake "ok").
// - Events are read from window.dataLayer, which the page fills even with GA4's own script blocked.
// Needs Google Chrome or Microsoft Edge. Set CHROME=<path to the browser> if it is somewhere unusual.
// Run: npm test   (or just this file: node --test tests/browser.test.mjs)
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { fakeCalendly, calendly } from './fake-calendly.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ── Local site + API ─────────────────────────────────────────────── */
process.env.SHEET_WEBHOOK = 'https://sheet.test/exec';
const sheetRows = [];
const realFetch = globalThis.fetch;
process.env.CALENDLY_TOKEN = 'test-token';
globalThis.fetch = async (url, o) => {
  const c = fakeCalendly(url, o);
  if (c) return c;
  if (url !== process.env.SHEET_WEBHOOK) return realFetch(url, o);
  sheetRows.push(...JSON.parse(o.body).rows);
  return { ok: true, json: async () => ({ ok: true }) };
};
const API = {
  '/api/lead': (await import('../api/lead.js')).default,
  '/api/signup': (await import('../api/signup.js')).default,
  '/api/call': (await import('../api/call.js')).default,
};
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.ico': 'image/x-icon', '.pdf': 'application/pdf', '.woff2': 'font/woff2' };
const isFile = (p) => fs.existsSync(p) && fs.statSync(p).isFile();
function resolveFile(urlPath) {
  const clean = decodeURIComponent(urlPath.split('?')[0].split('#')[0]);
  const m = /^\/podcast-([A-Za-z0-9_-]+)\/?$/.exec(clean);
  const p = path.join(ROOT, path.normalize(m ? `/podcast/episodes/${m[1]}/index.html` : clean));
  if (!p.startsWith(ROOT)) return null;
  for (const c of [p, path.join(p, 'index.html'), p + '.html']) if (isFile(c)) return c;
  return null;
}
const server = http.createServer(async (req, res) => {
  const route = API[req.url.split('?')[0]];
  if (route) {
    let raw = '';
    for await (const chunk of req) raw += chunk;
    let body = {};
    try { body = JSON.parse(raw); } catch (e) { /* empty */ }
    const out = { code: 200 };
    await route({ method: req.method, headers: req.headers, body },
      { setHeader() {}, status(c) { out.code = c; return this; }, json(j) { res.writeHead(out.code, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(j)); return this; } });
    return;
  }
  const file = resolveFile(req.url);
  if (!file) { res.writeHead(404); return res.end('Not found'); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

/* ── Chrome over the DevTools protocol ────────────────────────────── */
const ALLOWED_HOSTS = /^(localhost|fonts\.googleapis\.com|fonts\.gstatic\.com|unpkg\.com|cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com)$/;
const RECORDER = `(function () {
  var dl = window.dataLayer = window.dataLayer || [];
  var push = dl.push;
  dl.push = function () {
    for (var i = 0; i < arguments.length; i++) {
      try { var a = Array.prototype.slice.call(arguments[i]); if (a[0] === 'event') console.debug('__DL__' + JSON.stringify([a[1], a[2] || {}])); } catch (e) {}
    }
    return push.apply(dl, arguments);
  };
  window.open = function (u, t) { console.debug('__OPEN__' + JSON.stringify([u, t])); return null; };
  // Last listener to see a click: records whether the page stopped the link, then stops it so the test stays on the page.
  window.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a'); if (!a) return;
    console.debug('__CLICK__' + JSON.stringify({ href: a.getAttribute('href'), target: a.getAttribute('target'), prevented: e.defaultPrevented }));
    e.preventDefault();
  });
})();`;

let chrome, ws, sessionId, origin, msgId = 0;
const pending = new Map();
const listeners = new Set();
const events = [];        // [name, params, page]
const clicks = [];
const opens = [];
const errors = [];
const blocked = new Set();
const appsScriptPosts = [];

function send(method, params = {}, sid = sessionId) {
  const id = ++msgId;
  ws.send(JSON.stringify({ id, method, params, ...(sid ? { sessionId: sid } : {}) }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject, method }));
}
function waitFor(method, ms = 15000) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => { listeners.delete(l); reject(new Error('timeout waiting for ' + method)); }, ms);
    const l = (m) => { if (m.method === method) { clearTimeout(t); listeners.delete(l); resolve(m.params); } };
    listeners.add(l);
  });
}
async function js(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(expr.slice(0, 80) + ' → ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description));
  return r.result.value;
}
async function go(p, settle = 1200) {
  const loaded = waitFor('Page.loadEventFired');
  await send('Page.navigate', { url: origin + p });
  await loaded;
  await sleep(settle);
}
async function type(selector, text) {
  await js(`document.querySelector(${JSON.stringify(selector)}).focus()`);
  await send('Input.insertText', { text });
}
const mark = () => events.length;
const since = (n, name) => events.slice(n).filter((e) => !name || e[0] === name);

function onMessage(raw) {
  const m = JSON.parse(raw);
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id); pending.delete(m.id);
    return m.error ? p.reject(new Error(p.method + ': ' + m.error.message)) : p.resolve(m.result);
  }
  if (m.method === 'Runtime.consoleAPICalled') {
    const v = m.params.args[0] && m.params.args[0].value;
    if (typeof v !== 'string') return;
    if (v.startsWith('__DL__')) { const [name, params] = JSON.parse(v.slice(6)); events.push([name, params]); }
    else if (v.startsWith('__CLICK__')) clicks.push(JSON.parse(v.slice(9)));
    else if (v.startsWith('__OPEN__')) opens.push(JSON.parse(v.slice(8)));
  }
  if (m.method === 'Runtime.exceptionThrown') {
    const d = m.params.exceptionDetails;
    errors.push(((d.exception && d.exception.description) || d.text).split('\n')[0] + ' @ ' + (d.url || ''));
  }
  if (m.method === 'Fetch.requestPaused') {
    const { requestId, request } = m.params;
    const host = new URL(request.url).hostname;
    if (host === 'script.google.com') {
      appsScriptPosts.push(request.postData || '');
      send('Fetch.fulfillRequest', { requestId, responseCode: 200, responseHeaders: [{ name: 'Content-Type', value: 'text/plain' }], body: Buffer.from('ok').toString('base64') });
    } else if (ALLOWED_HOSTS.test(host)) {
      send('Fetch.continueRequest', { requestId });
    } else {
      blocked.add(host);
      send('Fetch.failRequest', { requestId, errorReason: 'BlockedByClient' });
    }
  }
  listeners.forEach((l) => l(m));
}

function findChrome() {
  const c = [process.env.CHROME,
    'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium'];
  return c.find((p) => p && fs.existsSync(p));
}

before(async () => {
  await new Promise((r) => server.listen(0, 'localhost', r));
  origin = 'http://localhost:' + server.address().port;
  const exe = findChrome();
  assert.ok(exe, 'Chrome or Edge not found; set CHROME=<path>');
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'tomo-chrome-'));
  chrome = spawn(exe, ['--headless=new', '--remote-debugging-port=0', '--user-data-dir=' + profile, '--no-first-run',
    '--no-default-browser-check', '--disable-gpu', '--disable-extensions', 'about:blank']);
  const wsUrl = await new Promise((resolve, reject) => {
    let buf = '';
    chrome.stderr.on('data', (d) => { buf += d; const m = /DevTools listening on (ws:\/\/\S+)/.exec(buf); if (m) resolve(m[1]); });
    setTimeout(() => reject(new Error('Chrome did not start')), 20000);
  });
  ws = new WebSocket(wsUrl);
  await new Promise((r) => ws.addEventListener('open', r));
  ws.addEventListener('message', (e) => onMessage(e.data));
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' }, null);
  ({ sessionId } = await send('Target.attachToTarget', { targetId, flatten: true }, null));
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Fetch.enable', { patterns: [{ urlPattern: 'http*://*' }] });
  await send('Page.setDownloadBehavior', { behavior: 'deny' }).catch(() => {});
  await send('Page.bringToFront');
  await send('Emulation.setFocusEmulationEnabled', { enabled: true });
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.addScriptToEvaluateOnNewDocument', { source: RECORDER });
});

after(async () => {
  try { ws.close(); } catch (e) { /* closed */ }
  if (chrome) chrome.kill();
  server.close();
});

const NAME = 'Testy McTestface', EMAIL = 'testy.person@district-example.org', ORG = 'Example Unified District';
const count = (list, name, pred = () => true) => list.filter((e) => e[0] === name && pred(e[1])).length;

test('home: book-a-call, FAQ, form steps and the lead', async () => {
  const pageStart = mark();
  await go('/', 3500); // over 3 seconds, so the form is not "too fast"
  let n = mark();
  await js(`document.querySelector('[data-book-call][data-event-label="hero"]').click()`);
  await sleep(300);
  assert.equal(count(since(n), 'book_call_click', (p) => p.cta_location === 'hero'), 1, 'book_call_click hero');
  assert.equal(count(since(n), 'cta_click'), 1, 'one cta_click, not two');
  assert.equal(since(n, 'cta_click')[0][1].cta_name, 'Book a call');
  assert.equal(await js(`!!document.querySelector('.tcb-overlay .tcb-box')`), true, 'booking pop-up opens');
  await js(`document.querySelector('.tcb-close').click()`);
  await sleep(300);
  assert.equal(await js(`!!document.querySelector('.tcb-overlay')`), false, 'booking pop-up closes');

  n = mark();
  await js(`document.querySelector('.h-faq summary').scrollIntoView(); document.querySelector('.h-faq summary').click()`);
  await js(`document.querySelector('.h-faq summary').click()`); // closing it sends nothing
  await sleep(200);
  assert.equal(count(since(n), 'faq_open'), 1);
  assert.equal(since(n, 'faq_open')[0][1].question, 'What does it cost?');

  // Scroll through the story section so its steps come on screen.
  await js(`(async () => { const s = document.querySelector('.h-story'); const top = s.getBoundingClientRect().top + scrollY;
    for (let y = top - 400; y < top + s.offsetHeight; y += 150) { scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); } })()`);
  await sleep(300);
  assert.ok(count(events, 'story_step_view') >= 1, 'story_step_view arrives');

  n = mark();
  await js(`document.getElementById('b2b-lead-form').scrollIntoView({block:'center'})`);
  await sleep(600);
  // The form may already have come on screen while scrolling to the FAQ just above it: count from page load.
  assert.equal(count(since(pageStart), 'form_view', (p) => p.form_name === 'home_discovery_form'), 1, 'form_view once');
  assert.equal(count(since(pageStart), 'form_view', (p) => p.form_name === 'guide_download'), 0, 'closed pop-up form is not a view');
  await type('#b2b-lead-form [name=name]', NAME);
  await type('#b2b-lead-form [name=email]', EMAIL);
  await js(`(() => { const f = document.getElementById('b2b-lead-form');
    const set = (n, v) => { const el = f.querySelector('[name="' + n + '"]'); if (el) el.value = v; };
    set('district', ${JSON.stringify(ORG)}); set('goal', 'Call me on +1 650 555 0101 about AI literacy');
    f.querySelectorAll('select[required]').forEach(s => { s.value = s.options[1].value; });
    f.requestSubmit(); })()`);
  await sleep(1500);
  assert.equal(count(since(n), 'form_start'), 1, 'form_start once');
  assert.equal(count(since(n), 'generate_lead', (p) => p.form_name === 'home_discovery_form'), 1, 'generate_lead');
  assert.match(await js(`document.querySelector('#b2b-lead-form .h-form-status').textContent`), /Thank you/);
  const metaLead = await js(`JSON.stringify((window.fbq && window.fbq.queue || []).map(a => Array.from(a)))`);
  assert.match(metaLead, /"track","Lead",\{"content_name":"home"\}/, 'Meta Lead');
  const row = sheetRows.find((r) => r.sheet === 'School leads' && r.data.email === EMAIL);
  assert.ok(row && /^[\w-]{8,64}$/.test(row.data.submission_id), 'row saved with a submission ID');

  n = mark();
  await js(`window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: false }))`);
  await sleep(200);
  assert.equal(count(since(n), 'form_abandon'), 0, 'no abandon after a sent form');
});

test('/faqs: FAQ opens and contact links', async () => {
  await go('/faqs');
  let n = mark();
  await js(`document.querySelector('.faq-question').click()`);
  await js(`document.querySelector('.faq-question').click()`);
  await sleep(200);
  assert.equal(count(since(n), 'faq_open'), 1);
  n = mark();
  const hasMail = await js(`!!document.querySelector('a[href^="mailto:"]')`);
  if (hasMail) {
    await js(`document.querySelector('a[href^="mailto:"]').click()`);
    assert.equal(count(since(n), 'contact_click', (p) => p.method === 'email'), 1);
  }
});

test('/guides: pop-up wording, form steps, download event and saved row', async () => {
  await go('/guides');
  let n = mark();
  const title = await js(`(() => { const b = document.querySelector('.open-download-modal'); b.click(); return b.getAttribute('data-title'); })()`);
  await sleep(600);
  assert.equal(count(since(n), 'form_view', (p) => p.form_name === 'guide_download'), 1, 'form_view when the pop-up opens');
  assert.match(await js(`document.getElementById('toolkit-download-form').textContent`), /Your download starts right away\./);
  await type('#toolkit-name', NAME);
  await type('#toolkit-email', EMAIL);
  await sleep(3100);
  await js(`document.getElementById('toolkit-download-form').requestSubmit()`);
  await sleep(1500);
  assert.equal(count(since(n), 'form_start'), 1);
  assert.equal(count(since(n), 'resource_download', (p) => p.resource_name === title), 1, 'resource_download with the guide title');
  const row = sheetRows.find((r) => r.sheet === 'Toolkit downloads' && r.data.email === EMAIL);
  assert.ok(row && row.data.submission_id, 'Toolkit row saved with a submission ID');
});

test('/guides: a pop-up sent within 3 seconds still downloads, but saves nothing', async () => {
  await go('/guides');
  const before = sheetRows.length, n = mark();
  await js(`document.querySelector('.open-download-modal').click()`);
  await sleep(500); // the pop-up fades in
  await type('#toolkit-name', 'Fast');
  await type('#toolkit-email', 'fast@district-example.org');
  await js(`document.getElementById('toolkit-download-form').requestSubmit()`);
  await sleep(1200);
  assert.equal(count(since(n), 'resource_download'), 1);
  assert.equal(sheetRows.length, before);
});

test('/guides: leaving a started pop-up form sends form_abandon', async () => {
  await go('/guides');
  await js(`document.querySelector('.open-download-modal').click()`);
  await sleep(500);
  await type('#toolkit-name', 'Leaver');
  await sleep(200);
  const n = mark();
  // The event the browser fires when the visitor leaves. Fired here directly: messages sent while a page
  // really unloads can be lost on their way to this test, though gtag still sends them.
  await js(`window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: false }))`);
  await sleep(200);
  assert.equal(count(since(n), 'form_abandon', (p) => p.form_name === 'guide_download'), 1);
  assert.equal(count(since(n), 'form_abandon'), 1, 'only the started form');
});

test('podcast episode page: shared call-to-action', async () => {
  const id = fs.readdirSync(path.join(ROOT, 'podcast/episodes'))[0];
  await go('/podcast-' + id);
  const n = mark();
  const clicked = await js(`(() => { const a = document.querySelector('[data-book-call], a[href*="calendly.com"]'); if (!a) return false; a.click(); return true; })()`);
  assert.ok(clicked, 'a book-a-call link exists');
  await sleep(300);
  assert.equal(count(since(n), 'book_call_click'), 1);
  assert.ok(count(since(n), 'cta_click') <= 1, 'cta_click not doubled');
  assert.equal(await js(`typeof window.tomoTrack`), 'function');
});

test('article page: tracking loads', async () => {
  const slug = fs.readdirSync(path.join(ROOT, 'articles')).find((d) => isFile(path.join(ROOT, 'articles', d, 'index.html')));
  await go('/articles/' + slug);
  assert.equal(await js(`typeof window.tomoTrack`), 'function');
});

test('/leaders-of-tomorrow: ebook form', async () => {
  const n = mark(); // the hero form is on screen from the start
  await go('/leaders-of-tomorrow', 3500);
  await js(`document.getElementById('hero-form').scrollIntoView({block:'center'})`);
  await sleep(600);
  await type('#hero-form [name=firstName]', 'Testy');
  await type('#hero-form [name=email]', EMAIL);
  await js(`document.getElementById('hero-form').requestSubmit()`);
  await sleep(1500);
  assert.equal(count(since(n), 'form_view', (p) => p.form_name === 'ebook_hero'), 1);
  assert.equal(count(since(n), 'form_start', (p) => p.form_name === 'ebook_hero'), 1);
  assert.equal(count(since(n), 'resource_download', (p) => p.resource_name === 'Leaders of Tomorrow ebook'), 1);
  const row = sheetRows.find((r) => r.sheet === 'E-book requests' && r.data.email === EMAIL);
  assert.ok(row && row.data.submission_id, 'E-book row saved with a submission ID');
});

test('/build-with-us: new-tab call links and the form flow are unchanged; events are counted', async () => {
  await go('/build-with-us');
  let n = mark();
  const c0 = clicks.length;
  const links = await js(`document.querySelectorAll('a[href*="calendly.com"]').length`);
  await js(`document.querySelectorAll('a[href*="calendly.com"]').forEach(a => a.click())`);
  await sleep(300);
  const seen = clicks.slice(c0);
  assert.equal(seen.length, links);
  assert.ok(seen.every((c) => c.target === '_blank' && c.prevented === false), 'links still open Calendly in a new tab');
  assert.equal(count(since(n), 'book_call_click'), links);

  n = mark();
  await js(`document.getElementById('project-form').scrollIntoView({block:'center'})`);
  await sleep(600);
  await type('#f-name', NAME);
  await type('#f-org', ORG);
  await type('#f-email', EMAIL);
  await type('#f-goal', 'Testing');
  const nav = waitFor('Page.loadEventFired');
  await js(`document.getElementById('project-form').requestSubmit()`);
  await nav;
  await sleep(1000);
  assert.equal(appsScriptPosts.length, 1, 'posted once to its own Apps Script');
  assert.match(appsScriptPosts[0], /email=testy\.person%40district-example\.org/);
  assert.equal(await js('location.pathname'), '/build-with-us/thank-you', 'redirected to the thank-you page');
  assert.equal(count(since(n), 'lead_submitted'), 1, 'existing lead_submitted still fires');
  assert.equal(count(since(n), 'generate_lead', (p) => p.form_name === 'build_with_us'), 1);
  n = mark();
  await go('/build-with-us/thank-you');
  assert.equal(count(since(n), 'generate_lead'), 0, 'a reload does not count the lead again');
});

test('booking pop-up: times are ready on open, pick a time, details, booked in Calendly, row saved', async () => {
  calendly.reset();
  await go('/', 2500); // the open times are fetched quietly after load
  assert.ok(calendly.seen.some((u) => u.includes('available_times')), 'times fetched before any click');
  const n = mark();
  await js(`document.querySelector('[data-book-call][data-event-label="nav"]').click()`);
  await sleep(150);
  assert.equal(await js(`document.querySelectorAll('.tcb-time').length`), 2, 'first open day and its times show at once');
  assert.match(await js(`document.querySelector('.tcb-tz').textContent`), /^Times in /);
  assert.equal(await js(`document.querySelector('[data-next]').disabled`), true);
  await js(`document.querySelector('.tcb-time').click()`);
  await js(`document.querySelector('[data-next]').click()`);
  await sleep(100);
  assert.equal(await js(`document.querySelector('[data-book]').disabled`), true, 'book button waits for the details');
  await type('.tcb-box input[name=name]', NAME);
  await type('.tcb-box input[name=email]', EMAIL);
  await js(`document.querySelector('[data-guests]').click()`);
  await type('.tcb-box input[name=guests]', 'second.person@district-example.org');
  await type('.tcb-box textarea[name=reason]', 'AI training for our teachers');
  assert.equal(await js(`document.querySelector('[data-book]').disabled`), false);
  await js(`document.querySelector('[data-book]').click()`);
  await sleep(800);
  assert.match(await js(`document.querySelector('.tcb-done h2').textContent`), /booked/);
  assert.equal(calendly.bookings.length, 1);
  assert.equal(calendly.bookings[0].invitee.email, EMAIL);
  assert.deepEqual(calendly.bookings[0].event_guests, ['second.person@district-example.org']);
  const row = sheetRows.find((r) => r.sheet === 'School leads' && r.data.type === 'call_booked' && r.data.email === EMAIL);
  assert.ok(row, 'call_booked row saved');
  assert.equal(row.data.page, '/');
  assert.equal(count(since(n), 'form_view', (p) => p.form_name === 'book_call'), 1);
  assert.equal(count(since(n), 'form_start', (p) => p.form_name === 'book_call'), 1);
  assert.equal(count(since(n), 'book_call_scheduled'), 1);
  await js(`document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })); document.querySelector('.tcb-box').dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))`);
  await sleep(300);
  assert.equal(await js(`!!document.querySelector('.tcb-overlay')`), false, 'Escape closes it');
});

test('booking pop-up: when times cannot load, the Calendly page is offered', async () => {
  calendly.reset();
  calendly.down = true;
  try {
    await go('/', 2500);
    await js(`document.querySelector('[data-book-call][data-event-label="hero"]').click()`);
    await sleep(500);
    assert.equal(await js(`!!document.querySelector('.tcb-box [data-calendly]')`), true, 'Calendly fallback offered');
    assert.equal(await js(`!!document.querySelector('.tcb-box [data-retry]')`), true, 'try again offered');
  } finally {
    calendly.down = false;
  }
  await js(`document.querySelector('.tcb-close').click()`);
});

test('no personal data in any event; nothing reached outside services; no script errors', () => {
  const all = JSON.stringify(events);
  for (const s of [NAME, EMAIL, ORG, 'Testy', '650 555 0101', 'district-example']) assert.ok(!all.includes(s), 'event data contains ' + s);
  assert.ok(events.length > 20, 'events were recorded');
  const ours = errors.filter((e) => /localhost/.test(e));
  assert.deepEqual(ours, [], 'script errors on the site');
  console.log('# events recorded:', events.length, '| blocked hosts:', [...blocked].sort().join(', '));
});
