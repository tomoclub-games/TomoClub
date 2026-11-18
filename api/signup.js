// Vercel serverless function: POST /api/signup
// Handles the Leaders of Tomorrow e-book forms and the toolkit download popup.
// Each submission is saved as one row in the shared Google Sheet through the Apps Script collector
// (data-capture/Code.gs), then added to Instantly under the ebook_download or guide_download intent
// (api/_lead-core.js). The download forms say "By downloading, you agree to receive future updates from TomoClub."
//
// Env vars:
//   SHEET_WEBHOOK   the Apps Script Web app URL (ends in /exec)

import {
  originAllowed, clientIp, tooMany, spamReason, clean as cleanCore, isEmail, emailType, attribution,
  saveToSheet as saveRows, pushToInstantly, splitName, readBody, signLead,
} from './_lead-core.js';

// Form type sent by the page -> tab in the Google Sheet, and the Instantly intent.
const TABS = {
  ebook_request: 'E-book requests',
  resource: 'Toolkit downloads',
};
const INTENTS = { ebook_request: 'ebook_download', resource: 'guide_download' };
const clean = (v, max) => cleanCore(v, max);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  if (!originAllowed(req)) return res.status(403).json({ error: 'Not allowed' });
  const ip = clientIp(req);
  if (tooMany(ip, 30)) return res.status(429).json({ error: 'Too many requests' });

  const b = readBody(req);
  const type = clean(b.type, 30);
  const tab = TABS[type];
  if (!tab) return res.status(400).json({ error: 'Unknown form type' });

  const reason = await spamReason(b, ip);
  if (reason) {
    console.warn('signup rejected as spam:', reason);
    return res.status(200).json({ success: true });
  }

  const finalEmail = clean(b.email, 200).toLowerCase();
  const firstName = clean(b.firstName || b.name, 120);
  const toolkitName = clean(b.toolkitName, 200);
  const source = clean(b.source, 120);
  const role = clean(b.role, 80);
  if (!isEmail(finalEmail)) return res.status(400).json({ error: 'Email is required' });

  try {
    const attr = attribution(b);
    const row = { timestamp: new Date().toISOString(), first_name: firstName, email: finalEmail, source: source || 'Website', ...attr };
    if (type === 'ebook_request') row.role = role;
    if (type === 'resource') row.toolkit = toolkitName;

    const names = splitName(firstName);
    const [saved, instantly] = await Promise.all([
      saveRows([{ sheet: tab, data: row }]),
      pushToInstantly(INTENTS[type], {
        email: finalEmail,
        first_name: names.first_name,
        last_name: names.last_name,
        job_title: role,
        custom_variables: {
          intent: INTENTS[type],
          resource: type === 'resource' ? toolkitName : 'Leaders of Tomorrow ebook',
          email_type: emailType(finalEmail),
          source_page: source,
          utm_source: attr.utm_source,
          utm_campaign: attr.utm_campaign,
          first_seen_page: attr.landing_page,
        },
      }),
    ]);
    if (!saved && !instantly.ok) {
      // The pages ignore this status and still show their thank-you message and start the download.
      return res.status(502).json({ error: 'Could not save' });
    }
    return res.status(200).json({ success: true, email: finalEmail, token: signLead(finalEmail, 'nurture'), scope: 'nurture' });
  } catch (error) {
    console.error('Server-side Error:', error);
    return res.status(500).json({ error: 'Internal processing error' });
  }
}
