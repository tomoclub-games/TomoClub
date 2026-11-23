// Turns raw Sheet rows into the numbers and lists the /admin dashboard shows. Pure functions, no I/O,
// so they can be tested directly (tests/api.test.mjs).

import crypto from 'node:crypto';

const STATUSES = ['New', 'Contacted', 'Meeting booked', 'Qualified', 'Not a fit', 'Closed'];
export { STATUSES };

// Same rules as sourceOf() in assets/js/tc-forms.js, so events and leads group the same way.
export function sourceOf(utmSource, referrer) {
  const u = String(utmSource || '').trim().toLowerCase();
  if (u) return u.slice(0, 60);
  let host = '';
  try { host = new URL(String(referrer || '')).hostname.replace(/^www\./, ''); } catch (e) { return 'direct'; }
  if (!host || /(^|\.)tomoclub\.org$/.test(host) || /vercel\.app$/.test(host)) return 'direct';
  if (/(^|\.)google\./.test(host)) return 'google';
  if (/bing\.com$/.test(host)) return 'bing';
  if (/duckduckgo\.com$/.test(host)) return 'duckduckgo';
  if (/linkedin\.com$|lnkd\.in$/.test(host)) return 'linkedin';
  if (/facebook\.com$|fb\.me$/.test(host)) return 'facebook';
  if (/instagram\.com$/.test(host)) return 'instagram';
  if (/(^|\.)t\.co$|twitter\.com$|x\.com$/.test(host)) return 'x';
  if (/youtube\.com$|youtu\.be$/.test(host)) return 'youtube';
  if (/chatgpt\.com$|openai\.com$|perplexity\.ai$|claude\.ai$|gemini\.google/.test(host)) return 'ai assistant';
  return host.slice(0, 60);
}

const day = (iso) => String(iso || '').slice(0, 10);
const inRange = (iso, from, to) => { const d = String(iso || ''); return d >= from && d <= to + 'T99'; };
const leadIdFor = (tab, r) => r.submission_id || 'h-' + crypto.createHash('sha256').update(tab + '|' + r.timestamp + '|' + r.email).digest('base64url').slice(0, 16);

const KIND = {
  discovery_request: 'Discovery form', build_with_us: 'Build With Us form', call_booked: 'Booked call',
  ebook_download: 'Ebook download', guide_download: 'Guide download',
};

function latestStatus(rows) {
  const map = {};
  (rows || []).forEach((s) => {
    const prev = map[s.lead_id];
    if (!prev || String(s.updated_at) >= String(prev.updated_at)) map[s.lead_id] = s;
  });
  return map;
}

export function normaliseLeads(tabs) {
  const status = latestStatus(tabs['Lead status']);
  const withStatus = (l) => {
    const s = status[l.lead_id];
    return { ...l, status: s ? s.status : 'New', note: s ? s.note || '' : '', status_updated_at: s ? s.updated_at : '', status_by: s ? s.updated_by || '' : '' };
  };
  const completed = [];
  (tabs['School leads'] || []).forEach((r) => completed.push(withStatus({
    lead_id: leadIdFor('School leads', r), kind: KIND[r.type] || 'Form', type: r.type || '', received_at: r.timestamp,
    name: r.name || '', email: r.email || '', phone: r.phone || '', organization: r.organization || '', role: r.role || '',
    state: r.state || '', interest: r.offer_interest || '', message: r.message || '', meeting_start: r.meeting_start || '',
    page: r.page || '', source: sourceOf(r.utm_source, r.referrer), marketing_consent: r.marketing_consent || '',
  })));
  (tabs['E-book requests'] || []).forEach((r) => completed.push(withStatus({
    lead_id: leadIdFor('E-book requests', r), kind: KIND.ebook_download, type: 'ebook_download', received_at: r.timestamp,
    name: r.first_name || '', email: r.email || '', phone: '', organization: '', role: r.role || '', state: '', interest: 'Leaders of Tomorrow ebook',
    message: '', meeting_start: '', page: r.source || '', source: sourceOf(r.utm_source, r.referrer), marketing_consent: r.marketing_consent || '',
  })));
  (tabs['Toolkit downloads'] || []).forEach((r) => completed.push(withStatus({
    lead_id: leadIdFor('Toolkit downloads', r), kind: KIND.guide_download, type: 'guide_download', received_at: r.timestamp,
    name: r.first_name || '', email: r.email || '', phone: '', organization: '', role: '', state: '', interest: r.toolkit || '',
    message: '', meeting_start: '', page: r.source || '', source: sourceOf(r.utm_source, r.referrer), marketing_consent: r.marketing_consent || '',
  })));
  const partial = (tabs['Partial leads'] || [])
    .filter((r) => r.status === 'partial' && (r.email || r.phone))
    .map((r) => withStatus({
      lead_id: 'p-' + r.draft_id, kind: 'Unfinished form', type: 'partial', received_at: r.first_seen, last_updated: r.last_updated,
      name: r.name || '', email: r.email || '', phone: r.phone || '', organization: r.organization || '', role: r.role || '',
      form: r.form || '', page: r.page || '', source: sourceOf(r.utm_source, r.referrer), notified_at: r.notified_at || '',
      marketing_consent: r.marketing_consent || '',
    }));
  completed.sort((a, b) => String(b.received_at).localeCompare(String(a.received_at)));
  partial.sort((a, b) => String(b.last_updated).localeCompare(String(a.last_updated)));
  return { completed, partial };
}

