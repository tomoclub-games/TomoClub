// Local test server: serves the site like Vercel (clean URLs) and runs the real /api functions, with the
// Apps Script replaced by an in-memory copy of data-capture/Code.gs (tests/gas-mock.mjs), and Instantly and
// Calendly answered by fakes. Usage: node tests/e2e-server.mjs [port]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { loadCodeGs } from './gas-mock.mjs';

const ROOT = path.resolve(new URL('..', import.meta.url).pathname);
const PORT = Number(process.argv[2] || 8100);
process.env.SHEET_WEBHOOK = 'https://script.google.test/exec';
process.env.SHEET_SECRET = 'test-secret';
process.env.ADMIN_PASSWORD = 'correct horse battery';
process.env.INSTANTLY_API_KEY = 'test-key';
process.env.INSTANTLY_ROUTES = JSON.stringify({ discovery_request: 'list:11111111-1111-1111-1111-111111111111', guide_download: 'campaign:22222222-2222-2222-2222-222222222222', build_with_us: 'list:11111111-1111-1111-1111-111111111111', partial_lead: 'list:33333333-3333-3333-3333-333333333333', ebook_download: 'campaign:22222222-2222-2222-2222-222222222222' });
process.env.CALENDLY_TOKEN = 'cal-token';

let gas = loadCodeGs(path.join(ROOT, 'data-capture/Code.gs'), { SHEET_SECRET: 'test-secret', SLACK_WEBHOOK_URL: 'https://hooks.slack.test/x', NOTIFY_EMAILS: 'team@tomoclub.org', PARTIAL_WAIT_MINUTES: '0' });
const instantly = [];
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, opt = {}) => {
  const u = String(url);
  const ok = (j) => new Response(JSON.stringify(j), { status: 200, headers: { 'Content-Type': 'application/json' } });
  if (u === process.env.SHEET_WEBHOOK) { const r = gas.post(JSON.parse(opt.body)); if (process.env.E2E_DEBUG && !r.ok) console.log('GAS refused', JSON.stringify(r)); return ok(r); }
  if (u.startsWith('https://api.instantly.ai/')) { instantly.push(JSON.parse(opt.body)); return ok({ status: 'success', leads_uploaded: 1 }); }
  if (/api\.calendly\.com\/scheduled_events\/EV1\/invitees\/IN1$/.test(u)) return ok({ resource: { name: 'Casey Booker', email: 'casey@district.k12.us', event: 'https://api.calendly.com/scheduled_events/EV1', questions_and_answers: [] } });
  if (/api\.calendly\.com\/scheduled_events\/EV1$/.test(u)) return ok({ resource: { start_time: '2026-11-25T16:00:00.000000Z' } });
  return realFetch(url, opt);
};

const handlers = {};
for (const f of ['lead', 'signup', 'partial', 'beat', 'admin']) handlers[f] = (await import(path.join(ROOT, 'api', f + '.js'))).default;
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.pdf': 'application/pdf' };

function shim(req, res, body) {
  const url = new URL(req.url, 'http://x');
  req.query = Object.fromEntries(url.searchParams);
  req.body = body;
  let code = 200;
  res.status = (c) => { code = c; return res; };
  res.json = (j) => { res.writeHead(code, { 'Content-Type': 'application/json', ...res._h }); res.end(JSON.stringify(j)); return res; };
  res._h = {};
  const origSet = res.setHeader.bind(res);
  res.setHeader = (k, v) => { res._h[k] = v; origSet(k, v); return res; };
  const origEnd = res.end.bind(res);
  res.end = (x) => { if (!res.headersSent) res.writeHead(code); return origEnd(x); };
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/__test/state') {
    const tabs = {}; for (const [n, s] of gas.sheets) tabs[n] = s.rows;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ tabs, slack: gas.sent.slack, mail: gas.sent.mail, instantly }));
  }
  if (url.pathname === '/__test/run-partial-check') {
    const n = gas.ctx.processPartialLeads();
    res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify({ sent: n }));
  }
  if (url.pathname === '/__test/reset') {
    gas = loadCodeGs(path.join(ROOT, 'data-capture/Code.gs'), gas.props); instantly.length = 0;
    res.writeHead(200); return res.end('ok');
  }
  const m = url.pathname.match(/^\/api\/([a-z]+)$/);
  if (m && handlers[m[1]]) {
    let raw = ''; for await (const c of req) raw += c;
    let body = raw; try { body = JSON.parse(raw); } catch (e) {}
    if (process.env.E2E_DEBUG) console.log('API', m[1], req.method, typeof body === 'object' ? (body.events || []).map((e) => e.name).join(',') : String(body).slice(0, 60));
    shim(req, res, body);
    try { await handlers[m[1]](req, res); } catch (e) { console.error(e); res.statusCode = 500; res.end('error'); }
    return;
  }
  let p = decodeURIComponent(url.pathname);
  let file = path.join(ROOT, p);
  if (!file.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  else if (!fs.existsSync(file) && fs.existsSync(file + '.html')) file += '.html';
  if (!fs.existsSync(file)) { res.writeHead(404); return res.end('not found'); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(PORT, () => console.log('test server on http://localhost:' + PORT));
