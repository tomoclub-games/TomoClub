// Usage:
//   node render.js stills 0.2 2.6 ...   -> stills/t_<sec>.png
//   node render.js video [fps]          -> frames piped to ffmpeg (video_noaudio.mp4) + events.json
const http = require('http'), fs = require('fs'), path = require('path');
const { spawn } = require('child_process');
const { chromium } = (() => {
  try { return require('playwright'); } catch { return require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright'); }
})();
const ROOT = __dirname;
const FFMPEG = process.env.FFMPEG;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.css': 'text/css' };

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
    res.end(data);
  });
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const port = server.address().port;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => { console.error('[pageerror]', e.message); process.exitCode = 1; });
  await page.goto(`http://localhost:${port}/index.html`);
  await page.waitForFunction('window.READY === true', null, { timeout: 30000 });
  const dur = await page.evaluate('window.DURATION');
  fs.writeFileSync(path.join(ROOT, 'events.json'), JSON.stringify(await page.evaluate('window.EVENTS'), null, 1));
  const [mode, ...args] = process.argv.slice(2);
  const stage = await page.$('#stage');

  if (mode === 'stills') {
    fs.mkdirSync(path.join(ROOT, 'stills'), { recursive: true });
    // play forward from 0 so every tween initialises in order, like the real render
    const times = args.map(Number).sort((a, b) => a - b);
    let ti = 0;
    for (let f = 0; ti < times.length; f++) {
      const t = f / 60;
      if (t >= times[ti] - 1e-6) {
        await page.evaluate(x => window.seek(x), times[ti]);
        await stage.screenshot({ path: path.join(ROOT, 'stills', `t_${times[ti].toFixed(2)}.png`) });
        ti++;
      } else await page.evaluate(x => window.seek(x), t);
    }
  } else {
    const fps = Number(args[0] || 60);
    const n = Math.round(dur * fps);
    const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', path.join(ROOT, 'video_noaudio.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      await page.evaluate(x => window.seek(x), i / fps);
      const buf = await page.screenshot({ type: 'jpeg', quality: 96 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 120 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('done', n, 'frames in', ((Date.now() - t0) / 1000).toFixed(0), 's');
  }
  await browser.close();
  server.close();
})();
