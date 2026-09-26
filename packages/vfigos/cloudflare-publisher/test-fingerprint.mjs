import assert from "node:assert/strict";
import {
  FINGERPRINT_WINDOW_SECONDS,
  checkRecentFingerprint,
  normalizeCaption,
  publishFingerprint,
  recordFingerprint,
} from "./src/fingerprint.js";

class FakeDB {
  constructor() { this.rows = []; }
  prepare(sql) {
    const db = this;
    return {
      bind(...args) {
        return {
          async first() {
            assert.match(sql, /^SELECT recorded_at/);
            const [fingerprint, earliest, latest] = args;
            const rows = db.rows
              .filter((r) => r.fingerprint === fingerprint)
              .filter((r) => r.recorded_at >= earliest && r.recorded_at <= latest)
              .sort((a, b) => b.recorded_at - a.recorded_at);
            return rows[0] ? { recorded_at: rows[0].recorded_at } : null;
          },
          async run() {
            assert.match(sql, /^INSERT INTO publish_fingerprints/);
            const [fingerprint, job_id, recorded_at, outcome] = args;
            db.rows.push({ fingerprint, job_id, recorded_at, outcome });
            return { success: true };
          },
        };
      },
    };
  }
}

const db = new FakeDB();
const now = 1_789_000_000;
const media = ["a".repeat(64)];
const caption = "  Velvet\n  Factory   ";
const fp = await publishFingerprint({
  igUserId: "17841400000000000",
  mediaSha256s: media,
  caption,
});
assert.equal(normalizeCaption(caption), "Velvet Factory");

let graphWrites = 0;
let check = await checkRecentFingerprint(db, fp, now);
assert.equal(check.ok, true);
graphWrites += 1;
await recordFingerprint(db, {
  fingerprint: fp,
  jobId: "incident-first",
  recordedAt: now,
  outcome: "published_verified",
});

let blocked = 0;
for (let i = 0; i < 5; i += 1) {
  check = await checkRecentFingerprint(db, fp, now + i + 1);
  if (!check.ok) blocked += 1;
  else graphWrites += 1;
}
assert.equal(blocked, 5);
assert.equal(graphWrites, 1);

const afterWindow = await checkRecentFingerprint(
  db,
  fp,
  now + FINGERPRINT_WINDOW_SECONDS + 1,
);
assert.equal(afterWindow.ok, true);

console.log(JSON.stringify({
  incident: "2026-09-13",
  repeats_blocked: blocked,
  extra_publishes: graphWrites - 1,
  graph_writes_total: graphWrites,
  fingerprint: fp,
}));
