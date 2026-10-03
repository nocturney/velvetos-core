#!/usr/bin/env python3
"""Build/validate one CONTENT_READY evidence envelope for routine Instagram work.

CONTENT_READY is evidence, not publication authorization. It collapses the
fragmented Product Truth / brand / copy / visual QA / rights/privacy /
render-transport checks into one exact-bound envelope. policy_id
instagram.publish remains the only ALLOW/DENY/REQUIRE_OWNER_APPROVAL authority.

CLI validation verifies evidence refs by default. --self-test uses in-memory
fixtures and performs no external I/O.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "packages" / "velvetos" / "policy" / "content-ready-test-vectors.json"

HEX64 = re.compile(r"^[0-9a-f]{64}$")
CONTENT_ID = re.compile(r"^[A-Za-z0-9._-]{3,120}$")
EVIDENCE_KEYS = (
    "product_truth",
    "brand",
    "copy",
    "visual_qa",
    "rights_privacy",
    "render_transport",
)
PASS_VALUES = {"PASS", "NOT_APPLICABLE"}
FAILURE_MODES = {"REPAIRABLE_QUALITY", "RETRYABLE_RUNTIME", "HARD_BLOCKER"}
QUALITY_REPAIRABLE = {"product_truth", "brand", "copy", "visual_qa"}
RUNTIME_RETRYABLE = {"render_transport"}
DEFAULT_HARD = {"rights_privacy"}


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_digest(envelope: dict[str, Any]) -> str:
    body = copy.deepcopy(envelope)
    body.pop("envelope_sha256", None)
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return digest_bytes(raw)


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _safe_ref(root: Path, ref: Any) -> Path | None:
    if not isinstance(ref, str) or not ref.strip():
        return None
    rel = Path(ref)
    if rel.is_absolute() or re.match(r"^[A-Za-z]:|^[/\\]|^[A-Za-z]+://", ref):
        return None
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None
    return path


def _binding_problems(bindings: Any, expected: dict[str, Any] | None) -> list[str]:
    problems: list[str] = []
    if not isinstance(bindings, dict):
        return ["BINDINGS_REQUIRED"]
    cid = bindings.get("content_id")
    package = bindings.get("package_sha256")
    copy_sha = bindings.get("copy_sha256")
    media = bindings.get("media_sha256s")
    if not isinstance(cid, str) or not CONTENT_ID.fullmatch(cid):
        problems.append("CONTENT_ID_INVALID")
    if not isinstance(package, str) or not HEX64.fullmatch(package):
        problems.append("PACKAGE_SHA256_INVALID")
    if not isinstance(copy_sha, str) or not HEX64.fullmatch(copy_sha):
        problems.append("COPY_SHA256_INVALID")
    if not isinstance(media, list) or not 1 <= len(media) <= 10 or any(
        not isinstance(x, str) or not HEX64.fullmatch(x) for x in (media or [])
    ):
        problems.append("MEDIA_SHA256S_INVALID")
    if expected:
        for key in ("content_id", "package_sha256", "copy_sha256"):
            if key in expected and expected[key] is not None and bindings.get(key) != expected[key]:
                problems.append(f"BINDING_MISMATCH:{key}")
        if expected.get("media_sha256s") is not None and bindings.get("media_sha256s") != expected["media_sha256s"]:
            problems.append("BINDING_MISMATCH:media_sha256s")
    return problems


def validate_envelope(
    envelope: Any,
    *,
    expected_bindings: dict[str, Any] | None = None,
    root: Path = ROOT,
    verify_refs: bool = True,
    at: datetime | None = None,
) -> dict[str, Any]:
    at = at or datetime.now(timezone.utc)
    problems: list[str] = []
    repair_targets: list[str] = []
    retry_targets: list[str] = []
    hard_blockers: list[str] = []

    if not isinstance(envelope, dict):
        return {
            "content_ready": "FAIL",
            "disposition": "HARD_BLOCKER",
            "owner_surface": "HARD_BLOCKER",
            "repair_targets": [],
            "retry_targets": [],
            "hard_blockers": ["ENVELOPE_OBJECT_REQUIRED"],
            "problems": ["ENVELOPE_OBJECT_REQUIRED"],
        }

    if envelope.get("schema_version") != "velvet.content_ready.v1":
        problems.append("SCHEMA_VERSION_INVALID")

    problems.extend(_binding_problems(envelope.get("bindings"), expected_bindings))

    validated_at = _parse_time(envelope.get("validated_at"))
    if validated_at is None:
        problems.append("VALIDATED_AT_INVALID")
    elif validated_at > at:
        problems.append("VALIDATED_AT_FUTURE")

    evidence = envelope.get("evidence")
    if not isinstance(evidence, dict):
        problems.append("EVIDENCE_OBJECT_REQUIRED")
        evidence = {}
    if set(evidence) != set(EVIDENCE_KEYS):
        problems.append("EVIDENCE_KEYSET_INVALID")

    for key in EVIDENCE_KEYS:
        item = evidence.get(key)
        if not isinstance(item, dict):
            problems.append(f"EVIDENCE_ITEM_INVALID:{key}")
            hard_blockers.append(f"{key}:missing")
            continue
        status = item.get("status")
        ref = item.get("ref")
        sha = item.get("sha256")
        mode = item.get("failure_mode")
        reason = str(item.get("reason") or "").strip()

        if status not in {"PASS", "NOT_APPLICABLE", "FAIL", "UNKNOWN"}:
            problems.append(f"EVIDENCE_STATUS_INVALID:{key}")
        if not isinstance(ref, str) or not ref.strip():
            problems.append(f"EVIDENCE_REF_INVALID:{key}")
        if not isinstance(sha, str) or not HEX64.fullmatch(sha):
            problems.append(f"EVIDENCE_SHA_INVALID:{key}")

        if verify_refs and isinstance(ref, str) and isinstance(sha, str) and HEX64.fullmatch(sha):
            path = _safe_ref(root, ref)
            if path is None:
                problems.append(f"EVIDENCE_REF_UNSAFE:{key}")
            elif not path.is_file():
                problems.append(f"EVIDENCE_REF_MISSING:{key}")
            elif digest_file(path) != sha:
                problems.append(f"EVIDENCE_REF_DIGEST_MISMATCH:{key}")

        if status in PASS_VALUES:
            if mode not in (None, ""):
                problems.append(f"PASS_EVIDENCE_HAS_FAILURE_MODE:{key}")
            continue

        if mode not in FAILURE_MODES:
            problems.append(f"FAILURE_MODE_REQUIRED:{key}")
            if key in DEFAULT_HARD:
                hard_blockers.append(f"{key}:{reason or status}")
            continue

        if mode == "REPAIRABLE_QUALITY":
            if key not in QUALITY_REPAIRABLE:
                problems.append(f"REPAIR_MODE_NOT_ALLOWED:{key}")
                hard_blockers.append(f"{key}:{reason or status}")
            else:
                repair_targets.append(key)
        elif mode == "RETRYABLE_RUNTIME":
            if key not in RUNTIME_RETRYABLE:
                problems.append(f"RETRY_MODE_NOT_ALLOWED:{key}")
                hard_blockers.append(f"{key}:{reason or status}")
            else:
                retry_targets.append(key)
        else:
            hard_blockers.append(f"{key}:{reason or status}")

    repair_targets = list(dict.fromkeys(repair_targets))
    retry_targets = list(dict.fromkeys(retry_targets))
    hard_blockers = list(dict.fromkeys(hard_blockers))

    semantic_fail = bool(repair_targets or retry_targets or hard_blockers or problems)
    computed_status = "FAIL" if semantic_fail else "PASS"
    if envelope.get("status") != computed_status:
        problems.append("DECLARED_STATUS_MISMATCH")
        computed_status = "FAIL"

    declared_repairs = envelope.get("repair_targets")
    declared_retries = envelope.get("retry_targets")
    declared_hard = envelope.get("hard_blockers")
    declared_owner = envelope.get("owner_surface")
    if declared_repairs != repair_targets:
        problems.append("REPAIR_TARGETS_MISMATCH")
    if declared_retries != retry_targets:
        problems.append("RETRY_TARGETS_MISMATCH")
    if declared_hard != hard_blockers:
        problems.append("HARD_BLOCKERS_MISMATCH")

    owner_surface = "HARD_BLOCKER" if hard_blockers else "NONE"
    if declared_owner != owner_surface:
        problems.append("OWNER_SURFACE_MISMATCH")

    if hard_blockers:
        disposition = "HARD_BLOCKER"
    elif repair_targets:
        disposition = "TARGETED_REPAIR"
    elif retry_targets:
        disposition = "RETRY_INTERNAL"
    elif problems:
        disposition = "HARD_BLOCKER"
        owner_surface = "HARD_BLOCKER"
    else:
        disposition = "PASS"

    return {
        "content_ready": "PASS" if disposition == "PASS" else "FAIL",
        "disposition": disposition,
        "owner_surface": owner_surface,
        "repair_targets": repair_targets,
        "retry_targets": retry_targets,
        "hard_blockers": hard_blockers,
        "problems": list(dict.fromkeys(problems)),
        "envelope_sha256": canonical_digest(envelope),
        "policy_authority": "instagram.publish",
        "authorization_claimed": False,
    }


def normalize(candidate: dict[str, Any], *, root: Path = ROOT, verify_refs: bool = True) -> dict[str, Any]:
    """Derive status/repair/owner fields instead of trusting caller declarations."""
    out = copy.deepcopy(candidate)
    out.setdefault("schema_version", "velvet.content_ready.v1")
    out.setdefault("validated_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    out["status"] = "PASS"
    out["repair_targets"] = []
    out["retry_targets"] = []
    out["hard_blockers"] = []
    out["owner_surface"] = "NONE"

    # First classify evidence without declaration cross-check noise.
    evidence = out.get("evidence") if isinstance(out.get("evidence"), dict) else {}
    repairs: list[str] = []
    retries: list[str] = []
    hard: list[str] = []
    for key in EVIDENCE_KEYS:
        item = evidence.get(key) if isinstance(evidence, dict) else None
        if not isinstance(item, dict):
            hard.append(f"{key}:missing")
            continue
        if item.get("status") in PASS_VALUES:
            item["failure_mode"] = None
            continue
        mode = item.get("failure_mode")
        reason = str(item.get("reason") or item.get("status") or "failed")
        if mode == "REPAIRABLE_QUALITY" and key in QUALITY_REPAIRABLE:
            repairs.append(key)
        elif mode == "RETRYABLE_RUNTIME" and key in RUNTIME_RETRYABLE:
            retries.append(key)
        else:
            hard.append(f"{key}:{reason}")
    out["repair_targets"] = list(dict.fromkeys(repairs))
    out["retry_targets"] = list(dict.fromkeys(retries))
    out["hard_blockers"] = list(dict.fromkeys(hard))
    out["owner_surface"] = "HARD_BLOCKER" if hard else "NONE"
    out["status"] = "FAIL" if (repairs or retries or hard) else "PASS"

    result = validate_envelope(out, root=root, verify_refs=verify_refs)
    if result["problems"]:
        out["status"] = "FAIL"
    return out


def _patch(doc: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    out = copy.deepcopy(doc)
    for op in ops:
        tokens = op["path"].strip("/").split("/")
        parent: Any = out
        for token in tokens[:-1]:
            parent = parent[token]
        leaf = tokens[-1]
        if op["op"] == "replace":
            parent[leaf] = copy.deepcopy(op.get("value"))
        elif op["op"] == "remove":
            parent.pop(leaf, None)
        else:
            raise ValueError(f"unsupported patch op {op['op']}")
    return out


def self_test() -> int:
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    failures = 0
    for vector in data["vectors"]:
        candidate = _patch(data["base_envelope"], vector.get("patch_ops") or [])
        if vector.get("normalize", False):
            candidate = normalize(candidate, verify_refs=False)
        at = _parse_time(vector["evaluation_time"])
        if at is None:
            print(f"FAIL {vector['id']}: bad evaluation_time")
            failures += 1
            continue
        result = validate_envelope(candidate, verify_refs=False, at=at)
        exp = vector["expected"]
        actual = {
            "content_ready": result["content_ready"],
            "disposition": result["disposition"],
            "owner_surface": result["owner_surface"],
            "repair_targets": result["repair_targets"],
            "retry_targets": result["retry_targets"],
            "hard_blockers": result["hard_blockers"],
        }
        if actual != exp:
            print(f"FAIL {vector['id']}: expected={exp} actual={actual} problems={result['problems']}")
            failures += 1
        else:
            print(f"PASS {vector['id']} {result['disposition']}")
    if failures:
        return 1
    print(f"OK content-ready vectors={len(data['vectors'])} authority=instagram.publish owner_prompt_on_quality_failure=NO")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="candidate/envelope JSON")
    parser.add_argument("--output", type=Path, help="write normalized envelope")
    parser.add_argument("--normalize", action="store_true", help="derive status/repair/owner fields before validation")
    parser.add_argument("--no-verify-refs", action="store_true", help="skip workspace ref/hash verification")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.input:
        parser.error("--input or --self-test is required")

    candidate = json.loads(args.input.read_text(encoding="utf-8"))
    envelope = normalize(candidate, verify_refs=not args.no_verify_refs) if args.normalize else candidate
    result = validate_envelope(envelope, verify_refs=not args.no_verify_refs)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["content_ready"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
