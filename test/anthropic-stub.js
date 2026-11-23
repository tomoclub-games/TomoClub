// TEST ONLY. A local stand-in for the Anthropic Messages API so the full
// pipeline (search, prompt, citation mapping, refusal path) can be tested
// without an API key. It answers by picking the source sentence that best
// overlaps the question, and says "not found" when nothing overlaps enough.
// It is never used by the real app: production calls api.anthropic.com.
import http from 'node:http';

const STOP = new Set('a an and are as at be by can do does for from has have how i if in is it its me my of on or our should the their this to was we what when where which who why will with you your about school district child student students'.split(' '));
const words = (s) => (s.toLowerCase().match(/[a-z0-9]+/g) || []).filter((w) => w.length > 2 && !STOP.has(w));
const stem = (w) => w.replace(/(ing|ed|es|s)$/, '');

export const calls = [];

export function startStub(port) {
  const server = http.createServer((req, res) => {
    let body = '';
    req.on('data', (c) => (body += c));
    req.on('end', () => {
      const payload = JSON.parse(body || '{}');
      calls.push({ model: payload.model, system: payload.system, key: req.headers['x-api-key'] });
      const user = payload.messages?.[0]?.content || '';
      let text;
      if (/search keywords/i.test(payload.system || '')) {
        const q = user.split('Question:').pop();
        text = JSON.stringify({ terms: words(q) });
      } else {
        const question = user.split('QUESTION:').pop();
        const qStems = new Set(words(question).map(stem));
        const sourcesOnly = user.split('QUESTION:')[0];
        const blocks = sourcesOnly.split(/\n(?=\[S\d+\] )/).filter((b) => /^\[S\d+\]/.test(b));
        let best = { score: 0 };
        for (const b of blocks) {
          const id = b.match(/^\[S(\d+)\]/)[1];
          const content = b.split('\n').slice(2).join(' ');
          for (const sentence of content.split(/(?<=[.!?])\s+/)) {
            const score = new Set(words(sentence).map(stem).filter((w) => qStems.has(w))).size;
            if (score > best.score) best = { score, id, sentence: sentence.trim() };
          }
        }
        text = best.score >= 2
          ? JSON.stringify({ found: true, answer: `${best.sentence} [S${best.id}]` })
          : JSON.stringify({ found: false, answer: '' });
      }
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ content: [{ type: 'text', text }] }));
    });
  });
  return new Promise((r) => server.listen(port, '127.0.0.1', () => r(server)));
}
