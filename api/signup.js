export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name, email, phone, message } = req.body;

  if (!name || !email) {
    return res.status(400).json({ error: 'Name and Email are required' });
  }

  const BREVO_API_KEY = process.env.BREVO_API_KEY;
  const GOOGLE_SHEET_WEBHOOK = 'https://script.google.com/macros/s/AKfycbzz2VpoSdbCDsfGo4-3O6KnnjsEHUaMHuCCUN0KsQyBatGz_EMc-xdFC5FnvlKBWb40/exec';
  const ADMIN_EMAIL = 'info@tomoclub.org'; // Default admin email

  try {
    // 1. Save to Google Sheets
    // Note: We use fetch to the Apps Script Webhook
    // Apps Script doesn't always support JSON POST well without 'no-cors' on frontend,
    // but from server-side we can send form-encoded or JSON depending on the script.
    // Assuming the script expects form data or simple object.
    const googleSheetPromise = fetch(GOOGLE_SHEET_WEBHOOK, {
      method: 'POST',
      body: new URLSearchParams({
        name: name,
        email: email,
        phone: phone || '',
        message: message || '',
        source: 'Vercel Signup Form'
      })
    }).catch(err => console.error('Google Sheets Error:', err));

    // 2. Send Confirmation Email to User via Brevo
    const userEmailPromise = fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'api-key': BREVO_API_KEY,
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        sender: { name: 'TomoClub', email: 'info@tomoclub.org' },
        to: [{ email: email, name: name }],
        subject: 'Thank you for your interest in TomoClub!',
        htmlContent: `
          <div style="font-family: sans-serif; line-height: 1.6; color: #333;">
            <h2>Hi ${name},</h2>
            <p>Thank you for reaching out to TomoClub! We've received your inquiry and our team will get back to you shortly.</p>
            <p>In the meantime, feel free to explore our <a href="https://www.tomoclub.org#guides">Guides & Toolkits</a> or listen to our <a href="https://www.tomoclub.org#podcast">Podcast</a>.</p>
            <br>
            <p>Best regards,<br>The TomoClub Team</p>
          </div>
        `
      })
    });

    // 3. Send Admin Notification Email via Brevo
    const adminEmailPromise = fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'api-key': BREVO_API_KEY,
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        sender: { name: 'TomoClub System', email: 'info@tomoclub.org' },
        to: [{ email: ADMIN_EMAIL, name: 'Admin' }],
        subject: 'New Signup from Website',
        htmlContent: `
          <div style="font-family: sans-serif; line-height: 1.6; color: #333;">
            <h2>New Signup Details</h2>
            <p><strong>Name:</strong> ${name}</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Phone:</strong> ${phone || 'N/A'}</p>
            <p><strong>Message/Interest:</strong> ${message || 'N/A'}</p>
            <p>This lead has also been sent to Google Sheets.</p>
          </div>
        `
      })
    });

    // Wait for Brevo emails to finish (Google Sheets is fire-and-forget for speed, but we caught errors)
    const [userRes, adminRes] = await Promise.all([userEmailPromise, adminEmailPromise]);

    if (!userRes.ok || !adminRes.ok) {
        const userErr = await userRes.text();
        const adminErr = await adminRes.text();
        console.error('Brevo Error Details:', { userErr, adminErr });
        throw new Error('Email sending failed');
    }

    return res.status(200).json({ success: true, message: 'Signup successful!' });

  } catch (error) {
    console.error('Signup API Error:', error);
    return res.status(500).json({ error: 'Internal server error. Please try again later.' });
  }
}
