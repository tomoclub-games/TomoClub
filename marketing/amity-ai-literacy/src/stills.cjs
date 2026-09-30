// Quick preview: grabs single frames of video.html at the given times.
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const outDir = process.argv[2]; const times = process.argv.slice(3).map(Number);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'video.html'));
  await page.evaluate(() => document.fonts.ready);
  for (const t of times) { await page.evaluate(t => window.render(t), t); await (await page.$('#stage')).screenshot({ path: path.join(outDir, `f${t}.png`) }); }
  await browser.close();
})();
