// Answers questions for ONE district using only that district's indexed text.
import { config } from './config.js';
import { db } from './db.js';
import { callClaude } from './llm.js';
import {
  NOT_FOUND,
  localTerms,
  cleanTerms,
  expansionPrompt,
  diversify,
  answerPrompt,
  parseJsonObject,
  finishAnswer,
  suggestedQuestions,
} from './shared/answering.js';

export { NOT_FOUND, suggestedQuestions };

async function expandTerms(question, history) {
  const p = expansionPrompt(question, history);
  try {
    const text = await callClaude({ model: config.searchModel, maxTokens: 150, system: p.system, messages: [{ role: 'user', content: p.user }] });
    const obj = parseJsonObject(text);
    if (obj && Array.isArray(obj.terms)) return obj.terms.map(String).filter(Boolean).slice(0, 10);
  } catch {
    /* fall back to local terms */
  }
  return [];
}

const searchStmt = db.prepare(`
  SELECT chunks.rowid AS rid, chunks.body, chunks.heading, chunks.title, chunks.source_id, chunks.page,
         s.url, s.kind, bm25(chunks, 1.0, 1.6, 1.6, 0, 0, 0) AS score
  FROM chunks JOIN sources s ON s.id = chunks.source_id
  WHERE chunks MATCH ? AND chunks.district_id = ?
  ORDER BY score LIMIT 60`);

export function search(districtId, terms, opts) {
  const cleaned = cleanTerms(terms);
  if (!cleaned.length) return [];
  const q = cleaned.map((t) => `"${t.replace(/"/g, '')}"`).join(' OR ');
  try {
    return diversify(searchStmt.all(q, districtId), opts);
  } catch (e) {
    console.error('search error', e.message, q);
    return [];
  }
}

export async function answerQuestion(district, question, history = []) {
  const q = String(question || '').trim().slice(0, 500);
  if (!q) return { found: false, answer: NOT_FOUND, citations: [] };
  const terms = [...localTerms(q), ...(await expandTerms(q, history))];
  const hits = search(district.id, terms);
  if (!hits.length) return { found: false, answer: NOT_FOUND, citations: [] };
  const p = answerPrompt(district.name, hits, q, history);
  const text = await callClaude({ model: config.answerModel, maxTokens: 700, system: p.system, messages: [{ role: 'user', content: p.user }] });
  return finishAnswer(text, hits);
}
