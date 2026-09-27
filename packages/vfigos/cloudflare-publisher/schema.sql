CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,
  package_sha256 TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('image','carousel')),
  scheduled_at INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('scheduled','publishing','retry','reconcile_required','published_verified','cancelled','dead_letter')),
  caption TEXT NOT NULL DEFAULT '',
  media_json TEXT NOT NULL,
  authorization_json TEXT NOT NULL,
  job_auth TEXT NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  lease_until INTEGER,
  next_attempt_at INTEGER,
  last_error_class TEXT,
  last_error TEXT,
  meta_media_id TEXT,
  permalink TEXT,
  published_at INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_due_idx ON jobs(status, scheduled_at, next_attempt_at);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL,
  event TEXT NOT NULL,
  detail_json TEXT NOT NULL DEFAULT '{}',
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS events_job_idx ON events(job_id, id);
CREATE TABLE IF NOT EXISTS runtime_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);
