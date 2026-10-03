#!/usr/bin/env python3
"""Generate Reform v2 Stage 4D repository-acceptance evidence.

This report proves the implementation contract before production deployment.
A separate cutover receipt records the live Worker version/readback after merge.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage4d-instagram-happy-path-implementation.json"
CUTOVER_RECEIPT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage4d-instagram-happy-path-cutover.json"


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        env=env,
    )
    return {
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stdout_tail": (proc.stdout or "").strip().splitlines()[-5:],
        "stderr_tail": (proc.stderr or "").strip().splitlines()[-5:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-against", required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    if len(args.prepared_against) != 40:
        parser.error("--prepared-against must be a full Git SHA")

    pyenv = dict(os.environ)
    pyenv["PYTHONPATH"] = str(ROOT / "packages") + os.pathsep + str(ROOT / "scripts")

    checks = [
        run([sys.executable, "scripts/vf_content_ready.py", "--self-test"], env=pyenv),
        run([sys.executable, "packages/vfigos/routine_publish.py", "--self-test"], env=pyenv),
        run(["node", "packages/velvetos/policy/test-instagram-publish-policy.mjs"]),
        run(["node", "packages/vfigos/cloudflare-publisher/test-policy-gate.mjs"]),
        run(["node", "packages/vfigos/cloudflare-publisher/test-format-contracts.mjs"]),
        run([sys.executable, "scripts/check-delivery-approval.py"], env=pyenv),
    ]
    failed = [row for row in checks if row["return_code"] != 0]

    policy = json.loads(
        (ROOT / "packages/velvetos/policy/instagram.publish.json").read_text(encoding="utf-8")
    )
    registry = json.loads(
        (ROOT / "packages/velvetos/policy/policy-registry.json").read_text(encoding="utf-8")
    )
    effect = next(
        row
        for row in registry["external_effect_contract"]["effects"]
        if row["policy_id"] == "instagram.publish"
    )
    direct_files = [
        ROOT / "packages/vfigos/approval/schema.py",
        ROOT / "packages/vfigos/remote/story_publish.py",
        ROOT / "packages/vfigos/remote/media_guard_params.py",
    ]
    direct_text = "\\n".join(path.read_text(encoding="utf-8") for path in direct_files)
    direct_boundary_preserved = (
        "velvet.delivery_approval.v1" in direct_text
        and "delivery_approval" in direct_text
        and effect["receipt_mode"] == "POLICY_NATIVE_RECEIPT"
    )

    production_cutover = {
        "status": "PENDING_AFTER_MERGE",
        "live_worker_version_id": None,
        "health_readback": None,
        "negative_control": None,
    }
    if CUTOVER_RECEIPT.is_file():
        cutover = json.loads(CUTOVER_RECEIPT.read_text(encoding="utf-8"))
        if cutover.get("schema") != "velvetos.stage4d-instagram-happy-path.cutover.v1":
            raise SystemExit("Stage 4D cutover receipt schema mismatch")
        if cutover.get("stage") != "4D" or cutover.get("policy_id") != "instagram.publish":
            raise SystemExit("Stage 4D cutover receipt identity mismatch")
        deployment = cutover.get("deployment") or {}
        production_cutover = {
            "status": cutover.get("cutover_status"),
            "deployed_main_sha": deployment.get("deployed_main_sha"),
            "live_worker_version_id": deployment.get("live_worker_version_id"),
            "worker_version_created_at": deployment.get("worker_version_created_at"),
            "worker_url": deployment.get("worker_url"),
            "health_readback": cutover.get("health_readback"),
            "negative_control": cutover.get("negative_control"),
            "compatibility": cutover.get("compatibility"),
            "rollback": cutover.get("rollback"),
            "receipt": CUTOVER_RECEIPT.relative_to(ROOT).as_posix(),
        }

    report = {
        "schema": "velvetos.stage4d-instagram-happy-path.implementation.v1",
        "stage": "4D",
        "prepared_against_main_sha": args.prepared_against.lower(),
        "captured_at": args.captured_at,
        "policy_id": "instagram.publish",
        "policy_version": policy.get("version"),
        "content_ready": {
            "schema_version": (policy.get("content_ready") or {}).get("schema_version"),
            "required_evidence": (policy.get("content_ready") or {}).get("required_evidence"),
            "required_gate_count": len(policy.get("required_gates") or []),
            "required_gates": policy.get("required_gates"),
            "evidence_is_authority": False,
        },
        "routine_happy_path": {
            "formats": ["image", "carousel", "reel", "story"],
            "risk_class": "LOW",
            "standing_authorization_from_runtime": True,
            "per_asset_owner_approval": False,
            "policy_decisions_per_publish_attempt": 1,
            "scheduler": "packages/vfigos/cloudflare-publisher/",
            "client": "packages/vfigos/routine_publish.py",
        },
        "failure_routing": {
            "quality_failure": "TARGETED_REPAIR",
            "transport_failure": "RETRY_INTERNAL",
            "rights_privacy_ambiguity": "HARD_BLOCKER",
            "owner_prompt_on_quality_failure": False,
        },
        "immediate_direct_mutation": {
            "signed_delivery_approval_preserved": direct_boundary_preserved,
            "receipt_schema": "velvet.delivery_approval.v1",
            "standing_routine_scheduler_does_not_mint_direct_receipt": True,
        },
        "postconditions": policy.get("postconditions"),
        "compatibility": {
            "old_policy_context_before": (
                (policy.get("content_ready") or {})
                .get("legacy_gate_compatibility", {})
                .get("jobs_created_before")
            ),
            "new_jobs_require_content_ready_after_cutoff": True,
        },
        "tests": checks,
        "repository_acceptance": "FAIL" if failed or not direct_boundary_preserved else "PASS",
        "production_cutover": production_cutover,
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE4D_IMPLEMENTATION "
        f"acceptance={report['repository_acceptance']} "
        f"policy_version={report['policy_version']} "
        f"formats={','.join(report['routine_happy_path']['formats'])}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
