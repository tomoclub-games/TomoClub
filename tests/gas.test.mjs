// Tests for data-capture/Code.gs. Run: node tests/gas.test.mjs
import fs from 'node:fs'; globalThis.__fs = fs;
import assert from 'node:assert/strict';
import { loadCodeGs } from './gas-mock.mjs';

const FILE = new URL('../data-capture/Code.gs', import.meta.url).pathname;
let n = 0;
const t = (name, fn) => { fn(); n++; console.log('ok', n, name); };

t('rows need the secret once SHEET_SECRET is set', () => {
  const g = loadCodeGs(FILE, { SHEET_SECRET: 's3' });
  assert.equal(g.post({ rows: [{ sheet: 'School leads', data: { email: 'a@b.org' } }] }).ok, false);
  assert.equal(g.post({ secret: 's3', rows: [{ sheet: 'School leads', data: { email: 'a@b.org' } }] }).ok, true);
});

t('actions are refused when no secret is configured', () => {
  const g = loadCodeGs(FILE, {});
  assert.equal(g.post({ action: 'read', tabs: ['School leads'] }).ok, false);
});

t('old rows keep working without a secret (backward compatible writes)', () => {
  const g = loadCodeGs(FILE, {});
  assert.equal(g.post({ rows: [{ sheet: 'Toolkit downloads', data: { email: 'x@y.org' } }] }).ok, true);
});

t('existing tab gets the new header cells added at the end', () => {
  const g = loadCodeGs(FILE, { SHEET_SECRET: 's' });
  const old = g.ctx.HEADERS['School leads'].slice(0, 21).map((h) => h[1]);
  const sh = g.sheets.get('School leads') || g.ctx.SpreadsheetApp.getActiveSpreadsheet().insertSheet('School leads');
  sh.appendRow(old); sh.appendRow(old.map((_, i) => 'old' + i));
  g.post({ secret: 's', rows: [{ sheet: 'School leads', data: { email: 'n@b.org', phone: '+1 555', submission_id: 'S1' } }] });
  const rows = g.tab('School leads');
  assert.equal(rows[0].length, g.ctx.HEADERS['School leads'].length);
  assert.equal(rows[0].at(-1), 'Instantly');
  assert.equal(rows[1][0], 'old0'); // existing row untouched
  const keys = g.ctx.HEADERS['School leads'].map((h) => h[0]);
  assert.equal(rows[2][keys.indexOf('phone')], '+1 555');
});

t('completed lead alerts once to Slack and email; retry with same submission id is not saved twice', () => {
  const g = loadCodeGs(FILE, { SHEET_SECRET: 's', SLACK_WEBHOOK_URL: 'https://hooks.slack.test/x', NOTIFY_EMAILS: 'team@tomoclub.org' });
  const row = { sheet: 'School leads', data: { timestamp: '2026-11-23T10:00:00Z', type: 'discovery_request', name: 'Jane Doe', email: 'jane@d.org', organization: 'Testville USD', submission_id: 'sub-1' } };
  g.post({ secret: 's', rows: [row] });
  g.post({ secret: 's', rows: [row] });
  assert.equal(g.tab('School leads').length, 2); // header + 1
  assert.equal(g.sent.slack.length, 1);
  assert.equal(g.sent.mail.length, 1);
  assert.match(g.sent.mail[0].subject, /Testville USD/);
  assert.equal(g.tab('Notifications').length, 2);
});

t('partial lead: create, update, withdraw erases details', () => {
  const g = loadCodeGs(FILE, { SHEET_SECRET: 's' });
  let r = g.post({ secret: 's', action: 'upsert_partial', data: { draft_id: 'draft12345', email: 'p@d.org', name: 'Pat', form: 'home' } });
  assert.equal(r.status, 'created');
  r = g.post({ secret: 's', action: 'upsert_partial', data: { draft_id: 'draft12345', organization: 'Org', phone: '555' } });
  assert.equal(r.status, 'updated');
  const keys = g.ctx.HEADERS['Partial leads'].map((h) => h[0]);
  let row = g.tab('Partial leads')[1];
  assert.equal(row[keys.indexOf('email')], 'p@d.org');
  assert.equal(row[keys.indexOf('organization')], 'Org');
  g.post({ secret: 's', action: 'upsert_partial', data: { draft_id: 'draft12345', withdraw: true } });
  row = g.tab('Partial leads')[1];
  assert.equal(row[keys.indexOf('email')], '');
  assert.equal(row[keys.indexOf('status')], 'withdrawn');
});

