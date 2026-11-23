// Reads a district website: robots.txt, sitemaps, then the most relevant
// public pages and PDFs, within fixed limits. Records what worked and what did not.
import crypto from 'node:crypto';
import robotsParser from 'robots-parser';
import { config } from './config.js';
import { db, now, deleteDistrictContent } from './db.js';
import { safeGet, FetchError } from './safeFetch.js';
import { parseHtml, parsePdf, chunkText, guessDistrictName, stripHeadingMarkers } from './extract.js';
import { linkScore, detectCategories, decodeURIComponentSafe } from './categories.js';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const running = new Map(); // districtId -> promise
const MAX_CONCURRENT = 2;

const isPdfUrl = (u) => /\.pdf($|[?#])/i.test(u);
const SKIP_EXT = /\.(jpe?g|png|gif|webp|svg|ico|mp4|mov|mp3|wav|zip|docx?|xlsx?|pptx?|csv|ics|css|js|json|xml|rss|woff2?)($|[?#])/i;
const VIEWER_HOSTS = /(^|\.)(drive\.google\.com|docs\.google\.com|sites\.google\.com|go\.boarddocs\.com|boarddocs\.com|simbli\.eboardsolutions\.com|youtube\.com|facebook\.com|instagram\.com|x\.com|twitter\.com|linkedin\.com)$/i;

export function normalizeInputUrl(input) {
  let s = String(input || '').trim();
  if (!s) throw new FetchError('Please enter a district website address.', 'invalid_url');
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(s) && !/^https?:\/\//i.test(s)) {
    throw new FetchError('Only http and https addresses can be read.', 'invalid_url');
  }
  if (!/^https?:\/\//i.test(s)) s = `https://${s}`;
  const u = new URL(s);
  u.hash = '';
  return u;
}

const baseHost = (host) => host.toLowerCase().replace(/^www\./, '');
const onSite = (u, base) => {
  const h = baseHost(u.hostname);
  return h === base || h.endsWith(`.${base}`);
};

function canonical(u) {
  const x = new URL(u);
  x.hash = '';
  // drop common tracking parameters
  for (const p of [...x.searchParams.keys()]) if (/^(utm_|fbclid|gclid)/i.test(p)) x.searchParams.delete(p);
  return x.toString();
}

function update(districtId, fields) {
  const keys = Object.keys(fields);
  db.prepare(`UPDATE districts SET ${keys.map((k) => `${k} = ?`).join(', ')}, updated_at = ? WHERE id = ?`).run(
    ...keys.map((k) => fields[k]),
    now(),
    districtId,
  );
}

const insertSource = db.prepare(
  'INSERT INTO sources (district_id, url, title, kind, status, reason, pages, chars, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
);
const insertChunk = db.prepare(
  'INSERT INTO chunks (body, heading, title, district_id, source_id, page) VALUES (?, ?, ?, ?, ?, ?)',
);

export function recordSource(districtId, { url = null, title = '', kind, status, reason = null, pages = null, chars = 0 }) {
  const r = insertSource.run(districtId, url, title.slice(0, 300), kind, status, reason, pages, chars, now());
  return Number(r.lastInsertRowid);
}

/** Store extracted text. `parts` = [{ page|null, text }]. Returns chunk count. */
export function indexDocument(districtId, sourceId, title, parts) {
  let n = 0;
  db.exec('BEGIN');
  try {
    for (const part of parts) {
      for (const c of chunkText(part.text)) {
        insertChunk.run(stripHeadingMarkers(c.body), c.heading || '', title, districtId, sourceId, part.page ?? null);
        n++;
      }
    }
    db.exec('COMMIT');
  } catch (e) {
    db.exec('ROLLBACK');
    throw e;
  }
  return n;
}

export function refreshCategories(districtId) {
  const docs = db
    .prepare(
      `SELECT s.title, s.url, group_concat(c.body, ' ') AS text
       FROM sources s LEFT JOIN chunks c ON c.source_id = s.id AND c.district_id = s.district_id
       WHERE s.district_id = ? AND s.status IN ('ok','partial') GROUP BY s.id`,
    )
    .all(districtId);
  update(districtId, { categories: JSON.stringify(detectCategories(docs)) });
}

/** Remove the district name from page titles ("Attendance | Riverbend USD" -> "Attendance"). */
function makeTitleCleaner(name) {
  const n = (name || '').toLowerCase().trim();
  return (title) => {
    const t = String(title || '').trim();
    if (!n || !t) return t;
    const parts = t.split(/\s+[|\-\u2013\u2014:\u00b7]\s+/).map((x) => x.trim()).filter(Boolean);
    const kept = parts.filter((x) => x.toLowerCase() !== n && !/^home(page)?$/i.test(x));
    return kept.length ? kept.join(' - ') : '';
  };
}

function pdfTitleFrom(url, linkText, metaTitle) {
  const file = decodeURIComponentSafe(new URL(url).pathname.split('/').pop() || '')
    .replace(/\.pdf$/i, '')
    .replace(/[-_+]+/g, ' ')
    .trim();
  const good = (s) => s && s.length > 3 && !/^(untitled|microsoft word|document\d*|click here|download|here|view|pdf)$/i.test(s.trim());
  if (good(linkText)) return linkText.trim().slice(0, 200);
  if (good(metaTitle)) return metaTitle.trim().slice(0, 200);
  return file || 'PDF document';
}

async function loadRobots(origin) {
  const robotsUrl = `${origin}/robots.txt`;
  try {
    const r = await safeGet(robotsUrl, { maxBytes: 512 * 1024, accept: 'text/plain' });
    return robotsParser(robotsUrl, r.body.toString('utf8'));
  } catch {
    return robotsParser(robotsUrl, ''); // no robots.txt: everything allowed
  }
}

async function loadSitemapUrls(origin, robots, base) {
  const queue = [...new Set([...(robots.getSitemaps?.() || []), `${origin}/sitemap.xml`])];
  const urls = [];
  let files = 0;
  while (queue.length && files < 6 && urls.length < 3000) {
    const sm = queue.shift();
    files++;
    try {
      const r = await safeGet(sm, { maxBytes: 8 * 1024 * 1024, accept: 'application/xml,text/xml' });
      const xml = r.body.toString('utf8');
      const locs = [...xml.matchAll(/<loc>\s*([^<\s]+)\s*<\/loc>/gi)].map((m) => m[1].replace(/&amp;/g, '&'));
      if (/<sitemapindex/i.test(xml)) {
        // prefer page and document sitemaps over news/event ones
        locs.sort((a, b) => Number(/news|event|post|blog/i.test(a)) - Number(/news|event|post|blog/i.test(b)));
        queue.push(...locs.slice(0, 10));
      } else {
        for (const l of locs) {
          try {
            if (onSite(new URL(l), base)) urls.push(l);
          } catch {
            /* skip */
          }
        }
      }
    } catch {
      /* no or unreadable sitemap */
    }
  }
  return urls;
}

/** Start (or reuse) processing for a district website. Returns the district row. */
export function startDistrict(input, { refresh = false, beforeNewCrawl } = {}) {
  const u = normalizeInputUrl(input);
  const host = baseHost(u.host); // includes a port if one was given

  if (!refresh) {
    const existing = db
      .prepare(
        `SELECT * FROM districts WHERE host = ? AND status IN ('ready','processing','queued')
         AND updated_at > ? ORDER BY updated_at DESC LIMIT 1`,
      )
      .get(host, new Date(Date.now() - config.reuseDays * 86400000).toISOString());
    if (existing) return { district: existing, reused: true };
  }
  if (running.size >= MAX_CONCURRENT) {
    throw new FetchError('Two district websites are being read right now. Please try again in a few minutes.', 'busy');
  }
  beforeNewCrawl?.();

  const id = crypto.randomUUID();
  const t = now();
  db.prepare(
    'INSERT INTO districts (id, name, website, host, status, message, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
  ).run(id, host, u.toString(), host, 'queued', 'Starting', t, t);

  const job = crawl(id, u)
    .catch((e) => {
      console.error('crawl failed', id, e);
      update(id, { status: 'failed', message: e instanceof FetchError ? e.message : 'Something went wrong while reading this website.' });
    })
    .finally(() => running.delete(id));
  running.set(id, job);
  return { district: db.prepare('SELECT * FROM districts WHERE id = ?').get(id), reused: false };
}

async function crawl(districtId, startUrl) {
  const started = Date.now();
  const base = baseHost(startUrl.hostname);
  update(districtId, { status: 'processing', message: 'Reading the home page', current_url: startUrl.toString() });

  // 1. robots.txt, then the home page: it must work, or we stop with a clear message.
  const robotsBlocked = () =>
    new FetchError(
      "This district's robots.txt asks automated tools not to read its website, so it was not read. You can upload PDFs instead.",
      'robots',
    );
  let robots = await loadRobots(startUrl.origin);
  if (robots.isAllowed(startUrl.toString(), config.userAgent) === false) throw robotsBlocked();
  let home;
  try {
    home = await safeGet(startUrl.toString());
  } catch (e) {
    throw new FetchError(`Could not open ${startUrl.hostname}: ${e.message}`, e.code);
  }
  const homeUrl = new URL(home.url);
  const origin = homeUrl.origin;
  if (origin !== startUrl.origin) {
    robots = await loadRobots(origin);
    if (robots.isAllowed(homeUrl.toString(), config.userAgent) === false) throw robotsBlocked();
  }
  // Documents on other hosts (for example a document CDN) follow that host's robots.txt.
  const robotsByOrigin = new Map([[origin, robots]]);
  const allowed = async (u) => {
    const o = new URL(u).origin;
    if (!robotsByOrigin.has(o)) robotsByOrigin.set(o, await loadRobots(o));
    return robotsByOrigin.get(o).isAllowed(u, config.userAgent) !== false;
  };
  const crawlDelay = Math.min(Math.max((robots.getCrawlDelay(config.userAgent) || 0) * 1000, config.delayBetweenRequestsMs), 5000);

  const visited = new Set();
  const queued = new Map(); // url -> item
  let pages = 0;
  let pdfs = 0;
  let unreadable = 0;
  const viewerNoted = new Set();

  const enqueue = (url, text, depth, from) => {
    let u;
    try {
      u = new URL(url);
    } catch {
      return;
    }
    if (!['http:', 'https:'].includes(u.protocol)) return;
    const key = canonical(u);
    if (visited.has(key)) return;
    const pdf = isPdfUrl(key);
    if (VIEWER_HOSTS.test(u.hostname)) {
      // Documents on Google Drive, BoardDocs and similar need a browser or sign-in.
      const score = linkScore(key, text);
      if (score >= 3 && !viewerNoted.has(key) && viewerNoted.size < 15) {
        viewerNoted.add(key);
        recordSource(districtId, {
          url: key,
          title: text || u.hostname,
          kind: 'page',
          status: 'skipped',
          reason: `Hosted on ${u.hostname}, which needs a browser or sign-in to read. Upload the PDF instead if it matters.`,
        });
      }
      return;
    }
    if (!pdf && !onSite(u, base)) return; // only follow the district's own pages
    if (!pdf && SKIP_EXT.test(u.pathname)) return;
    if (depth > config.maxDepth) return;
    const score = linkScore(key, text) - depth * 0.5;
    const prev = queued.get(key);
    if (!prev || prev.score < score) queued.set(key, { url: key, text, depth, score, pdf, from });
  };

  const takeNext = () => {
    let best = null;
    for (const item of queued.values()) {
      if (item.pdf && pdfs >= config.maxPdfs) continue;
      if (!item.pdf && pages >= config.maxPages) continue;
      if (!best || item.score > best.score) best = item;
    }
    if (best) queued.delete(best.url);
    return best;
  };

  // Process the home page we already fetched.
  let cleanTitle = (t) => t;
  const processHtml = (res, item) => {
    const parsed = parseHtml(res.body.toString('utf8'), res.url);
    for (const l of parsed.links) enqueue(l.url, l.text, item.depth + 1, res.url);
    const title = (cleanTitle(parsed.title || '') || parsed.title || res.url).slice(0, 200);
    if (parsed.looksDynamic) {
      unreadable++;
      recordSource(districtId, {
        url: res.url,
        title,
        kind: 'page',
        status: 'failed',
        reason: 'This page loads its content with JavaScript, so its text could not be read without a browser.',
      });
      return parsed;
    }
    const chars = stripHeadingMarkers(parsed.text).length;
    if (chars < 80) {
      recordSource(districtId, { url: res.url, title, kind: 'page', status: 'skipped', reason: 'No readable text on this page.' });
      return parsed;
    }
    const sid = recordSource(districtId, { url: res.url, title, kind: 'page', status: 'ok', chars });
    indexDocument(districtId, sid, title, [{ page: null, text: parsed.text }]);
    pages++;
    parsed.sourceId = sid;
    return parsed;
  };

  visited.add(canonical(homeUrl));
  if (!/html/.test(home.contentType)) throw new FetchError('The address did not return a web page.', 'not_html');
  const homeParsed = processHtml(home, { depth: 0 });
  const name = guessDistrictName(homeParsed, base);
  update(districtId, { name, website: homeUrl.toString(), message: 'Looking for handbooks, calendars and policies' });
  cleanTitle = makeTitleCleaner(name);
  if (homeParsed.sourceId) {
    const t = cleanTitle(homeParsed.title || '') || 'Home page';
    db.prepare('UPDATE sources SET title = ? WHERE id = ?').run(t, homeParsed.sourceId);
    db.prepare('UPDATE chunks SET title = ? WHERE source_id = ?').run(t, homeParsed.sourceId);
  }

  // 2. Sitemap URLs that look relevant join the queue.
  const sitemapUrls = await loadSitemapUrls(origin, robots, base);
  for (const s of sitemapUrls) if (linkScore(s) >= 3) enqueue(s, '', 1, 'sitemap');

  // 3. Read the best-scoring pages and PDFs within limits.
  for (;;) {
    if (Date.now() - started > config.crawlTimeLimitMs) break;
    if (pages >= config.maxPages && pdfs >= config.maxPdfs) break;
    const item = takeNext();
    if (!item) break;
    if (item.score < 0 && pages >= 10) continue; // low-value page and we already have a base
    visited.add(item.url);

    if (!(await allowed(item.url))) {
      recordSource(districtId, {
        url: item.url,
        title: item.text || item.url,
        kind: item.pdf ? 'pdf' : 'page',
        status: 'skipped',
        reason: "The district's robots.txt asks automated tools not to read this address, so it was not read.",
      });
      continue;
    }

    update(districtId, {
      current_url: item.url,
      message: `Read ${pages} pages and ${pdfs} PDFs so far`,
    });
    await sleep(crawlDelay);

    let res;
    try {
      res = await safeGet(item.url, { maxBytes: item.pdf ? config.maxPdfBytes : config.maxHtmlBytes });
    } catch (e) {
      unreadable++;
      recordSource(districtId, {
        url: item.url,
        title: cleanTitle(item.text || '') || item.text || item.url,
        kind: item.pdf ? 'pdf' : 'page',
        status: 'failed',
        reason: e instanceof FetchError ? e.message : 'Could not be read.',
      });
      continue;
    }
    const finalUrl = canonical(res.url);
    if (finalUrl !== item.url) {
      if (visited.has(finalUrl)) continue;
      visited.add(finalUrl);
    }

    const isPdf = res.contentType.includes('pdf') || (isPdfUrl(finalUrl) && !res.contentType.includes('html'));
    if (isPdf) {
      try {
        const parsed = await parsePdf(res.body);
        const title = pdfTitleFrom(finalUrl, item.text, parsed.title);
        if (parsed.pagesWithText === 0) {
          unreadable++;
          recordSource(districtId, {
            url: finalUrl,
            title,
            kind: 'pdf',
            status: 'failed',
            pages: parsed.totalPages,
            reason: 'Scanned PDF with no text layer. Text recognition (OCR) is not turned on in this prototype.',
          });
          continue;
        }
        const partial = parsed.pagesWithText < parsed.totalPages;
        const chars = parsed.pages.reduce((a, p) => a + p.length, 0);
        const sid = recordSource(districtId, {
          url: finalUrl,
          title,
          kind: 'pdf',
          status: partial ? 'partial' : 'ok',
          pages: parsed.totalPages,
          chars,
          reason: partial ? `${parsed.totalPages - parsed.pagesWithText} of ${parsed.totalPages} pages had no readable text (likely scanned).` : null,
        });
        indexDocument(districtId, sid, title, parsed.pages.map((text, i) => ({ page: i + 1, text })));
        pdfs++;
      } catch (e) {
        unreadable++;
        recordSource(districtId, {
          url: finalUrl,
          title: pdfTitleFrom(finalUrl, item.text, ''),
          kind: 'pdf',
          status: 'failed',
          reason: 'The PDF could not be opened (damaged or password protected).',
        });
      }
    } else if (res.contentType.includes('html') || res.contentType === '') {
      if (!onSite(new URL(finalUrl), base)) continue; // redirected off-site
      processHtml(res, item);
    }
  }

  refreshCategories(districtId);
  const ok = db.prepare("SELECT COUNT(*) n FROM sources WHERE district_id = ? AND status IN ('ok','partial')").get(districtId).n;
  if (!ok) {
    update(districtId, {
      status: 'failed',
      current_url: null,
      message: 'No readable pages or documents were found. The site may block automated tools or load everything with JavaScript. Try uploading PDFs instead.',
    });
    return;
  }
  update(districtId, {
    status: 'ready',
    current_url: null,
    message: `Read ${pages} page${pages === 1 ? '' : 's'} and ${pdfs} PDF${pdfs === 1 ? '' : 's'}${unreadable ? `; ${unreadable} could not be read` : ''}.`,
  });
}

/** Create an empty district for PDF uploads only. */
export function createUploadOnlyDistrict(name) {
  const id = crypto.randomUUID();
  const t = now();
  const clean = String(name || '').trim().slice(0, 120);
  if (!clean) throw new FetchError('Please enter the district name.', 'invalid');
  db.prepare(
    'INSERT INTO districts (id, name, website, host, status, message, categories, created_at, updated_at) VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, ?)',
  ).run(id, clean, 'ready', 'Waiting for uploaded documents.', '[]', t, t);
  return db.prepare('SELECT * FROM districts WHERE id = ?').get(id);
}

/** Add an uploaded PDF to a district's index. */
export async function addUploadedPdf(districtId, fileName, buffer) {
  const parsed = await parsePdf(buffer).catch(() => null);
  const title = String(fileName || 'Uploaded PDF').replace(/\.pdf$/i, '').slice(0, 200);
  if (!parsed) {
    recordSource(districtId, { title, kind: 'upload', status: 'failed', reason: 'The PDF could not be opened (damaged or password protected).' });
    return { status: 'failed', message: `${fileName}: could not be opened.` };
  }
  if (parsed.pagesWithText === 0) {
    recordSource(districtId, {
      title,
      kind: 'upload',
      status: 'failed',
      pages: parsed.totalPages,
      reason: 'Scanned PDF with no text layer. Text recognition (OCR) is not turned on in this prototype.',
    });
    return { status: 'failed', message: `${fileName}: scanned PDF with no readable text.` };
  }
  const partial = parsed.pagesWithText < parsed.totalPages;
  const sid = recordSource(districtId, {
    title,
    kind: 'upload',
    status: partial ? 'partial' : 'ok',
    pages: parsed.totalPages,
    chars: parsed.pages.reduce((a, p) => a + p.length, 0),
    reason: partial ? `${parsed.totalPages - parsed.pagesWithText} of ${parsed.totalPages} pages had no readable text.` : null,
  });
  indexDocument(districtId, sid, title, parsed.pages.map((text, i) => ({ page: i + 1, text })));
  refreshCategories(districtId);
  db.prepare("UPDATE districts SET status = 'ready', message = ?, updated_at = ? WHERE id = ? AND status != 'processing'").run(
    'Documents ready.',
    now(),
    districtId,
  );
  return { status: partial ? 'partial' : 'ok', message: `${fileName}: ${parsed.pagesWithText} of ${parsed.totalPages} pages read.` };
}

export { deleteDistrictContent };
