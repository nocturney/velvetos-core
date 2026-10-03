#!/usr/bin/env python3
"""Validate VelvetOS runtime contracts with dependency-scoped live proof.

Default invocation proves CODE_VALID only. Live receipt freshness/health is
required only when a caller explicitly requests a deployment/runtime/
external-action/acceptance scope and names the runtime component(s) it depends
on.

Examples:
  python scripts/check-runtime-doctor.py
  python scripts/check-runtime-doctor.py --scope deployment --require-component github
  python scripts/check-runtime-doctor.py --scope runtime --require-component edge-execution
  python scripts/check-runtime-doctor.py --scope external_action --require-component google-drive
  python scripts/check-runtime-doctor.py --strict   # legacy repository-wide live proof
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vf_runtime_receipt_policy import (  # noqa: E402
    CODE_SCOPE,
    LIVE_SCOPES,
    RuntimeProofRequest,
    build_runtime_proof_request,
    proof_scope_line,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages/vfharness/runtime/expected-components.json"
RECEIPTS = ROOT / "packages/vfharness/state/runtime"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def inspect_receipt(receipt_id: str, max_age_hours: float) -> tuple[bool, str]:
    """Strictly inspect one receipt because a live dependency was requested."""

    path = RECEIPTS / f"{receipt_id}.json"
    if not path.is_file():
        return False, f"{receipt_id}: missing receipt"
    try:
        receipt = load_json(path)
    except Exception as exc:
        return False, f"{receipt_id}: invalid receipt: {exc}"
    if receipt.get("component_id") != receipt_id:
        return False, f"{receipt_id}: component_id mismatch"
    state = receipt.get("state")
    if state not in {"healthy", "degraded", "blocked"}:
        return False, f"{receipt_id}: invalid state={state!r}"
    observed = parse_time(receipt.get("observed_at"))
    if observed is None:
        return False, f"{receipt_id}: missing/invalid observed_at"
    if not receipt.get("evidence"):
        return False, f"{receipt_id}: missing evidence"
    age_hours = (datetime.now(timezone.utc) - observed).total_seconds() / 3600
    if age_hours < -0.25:
        return False, f"{receipt_id}: observed_at is in the future"
    if state != "healthy":
        return False, f"{receipt_id}: state={state}"
    if age_hours > max_age_hours:
        return False, f"{receipt_id}: stale age={age_hours:.1f}h max={max_age_hours:g}h"
    return True, f"{receipt_id}: healthy age={age_hours:.1f}h"


def _builtin_proof(component: dict[str, Any]) -> tuple[bool, str]:
    cid = component.get("id")
    kind = component.get("kind")
    if kind == "git" and cid == "repo-main":
        probe = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if probe.returncode == 0 and len(probe.stdout.strip()) == 40:
            return True, f"{cid}: git HEAD valid"
        return False, "repo-main: git HEAD proof failed"
    return False, f"{cid}: unsupported builtin proof"


def _request_from_cli(argv: list[str] | None = None) -> RuntimeProofRequest:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=sorted({CODE_SCOPE, *LIVE_SCOPES}))
    parser.add_argument(
        "--require-component",
        action="append",
        default=[],
        metavar="ID",
        help="runtime manifest component required by this live claim; repeatable",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="legacy compatibility: repository-wide runtime proof (all components)",
    )
    args = parser.parse_args(argv)

    if args.strict and (args.scope or args.require_component):
        parser.error("--strict is the legacy all-components mode; do not combine it with --scope/--require-component")

    legacy_env = os.environ.get("VF_RUNTIME_STRICT", "").strip() == "1"
    if args.strict or legacy_env:
        return build_runtime_proof_request(
            scope="runtime",
            required_components=("*",),
            legacy_repository_wide=True,
        )

    try:
        return build_runtime_proof_request(
            scope=args.scope,
            required_components=args.require_component or None,
        )
    except ValueError as exc:
        parser.error(str(exc))


def validate(request: RuntimeProofRequest) -> tuple[int, list[str]]:
    lines: list[str] = [proof_scope_line(request)]
    if not MANIFEST.is_file():
        return 1, lines + ["FAIL missing expected-components.json"]
    try:
        data = load_json(MANIFEST)
    except Exception as exc:
        return 1, lines + [f"FAIL invalid manifest: {exc}"]
    if data.get("schema") != "vf.runtime.expected.v2":
        return 1, lines + ["FAIL unsupported runtime manifest schema"]

    components = data.get("components") or []
    if not isinstance(components, list) or not components:
        return 1, lines + ["FAIL manifest has no components"]

    errors: list[str] = []
    degraded: list[str] = []
    seen: set[str] = set()
    component_by_id: dict[str, dict[str, Any]] = {}

    for component in components:
        if not isinstance(component, dict):
            errors.append("component entry must be object")
            continue
        cid = component.get("id")
        kind = component.get("kind")
        if not isinstance(cid, str) or not cid or not isinstance(kind, str) or not kind:
            errors.append("component missing id/kind")
            continue
        if cid in seen:
            errors.append(f"duplicate component id {cid}")
        seen.add(cid)
        component_by_id[cid] = component
        if not component.get("evidence"):
            errors.append(f"{cid}: missing evidence type")
        any_of = component.get("anyOf")
        if any_of is not None and (
            not isinstance(any_of, list)
            or not any_of
            or not all(isinstance(x, str) and x for x in any_of)
        ):
            errors.append(f"{cid}: invalid anyOf")

    # CODE_VALID proves repository/runtime contract structure but intentionally
    # does not consume current provider/connector/host receipts.
    repo_main = component_by_id.get("repo-main")
    if repo_main and repo_main.get("proofMode") == "builtin":
        ok, detail = _builtin_proof(repo_main)
        if not ok:
            errors.append(detail)

    if request.scope == CODE_SCOPE:
        if request.required_components:
            errors.append("CODE_VALID cannot declare runtime components; choose a live proof scope")
        if errors:
            return 1, lines + ["FAIL " + e for e in errors]
        lines.append(
            f"OK runtime proof status=CODE_VALID schema=v2 components={len(components)} "
            "runtime_health=NOT_REQUIRED"
        )
        return 0, lines

    # Live claims must name their dependency surface. The legacy --strict/all
    # mode is the only repository-wide exception.
    requested = set(request.required_components)
    if not requested:
        errors.append(
            "live proof scope requires explicit runtime dependencies via "
            "--require-component or VF_RUNTIME_REQUIRED_COMPONENTS"
        )
    if "*" in requested:
        selected_ids = set(component_by_id)
    else:
        unknown = requested - set(component_by_id)
        if unknown:
            errors.append("unknown required runtime component(s): " + ", ".join(sorted(unknown)))
        selected_ids = requested & set(component_by_id)

    default_age = float(data.get("receiptFreshnessDefaultHours", 24))
    RECEIPTS.mkdir(parents=True, exist_ok=True)

    legacy_all = request.legacy_repository_wide and "*" in requested

    for cid in sorted(selected_ids):
        component = component_by_id[cid]
        legacy_optional = legacy_all and component.get("required") is False

        if component.get("proofMode") == "builtin":
            ok, detail = _builtin_proof(component)
            if not ok:
                (degraded if legacy_optional else errors).append(detail)
            continue

        max_age = float(component.get("maxAgeHours", default_age))
        any_of = component.get("anyOf")
        if any_of:
            checks = [inspect_receipt(member, max_age) for member in any_of]
            if any(ok for ok, _ in checks):
                healthy = [message for ok, message in checks if ok]
                unhealthy = [message for ok, message in checks if not ok]
                if unhealthy:
                    degraded.append(f"{cid}: fallback healthy via {healthy[0]}; " + "; ".join(unhealthy))
                continue
            detail = f"{cid}: no healthy member (" + "; ".join(message for _, message in checks) + ")"
            (degraded if legacy_optional else errors).append(detail)
            continue

        receipt_id = str(component.get("receipt") or cid)
        ok, detail = inspect_receipt(receipt_id, max_age)
        if not ok:
            (degraded if legacy_optional else errors).append(f"{cid}: {detail}")

    if errors:
        lines.extend("FAIL " + e for e in errors)
        if degraded:
            lines.append("DEGRADED " + "; ".join(degraded))
        return 1, lines

    if degraded:
        lines.append("DEGRADED " + "; ".join(degraded))

    required_label = ",".join(sorted(selected_ids)) or "none"
    lines.append(
        f"OK runtime proof status={request.status} scope={request.scope} "
        f"required={required_label}"
    )
    return 0, lines


def main(argv: list[str] | None = None, *, request: RuntimeProofRequest | None = None) -> int:
    try:
        resolved = request or _request_from_cli(argv)
    except ValueError as exc:
        print(f"FAIL runtime proof request: {exc}", file=sys.stderr)
        return 1
    code, lines = validate(resolved)
    stream = sys.stderr if code else sys.stdout
    for line in lines:
        print(line, file=stream)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
