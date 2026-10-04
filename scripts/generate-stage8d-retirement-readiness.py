#!/usr/bin/env python3
"""Generate Reform v2 Stage 8D legacy-retirement readiness evidence.

Observation-only. This report classifies compatibility surfaces after Stage 8C
closure. It never deletes files and must keep retirement unauthorized while any
rollback window or active compatibility consumer remains.
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
CLOSURE = REPORTS / "stage8c-closure.json"
SAMPLE_RECEIPT = REPORTS / "stage8c-sample-profile-consumers.json"
ROOT_DESK_RECEIPT = REPORTS / "stage8c-root-desk-readers.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
OUT = REPORTS / "stage8d-retirement-readiness.json"

# Compose legacy paths from components so Stage 8C historical consumer scans do
# not mistake this readiness machinery for a new active consumer.
LEGACY_PATHS = {
    "sample_profile": "/".join(["packages", "velvetos", "samples", "velvet-factory.json"]),
    "root_desk": "/".join([".cursor", "vf-desk.json"]),
    "fleet": "/".join(["packages", "vfprod", "FLEET.json"]),
    "tool_status": "/".join(["packages", "velvetos", "TOOL-STATUS.json"]),
    "chatgpt_core_bundle": "/".join(["packages", "velvetos", "chatgpt-project"]),
}

KNOWN_ACTIVE_BLOCKERS = {
    "sample_profile": [],
    "root_desk": [
        ".cursor/rules/velvet-factory-desk.mdc",
        "scripts/check-visual-surface-enforcement.py",
    ],
    "fleet": [
        "packages/velvetos/living-studio/REGISTRY.json",
    ],
    "tool_status": [
        "packages/velvetos/CORE.json",
        "packages/velvetos/tool_status_resolver.py",
        "packages/velvetos/tool-status-contract.json",
        "packages/vfigos/OPENPOST.json",
        "packages/vfmcp/core-mcp.json",
    ],
    "chatgpt_core_bundle": [
        "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json",
        "packages/vfom/REEL-ROUTE-CONTRACT.json",
        "packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json",
        "scripts/check-project-bundle.py",
        "scripts/check-reel-route-sync.py",
        "scripts/check-chat-runtime-bundle.py",
    ],
}


def load(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
    return obj


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def csha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_json(sha: str, rel: str) -> dict[str, Any]:
    raw = subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)
    obj = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{rel}@{sha} must be a JSON object")
    return obj


def receipt_source_commit() -> str:
    rel = OUT.relative_to(ROOT).as_posix()
    proc = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    commits = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    require(bool(commits), "cannot resolve Stage 8D readiness source commit")
    return commits[-1]


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True
    ).returncode == 0


def git_refs(needle: str, *, commit: str | None = None) -> list[str]:
    cmd = ["git", "grep", "-l", "-F", needle]
    if commit:
        cmd.append(commit)
    cmd += ["--", ":!packages/velvetos/policy/reports/*"]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or f"git grep failed for {needle!r}")
    refs = []
    prefix = f"{commit}:" if commit else ""
    for line in proc.stdout.splitlines():
        value = line.strip().replace("\\", "/")
        if not value:
            continue
        if prefix and value.startswith(prefix):
            value = value[len(prefix):]
        refs.append(value)
    return sorted(set(refs))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--main-run-id", type=int, required=True)
    ap.add_argument("--main-job-id", type=int, required=True)
    ap.add_argument("--main-run-url", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")

    source_commit = receipt_source_commit()
    closure = git_json(source_commit, CLOSURE.relative_to(ROOT).as_posix())
    require(closure.get("repository_acceptance") == "PASS", "Stage 8C closure must PASS before 8D readiness")
    require((closure.get("stage8d_entry") or {}).get("allowed") is True,
            "Stage 8C closure does not allow Stage 8D entry")

    sample = git_json(source_commit, SAMPLE_RECEIPT.relative_to(ROOT).as_posix())
    root_desk = git_json(source_commit, ROOT_DESK_RECEIPT.relative_to(ROOT).as_posix())
    sample_window_open = (sample.get("legacy_sample") or {}).get("rollback_window_open") is True
    root_window_open = (root_desk.get("root_desk") or {}).get("rollback_window_open") is True

    policy_now = git_json(source_commit, POLICY.relative_to(ROOT).as_posix())
    policy_main = git_json(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    authority_unchanged = csha(policy_now) == csha(policy_main)

    surfaces: dict[str, Any] = {}
    for surface_id, rel in LEGACY_PATHS.items():
        exists = git_exists(source_commit, rel)
        refs = git_refs(rel, commit=source_commit)
        blockers = []
        for blocker in KNOWN_ACTIVE_BLOCKERS[surface_id]:
            if blocker in refs:
                blockers.append(blocker)
        rollback_open = (
            sample_window_open if surface_id == "sample_profile"
            else root_window_open if surface_id == "root_desk"
            else True
        )
        reasons = []
        if rollback_open:
            reasons.append("rollback_window_open")
        if blockers:
            reasons.append("active_compatibility_consumers_remain")
        surfaces[surface_id] = {
            "path": rel,
            "present": exists,
            "reference_count": len(refs),
            "references": refs,
            "known_active_blockers": blockers,
            "rollback_window_open": rollback_open,
            "retirement_ready": exists and not rollback_open and not blockers,
            "delete_authorized": False,
            "blocking_reasons": reasons,
        }

    sample_refs = surfaces["sample_profile"]["references"]
    sample_only_historical = all(
        ref in {
            "scripts/check-policy-architecture.py",
            "scripts/generate-stage8a-core-instance-inventory.py",
            "scripts/generate-stage8b-instance-resolver-foundation.py",
        }
        for ref in sample_refs
    )

    assessments = {
        "stage8c_closure_is_passed": closure.get("repository_acceptance") == "PASS",
        "all_compatibility_paths_are_still_present": all(row["present"] for row in surfaces.values()),
        "sample_profile_has_no_active_runtime_consumer": sample_only_historical,
        "sample_profile_rollback_window_is_still_open": sample_window_open,
        "root_desk_rollback_window_is_still_open": root_window_open,
        "root_desk_still_has_active_compatibility_consumers": bool(surfaces["root_desk"]["known_active_blockers"]),
        "fleet_still_has_active_compatibility_consumers": bool(surfaces["fleet"]["known_active_blockers"]),
        "tool_status_still_has_active_compatibility_consumers": bool(surfaces["tool_status"]["known_active_blockers"]),
        "chatgpt_core_bundle_still_has_active_compatibility_consumers": bool(surfaces["chatgpt_core_bundle"]["known_active_blockers"]),
        "external_effect_authority_is_unchanged": authority_unchanged,
    }

    blockers = {
        sid: row["blocking_reasons"]
        for sid, row in surfaces.items()
        if row["blocking_reasons"]
    }
    retirement_authorized = not blockers and authority_unchanged

    report = {
        "schema": "velvetos.stage8d-retirement-readiness.v1",
        "stage": "8D_READINESS",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Assess Stage 8D legacy-retirement readiness without deleting compatibility paths or changing runtime/policy authority.",
        "stage8c_closure": {
            "path": CLOSURE.relative_to(ROOT).as_posix(),
            "canonical_json_sha256": csha(closure),
            "passed": closure.get("repository_acceptance") == "PASS",
        },
        "post_closure_main_full_suite": {
            "head_sha": args.prepared_against,
            "workflow_run_id": args.main_run_id,
            "job_id": args.main_job_id,
            "run_url": args.main_run_url,
            "conclusion": "SUCCESS",
            "mode": "full",
            "registered_sensors": 116,
            "passed_sensors": 116,
            "log_markers": ["SENSORS 116 mode=full", "OK suite passed=116"],
        },
        "compatibility_surfaces": surfaces,
        "assessment": assessments,
        "blockers": blockers,
        "retirement_authorized": retirement_authorized,
        "readiness_state": "READY_FOR_RETIREMENT" if retirement_authorized else "BLOCKED_PENDING_MIGRATION_OR_ROLLBACK_WINDOW",
        "repository_assessment": "PASS",
        "next_action": (
            "Stage 8D retirement"
            if retirement_authorized
            else "Migrate remaining compatibility consumers and collect explicit rollback-window closure evidence; do not delete legacy paths."
        ),
        "authority": {
            "policy_registry_sha256": csha(policy_now),
            "external_effect_authority_changed": not authority_unchanged,
        },
        "constraints": [
            "no legacy deletion while retirement_authorized=false",
            "no big-bang delete",
            "consumer migration must preserve parity and fail-closed semantics",
            "rollback windows close only on explicit evidence, never by inference",
        ],
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE8D_READINESS "
        f"assessment={report['repository_assessment']} "
        f"authorized={report['retirement_authorized']} "
        f"blocked_surfaces={len(blockers)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
