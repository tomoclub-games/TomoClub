// Calls to Claude through the Anthropic Messages API. The key stays on the server.
import { config } from './config.js';

export class AiError extends Error {
  constructor(message, code) {
    super(message);
    this.code = code;
  }
}

export async function callClaude({ model, system, messages, maxTokens = 700, temperature = 0 }) {
  if (!config.anthropicApiKey) {
    throw new AiError('The AI service is not configured yet (missing ANTHROPIC_API_KEY).', 'not_configured');
  }
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 45000);
  let res;
  try {
    res = await fetch(`${config.anthropicApiUrl}/v1/messages`, {
      method: 'POST',
      signal: ctrl.signal,
      headers: {
        'content-type': 'application/json',
        'x-api-key': config.anthropicApiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({ model, system, messages, max_tokens: maxTokens, temperature }),
    });
  } catch (e) {
    throw new AiError('The AI service could not be reached. Please try again in a minute.', 'unavailable');
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    console.error('Anthropic API error', res.status, detail.slice(0, 500));
    if (res.status === 401 || res.status === 403) throw new AiError('The AI service key was rejected. Check ANTHROPIC_API_KEY.', 'auth');
    if (res.status === 404) throw new AiError(`The AI model "${model}" was not found. Check ANTHROPIC_MODEL.`, 'model');
    if (res.status === 429) throw new AiError('The AI service is busy right now. Please try again in a minute.', 'rate_limited');
    throw new AiError('The AI service is unavailable right now. Please try again in a minute.', 'unavailable');
  }
  const data = await res.json();
  return (data.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('').trim();
}

/** Pull the first JSON object out of a model reply. */
export function parseJsonObject(text) {
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end <= start) return null;
  try {
    return JSON.parse(text.slice(start, end + 1));
  } catch {
    return null;
  }
}
