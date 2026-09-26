export const FINGERPRINT_WINDOW_SECONDS = 72 * 60 * 60;
const te = new TextEncoder();

function hex(bytes) {
  return [...new Uint8Array(bytes)]
    .map((x) => x.toString(16).padStart(2, "0"))
    .join("");
}

export function normalizeCaption(caption) {
  if (caption == null) return "";
  if (typeof caption !== "string") throw new TypeError("caption must be a string");
  return caption.normalize("NFC").replace(/\s+/gu, " ").trim();
}

export function normalizeMediaSha256s(mediaSha256s) {
  if (!Array.isArray(mediaSha256s) || mediaSha256s.length < 1) {
    throw new TypeError("media_sha256s must be a non-empty array");
  }
  return mediaSha256s.map((digest) => {
    if (typeof digest !== "string" || !/^[0-9a-f]{64}$/.test(digest)) {
      throw new TypeError("media_sha256s entries must be lowercase sha256 hex");
    }
    return digest;
  });
}

export async function publishFingerprint({ igUserId, mediaSha256s, caption }) {
  const body = JSON.stringify({
    caption: normalizeCaption(caption),
    ig_user_id: String(igUserId || "").trim(),
    media_sha256s: normalizeMediaSha256s(mediaSha256s),
  });
  return hex(await crypto.subtle.digest("SHA-256", te.encode(body)));
}

export async function checkRecentFingerprint(
  db,
  fingerprint,
  nowSeconds,
  windowSeconds = FINGERPRINT_WINDOW_SECONDS,
) {
  const earliest = nowSeconds - windowSeconds;
  const latest = nowSeconds + 60;
  const row = await db
    .prepare(
      "SELECT recorded_at FROM publish_fingerprints " +
      "WHERE fingerprint=? AND recorded_at>=? AND recorded_at<=? " +
      "ORDER BY recorded_at DESC LIMIT 1",
    )
    .bind(fingerprint, earliest, latest)
    .first();
  if (!row) return { ok: true, status: "clear" };
  return {
    ok: false,
    status: "repeat_within_window",
    last_recorded_at: Number(row.recorded_at),
  };
}

export async function recordFingerprint(
  db,
  { fingerprint, jobId, recordedAt, outcome },
) {
  await db
    .prepare(
      "INSERT INTO publish_fingerprints" +
      "(fingerprint,job_id,recorded_at,outcome) VALUES(?,?,?,?)",
    )
    .bind(fingerprint, jobId, recordedAt, outcome)
    .run();
}
