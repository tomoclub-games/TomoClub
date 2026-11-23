// SQLite storage (Node's built-in driver). One file holds districts, sources,
// the full-text index and leads. Indexed content is public website text only.
import { DatabaseSync } from 'node:sqlite';
import fs from 'node:fs';
import path from 'node:path';
import { config } from './config.js';

fs.mkdirSync(config.dataDir, { recursive: true });
export const db = new DatabaseSync(path.join(config.dataDir, 'app.db'));

db.exec(`
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS districts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  website TEXT,
  host TEXT,
  status TEXT NOT NULL,           -- queued | processing | ready | failed
  message TEXT,
  current_url TEXT,
  categories TEXT,                -- JSON array of {key,label,count}
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS districts_host ON districts(host);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  district_id TEXT NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
  url TEXT,                       -- null for uploads
  title TEXT,
  kind TEXT NOT NULL,             -- page | pdf | upload
  status TEXT NOT NULL,           -- ok | partial | failed | skipped
  reason TEXT,
  pages INTEGER,
  chars INTEGER DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sources_district ON sources(district_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
  body, heading, title,
  district_id UNINDEXED, source_id UNINDEXED, page UNINDEXED,
  tokenize = 'porter unicode61'
);

CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL,
  work_email TEXT NOT NULL,
  job_title TEXT NOT NULL,
  school_district TEXT NOT NULL,
  problem TEXT NOT NULL,
  demo_district TEXT,             -- which district the visitor was trying, if any
  ip_hash TEXT,
  user_agent TEXT,
  webhook_status TEXT,
  created_at TEXT NOT NULL
);
`);

export const now = () => new Date().toISOString();

export function deleteDistrictContent(districtId) {
  db.prepare('DELETE FROM chunks WHERE district_id = ?').run(districtId);
  db.prepare('DELETE FROM sources WHERE district_id = ?').run(districtId);
}
