// Turns HTML pages and PDFs into plain text with headings and page numbers,
// then into small chunks for the search index.
import * as cheerio from 'cheerio';
import * as unpdf from 'unpdf';
import { parsePdfWith } from './shared/pdf.js';
import { H, clean } from './shared/text.js';
export { chunkText, stripHeadingMarkers } from './shared/text.js';


/** Extract links, title and readable text from an HTML page. */
export function parseHtml(html, pageUrl) {
  const $ = cheerio.load(html);

  const links = [];
  $('a[href]').each((_, el) => {
    const href = ($(el).attr('href') || '').trim();
    if (!href || href.startsWith('#') || /^(mailto|tel|javascript|sms):/i.test(href)) return;
    try {
      const abs = new URL(href, pageUrl);
      abs.hash = '';
      links.push({ url: abs.toString(), text: clean($(el).text() || $(el).attr('title') || $(el).attr('aria-label') || '').slice(0, 200) });
    } catch {
      /* ignore bad links */
    }
  });
  // Some sites list documents in iframes or embeds
  $('iframe[src], embed[src], object[data]').each((_, el) => {
    const src = $(el).attr('src') || $(el).attr('data');
    try {
      links.push({ url: new URL(src, pageUrl).toString(), text: $(el).attr('title') || '' });
    } catch {
      /* ignore */
    }
  });

  const siteName =
    $('meta[property="og:site_name"]').attr('content') ||
    $('meta[name="application-name"]').attr('content') ||
    '';
  const rawTitle = clean($('title').first().text() || $('meta[property="og:title"]').attr('content') || '');
  const scriptCount = $('script').length;

  $('script, style, noscript, svg, template, iframe, form, nav, header, footer, aside, [role="navigation"], [role="banner"], [role="contentinfo"], [aria-hidden="true"], .visually-hidden, .sr-only, .skip-link').remove();

  let root = $('main, [role="main"], #main, #main-content, #content, article').first();
  if (!root.length || clean(root.text()).length < 200) root = $('body');

  root.find('br').replaceWith('\n');
  root.find('h1,h2,h3,h4').each((_, el) => {
    const t = clean($(el).text());
    $(el).replaceWith(t ? `\n${H}${t}\n` : '\n');
  });
  root.find('p,div,li,tr,section,article,dd,dt,table,ul,ol,blockquote,pre').each((_, el) => {
    $(el).append('\n');
  });
  root.find('td,th').each((_, el) => {
    $(el).append(' | ');
  });
  const text = clean(root.text());
  const h1 = (text.split('\n').find((l) => l.startsWith(H)) || '').replace(H, '');

  const readable = text.replaceAll(H, '').replace(/\s+/g, ' ').trim();
  const looksDynamic =
    readable.length < 300 &&
    (scriptCount >= 5 || /id=["'](root|app|__next|__nuxt)["']/i.test(html));

  return { title: rawTitle || h1, siteName, text, links, looksDynamic };
}

/** Best-effort district name from the home page. */
export function guessDistrictName({ siteName, title }, host) {
  const candidates = [siteName, ...(title || '').split(/\s[|\-–—:·]\s/)].map((s) => (s || '').trim()).filter(Boolean);
  const pick =
    candidates.find((c) => /(school|district|isd|usd|schools|public|academy|charter|unified|county)/i.test(c)) ||
    candidates.sort((a, b) => b.length - a.length)[0];
  if (pick && !/^home(page)?$/i.test(pick)) return pick.slice(0, 120);
  return host;
}

/** Per-page text from a PDF buffer. */
export const parsePdf = (buffer) => parsePdfWith(unpdf, buffer);

