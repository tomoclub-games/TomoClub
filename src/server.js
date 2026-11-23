import express from 'express';
import multer from 'multer';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config, aiConfigured } from './config.js';
import { db, now } from './db.js';
import { startDistrict, createUploadOnlyDistrict, addUploadedPdf } from './crawler.js';
import { answerQuestion, suggestedQuestions } from './assistant.js';
import { FetchError } from './safeFetch.js';
import { AiError } from './llm.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
if (config.trustProxy) app.set('trust proxy', 1);
app.disable('x-powered-by');

app.use((req, res, next) => {
  res.set({
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'X-Frame-Options': 'SAMEORIGIN',
    'Content-Security-Policy':
      "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'",
  });
  next();
});
app.use(express.json({ limit: '64kb' }));

// ---- simple per-IP hourly rate limits ----
const buckets = new Map();
function limit(kind) {
  return (req, res, next) => {
    const key = `${kind}:${req.ip}`;
    const t = Date.now();
    const arr = (buckets.get(key) || []).filter((x) => t - x < 3600000);
    if (arr.length >= config.limits[kind]) {
      return res.status(429).json({ error: 'Too many requests from this connection. Please try again later.' });
    }
    arr.push(t);
    buckets.set(key, arr);
    next();
  };
}
setInterval(() => {
  const t = Date.now();
  for (const [k, arr] of buckets) if (!arr.some((x) => t - x < 3600000)) buckets.delete(k);
}, 600000).unref();

// Whole-site daily caps (reset at midnight UTC or on restart).
const daily = { day: '', ask: 0, crawl: 0 };
function dailyCap(kind) {
  return (req, res, next) => {
    const today = new Date().toISOString().slice(0, 10);
    if (daily.day !== today) Object.assign(daily, { day: today, ask: 0, crawl: 0 });
    if (daily[kind] >= config.daily[kind]) {
      return res.status(429).json({
        error: "This demo has reached today's limit. Request a demo below and we will walk you through it with your own district.",
      });
    }
    daily[kind]++;
    next();
  };
}

const getDistrict = (id) => db.prepare('SELECT * FROM districts WHERE id = ?').get(id);

function districtView(d) {
  const sources = db
    .prepare('SELECT id, url, title, kind, status, reason, pages FROM sources WHERE district_id = ? ORDER BY id')
    .all(d.id);
  const categories = JSON.parse(d.categories || '[]');
  return {
    id: d.id,
    name: d.name,
    website: d.website,
    status: d.status,
    message: d.message,
    currentUrl: d.current_url,
    categories,
    suggestedQuestions: d.status === 'ready' ? suggestedQuestions(categories) : [],
    counts: {
      pages: sources.filter((s) => s.kind === 'page' && ['ok', 'partial'].includes(s.status)).length,
      pdfs: sources.filter((s) => s.kind !== 'page' && ['ok', 'partial'].includes(s.status)).length,
      notRead: sources.filter((s) => ['failed', 'skipped'].includes(s.status)).length,
    },
    sources,
    updatedAt: d.updated_at,
  };
}

// ---- API ----
app.get('/api/health', (req, res) => {
  res.json({ ok: true, ai: aiConfigured(), model: aiConfigured() ? config.answerModel : null });
});

app.post('/api/districts', limit('crawl'), (req, res) => {
  try {
    const { district, reused } = startDistrict(req.body?.url, {
      refresh: req.body?.refresh === true,
      // only brand-new website reads count toward the daily cap; reused districts are free
      beforeNewCrawl: () => {
        const today = new Date().toISOString().slice(0, 10);
        if (daily.day !== today) Object.assign(daily, { day: today, ask: 0, crawl: 0 });
        if (daily.crawl >= config.daily.crawl) {
          throw new FetchError("This demo has read its limit of new district websites for today. Request a demo below and we will walk you through it with your own district.", 'daily_limit');
        }
        daily.crawl++;
      },
    });
    res.status(reused ? 200 : 202).json({ reused, district: districtView(district) });
  } catch (e) {
    const msg = e instanceof FetchError || e instanceof TypeError ? e.message.replace(/^Invalid URL.*/, 'That is not a valid web address.') : 'Could not start.';
    res.status(e.code === 'busy' ? 503 : e.code === 'daily_limit' ? 429 : 400).json({ error: msg });
  }
});

