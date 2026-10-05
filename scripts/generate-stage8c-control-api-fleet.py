#!/usr/bin/env python3
"""Generate Stage 8C Control API instance/fleet consumer migration evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage8c-control-api-fleet.json"
REPORT_REL = OUT.relative_to(ROOT).as_posix()
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
CANON_FLEET = ROOT / "instances" / "velvet-factory" / "instance" / "fleet.json"
LEGACY_FLEET = ROOT / "packages" / "vfprod" / "FLEET.json"
OPERATIONAL = ROOT / "packages" / "velvetos_control_api" / "contributions" / "operational.py"
INTEGRATIONS = ROOT / "packages" / "velvetos_control_api" / "contributions" / "integrations.py"
INSTANCE_SOURCES = ROOT / "packages" / "velvetos_control_api" / "instance_sources.py"
CONTRIB = ROOT / "packages" / "velvetos_control_api" / "CONTRIBUTIONS.json"
DOCKER = ROOT / "packages" / "velvetos_control_api" / "Dockerfile"
DEPLOY = ROOT / "packages" / "velvetos_control_api" / "deploy.sh"
README = ROOT / "packages" / "velvetos_control_api" / "README.md"
DEPLOY_DOC = ROOT / "packages" / "velvetos_control_api" / "DEPLOY.md"

def load(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must be object")
    return obj

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)

def csha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def git_json(commit: str, rel: str) -> dict[str, Any]:
    raw = subprocess.check_output(["git", "show", f"{commit}:{rel}"], cwd=ROOT)
    obj = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{rel}@{commit} must be object")
    return obj


def git_text(commit: str, rel: str) -> str:
    return subprocess.check_output(["git", "show", f"{commit}:{rel}"], cwd=ROOT).decode("utf-8-sig", errors="replace")


def git_exists(commit: str, rel: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{commit}:{rel}"], cwd=ROOT, capture_output=True).returncode == 0


def source_commit() -> str | None:
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", REPORT_REL],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    value = proc.stdout.strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value or "") else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    a = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", a.prepared_against) is not None, "bad sha")

    src = source_commit()
    def src_json(path: Path) -> dict[str, Any]:
        return git_json(src, path.relative_to(ROOT).as_posix()) if src else load(path)
    def src_text(path: Path) -> str:
        return git_text(src, path.relative_to(ROOT).as_posix()) if src else path.read_text(encoding="utf-8")

    canon = src_json(CANON_FLEET)
    legacy = src_json(LEGACY_FLEET)
    legacy_base = git_json(a.prepared_against, "packages/vfprod/FLEET.json")
    require(csha(canon) == csha(legacy), "canonical fleet differs from legacy compatibility fleet")
    require(csha(legacy) == csha(legacy_base), "legacy fleet changed during Control API cutover")

    operational = src_text(OPERATIONAL)
    integrations = src_text(INTEGRATIONS)
    helper = src_text(INSTANCE_SOURCES)
    contributions = src_json(CONTRIB)
    docker = src_text(DOCKER)
    deploy = src_text(DEPLOY)
    readme = src_text(README)
    deploy_doc = src_text(DEPLOY_DOC)

    runtime_files = {
        "operational": operational,
        "integrations": integrations,
        "instance_sources": helper,
    }
    require(all("packages/vfprod/FLEET.json" not in text for text in runtime_files.values()),
            "Control API runtime code still names legacy fleet")
    require("or \"velvet-factory\"" not in operational and "or \"velvet-factory\"" not in integrations,
            "Control API runtime code retains silent VF default")
    require('_surface(root, "fleet")' in operational, "production does not resolve fleet surface")
    require('_surface(root, "toolDesk")' in operational, "agents do not resolve toolDesk surface")
    require('resolve_instance_surface(root, "toolDesk"' in integrations, "integrations do not resolve toolDesk surface")

    by_id = {row.get("id"): row for row in contributions.get("contributions") or [] if isinstance(row, dict)}
    op_sources = set((by_id.get("operational_domains") or {}).get("authoritativeSources") or [])
    int_sources = set((by_id.get("integrations") or {}).get("authoritativeSources") or [])
    require("instances/<VELVETOS_INSTANCE_ID>/instance/fleet.json" in op_sources,
            "operational contribution does not declare canonical fleet authority")
    require("packages/vfprod/FLEET.json" not in op_sources,
            "operational contribution still declares legacy fleet authority")
    require("instances/<VELVETOS_INSTANCE_ID>/.cursor/vf-desk.json#desk" in op_sources,
            "operational contribution desk authority drift")
    require(int_sources == {"instances/<VELVETOS_INSTANCE_ID>/.cursor/vf-desk.json#tools"},
            "integrations contribution authority drift")

    required_copies = {
        "packages/velvetos/instance_resolver.py",
        "instances/velvet-factory/INSTANCE.json",
        "instances/velvet-factory/instance/velvet-factory.json",
        "instances/velvet-factory/instance/fleet.json",
        "instances/velvet-factory/instance/tool-status.json",
        "instances/velvet-factory/.cursor/vf-desk.json",
    }
    require(all(f"COPY {rel}" in docker for rel in required_copies),
            "Cloud Run image misses one or more declared instance surfaces")
    require("COPY packages/vfprod/FLEET.json" not in docker,
            "Cloud Run image still packages legacy fleet")
    require('--set-env-vars "VELVETOS_INSTANCE_ID=velvet-factory"' in deploy,
            "VF deployment does not select instance explicitly")
    require("VELVETOS_INSTANCE_ID=velvet-factory" in deploy_doc,
            "deploy documentation omits explicit instance selection")
    require("instances/<VELVETOS_INSTANCE_ID>/instance/fleet.json" in readme,
            "Control API README still teaches legacy production authority")

    policy_now = csha(src_json(POLICY))
    policy_base = csha(git_json(a.prepared_against, "packages/velvetos/policy/policy-registry.json"))
    require(policy_now == policy_base, "external-effect policy changed")

    criteria = {
        "control_api_production_reads_canonical_instance_fleet_surface": '_surface(root, "fleet")' in operational,
        "control_api_agents_and_integrations_read_canonical_tooldesk_surface": (
            '_surface(root, "toolDesk")' in operational
            and 'resolve_instance_surface(root, "toolDesk"' in integrations
        ),
        "control_api_runtime_has_no_legacy_fleet_path_or_silent_vf_default": (
            all("packages/vfprod/FLEET.json" not in text for text in runtime_files.values())
            and "or \"velvet-factory\"" not in operational
            and "or \"velvet-factory\"" not in integrations
        ),
        "control_api_registry_declares_instance_owned_fleet_and_desk_authority": (
            "instances/<VELVETOS_INSTANCE_ID>/instance/fleet.json" in op_sources
            and "instances/<VELVETOS_INSTANCE_ID>/.cursor/vf-desk.json#desk" in op_sources
        ),
        "cloud_run_image_packages_resolver_manifest_and_declared_surfaces_not_legacy_fleet": (
            all(f"COPY {rel}" in docker for rel in required_copies)
            and "COPY packages/vfprod/FLEET.json" not in docker
        ),
        "vf_cloud_run_deployment_selects_instance_explicitly": '--set-env-vars "VELVETOS_INSTANCE_ID=velvet-factory"' in deploy,
        "canonical_fleet_remains_exactly_equal_to_legacy_rollback_copy": csha(canon) == csha(legacy),
        "legacy_fleet_is_unchanged_and_retained_for_rollback": csha(legacy) == csha(legacy_base) and (git_exists(src, LEGACY_FLEET.relative_to(ROOT).as_posix()) if src else LEGACY_FLEET.is_file()),
        "external_effect_policy_registry_is_unchanged": policy_now == policy_base,
    }

    report = {
        "schema": "velvetos.stage8c-control-api-fleet.v1",
        "stage": "8C_CONTROL_API_FLEET",
        "behavior_change": True,
        "prepared_against_main_sha": a.prepared_against,
        "captured_at": a.captured_at,
        "purpose": "Migrate Control API production/agent/integration instance projections to generic instance surfaces while retaining legacy vfprod fleet for rollback and non-migrated consumers.",
        "fleet": {
            "canonical": CANON_FLEET.relative_to(ROOT).as_posix(),
            "legacy": LEGACY_FLEET.relative_to(ROOT).as_posix(),
            "parity": csha(canon) == csha(legacy),
            "legacy_unchanged_from_prepared_against": csha(legacy) == csha(legacy_base),
            "printer_count": len(canon.get("printers") or []),
            "legacy_delete_authorized": False,
        },
        "control_api": {
            "production_source": "instances/<VELVETOS_INSTANCE_ID>/instance/fleet.json",
            "agent_source": "instances/<VELVETOS_INSTANCE_ID>/.cursor/vf-desk.json#desk",
            "integration_source": "instances/<VELVETOS_INSTANCE_ID>/.cursor/vf-desk.json#tools",
            "explicit_instance_environment": "VELVETOS_INSTANCE_ID",
            "vf_deployment_instance": "velvet-factory",
            "legacy_fleet_runtime_reference": False,
        },
        "docker_required_instance_copies": sorted(required_copies),
        "authority_baseline": {
            "policy_registry_canonical_sha256": policy_now,
            "prepared_against_policy_registry_canonical_sha256": policy_base,
            "unchanged": policy_now == policy_base,
        },
        "acceptance_criteria": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_stage": "Stage 8C — Remaining consumer domains" if all(criteria.values()) else None,
        "constraints": [
            "legacy vfprod fleet remains for rollback and non-migrated consumers",
            "no legacy delete in this slice",
            "no external-effect authority change",
            "Control API remains projection-only and read-only",
        ],
    }
    out = a.output if a.output.is_absolute() else ROOT / a.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"STAGE8C_CONTROL_API_FLEET acceptance={report['repository_acceptance']} criteria={sum(map(bool,criteria.values()))}/{len(criteria)} printers={report['fleet']['printer_count']}")
    return 0 if report["repository_acceptance"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
