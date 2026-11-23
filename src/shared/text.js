// Pure text helpers shared by the server and the in-browser preview.

export const H = '\u0001H\u0001'; // heading marker inside extracted text

export const clean = (s) =>
  s
    .replace(/ /g, ' ')
    .replace(/[ \t\f\v]+/g, ' ')
    .replace(/ *\n */g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

/** Split text into ~1,100 character chunks that keep their nearest heading. */
export function chunkText(text, { maxChars = 1100, overlap = 150 } = {}) {
  const chunks = [];
  let heading = '';
  let buf = '';
  let bufHeading = '';
  let fresh = false; // new text since the last flush
  const flush = () => {
    const body = buf.trim();
    if (fresh && body.replace(/\s/g, '').length >= 40) chunks.push({ heading: bufHeading, body });
    buf = body.length > overlap ? body.slice(-overlap) : '';
    bufHeading = heading;
    fresh = false;
  };
  const paras = text.split(/\n+/);
  for (const p of paras) {
    if (p.startsWith(H)) {
      if (buf.trim().length > 200) flush();
      heading = p.replace(H, '').trim().slice(0, 200);
      if (!buf.trim()) bufHeading = heading;
      buf += `\n${heading}\n`;
      fresh = true;
      continue;
    }
    if (buf.length + p.length > maxChars && buf.trim()) flush();
    fresh = true;
    if (p.length > maxChars) {
      // very long paragraph (common in PDFs): split on sentence boundaries
      const sentences = p.match(/[^.!?]+[.!?]+["')\]]*\s*|[^.!?]+$/g) || [p];
      for (const s of sentences) {
        if (buf.length + s.length > maxChars && buf.trim()) flush();
        buf += s.length > maxChars ? s.slice(0, maxChars) : s;
        fresh = true;
      }
      buf += '\n';
    } else {
      buf += p + '\n';
    }
  }
  if (fresh && buf.trim()) {
    const body = buf.trim();
    if (body.replace(/\s/g, '').length >= 40) chunks.push({ heading: bufHeading, body });
  }
  return chunks;
}

export const stripHeadingMarkers = (s) => s.replaceAll(H, '');
