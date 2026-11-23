// Runs the REAL crawler against the two fictional fixture districts and saves
// its output (sources, status reasons, indexed passages, categories) as JSON
// for the browser preview, which cannot reach websites itself.
// Run: python3 test/make_fixtures.py && node test/export-preview-data.js
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';

const here = path.dirname(fileURLToPath(import.meta.url));
const FIX = path.join(here, 'fixtures');
const OUT = path.join(here, '..', 'preview', 'data', 'saved-districts.json');
const SITES = [
  { dir: 'riverbend', port: 4599, publicOrigin: 'https://www.riverbend-usd.example' },
  { dir: 'lakeside', port: 4598, publicOrigin: 'https://www.lakeside-sd.example' },
];

const servers = SITES.map(({ dir, port }) =>
  http
    .createServer((req, res) => {
      const origin = `http://127.0.0.1:${port}`;
      const p = decodeURIComponent(new URL(req.url, origin).pathname);
      let file = path.join(FIX, dir, p);
      if (p.endsWith('/')) file = path.join(file, 'index.html');
      if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
        res.writeHead(404, { 'content-type': 'text/html' });
        return res.end('<h1>Not found</h1>');
      }
      const ext = path.extname(file);
      let body = fs.readFileSync(file);
      if (ext === '.xml') body = Buffer.from(body.toString().replaceAll('__ORIGIN__', origin));
      res.writeHead(200, { 'content-type': { '.html': 'text/html', '.pdf': 'application/pdf', '.xml': 'application/xml', '.txt': 'text/plain' }[ext] });
      res.end(body);
    })
    .listen(port, '127.0.0.1'),
);

const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'export-'));
const app = spawn(process.execPath, ['--disable-warning=ExperimentalWarning', 'src/server.js'], {
  cwd: path.join(here, '..'),
  env: { ...process.env, PORT: '4750', DATA_DIR: dataDir, ALLOW_PRIVATE_HOSTS: 'true', CRAWL_DELAY_MS: '0' },
  stdio: 'ignore',
});
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
for (let i = 0; i < 50; i++) {
  try {
    if ((await fetch('http://127.0.0.1:4750/api/health')).ok) break;
  } catch {}
  await sleep(200);
}

const out = { generatedAt: new Date().toISOString(), note: 'Output of the real crawler run on fictional test districts.', districts: [] };
for (const s of SITES) {
  const r = await fetch('http://127.0.0.1:4750/api/districts', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ url: `http://127.0.0.1:${s.port}/` }),
  }).then((x) => x.json());
  let d;
  for (let i = 0; i < 200; i++) {
    d = (await fetch(`http://127.0.0.1:4750/api/districts/${r.district.id}`).then((x) => x.json())).district;
    if (['ready', 'failed'].includes(d.status)) break;
    await sleep(250);
  }
  const db = new DatabaseSync(path.join(dataDir, 'app.db'));
  const fix = (u) => (u ? u.replace(`http://127.0.0.1:${s.port}`, s.publicOrigin) : u);
  const row = db.prepare('SELECT * FROM districts WHERE id = ?').get(d.id);
  const sources = db.prepare('SELECT id, url, title, kind, status, reason, pages, chars FROM sources WHERE district_id = ? ORDER BY id').all(d.id);
  const chunks = db.prepare('SELECT body, heading, title, source_id, page FROM chunks WHERE district_id = ?').all(d.id);
  out.districts.push({
    host: new URL(s.publicOrigin).hostname.replace(/^www\./, ''),
    name: row.name,
    website: fix(row.website),
    message: row.message,
    categories: JSON.parse(row.categories || '[]'),
    sources: sources.map((x) => ({ ...x, url: fix(x.url) })),
    chunks: chunks.map((c) => ({ ...c, page: c.page ?? null })),
  });
  db.close();
}
app.kill();
servers.forEach((x) => x.close());
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(out));
console.log('wrote', OUT, out.districts.map((d) => `${d.name}: ${d.sources.length} sources, ${d.chunks.length} passages`).join('; '));
