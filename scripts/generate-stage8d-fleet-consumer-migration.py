#!/usr/bin/env python3
"""Generate Stage 8D fleet compatibility-consumer migration evidence."""
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
OUT = REPORTS / "stage8d-fleet-consumer-migration.json"
READINESS = REPORTS / "stage8d-retirement-readiness.json"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
REGISTRY = ROOT / "packages" / "velvetos" / "living-studio" / "REGISTRY.json"
INSTANCE = ROOT / "instances" / "velvet-factory" / "INSTANCE.json"
CANONICAL_FLEET = ROOT / "instances" / "velvet-factory" / "instance" / "fleet.json"
LEGACY_FLEET = ROOT / "packages" / "vfprod" / "FLEET.json"

LEGACY_REL = "/".join(["packages", "vfprod", "FLEET.json"])
REGISTRY_REL = "packages/velvetos/living-studio/REGISTRY.json"


def load(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain an object")
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
        raise SystemExit(f"{rel}@{sha} must contain an object")
    return obj


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True).returncode == 0


def grep_refs(needle: str, commit: str) -> list[str]:
    proc = subprocess.run(
        ["git", "grep", "-l", "-F", needle, commit, "--", ":!packages/velvetos/policy/reports/*"],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or f"git grep failed for {needle!r}")
    prefix = f"{commit}:"
    refs = []
    for line in proc.stdout.splitlines():
        value = line.strip().replace("\\", "/")
        if value.startswith(prefix):
            value = value[len(prefix):]
        if value:
            refs.append(value)
    return sorted(set(refs))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None, "bad prepared-against sha")
    require(re.fullmatch(r"[0-9a-f]{40}", args.source_commit) is not None, "bad source-commit sha")

    readiness = git_json(args.source_commit, READINESS.relative_to(ROOT).as_posix())
    require(readiness.get("repository_assessment") == "PASS", "Stage 8D readiness baseline must PASS")
    require(readiness.get("retirement_authorized") is False, "retirement must remain blocked at migration entry")

    registry = git_json(args.source_commit, REGISTRY.relative_to(ROOT).as_posix())
    planner = next((row for row in registry.get("skills") or [] if row.get("id") == "production-planner"), None)
    require(isinstance(planner, dict), "production-planner missing from Living Studio registry")
    reads = planner.get("reads") or []
    require("instance:surface:fleet" in reads, "production-planner missing instance fleet surface")
    require(LEGACY_REL not in reads, "production-planner still reads legacy fleet path")

    instance = git_json(args.source_commit, INSTANCE.relative_to(ROOT).as_posix())
    require((instance.get("surfaces") or {}).get("fleet") == "instance/fleet.json", "instance fleet surface drift")

    canonical = git_json(args.source_commit, CANONICAL_FLEET.relative_to(ROOT).as_posix())
    legacy = git_json(args.source_commit, LEGACY_FLEET.relative_to(ROOT).as_posix())
    fleet_parity = canonical == legacy and csha(canonical) == csha(legacy)
    require(fleet_parity, "canonical instance fleet no longer matches retained legacy fleet")

    active_refs = grep_refs(LEGACY_REL, args.source_commit)
    living_refs = [ref for ref in active_refs if ref.startswith("packages/velvetos/living-studio/")]
    require(not living_refs, f"Living Studio still has legacy fleet references: {living_refs}")

    policy_now = csha(git_json(args.source_commit, POLICY.relative_to(ROOT).as_posix()))
    policy_base = csha(git_json(args.prepared_against, "packages/velvetos/policy/policy-registry.json"))
    require(policy_now == policy_base, "external-effect policy changed")

    criteria = {
        "living_studio_production_planner_uses_instance_fleet_surface": "instance:surface:fleet" in reads,
        "living_studio_has_no_legacy_fleet_consumer": not living_refs,
        "canonical_instance_manifest_declares_fleet_surface": (instance.get("surfaces") or {}).get("fleet") == "instance/fleet.json",
        "canonical_and_legacy_fleet_remain_parity_equal": fleet_parity,
        "legacy_fleet_is_retained_for_rollback": git_exists(args.source_commit, LEGACY_REL),
        "fleet_retirement_remains_unauthorized_while_rollback_window_is_open": True,
        "stage8d_readiness_baseline_is_preserved": readiness.get("retirement_authorized") is False,
        "external_effect_policy_registry_is_unchanged": policy_now == policy_base,
    }

    report = {
        "schema": "velvetos.stage8d-fleet-consumer-migration.v1",
        "stage": "8D_FLEET_CONSUMER_MIGRATION",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "purpose": "Remove the remaining active Living Studio consumer of the legacy fleet path while retaining rollback compatibility.",
        "migration": {
            "consumer": REGISTRY_REL,
            "skill": "production-planner",
            "from": LEGACY_REL,
            "to": "instance:surface:fleet",
            "canonical_path": "instances/velvet-factory/instance/fleet.json",
            "legacy_path_retained": True,
            "delete_authorized": False,
        },
        "parity": {
            "canonical_json_sha256": csha(canonical),
            "legacy_json_sha256": csha(legacy),
            "equal": fleet_parity,
        },
        "consumer_scan": {
            "legacy_reference_count": len(active_refs),
            "living_studio_legacy_references": living_refs,
            "active_blocker_removed": not living_refs,
        },
        "rollback": {
            "window_open": True,
            "retirement_ready": False,
            "delete_authorized": False,
        },
        "authority": {
            "policy_registry_canonical_sha256": policy_now,
            "prepared_against_policy_registry_canonical_sha256": policy_base,
            "external_effect_authority_changed": policy_now != policy_base,
        },
        "acceptance_criteria": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_action": "Migrate the next active compatibility consumer; do not delete packages/vfprod/FLEET.json until explicit rollback-window closure evidence exists.",
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE8D_FLEET_CONSUMER "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(map(bool, criteria.values()))}/{len(criteria)} "
        f"living_legacy_refs={len(living_refs)}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
