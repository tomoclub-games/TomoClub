/**
 * TomoClub website: form data collector (one script, one sheet for all the site's forms).
 * Receives form submissions from the website and appends them to this spreadsheet, one tab per type:
 *   Parents site: Leads, Trial bookings, Enrolments (and Events, only if click logging is switched on)
 *   Leaders of Tomorrow and toolkits: E-book requests, Toolkit downloads
 * The Build With Us project form has its own separate script and is not part of this.
 * Tabs and their header rows are created automatically the first time a row arrives.
 * Also: "Failed bookings" (a trial booking that did not go through).
 *
 * Slack alerts (confirmed trial booking, paid enrolment, failed booking): add a script property named
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

function doPost(e) {
  var lock = LockService.getScriptLock();
  var result, saved = [];
  try {
    lock.waitLock(20000);
    var body = JSON.parse(e.postData.contents || '{}');
    var rows = body.rows || [];
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var grouped = {};
    var valid = [];
    rows.forEach(function (r) {
      if (!r || !HEADERS[r.sheet]) return;
      (grouped[r.sheet] = grouped[r.sheet] || []).push(r.data || {});
      valid.push(r);
    });
    Object.keys(grouped).forEach(function (name) {
      var sheet = getSheet_(ss, name);
      var keys = HEADERS[name].map(function (h) { return h[0]; });
      var values = grouped[name].map(function (d) {
        return keys.map(function (k) { var v = d[k]; return v === undefined || v === null ? '' : (typeof v === 'object' ? JSON.stringify(v) : v); });
      });
      var range = sheet.getRange(sheet.getLastRow() + 1, 1, values.length, keys.length);
      range.setNumberFormat('@'); // plain text: keeps "+91..." phone numbers intact and stops "=..." being run as a formula
      range.setValues(values);
    });
    saved = valid; // only alert for rows that really were saved
    result = { ok: true, saved: rows.length };
  } catch (err) {
    result = { ok: false, error: String(err) };
  } finally {
    lock.releaseLock();
  }
  // Slack alerts go out after the rows are saved and the lock is released. A Slack problem never affects the save.
  saved.forEach(function (r) { notifySlack_(r.sheet, r.data || {}); });
  return json_(result);
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
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS[name].map(function (h) { return h[1]; }));
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, HEADERS[name].length).setFontWeight('bold');
  }
  return sheet;
}

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
