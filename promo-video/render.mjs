// Renders promo-video/index.html to an MP4, frame by frame, so the result is
// deterministic and independent of machine speed.
//
//   node promo-video/render.mjs --jobs 4             # full render -> promo-video/tomoclub-promo.mp4
//   node promo-video/render.mjs --stills 1.2,8.6     # review frames -> promo-video/.stills/*.png
//   node promo-video/render.mjs --cues               # write sound cue list -> promo-video/cues.json
//
// Options: --fps 30  --crf 22  --out path.mp4  --audio promo-video/soundtrack.m4a  --from 0 --to 46
// Needs Playwright (with Chromium) and an ffmpeg that has libx264 (FFMPEG env var or on PATH).

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf('--' + name); return i < 0 ? dflt : (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true); };

const FPS = +opt('fps', 30);
const OUT = path.resolve(opt('out', path.join(HERE, 'tomoclub-promo.mp4')));
const AUDIO = opt('silent', false) ? '' : opt('audio', path.join(HERE, 'soundtrack.m4a'));
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const JOBS = +opt('jobs', 1);
const CRF = String(opt('crf', 22));

const run = (cmd, argv) => new Promise((res, rej) => {
  spawn(cmd, argv, { stdio: 'inherit' }).on('close', c => c === 0 ? res() : rej(new Error(`${cmd} exited ${c}`)));
});

// --jobs N: render N time-slices in parallel processes, then stitch them and add the soundtrack
if (JOBS > 1) {
  const total = +opt('to', 46), frames = Math.round(total * FPS), per = Math.ceil(frames / JOBS);
  const tmp = fs.mkdtempSync(path.join(HERE, '.segs-'));
  const segs = [];
  const kids = [];
  for (let j = 0; j < JOBS; j++) {
    const a = j * per, b = Math.min(frames, (j + 1) * per);
    if (a >= b) break;
    const seg = path.join(tmp, `seg${j}.mp4`); segs.push(seg);
    kids.push(run(process.execPath, [fileURLToPath(import.meta.url), '--from', String(a / FPS), '--to', String(b / FPS), '--fps', String(FPS), '--crf', CRF, '--silent', '--out', seg]));
  }
  await Promise.all(kids);
  const list = path.join(tmp, 'list.txt');
  fs.writeFileSync(list, segs.map(s => `file '${s}'`).join('\n'));
  const hasAudio = AUDIO && fs.existsSync(AUDIO);
  await run(FFMPEG, ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list,
    ...(hasAudio ? ['-i', AUDIO] : []), '-c:v', 'copy', ...(hasAudio ? ['-c:a', 'copy', '-shortest'] : []), '-movflags', '+faststart', OUT]);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`\nwrote ${OUT}`);
  process.exit(0);
}

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.m4a': 'audio/mp4', '.svg': 'image/svg+xml' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/promo-video/index.html?render=1`;

const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--font-render-hinting=none', '--hide-scrollbars'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(url);
await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
const DURATION = await page.evaluate(() => window.__duration);

const shot = () => page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1920, height: 1080 } });

if (opt('cues', false)) {
  const cues = await page.evaluate(() => window.__cues);
  fs.writeFileSync(path.join(HERE, 'cues.json'), JSON.stringify({ duration: DURATION, cues }, null, 1));
  console.log(`wrote ${cues.length} cues`);
} else if (opt('stills', false)) {
  const dir = path.join(HERE, '.stills'); fs.mkdirSync(dir, { recursive: true });
  for (const t of String(opt('stills')).split(',').map(Number)) {
    await page.evaluate(t => window.__seek(t), t);
    fs.writeFileSync(path.join(dir, `t${t.toFixed(2).padStart(6, '0')}.png`), await shot());
  }
  console.log('stills in', dir);
} else {
  const from = +opt('from', 0), to = +opt('to', DURATION);
  const n = Math.round((to - from) * FPS);
  const hasAudio = fs.existsSync(AUDIO);
  const ff = spawn(FFMPEG, [
    '-y', '-hide_banner', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    ...(hasAudio ? ['-ss', String(from), '-i', AUDIO] : []),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', CRF, '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
    ...(hasAudio ? ['-c:a', 'aac', '-b:a', '192k', '-shortest'] : []),
    '-movflags', '+faststart', OUT,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.__seek(t), from + i / FPS);
    const buf = await shot();
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % FPS === 0) process.stdout.write(`\rframe ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg exited ' + c))));
  console.log(`\nwrote ${OUT}${hasAudio ? '' : AUDIO ? ' (no soundtrack found, silent)' : ' (video only)'}`);
}

await browser.close();
server.close();
