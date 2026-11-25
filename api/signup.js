// Vercel serverless function: POST /api/signup
// Handles the Leaders of Tomorrow e-book forms and the toolkit download popup.
// Each submission is saved as one row in the shared Google Sheet through the Apps Script collector
// (data-capture/Code.gs). No emails are sent. The pages start the download whatever this returns.

import {
  originAllowed, clientIp, tooMany, spamReason, clean, isEmail, isThrowaway, attribution,
  submissionId, saveToSheet, readBody,
} from './_lead-core.js';

// Form type sent by the page -> tab in the Google Sheet.
const TABS = {
  ebook_request: 'E-book requests',
  resource: 'Toolkit downloads',
};

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  if (!originAllowed(req)) return res.status(403).json({ error: 'Not allowed' });
  if (tooMany(clientIp(req), 30)) return res.status(429).json({ error: 'Too many requests' });

  const b = readBody(req);
  const type = clean(b.type, 30);
  const tab = TABS[type];
  if (!tab) return res.status(400).json({ error: 'Unknown form type' });

  const email = clean(b.email, 200);
  if (!isEmail(email)) return res.status(400).json({ error: 'Email is required' });

  // Spam and disposable inboxes: answer like a success so bots learn nothing, and save nothing.
  const reason = spamReason(b) || (isThrowaway(email) ? 'throwaway' : '');
  if (reason) {
    console.warn('signup rejected:', reason);
    return res.status(200).json({ success: true });
  }

  const row = {
    timestamp: new Date().toISOString(),
    first_name: clean(b.firstName || b.name, 120),
    email,
    source: clean(b.source, 120) || 'Website',
  };
  if (type === 'ebook_request') row.role = clean(b.role, 80);
  if (type === 'resource') row.toolkit = clean(b.toolkitName, 200);
  Object.assign(row, attribution(b), { submission_id: submissionId(b) });

  if (!(await saveToSheet([{ sheet: tab, data: row }]))) return res.status(502).json({ error: 'Could not save' });
  return res.status(200).json({ success: true });
}
