// PDF text per page, shared by the server and the in-browser preview.
// `unpdf` is passed in so each side loads its own build of the library.
import { clean } from './text.js';

export async function parsePdfWith(unpdf, buffer) {
  const { extractText, getDocumentProxy, getMeta } = unpdf;
  const pdf = await getDocumentProxy(new Uint8Array(buffer));
  const { totalPages, text } = await extractText(pdf, { mergePages: false });
  let title = '';
  try {
    const meta = await getMeta(pdf);
    title = (meta?.info?.Title || '').toString().trim();
  } catch {
    /* no metadata */
  }
  const pages = (Array.isArray(text) ? text : [text]).map((t) => clean(String(t || '')));
  const withText = pages.filter((p) => p.replace(/\s/g, '').length >= 40).length;
  return { title, totalPages, pages, pagesWithText: withText };
}
