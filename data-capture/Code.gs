/**
 * TomoClub website: form data collector (one script, one sheet for all the site's forms).
 * Receives form submissions from the website and appends them to this spreadsheet, one tab per type:
 *   Parents site: Leads, Trial bookings, Enrolments (and Events, only if click logging is switched on)
 *   Leaders of Tomorrow and toolkits: E-book requests, Toolkit downloads
 * The Build With Us project form has its own separate script and is not part of this.
 * Tabs and their header rows are created automatically the first time a row arrives.
 *   B2B site: School leads (api/lead.js: home page form, Build With Us form, Calendly bookings),
 *             Partial leads (api/partial.js: unfinished forms, saved only when the visitor ticks the consent box),
 *             Website events (api/event.js: page views, clicks and form steps; never names or emails),
 *             Lead status (follow-up status set from the /admin dashboard), Notifications (sent alerts, for dedup)
 * Also: "Failed bookings" (a trial booking that did not go through).
 *
 * Slack alerts (new school lead, booked discovery call, confirmed trial booking, paid enrolment, failed booking): add a script property named
 * SLACK_WEBHOOK_URL (Project Settings > Script properties) with the Slack Incoming Webhook URL, then run
 * testSlack once from the editor to authorise and test it. No property, no alerts.
 *
 * Set up (5 minutes):
 * 1. Create a new Google Sheet (or import TomoClub_Parents_Funnel_Data.xlsx into Google Sheets).
 * 2. Extensions > Apps Script. Delete the sample code and paste this whole file. Save.
 * 3. Deploy > New deployment > type "Web app". Execute as: Me. Who has access: Anyone. Deploy and authorise.
 * 4. Copy the Web app URL and add it in Vercel (Settings > Environment Variables, Production and Preview) as SHEET_WEBHOOK, then redeploy.
 *    Editing this script later: Deploy > Manage deployments > Edit > New version (a new deployment would change the URL).
 * The sheet opens in Excel any time: File > Download > Microsoft Excel (.xlsx).
 *
 * Analytics and lead tracking (Nov 2026), extra one-time set up:
 * 5. Script properties (Project Settings > Script properties):
 *      SHEET_SECRET   a long random string; the same value goes in Vercel as SHEET_SECRET. Required for the
 *                     /admin dashboard; once set, every write must carry it too.
 *      NOTIFY_EMAILS  comma-separated addresses that get lead alerts by email (for example avinash@tomoclub.org)
 *      ADMIN_URL      optional, the dashboard address used in alerts (default https://www.tomoclub.org/admin)
 * 6. Select installTriggers and press Run once. It authorises email sending and starts the 10-minute check that
 *    alerts the team about consented partial leads that were not finished.
 * 7. Optional: select testNotifications and press Run to send one test alert to Slack and email.
 */