app.post('/api/districts/upload-only', limit('crawl'), (req, res) => {
  try {
    res.status(201).json({ district: districtView(createUploadOnlyDistrict(req.body?.name)) });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

app.get('/api/districts/:id', (req, res) => {
  const d = getDistrict(req.params.id);
  if (!d) return res.status(404).json({ error: 'District not found.' });
  res.json({ district: districtView(d) });
});

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: config.maxPdfBytes, files: 5 },
  fileFilter: (req, file, cb) => cb(null, /\.pdf$/i.test(file.originalname) || file.mimetype === 'application/pdf'),
});
app.post('/api/districts/:id/documents', limit('upload'), (req, res) => {
  upload.array('files', 5)(req, res, async (err) => {
    if (err) {
      return res.status(400).json({ error: err.code === 'LIMIT_FILE_SIZE' ? `Each PDF must be under ${Math.round(config.maxPdfBytes / 1048576)} MB.` : 'Upload failed.' });
    }
    const d = getDistrict(req.params.id);
    if (!d) return res.status(404).json({ error: 'District not found.' });
    if (!req.files?.length) return res.status(400).json({ error: 'Please choose one or more PDF files.' });
    const results = [];
    for (const f of req.files) {
      if (!f.buffer.subarray(0, 5).toString('latin1').startsWith('%PDF')) {
        results.push({ status: 'failed', message: `${f.originalname}: not a PDF file.` });
        continue;
      }
      results.push(await addUploadedPdf(d.id, f.originalname, f.buffer));
    }
    res.json({ results, district: districtView(getDistrict(d.id)) });
  });
});

app.post('/api/districts/:id/ask', limit('ask'), dailyCap('ask'), async (req, res) => {
  const d = getDistrict(req.params.id);
  if (!d) return res.status(404).json({ error: 'District not found.' });
  if (d.status !== 'ready') return res.status(409).json({ error: 'This district is still being processed.' });
  const question = String(req.body?.question || '').trim();
  if (!question) return res.status(400).json({ error: 'Please type a question.' });
  if (question.length > 500) return res.status(400).json({ error: 'Please keep questions under 500 characters.' });
  const history = Array.isArray(req.body?.history)
    ? req.body.history.slice(-2).map((h) => ({ question: String(h.question || '').slice(0, 500), answer: String(h.answer || '').slice(0, 800) }))
    : [];
  try {
    res.json(await answerQuestion(d, question, history));
  } catch (e) {
    if (e instanceof AiError) return res.status(e.code === 'not_configured' ? 503 : 502).json({ error: e.message });
    console.error(e);
    res.status(500).json({ error: 'Something went wrong while answering. Please try again.' });
  }
});

