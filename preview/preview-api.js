// PREVIEW BACKEND. Runs the prototype's /api inside the browser so the real
// interface (app.js, unchanged) can be used without a server:
// - saved test districts replay the real crawler's output (browsers cannot read other websites)
// - PDF uploads are read in the browser with the same code as the server
// - questions use the same search words, prompts and citation checks, answered by Claude via `sample`
// - leads are saved to this artifact's private store via `db`
import { chunkText, stripHeadingMarkers } from './shared/text.js';
import { parsePdfWith } from './shared/pdf.js';
import { detectCategories } from './shared/categories.js';
import {
  NOT_FOUND,
  STOP,
  localTerms,
  cleanTerms,
  expansionPrompt,
  diversify,
  answerPrompt,
  parseJsonObject,
  finishAnswer,
  suggestedQuestions,
} from './shared/answering.js';
import { stemmer } from './vendor/stemmer.js';

const MIN_FORM_SECONDS = 3;
const MAX_PDF_BYTES = 25 * 1024 * 1024;
const districts = new Map(); // id -> { id, name, website, status, message, currentUrl, categories, sources[], chunks[], updatedAt }
let savedData = null;
let nextSourceId = 100000;

// ---------- capabilities ----------
const cap = (name) => (window.claude?.use ? window.claude.use(name).catch(() => null) : Promise.resolve(null));
const samplePromise = cap('sample');
const dbPromise = cap('db');

// ---------- helpers ----------
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const nowIso = () => new Date().toISOString();
const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2));
const baseHost = (h) => h.toLowerCase().replace(/^www\./, '');

async function loadSaved() {
  if (!savedData) savedData = await fetch('data/saved-districts.json').then((r) => r.json());
  return savedData;
}

function view(d) {
  const s = d.sources;
  return {
    id: d.id,
    name: d.name,
    website: d.website,
    status: d.status,
    message: d.message,
    currentUrl: d.currentUrl || null,
    categories: d.categories,
    suggestedQuestions: d.status === 'ready' ? suggestedQuestions(d.categories) : [],
    counts: {
      pages: s.filter((x) => x.kind === 'page' && ['ok', 'partial'].includes(x.status)).length,
      pdfs: s.filter((x) => x.kind !== 'page' && ['ok', 'partial'].includes(x.status)).length,
      notRead: s.filter((x) => ['failed', 'skipped'].includes(x.status)).length,
    },
    sources: s.map(({ id, url, title, kind, status, reason, pages }) => ({ id, url, title, kind, status, reason, pages })),
    updatedAt: d.updatedAt,
  };
}

function refreshCategories(d) {
  const docs = d.sources
    .filter((s) => ['ok', 'partial'].includes(s.status))
    .map((s) => ({ title: s.title, url: s.url, text: d.chunks.filter((c) => c.source_id === s.id).map((c) => c.body).join(' ') }));
  d.categories = detectCategories(docs);
  d.index = null; // rebuild search index on next question
}

