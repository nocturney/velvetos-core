#!/usr/bin/env python3
"""Test the runtime-receipt age policy in both modes, against temp fixtures only.

Expired-but-otherwise-valid receipts WARN on pull_request CI and local runs and FAIL
on push/schedule/workflow_dispatch or with VF_RUNTIME_RECEIPTS_STRICT=1. Missing,
malformed, mismatched, future-dated and non-healthy receipts FAIL in every mode.
No network, no repo writes.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from vf_runtime_receipt_policy import receipt_age_policy  # noqa: E402

CONTEXT_KEYS = ("GITHUB_ACTIONS", "GITHUB_EVENT_NAME", "VF_RUNTIME_RECEIPTS_STRICT")
PR = {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "pull_request"}
LOCAL: dict[str, str] = {}
STRICT_CONTEXTS = {
    "push": {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "push"},
    "schedule": {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "schedule"},
    "workflow_dispatch": {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "workflow_dispatch"},
    "pr+override": {**PR, "VF_RUNTIME_RECEIPTS_STRICT": "1"},
    "local+override": {"VF_RUNTIME_RECEIPTS_STRICT": "1"},
}
SOFT_CONTEXTS = {"pull_request": PR, "local": LOCAL}


def fail(msg: str) -> None:
    print("FAIL runtime-receipt-age-policy: " + msg, file=sys.stderr)
    raise SystemExit(1)


def load_doctor():
    spec = importlib.util.spec_from_file_location("vf_runtime_doctor_under_test", ROOT / "scripts/check-runtime-doctor.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def iso(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def receipt(cid: str, hours_ago: float, state: str = "healthy") -> dict:
    return {"component_id": cid, "state": state, "observed_at": iso(hours_ago), "evidence": {"source": "fixture"}}


def run_doctor(doctor, tmp: Path, receipts: dict[str, object], context: dict[str, str]) -> tuple[int, str]:
    rdir = tmp / "receipts"
    rdir.mkdir(parents=True, exist_ok=True)
    for old in rdir.glob("*.json"):
        old.unlink()
    for cid, body in receipts.items():
        text = body if isinstance(body, str) else json.dumps(body)
        (rdir / f"{cid}.json").write_text(text, encoding="utf-8")
    manifest = tmp / "expected-components.json"
    manifest.write_text(json.dumps({
        "schema": "vf.runtime.expected.v2",
        "receiptFreshnessDefaultHours": 24,
        "components": [
            {"id": "alpha", "kind": "service", "required": True, "evidence": "receipt", "maxAgeHours": 24},
            {"id": "edge", "kind": "host", "required": True, "evidence": "receipt", "anyOf": ["edge-a", "edge-b"], "maxAgeHours": 24},
        ],
    }), encoding="utf-8")
    doctor.MANIFEST, doctor.RECEIPTS, doctor.STRICT = manifest, rdir, True
    saved = {key: os.environ.get(key) for key in CONTEXT_KEYS}
    out = io.StringIO()
    try:
        for key in CONTEXT_KEYS:
            os.environ.pop(key, None)
        os.environ.update(context)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = doctor.main()
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return code, out.getvalue()


def main() -> int:
    # Policy matrix.
    for name, ctx in SOFT_CONTEXTS.items():
        if receipt_age_policy(ctx)[0]:
            fail(f"{name} must be soft for age-only expiry")
    for name, ctx in STRICT_CONTEXTS.items():
        if not receipt_age_policy(ctx)[0]:
            fail(f"{name} must be strict")
    if not receipt_age_policy({"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "merge_group"})[0]:
        fail("unknown GitHub events must default to strict")
    if receipt_age_policy({**PR, "VF_RUNTIME_RECEIPTS_STRICT": "0"})[0]:
        fail("only VF_RUNTIME_RECEIPTS_STRICT=1 forces strict")

    doctor = load_doctor()
    fresh = {"alpha": receipt("alpha", 1), "edge-a": receipt("edge-a", 1)}
    expired = {"alpha": receipt("alpha", 30.5), "edge-b": receipt("edge-b", 26)}
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        for name, ctx in {**SOFT_CONTEXTS, **STRICT_CONTEXTS}.items():
            code, out = run_doctor(doctor, tmp, fresh, ctx)
            if code != 0 or "WARN" in out:
                fail(f"fresh receipts must pass cleanly in {name}: {out}")

        for name, ctx in SOFT_CONTEXTS.items():
            code, out = run_doctor(doctor, tmp, expired, ctx)
            warn = [line for line in out.splitlines() if line.startswith("WARN runtime receipts expired")]
            if code != 0 or "FAIL" in out:
                fail(f"expired receipts must only warn in {name}: {out}")
            if not warn or "alpha age=30.5h max=24h" not in warn[0] or "edge-b age=26.0h" not in warn[0]:
                fail(f"warning must name each stale receipt and its age in {name}: {out}")
            if "fallback healthy via edge-b" not in out:
                fail(f"stale fallback member must still count as the healthy member in {name}: {out}")

        for name, ctx in STRICT_CONTEXTS.items():
            code, out = run_doctor(doctor, tmp, expired, ctx)
            if code == 0 or "FAIL alpha: alpha: stale age=30.5h" not in out or "edge: no healthy member" not in out:
                fail(f"expired receipts must FAIL in {name}: {out}")

        hard_cases = {
            "missing": {"edge-a": receipt("edge-a", 1)},
            "malformed": {"alpha": "{not json", "edge-a": receipt("edge-a", 1)},
            "component-mismatch": {"alpha": receipt("other", 1), "edge-a": receipt("edge-a", 1)},
            "future": {"alpha": receipt("alpha", -5), "edge-a": receipt("edge-a", 1)},
            "no-evidence": {"alpha": {**receipt("alpha", 1), "evidence": {}}, "edge-a": receipt("edge-a", 1)},
            "expired-and-degraded": {"alpha": receipt("alpha", 30, "degraded"), "edge-a": receipt("edge-a", 1)},
        }
        for case, receipts in hard_cases.items():
            for name, ctx in {**SOFT_CONTEXTS, **STRICT_CONTEXTS}.items():
                code, out = run_doctor(doctor, tmp, receipts, ctx)
                if code == 0 or "FAIL alpha" not in out:
                    fail(f"{case} receipt must FAIL in every mode, including {name}: {out}")

    print("OK runtime-receipt-age-policy soft=pull_request,local strict=push,schedule,workflow_dispatch,override hard-fail=missing,malformed,mismatch,future,no-evidence,non-healthy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
