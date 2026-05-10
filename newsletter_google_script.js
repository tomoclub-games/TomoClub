/**
 * Google Apps Script for Newsletter Signups
 * 1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1bv-G_5yOnN8OZ4EnDOA3Vgr99mTtDQix5W1FlqUn5bc/edit
 * 2. Go to Extensions > Apps Script.
 * 3. Replace the existing code with this code.
 * 4. Click 'Deploy' > 'New Deployment'.
 * 5. Choose 'Web App'.
 * 6. Set 'Who has access' to 'Anyone'.
 * 7. Click 'Deploy' and copy the 'Web App URL'.
 */

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = e.parameter;
  
  // If the request is JSON
  if (e.postData && e.postData.contents) {
    data = JSON.parse(e.postData.contents);
  }
  
  var row = [
    new Date(),
    data.firstName || data.FIRSTNAME || data.name || "",
    data.email || data.EMAIL || "",
    data.source || "Newsletter Signup",
    data.role || data.JOB_TITLE || ""
  ];
  
  sheet.appendRow(row);
  
  return ContentService.createTextOutput(JSON.stringify({"success": true}))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  return ContentService.createTextOutput("Webhook is running.");
}
