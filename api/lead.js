// Vercel serverless function: POST /api/lead
// The B2B forms send leads here. Each lead is saved to the "School leads" tab of the form Sheet and then
// added to Instantly (see api/_lead-core.js for the env vars and the intent -> list/campaign routing).
//
// Types:
//   discovery_request  "Tell us about your school" form (home page, contact page, Build With Us)
//   newsletter         email-only signup
//   call_booked        sent by the page after Calendly reports a booking; carries the Calendly invitee URI,
//                      and this function reads the invitee's name and email from Calendly (needs CALENDLY_TOKEN
//                      with the scheduled_events:read scope). Nothing the browser says about the invitee is trusted.

import {
  originAllowed, clientIp, tooMany, spamReason, clean, isEmail, emailType, attribution,
  saveToSheet, pushToInstantly, splitName, readBody, signLead,
} from './_lead-core.js';

const ROLES = ['Superintendent', 'Assistant or deputy superintendent', 'Principal or head of school',
  'Curriculum or PD leader', 'Technology or innovation leader', 'Student services or special education',
  'Teacher or coach', 'Board member', 'Education partner or nonprofit', 'Other'];

async function calendlyInvitee(uri) {
  const token = process.env.CALENDLY_TOKEN;
  if (!token || !/^https:\/\/api\.calendly\.com\/scheduled_events\/[\w-]+\/invitees\/[\w-]+$/.test(uri)) return null;
  try {
    const r = await fetch(uri, { headers: { Authorization: 'Bearer ' + token }, signal: AbortSignal.timeout(8000) });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j || !j.resource) { console.error('Calendly invitee read failed:', r.status); return null; }
    const inv = j.resource;
    let start = '';
    try {
      const ev = await fetch(inv.event, { headers: { Authorization: 'Bearer ' + token }, signal: AbortSignal.timeout(8000) });
      const ej = await ev.json().catch(() => null);
      start = (ej && ej.resource && ej.resource.start_time) || '';
    } catch (e) { /* start time is optional */ }
    const answers = (inv.questions_and_answers || []).map((q) => q.question + ': ' + q.answer).join(' | ');
    return { name: inv.name || '', email: inv.email || '', start, answers };
  } catch (e) {
    console.error('Calendly request error:', e);
    return null;
  }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Method not allowed' });
  if (!originAllowed(req)) return res.status(403).json({ ok: false, error: 'Not allowed' });
  const ip = clientIp(req);
  if (tooMany(ip, 15)) return res.status(429).json({ ok: false, error: 'Too many requests' });

  const b = readBody(req);
  const type = clean(b.type, 30);
  if (!['discovery_request', 'newsletter', 'call_booked'].includes(type)) {
    return res.status(400).json({ ok: false, error: 'Unknown form type' });
  }

  let lead;
  if (type === 'call_booked') {
    const inv = await calendlyInvitee(clean(b.invitee_uri, 300));
    if (!inv || !isEmail(inv.email)) return res.status(400).json({ ok: false, error: 'Booking not found' });
    lead = { name: inv.name, email: inv.email, org: '', role: '', message: inv.answers, meeting_start: inv.start };
  } else {
    const reason = await spamReason(b, ip);
    if (reason) {
      console.warn('lead rejected as spam:', reason);
      // Answer like a success so bots learn nothing.
      return res.status(200).json({ ok: true });
    }
    lead = {
      name: clean(b.name, 120),
      email: clean(b.email, 200).toLowerCase(),
      org: clean(b.district || b.organization, 160),
      role: ROLES.includes(clean(b.role, 80)) ? clean(b.role, 80) : clean(b.role, 80) ? 'Other' : '',
      state: clean(b.state, 40),
      message: clean(b.goal || b.message, 3000),
    };
    if (!isEmail(lead.email)) return res.status(400).json({ ok: false, error: 'A valid email is required' });
    if (type === 'discovery_request' && (!lead.name || !lead.org)) {
      return res.status(400).json({ ok: false, error: 'Name and school or district are required' });
    }
  }

  const attr = attribution(b);
  const page = clean(b.page, 120);
  const offer = clean(b.offer_interest, 60);
  const row = {
    timestamp: new Date().toISOString(),
    type,
    name: lead.name,
    email: lead.email,
    email_type: emailType(lead.email),
    organization: lead.org,
    role: lead.role,
    state: lead.state || '',
    offer_interest: offer,
    message: lead.message,
    meeting_start: lead.meeting_start || '',
    page,
    pages_viewed: clean(b.pages_viewed, 500),
    ...attr,
    instantly_status: '',
  };

  const { first_name, last_name } = splitName(lead.name);
  const instantly = await pushToInstantly(type, {
    email: lead.email,
    first_name,
    last_name,
    company_name: lead.org,
    job_title: lead.role,
    custom_variables: {
      intent: type,
      offer_interest: offer,
      source_page: page,
      state: lead.state || '',
      their_words: lead.message ? lead.message.slice(0, 400) : '',
      meeting_start: lead.meeting_start || '',
      utm_source: attr.utm_source,
      utm_campaign: attr.utm_campaign,
      first_seen_page: attr.landing_page,
    },
  });
  row.instantly_status = instantly.status + (instantly.detail ? ' (' + instantly.detail + ')' : '');

  const saved = await saveToSheet([{ sheet: 'School leads', data: row }]);
  if (!saved && !instantly.ok) {
    return res.status(502).json({ ok: false, error: 'Could not save. Please email avinash@tomoclub.org.' });
  }
  return res.status(200).json({ ok: true, name: first_name, email: lead.email, token: signLead(lead.email, 'hot'), scope: 'hot' });
}
