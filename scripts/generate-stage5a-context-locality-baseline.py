#!/usr/bin/env python3
"""Capture the pre-Stage-5A instruction-locality baseline.

Observation only: no routing or authorization behavior changes.
All measured repository content is read from the exact prepared-against Git tree;
working-tree state is never accepted as historical baseline evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5a-context-locality-baseline.json"

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


def metrics(text: str) -> dict:
    return {
        "lines": len(text.splitlines()),
        "words": len(re.findall(r"\S+", text)),
        "characters": len(text),
    }


def git_text(ref: str, rel: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise SystemExit(f"cannot read {rel} from {ref}: {proc.stderr.strip()}")
    return proc.stdout


def git_paths(ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise SystemExit(f"cannot list {ref}: {proc.stderr.strip()}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def analyze_consumers(items: list[tuple[str, str]]) -> list[dict]:
    consumers = []
    for rel, body in items:
        if "AGENTS.md" not in body:
            continue
        reasons = []
        if 'AGENTS = ROOT / "AGENTS.md"' in body:
            reasons.append("root_agents_constant")
        if "AGENTS.read_text" in body or "agents = AGENTS.read_text" in body:
            reasons.append("root_agents_content_assertion")
        if "'AGENTS.md'" in body or '"AGENTS.md"' in body:
            reasons.append("root_agents_surface_or_path")
        consumers.append({"path": rel, "reasons": reasons})
    return consumers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--source-ref")
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    if len(args.prepared_against) != 40:
        ap.error("--prepared-against must be a full Git SHA")

    source_ref = args.source_ref or args.prepared_against
    if source_ref:
        resolved = subprocess.run(
            ["git", "rev-parse", source_ref],
            cwd=ROOT, text=True, encoding="utf-8", capture_output=True, timeout=30,
        )
        if resolved.returncode != 0:
            raise SystemExit(f"cannot resolve --source-ref {source_ref}: {resolved.stderr.strip()}")
        if resolved.stdout.strip().lower() != args.prepared_against.lower():
            raise SystemExit("--source-ref must resolve exactly to --prepared-against")
        paths = git_paths(source_ref)
        text = git_text(source_ref, "AGENTS.md")
        package_agents = sorted(
            p for p in paths if p.startswith("packages/") and p.endswith("/AGENTS.md")
        )
        instance_agents = sorted(
            p for p in paths if p.startswith("instances/") and p.endswith("/AGENTS.md")
        )
        script_paths = sorted(
            p for p in paths
            if p.startswith("scripts/check-") and p.endswith(".py")
        )
        consumers = analyze_consumers([
            (p, git_text(source_ref, p)) for p in script_paths
        ])
    else:
        root_agents = ROOT / "AGENTS.md"
        text = root_agents.read_text(encoding="utf-8")
        package_agents = sorted(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "packages").rglob("AGENTS.md")
        )
        instance_agents = sorted(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "instances").rglob("AGENTS.md")
        )
        consumers = analyze_consumers([
            (p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8", errors="replace"))
            for p in sorted((ROOT / "scripts").glob("check-*.py"))
        ])

    leakage = {key: text.count(marker) for key, marker in LEAKAGE_MARKERS.items()}
    report = {
        "schema": "velvetos.stage5a-context-locality-baseline.v1",
        "stage": "5A",
        "behavior_change": False,
        "prepared_against_main_sha": args.prepared_against.lower(),
        "captured_at": args.captured_at,
        "source_ref": source_ref or "worktree",
        "root_agents": metrics(text),
        "root_domain_leakage_marker_counts": leakage,
        "root_domain_leakage_total": sum(leakage.values()),
        "package_local_agents_count": len(package_agents),
        "package_local_agents": package_agents,
        "instance_agents_count": len(instance_agents),
        "instance_agents": instance_agents,
        "check_scripts_referencing_agents_count": len(consumers),
        "check_scripts_referencing_agents": consumers,
        "targets": {
            "root_max_lines": 80,
            "root_max_words": 1200,
            "root_vf_business_fact_markers": 0,
            "package_local_agents_minimum": 6,
            "core_system_task_loads_vf_creative_or_printer_context": False,
            "known_task_loads_only_nearest_local_instructions": True,
            "authorization_semantics_change": False,
        },
    }
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE5A_BASELINE "
        f"source={report['source_ref']} "
        f"root_lines={report['root_agents']['lines']} "
        f"root_words={report['root_agents']['words']} "
        f"leakage={report['root_domain_leakage_total']} "
        f"package_agents={report['package_local_agents_count']} "
        f"check_consumers={report['check_scripts_referencing_agents_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
