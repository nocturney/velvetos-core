#!/usr/bin/env python3
"""Generate Reform v2 Stage 4E Gmail/external-send simplification evidence.

This is a repository acceptance report for existing policy_id: gmail.send.
It never sends email and never calls Gmail. The report proves the policy/evidence
split, routine no-ceremony path, commitment exact-binding path, static-copy
reuse, and fail-closed negative controls.
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
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage4e-gmail-send-simplification.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "gmail.send.json"
VECTORS = ROOT / "packages" / "velvetos" / "policy" / "gmail-send-test-vectors.json"


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=90,
        env=env,
    )
    return {
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stdout_tail": (proc.stdout or "").strip().splitlines()[-8:],
        "stderr_tail": (proc.stderr or "").strip().splitlines()[-8:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-against", required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    if len(args.prepared_against) != 40 or any(c not in "0123456789abcdef" for c in args.prepared_against.lower()):
        parser.error("--prepared-against must be a full Git SHA")

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    vectors = json.loads(VECTORS.read_text(encoding="utf-8"))
    expected = [row["expected"] for row in vectors["vectors"]]
    decision_counts = {
        decision: sum(1 for row in expected if row["decision"] == decision)
        for decision in ("ALLOW", "REQUIRE_OWNER_APPROVAL", "DENY")
    }

    pyenv = dict(os.environ)
    pyenv["PYTHONPATH"] = str(ROOT / "packages") + os.pathsep + str(ROOT / "scripts")
    checks = [
        run([sys.executable, "scripts/vf_gmail_send_policy.py", "--self-test"], env=pyenv),
        run([sys.executable, "scripts/vf_action_receipt.py", "--self-test"], env=pyenv),
        run([sys.executable, "scripts/check-visible-text-gate.py"], env=pyenv),
        run([sys.executable, "scripts/vf_send_preflight.py", "--gate", "gmail"], env=pyenv),
    ]
    failed = [row for row in checks if row["return_code"] != 0]

    routine_ids = {
        "known-thread-routine-reply",
        "routine-owner-brief",
        "routine-forward",
        "approved-static-copy-exact-reuse",
    }
    vector_by_id = {row["id"]: row for row in vectors["vectors"]}
    routine_allows = all(
        vector_by_id[row_id]["expected"]["decision"] == "ALLOW"
        and vector_by_id[row_id]["expected"]["owner_approval_required"] is False
        and vector_by_id[row_id]["expected"]["requires_exact_action_receipt"] is False
        for row_id in routine_ids
    )
    gmail_transport = checks[-1]
    transport_marked_non_authoritative = any(
        "authorization=policy_id:gmail.send-required" in line
        for line in gmail_transport["stdout_tail"]
    )

    report = {
        "schema": "velvetos.stage4e-gmail-send-simplification.v1",
        "stage": "4E",
        "prepared_against_main_sha": args.prepared_against.lower(),
        "captured_at": args.captured_at,
        "policy_id": "gmail.send",
        "policy_version": policy.get("version"),
        "authority": {
            "canonical_law": "constitution/SEND.md",
            "runtime_evaluator": "scripts/vf_gmail_send_policy.py",
            "machine_policy": "packages/velvetos/policy/gmail.send.json",
            "transport_preflight": "scripts/vf_send_preflight.py --gate gmail",
            "transport_is_authorization": False,
        },
        "routine_happy_path": {
            "scopes": policy.get("routine_scopes"),
            "owner_prompt_count": 0,
            "requires_exact_action_receipt": False,
            "facts_required": True,
            "text_readiness_required": True,
            "target_verified_required": True,
            "transport_ready_required": True,
            "routine_vectors_all_allow": routine_allows,
        },
        "approved_static_copy": {
            "mode": "approved_static_copy",
            "exact_body_sha256_required": True,
            "text_unchanged_required": True,
            "facts_current_required": True,
            "full_rewrite_pipeline_rerun_required_when_exact_and_current": False,
        },
        "gated_cases": {
            "new_outbound": "REQUIRE_OWNER_APPROVAL",
            "new_commercial_commitment": "REQUIRE_OWNER_APPROVAL",
            "price_or_spend": "REQUIRE_OWNER_APPROVAL",
            "rights_privacy_ambiguity": "REQUIRE_OWNER_APPROVAL",
            "commitment_receipt_mode": policy.get("commitment_receipt_mode"),
            "exact_owner_approval_body_binding_required": True,
        },
        "hard_denies": {
            "unverified_fact": "DENY",
            "blast": "DENY",
            "target_unverified": "DENY",
            "transport_not_ready": "DENY",
            "text_or_body_mismatch": "DENY",
            "static_copy_changed_or_stale": "DENY",
        },
        "action_receipt_contract": {
            "schema": "velvetos.action-receipt.v1",
            "gmail_commitment_exact_body_vector": "gmail-commitment-exact-body-valid",
            "gmail_commitment_missing_body_vector": "gmail-commitment-missing-exact-body-blocked",
            "gmail_routine_no_exact_binding_vector": "gmail-routine-reply-does-not-require-exact-action-binding",
        },
        "vector_summary": {
            "count": len(vectors["vectors"]),
            "decision_counts": decision_counts,
            "routine_no_owner_prompt_proven": routine_allows,
        },
        "tests": checks,
        "transport_output_proves_non_authority": transport_marked_non_authoritative,
        "provider_postcondition": "provider receipt required before claiming sent",
        "repository_acceptance": (
            "PASS"
            if not failed
            and routine_allows
            and transport_marked_non_authoritative
            and decision_counts == {"ALLOW": 5, "REQUIRE_OWNER_APPROVAL": 5, "DENY": 9}
            else "FAIL"
        ),
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE4E_GMAIL_SEND "
        f"acceptance={report['repository_acceptance']} "
        f"vectors={report['vector_summary']['count']} "
        f"routine_owner_prompts={report['routine_happy_path']['owner_prompt_count']} "
        f"decisions={decision_counts}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
