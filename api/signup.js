// Vercel serverless function: POST /api/signup
// Handles the Leaders of Tomorrow e-book forms and the toolkit download popup.
// Each submission is saved as one row in the shared Google Sheet through the Apps Script collector
// (data-capture/Code.gs), which alerts the team once per submission. The contact is added to Instantly only when
// the visitor ticked "Send me occasional emails" (marketing_consent = yes).
//
// Env vars:
//   SHEET_WEBHOOK   the Apps Script Web app URL (ends in /exec)

import {
  originAllowed, clientIp, tooMany, spamReason, clean, isEmail, emailType, attribution, saveToSheet, readBody,
  yes, newId, cleanId, pushToInstantly, splitName,
} from './_lead-core.js';

// Form type sent by the page -> tab in the Google Sheet, and the Instantly intent.
const TABS = { ebook_request: 'E-book requests', resource: 'Toolkit downloads' };
const INTENTS = { ebook_request: 'ebook_download', resource: 'guide_download' };

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  if (!originAllowed(req)) return res.status(403).json({ error: 'Not allowed' });
  if (tooMany(clientIp(req), 30, undefined, 'signup')) return res.status(429).json({ error: 'Too many requests' });

  const b = readBody(req);
  const type = clean(b.type, 30);
  const tab = TABS[type];
  if (!tab) return res.status(400).json({ error: 'Unknown form type' });

  const reason = spamReason(b);
  if (reason) {
    console.warn('signup rejected as spam:', reason);
    return res.status(200).json({ success: true }); // look like a success so bots learn nothing
  }

  const email = clean(b.email, 200).toLowerCase();
  const firstName = clean(b.firstName || b.name, 120);
  if (!isEmail(email)) return res.status(400).json({ error: 'Email is required' });

  const marketing = yes(b.marketing_consent);
  const row = {
    timestamp: new Date().toISOString(), first_name: firstName, email, source: clean(b.source, 120) || 'Website',
    ...attribution(b),
    submission_id: cleanId(b.submission_id) || newId('dl'),
    draft_id: cleanId(b.draft_id),
    marketing_consent: marketing ? 'yes' : 'no',
    visitor_id: cleanId(b.visitor_id),
    instantly_status: 'not sent: no marketing consent',
  };
  if (type === 'ebook_request') row.role = clean(b.role, 80);
  if (type === 'resource') row.toolkit = clean(b.toolkitName, 200);

  if (marketing) {
    const n = splitName(firstName);
    row.instantly_status = await pushToInstantly(INTENTS[type], {
      email, first_name: n.first_name, last_name: n.last_name, job_title: row.role || '',
      custom_variables: { intent: INTENTS[type], resource: row.toolkit || 'Leaders of Tomorrow ebook', email_type: emailType(email), source_page: row.source },
    });
  }

  if (!(await saveToSheet([{ sheet: tab, data: row }]))) {
    // The pages ignore this status and still show their thank-you message and start the download.
    return res.status(502).json({ error: 'Could not save' });
  }
  return res.status(200).json({ success: true, submission_id: row.submission_id });
}