var HEADERS = {
  "Leads": [
    [
      "timestamp",
      "Timestamp (UTC)"
    ],
    [
      "page",
      "Page"
    ],
    [
      "program",
      "Program"
    ],
    [
      "parent_name",
      "Parent name"
    ],
    [
      "email",
      "Email"
    ],
    [
      "whatsapp",
      "WhatsApp number"
    ],
    [
      "country",
      "Country"
    ],
    [
      "city",
      "City"
    ],
    [
      "grade",
      "Grade"
    ],
    [
      "session_id",
      "Session ID"
    ],
    [
      "visitor_id",
      "Visitor ID"
    ],
    [
      "utm_source",
      "UTM source"
    ],
    [
      "utm_medium",
      "UTM medium"
    ],
    [
      "utm_campaign",
      "UTM campaign"
    ],
    [
      "utm_content",
      "UTM content"
    ],
    [
      "utm_term",
      "UTM term"
    ],
    [
      "gclid",
      "Google click ID"
    ],
    [
      "fbclid",
      "Meta click ID"
    ],
    [
      "referrer",
      "Referrer"
    ],
    [
      "landing_page",
      "Landing page"
    ]
  ],
  "Trial bookings": [
    [
      "timestamp",
      "Timestamp (UTC)"
    ],
    [
      "page",
      "Page"
    ],
    [
      "program",
      "Program"
    ],
    [
      "parent_name",
      "Parent name"
    ],
    [
      "email",
      "Email"
    ],
    [
      "whatsapp",
      "WhatsApp number"
    ],
    [
      "country",
      "Country"
    ],
    [
      "city",
      "City"
    ],
    [
      "grade",
      "Grade"
    ],
    [
      "class_date",
      "Class date"
    ],
    [
      "class_time",
      "Class time"
    ],
    [
      "time_zone",
      "Time zone"
    ],
    [
      "whatsapp_reminders",
      "WhatsApp reminders opt-in"
    ],
    [
      "session_id",
      "Session ID"
    ],
    [
      "visitor_id",
      "Visitor ID"
    ],
    [
      "utm_source",
      "UTM source"
    ],
    [
      "utm_medium",
      "UTM medium"
    ],
    [
      "utm_campaign",
      "UTM campaign"
    ],
    [
      "utm_content",
      "UTM content"
    ],
    [
      "utm_term",
      "UTM term"
    ],
    [
      "gclid",
      "Google click ID"
    ],
    [
      "fbclid",
      "Meta click ID"
    ],
    [
      "referrer",
      "Referrer"
    ],
    [
      "landing_page",
      "Landing page"
    ],
    [
      "class_start_utc",
      "Class start (UTC)"
    ],
    [
      "calendly_booking",
      "Calendly booking"
    ]
  ],
  "Enrolments": [
    [
      "timestamp",
      "Timestamp (UTC)"
    ],
    [
      "status",
      "Status"
    ],
    [
      "parent_name",
      "Parent name"
    ],
    [
      "email",
      "Email"
    ],
    [
      "whatsapp",
      "WhatsApp number"
    ],
    [
      "country",
      "Country"
    ],
    [
      "city",
      "City"
    ],
    [
      "grade",
      "Grade"
    ],
    [
      "life_skills_batch",
      "Life Skills batch"
    ],
    [
      "ai_lab_batch",
      "AI Lab batch"
    ],
    [
      "payment_method",
      "Payment method"
    ],
    [
      "amount_inr",
      "Amount (INR)"
    ],
    [
      "transaction_id",
      "Transaction ID"
    ],
    [
      "whatsapp_reminders",
      "WhatsApp reminders opt-in"
    ],
    [
      "session_id",
      "Session ID"
    ],
    [
      "visitor_id",
      "Visitor ID"
    ],
    [
      "utm_source",
      "UTM source"
    ],
    [
      "utm_medium",
      "UTM medium"
    ],
    [
      "utm_campaign",
      "UTM campaign"
    ],
    [
      "utm_content",
      "UTM content"
    ],
    [
      "utm_term",
      "UTM term"
    ],
    [
      "gclid",
      "Google click ID"
    ],
    [
      "fbclid",
      "Meta click ID"
    ],
    [
      "referrer",
      "Referrer"
    ],
    [
      "landing_page",
      "Landing page"
    ]
  ],
  "Events": [
    [
      "timestamp",
      "Timestamp (UTC)"
    ],
    [
      "event",
      "Event"
    ],
    [
      "page",
      "Page"
    ],
    [
      "cta_location",
      "Location on page"
    ],
    [
      "label",
      "Button / link text"
    ],
    [
      "program",
      "Program"
    ],
    [
      "grade",
      "Grade"
    ],
    [
      "details",
      "Details"
    ],
    [
      "path",
      "URL path"
    ],
    [
      "session_id",
      "Session ID"
    ],
    [
      "visitor_id",
      "Visitor ID"
    ],
    [
      "utm_source",
      "UTM source"
    ],
    [
      "utm_medium",
      "UTM medium"
    ],
    [
      "utm_campaign",
      "UTM campaign"
    ],
    [
      "utm_content",
      "UTM content"
    ],
    [
      "utm_term",
      "UTM term"
    ],
    [
      "gclid",
      "Google click ID"
    ],
    [
      "fbclid",
      "Meta click ID"
    ],
    [
      "referrer",
      "Referrer"
    ],
    [
      "landing_page",
      "Landing page"
    ]
  ],
  "E-book requests": [
    ["timestamp", "Timestamp (UTC)"],
    ["first_name", "First name"],
    ["email", "Email"],
    ["role", "Role"],
    ["source", "Form location"]
  ],
  "Toolkit downloads": [
    ["timestamp", "Timestamp (UTC)"],
    ["first_name", "First name"],
    ["email", "Email"],
    ["toolkit", "Toolkit file"],
    ["source", "Form location"]
  ]
};

