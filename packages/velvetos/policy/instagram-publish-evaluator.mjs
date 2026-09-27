const HEX64 = /^[0-9a-f]{64}$/;
const CONTENT_ID = /^[A-Za-z0-9._-]{3,120}$/;

function receipt(policy, context, decision, reasonCodes) {
  return {
    receipt_version: "instagram.publish.decision.v1",
    policy_id: policy.policy_id,
    policy_version: policy.version,
    decision,
    reason_codes: reasonCodes,
    bindings: {
      content_id: context.content_id ?? null,
      package_sha256: context.package_sha256 ?? null,
      copy_sha256: context.copy_sha256 ?? null,
      media_sha256s: Array.isArray(context.media_sha256s) ? [...context.media_sha256s] : [],
    },
    postconditions: {
      provider_receipt_required: policy.postconditions.provider_receipt_required === true,
      live_readback_required: policy.postconditions.live_readback_required === true,
      ambiguous_after_publish_boundary: policy.postconditions.ambiguous_after_publish_boundary,
    },
  };
}

function finish(policy, context, decision, ...reasonCodes) {
  return {
    decision,
    reason_codes: reasonCodes,
    receipt: receipt(policy, context, decision, reasonCodes),
  };
}

function exactBindingsValid(context) {
  return (
    CONTENT_ID.test(context.content_id || "") &&
    HEX64.test(context.package_sha256 || "") &&
    HEX64.test(context.copy_sha256 || "") &&
    Array.isArray(context.media_sha256s) &&
    context.media_sha256s.length >= 1 &&
    context.media_sha256s.length <= 10 &&
    context.media_sha256s.every((value) => HEX64.test(value || ""))
  );
}

function humanApprovalState(context) {
  const approval = context.human_approval;
  if (approval == null) return {present: false, valid: false};
  const valid = (
    approval.approved === true &&
    typeof approval.evidence === "string" &&
    approval.evidence.trim().length >= 8 &&
    approval.content_id === context.content_id &&
    approval.package_sha256 === context.package_sha256 &&
    approval.copy_sha256 === context.copy_sha256
  );
  return {present: true, valid};
}

function legacyAuthorizationState(policy, context) {
  const legacy = context.legacy_authorization;
  if (legacy == null) return {present: false, valid: false};
  const compat = policy.legacy_compatibility || {};
  const createdAt = Date.parse(context.job_created_at || "");
  const cutoff = Date.parse(compat.jobs_created_before || "");
  const kindAllowed = Array.isArray(compat.allowed_authorization_kinds) &&
    compat.allowed_authorization_kinds.includes(legacy.kind);
  let kindEvidence = typeof legacy.evidence === "string" && legacy.evidence.trim().length >= 8;
  if (legacy.kind === "owner_schedule_authorization") kindEvidence = kindEvidence && legacy.owner_approved === true;
  const valid = (
    kindAllowed &&
    Number.isFinite(createdAt) &&
    Number.isFinite(cutoff) &&
    createdAt < cutoff &&
    legacy.content_id === context.content_id &&
    legacy.package_sha256 === context.package_sha256 &&
    kindEvidence
  );
  return {present: true, valid};
}

export function evaluateInstagramPublish(policy, context) {
  if (!policy || policy.policy_id !== "instagram.publish" || policy.version !== 1) {
    return finish(policy || {policy_id: "instagram.publish", version: 0, postconditions: {}}, context || {}, "DENY", "POLICY_INVALID");
  }
  if (!context || typeof context !== "object") {
    return finish(policy, {}, "DENY", "CONTEXT_REQUIRED");
  }
  if (context.channel !== policy.scope.channel || context.publication_type !== policy.scope.publication_type) {
    return finish(policy, context, "DENY", "SCOPE_MISMATCH");
  }
  if (!policy.scope.mutation_tools.includes(context.mutation_tool)) {
    return finish(policy, context, "DENY", "MUTATION_TOOL_NOT_ALLOWED");
  }
  if (!exactBindingsValid(context)) {
    return finish(policy, context, "DENY", "EXACT_BINDINGS_INVALID");
  }

  const forbidden = Array.isArray(context.forbidden_effects) ? context.forbidden_effects : [];
  const blocked = forbidden.filter((value) => policy.forbidden_effects.includes(value));
  if (blocked.length) {
    return finish(policy, context, "DENY", "FORBIDDEN_EFFECT", ...blocked.map((value) => "FORBIDDEN:" + value));
  }

  const legacy = legacyAuthorizationState(policy, context);
  if (legacy.present) {
    if (!legacy.valid) return finish(policy, context, "DENY", "LEGACY_AUTHORIZATION_INVALID_OR_EXPIRED");
    return finish(policy, context, "ALLOW", "LEGACY_COMPATIBILITY");
  }

  const gates = context.gates && typeof context.gates === "object" ? context.gates : {};
  for (const gate of policy.required_gates) {
    const value = gates[gate];
    if (!policy.gate_pass_values.includes(value)) {
      return finish(policy, context, "DENY", "GATE_NOT_PASS:" + gate);
    }
  }

  const risk = String(context.risk_class || "").toUpperCase();
  if (!["LOW", "MEDIUM", "HIGH"].includes(risk)) {
    return finish(policy, context, "DENY", "RISK_CLASS_INVALID");
  }

  const human = humanApprovalState(context);
  if (human.present && !human.valid) {
    return finish(policy, context, "DENY", "HUMAN_APPROVAL_BINDING_MISMATCH");
  }
  if (human.valid) {
    if (!policy.risk.owner_approval_allows.includes(risk)) {
      return finish(policy, context, "DENY", "OWNER_APPROVAL_RISK_NOT_ALLOWED");
    }
    return finish(policy, context, "ALLOW", "EXACT_OWNER_APPROVAL");
  }

  if (context.standing_authorization === true) {
    if (risk === policy.risk.standing_authorization_max) {
      return finish(policy, context, "ALLOW", "STANDING_AUTHORIZATION");
    }
    return finish(policy, context, "REQUIRE_OWNER_APPROVAL", "RISK_EXCEEDS_STANDING_AUTHORIZATION");
  }

  return finish(policy, context, policy.authorization.default, "OWNER_APPROVAL_REQUIRED");
}

export function validateDecisionReceipt(policy, context, decisionResult) {
  if (!decisionResult || typeof decisionResult !== "object") return false;
  const fresh = evaluateInstagramPublish(policy, context);
  return JSON.stringify(fresh) === JSON.stringify(decisionResult);
}
