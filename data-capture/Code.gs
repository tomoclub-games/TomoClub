/**
 * TomoClub parents site: data collector.
 * Receives form submissions and click events from the website and appends them to this spreadsheet,
 * one tab per type: Leads, Trial bookings, Enrolments, Newsletter, Events.
 *
 * Set up (5 minutes):
 * 1. Create a new Google Sheet (or import TomoClub_Parents_Funnel_Data.xlsx into Google Sheets).
 * 2. Extensions > Apps Script. Delete the sample code and paste this whole file. Save.
 * 3. Deploy > New deployment > type "Web app". Execute as: Me. Who has access: Anyone. Deploy and authorise.
 * 4. Copy the Web app URL and paste it into assets/js/parents-site.js (the TOMO_CONFIG block at the top) as sheetEndpoint.
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
  "Newsletter": [
    [
      "timestamp",
      "Timestamp (UTC)"
    ],
    [
      "page",
      "Page"
    ],
    [
      "email",
      "Email"
    ],
    [
      "email_consent",
      "Email consent"
    ],
    [
      "whatsapp",
      "WhatsApp number"
    ],
    [
      "whatsapp_consent",
      "WhatsApp consent"
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
  ]
};

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var body = JSON.parse(e.postData.contents || '{}');
    var rows = body.rows || [];
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var grouped = {};
    rows.forEach(function (r) {
      if (!r || !HEADERS[r.sheet]) return;
      (grouped[r.sheet] = grouped[r.sheet] || []).push(r.data || {});
    });
    Object.keys(grouped).forEach(function (name) {
      var sheet = getSheet_(ss, name);
      var keys = HEADERS[name].map(function (h) { return h[0]; });
      var values = grouped[name].map(function (d) {
        return keys.map(function (k) { var v = d[k]; return v === undefined || v === null ? '' : (typeof v === 'object' ? JSON.stringify(v) : v); });
      });
      sheet.getRange(sheet.getLastRow() + 1, 1, values.length, keys.length).setValues(values);
    });
    return json_({ ok: true, saved: rows.length });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
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