// Where each visitor came from, added to the end of the two Leaders of Tomorrow / toolkit tabs.
var ATTRIBUTION_COLUMNS = [
  ["utm_source", "UTM source"],
  ["utm_medium", "UTM medium"],
  ["utm_campaign", "UTM campaign"],
  ["utm_content", "UTM content"],
  ["utm_term", "UTM term"],
  ["gclid", "Google click ID"],
  ["fbclid", "Meta click ID"],
  ["referrer", "Referrer"],
  ["landing_page", "Landing page"]
];
["E-book requests", "Toolkit downloads"].forEach(function (name) {
  HEADERS[name] = HEADERS[name].concat(ATTRIBUTION_COLUMNS);
});

// Added to the end of the three parents tabs: the visitor's country by IP (set by the server, not the browser),
// the page language, and the currency of the price they were shown (blank when no price was shown).
var GEO_COLUMNS = [
  ["detected_country", "Detected country"],
  ["language", "Language"],
  ["currency", "Currency"]
];
["Leads", "Trial bookings", "Enrolments"].forEach(function (name) {
  HEADERS[name] = HEADERS[name].concat(GEO_COLUMNS);
});

// A parent filled in the booking form but the booking did not go through (time just taken, or an error).
HEADERS["Failed bookings"] = [
  ["timestamp", "Timestamp (UTC)"],
  ["page", "Page"],
  ["reason", "Reason"],
  ["program", "Program"],
  ["parent_name", "Parent name"],
  ["email", "Email"],
  ["whatsapp", "WhatsApp number"],
  ["country", "Country"],
  ["city", "City"],
  ["grade", "Grade"],
  ["class_date", "Class date wanted"],
  ["class_time", "Class time wanted"],
  ["time_zone", "Time zone"],
  ["class_start_utc", "Class start wanted (UTC)"],
  ["session_id", "Session ID"],
  ["visitor_id", "Visitor ID"]
].concat(ATTRIBUTION_COLUMNS, GEO_COLUMNS);

// B2B: every lead from api/lead.js (home page form, Calendly bookings).
HEADERS["School leads"] = [
  ["timestamp", "Timestamp (UTC)"],
  ["type", "Type"],
  ["name", "Name"],
  ["email", "Email"],
  ["email_type", "Work or personal email"],
  ["organization", "School or district"],
  ["role", "Role"],
  ["state", "State"],
  ["offer_interest", "Offer interest"],
  ["message", "What they wrote"],
  ["meeting_start", "Meeting start (UTC)"],
  ["page", "Page"]
].concat(ATTRIBUTION_COLUMNS);

// Columns added in Nov 2026 for the analytics and lead-tracking system. New columns always go at the END of a
// tab so rows already in the sheet keep their meaning; getSheet_ adds the missing header cells on first use.
var LEAD_EXTRA_COLUMNS = [
  ["phone", "Phone"],
  ["form", "Form"],
  ["submission_id", "Submission ID"],
  ["draft_id", "Draft ID (links a partial lead)"],
  ["marketing_consent", "Agreed to marketing emails"],
  ["visitor_id", "Visitor ID"],
  ["instantly_status", "Instantly"]
];
HEADERS["School leads"] = HEADERS["School leads"].concat(LEAD_EXTRA_COLUMNS);
["E-book requests", "Toolkit downloads"].forEach(function (name) {
  HEADERS[name] = HEADERS[name].concat(LEAD_EXTRA_COLUMNS.filter(function (c) { return c[0] !== 'phone' && c[0] !== 'form'; }));
});

// A visitor typed contact details into a form, ticked "save my details", and left without sending it.
HEADERS["Partial leads"] = [
  ["draft_id", "Draft ID"],
  ["first_seen", "First saved (UTC)"],
  ["last_updated", "Last updated (UTC)"],
  ["form", "Form"],
  ["page", "Page"],
  ["name", "Name"],
  ["email", "Email"],
  ["organization", "School or district"],
  ["phone", "Phone"],
  ["role", "Role"],
  ["consent_text", "Consent shown"],
  ["marketing_consent", "Agreed to marketing emails"],
  ["status", "Status (partial / converted / withdrawn)"],
  ["converted_at", "Converted (UTC)"],
  ["notified_at", "Team notified (UTC)"],
  ["visitor_id", "Visitor ID"],
  ["instantly_status", "Instantly"]
].concat(ATTRIBUTION_COLUMNS);

