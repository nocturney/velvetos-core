#!/usr/bin/env python3
"""Generate Reform v2 Stage 5A context-locality acceptance evidence.

Observation-only: measures root instruction reduction and proves routed local
instruction loading. It performs no external effect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5a-context-locality-baseline.json"
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5a-context-locality.json"
MANIFEST = ROOT / "packages" / "velvetos" / "PROJECT-AUTHORITY-MANIFEST.json"
POLICY_REGISTRY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
STAGE4_ACCEPTANCE = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage4-acceptance.json"
CLI = ROOT / "scripts" / "vf_project_preflight.py"

LEAKAGE_MARKERS = {
    "reference_studio": "REFERENCE_STUDIO:",
    "sderot": "Sderot",
    "business_phone": "050-2517000",
    "public_cta": "PUBLIC_CURRENT_CTA",
    "publication_route": "VF_PUBLICATION_ROUTE_V1",
    "creative_transformation": "CREATIVE-TRANSFORMATION-LOCK.md",
    "brand_asset_lock": "BRAND-ASSET-LOCK.md",
    "publication_prep": "PUBLICATION-PREP-EXECUTION.md",
    "fabrication_router": "FABRICATION-ROUTER.md",
    "grok_quota_failover": "Grok Bot quota failover",
    "live_packet": "LIVE-PACKET",
    "organic_growth": "ORGANIC_GROWTH.md",
    "instagram": "Instagram",
    "gmail": "Gmail",
    "whatsapp": "WhatsApp",
}

def metrics(text: str) -> dict[str, int]:
    return {
        "lines": len(text.splitlines()),
        "words": len(re.findall(r"\S+", text)),
        "characters": len(text),
    }

def run_receipt(domain: str, text: str) -> tuple[int, dict[str, Any]]:
    proc = subprocess.run(
        [sys.executable, str(CLI), "--domain", domain, "--text", text],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if not proc.stdout.strip():
        raise SystemExit(f"preflight emitted no JSON for {domain}: {proc.stderr}")
    return proc.returncode, json.loads(proc.stdout)

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stage4 = json.loads(STAGE4_ACCEPTANCE.read_text(encoding="utf-8"))
    stage4_policy_hash = ((stage4.get("source_receipts") or {}).get("policy_registry") or {}).get("sha256")
    current_policy_hash = hashlib.sha256(POLICY_REGISTRY.read_bytes()).hexdigest()
    policy_registry_unchanged = bool(stage4_policy_hash) and current_policy_hash == stage4_policy_hash
    root_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    current = metrics(root_text)
    leakage = {k: root_text.count(v) for k, v in LEAKAGE_MARKERS.items()}
    local_agents = sorted(
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "packages").rglob("AGENTS.md")
    )

    locality = manifest.get("instructionLocality") or {}
    guides = locality.get("domainGuides") or {}
    domain_results: dict[str, Any] = {}
    all_locality_pass = True
    for domain in sorted(manifest.get("domains") or {}):
        rc, receipt = run_receipt(domain, f"Stage 5A locality fixture for {domain}")
        expected = ["AGENTS.md"] + list(guides.get(domain) or [])
        actual = receipt.get("local_instructions")
        pass_row = (
            actual == expected
            and len(guides.get(domain) or []) == 1
            and all((ROOT / rel).is_file() for rel in expected)
        )
        all_locality_pass = all_locality_pass and pass_row
        domain_results[domain] = {
            "return_code": rc,
            "expected_local_instructions": expected,
            "actual_local_instructions": actual,
            "pass": pass_row,
        }

    _, system_receipt = run_receipt("system_engineering", "update VelvetOS core policy registry")
    system_local = system_receipt.get("local_instructions") or []
    unrelated = [
        "packages/vfom/AGENTS.md",
        "packages/vfprod/AGENTS.md",
        "packages/vfharness/devtools/creative-craft/AGENTS.md",
        "packages/vfharness/devtools/creative-tools/AGENTS.md",
    ]
    system_context_clean = (
        system_local == ["AGENTS.md", "packages/velvetos/AGENTS.md"]
        and not any(rel in system_local for rel in unrelated)
    )

    unknown = subprocess.run(
        [sys.executable, str(CLI), "--domain", "not-a-domain", "--text", "unknown route"],
        cwd=ROOT, text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=60,
    )
    unknown_receipt = json.loads(unknown.stdout)
    unknown_pass = (
        unknown.returncode == 2
        and unknown_receipt.get("preflight_mode") == "FULL"
        and unknown_receipt.get("local_instructions") == ["AGENTS.md"]
        and unknown_receipt.get("project_preflight") == "BLOCKED"
    )

    root_reduction_pct = round(
        100.0 * (baseline["root_agents"]["words"] - current["words"]) / baseline["root_agents"]["words"],
        1,
    )
    leakage_total = sum(leakage.values())

    report = {
        "schema": "velvetos.stage5a-context-locality.v1",
        "stage": "5A",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against.lower(),
        "captured_at": args.captured_at,
        "baseline_receipt": BASELINE.relative_to(ROOT).as_posix(),
        "before": {
            "root_agents": baseline["root_agents"],
            "root_domain_leakage_total": baseline["root_domain_leakage_total"],
            "package_local_agents_count": baseline["package_local_agents_count"],
            "check_scripts_referencing_agents_count": baseline["check_scripts_referencing_agents_count"],
        },
        "after": {
            "root_agents": current,
            "root_domain_leakage_marker_counts": leakage,
            "root_domain_leakage_total": leakage_total,
            "package_local_agents_count": len(local_agents),
            "package_local_agents": local_agents,
            "root_word_reduction_percent": root_reduction_pct,
        },
        "instruction_locality": {
            "mode": locality.get("mode"),
            "warehouse_default": locality.get("warehouseDefault"),
            "domain_count": len(guides),
            "all_domains_have_exactly_one_primary_guide": (
                set(guides) == set(manifest.get("domains") or {})
                and all(isinstance(v, list) and len(v) == 1 for v in guides.values())
            ),
            "domain_results": domain_results,
            "all_domain_receipts_pass": all_locality_pass,
        },
        "negative_controls": {
            "system_engineering_loads_only_root_plus_core": system_context_clean,
            "unknown_domain_root_only_full_blocked": unknown_pass,
            "unrelated_specialist_guides_in_system_receipt": [r for r in unrelated if r in system_local],
        },
        "authorization_semantics": {
            "stage4_policy_registry_sha256": stage4_policy_hash,
            "current_policy_registry_sha256": current_policy_hash,
            "external_effect_authority_registry_unchanged": policy_registry_unchanged,
            "local_guides_are_authority": False,
            "project_request_remains_router_only": True,
        },
        "targets": baseline.get("targets") or {},
        "repository_acceptance": "PASS" if (
            current["lines"] <= 80
            and current["words"] <= 1200
            and leakage_total == 0
            and len(local_agents) >= 6
            and all_locality_pass
            and system_context_clean
            and unknown_pass
            and policy_registry_unchanged
            and locality.get("warehouseDefault") == "off"
        ) else "FAIL",
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE5A_CONTEXT_LOCALITY "
        f"acceptance={report['repository_acceptance']} "
        f"root={current['lines']}lines/{current['words']}words "
        f"reduction={root_reduction_pct}% leakage={leakage_total} "
        f"local_agents={len(local_agents)} domains={len(guides)}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
