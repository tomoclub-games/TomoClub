// Vercel serverless function: POST /api/signup
// Handles the Leaders of Tomorrow e-book forms and the toolkit download popup.
// Each submission is checked for spam (api/_lib/guard.js), saved as one row in the shared Google Sheet
// through the Apps Script collector (data-capture/Code.gs), and added to the Instantly lead list when
// INSTANTLY_API_KEY and INSTANTLY_LIST_ID are set. No emails are sent from here.
//
// Env vars:
//   SHEET_WEBHOOK       the Apps Script Web app URL (ends in /exec)
//   INSTANTLY_API_KEY   optional, Instantly API v2 key (leads:create)
//   INSTANTLY_LIST_ID   optional, Instantly lead list id

import { clean, clientIp, originAllowed, tooMany, checkHuman, validEmail, saveToSheet, addToInstantly } from './_lib/guard.js';

// Form type sent by the page -> tab in the Google Sheet.
const TABS = {
  ebook_request: 'E-book requests',
  resource: 'Toolkit downloads',
};

// Attribution fields the pages send along with the form, and their maximum lengths.
const ATTRIBUTION_FIELDS = {
  utm_source: 120, utm_medium: 120, utm_campaign: 120, utm_content: 120, utm_term: 120,
  gclid: 200, fbclid: 200, referrer: 300, landing_page: 300,
};

export default async function handler(req, res) {
  // 1. Security: enforce POST and the site's own origin
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  if (!originAllowed(req)) {
    return res.status(403).json({ error: 'Not allowed' });
  }

  const ip = clientIp(req);
  if (tooMany(ip, 30)) {
    return res.status(429).json({ error: 'Too many requests' });
  }

  // 2. Data extraction and basic sanitisation
  const b = req.body && typeof req.body === 'object' ? req.body : {};

  // Spam checks (honeypot, time trap, optional Turnstile). Bots get a normal reply and nothing is saved.
  const verdict = await checkHuman(b, ip);
  if (verdict === 'silent-drop') return res.status(200).json({ success: true, message: 'Processed successfully' });
  if (verdict === 'reject') return res.status(400).json({ error: 'Verification failed' });
  const type = clean(b.type, 30);
  const tab = TABS[type];
  if (!tab) {
    return res.status(400).json({ error: 'Unknown form type' });
  }

  const finalEmail = clean(b.email, 200);
  const firstName = clean(b.firstName || b.name, 120);
  const toolkitName = clean(b.toolkitName, 200);
  const source = clean(b.source, 120);
  const role = clean(b.role, 80);

  if (!validEmail(finalEmail)) {
    return res.status(400).json({ error: 'Email is required' });
  }

  try {
    // 3. Save to Google Sheets (server side, so the Apps Script URL never appears in the page)
    const row = { timestamp: new Date().toISOString(), first_name: firstName, email: finalEmail, source: source || 'Website' };
    if (type === 'ebook_request') row.role = role;
    if (type === 'resource') row.toolkit = toolkitName;
    // Where the visitor came from (captured in the browser by assets/js/analytics.js)
    Object.keys(ATTRIBUTION_FIELDS).forEach((k) => { row[k] = clean(b[k], ATTRIBUTION_FIELDS[k]); });
    // Save to the sheet and add the contact to the Instantly lead list at the same time.
    const [saved] = await Promise.all([
      saveToSheet(process.env.SHEET_WEBHOOK, tab, row),
      addToInstantly({
        email: finalEmail, name: firstName, role, form: type, page: source || 'website',
        utm_source: row.utm_source, utm_medium: row.utm_medium, utm_campaign: row.utm_campaign,
      }),
    ]);
    if (!saved) {
      // The pages ignore this status and still show their thank-you message and start the download.
      return res.status(502).json({ error: 'Could not save' });
    }
    return res.status(200).json({ success: true, message: 'Processed successfully' });

  } catch (error) {
    console.error('Server-side Error:', error);
    // Security: Don't leak internal error details to client
    return res.status(500).json({ error: 'Internal processing error' });
  }
}