// Site interactions. No names, emails or phone numbers are ever written here.
HEADERS["Website events"] = [
  ["timestamp", "Timestamp (UTC)"],
  ["visitor_id", "Visitor ID"],
  ["session_id", "Session ID"],
  ["event", "Event"],
  ["label", "Detail"],
  ["form", "Form"],
  ["page", "Page"],
  ["source", "Source"],
  ["medium", "Medium"],
  ["campaign", "Campaign"],
  ["device", "Device"],
  ["country", "Country"]
];

// Follow-up status set from the dashboard. One row per lead; the newest row for a lead wins.
HEADERS["Lead status"] = [
  ["lead_id", "Lead ID"],
  ["status", "Status"],
  ["note", "Note"],
  ["updated_at", "Updated (UTC)"],
  ["updated_by", "Updated by"]
];

// Every alert sent, so the same lead never triggers two alerts.
HEADERS["Notifications"] = [
  ["key", "Key"],
  ["sent_at", "Sent (UTC)"],
  ["kind", "Kind"],
  ["channels", "Channels"]
];

function doPost(e) {
  var lock = LockService.getScriptLock();
  var result, saved = [], ss;
  try {
    lock.waitLock(20000);
    var body = JSON.parse(e.postData.contents || '{}');
    var secret = prop_('SHEET_SECRET');
    if (body.action) {
      // Dashboard and partial-lead actions always need the shared secret.
      if (!secret || !sameText_(String(body.secret || ''), secret)) throw new Error('not allowed');
    } else if (secret && !sameText_(String(body.secret || ''), secret)) {
      throw new Error('not allowed');
    }
    ss = spreadsheet_();
    if (body.action) {
      result = handleAction_(ss, body);
    } else {
      var rows = body.rows || [];
      var grouped = {};
      var valid = [];
      var seenIds = {};
      rows.forEach(function (r) {
        if (!r || !HEADERS[r.sheet]) return;
        var d = r.data || {};
        // A retried submission (same submission ID) is saved and alerted only once.
        if (LEAD_TABS[r.sheet] && d.submission_id) {
          if (!seenIds[r.sheet]) {
            seenIds[r.sheet] = {};
            readObjects_(ss, r.sheet).forEach(function (o) { if (o.submission_id) seenIds[r.sheet][o.submission_id] = true; });
          }
          if (seenIds[r.sheet][d.submission_id]) return;
          seenIds[r.sheet][d.submission_id] = true;
        }
        (grouped[r.sheet] = grouped[r.sheet] || []).push(d);
        valid.push(r);
      });
      Object.keys(grouped).forEach(function (name) { appendRows_(ss, name, grouped[name]); });
      // A finished form closes any partial lead from the same draft or the same email.
      valid.forEach(function (r) { if (LEAD_TABS[r.sheet]) markConverted_(ss, r.data || {}); });
      saved = valid; // only alert for rows that really were saved
      result = { ok: true, saved: valid.length };
    }
  } catch (err) {
    result = { ok: false, error: String(err && err.message || err) };
  } finally {
    lock.releaseLock();
  }
  // Alerts go out after the rows are saved and the lock is released. An alert problem never affects the save.
  saved.forEach(function (r) {
    if (LEAD_TABS[r.sheet]) notifyLead_(ss, r.sheet, r.data || {});
    else notifySlack_(r.sheet, r.data || {});
  });
  return json_(result);
}

// Tabs whose rows are finished leads (shown in the dashboard, alerted once each).
var LEAD_TABS = { 'School leads': true, 'E-book requests': true, 'Toolkit downloads': true };

function prop_(name) { return PropertiesService.getScriptProperties().getProperty(name) || ''; }

