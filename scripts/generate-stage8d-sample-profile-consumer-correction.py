#!/usr/bin/env python3
"""Generate Stage 8D correction evidence for a hidden legacy sample consumer.

This receipt does not delete the legacy sample. It records that PR #529's
sample rollback-window closure was based on an incomplete exact-string scan,
migrates the hidden public-CTA sensor to canonical instance authority, and
reopens the rollback observation window until fresh downstream evidence exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-sample-profile-consumer-correction.json"
STAGE8C = REPORTS / "stage8c-sample-profile-consumers.json"
CLOSURE = REPORTS / "stage8d-sample-profile-rollback-closure.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"

LEGACY = "/".join(["packages", "velvetos", "samples", "velvet-factory.json"])
CANONICAL = "/".join(["instances", "velvet-factory", "instance", "velvet-factory.json"])
HIDDEN_CONSUMER = "scripts/check-public-cta.py"
CODE_SUFFIXES = {".py", ".json", ".yml", ".yaml", ".js", ".mjs", ".ps1", ".sh", ".bat", ".mdc"}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def git_bytes(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def git_text(sha: str, rel: str) -> str:
    return git_bytes(sha, rel).decode("utf-8-sig", errors="replace")


def git_json(sha: str, rel: str) -> dict[str, Any]:
    obj = json.loads(git_text(sha, rel))
    require(isinstance(obj, dict), f"{rel}@{sha} must be a JSON object")
    return obj


def csha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def candidate_paths(sha: str) -> list[str]:
    """Return tracked files mentioning the distinctive legacy filename.

    This narrows semantic inspection to a small Git-native candidate set while
    still catching assembled paths such as ROOT / "packages" / ... / "samples".
    """
    proc = subprocess.run(
        [
            "git", "grep", "-l", "-F", "velvet-factory.json", sha, "--", ".",
            ":(exclude)packages/velvetos/policy/reports/*",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or "git grep candidate scan failed")
    prefix = f"{sha}:"
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        rel = line.strip().replace("\\", "/")
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
        if rel:
            paths.append(rel)
    return sorted(set(paths))


def is_semantic_legacy_reference(text: str) -> bool:
    low = text.lower().replace("\\", "/")
    if LEGACY.lower() in low:
        return True
    has_sample_dir = (
        '"samples"' in low
        or "'samples'" in low
        or "samples/" in low
        or "/samples" in low
    )
    return (
        has_sample_dir
        and "velvet-factory.json" in low
        and ("packages" in low or "velvetos" in low)
    )


def classify_semantic_refs(sha: str) -> dict[str, list[str]]:
    evidence: list[str] = []
    active: list[str] = []
    for rel in candidate_paths(sha):
        if rel.startswith("packages/velvetos/policy/reports/"):
            continue
        if Path(rel).suffix.lower() not in CODE_SUFFIXES:
            continue
        try:
            text = git_text(sha, rel)
        except subprocess.CalledProcessError:
            continue
        if not is_semantic_legacy_reference(text):
            continue
        if rel == "scripts/check-policy-architecture.py" or rel.startswith("scripts/generate-stage8"):
            evidence.append(rel)
        else:
            active.append(rel)
    return {"evidence": sorted(set(evidence)), "active": sorted(set(active))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    for label, value in (("prepared-against", args.prepared_against), ("source-commit", args.source_commit)):
        require(re.fullmatch(r"[0-9a-f]{40}", value) is not None, f"--{label} must be a full lowercase Git SHA")

    stage8c = git_json(args.prepared_against, STAGE8C.relative_to(ROOT).as_posix())
    closure = git_json(args.prepared_against, CLOSURE.relative_to(ROOT).as_posix())
    policy_before = git_json(args.prepared_against, POLICY.relative_to(ROOT).as_posix())
    policy_after = git_json(args.source_commit, POLICY.relative_to(ROOT).as_posix())
    legacy_before = git_json(args.prepared_against, LEGACY)
    legacy_after = git_json(args.source_commit, LEGACY)
    canonical_after = git_json(args.source_commit, CANONICAL)

    require(stage8c.get("repository_acceptance") == "PASS", "historical Stage 8C sample receipt must remain PASS")
    require(closure.get("repository_assessment") == "PASS", "PR #529 closure receipt must exist and PASS")
    require(closure.get("rollback_window_closed") is True, "PR #529 closure did not record a closed window")
    require(closure.get("delete_authorized") is False, "PR #529 must not have authorized deletion")

    before = classify_semantic_refs(args.prepared_against)
    after = classify_semantic_refs(args.source_commit)
    require(HIDDEN_CONSUMER in before["active"], "prepared-against main does not expose the hidden CTA consumer")
    require(HIDDEN_CONSUMER not in after["active"], "hidden CTA consumer still references the legacy sample")
    require(after["active"] == [], f"active semantic legacy sample refs remain: {after['active']}")

    consumer_before = git_text(args.prepared_against, HIDDEN_CONSUMER)
    consumer_after = git_text(args.source_commit, HIDDEN_CONSUMER)
    require(is_semantic_legacy_reference(consumer_before), "hidden consumer proof is not reproducible")
    require(not is_semantic_legacy_reference(consumer_after), "corrected CTA sensor still semantically references legacy sample")
    require("instance_path" in consumer_after, "corrected CTA sensor lost canonical instance validation")

    require(csha(legacy_before) == csha(legacy_after), "legacy sample changed during hidden-consumer correction")
    require(
        set(legacy_after.get("modulesEnabled") or []) == set(canonical_after.get("modulesEnabled") or []),
        "canonical/legacy module parity changed during correction",
    )
    policy_sha_before = csha(policy_before)
    policy_sha_after = csha(policy_after)
    require(policy_sha_before == policy_sha_after, "external-effect policy authority changed")

    criteria = {
        "historical_stage8c_receipt_is_preserved": True,
        "pr529_closure_receipt_is_preserved_as_historical_evidence": True,
        "hidden_consumer_is_detected_by_semantic_scan": True,
        "hidden_consumer_is_migrated_to_canonical_instance_only": True,
        "no_active_semantic_legacy_sample_consumers_remain": True,
        "legacy_sample_remains_present_and_unchanged": True,
        "canonical_legacy_module_parity_is_preserved": True,
        "external_effect_authority_is_unchanged": True,
        "previous_rollback_closure_is_superseded_not_used_for_deletion": True,
        "rollback_window_is_reopened_for_fresh_downstream_observation": True,
        "delete_authority_remains_false": True,
    }

    report = {
        "schema": "velvetos.stage8d-sample-profile-consumer-correction.v1",
        "stage": "8D_SAMPLE_PROFILE_CONSUMER_CORRECTION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "surface_id": "sample_profile",
        "path": LEGACY,
        "canonical_path": CANONICAL,
        "purpose": (
            "Correct an exact-string consumer-scan blind spot discovered after PR #529. "
            "Migrate the hidden public-CTA validation consumer to canonical instance authority, "
            "supersede the prior rollback-window closure for deletion purposes, and reopen the "
            "observation window without deleting the legacy sample."
        ),
        "discovery": {
            "previous_closure_receipt": CLOSURE.relative_to(ROOT).as_posix(),
            "previous_closure_pull_request": 529,
            "scan_blind_spot": "LEGACY_PATH_ASSEMBLED_FROM_PATH_SEGMENTS",
            "hidden_consumer": HIDDEN_CONSUMER,
            "prepared_against_active_semantic_refs": before["active"],
            "prepared_against_evidence_refs": before["evidence"],
        },
        "correction": {
            "hidden_consumer_migrated": True,
            "canonical_instance_validation_retained": True,
            "active_semantic_legacy_refs_after": after["active"],
            "evidence_refs_after": after["evidence"],
            "legacy_present_after_correction": True,
            "legacy_unchanged": True,
            "canonical_legacy_module_parity": True,
        },
        "rollback_window": {
            "previous_closure_receipt_preserved": True,
            "previous_closure_superseded_for_retirement": True,
            "reopened": True,
            "closed": False,
            "closure_evidence": None,
            "reclosure_requires_fresh_downstream_main_full_suite_observation": True,
        },
        "acceptance_criteria": criteria,
        "repository_assessment": "PASS",
        "rollback_window_closed": False,
        "retirement_ready_for_deletion_gate": False,
        "delete_authorized": False,
        "retirement_authorized": False,
        "next_action": (
            "Merge this correction, verify main post-merge, then collect fresh downstream main full-suite "
            "observations after the hidden-consumer cutover. Only a new explicit rollback re-closure receipt "
            "may make sample_profile eligible for a later isolated deletion gate."
        ),
        "authority": {
            "policy_registry_sha256": policy_sha_after,
            "prepared_against_policy_registry_sha256": policy_sha_before,
            "external_effect_authority_changed": False,
        },
        "constraints": [
            "do not delete the legacy sample in this correction",
            "PR #529 closure is historical evidence but is superseded for retirement authority",
            "rollback re-closure requires fresh post-correction evidence",
            "no big-bang delete",
            "external-effect authority must remain unchanged",
        ],
    }

    require(all(criteria.values()), "sample consumer correction acceptance criteria failed")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_SAMPLE_CONSUMER_CORRECTION "
        f"assessment={report['repository_assessment']} "
        f"active_before={len(before['active'])} active_after={len(after['active'])} "
        f"rollback_closed={report['rollback_window_closed']} delete_authorized={report['delete_authorized']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
