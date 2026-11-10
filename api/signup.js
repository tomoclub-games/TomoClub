// Vercel serverless function: POST /api/signup
// Handles the Leaders of Tomorrow e-book forms and the toolkit download popup.
// Each submission is saved as one row in the shared Google Sheet through the Apps Script collector
// (data-capture/Code.gs). Optional Brevo emails are sent too, only if BREVO_API_KEY is set.
//
// Env vars:
//   SHEET_WEBHOOK   the Apps Script Web app URL (ends in /exec)
//   BREVO_API_KEY   optional; without it no emails are sent
//   ADMIN_EMAIL     optional, where the admin notification goes (default info@tomoclub.org)

const ALLOWED_ORIGINS = [
  /^https:\/\/(www\.)?tomoclub\.org$/,
  /^https:\/\/tomoclub-website[a-z0-9-]*\.vercel\.app$/,
  /^http:\/\/localhost:\d+$/,
];

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

// Best-effort limit per warm server instance.
const hits = new Map();
function tooMany(ip) {
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter((t) => now - t < 10 * 60 * 1000);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 500) hits.clear();
  return recent.length > 30;
}

const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);

// Append one row to the Google Sheet through the Apps Script collector.
async function saveToSheet(sheet, data) {
  const url = process.env.SHEET_WEBHOOK;
  if (!url) { console.error('SHEET_WEBHOOK env var is not set'); return false; }
  try {
    // Apps Script answers through a redirect, which fetch follows; the JSON body says whether it worked.
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ rows: [{ sheet, data }] }),
      signal: AbortSignal.timeout(8000),
    });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j || j.ok !== true) { console.error('Apps Script rejected the row:', r.status, JSON.stringify(j)); return false; }
    return true;
  } catch (error) {
    console.error('sheet write error:', error);
    return false;
  }
}

export default async function handler(req, res) {
  // 1. Security: enforce POST and the site's own origin
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  if (!ALLOWED_ORIGINS.some((re) => re.test(req.headers.origin || ''))) {
    return res.status(403).json({ error: 'Not allowed' });
  }

  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  if (tooMany(ip)) {
    return res.status(429).json({ error: 'Too many requests' });
  }

  // 2. Data extraction and basic sanitisation
  const b = req.body && typeof req.body === 'object' ? req.body : {};
  const type = clean(b.type, 30);
  const tab = TABS[type];
  if (!tab) {
    return res.status(400).json({ error: 'Unknown form type' });
  }

  const finalEmail = clean(b.email, 200);
  const firstName = clean(b.firstName || b.name, 120);
  const finalName = firstName || 'User';
  const phone = clean(b.phone, 40);
  const message = clean(b.message, 1000);
  const toolkitName = clean(b.toolkitName, 200);
  const source = clean(b.source, 120);
  const role = clean(b.role, 80);

  if (!/^\S+@\S+\.\S+$/.test(finalEmail)) {
    return res.status(400).json({ error: 'Email is required' });
  }

  const BREVO_API_KEY = process.env.BREVO_API_KEY;
  const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'info@tomoclub.org';

  try {
    // 3. Save to Google Sheets (server side, so the Apps Script URL never appears in the page)
    const row = { timestamp: new Date().toISOString(), first_name: firstName, email: finalEmail, source: source || 'Website' };
    if (type === 'ebook_request') row.role = role;
    if (type === 'resource') row.toolkit = toolkitName;
    // Where the visitor came from (captured in the browser by assets/js/analytics.js)
    Object.keys(ATTRIBUTION_FIELDS).forEach((k) => { row[k] = clean(b[k], ATTRIBUTION_FIELDS[k]); });
    const sheetPromise = saveToSheet(tab, row);

    // 4. Email notifications (only if a Brevo key is present)
    let emailPromises = [];
    if (BREVO_API_KEY) {
      // Send Confirmation Email to User
      emailPromises.push(fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'api-key': BREVO_API_KEY,
          'content-type': 'application/json'
        },
        body: JSON.stringify({
          sender: { name: 'TomoClub', email: 'info@tomoclub.org' },
          to: [{ email: finalEmail, name: finalName }],
          subject: (type === 'resource') ? `Your Guide: ${toolkitName}` : 'Thank you for your interest in TomoClub!',
          htmlContent: `
            <div style="font-family: sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
              <h2>Hi ${finalName},</h2>
              <p>Thank you for reaching out to TomoClub! We've received your ${(type === 'resource') ? 'request for the ' + toolkitName : 'inquiry'} and our team will get back to you shortly.</p>
              <p>In the meantime, feel free to explore our <a href="https://www.tomoclub.org/guides">Guides & Toolkits</a> or listen to our <a href="https://www.tomoclub.org/podcast">Podcast</a>.</p>
              <br>
              <p>Best regards,<br><strong>The TomoClub Team</strong></p>
            </div>
          `
        })
      }));

      // Send Admin Notification Email
      emailPromises.push(fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'api-key': BREVO_API_KEY,
          'content-type': 'application/json'
        },
        body: JSON.stringify({
          sender: { name: 'TomoClub System', email: 'info@tomoclub.org' },
          to: [{ email: ADMIN_EMAIL, name: 'Admin' }],
          subject: `New ${type || 'Signup'} from Website`,
          htmlContent: `
            <div style="font-family: sans-serif; line-height: 1.6; color: #333;">
              <h2>New Lead Details</h2>
              <p><strong>Type:</strong> ${type || 'General'}</p>
              <p><strong>Name:</strong> ${finalName}</p>
              <p><strong>Email:</strong> ${finalEmail}</p>
              ${phone ? `<p><strong>Phone:</strong> ${phone}</p>` : ''}
              ${toolkitName ? `<p><strong>Resource:</strong> ${toolkitName}</p>` : ''}
              ${message ? `<p><strong>Message:</strong> ${message}</p>` : ''}
              <p><strong>Source:</strong> ${source || 'Website'}</p>
            </div>
          `
        })
      }));
    }

    // Wait for the critical tasks
    const [saved] = await Promise.all([sheetPromise, ...emailPromises]);
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
