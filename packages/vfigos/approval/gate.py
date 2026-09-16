"""Authoritative mutation-boundary gate: verify then atomic claim, then allow Graph.

Preflight uses verify_receipt only (advisory). This module is required before
any Instagram write mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .keys_registry import KeyRegistry
from .spend import ClaimResult, SpendStore
from .verify import VerifyResult, verify_receipt


@dataclass
class GateResult:
    ok: bool
    stage: str  # verified | claimed | blocked
    problems: list[str] = field(default_factory=list)
    verify: VerifyResult | None = None
    claim: ClaimResult | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "stage": self.stage,
            "problems": list(self.problems),
            "verify": self.verify.as_dict() if self.verify else None,
            "claim": self.claim.as_dict() if self.claim else None,
            "delivery_authorized": self.ok,
            "mutated": False,
        }


def authorize_mutation(
    *,
    receipt: str | Mapping[str, Any] | None,
    mutation_tool: str,
    spend_store: SpendStore,
    registry: KeyRegistry,
    content_id: str | None = None,
    package_sha256: str | None = None,
    mutation_payload_sha256: str | None = None,
    media_sha256s: list[str] | None = None,
    ig_user_id: str | None = None,
    now: datetime | None = None,
) -> GateResult:
    """Verify receipt bindings then atomically claim approval_id before Graph I/O."""
    if receipt is None or receipt == "":
        return GateResult(
            ok=False,
            stage="blocked",
            problems=["no delivery approval receipt"],
        )

    vr = verify_receipt(
        receipt,
        registry=registry,
        expected_mutation_tool=mutation_tool,
        expected_content_id=content_id,
        expected_package_sha256=package_sha256,
        expected_mutation_payload_sha256=mutation_payload_sha256,
        expected_media_sha256s=media_sha256s,
        expected_ig_user_id=ig_user_id,
        now=now,
    )
    if not vr.ok:
        return GateResult(ok=False, stage="blocked", problems=list(vr.problems), verify=vr)

    approval_id = vr.claims["approval_id"]
    claim = spend_store.claim(
        approval_id,
        meta={
            "mutation_tool": mutation_tool,
            "content_id": vr.claims.get("content_id"),
            "package_sha256": vr.claims.get("package_sha256"),
            "mutation_payload_sha256": vr.claims.get("mutation_payload_sha256"),
            "media_sha256s": vr.claims.get("media_sha256s"),
        },
    )
    if not claim.ok:
        problems = [f"approval claim failed: {claim.status}"]
        if claim.detail:
            problems.append(claim.detail)
        return GateResult(
            ok=False,
            stage="blocked",
            problems=problems,
            verify=vr,
            claim=claim,
        )
    return GateResult(ok=True, stage="claimed", verify=vr, claim=claim)
