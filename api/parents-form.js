export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const webhook = process.env.PARENTS_FORM_WEBHOOK;
  if (!webhook) {
    console.error('PARENTS_FORM_WEBHOOK env var is not set');
    return res.status(500).json({ ok: false, error: 'Form is not configured' });
  }

  const data = req.body || {};
  if (!data.email) {
    return res.status(400).json({ ok: false, error: 'Email is required' });
  }

  try {
    // Apps Script always responds via a redirect to script.googleusercontent.com
    // (even on a correctly public deployment) so redirects must be followed;
    // whether it actually reached doPost is decided by the JSON body below.
    const upstream = await fetch(webhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const result = await upstream.json().catch(() => null);

    if (!upstream.ok || result === null || result.ok !== true) {
      console.error('Apps Script webhook rejected submission:', upstream.status, result);
      return res.status(502).json({ ok: false, error: 'Could not save submission' });
    }

    return res.status(200).json({ ok: true });
  } catch (error) {
    console.error('parents-form proxy error:', error);
    return res.status(502).json({ ok: false, error: 'Could not reach form backend' });
  }
}