function sameText_(a, b) {
  if (a.length !== b.length) return false;
  var diff = 0;
  for (var i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function spreadsheet_() {
  // A script created from the Sheet (Extensions > Apps Script) is bound to it. A standalone script
  // (created at script.google.com) is not, so it opens the Sheet by the SHEET_ID Script Property.
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    var sheetId = prop_('SHEET_ID');
    if (!sheetId) throw new Error('Not bound to a Sheet: set the SHEET_ID Script Property');
    ss = SpreadsheetApp.openById(sheetId);
  }
  return ss;
}

function cellValue_(v) {
  if (v === undefined || v === null) return '';
  if (typeof v === 'object') return JSON.stringify(v);
  return v;
}

function appendRows_(ss, name, list) {
  var sheet = getSheet_(ss, name);
  var keys = HEADERS[name].map(function (h) { return h[0]; });
  var values = list.map(function (d) { return keys.map(function (k) { return cellValue_(d[k]); }); });
  var range = sheet.getRange(sheet.getLastRow() + 1, 1, values.length, keys.length);
  range.setNumberFormat('@'); // plain text: keeps "+1..." phone numbers intact and stops "=..." being run as a formula
  range.setValues(values);
}

// All data rows of a tab as objects keyed by the HEADERS keys (column order = HEADERS order).
function readObjects_(ss, name) {
  var sheet = ss.getSheetByName(name);
  if (!sheet || sheet.getLastRow() < 2) return [];
  var keys = HEADERS[name].map(function (h) { return h[0]; });
  var width = Math.min(keys.length, sheet.getLastColumn());
  var values = sheet.getRange(2, 1, sheet.getLastRow() - 1, width).getValues();
  return values.map(function (row, i) {
    var o = { _row: i + 2 };
    for (var c = 0; c < width; c++) o[keys[c]] = row[c] instanceof Date ? row[c].toISOString() : row[c];
    return o;
  });
}

function setCells_(ss, name, rowNumber, data) {
  var sheet = getSheet_(ss, name);
  var keys = HEADERS[name].map(function (h) { return h[0]; });
  Object.keys(data).forEach(function (k) {
    var c = keys.indexOf(k);
    if (c < 0) return;
    var cell = sheet.getRange(rowNumber, c + 1);
    cell.setNumberFormat('@');
    cell.setValue(cellValue_(data[k]));
  });
}

function handleAction_(ss, body) {
  if (body.action === 'upsert_partial') return upsertPartial_(ss, body.data || {});
  if (body.action === 'set_status') return setStatus_(ss, body.data || {});
  if (body.action === 'read') {
    var since = String(body.since || '');
    var out = {};
    (body.tabs || []).forEach(function (name) {
      if (!HEADERS[name]) return;
      var timeKey = name === 'Partial leads' ? 'last_updated' : (name === 'Lead status' ? 'updated_at' : (name === 'Notifications' ? 'sent_at' : 'timestamp'));
      var rows = readObjects_(ss, name).filter(function (o) { return !since || String(o[timeKey] || '') >= since; });
      out[name] = rows;
    });
    return { ok: true, tabs: out };
  }
  throw new Error('unknown action');
}

function upsertPartial_(ss, d) {
  var id = String(d.draft_id || '');
  if (!/^[A-Za-z0-9_-]{8,64}$/.test(id)) throw new Error('bad draft id');
  var now = new Date().toISOString();
  var rows = readObjects_(ss, 'Partial leads');
  var found = null;
  for (var i = rows.length - 1; i >= 0; i--) { if (rows[i].draft_id === id) { found = rows[i]; break; } }
  if (d.withdraw) {
    // The visitor unticked the box: keep the row for the audit trail but erase what they typed.
    if (found) setCells_(ss, 'Partial leads', found._row, { name: '', email: '', organization: '', phone: '', role: '', status: 'withdrawn', last_updated: now });
    return { ok: true, status: 'withdrawn' };
  }
  if (found && found.status === 'converted') return { ok: true, status: 'converted' };
  var fields = ['form', 'page', 'name', 'email', 'organization', 'phone', 'role', 'consent_text', 'marketing_consent', 'visitor_id', 'instantly_status']
    .concat(ATTRIBUTION_COLUMNS.map(function (c) { return c[0]; }));
  if (found) {
    var upd = { last_updated: now, status: 'partial' };
    fields.forEach(function (k) { if (d[k] !== undefined && d[k] !== '') upd[k] = d[k]; });
    setCells_(ss, 'Partial leads', found._row, upd);
    return { ok: true, status: 'updated' };
  }
  var row = { draft_id: id, first_seen: now, last_updated: now, status: 'partial' };
  fields.forEach(function (k) { if (d[k] !== undefined) row[k] = d[k]; });
  appendRows_(ss, 'Partial leads', [row]);
  return { ok: true, status: 'created' };
}

function markConverted_(ss, d) {
  var id = String(d.draft_id || ''), email = String(d.email || '').toLowerCase();
  if (!id && !email) return;
  var now = new Date().toISOString();
  readObjects_(ss, 'Partial leads').forEach(function (p) {
    if (p.status !== 'partial') return;
    if ((id && p.draft_id === id) || (email && String(p.email || '').toLowerCase() === email)) {
      setCells_(ss, 'Partial leads', p._row, { status: 'converted', converted_at: now });
    }
  });
}

var STATUSES = ['New', 'Contacted', 'Meeting booked', 'Qualified', 'Not a fit', 'Closed'];

function setStatus_(ss, d) {
  var id = String(d.lead_id || '');
  if (!/^[A-Za-z0-9:_-]{4,120}$/.test(id)) throw new Error('bad lead id');
  if (STATUSES.indexOf(d.status) < 0) throw new Error('bad status');
  var row = { lead_id: id, status: d.status, note: String(d.note || '').slice(0, 500), updated_at: new Date().toISOString(), updated_by: String(d.by || '').slice(0, 60) };
  appendRows_(ss, 'Lead status', [row]);
  return { ok: true, saved: row };
}

// ---------- Slack alerts ----------
// The webhook URL is kept in Script Properties (Project Settings > Script properties > SLACK_WEBHOOK_URL),
// never in this file. With no property set, nothing is sent. Alerts: confirmed trial booking, paid enrolment,
// failed booking attempt. Other tabs are saved but not announced.
function notifySlack_(sheetName, d) {
  try {
    var url = PropertiesService.getScriptProperties().getProperty('SLACK_WEBHOOK_URL');
    if (!url || url.indexOf('https://') !== 0) return;
    var text = slackText_(sheetName, d);
    if (!text) return;
    UrlFetchApp.fetch(url, { method: 'post', contentType: 'application/json', payload: JSON.stringify({ text: text }), muteHttpExceptions: true });
  } catch (err) {
    console.error('Slack alert failed: ' + err);
  }
}

function slackText_(sheetName, d) {
  // Slack treats & < > as markup; escaping them stops a typed "<!channel>" from pinging everyone.
  var e = function (v) { return String(v === undefined || v === null || v === '' ? '-' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); };
  var programs = { life_skills: 'Tomo Life Skills', ai_lab: 'Tomo AI Lab', bundle: 'Life Skills + AI Lab' };
  var person = '*Parent:* ' + e(d.parent_name) + '\n*Email:* ' + e(d.email) + '\n*WhatsApp:* ' + e(d.whatsapp) + '\n' +
    '*Country:* ' + e(d.country) + (d.detected_country ? ' (detected ' + e(d.detected_country) + ')' : '') + '\n*City:* ' + e(d.city) + '\n' +
    '*Grade:* ' + e(d.grade) + '\n*Program:* ' + e(programs[d.program] || d.program);
  var lang = '\n*Language / currency:* ' + e(d.language) + ' / ' + e(d.currency);

  if (sheetName === 'School leads') {
    var kind = { discovery_request: 'New school lead', build_with_us: 'New Build With Us request', call_booked: 'Discovery call booked' }[d.type] || 'School lead';
    return ':school: *' + kind + '*\n*Name:* ' + e(d.name) + '\n*Email:* ' + e(d.email) + ' (' + e(d.email_type) + ')\n' +
      (d.phone ? '*Phone:* ' + e(d.phone) + '\n' : '') +
      '*School or district:* ' + e(d.organization) + '\n*Role:* ' + e(d.role) + '\n*State:* ' + e(d.state) + '\n' +
      (d.meeting_start ? '*Meeting:* ' + e(d.meeting_start) + ' UTC\n' : '') +
      '*Interest:* ' + e(d.offer_interest) + '\n*In their words:* ' + e(d.message) + '\n*Page:* ' + e(d.page) +
      ' | *Source:* ' + e(d.utm_source || d.referrer) + '\n*Marketing emails:* ' + (d.marketing_consent === 'yes' ? 'agreed' : 'not agreed');
  }
  if (sheetName === 'E-book requests' || sheetName === 'Toolkit downloads') {
    return ':page_facing_up: *' + (sheetName === 'E-book requests' ? 'Leaders of Tomorrow ebook download' : 'Guide download') + '*\n' +
      '*Name:* ' + e(d.first_name) + '\n*Email:* ' + e(d.email) + '\n' + (d.role ? '*Role:* ' + e(d.role) + '\n' : '') +
      (d.toolkit ? '*File:* ' + e(d.toolkit) + '\n' : '') + '*Page:* ' + e(d.source) + ' | *Source:* ' + e(d.utm_source || d.referrer) +
      '\n*Marketing emails:* ' + (d.marketing_consent === 'yes' ? 'agreed' : 'not agreed');
  }
  if (sheetName === 'Partial leads') {
    return ':hourglass: *Unfinished form, contact saved with consent*\n*Name:* ' + e(d.name) + '\n*Email:* ' + e(d.email) + '\n' +
      '*Phone:* ' + e(d.phone) + '\n*School or district:* ' + e(d.organization) + '\n*Form:* ' + e(d.form) + ' on ' + e(d.page) +
      '\n*First saved:* ' + e(d.first_seen) + ' UTC | *Source:* ' + e(d.utm_source || d.referrer);
  }
  if (sheetName === 'Trial bookings') {
    return ':tada: *New free trial class booked*\n' + person + '\n' +
      '*Class:* ' + e(d.class_date) + ', ' + e(d.class_time) + ' (' + e(d.time_zone) + ')\n*Starts (UTC):* ' + e(d.class_start_utc) + lang;
  }
  if (sheetName === 'Enrolments' && d.status === 'paid') {
    return ':white_check_mark: *New enrolment*\n*Parent:* ' + e(d.parent_name) + '\n*Email:* ' + e(d.email) + '\n*WhatsApp:* ' + e(d.whatsapp) + '\n' +
      '*Country:* ' + e(d.country) + (d.detected_country ? ' (detected ' + e(d.detected_country) + ')' : '') + '\n*City:* ' + e(d.city) + '\n*Grade:* ' + e(d.grade) + '\n' +
      '*Batches:* Life Skills ' + e(d.life_skills_batch) + ' / AI Lab ' + e(d.ai_lab_batch) + '\n*Payment:* ' + e(d.payment_method) + ', INR ' + e(d.amount_inr) +
      ', transaction ' + e(d.transaction_id) + lang;
  }
  if (sheetName === 'Failed bookings') {
    var why = d.reason === 'slot_taken' ? 'that time was just taken' : 'a booking error';
    return ':warning: *Trial booking did not go through* (' + why + ')\n' + person + '\n' +
      '*Wanted:* ' + e(d.class_date) + ', ' + e(d.class_time) + ' (' + e(d.time_zone) + ')' + lang + '\n_Follow up with this parent._';
  }
  return '';
}

// Run once from the editor after adding the SLACK_WEBHOOK_URL script property (select testSlack, then Run).
// The first run asks you to authorise the script to connect to an external service; it then posts a test message.
function testSlack() {
  var url = PropertiesService.getScriptProperties().getProperty('SLACK_WEBHOOK_URL');
  if (!url) throw new Error('Add the SLACK_WEBHOOK_URL script property first (Project Settings > Script properties).');
  UrlFetchApp.fetch(url, { method: 'post', contentType: 'application/json', payload: JSON.stringify({ text: ':white_check_mark: The TomoClub form collector is connected to Slack.' }) });
}

function doGet() { return json_({ ok: true, message: 'TomoClub collector is running' }); }

function getSheet_(ss, name) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  var labels = HEADERS[name].map(function (h) { return h[1]; });
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(labels);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, labels.length).setFontWeight('bold');
  } else if (sheet.getLastColumn() < labels.length) {
    // Columns added to HEADERS after this tab was created: write their header cells at the end.
    var from = sheet.getLastColumn() + 1;
    sheet.getRange(1, from, 1, labels.length - from + 1).setValues([labels.slice(from - 1)]).setFontWeight('bold');
  }
  return sheet;
}

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

