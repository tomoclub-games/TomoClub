// Renders every element with a data-out attribute to PNG, and the carousel to a PDF.
// Usage (from this folder): NODE_PATH=$(npm root -g) node render.cjs [carousel|images|all]
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

const OUT = path.resolve(__dirname, '..');
const which = process.argv[2] || 'all';

async function shoot(page, file) {
  await page.goto('file://' + path.join(__dirname, file));
  await page.evaluate(() => document.fonts.ready);
  const els = await page.$$('[data-out]');
  for (const el of els) {
    const name = await el.getAttribute('data-out');
    const dest = path.join(OUT, name + '.png');
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    await el.screenshot({ path: dest });
    console.log('wrote', path.relative(OUT, dest));
  }
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1700, height: 1400 }, deviceScaleFactor: 1 });
  if (which === 'carousel' || which === 'all') {
    await shoot(page, 'carousel.html');
    await page.emulateMedia({ media: 'print' });
    await page.pdf({ path: path.join(OUT, 'carousel', 'amity-ai-literacy-carousel.pdf'), width: '1080px', height: '1350px', printBackground: true });
    await page.emulateMedia({ media: 'screen' });
    console.log('wrote carousel/amity-ai-literacy-carousel.pdf');
  }
  if (which === 'images' || which === 'all') await shoot(page, 'images.html');
  await browser.close();
})();
