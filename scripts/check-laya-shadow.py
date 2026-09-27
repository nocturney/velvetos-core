#!/usr/bin/env python3
"""Deterministic guard for the Phase 6 Laya shadow evidence."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "packages" / "vfharness" / "evals" / "laya-shadow-dataset.jsonl"
RECEIPT = ROOT / "packages" / "vfharness" / "state" / "laya-shadow-2026-09-27.json"
CALIBRATION = ROOT / "packages" / "vfharness" / "state" / "laya-shadow-calibration-2026-09-27.json"
ASSESSMENT = ROOT / "packages" / "vfharness" / "state" / "laya-shadow-assessment-2026-09-27.json"
PREFLIGHT = ROOT / "packages" / "vfharness" / "cost-preflight" / "laya-0.3.20.json"
RUNNER = ROOT / "scripts" / "run-laya-shadow.py"

LABELS = {
    "domain": {"office", "velvet-factory", "development", "media", "system", "unknown"},
    "action": {"read", "analyse", "generate", "write", "execute", "publish"},
    "escalation": {"no-model", "local/small", "reasoning/frontier capability"},
}
HEBREW_RE = re.compile(r"[\u0590-\u05FF]")


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
def main() -> None:
    if not DATASET.is_file():
        fail("missing Laya dataset")
    rows = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(rows) != 78:
        fail(f"unexpected dataset size {len(rows)}")
    ids = [row.get("id") for row in rows]
    if len(ids) != len(set(ids)):
        fail("duplicate dataset ids")
    for row in rows:
        for task, allowed in LABELS.items():
            if row.get(task) not in allowed:
                fail(f"{row.get('id')} invalid {task}={row.get(task)!r}")
    hebrew = sum(bool(HEBREW_RE.search(row.get("text", ""))) for row in rows)
    if hebrew != 72:
        fail(f"Hebrew representation changed: {hebrew}/78")
    domain_counts = Counter(row["domain"] for row in rows)
    if set(domain_counts.values()) != {13}:
        fail(f"domain balance changed: {dict(domain_counts)}")

    receipt = load_json(RECEIPT)
    calibration = load_json(CALIBRATION)
    assessment = load_json(ASSESSMENT)
    preflight = load_json(PREFLIGHT)

    if receipt.get("state") != "SHADOW":
        fail("measurement receipt is not SHADOW")
    authority = receipt.get("authority", {})
    if any(authority.get(key) is not False for key in (
        "execution_authority", "authorization_authority", "production_routing_authority"
    )):
        fail("Laya receipt gained authority")
    if receipt.get("dataset", {}).get("n") != len(rows):
        fail("receipt dataset size mismatch")
    if receipt.get("dataset", {}).get("hebrew_script_rows") != hebrew:
        fail("receipt Hebrew count mismatch")
    if assessment.get("state") != "SHADOW_NOT_PROMOTED":
        fail("assessment state changed")
    if assessment.get("promotion_decision") != "STAY_SHADOW_NOT_PROMOTED":
        fail("Laya was promoted without a new evidence gate")
    if assessment.get("authority", {}).get("velvetos_hard_rules_above_laya") is not True:
        fail("VelvetOS authority invariant missing")
    for key in ("execution_authority", "authorization_authority", "production_routing_authority"):
        if assessment.get("authority", {}).get(key) is not False:
            fail(f"assessment authority violation: {key}")
    criterion = assessment.get("promotion_criterion", {})
    if criterion.get("fresh_holdout_required") is not True or len(criterion.get("requirements", [])) < 5:
        fail("promotion criterion is incomplete")

    cases_blob = json.dumps(
        receipt.get("cases", []),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    cases_hash = hashlib.sha256(cases_blob).hexdigest()
    expected_hash = assessment.get("repeatability", {}).get("canonical_cases_sha256")
    if cases_hash != expected_hash:
        fail(f"measurement cases hash mismatch {cases_hash}")
    if assessment.get("repeatability", {}).get("cases_equal") is not True:
        fail("repeatability evidence is not PASS")

    if calibration.get("state") != "SHADOW_CALIBRATION_EVIDENCE":
        fail("calibration receipt state mismatch")
    if not str(calibration.get("deployment_effect", "")).startswith("NONE"):
        fail("calibration was deployed despite shadow-only decision")
    if not str(calibration.get("authorization_effect", "")).startswith("NONE"):
        fail("calibration changed authorization")
    if preflight.get("classification") != "FREE_LOCAL":
        fail("Laya cost classification changed")
    if preflight.get("expected_recurring_cost") != "0 ILS/month incremental":
        fail("Laya recurring cost invariant changed")
    if assessment.get("incremental_recurring_cost_ils") != 0:
        fail("assessment recurring cost changed")

    runner = RUNNER.read_text(encoding="utf-8")
    forbidden = (
        "import subprocess",
        "import requests",
        "mcp__",
        "tools.",
        '"authorization_authority": True',
        '"execution_authority": True',
        '"production_routing_authority": True',
    )
    for marker in forbidden:
        if marker in runner:
            fail(f"runner contains forbidden capability marker: {marker}")

    measured = assessment.get("measured_baseline", {})
    if measured.get("escalation_accuracy", 1.0) >= measured.get("trivial_majority_accuracy", {}).get("escalation", 0.0):
        fail("assessment no longer captures the observed escalation-under-majority blocker")

    print(
        "OK laya-shadow "
        f"cases={len(rows)} hebrew={hebrew} state=SHADOW_NOT_PROMOTED "
        f"repeatability={cases_hash[:12]} cost=0 authority=false"
    )


if __name__ == "__main__":
    main()
