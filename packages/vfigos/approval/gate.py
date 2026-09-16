"""Authoritative mutation-boundary gate: verify → claim → (media) → Graph.

Preflight uses verify_receipt only (advisory). This module is required before
any Instagram write mutation.

Staged trust order for media-bearing writes:
  Phase A — verify_authorization_pre_media (no media I/O, no claim)
  Phase B — claim_authorization (atomic spend; no media I/O)
  Phase C — fetch/hash media + verify_post_claim_bindings (no unclaim)
  Phase D — Graph mutation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .keys_registry import KeyRegistry
from .spend import ClaimResult, SpendStore
from .verify import VerifyResult, verify_receipt, verify_receipt_pre_media


@dataclass
class GateResult:
    ok: bool
    stage: str  # verified_pre_media | claimed | verified_post_claim | blocked
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


def verify_authorization_pre_media(
    *,
    receipt: str | Mapping[str, Any] | None,
    mutation_tool: str,
    registry: KeyRegistry,
    content_id: str | None = None,
    package_sha256: str | None = None,
    ig_user_id: str | None = None,
    now: datetime | None = None,
) -> GateResult:
    """Phase A — authenticate + non-media bindings before claim or media fetch.

    Invalid / missing / forged receipts fail here with no CAS/HTTP media I/O
    and no replay spend.
    """
    if receipt is None or receipt == "":
        return GateResult(
            ok=False,
            stage="blocked",
            problems=["no delivery approval receipt"],
        )

    vr = verify_receipt_pre_media(
        receipt,
        registry=registry,
        expected_mutation_tool=mutation_tool,
        expected_content_id=content_id,
        expected_package_sha256=package_sha256,
        expected_ig_user_id=ig_user_id,
        now=now,
    )
    if not vr.ok:
        return GateResult(ok=False, stage="blocked", problems=list(vr.problems), verify=vr)
    return GateResult(ok=True, stage="verified_pre_media", verify=vr)


def claim_authorization(
    *,
    pre: GateResult,
    spend_store: SpendStore,
    mutation_tool: str,
) -> GateResult:
    """Phase B — atomic claim after Phase A. No media I/O.

    On success the approval is spent. Later media/binding/Graph failures must
    NOT unclaim — a new owner approval is required.
    """
    if not pre.ok or pre.verify is None or not pre.verify.ok:
        return GateResult(
            ok=False,
            stage="blocked",
            problems=list(pre.problems) or ["pre-media verification required before claim"],
            verify=pre.verify,
        )
    claims = pre.verify.claims
    approval_id = claims["approval_id"]
    claim = spend_store.claim(
        approval_id,
        meta={
            "mutation_tool": mutation_tool,
            "content_id": claims.get("content_id"),
            "package_sha256": claims.get("package_sha256"),
            "mutation_payload_sha256": claims.get("mutation_payload_sha256"),
            "media_sha256s": claims.get("media_sha256s"),
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
            verify=pre.verify,
            claim=claim,
        )
    return GateResult(ok=True, stage="claimed", verify=pre.verify, claim=claim)


def verify_post_claim_bindings(
    *,
    receipt: str | Mapping[str, Any],
    mutation_tool: str,
    registry: KeyRegistry,
    content_id: str | None = None,
    package_sha256: str | None = None,
    mutation_payload_sha256: str | None = None,
    media_sha256s: list[str] | None = None,
    ig_user_id: str | None = None,
    now: datetime | None = None,
) -> GateResult:
    """Phase C — verify media/payload bindings after claim. Does not claim/unclaim."""
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
    return GateResult(ok=True, stage="verified_post_claim", verify=vr)


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
    """Full verify + claim helper (tests / digests-already-known callers).

    Production media-bearing path uses staged claim-before-fetch in
    ``authorize_or_block`` instead of this combined helper.
    """
    if receipt is None or receipt == "":
        return GateResult(
            ok=False,
            stage="blocked",
            problems=["no delivery approval receipt"],
        )

    # When media/payload digests are not yet known, Phase A + claim only.
    if mutation_payload_sha256 is None and media_sha256s is None:
        pre = verify_authorization_pre_media(
            receipt=receipt,
            mutation_tool=mutation_tool,
            registry=registry,
            content_id=content_id,
            package_sha256=package_sha256,
            ig_user_id=ig_user_id,
            now=now,
        )
        if not pre.ok:
            return pre
        return claim_authorization(pre=pre, spend_store=spend_store, mutation_tool=mutation_tool)

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

    claimed = claim_authorization(
        pre=GateResult(ok=True, stage="verified_pre_media", verify=vr),
        spend_store=spend_store,
        mutation_tool=mutation_tool,
    )
    return claimed