t('finishing the form converts the partial lead, and the 10-minute check never alerts it', () => {
  const g = loadCodeGs(FILE, { SHEET_SECRET: 's', NOTIFY_EMAILS: 'team@tomoclub.org', PARTIAL_WAIT_MINUTES: '0' });
  g.post({ secret: 's', action: 'upsert_partial', data: { draft_id: 'draftAAAA1', email: 'q@d.org', name: 'Q' } });
  g.post({ secret: 's', rows: [{ sheet: 'School leads', data: { email: 'q@d.org', draft_id: 'draftAAAA1', submission_id: 'S2', name: 'Q', organization: 'O' } }] });
  const keys = g.ctx.HEADERS['Partial leads'].map((h) => h[0]);
  assert.equal(g.tab('Partial leads')[1][keys.indexOf('status')], 'converted');
  const mailsBefore = g.sent.mail.length;
  assert.equal(g.ctx.processPartialLeads(), 0);
  assert.equal(g.sent.mail.length, mailsBefore);
});

t('unfinished consented partial lead alerts once after the wait, never twice', () => {
  const g = loadCodeGs(FILE, { SHEET_SECRET: 's', NOTIFY_EMAILS: 'team@tomoclub.org', PARTIAL_WAIT_MINUTES: '0' });
  g.post({ secret: 's', action: 'upsert_partial', data: { draft_id: 'draftBBBB1', email: 'r@d.org', name: 'R', organization: 'District R', phone: '+1 555 0100' } });
  assert.equal(g.ctx.processPartialLeads(), 1);
  assert.equal(g.ctx.processPartialLeads(), 0);
  assert.equal(g.sent.mail.length, 1);
  assert.match(g.sent.mail[0].body, /District R/);
  assert.match(g.sent.mail[0].body, /\+1 555 0100/);
  // Second draft from the same person the same day: no new alert.
  g.post({ secret: 's', action: 'upsert_partial', data: { draft_id: 'draftBBBB2', email: 'r@d.org', name: 'R' } });
  g.ctx.processPartialLeads();
  assert.equal(g.sent.mail.length, 1);
});

t('partial lead younger than the wait is not alerted yet', () => {
  const g = loadCodeGs(FILE, { SHEET_SECRET: 's', NOTIFY_EMAILS: 'team@tomoclub.org' });
  g.post({ secret: 's', action: 'upsert_partial', data: { draft_id: 'draftCCCC1', email: 's@d.org' } });
  assert.equal(g.ctx.processPartialLeads(), 0);
  assert.equal(g.sent.mail.length, 0);
});

t('status updates and reads with since filter', () => {
  const g = loadCodeGs(FILE, { SHEET_SECRET: 's' });
  assert.equal(g.post({ secret: 's', action: 'set_status', data: { lead_id: 'sub-1', status: 'Bogus' } }).ok, false);
  assert.equal(g.post({ secret: 's', action: 'set_status', data: { lead_id: 'sub-1', status: 'Contacted', note: 'Emailed', by: 'Avinash' } }).ok, true);
  g.post({ secret: 's', rows: [{ sheet: 'Website events', data: { timestamp: '2026-11-01T00:00:00Z', event: 'page_view' } }, { sheet: 'Website events', data: { timestamp: '2026-11-22T00:00:00Z', event: 'page_view' } }] });
  const r = g.post({ secret: 's', action: 'read', tabs: ['Lead status', 'Website events'], since: '2026-11-15' });
  assert.equal(r.tabs['Website events'].length, 1);
  assert.equal(r.tabs['Lead status'][0].status, 'Contacted');
});

t('installTriggers is idempotent', () => {
  const g = loadCodeGs(FILE, {});
  g.ctx.installTriggers(); g.ctx.installTriggers();
  assert.deepEqual(g.sent.triggers, ['processPartialLeads']);
});

t('formulas typed into a form are stored as plain text, not run', () => {
  const src = fs.readFileSync(FILE, 'utf8');
  assert.ok(/setNumberFormat\('@'\);[^]*?setValues\(values\)/.test(src));
});
console.log('all', n, 'Apps Script tests passed');
