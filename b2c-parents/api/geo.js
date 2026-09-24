// Vercel serverless function: GET /api/geo -> {"country":"ES"}
// Vercel adds the visitor's country to every request as the x-vercel-ip-country header,
// so this needs no external service and cannot be blocked by ad blockers.
// Put this file at api/geo.js in the root of the Vercel project (next to the page), then redeploy.
export default function handler(req, res) {
  const country = (req.headers['x-vercel-ip-country'] || '').toUpperCase();
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.status(200).json({ country: /^[A-Z]{2}$/.test(country) ? country : '' });
}