// ---------- website (saved crawl replay) ----------
function normalizeInputUrl(input) {
  let s = String(input || '').trim();
  if (!s) throw new Error('Please enter a district website address.');
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(s) && !/^https?:\/\//i.test(s)) throw new Error('Only http and https addresses can be read.');
  if (!/^https?:\/\//i.test(s)) s = `https://${s}`;
  try {
    return new URL(s);
  } catch {
    throw new Error('That is not a valid web address.');
  }
}

async function startDistrict(body) {
  let u;
  try {
    u = normalizeInputUrl(body?.url);
  } catch (e) {
    return json({ error: e.message }, 400);
  }
  const data = await loadSaved();
  const saved = data.districts.find((d) => d.host === baseHost(u.hostname));
  if (!saved) {
    return json(
      {
        error: `Preview limit: reading a live website such as ${u.hostname} runs on the deployed server, because a browser page is not allowed to read other websites. Try one of the saved test districts, or start with the district's PDFs below.`,
      },
      400,
    );
  }
  for (const d of districts.values()) {
    if (d.host === saved.host && d.status !== 'failed') return json({ reused: true, district: view(d) });
  }
  const d = {
    id: uuid(),
    host: saved.host,
    name: saved.host,
    website: saved.website,
    status: 'processing',
    message: 'Replaying the saved crawl: reading the home page',
    currentUrl: saved.website,
    categories: [],
    sources: [],
    chunks: [],
    updatedAt: nowIso(),
  };
  districts.set(d.id, d);
  // Replay the crawler's real record one source at a time.
  const order = saved.sources.slice();
  let i = 0;
  const tick = () => {
    if (i < order.length) {
      const s = order[i++];
      d.sources.push(s);
      d.chunks.push(...saved.chunks.filter((c) => c.source_id === s.id));
      if (i === 1) d.name = saved.name;
      const v = view(d);
      d.currentUrl = s.url;
      d.message = `Replaying the saved crawl: read ${v.counts.pages} pages and ${v.counts.pdfs} PDFs so far`;
      setTimeout(tick, 450);
    } else {
      d.categories = saved.categories;
      d.status = 'ready';
      d.message = saved.message;
      d.currentUrl = null;
      d.updatedAt = data.generatedAt;
    }
  };
  setTimeout(tick, 600);
  return json({ reused: false, district: view(d) }, 202);
}

// ---------- uploads ----------
let unpdfPromise = null;
const getUnpdf = () => (unpdfPromise ||= import('./vendor/unpdf.mjs'));

function addSource(d, src) {
  const s = { id: nextSourceId++, url: null, reason: null, pages: null, chars: 0, ...src };
  d.sources.push(s);
  return s;
}

async function addUploadedPdf(d, file) {
  const name = file.name || 'Uploaded PDF';
  const title = name.replace(/\.pdf$/i, '').slice(0, 200);
  if (file.size > MAX_PDF_BYTES) return { status: 'failed', message: `${name}: larger than 25 MB.` };
  const buf = new Uint8Array(await file.arrayBuffer());
  if (String.fromCharCode(...buf.subarray(0, 4)) !== '%PDF') return { status: 'failed', message: `${name}: not a PDF file.` };
  let parsed;
  try {
    parsed = await parsePdfWith(await getUnpdf(), buf);
  } catch (e) {
    console.error(e);
    addSource(d, { title, kind: 'upload', status: 'failed', reason: 'The PDF could not be opened (damaged or password protected).' });
    return { status: 'failed', message: `${name}: could not be opened.` };
  }
  if (parsed.pagesWithText === 0) {
    addSource(d, { title, kind: 'upload', status: 'failed', pages: parsed.totalPages, reason: 'Scanned PDF with no text layer. Text recognition (OCR) is not turned on in this prototype.' });
    return { status: 'failed', message: `${name}: scanned PDF with no readable text.` };
  }
  const partial = parsed.pagesWithText < parsed.totalPages;
  const s = addSource(d, {
    title,
    kind: 'upload',
    status: partial ? 'partial' : 'ok',
    pages: parsed.totalPages,
    chars: parsed.pages.reduce((a, p) => a + p.length, 0),
    reason: partial ? `${parsed.totalPages - parsed.pagesWithText} of ${parsed.totalPages} pages had no readable text.` : null,
  });
  parsed.pages.forEach((text, i) => {
    for (const c of chunkText(text)) d.chunks.push({ body: stripHeadingMarkers(c.body), heading: c.heading || '', title, source_id: s.id, page: i + 1 });
  });
  refreshCategories(d);
  if (d.status !== 'processing') {
    d.status = 'ready';
    d.message = 'Documents ready.';
  }
  d.updatedAt = nowIso();
  return { status: partial ? 'partial' : 'ok', message: `${name}: ${parsed.pagesWithText} of ${parsed.totalPages} pages read.` };
}

// ---------- search (BM25 with heading and title weighted, like the server) ----------
const tokenize = (s) => (String(s).toLowerCase().match(/[a-z0-9]+/g) || []).map((w) => stemmer(w));

function buildIndex(d) {
  const docs = d.chunks.map((c) => {
    const tf = new Map();
    const add = (text, w) => {
      for (const t of tokenize(text)) tf.set(t, (tf.get(t) || 0) + w);
    };
    add(c.body, 1);
    add(c.heading, 1.6);
    add(c.title, 1.6);
    const len = tokenize(c.body).length + tokenize(c.heading).length + tokenize(c.title).length;
    return { c, tf, len };
  });
  const df = new Map();
  for (const x of docs) for (const t of x.tf.keys()) df.set(t, (df.get(t) || 0) + 1);
  const avg = docs.reduce((a, x) => a + x.len, 0) / Math.max(1, docs.length);
  return { docs, df, avg, n: docs.length };
}

function search(d, terms) {
  const tokens = [...new Set(cleanTerms(terms).flatMap((t) => t.split(' ')).filter((w) => w.length > 1 && !STOP.has(w)).map((w) => stemmer(w)))];
  if (!tokens.length) return [];
  d.index ||= buildIndex(d);
  const { docs, df, avg, n } = d.index;
  const k1 = 1.2;
  const b = 0.75;
  const scored = [];
  for (const x of docs) {
    let score = 0;
    for (const t of tokens) {
      const f = x.tf.get(t);
      if (!f) continue;
      const idf = Math.log(1 + (n - df.get(t) + 0.5) / (df.get(t) + 0.5));
      score += (idf * (f * (k1 + 1))) / (f + k1 * (1 - b + (b * x.len) / avg));
    }
    if (score > 0) scored.push({ score, x });
  }
  scored.sort((a, b2) => b2.score - a.score);
  const rows = scored.slice(0, 60).map(({ x }) => {
    const src = d.sources.find((s) => s.id === x.c.source_id) || {};
    return { ...x.c, url: src.url || null, kind: src.kind };
  });
  return diversify(rows);
}

// ---------- answering via Claude (`sample`) ----------
async function askClaude(sample, system, user, opts) {
  const res = await sample(`${system}\n\n=====\n\n${user}`, opts);
  return res?.text || '';
}

async function answer(d, body) {
  if (d.status !== 'ready') return json({ error: 'This district is still being processed.' }, 409);
  const q = String(body?.question || '').trim();
  if (!q) return json({ error: 'Please type a question.' }, 400);
  if (q.length > 500) return json({ error: 'Please keep questions under 500 characters.' }, 400);
  const history = Array.isArray(body?.history) ? body.history.slice(-2) : [];
  const sample = await samplePromise;
  if (!sample) return json({ error: 'AI answers are not available in this view. Open the preview on claude.ai while signed in.' }, 503);
  try {
    let extra = [];
    try {
      const p = expansionPrompt(q, history);
      const obj = parseJsonObject(await askClaude(sample, p.system, p.user, { modelTier: 'quick' }));
      if (obj && Array.isArray(obj.terms)) extra = obj.terms.map(String).slice(0, 10);
    } catch (e) {
      if (e?.code === 'not_granted') throw e;
    }
    const hits = search(d, [...localTerms(q), ...extra]);
    if (!hits.length) return json({ found: false, answer: NOT_FOUND, citations: [] });
    const p = answerPrompt(d.name, hits, q, history);
    const text = await askClaude(sample, p.system, p.user, { cache: false });
    return json(finishAnswer(text, hits));
  } catch (e) {
    console.error(e);
    if (e?.code === 'not_granted') return json({ error: 'Claude needs your permission to answer. Ask again and choose Allow.' }, 503);
    if (e?.code === 'rate_limited') return json({ error: 'The AI service is busy right now. Please try again in a minute.' }, 503);
    return json({ error: 'The AI service is unavailable right now. Please try again in a minute.' }, 502);
  }
}

// ---------- leads via `db` ----------
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
async function saveLead(b) {
  if (b?.website_url) return json({ ok: true }); // honeypot
  const elapsed = (Date.now() - Number(b?.started_at || 0)) / 1000;
  if (!Number.isFinite(elapsed) || elapsed < MIN_FORM_SECONDS) return json({ error: 'Please take a moment to fill in the form, then send it again.' }, 400);
  const f = {
    fullName: String(b.fullName || '').trim().slice(0, 120),
    workEmail: String(b.workEmail || '').trim().toLowerCase().slice(0, 200),
    jobTitle: String(b.jobTitle || '').trim().slice(0, 120),
    district: String(b.district || '').trim().slice(0, 200),
    problem: String(b.problem || '').trim().slice(0, 3000),
    demoDistrict: String(b.demoDistrict || '').trim().slice(0, 200),
  };
  if (['fullName', 'workEmail', 'jobTitle', 'district', 'problem'].some((k) => !f[k])) return json({ error: 'Please fill in every field.' }, 400);
  if (!EMAIL_RE.test(f.workEmail)) return json({ error: 'Please enter a valid work email.' }, 400);
  if ((f.problem.match(/https?:\/\//g) || []).length > 2) return json({ error: 'Please remove the links and describe the problem in words.' }, 400);
  const db = await dbPromise;
  if (!db) return json({ error: 'Saving requests needs you to be signed in to claude.ai in this preview.' }, 503);
  try {
    await db.collection('leads').add({ ...f, createdAt: nowIso(), source: 'preview' });
    return json({ ok: true }, 201);
  } catch (e) {
    console.error(e);
    if (e?.code === 'invalid_argument') return json({ error: 'In this preview only the owner and editors can save requests. The deployed app accepts them from anyone.' }, 403);
    return json({ error: 'The request could not be saved. Please try again.' }, 502);
  }
}

// ---------- router: intercept the app's /api calls ----------
const realFetch = window.fetch.bind(window);
window.fetch = async (input, opts = {}) => {
  const url = new URL(typeof input === 'string' ? input : input.url, location.href);
  if (url.origin !== location.origin || !url.pathname.startsWith('/api/')) return realFetch(input, opts);
  const method = (opts.method || 'GET').toUpperCase();
  const p = url.pathname;
  const body = typeof opts.body === 'string' ? JSON.parse(opts.body || '{}') : opts.body;
  try {
    if (p === '/api/health') return json({ ok: true, ai: Boolean(await samplePromise), preview: true });
    if (p === '/api/districts' && method === 'POST') return await startDistrict(body);
    if (p === '/api/districts/upload-only' && method === 'POST') {
      const name = String(body?.name || '').trim().slice(0, 120);
      if (!name) return json({ error: 'Please enter the district name.' }, 400);
      const d = { id: uuid(), name, website: null, status: 'ready', message: 'Waiting for uploaded documents.', categories: [], sources: [], chunks: [], updatedAt: nowIso() };
      districts.set(d.id, d);
      return json({ district: view(d) }, 201);
    }
    if (p === '/api/leads' && method === 'POST') return await saveLead(body);
    const m = p.match(/^\/api\/districts\/([^/]+)(\/documents|\/ask)?$/);
    if (m) {
      const d = districts.get(decodeURIComponent(m[1]));
      if (!d) return json({ error: 'District not found. Saved districts and uploads last until the page is reloaded.' }, 404);
      if (!m[2] && method === 'GET') return json({ district: view(d) });
      if (m[2] === '/documents' && method === 'POST') {
        const files = body instanceof FormData ? body.getAll('files').filter((f) => f && f.size !== undefined) : [];
        if (!files.length) return json({ error: 'Please choose one or more PDF files.' }, 400);
        const results = [];
        for (const f of files.slice(0, 5)) results.push(await addUploadedPdf(d, f));
        return json({ results, district: view(d) });
      }
      if (m[2] === '/ask' && method === 'POST') return await answer(d, body);
    }
    return json({ error: 'Not found.' }, 404);
  } catch (e) {
    console.error(e);
    return json({ error: 'Something went wrong in the preview.' }, 500);
  }
};

// ---------- preview-only interface extras ----------
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

document.addEventListener('click', (e) => {
  const t = e.target.closest('[data-try]');
  if (t) {
    $('#district-url').value = t.dataset.try;
    $('#url-form').requestSubmit();
  }
});

// Fictional districts have no real website: open the saved source text instead.
document.addEventListener(
  'click',
  (e) => {
    const a = e.target.closest('a[href]');
    if (!a) return;
    let u;
    try {
      u = new URL(a.href);
    } catch {
      return;
    }
    if (!u.hostname.endsWith('.example') && !u.hostname.endsWith('drive.google.com')) return;
    e.preventDefault();
    e.stopPropagation();
    showSource(u);
  },
  true,
);

function showSource(u) {
  const page = Number((u.hash.match(/page=(\d+)/) || [])[1] || 0) || null;
  const base = `${u.origin}${u.pathname}`;
  let src = null;
  let d = null;
  for (const x of districts.values()) {
    src = x.sources.find((s) => s.url && s.url.split('#')[0] === base);
    if (src) {
      d = x;
      break;
    }
  }
  $('#src-title').textContent = src ? src.title : 'Not available';
  if (!src || !['ok', 'partial'].includes(src.status)) {
    $('#src-meta').textContent = src ? `Not read: ${src.reason || ''}` : '';
    $('#src-body').textContent = 'This is a fictional test district, so there is no live page to open. The crawler did not read this address.';
  } else {
    const chunks = d.chunks.filter((c) => c.source_id === src.id && (!page || c.page === page));
    $('#src-meta').textContent = `Saved text the crawler read from ${src.url}${page ? `, page ${page}` : ''}. Fictional test district.`;
    const byPage = new Map();
    for (const c of chunks) {
      const k = c.page || 0;
      if (!byPage.has(k)) byPage.set(k, []);
      byPage.get(k).push(c.body);
    }
    $('#src-body').innerHTML = [...byPage.entries()]
      .map(([pg, bodies]) => `${pg ? `<h4>Page ${pg}</h4>` : ''}${esc(bodies.join('\n\n'))}`)
      .join('');
  }
  $('#src-modal').hidden = false;
  $('#src-close').focus();
}
$('#src-close').addEventListener('click', () => ($('#src-modal').hidden = true));
$('#src-modal').addEventListener('click', (e) => {
  if (e.target.id === 'src-modal') $('#src-modal').hidden = true;
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') $('#src-modal').hidden = true;
});

let leadsCsv = '';
$('#load-leads').addEventListener('click', async () => {
  const status = $('#leads-status');
  status.textContent = 'Loading...';
  const db = await dbPromise;
  if (!db) {
    status.textContent = 'The saved-requests store is not available in this view. Open the preview on claude.ai while signed in.';
    return;
  }
  const timer = setTimeout(() => (status.textContent = 'Still loading. The store may be unreachable right now.'), 10000);
  try {
    const snap = await db.collection('leads').orderBy('createdAt', 'desc').limit(200).get();
    clearTimeout(timer);
    const rows = snap.docs.map((x) => x.data());
    status.textContent = rows.length ? `${rows.length} saved request${rows.length === 1 ? '' : 's'}.` : 'No requests saved yet.';
    const cols = [
      ['createdAt', 'Received (UTC)'],
      ['fullName', 'Name'],
      ['workEmail', 'Work email'],
      ['jobTitle', 'Job title'],
      ['district', 'School district'],
      ['problem', 'Problem to solve'],
      ['demoDistrict', 'Demo district'],
    ];
    $('#leads-table').innerHTML = rows.length
      ? `<table><thead><tr>${cols.map((c) => `<th>${c[1]}</th>`).join('')}</tr></thead><tbody>${rows
          .map((r) => `<tr>${cols.map(([k]) => `<td>${esc(k === 'createdAt' ? String(r[k] || '').replace('T', ' ').slice(0, 16) : r[k])}</td>`).join('')}</tr>`)
          .join('')}</tbody></table>`
      : '';
    const cell = (v) => {
      let s = String(v ?? '');
      if (/^[=+\-@]/.test(s)) s = `'${s}`;
      return `"${s.replace(/"/g, '""')}"`;
    };
    leadsCsv = [cols.map((c) => cell(c[1])).join(','), ...rows.map((r) => cols.map(([k]) => cell(r[k])).join(','))].join('\r\n');
    $('#copy-leads').hidden = !rows.length;
  } catch (e) {
    clearTimeout(timer);
    console.error(e);
    status.textContent = 'Only the owner and editors of this preview can see saved requests.';
  }
});
$('#copy-leads').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(leadsCsv);
    $('#leads-status').textContent = 'Copied. Paste into a spreadsheet.';
  } catch {
    $('#leads-status').textContent = 'Copy was blocked by the browser.';
  }
});
