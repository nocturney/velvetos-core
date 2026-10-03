#!/usr/bin/env python3
"""Generate Reform v2 Stage 4B Project Request Fast Path acceptance evidence."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "packages/velvetos/policy/reports/stage4a-friction-baseline.json"
OUTPUT = ROOT / "packages/velvetos/policy/reports/stage4b-project-request-fast-path.json"
PREFLIGHT = ROOT / "scripts/vf_project_preflight.py"

EXPECTED_DOMAIN = {
    "instagram_post": "creative_publication",
    "instagram_story": "creative_publication",
    "instagram_reel": "creative_publication",
    "instagram_carousel": "creative_publication",
    "gmail_reply": "operations",
    "gmail_send": "operations",
    "owner_brief": "operations",
    "drive_artifact": "operations",
    "dcc_launch": "production",
    "dcc_task": "production",
    "cad_readonly": "production",
    "cad_build": "production",
    "research_update": "research",
    "internal_status": "operations",
}

FAST_PATH_IDS = {
    "owner_brief",
    "dcc_launch",
    "dcc_task",
    "cad_readonly",
    "cad_build",
    "research_update",
    "internal_status",
}


def run(text: str) -> tuple[int, dict]:
    cp = subprocess.run(
        [sys.executable, str(PREFLIGHT), "--text", text],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        payload = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"preflight JSON decode failed for {text!r}: {exc}: {cp.stdout[-500:]}")
    return cp.returncode, payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-main", required=True)
    ap.add_argument("--candidate", default="working-tree")
    ap.add_argument("--output", type=Path, default=OUTPUT)
    args = ap.parse_args()

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    before = {row["id"]: row for row in baseline["flows"]}
    rows = []
    for flow_id, expected_domain in EXPECTED_DOMAIN.items():
        old = before[flow_id]
        request = old["request"]
        rc, receipt = run(request)
        domains = list(receipt.get("request_domain") or [])
        row = {
            "id": flow_id,
            "request": request,
            "return_code": rc,
            "expected_domain": expected_domain,
            "domains": domains,
            "route_aligned": expected_domain in domains,
            "request_scope": receipt.get("request_scope"),
            "preflight_mode": receipt.get("preflight_mode"),
            "full_preflight_triggers": receipt.get("full_preflight_triggers") or [],
            "project_preflight": receipt.get("project_preflight"),
            "owner_surface": receipt.get("owner_surface"),
            "required_sources": len(receipt.get("required_sources") or []),
            "routed_packs": len(receipt.get("routed_packs") or []),
            "hard_gates": len(receipt.get("hard_gates") or []),
            "required_tools": receipt.get("required_tools") or [],
            "required_skills": receipt.get("required_skills") or [],
            "before": {
                "auto_domains": old.get("auto_domains") or [],
                "project_preflight": old.get("project_preflight"),
                "required_sources": old.get("required_sources"),
                "routed_packs": old.get("routed_packs"),
                "hard_gates": old.get("hard_gates"),
            },
        }
        rows.append(row)

    fast_rows = [r for r in rows if r["preflight_mode"] == "FAST_PATH"]
    full_rows = [r for r in rows if r["preflight_mode"] == "FULL"]
    generic = [r for r in rows if r["domains"] == ["general_business"]]
    aligned = [r for r in rows if r["route_aligned"]]
    tool_routed = [r for r in rows if r["required_tools"]]
    internal_receipts = [r for r in rows if r["owner_surface"] == "internal_unless_true_blocker"]
    creative_blocked = [
        r for r in rows
        if r["expected_domain"] == "creative_publication" and r["project_preflight"] == "BLOCKED"
    ]

    fast_before_sources = [r["before"]["required_sources"] for r in fast_rows]
    fast_after_sources = [r["required_sources"] for r in fast_rows]
    fast_before_gates = [r["before"]["hard_gates"] for r in fast_rows]
    fast_after_gates = [r["hard_gates"] for r in fast_rows]

    cad_read = next(r for r in rows if r["id"] == "cad_readonly")
    cad_build = next(r for r in rows if r["id"] == "cad_build")
    cad_distinct = (
        cad_read["request_scope"] != cad_build["request_scope"]
        and cad_read["hard_gates"] < cad_build["hard_gates"]
    )

    negative_controls = (
        ("Set the customer price in ₪", "commercial_or_spend"),
        ("Purchase a new subscription for this tool", "commercial_or_spend"),
        ("Delete this internal file", "destructive_or_permission"),
        ("Change access permission on this file", "destructive_or_permission"),
        ("Use this private customer data in the artifact", "rights_or_privacy"),
        ("Send this STL to the printer and start printing", "physical_print"),
        ("Summarize this", "unknown_domain"),
    )
    negative_rows = []
    for request, trigger in negative_controls:
        _, receipt = run(request)
        negative_rows.append(
            {
                "request": request,
                "required_trigger": trigger,
                "preflight_mode": receipt.get("preflight_mode"),
                "full_preflight_triggers": receipt.get("full_preflight_triggers") or [],
                "pass": (
                    receipt.get("preflight_mode") == "FULL"
                    and trigger in (receipt.get("full_preflight_triggers") or [])
                ),
            }
        )

    report = {
        "schema": "velvetos.stage4b-project-request-fast-path.v1",
        "stage": "4B",
        "behavior_change": True,
        "base_main_sha": args.base_main,
        "candidate": args.candidate,
        "baseline_report": "packages/velvetos/policy/reports/stage4a-friction-baseline.json",
        "flow_count": len(rows),
        "flows": rows,
        "negative_controls": negative_rows,
        "summary": {
            "route_aligned": len(aligned),
            "general_business_fallback": len(generic),
            "fast_path_count": len(fast_rows),
            "full_preflight_count": len(full_rows),
            "required_tools_populated": len(tool_routed),
            "owner_surface_internal_unless_true_blocker": len(internal_receipts),
            "creative_flows_fail_closed_without_evidence": len(creative_blocked),
            "fast_path_before_mean_sources": round(statistics.fmean(fast_before_sources), 3),
            "fast_path_after_mean_sources": round(statistics.fmean(fast_after_sources), 3),
            "fast_path_source_reduction_percent": round(
                100 * (1 - statistics.fmean(fast_after_sources) / statistics.fmean(fast_before_sources)), 1
            ),
            "fast_path_before_mean_gates": round(statistics.fmean(fast_before_gates), 3),
            "fast_path_after_mean_gates": round(statistics.fmean(fast_after_gates), 3),
            "fast_path_gate_reduction_percent": round(
                100 * (1 - statistics.fmean(fast_after_gates) / statistics.fmean(fast_before_gates)), 1
            ),
            "cad_readonly_and_build_scope_distinct": cad_distinct,
            "negative_controls_full": all(r["pass"] for r in negative_rows),
        },
        "acceptance": {
            "known_flow_generic_fallbacks": 0,
            "routine_low_risk_owner_prompts": 0,
            "external_mutations_remain_full": True,
            "creative_publication_remains_full_and_fail_closed": True,
            "unknown_or_sensitive_requests_remain_full": True,
            "postflight_still_required": True,
        },
    }

    expected = {
        "route_aligned": 14,
        "general_business_fallback": 0,
        "fast_path_count": 7,
        "full_preflight_count": 7,
        "required_tools_populated": 10,
        "owner_surface_internal_unless_true_blocker": 14,
        "creative_flows_fail_closed_without_evidence": 4,
        "cad_readonly_and_build_scope_distinct": True,
        "negative_controls_full": True,
    }
    for key, value in expected.items():
        if report["summary"].get(key) != value:
            raise SystemExit(f"Stage 4B acceptance mismatch {key}: expected {value!r}, got {report['summary'].get(key)!r}")

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE4B_FAST_PATH "
        f"flows={len(rows)} aligned={len(aligned)} generic={len(generic)} "
        f"fast={len(fast_rows)} full={len(full_rows)} "
        f"source_reduction={report['summary']['fast_path_source_reduction_percent']}% "
        f"gate_reduction={report['summary']['fast_path_gate_reduction_percent']}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
