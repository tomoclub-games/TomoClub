// Vercel serverless function: POST /api/lead
// The home page form and the Calendly booking capture send leads here. Each lead is saved as a row in the
// "School leads" tab of the form Sheet through the Apps Script collector (data-capture/Code.gs), which also
// posts the Slack alert.
//
// Types:
//   discovery_request  "Tell us what you are trying to fix" form on the home page
//   build_with_us      "Tell us about your school" form on /build-with-us
//   call_booked        sent by the page after Calendly reports a booking; carries the Calendly invitee URI,
//                      and this function reads the invitee's name and email from Calendly (needs CALENDLY_TOKEN
//                      with the scheduled_events:read scope). Nothing the browser says about the invitee is trusted.
//
// Every row carries a submission_id, so a retried request is saved and alerted only once (Code.gs), and a
// draft_id, so a partial lead saved from the same form is marked as converted. The contact goes to Instantly only
// when the visitor ticked "Send me occasional emails" (marketing_consent = yes); Calendly bookings never do.

import {
  originAllowed, clientIp, tooMany, spamReason, clean, isEmail, emailType, attribution,
  saveToSheet, readBody, isPhone, yes, newId, cleanId, hashId, pushToInstantly, splitName,
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
  if (tooMany(ip, 15, undefined, 'lead')) return res.status(429).json({ ok: false, error: 'Too many requests' });

  const b = readBody(req);
  const type = clean(b.type, 30);
  if (!['discovery_request', 'build_with_us', 'call_booked'].includes(type)) {
    return res.status(400).json({ ok: false, error: 'Unknown form type' });
  }

  let lead;
  if (type === 'call_booked') {
    const inv = await calendlyInvitee(clean(b.invitee_uri, 300));
    if (!inv || !isEmail(inv.email)) return res.status(400).json({ ok: false, error: 'Booking not found' });
    lead = { name: inv.name, email: inv.email.toLowerCase(), org: '', role: '', message: inv.answers, meeting_start: inv.start,
      submission_id: hashId('cal', clean(b.invitee_uri, 300)), marketing: false };
  } else {
    const reason = spamReason(b);
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
      phone: isPhone(b.phone) ? clean(b.phone, 30) : '',
      submission_id: cleanId(b.submission_id) || newId('sub'),
      marketing: yes(b.marketing_consent),
    };
    if (!isEmail(lead.email)) return res.status(400).json({ ok: false, error: 'A valid email is required' });
    if (!lead.name || !lead.org) return res.status(400).json({ ok: false, error: 'Name and school or district are required' });
  }

  const row = {
    timestamp: new Date().toISOString(),
    type,
    name: lead.name,
    email: lead.email,
    email_type: emailType(lead.email),
    organization: lead.org,
    role: lead.role,
    state: lead.state || '',
    offer_interest: clean(b.offer_interest, 60),
    message: lead.message,
    meeting_start: lead.meeting_start || '',
    page: clean(b.page, 120),
    ...attribution(b),
    phone: lead.phone || '',
    form: clean(b.form_name, 60) || type,
    submission_id: lead.submission_id,
    draft_id: cleanId(b.draft_id),
    marketing_consent: lead.marketing ? 'yes' : 'no',
    visitor_id: cleanId(b.visitor_id),
    instantly_status: '',
  };

  if (lead.marketing) {
    const n = splitName(lead.name);
    row.instantly_status = await pushToInstantly(type, {
      email: lead.email, first_name: n.first_name, last_name: n.last_name, company_name: lead.org, job_title: lead.role,
      phone: lead.phone, custom_variables: { intent: type, offer_interest: row.offer_interest, state: row.state, source_page: row.page, utm_source: row.utm_source },
    });
  } else {
    row.instantly_status = 'not sent: no marketing consent';
  }

  if (!(await saveToSheet([{ sheet: 'School leads', data: row }]))) {
    return res.status(502).json({ ok: false, error: 'Could not save. Please email avinash@tomoclub.org.' });
  }
  return res.status(200).json({ ok: true, name: lead.name.split(/\s+/)[0], submission_id: lead.submission_id });
}