// ---------- Lead alerts (Slack + email), never twice for the same lead ----------
// Keys: a finished form uses its submission ID (or tab + email + day); a partial lead uses its email for 7 days.
function alreadySent_(ss, key) {
  var cache = CacheService.getScriptCache();
  if (cache.get('n:' + key)) return true;
  var found = readObjects_(ss, 'Notifications').some(function (n) { return n.key === key; });
  if (found) cache.put('n:' + key, '1', 21600);
  return found;
}

function recordSent_(ss, key, kind, channels) {
  appendRows_(ss, 'Notifications', [{ key: key, sent_at: new Date().toISOString(), kind: kind, channels: channels.join(',') }]);
  CacheService.getScriptCache().put('n:' + key, '1', 21600);
}

function leadKey_(sheetName, d) {
  if (d.submission_id) return 'done:' + d.submission_id;
  return 'done:' + sheetName + ':' + String(d.email || '').toLowerCase() + ':' + String(d.timestamp || new Date().toISOString()).slice(0, 10);
}

function notifyLead_(ss, sheetName, d) {
  try {
    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    var key = leadKey_(sheetName, d);
    try {
      if (alreadySent_(ss, key)) return;
      var channels = sendAlert_(sheetName, d);
      recordSent_(ss, key, sheetName + (d.type ? ':' + d.type : ''), channels);
    } finally { lock.releaseLock(); }
  } catch (err) {
    console.error('Lead alert failed: ' + err);
  }
}

