#!/usr/bin/env python3
"""Dependency-scoped policy for VelvetOS runtime receipts.

Stage 4F separates three truths that used to be conflated:

* CODE_VALID: code/contracts can be validated without live runtime freshness.
* DEPLOYMENT_VALID: a deployment claim must prove the runtime components it
  actually depends on.
* RUNTIME_HEALTHY: runtime/external-action/acceptance claims must prove the
  explicitly required components are healthy and fresh.

GitHub event type is deliberately *not* an authorization/proof scope. A push or
workflow_dispatch that changes unrelated code does not become runtime-dependent
merely because it is a push or workflow_dispatch.

Compatibility:
* VF_RUNTIME_RECEIPTS_STRICT=1 remains a repository-wide live-proof override.
* VF_RUNTIME_STRICT=1 is interpreted by check-runtime-doctor.py as the same
  legacy repository-wide strict request.

For new callers use:
  VF_RUNTIME_PROOF_SCOPE=deployment|runtime|external_action|acceptance
  VF_RUNTIME_REQUIRED_COMPONENTS=github,grok-production-scheduler

or the equivalent check-runtime-doctor.py CLI flags.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

SCOPE_ENV = "VF_RUNTIME_PROOF_SCOPE"
COMPONENTS_ENV = "VF_RUNTIME_REQUIRED_COMPONENTS"
LEGACY_STRICT_ENV = "VF_RUNTIME_RECEIPTS_STRICT"

CODE_SCOPE = "code"
LIVE_SCOPES = {"deployment", "runtime", "external_action", "acceptance"}
VALID_SCOPES = {CODE_SCOPE, *LIVE_SCOPES}
STATUS_BY_SCOPE = {
    "code": "CODE_VALID",
    "deployment": "DEPLOYMENT_VALID",
    "runtime": "RUNTIME_HEALTHY",
    "external_action": "RUNTIME_HEALTHY",
    "acceptance": "RUNTIME_HEALTHY",
}


@dataclass(frozen=True)
class RuntimeProofRequest:
    scope: str
    status: str
    runtime_health_required: bool
    required_components: tuple[str, ...]
    source: str
    legacy_repository_wide: bool = False

    def requires_component(self, component_id: str, *, implied_if_live: bool = False) -> bool:
        if not self.runtime_health_required:
            return False
        components = set(self.required_components)
        if "*" in components:
            return True
        if components:
            return component_id in components
        return implied_if_live


def _parse_components(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    values: list[str] = []
    for token in raw.replace(";", ",").split(","):
        value = token.strip()
        if value and value not in values:
            values.append(value)
    return tuple(values)


def build_runtime_proof_request(
    env: Mapping[str, str] | None = None,
    *,
    scope: str | None = None,
    required_components: Iterable[str] | None = None,
    legacy_repository_wide: bool = False,
) -> RuntimeProofRequest:
    """Resolve the requested proof scope without consulting GitHub event type.

    Invalid scopes fail closed via ValueError. Live scopes may intentionally have
    no component list at this layer; a component-specific checker may imply its
    own component. Repository-wide doctor calls must provide dependencies or use
    an explicit legacy all-components override.
    """

    env = os.environ if env is None else env
    legacy_env = env.get(LEGACY_STRICT_ENV, "").strip() == "1"
    legacy_all = legacy_repository_wide or legacy_env

    raw_scope = (scope if scope is not None else env.get(SCOPE_ENV, "")).strip().lower()
    if legacy_all:
        resolved_scope = "runtime"
        source = "legacy repository-wide strict override"
    else:
        resolved_scope = raw_scope or CODE_SCOPE
        source = f"{SCOPE_ENV}={resolved_scope}" if raw_scope else "default code validation"

    if resolved_scope not in VALID_SCOPES:
        raise ValueError(
            f"invalid {SCOPE_ENV}={resolved_scope!r}; expected one of {sorted(VALID_SCOPES)}"
        )

    if required_components is None:
        components = _parse_components(env.get(COMPONENTS_ENV))
    else:
        normalized: list[str] = []
        for item in required_components:
            value = str(item).strip()
            if value and value not in normalized:
                normalized.append(value)
        components = tuple(normalized)

    if legacy_all:
        # Legacy strict has always meant repository-wide proof. Never allow a
        # stale VF_RUNTIME_REQUIRED_COMPONENTS value to silently narrow it.
        components = ("*",)

    return RuntimeProofRequest(
        scope=resolved_scope,
        status=STATUS_BY_SCOPE[resolved_scope],
        runtime_health_required=resolved_scope in LIVE_SCOPES,
        required_components=components,
        source=source,
        legacy_repository_wide=legacy_all,
    )


def receipt_age_policy(
    env: Mapping[str, str] | None = None,
    *,
    component_id: str | None = None,
    implied_if_live: bool = False,
) -> tuple[bool, str]:
    """Return (strict, context) for age-based expiry of one dependency.

    This preserves the old helper shape while moving strictness from GitHub
    event type to dependency scope.
    """

    request = build_runtime_proof_request(env)
    if component_id is None:
        strict = request.runtime_health_required and (
            request.legacy_repository_wide or bool(request.required_components)
        )
    else:
        strict = request.requires_component(component_id, implied_if_live=implied_if_live)
    context = (
        f"scope={request.scope} status={request.status} "
        f"required={','.join(request.required_components) or 'none'} source={request.source}"
    )
    return strict, context


def warn_line(stale: list[str], context: str) -> str:
    return (
        "WARN runtime receipts expired (age-only; live dependency not required for this proof; "
        + context
        + "): "
        + "; ".join(stale)
    )


def proof_scope_line(request: RuntimeProofRequest) -> str:
    return (
        f"RUNTIME_PROOF scope={request.scope} status={request.status} "
        f"runtime_health_required={'true' if request.runtime_health_required else 'false'} "
        f"required_components={','.join(request.required_components) or 'none'}"
    )
