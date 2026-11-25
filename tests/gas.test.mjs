// Tests for data-capture/Code.gs (the Apps Script collector), run in Node with small stand-ins for
// SpreadsheetApp, CacheService, LockService, PropertiesService, UrlFetchApp and ContentService.
// Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const CODE = fs.readFileSync(new URL('../data-capture/Code.gs', import.meta.url), 'utf8');

function makeSheet(grid) {
  const cell = (r, c) => (grid[r] && grid[r][c] !== undefined ? grid[r][c] : '');
  return {
    grid,
    getLastRow: () => grid.length,
    appendRow: (a) => grid.push(a.slice()),
    setFrozenRows() {},
    getRange(r, c, nr = 1, nc = 1) {
      return {
        setFontWeight() { return this; },
        setNumberFormat() { return this; },
        getValues: () => Array.from({ length: nr }, (_, i) => Array.from({ length: nc }, (_, j) => cell(r - 1 + i, c - 1 + j))),
        setValue(v) { (grid[r - 1] = grid[r - 1] || [])[c - 1] = v; return this; },
        setValues(vals) {
          vals.forEach((row, i) => { grid[r - 1 + i] = grid[r - 1 + i] || []; row.forEach((v, j) => { grid[r - 1 + i][c - 1 + j] = v; }); });
          return this;
        },
      };
    },
  };
}

function load() {
  const env = { sheets: {}, cache: {}, slack: 0, warnings: [] };
  const ctx = {
    console: { ...console, warn: (m) => env.warnings.push(m), error: () => {} },
    SpreadsheetApp: { getActiveSpreadsheet: () => ({ getSheetByName: (n) => env.sheets[n] || null, insertSheet: (n) => (env.sheets[n] = makeSheet([])) }) },
    LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
    CacheService: { getScriptCache: () => ({
      get: (k) => env.cache[k] || null,
      putAll: (o, ttl) => { assert.ok(ttl <= 21600, 'CacheService allows at most 6 hours'); Object.assign(env.cache, o); },
    }) },
    PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => (k === 'SLACK_WEBHOOK_URL' ? 'https://hooks.slack.test/x' : null) }) },
    UrlFetchApp: { fetch: () => { env.slack++; } },
    ContentService: { createTextOutput: (s) => ({ setMimeType: () => JSON.parse(s) }), MimeType: { JSON: 1 } },
  };
  vm.createContext(ctx);
  vm.runInContext(CODE, ctx);
  env.HEADERS = ctx.HEADERS;
  env.post = (rows) => ctx.doPost({ postData: { contents: JSON.stringify({ rows }) } });
  return env;
}

const leadRow = (id) => ({ sheet: 'School leads', data: { type: 'discovery_request', name: 'Jane', email: 'j@x.org', submission_id: id } });

test('new columns are added at the end of the tabs', () => {
  const { HEADERS } = load();
  assert.deepEqual(Array.from(HEADERS['School leads'].slice(-3), (h) => h[1]), ['Landing page', 'Submission ID', 'Follow-up status']);
  assert.equal(HEADERS['E-book requests'].slice(-1)[0][1], 'Submission ID');
  assert.equal(HEADERS['Toolkit downloads'].slice(-1)[0][1], 'Submission ID');
});

test('the same submission ID twice gives one row and one Slack alert', () => {
  const env = load();
  assert.deepEqual({ ...env.post([leadRow('abc')]) }, { ok: true, saved: 1, duplicates: 0 });
  assert.deepEqual({ ...env.post([leadRow('abc')]) }, { ok: true, saved: 0, duplicates: 1 });
  assert.equal(env.sheets['School leads'].grid.length, 2); // header + one row
  assert.equal(env.slack, 1);
});

test('a duplicate inside one batch is skipped too', () => {
  const env = load();
  assert.equal(env.post([leadRow('zz'), leadRow('zz')]).saved, 1);
  assert.equal(env.slack, 1);
});

test('rows without a submission ID are always saved', () => {
  const env = load();
  env.post([{ sheet: 'School leads', data: { name: 'A' } }]);
  env.post([{ sheet: 'School leads', data: { name: 'A' } }]);
  assert.equal(env.sheets['School leads'].grid.length, 3);
});

test('the same ID in a different tab is not a duplicate', () => {
  const env = load();
  env.post([leadRow('abc')]);
  assert.equal(env.post([{ sheet: 'Toolkit downloads', data: { email: 'j@x.org', submission_id: 'abc' } }]).saved, 1);
});

test('an existing tab gets the new header titles; old rows are untouched; follow-up status is left blank', () => {
  const env = load();
  const H = env.HEADERS['School leads'];
  const oldTitles = H.slice(0, -2).map((h) => h[1]);
  env.sheets['School leads'] = makeSheet([oldTitles.slice(), oldTitles.map(() => 'old')]);
  env.post([leadRow('abc')]);
  const g = env.sheets['School leads'].grid;
  assert.deepEqual(Array.from(g[0]), Array.from(H, (h) => h[1]));
  assert.equal(g[1].length, oldTitles.length);
  assert.equal(g[2][H.length - 2], 'abc');
  assert.equal(g[2][H.length - 1], '');
});

test('a hand-written header title is not overwritten; a warning is logged', () => {
  const env = load();
  const H = env.HEADERS['E-book requests'];
  env.sheets['E-book requests'] = makeSheet([H.slice(0, -1).map((h) => h[1]).concat(['My notes'])]);
  assert.equal(env.post([{ sheet: 'E-book requests', data: { email: 'a@b.org', submission_id: 'e1' } }]).saved, 1);
  assert.equal(env.sheets['E-book requests'].grid[0].slice(-1)[0], 'My notes');
  assert.equal(env.warnings.length, 1);
});