// Sends one alert to Slack (if SLACK_WEBHOOK_URL is set) and email (if NOTIFY_EMAILS is set). Returns the channels used.
function sendAlert_(sheetName, d) {
  var channels = [];
  var text = slackText_(sheetName, d);
  if (!text) return channels;
  var url = prop_('SLACK_WEBHOOK_URL');
  if (url && url.indexOf('https://') === 0) {
    var r = UrlFetchApp.fetch(url, { method: 'post', contentType: 'application/json', payload: JSON.stringify({ text: text }), muteHttpExceptions: true });
    if (r.getResponseCode() < 300) channels.push('slack');
  }
  var to = prop_('NOTIFY_EMAILS');
  if (to) {
    var admin = prop_('ADMIN_URL') || 'https://www.tomoclub.org/admin';
    var plain = text.replace(/\*/g, '').replace(/:[a-z_]+: /g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    var subject = 'TomoClub: ' + plain.split('\n')[0] + (d.organization ? ' (' + d.organization + ')' : '') + (d.email ? ' - ' + d.email : '');
    MailApp.sendEmail({ to: to, subject: subject.slice(0, 180), body: plain + '\n\nOpen the dashboard: ' + admin + '\n' });
    channels.push('email');
  }
  return channels;
}

// Runs every 10 minutes (installTriggers). Alerts the team about partial leads that were saved with consent,
// have not changed for PARTIAL_WAIT_MINUTES (default 20) and were not finished since.
function processPartialLeads() {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  var toSend = [];
  var ss;
  try {
    ss = spreadsheet_();
    var wait = Number(prop_('PARTIAL_WAIT_MINUTES') || 20) * 60000;
    var now = Date.now();
    var done = {};
    Object.keys(LEAD_TABS).forEach(function (t) {
      readObjects_(ss, t).forEach(function (r) { if (r.email) done[String(r.email).toLowerCase()] = String(r.timestamp || ''); });
    });
    readObjects_(ss, 'Partial leads').forEach(function (p) {
      if (p.status !== 'partial' || p.notified_at || !p.email) return;
      if (now - new Date(p.last_updated).getTime() < wait) return;
      var email = String(p.email).toLowerCase();
      if (done[email] && done[email] >= String(p.first_seen)) {
        setCells_(ss, 'Partial leads', p._row, { status: 'converted', converted_at: done[email] });
        return;
      }
      toSend.push(p);
    });
    toSend.forEach(function (p) {
      var key = 'partial:' + String(p.email).toLowerCase() + ':' + String(p.first_seen).slice(0, 10);
      var stamp = new Date().toISOString();
      if (!alreadySent_(ss, key)) {
        var channels = sendAlert_('Partial leads', p);
        recordSent_(ss, key, 'Partial leads', channels);
      }
      setCells_(ss, 'Partial leads', p._row, { notified_at: stamp });
    });
  } finally {
    lock.releaseLock();
  }
  return toSend.length;
}

// Run once from the editor (select installTriggers, then Run). Safe to run again: it replaces its own trigger.
function installTriggers() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'processPartialLeads') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('processPartialLeads').timeBased().everyMinutes(10).create();
  return 'Partial lead check runs every 10 minutes';
}

// Run once to check that alerts reach Slack and email.
function testNotifications() {
  return sendAlert_('School leads', {
    type: 'discovery_request', name: 'Test Lead', email: 'test@example.org', email_type: 'work',
    organization: 'Test School District', role: 'Superintendent', state: 'OH', offer_interest: 'Build With Us',
    message: 'This is a test alert from the TomoClub lead system.', page: '/', marketing_consent: 'no'
  });
}
