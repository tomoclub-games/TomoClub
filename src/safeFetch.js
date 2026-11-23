// Fetches public URLs only. Blocks private network addresses (so a visitor
// cannot point the server at internal systems), follows redirects by hand so
// every hop is checked, and caps size and time.
import dns from 'node:dns/promises';
import net from 'node:net';
import { config } from './config.js';

export class FetchError extends Error {
  constructor(message, code) {
    super(message);
    this.code = code;
  }
}

function isPrivateIp(ip) {
  if (net.isIPv4(ip)) {
    const [a, b] = ip.split('.').map(Number);
    return (
      a === 10 || a === 127 || a === 0 ||
      (a === 169 && b === 254) ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 168) ||
      (a === 100 && b >= 64 && b <= 127) ||
      a >= 224
    );
  }
  const v = ip.toLowerCase();
  if (v.startsWith('::ffff:')) return isPrivateIp(v.slice(7));
  return v === '::1' || v === '::' || v.startsWith('fc') || v.startsWith('fd') || v.startsWith('fe80');
}

export async function assertPublicUrl(rawUrl) {
  let u;
  try {
    u = new URL(rawUrl);
  } catch {
    throw new FetchError('That is not a valid web address.', 'invalid_url');
  }
  if (!['http:', 'https:'].includes(u.protocol)) {
    throw new FetchError('Only http and https addresses can be read.', 'invalid_url');
  }
  if (u.username || u.password) throw new FetchError('Addresses with passwords are not allowed.', 'invalid_url');
  if (config.allowPrivateHosts) return u;
  const host = u.hostname.replace(/^\[|\]$/g, '');
  if (host === 'localhost' || host.endsWith('.local') || host.endsWith('.internal')) {
    throw new FetchError('Private network addresses are not allowed.', 'blocked_host');
  }
  let addrs;
  try {
    addrs = net.isIP(host) ? [{ address: host }] : await dns.lookup(host, { all: true });
  } catch {
    throw new FetchError(`Could not find the website ${host}.`, 'dns');
  }
  if (!addrs.length || addrs.some((a) => isPrivateIp(a.address))) {
    throw new FetchError('Private network addresses are not allowed.', 'blocked_host');
  }
  return u;
}

async function readLimited(res, maxBytes) {
  const len = Number(res.headers.get('content-length') || 0);
  if (len && len > maxBytes) throw new FetchError(`File is larger than ${Math.round(maxBytes / 1048576)} MB.`, 'too_large');
  const reader = res.body?.getReader();
  if (!reader) return Buffer.alloc(0);
  const parts = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maxBytes) {
      reader.cancel().catch(() => {});
      throw new FetchError(`File is larger than ${Math.round(maxBytes / 1048576)} MB.`, 'too_large');
    }
    parts.push(value);
  }
  return Buffer.concat(parts.map((p) => Buffer.from(p)));
}

/**
 * GET a public URL. Returns { url (final), status, contentType, body (Buffer) }.
 * Throws FetchError for network failures, blocked hosts, HTTP errors and size limits.
 */
export async function safeGet(rawUrl, { maxBytes = config.maxHtmlBytes, accept } = {}) {
  let url = rawUrl;
  for (let hop = 0; hop < 6; hop++) {
    await assertPublicUrl(url);
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), config.requestTimeoutMs);
    let res;
    try {
      res = await fetch(url, {
        redirect: 'manual',
        signal: ctrl.signal,
        headers: {
          'user-agent': config.userAgent,
          accept: accept || 'text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.5',
          'accept-language': 'en-US,en;q=0.8',
        },
      });
    } catch (e) {
      clearTimeout(timer);
      if (e.name === 'AbortError') throw new FetchError('The site took too long to respond.', 'timeout');
      throw new FetchError('Could not connect to the site.', 'network');
    }
    if ([301, 302, 303, 307, 308].includes(res.status)) {
      clearTimeout(timer);
      const loc = res.headers.get('location');
      if (!loc) throw new FetchError('Redirect without a destination.', 'http');
      url = new URL(loc, url).toString();
      continue;
    }
    try {
      if (res.status === 401 || res.status === 403) {
        throw new FetchError(`Access denied by the site (HTTP ${res.status}).`, 'denied');
      }
      if (res.status === 429) throw new FetchError('The site asked us to slow down (HTTP 429).', 'rate_limited');
      if (res.status >= 400) throw new FetchError(`The page returned HTTP ${res.status}.`, 'http');
      const body = await readLimited(res, maxBytes);
      return {
        url,
        status: res.status,
        contentType: (res.headers.get('content-type') || '').toLowerCase(),
        body,
      };
    } finally {
      clearTimeout(timer);
    }
  }
  throw new FetchError('Too many redirects.', 'http');
}