function countBy(list, keyFn, valFn) {
  const m = new Map();
  list.forEach((x) => { const k = keyFn(x); if (k === undefined || k === null || k === '') return; const v = m.get(k) || valFn(); m.set(k, v); });
  return m;
}

export function computeDashboard(tabs, { from, to }) {
  const events = (tabs['Website events'] || []).filter((e) => inRange(e.timestamp, from, to));
  const { completed, partial } = normaliseLeads(tabs);
  const leadsIn = completed.filter((l) => inRange(l.received_at, from, to));
  const partialIn = partial.filter((l) => inRange(l.last_updated || l.received_at, from, to));

  const pv = events.filter((e) => e.event === 'page_view');
  const visitors = new Set(pv.map((e) => e.visitor_id));
  const sessions = new Set(pv.map((e) => e.session_id || e.visitor_id));
  const count = (name) => events.filter((e) => e.event === name).length;
  const bookingsConfirmed = leadsIn.filter((l) => l.type === 'call_booked').length;
  const formLeads = leadsIn.filter((l) => l.type !== 'call_booked').length;

  const kpis = {
    visitors: visitors.size,
    sessions: sessions.size,
    page_views: pv.length,
    cta_clicks: count('cta_click') + count('book_call_click'),
    form_views: count('form_view'),
    form_starts: count('form_start'),
    form_submissions: count('form_success'),
    form_abandons: count('form_abandon'),
    completed_leads: leadsIn.length,
    form_leads: formLeads,
    meetings_booked: bookingsConfirmed,
    partial_leads: partialIn.length,
  };
  const pct = (a, b) => (b ? Math.round((a / b) * 1000) / 10 : 0);
  kpis.visitor_to_lead_pct = pct(leadsIn.length, visitors.size);
  kpis.form_completion_pct = pct(kpis.form_submissions, kpis.form_starts);
  kpis.visitor_to_meeting_pct = pct(bookingsConfirmed, visitors.size);
  kpis.abandon_saved_pct = pct(partialIn.length, kpis.form_abandons);

  // Daily series
  const days = [];
  for (let d = new Date(from + 'T00:00:00Z'); day(d.toISOString()) <= to; d.setUTCDate(d.getUTCDate() + 1)) days.push(day(d.toISOString()));
  const series = days.map((d) => {
    const dv = pv.filter((e) => day(e.timestamp) === d);
    return {
      date: d, visitors: new Set(dv.map((e) => e.visitor_id)).size, page_views: dv.length,
      leads: leadsIn.filter((l) => day(l.received_at) === d).length,
      partial: partialIn.filter((l) => day(l.last_updated || l.received_at) === d).length,
    };
  });

  // Sources: visitors and sessions from page views, leads from the lead rows.
  const src = countBy(pv, (e) => e.source || 'direct', () => ({ visitors: new Set(), sessions: new Set(), leads: 0 }));
  pv.forEach((e) => { const s = src.get(e.source || 'direct'); s.visitors.add(e.visitor_id); s.sessions.add(e.session_id); });
  leadsIn.forEach((l) => { if (!src.has(l.source)) src.set(l.source, { visitors: new Set(), sessions: new Set(), leads: 0 }); src.get(l.source).leads++; });
  const sources = [...src.entries()].map(([name, s]) => ({ name, visitors: s.visitors.size, sessions: s.sessions.size, leads: s.leads, lead_rate_pct: pct(s.leads, s.visitors.size) }))
    .sort((a, b) => b.visitors - a.visitors || b.leads - a.leads);

  const dev = countBy(pv, (e) => e.device || 'unknown', () => new Set());
  pv.forEach((e) => dev.get(e.device || 'unknown').add(e.visitor_id));
  const devices = [...dev.entries()].map(([name, s]) => ({ name, visitors: s.size })).sort((a, b) => b.visitors - a.visitors);

  const pages = [...countBy(pv, (e) => e.page || '/', () => ({ n: 0 })).entries()]
    .map(([name]) => ({ name, views: pv.filter((e) => (e.page || '/') === name).length })).sort((a, b) => b.views - a.views).slice(0, 15);

  const clicks = events.filter((e) => e.event === 'cta_click' || e.event === 'book_call_click');
  const ctaMap = new Map();
  clicks.forEach((e) => { const k = (e.label || '(no label)').split(' | ')[0]; ctaMap.set(k, (ctaMap.get(k) || 0) + 1); });
  const ctas = [...ctaMap.entries()].map(([name, clicks]) => ({ name, clicks })).sort((a, b) => b.clicks - a.clicks).slice(0, 20);

  const formNames = new Set(events.filter((e) => e.form).map((e) => e.form));
  const forms = [...formNames].map((f) => {
    const n = (ev) => events.filter((e) => e.form === f && e.event === ev).length;
    const starts = n('form_start'), success = n('form_success');
    return { name: f, views: n('form_view'), starts, submissions: success, abandons: n('form_abandon'), partial_saved: n('partial_saved'), completion_pct: pct(success, starts) };
  }).sort((a, b) => b.views - a.views);

  return { range: { from, to }, kpis, series, sources, devices, pages, ctas, forms, leads: { completed: leadsIn, partial: partialIn }, statuses: STATUSES };
}
