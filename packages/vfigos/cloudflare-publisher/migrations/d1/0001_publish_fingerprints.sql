-- D1 migration for the 72h publish fingerprint guard (#374).
-- Idempotent. Apply to the EXISTING production D1 BEFORE deploying a Worker that
-- contains src/fingerprint.js; otherwise the guard query fails and every due job
-- fails closed (retry -> dead_letter) instead of publishing.
--   npx wrangler d1 execute velvetos-instagram-publisher --remote --file=migrations/d1/0001_publish_fingerprints.sql
CREATE TABLE IF NOT EXISTS publish_fingerprints (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fingerprint TEXT NOT NULL,
  job_id TEXT NOT NULL,
  recorded_at INTEGER NOT NULL,
  outcome TEXT NOT NULL CHECK(outcome IN ('published_verified','reconcile_required'))
);
CREATE INDEX IF NOT EXISTS publish_fingerprints_lookup_idx
  ON publish_fingerprints(fingerprint, recorded_at DESC);
