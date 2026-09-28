#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vf_runtime_receipt_policy import receipt_age_policy, warn_line  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages/vfharness/runtime/expected-components.json"
RECEIPTS = ROOT / "packages/vfharness/state/runtime"
STRICT = os.environ.get("VF_RUNTIME_STRICT") == "1" or "--strict" in sys.argv
# Age-only expiry that was softened to a warning for this run (see vf_runtime_receipt_policy).
STALE_WARNINGS: list[str] = []


def load_json(path: Path) -> dict:
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


def inspect_receipt(receipt_id: str, max_age_hours: float, age_strict: bool = True) -> tuple[bool, str]:
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
        if age_strict:
            return False, f"{receipt_id}: stale age={age_hours:.1f}h max={max_age_hours:g}h"
        stale = f"{receipt_id} age={age_hours:.1f}h max={max_age_hours:g}h"
        if stale not in STALE_WARNINGS:
            STALE_WARNINGS.append(stale)
        return True, f"{receipt_id}: healthy but EXPIRED age={age_hours:.1f}h max={max_age_hours:g}h (warning only)"
    return True, f"{receipt_id}: healthy age={age_hours:.1f}h"


def main() -> int:
    if not MANIFEST.is_file():
        print("FAIL missing expected-components.json", file=sys.stderr)
        return 1
    try:
        data = load_json(MANIFEST)
    except Exception as exc:
        print(f"FAIL invalid manifest: {exc}", file=sys.stderr)
        return 1
    if data.get("schema") != "vf.runtime.expected.v2":
        print("FAIL unsupported runtime manifest schema", file=sys.stderr)
        return 1

    components = data.get("components") or []
    if not isinstance(components, list) or not components:
        print("FAIL manifest has no components", file=sys.stderr)
        return 1
    default_age = float(data.get("receiptFreshnessDefaultHours", 24))
    age_strict, age_context = receipt_age_policy()
    STALE_WARNINGS.clear()
    errors: list[str] = []
    degraded: list[str] = []
    seen: set[str] = set()
    RECEIPTS.mkdir(parents=True, exist_ok=True)

    for component in components:
        cid = component.get("id")
        kind = component.get("kind")
        required = bool(component.get("required"))
        if not cid or not kind:
            errors.append("component missing id/kind")
            continue
        if cid in seen:
            errors.append(f"duplicate component id {cid}")
        seen.add(cid)

        if not component.get("evidence"):
            errors.append(f"{cid}: missing evidence type")
            continue
        any_of = component.get("anyOf")
        if any_of is not None and (
            not isinstance(any_of, list) or not any_of or not all(isinstance(x, str) and x for x in any_of)
        ):
            errors.append(f"{cid}: invalid anyOf")
            continue
        if not STRICT:
            continue
        if component.get("proofMode") == "builtin":
            if kind == "git" and cid == "repo-main":
                probe = subprocess.run(
                    ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                if probe.returncode != 0 or len(probe.stdout.strip()) != 40:
                    errors.append("repo-main: git HEAD proof failed")
            else:
                errors.append(f"{cid}: unsupported builtin proof")
            continue

        max_age = float(component.get("maxAgeHours", default_age))
        if any_of:
            checks = [inspect_receipt(member, max_age, age_strict) for member in any_of]
            if any(ok for ok, _ in checks):
                healthy = [message for ok, message in checks if ok]
                unhealthy = [message for ok, message in checks if not ok]
                if unhealthy:
                    degraded.append(f"{cid}: fallback healthy via {healthy[0]}; " + "; ".join(unhealthy))
                continue
            message = f"{cid}: no healthy member (" + "; ".join(msg for _, msg in checks) + ")"
        else:
            receipt_id = str(component.get("receipt") or cid)
            ok, detail = inspect_receipt(receipt_id, max_age, age_strict)
            if ok:
                continue
            message = f"{cid}: {detail}"

        (errors if required else degraded).append(message)

    if STALE_WARNINGS:
        print(warn_line(STALE_WARNINGS, age_context))

    if errors:
        for error in errors:
            print("FAIL " + error, file=sys.stderr)
        if degraded:
            print("DEGRADED " + "; ".join(degraded))
        return 1

    if STRICT:
        if degraded:
            print("DEGRADED " + "; ".join(degraded))
        else:
            print("OK runtime strict receipts healthy")
    else:
        print(
            f"OK runtime contract schema=v2 components={len(components)}; "
            "strict proof requires --strict or VF_RUNTIME_STRICT=1"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
