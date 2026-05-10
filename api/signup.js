export default async function handler(req, res) {
  // 1. Security: Enforce POST method
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // 2. Data Extraction & Basic Sanitization
  // In a full production app, use a library like 'validator' or 'zod'
  const { type, name, firstName, email, phone, message, toolkitName, source } = req.body;
  
  // Basic validation
  const finalEmail = email || '';
  const finalName = name || firstName || 'User';

  if (!finalEmail) {
    return res.status(400).json({ error: 'Email is required' });
  }

  // 3. Secrets Management
  // IMPORTANT: Move these to Vercel Project Settings > Environment Variables
  const BREVO_API_KEY = process.env.BREVO_API_KEY;
  const NEWSLETTER_WEBHOOK = process.env.NEWSLETTER_WEBHOOK || 'https://script.google.com/macros/s/AKfycbw6U18U6Y8-W7z9M5Y7W8z8z8z8z8z8z8z8z8z8z8z8z8z8/exec'; // Placeholder, user needs to update
  const SIGNUP_WEBHOOK = process.env.SIGNUP_WEBHOOK || 'https://script.google.com/macros/s/AKfycbzz2VpoSdbCDsfGo4-3O6KnnjsEHUaMHuCCUN0KsQyBatGz_EMc-xdFC5FnvlKBWb40/exec';
  const RESOURCE_WEBHOOK = process.env.RESOURCE_WEBHOOK || 'https://script.google.com/macros/s/AKfycbwFuKr-0GwdBfPylk7pmIhcbQX401Qye5t61ZsrjfbQ6TUToblKfX-l2bzv5DAFKuxc/exec';
  const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'info@tomoclub.org';

  try {
    // 4. Determine which webhook to use
    let targetWebhook = SIGNUP_WEBHOOK;
    if (type === 'resource') {
      targetWebhook = RESOURCE_WEBHOOK;
    } else if (type === 'newsletter') {
      targetWebhook = NEWSLETTER_WEBHOOK;
    }
    
    // 5. Save to Google Sheets (Proxy request to avoid CORS issues and expose endpoint)
    const googleSheetPromise = fetch(targetWebhook, {
      method: 'POST',
      body: new URLSearchParams({
        ...req.body,
        source: source || 'Vercel API Proxy'
      })
    }).catch(err => console.error('Data Logging Error:', err));

    // 6. Email Notifications (If Brevo key is present)
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
              <p>In the meantime, feel free to explore our <a href="https://www.tomoclub.org#guides">Guides & Toolkits</a> or listen to our <a href="https://www.tomoclub.org#podcast">Podcast</a>.</p>
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

    // Wait for critical tasks
    await Promise.all([...emailPromises, googleSheetPromise]);

    return res.status(200).json({ success: true, message: 'Processed successfully' });

  } catch (error) {
    console.error('Server-side Error:', error);
    // Security: Don't leak internal error details to client
    return res.status(500).json({ error: 'Internal processing error' });
  }
}
