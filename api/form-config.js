// Vercel serverless function: GET /api/form-config -> { turnstileSiteKey: "..." | "" }
// Tells assets/js/form-guard.js whether to show the Cloudflare Turnstile check on forms.
// Set TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY together in Vercel; with neither set, forms rely on the
// honeypot, time trap and rate limit in api/_lib/guard.js.
export default function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
  res.status(200).json({ turnstileSiteKey: process.env.TURNSTILE_SECRET_KEY ? (process.env.TURNSTILE_SITE_KEY || '') : '' });
}
