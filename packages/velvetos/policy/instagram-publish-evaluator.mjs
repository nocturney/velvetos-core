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

function contentReadyState(policy, context) {
  const ready = context.content_ready;
  const cfg = policy.content_ready || {};
  const passValues = Array.isArray(cfg.pass_values) ? cfg.pass_values : ["PASS", "NOT_APPLICABLE"];
  const requiredEvidence = Array.isArray(cfg.required_evidence) ? cfg.required_evidence : [];

  if (ready != null) {
    if (!ready || typeof ready !== "object" || Array.isArray(ready)) {
      return {present: true, valid: false, reason: "CONTENT_READY_INVALID"};
    }
    if (ready.schema_version !== cfg.schema_version || ready.status !== "PASS") {
      return {present: true, valid: false, reason: ready.status === "FAIL" ? "CONTENT_READY_NOT_PASS" : "CONTENT_READY_INVALID"};
    }
    const bindings = ready.bindings && typeof ready.bindings === "object" ? ready.bindings : {};
    const exact = (
      bindings.content_id === context.content_id &&
      bindings.package_sha256 === context.package_sha256 &&
      bindings.copy_sha256 === context.copy_sha256 &&
      Array.isArray(bindings.media_sha256s) &&
      JSON.stringify(bindings.media_sha256s) === JSON.stringify(context.media_sha256s)
    );
    if (!exact) return {present: true, valid: false, reason: "CONTENT_READY_BINDING_MISMATCH"};

    const evidence = ready.evidence && typeof ready.evidence === "object" ? ready.evidence : {};
    if (Object.keys(evidence).length !== requiredEvidence.length ||
        requiredEvidence.some((key) => !Object.prototype.hasOwnProperty.call(evidence, key))) {
      return {present: true, valid: false, reason: "CONTENT_READY_EVIDENCE_SET_INVALID"};
    }
    for (const key of requiredEvidence) {
      const item = evidence[key];
      if (!item || typeof item !== "object" || !passValues.includes(item.status)) {
        return {present: true, valid: false, reason: "CONTENT_READY_EVIDENCE_NOT_PASS:" + key};
      }
      if (typeof item.ref !== "string" || item.ref.trim().length < 1 || !HEX64.test(item.sha256 || "")) {
        return {present: true, valid: false, reason: "CONTENT_READY_EVIDENCE_IDENTITY_INVALID:" + key};
      }
    }
    if ((Array.isArray(ready.repair_targets) && ready.repair_targets.length) ||
        (Array.isArray(ready.retry_targets) && ready.retry_targets.length) ||
        (Array.isArray(ready.hard_blockers) && ready.hard_blockers.length) ||
        ready.owner_surface !== "NONE") {
      return {present: true, valid: false, reason: "CONTENT_READY_UNRESOLVED_WORK"};
    }
    return {present: true, valid: true, legacy: false};
  }

  const compat = cfg.legacy_gate_compatibility || {};
  const createdAt = Date.parse(context.job_created_at || "");
  const cutoff = Date.parse(compat.jobs_created_before || "");
  if (Number.isFinite(createdAt) && Number.isFinite(cutoff) && createdAt < cutoff) {
    const gates = context.gates && typeof context.gates === "object" ? context.gates : {};
    const required = Array.isArray(compat.required_gates) ? compat.required_gates : [];
    const allowed = Array.isArray(compat.pass_values) ? compat.pass_values : ["PASS", "NOT_APPLICABLE"];
    for (const gate of required) {
      if (!allowed.includes(gates[gate])) {
        return {present: false, valid: false, legacy: true, reason: "LEGACY_GATE_NOT_PASS:" + gate};
      }
    }
    return {present: false, valid: true, legacy: true};
  }
  return {present: false, valid: false, legacy: false, reason: "CONTENT_READY_REQUIRED"};
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
  if (!policy || policy.policy_id !== "instagram.publish" || policy.version !== 2) {
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

  const forbidden = Array.isArray(context.forbidden_effects) ? context.forbidden_effects : [];
  const blocked = forbidden.filter((value) => policy.forbidden_effects.includes(value));
  if (blocked.length) {
    return finish(policy, context, "DENY", "FORBIDDEN_EFFECT", ...blocked.map((value) => "FORBIDDEN:" + value));
  }

  const legacy = legacyAuthorizationState(policy, context);
  if (legacy.present) {
    const legacyBindingsValid = (
      CONTENT_ID.test(context.content_id || "") &&
      HEX64.test(context.package_sha256 || "") &&
      Array.isArray(context.media_sha256s) &&
      context.media_sha256s.length >= 1 &&
      context.media_sha256s.length <= 10 &&
      context.media_sha256s.every((value) => HEX64.test(value || ""))
    );
    if (!legacyBindingsValid) return finish(policy, context, "DENY", "LEGACY_BINDINGS_INVALID");
    if (!legacy.valid) return finish(policy, context, "DENY", "LEGACY_AUTHORIZATION_INVALID_OR_EXPIRED");
    return finish(policy, context, "ALLOW", "LEGACY_COMPATIBILITY");
  }

  if (!exactBindingsValid(context)) {
    return finish(policy, context, "DENY", "EXACT_BINDINGS_INVALID");
  }

  const ready = contentReadyState(policy, context);
  if (!ready.valid) {
    return finish(policy, context, "DENY", ready.reason || "CONTENT_READY_INVALID");
  }
  const readinessReason = ready.legacy ? "CONTENT_READY_LEGACY_GATE_COMPATIBILITY" : "CONTENT_READY_PASS";

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
    return finish(policy, context, "ALLOW", readinessReason, "EXACT_OWNER_APPROVAL");
  }

  if (context.standing_authorization === true) {
    if (risk === policy.risk.standing_authorization_max) {
      return finish(policy, context, "ALLOW", readinessReason, "STANDING_AUTHORIZATION");
    }
    return finish(policy, context, "REQUIRE_OWNER_APPROVAL", readinessReason, "RISK_EXCEEDS_STANDING_AUTHORIZATION");
  }

  return finish(policy, context, policy.authorization.default, readinessReason, "OWNER_APPROVAL_REQUIRED");
}

export function validateDecisionReceipt(policy, context, decisionResult) {
  if (!decisionResult || typeof decisionResult !== "object") return false;
  const fresh = evaluateInstagramPublish(policy, context);
  return JSON.stringify(fresh) === JSON.stringify(decisionResult);
}
