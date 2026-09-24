/**
 * TomoClub Parents page: form handler
 * Saves every submission to Google Sheets and posts it to a Slack channel.
 *
 * SETUP (about 10 minutes)
 * 1. Create a Google Sheet. Copy its ID from the URL (the long string between /d/ and /edit).
 * 2. In Slack: create an Incoming Webhook for your channel (api.slack.com/apps > Create App >
 *    Incoming Webhooks > Add New Webhook to Workspace). Copy the webhook URL.
 * 3. In the Sheet: Extensions > Apps Script. Paste this whole file. Fill in the two values below.
 * 4. Deploy > New deployment > type "Web app". Execute as: Me. Who has access: Anyone.
 * 5. Copy the Web app URL and paste it into FORM_ENDPOINT near the bottom of tomoclub-parents.html.
 *
 * detected_country is where the visitor's browser says they are (this sets the price they saw);
 * country is what they picked in the form. If the two differ, take a look before billing.
 * Country is saved as a 2-letter code (IN = India, US = United States, ES = Spain, MX = Mexico, and so on).
 * Two tabs are created automatically: "Enroll" (Reserve a seat form) and "Talk" (Talk to a team member form).
 */

const SHEET_ID = 'PASTE_GOOGLE_SHEET_ID_HERE';
const SLACK_WEBHOOK_URL = 'PASTE_SLACK_WEBHOOK_URL_HERE';

const COLUMNS = {
  enroll: ['submitted_at', 'parent_name', 'email', 'whatsapp', 'country', 'child_grade', 'program', 'language', 'currency', 'detected_country', 'consent', 'page'],
  talk:   ['submitted_at', 'name', 'email', 'whatsapp', 'role', 'message', 'language', 'currency', 'detected_country', 'consent', 'page']
};

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const type = data.form === 'talk' ? 'talk' : 'enroll';
    saveToSheet_(type, data);
    notifySlack_(type, data);
    return ContentService.createTextOutput(JSON.stringify({ ok: true })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: String(err) })).setMimeType(ContentService.MimeType.JSON);
  }
}

function saveToSheet_(type, data) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const tabName = type === 'talk' ? 'Talk' : 'Enroll';
  let sheet = ss.getSheetByName(tabName);
  if (!sheet) {
    sheet = ss.insertSheet(tabName);
    sheet.appendRow(COLUMNS[type]);
    sheet.setFrozenRows(1);
  }
  sheet.appendRow(COLUMNS[type].map(k => data[k] || ''));
}

function notifySlack_(type, data) {
  if (!SLACK_WEBHOOK_URL || SLACK_WEBHOOK_URL.indexOf('http') !== 0) return;
  const text = type === 'talk'
    ? `:telephone_receiver: *New call request* (${data.role || 'n/a'})\n` +
      `*Name:* ${data.name}\n*Email:* ${data.email}\n*WhatsApp:* ${data.whatsapp}\n` +
      `*Message:* ${data.message || '-'}\n*Language / currency:* ${data.language || '-'} / ${data.currency || '-'}`
    : `:tada: *New free session sign-up*\n` +
      `*Parent:* ${data.parent_name}\n*Email:* ${data.email}\n*WhatsApp:* ${data.whatsapp}\n` +
      `*Country:* ${data.country}\n*Grade:* ${data.child_grade}\n*Program:* ${data.program}\n*Language / currency:* ${data.language || '-'} / ${data.currency || '-'}`;
  UrlFetchApp.fetch(SLACK_WEBHOOK_URL, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ text: text }),
    muteHttpExceptions: true
  });
}
