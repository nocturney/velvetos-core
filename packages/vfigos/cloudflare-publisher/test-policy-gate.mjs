import assert from "node:assert/strict";
import {evaluateInstagramPublishJob} from "./src/policy_gate.js";

const hex = (buffer) => [...new Uint8Array(buffer)].map((value) => value.toString(16).padStart(2, "0")).join("");
const shaText = async (value) => hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));

const caption = "Velvet Factory";
const copySha = await shaText(caption);
const packageSha = "a".repeat(64);
const mediaSha = "b".repeat(64);
const gates = {
  transport: "PASS",
  visible_text: "PASS",
  exact_final_preflight: "PASS",
  visual_standard: "PASS",
  rights_privacy: "PASS",
  brand: "PASS",
  product_truth: "PASS",
};

function job(policyContext, overrides = {}) {
  return {
    id: "job-policy-test",
    content_id: "G100",
    package_sha256: packageSha,
    kind: "image",
    scheduled_at: 1_790_000_000,
    caption,
    media: [{key: "media.jpg", sha256: mediaSha, url: "https://example.invalid/media.jpg"}],
    authorization: {
      kind: "policy_authorization_v1",
      evidence: "exact preflight receipt",
      policy_context: policyContext,
    },
    created_at: 1_790_000_000,
    ...overrides,
  };
}

const standing = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  gates,
  forbidden_effects: [],
  human_approval: null,
}), {STANDING_AUTHORIZATION: "true"});
assert.equal(standing.result.decision, "ALLOW");
assert.ok(standing.result.reason_codes.includes("STANDING_AUTHORIZATION"));
assert.equal(standing.result.receipt.bindings.copy_sha256, copySha);

const noStanding = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  gates,
  forbidden_effects: [],
  human_approval: null,
}), {STANDING_AUTHORIZATION: "false"});
assert.equal(noStanding.result.decision, "REQUIRE_OWNER_APPROVAL");

const ownerApproved = await evaluateInstagramPublishJob(job({
  risk_class: "MEDIUM",
  gates,
  forbidden_effects: [],
  human_approval: {
    approved: true,
    evidence: "owner approval receipt",
    content_id: "G100",
    package_sha256: packageSha,
    copy_sha256: copySha,
  },
}), {STANDING_AUTHORIZATION: "false"});
assert.equal(ownerApproved.result.decision, "ALLOW");
assert.ok(ownerApproved.result.reason_codes.includes("EXACT_OWNER_APPROVAL"));

const badGate = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  gates: {...gates, exact_final_preflight: "FAIL"},
  forbidden_effects: [],
  human_approval: null,
}), {STANDING_AUTHORIZATION: "true"});
assert.equal(badGate.result.decision, "DENY");

const legacy = await evaluateInstagramPublishJob({
  id: "legacy-job",
  content_id: "G099",
  package_sha256: packageSha,
  kind: "image",
  scheduled_at: 1_790_000_000,
  caption,
  media: [{key: "legacy.jpg", sha256: mediaSha, url: "https://example.invalid/legacy.jpg"}],
  authorization: {
    kind: "owner_schedule_authorization",
    owner_approved: true,
    evidence: "legacy approval receipt",
    content_id: "G099",
    package_sha256: packageSha,
  },
  created_at: 1_790_000_000,
}, {STANDING_AUTHORIZATION: "false"});
assert.equal(legacy.context.copy_sha256, null);
assert.equal(legacy.result.decision, "ALLOW");
assert.ok(legacy.result.reason_codes.includes("LEGACY_COMPATIBILITY"));

const legacyExpired = await evaluateInstagramPublishJob({
  ...job(null),
  content_id: "G098",
  authorization: {
    kind: "owner_schedule_authorization",
    owner_approved: true,
    evidence: "legacy approval receipt",
    content_id: "G098",
    package_sha256: packageSha,
  },
  created_at: Math.floor(Date.parse("2026-09-28T00:00:01Z") / 1000),
}, {STANDING_AUTHORIZATION: "false"});
assert.equal(legacyExpired.result.decision, "DENY");
assert.ok(legacyExpired.result.reason_codes.includes("LEGACY_AUTHORIZATION_INVALID_OR_EXPIRED"));

console.log("OK cloudflare publisher policy gate cases=6");