// ---- Leads ----
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
app.post('/api/leads', limit('lead'), async (req, res) => {
  const b = req.body || {};
  // Spam checks: hidden field must stay empty, form open at least a few seconds, few links.
  if (b.website_url) return res.json({ ok: true });
  const elapsed = (Date.now() - Number(b.started_at || 0)) / 1000;
  if (!Number.isFinite(elapsed) || elapsed < config.minFormSeconds) {
    return res.status(400).json({ error: 'Please take a moment to fill in the form, then send it again.' });
  }
  const f = {
    fullName: String(b.fullName || '').trim().slice(0, 120),
    workEmail: String(b.workEmail || '').trim().toLowerCase().slice(0, 200),
    jobTitle: String(b.jobTitle || '').trim().slice(0, 120),
    district: String(b.district || '').trim().slice(0, 200),
    problem: String(b.problem || '').trim().slice(0, 3000),
    demoDistrict: String(b.demoDistrict || '').trim().slice(0, 200),
  };
  const missing = ['fullName', 'workEmail', 'jobTitle', 'district', 'problem'].filter((k) => !f[k]);
  if (missing.length) return res.status(400).json({ error: 'Please fill in every field.' });
  if (!EMAIL_RE.test(f.workEmail)) return res.status(400).json({ error: 'Please enter a valid work email.' });
  if ((f.problem.match(/https?:\/\//g) || []).length > 2) return res.status(400).json({ error: 'Please remove the links and describe the problem in words.' });

  const ipHash = crypto.createHash('sha256').update(`${config.ipHashSalt}:${req.ip}`).digest('hex').slice(0, 16);
  const r = db
    .prepare(
      `INSERT INTO leads (full_name, work_email, job_title, school_district, problem, demo_district, ip_hash, user_agent, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    )
    .run(f.fullName, f.workEmail, f.jobTitle, f.district, f.problem, f.demoDistrict || null, ipHash, String(req.get('user-agent') || '').slice(0, 300), now());
  const leadId = Number(r.lastInsertRowid);

  // Optional: forward to the team's existing intake (Apps Script, Zapier, Slack workflow...).
  if (config.leadWebhookUrl) {
    let status = 'failed';
    try {
      const w = await fetch(config.leadWebhookUrl, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ source: 'district-assistant', leadId, ...f, createdAt: now() }),
        signal: AbortSignal.timeout(8000),
      });
      status = w.ok ? 'sent' : `http_${w.status}`;
    } catch {
      status = 'failed';
    }
    db.prepare('UPDATE leads SET webhook_status = ? WHERE id = ?').run(status, leadId);
  }
  res.status(201).json({ ok: true });
});

// ---- Admin (leads are never public) ----
function adminAuth(req, res, next) {
  if (!config.adminPassword) return res.status(503).send('Admin is turned off. Set ADMIN_PASSWORD to turn it on.');
  const [scheme, value] = String(req.get('authorization') || '').split(' ');
  if (scheme === 'Basic' && value) {
    const [user, ...rest] = Buffer.from(value, 'base64').toString('utf8').split(':');
    const pass = rest.join(':');
    const ok = (a, b) => a.length === b.length && crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));
    if (ok(user, config.adminUser) && ok(pass, config.adminPassword)) return next();
  }
  res.set('WWW-Authenticate', 'Basic realm="TomoClub leads"').status(401).send('Sign in required.');
}
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

app.get('/admin', adminAuth, (req, res) => {
  const leads = db.prepare('SELECT * FROM leads ORDER BY id DESC LIMIT 500').all();
  const districts = db
    .prepare(
      `SELECT d.name, d.website, d.status, d.created_at,
        (SELECT COUNT(*) FROM sources s WHERE s.district_id = d.id AND s.status IN ('ok','partial')) AS read_count
       FROM districts d ORDER BY d.created_at DESC LIMIT 100`,
    )
    .all();
  res.set('Cache-Control', 'no-store').send(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Leads | District Assistant</title><link rel="stylesheet" href="/styles.css"></head><body class="admin">
<main class="wrap"><h1>Demo requests (${leads.length})</h1><p><a class="btn btn-secondary" href="/admin/leads.csv">Download CSV</a></p>
<div class="table-scroll"><table><thead><tr><th>Received (UTC)</th><th>Name</th><th>Work email</th><th>Job title</th><th>School district</th><th>Problem to solve</th><th>Demo district</th><th>Forwarded</th></tr></thead><tbody>
${leads.map((l) => `<tr><td>${esc(l.created_at.replace('T', ' ').slice(0, 16))}</td><td>${esc(l.full_name)}</td><td><a href="mailto:${esc(l.work_email)}">${esc(l.work_email)}</a></td><td>${esc(l.job_title)}</td><td>${esc(l.school_district)}</td><td>${esc(l.problem)}</td><td>${esc(l.demo_district)}</td><td>${esc(l.webhook_status || 'not set up')}</td></tr>`).join('') || '<tr><td colspan="8">No requests yet.</td></tr>'}
</tbody></table></div>
<h2>Districts tried (${districts.length})</h2><div class="table-scroll"><table><thead><tr><th>Started (UTC)</th><th>District</th><th>Website</th><th>Status</th><th>Sources read</th></tr></thead><tbody>
${districts.map((d) => `<tr><td>${esc(d.created_at.replace('T', ' ').slice(0, 16))}</td><td>${esc(d.name)}</td><td>${esc(d.website || 'uploads only')}</td><td>${esc(d.status)}</td><td>${d.read_count}</td></tr>`).join('')}
</tbody></table></div></main></body></html>`);
});

app.get('/admin/leads.csv', adminAuth, (req, res) => {
  const rows = db.prepare('SELECT created_at, full_name, work_email, job_title, school_district, problem, demo_district, webhook_status FROM leads ORDER BY id DESC').all();
  const cell = (v) => {
    let s = String(v ?? '');
    if (/^[=+\-@]/.test(s)) s = `'${s}`; // stop spreadsheet formulas
    return `"${s.replace(/"/g, '""')}"`;
  };
  const header = ['Received (UTC)', 'Full name', 'Work email', 'Job title', 'School district', 'Problem', 'Demo district', 'Forwarded'];
  const csv = [header.map(cell).join(','), ...rows.map((r) => Object.values(r).map(cell).join(','))].join('\r\n');
  res.set({ 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'attachment; filename="district-assistant-leads.csv"', 'Cache-Control': 'no-store' }).send(csv);
});

// ---- Front end ----
app.use(express.static(path.join(__dirname, '..', 'public'), { extensions: ['html'], maxAge: '1h' }));
app.use('/api', (req, res) => res.status(404).json({ error: 'Not found.' }));

// Processing that was interrupted by a restart cannot resume; mark it clearly.
db.prepare("UPDATE districts SET status = 'failed', message = 'Processing was interrupted. Please start again.' WHERE status IN ('queued','processing')").run();

export const server = app.listen(config.port, () => {
  console.log(`District Assistant running on http://localhost:${config.port} (AI ${aiConfigured() ? 'configured' : 'NOT configured'})`);
});
export default app;
