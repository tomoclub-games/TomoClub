// Vercel serverless function: GET /api/slots -> { ok: true, slots: ["2026-11-12T11:30:00Z", ...] }
// Returns the open times of the free trial class event type in Calendly (next 30 days).
// Calendly only lists times that are still open, so booked times are simply absent.
// Needs two env vars (Vercel > Settings > Environment Variables):
//   CALENDLY_TOKEN           personal access token (scopes: availability:read, scheduled_events:write)
//   CALENDLY_EVENT_TYPE_URI  e.g. https://api.calendly.com/event_types/XXXXXXXX
export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  const token = process.env.CALENDLY_TOKEN;
  const eventType = process.env.CALENDLY_EVENT_TYPE_URI;
  if (!token || !eventType) {
    console.error('CALENDLY_TOKEN or CALENDLY_EVENT_TYPE_URI env var is not set');
    return res.status(500).json({ ok: false, error: 'Booking is not configured' });
  }

  // Calendly: start must not be in the past, and the range can be at most 31 days.
  const start = new Date(Date.now() + 60 * 1000);
  const end = new Date(start.getTime() + 30 * 24 * 60 * 60 * 1000);
  const url = 'https://api.calendly.com/event_type_available_times?' + new URLSearchParams({
    event_type: eventType,
    start_time: start.toISOString(),
    end_time: end.toISOString(),
  });

  try {
    const upstream = await fetch(url, { headers: { Authorization: 'Bearer ' + token } });
    const body = await upstream.json().catch(() => null);
    if (!upstream.ok || !body || !Array.isArray(body.collection)) {
      console.error('Calendly available times failed:', upstream.status, JSON.stringify(body));
      return res.status(502).json({ ok: false, error: 'Could not load available times' });
    }
    const slots = body.collection
      .filter((s) => s && s.status === 'available' && s.start_time)
      .map((s) => s.start_time)
      .sort();
    // Short cache: protects the Calendly rate limit. A stale slot is caught when booking.
    res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=30');
    return res.status(200).json({ ok: true, slots });
  } catch (error) {
    console.error('slots proxy error:', error);
    return res.status(502).json({ ok: false, error: 'Could not reach the booking service' });
  }
}
