// Vercel serverless function: POST /api/partial
// Saves the contact details from a form the visitor has NOT sent yet, but only when they ticked
// "Save my details if I don't finish" (consent = yes). The page sends it when they leave or hide the page,
// and again when they untick the box (withdraw = true), which erases what was saved.
//
// Only contact fields are kept: name, email, school or district, phone, role. Never the free-text message.
// Rows go to the "Partial leads" tab; Code.gs alerts the team once, about 20 minutes after the last change,
// and only if the same person has not finished a form in the meantime.
// Needs SHEET_WEBHOOK and SHEET_SECRET (see api/_lead-core.js).

import {
  originAllowed, clientIp, tooMany, clean, isEmail, isPhone, attribution, callSheet, readBody, yes, cleanId,
  pushToInstantly, splitName,
} from './_lead-core.js';

const FORMS = /^[a-z0-9_]{2,40}$/;
export const CONSENT_TEXT = "Save my details if I don't finish, so TomoClub can follow up.";

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false });
  if (!originAllowed(req)) return res.status(403).json({ ok: false });
  if (tooMany(clientIp(req), 40, undefined, 'partial')) return res.status(429).json({ ok: false });

  const b = readBody(req);
  const draftId = cleanId(b.draft_id);
  if (!draftId) return res.status(400).json({ ok: false, error: 'draft_id' });
  if (b.hp_company_website) return res.status(200).json({ ok: true });

  if (yes(b.withdraw)) {
    const r = await callSheet({ action: 'upsert_partial', data: { draft_id: draftId, withdraw: true } });
    return res.status(r ? 200 : 502).json({ ok: !!r });
  }

  // Nothing is stored without the visitor's explicit, separate consent.
  if (!yes(b.consent)) return res.status(400).json({ ok: false, error: 'consent required' });

  const email = clean(b.email, 200).toLowerCase();
  const phone = isPhone(b.phone) ? clean(b.phone, 30) : '';
  if (!isEmail(email) && !phone) return res.status(400).json({ ok: false, error: 'email or phone required' });

  const marketing = yes(b.marketing_consent) && isEmail(email);
  const data = {
    draft_id: draftId,
    form: FORMS.test(String(b.form_name || '')) ? String(b.form_name) : 'unknown',
    page: clean(b.page, 120),
    name: clean(b.name || b.firstName, 120),
    email: isEmail(email) ? email : '',
    organization: clean(b.district || b.organization, 160),
    phone,
    role: clean(b.role, 80),
    consent_text: CONSENT_TEXT,
    marketing_consent: marketing ? 'yes' : 'no',
    visitor_id: cleanId(b.visitor_id),
    ...attribution(b),
  };

  if (marketing) {
    const n = splitName(data.name);
    data.instantly_status = await pushToInstantly('partial_lead', {
      email, first_name: n.first_name, last_name: n.last_name, company_name: data.organization, job_title: data.role, phone,
      custom_variables: { intent: 'partial_lead', form: data.form, source_page: data.page },
    });
  }

  const r = await callSheet({ action: 'upsert_partial', data });
  return res.status(r ? 200 : 502).json({ ok: !!r, status: r && r.status });
}
