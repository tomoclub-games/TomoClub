// Renders video.html frame by frame into an H.264 MP4 (silent, 30fps).
// Usage (from this folder): NODE_PATH=$(npm root -g) FFMPEG=/path/to/ffmpeg node video.cjs [out.mp4] [fps]
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const out = path.resolve(__dirname, '..', process.argv[2] || 'video/amity-ai-literacy-reel.mp4');
const fps = +(process.argv[3] || 30);
const ffmpegBin = process.env.FFMPEG || 'ffmpeg';

(async () => {
  require('fs').mkdirSync(path.dirname(out), { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'video.html'));
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);
  const frames = Math.round(duration * fps);

  const ff = spawn(ffmpegBin, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });

  const stage = await page.$('#stage');
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.render(t), i / fps);
    const buf = await stage.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (fps * 5) === 0) console.log(`frame ${i}/${frames}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('wrote', out);
})();
