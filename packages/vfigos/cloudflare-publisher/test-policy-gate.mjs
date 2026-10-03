import assert from "node:assert/strict";
import {evaluateInstagramPublishJob} from "./src/policy_gate.js";

const hex = (buffer) => [...new Uint8Array(buffer)].map((value) => value.toString(16).padStart(2, "0")).join("");
const shaText = async (value) => hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));

const caption = "Velvet Factory";
const copySha = await shaText(caption);
const packageSha = "a".repeat(64);
const mediaSha = "b".repeat(64);
const oldGates = {
  transport: "PASS",
  visible_text: "PASS",
  exact_final_preflight: "PASS",
  visual_standard: "PASS",
  rights_privacy: "PASS",
  brand: "PASS",
  product_truth: "PASS",
};

function evidenceItem(n) {
  return {
    status: "PASS",
    ref: "fixture://evidence/" + n,
    sha256: String(n).repeat(64),
    failure_mode: null,
    reason: null,
  };
}

function contentReady(overrides = {}) {
  const base = {
    schema_version: "velvet.content_ready.v1",
    status: "PASS",
    bindings: {
      content_id: "G100",
      package_sha256: packageSha,
      copy_sha256: copySha,
      media_sha256s: [mediaSha],
    },
    evidence: {
      product_truth: evidenceItem(1),
      brand: evidenceItem(2),
      copy: evidenceItem(3),
      visual_qa: evidenceItem(4),
      rights_privacy: evidenceItem(5),
      render_transport: evidenceItem(6),
    },
    repair_targets: [],
    retry_targets: [],
    hard_blockers: [],
    owner_surface: "NONE",
    validated_at: "2026-10-03T15:30:00Z",
  };
  return {
    ...base,
    ...overrides,
    bindings: {...base.bindings, ...(overrides.bindings || {})},
    evidence: {...base.evidence, ...(overrides.evidence || {})},
  };
}

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
      evidence: "CONTENT_READY exact envelope",
      policy_context: policyContext,
    },
    created_at: Math.floor(Date.parse("2026-10-04T00:00:01Z") / 1000),
    ...overrides,
  };
}

const standing = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  content_ready: contentReady(),
  forbidden_effects: [],
  human_approval: null,
}), {STANDING_AUTHORIZATION: "true"});
assert.equal(standing.result.decision, "ALLOW");
assert.ok(standing.result.reason_codes.includes("CONTENT_READY_PASS"));
assert.ok(standing.result.reason_codes.includes("STANDING_AUTHORIZATION"));
assert.equal(standing.result.receipt.bindings.copy_sha256, copySha);

const noStanding = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  content_ready: contentReady(),
  forbidden_effects: [],
  human_approval: null,
}), {STANDING_AUTHORIZATION: "false"});
assert.equal(noStanding.result.decision, "REQUIRE_OWNER_APPROVAL");
assert.ok(noStanding.result.reason_codes.includes("CONTENT_READY_PASS"));

const ownerApproved = await evaluateInstagramPublishJob(job({
  risk_class: "MEDIUM",
  content_ready: contentReady(),
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

const qualityFailure = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  content_ready: contentReady({
    status: "FAIL",
    repair_targets: ["brand"],
  }),
  forbidden_effects: [],
  human_approval: null,
}), {STANDING_AUTHORIZATION: "true"});
assert.equal(qualityFailure.result.decision, "DENY");
assert.ok(qualityFailure.result.reason_codes.includes("CONTENT_READY_NOT_PASS"));

const bindingMismatch = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  content_ready: contentReady({bindings: {package_sha256: "d".repeat(64)}}),
  forbidden_effects: [],
  human_approval: null,
}), {STANDING_AUTHORIZATION: "true"});
assert.equal(bindingMismatch.result.decision, "DENY");
assert.ok(bindingMismatch.result.reason_codes.includes("CONTENT_READY_BINDING_MISMATCH"));

const missingAfterCutover = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  forbidden_effects: [],
  human_approval: null,
}), {STANDING_AUTHORIZATION: "true"});
assert.equal(missingAfterCutover.result.decision, "DENY");
assert.ok(missingAfterCutover.result.reason_codes.includes("CONTENT_READY_REQUIRED"));

const boundedCompatibility = await evaluateInstagramPublishJob(job({
  risk_class: "LOW",
  gates: oldGates,
  forbidden_effects: [],
  human_approval: null,
}, {
  created_at: Math.floor(Date.parse("2026-10-03T15:58:00Z") / 1000),
}), {STANDING_AUTHORIZATION: "true"});
assert.equal(boundedCompatibility.result.decision, "ALLOW");
assert.ok(boundedCompatibility.result.reason_codes.includes("CONTENT_READY_LEGACY_GATE_COMPATIBILITY"));

const legacy = await evaluateInstagramPublishJob({
  id: "legacy-job",
  content_id: "G099",
  package_sha256: packageSha,
  kind: "image",
  scheduled_at: 1_790_000_000,
  caption,
  media: [{key: "legacy.jpg", sha256: mediaSha, url: "https://example.invalid/media.jpg"}],
  authorization: {
    kind: "owner_schedule_authorization",
    owner_approved: true,
    evidence: "legacy approval receipt",
    content_id: "G099",
    package_sha256: packageSha,
  },
  created_at: Math.floor(Date.parse("2026-09-27T12:00:00Z") / 1000),
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

console.log("OK cloudflare publisher policy gate cases=9 content_ready=required_new_jobs");
