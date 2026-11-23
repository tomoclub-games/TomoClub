// In-memory stand-ins for the Apps Script services Code.gs uses, so it can be tested with Node.
import fs from 'node:fs';
import vm from 'node:vm';

export function loadCodeGs(file, props = {}) {
  const sheets = new Map();
  const sent = { slack: [], mail: [], triggers: [] };
  const cache = new Map();
  class Range {
    constructor(sh, r, c, nr = 1, nc = 1) { Object.assign(this, { sh, r, c, nr, nc }); }
    setValues(v) { v.forEach((row, i) => row.forEach((x, j) => this.sh.set(this.r + i, this.c + j, x))); return this; }
    setValue(x) { this.sh.set(this.r, this.c, x); return this; }
    getValues() { const out = []; for (let i = 0; i < this.nr; i++) { const row = []; for (let j = 0; j < this.nc; j++) row.push(this.sh.get(this.r + i, this.c + j)); out.push(row); } return out; }
    setNumberFormat() { return this; } setFontWeight() { return this; }
  }
  class Sheet {
    constructor(name) { this.name = name; this.rows = []; }
    set(r, c, v) { while (this.rows.length < r) this.rows.push([]); const row = this.rows[r - 1]; while (row.length < c) row.push(''); row[c - 1] = v; }
    get(r, c) { const row = this.rows[r - 1] || []; return row[c - 1] === undefined ? '' : row[c - 1]; }
    getLastRow() { return this.rows.length; }
    getLastColumn() { return this.rows.reduce((m, r) => Math.max(m, r.length), 0); }
    appendRow(v) { this.rows.push(v.slice()); }
    setFrozenRows() {}
    getRange(r, c, nr, nc) { return new Range(this, r, c, nr, nc); }
  }
  const ss = {
    getSheetByName: (n) => sheets.get(n) || null,
    insertSheet: (n) => { const s = new Sheet(n); sheets.set(n, s); return s; },
  };
  const ctx = {
    console,
    SpreadsheetApp: { getActiveSpreadsheet: () => ss, openById: () => ss },
    LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
    PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => (k in props ? props[k] : null) }) },
    CacheService: { getScriptCache: () => ({ get: (k) => cache.get(k) || null, put: (k, v) => cache.set(k, v) }) },
    UrlFetchApp: { fetch: (url, opt) => { sent.slack.push(JSON.parse(opt.payload).text); return { getResponseCode: () => 200 }; } },
    MailApp: { sendEmail: (m) => sent.mail.push(m) },
    ContentService: { MimeType: { JSON: 'json' }, createTextOutput: (t) => ({ setMimeType: () => ({ body: t }) }) },
    ScriptApp: {
      getProjectTriggers: () => sent.triggers.map((h) => ({ getHandlerFunction: () => h })),
      deleteTrigger: (t) => { sent.triggers.splice(sent.triggers.indexOf(t.getHandlerFunction()), 1); },
      newTrigger: (h) => ({ timeBased: () => ({ everyMinutes: () => ({ create: () => sent.triggers.push(h) }) }) }),
    },
    Date,
  };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(file, 'utf8'), ctx);
  const post = (body) => JSON.parse(ctx.doPost({ postData: { contents: JSON.stringify(body) } }).body);
  const tab = (name) => { const s = sheets.get(name); return s ? s.rows : null; };
  return { ctx, post, tab, sheets, sent, cache, props };
}
