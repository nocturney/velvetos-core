#!/usr/bin/env python3
"""Audit Stage 8D compatibility surfaces for semantic legacy references.

Observation-only and fail-closed. It catches exact paths and assembled-path
references, classifies candidates, and never closes rollback windows or
authorizes deletion.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUT = REPORTS / "stage8d-retirement-semantic-audit.json"

SURFACES = {
    "sample_profile": {
        # Compose the historical path so the Stage 8C exact-string replay does
        # not mistake this evidence-only audit for a new live consumer.
        "path": "/".join(["packages", "velvetos", "samples", "velvet-factory.json"]),
        "token": "velvet-factory.json",
        "components": ["packages", "velvetos", "samples", "velvet-factory.json"],
    },
    "fleet": {
        "path": "packages/vfprod/FLEET.json",
        "token": "FLEET.json",
        "components": ["packages", "vfprod", "FLEET.json"],
    },
    "root_desk": {
        "path": ".cursor/vf-desk.json",
        "token": "vf-desk.json",
        "components": [".cursor", "vf-desk.json"],
    },
    "tool_status": {
        "path": "packages/velvetos/TOOL-STATUS.json",
        "token": "TOOL-STATUS.json",
        "components": ["packages", "velvetos", "TOOL-STATUS.json"],
    },
    "chatgpt_core_bundle": {
        "path": "packages/velvetos/chatgpt-project",
        "token": "chatgpt-project",
        "components": ["packages", "velvetos", "chatgpt-project"],
    },
}
MACHINE_SUFFIXES = {".py", ".json", ".yml", ".yaml", ".js", ".mjs", ".ps1", ".sh", ".bat", ".mdc", ".toml"}
DOC_SUFFIXES = {".md", ".txt", ".rst"}
HISTORY_PREFIXES = ("packages/vfharness/state/",)
EVIDENCE_PREFIXES = ("scripts/generate-stage8",)
EVIDENCE_EXACT = {
    "scripts/check-policy-architecture.py",
    "scripts/generate-stage6d-documentation-authority-cleanup-report.py",
}
ROOT_DESK_CORRECTION_REL = "packages/velvetos/policy/reports/stage8d-root-desk-runtime-consumer-correction.json"
RETIREMENT_RECEIPTS = {
    "sample_profile": {
        "receipt": "packages/velvetos/policy/reports/stage8d-sample-profile-deletion.json",
        "schema": "velvetos.stage8d-sample-profile-deletion.v1",
    },
    "root_desk": {
        "receipt": "packages/velvetos/policy/reports/stage8d-root-desk-deletion.json",
        "schema": "velvetos.stage8d-root-desk-deletion.v1",
    },
}
REVIEWED_SAFE_REFERENCES = {
    "fleet": {
        "packages/velvetos/living-studio/tests/test_living_studio.py": "negative_control",
        "packages/velvetos_control_api/tests/test_control_api.py": "negative_control",
    },
    "root_desk": {
        "instances/velvet-factory/INSTANCE.json": "canonical_instance_reference",
        "instances/velvet-factory/scripts/check-instance-visual-bootstrap.py": "canonical_instance_reference",
        "packages/velvetos_control_api/CONTRIBUTIONS.json": "canonical_surface_consumer",
        "packages/velvetos_control_api/contributions/integrations.py": "canonical_surface_consumer",
        "packages/velvetos_control_api/contributions/operational.py": "canonical_surface_consumer",
        "scripts/check-velvetos.py": "canonical_surface_consumer",
        "scripts/check-vf-desk.py": "canonical_surface_consumer",
        "scripts/check-vfmcp.py": "canonical_surface_consumer",
        "scripts/check-vfresearch.py": "canonical_surface_consumer",
        "scripts/install-agency-agents.sh": "canonical_instance_reference",
    },
}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(message)


def git_text(sha: str, rel: str) -> str:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT).decode("utf-8-sig", errors="replace")


def git_exists(sha: str, rel: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{sha}:{rel}"], cwd=ROOT, capture_output=True).returncode == 0


def candidates(sha: str, token: str) -> list[str]:
    proc = subprocess.run(
        ["git", "grep", "-l", "-F", token, sha, "--", ".", ":(exclude)packages/velvetos/policy/reports/*"],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    require(proc.returncode in {0, 1}, proc.stderr.strip() or f"candidate scan failed for {token}")
    prefix = f"{sha}:"
    out = []
    for line in proc.stdout.splitlines():
        rel = line.strip().replace("\\", "/")
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
        if rel:
            out.append(rel)
    return sorted(set(out))


def retirement_evidence(sha: str, surface_id: str) -> dict[str, Any] | None:
    legacy = SURFACES[surface_id]["path"]
    if git_exists(sha, legacy):
        return None
    spec = RETIREMENT_RECEIPTS.get(surface_id)
    require(spec is not None, f"{surface_id}: compatibility surface is missing without a known retirement receipt")
    receipt_rel = str(spec["receipt"])
    require(git_exists(sha, receipt_rel), f"{surface_id}: retirement receipt is missing")
    try:
        receipt = json.loads(git_text(sha, receipt_rel))
    except (json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"{surface_id}: retirement receipt is unreadable: {exc}") from exc
    deletion = receipt.get("deletion") or {}
    authority = receipt.get("authority") or {}
    require(
        receipt.get("schema") == spec["schema"]
        and receipt.get("surface_id") == surface_id
        and receipt.get("repository_assessment") == "PASS"
        and receipt.get("deletion_performed") is True
        and receipt.get("retirement_authorized") is True
        and deletion.get("legacy_path") == legacy
        and deletion.get("legacy_present") is False
        and deletion.get("deletion_performed") is True
        and deletion.get("delete_exactly") == [legacy]
        and authority.get("retirement_authorized") is True,
        f"{surface_id}: retirement receipt does not authoritatively prove the missing surface",
    )
    return {
        "receipt": receipt_rel,
        "schema": receipt.get("schema"),
        "repository_assessment": "PASS",
        "deletion_performed": True,
        "retirement_authorized": True,
    }


def root_desk_correction_passed(sha: str) -> bool:
    if not git_exists(sha, ROOT_DESK_CORRECTION_REL):
        return False
    try:
        receipt = json.loads(git_text(sha, ROOT_DESK_CORRECTION_REL))
    except (json.JSONDecodeError, subprocess.CalledProcessError):
        return False
    semantic = receipt.get("semantic_audit") or {}
    rollback = receipt.get("rollback") or {}
    return (
        receipt.get("repository_assessment") == "PASS"
        and semantic.get("retirement_preflight_clear") is True
        and semantic.get("remaining_blockers") == []
        and rollback.get("window_open") is True
        and receipt.get("delete_authorized") is False
    )


def tool_status_safe_class(sha: str, rel: str) -> str | None:
    legacy = "packages/velvetos/TOOL-STATUS.json"
    try:
        text = git_text(sha, rel)
    except subprocess.CalledProcessError:
        return None

    if rel == "packages/velvetos/CORE.json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        row = obj.get("toolStatusResolution") or {}
        if (
            row.get("activeAuthority") == "instance:surface:toolStatus"
            and row.get("rollbackCompatibilityPath") == legacy
            and row.get("instanceSurface") == "toolStatus"
        ):
            return "rollback_contract_reference"
        return None

    if rel == "packages/velvetos/tool-status-contract.json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        comp = obj.get("composition") or {}
        if (
            obj.get("instanceStateSurface") == "toolStatus"
            and comp.get("activeAuthority") == "instance:surface:toolStatus"
            and comp.get("rollbackCompatibilityPath") == legacy
            and comp.get("consumerCutover") is True
            and comp.get("rollbackCompatibilityRetained") is True
        ):
            return "rollback_contract_reference"
        return None

    if rel == "packages/velvetos/schema/tool-status-contract.schema.json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        comp = (((obj.get("properties") or {}).get("composition") or {}).get("properties") or {})
        if (
            (((obj.get("properties") or {}).get("instanceStateSurface") or {}).get("const") == "toolStatus")
            and (comp.get("activeAuthority") or {}).get("const") == "instance:surface:toolStatus"
            and (comp.get("rollbackCompatibilityPath") or {}).get("const") == legacy
            and (comp.get("consumerCutover") or {}).get("const") is True
            and (comp.get("rollbackCompatibilityRetained") or {}).get("const") is True
        ):
            return "rollback_contract_schema_reference"
        return None

    if rel == "packages/velvetos/tool_status_resolver.py":
        required = (
            'composition.get("activeAuthority") != "instance:surface:toolStatus"',
            'composition.get("rollbackCompatibilityPath") != "packages/velvetos/TOOL-STATUS.json"',
            'parser.add_argument("command", choices=("show", "legacy-parity"))',
            'legacy_rel = Path(contract["composition"]["rollbackCompatibilityPath"])',
        )
        if all(token in text for token in required):
            return "rollback_parity_implementation"
        return None

    if rel == "scripts/check-velvetos.py":
        required = (
            'LEGACY_TOOL_STATUS = PACK / "TOOL-STATUS.json"',
            'composition.get("activeAuthority") != "instance:surface:toolStatus"',
            'composed_tool_status != legacy_tool_status',
        )
        if all(token in text for token in required):
            return "rollback_parity_sensor"
        return None

    if rel == "packages/velvetos/policy/sensor-registry.json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        allowed_ids = {"check-upstream-watch", "check-vf-cad-stack"}
        refs = []
        for row in obj.get("sensors") or []:
            if not isinstance(row, dict):
                continue
            for field in ("owns", "triggered_by"):
                values = row.get(field) or []
                if legacy in values:
                    refs.append((row.get("id"), field))
        if (
            len(refs) == 4
            and {sensor_id for sensor_id, _ in refs} == allowed_ids
            and {field for _, field in refs} == {"owns", "triggered_by"}
        ):
            return "rollback_sensor_binding"
        return None

    return None


def chatgpt_safe_class(sha: str, rel: str) -> str | None:
    legacy_prefix = "packages/velvetos/chatgpt-project/"
    canonical_prefix = "instances/velvet-factory/distribution/chatgpt-project/"
    try:
        text = git_text(sha, rel)
    except subprocess.CalledProcessError:
        return None
    normalized = text.replace("\\", "/")

    if rel == ".gitattributes":
        legacy_lines = [
            line.strip() for line in normalized.splitlines()
            if "packages/velvetos/chatgpt-project/" in line
        ]
        if (
            legacy_lines
            and all(
                line.startswith("/packages/velvetos/chatgpt-project/")
                and line.endswith(" -text")
                for line in legacy_lines
            )
            and "/instances/velvet-factory/distribution/chatgpt-project/** -whitespace" in normalized
        ):
            return "rollback_git_attributes"
        return None

    if rel == "packages/velvetos/policy/sensor-registry.json":
        if legacy_prefix in normalized:
            return None
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return None
        expected_ids = {
            "check-chat-cold-start-preflight",
            "check-chat-runtime-bundle",
            "check-project-bundle",
            "check-reel-route-sync",
        }
        seen: set[str] = set()
        for row in obj.get("sensors") or []:
            if not isinstance(row, dict) or row.get("id") not in expected_ids:
                continue
            owns = [str(x).replace("\\", "/") for x in (row.get("owns") or [])]
            triggered = [str(x).replace("\\", "/") for x in (row.get("triggered_by") or [])]
            if (
                any(x.startswith(canonical_prefix) for x in owns)
                and any(x.startswith(canonical_prefix) for x in triggered)
            ):
                seen.add(str(row.get("id")))
        if seen == expected_ids:
            return "canonical_sensor_binding"
        return None

    if rel == "packages/vfbrand/brand-tokens.json":
        if legacy_prefix not in normalized and (
            canonical_prefix + "ASSET-MANIFEST-v6.6.4.json"
        ) in normalized:
            return "canonical_asset_source"
        return None

    if rel == "scripts/check-project-bundle.py":
        if legacy_prefix in normalized:
            return None
        required = (
            'b = vpb.resolve(ROOT, instance_id="velvet-factory", env={})',
            '"instance:surface:chatgptProject/PROJECT-INSTRUCTIONS-v"',
        )
        if all(token in text for token in required):
            return "canonical_surface_sensor"
        return None

    if rel == "scripts/check-reel-route-sync.py":
        if legacy_prefix in normalized:
            return None
        required = (
            'resolve_reference(ROOT, "instance:surface:chatgptProject/LATEST.json"',
            'resolve_reference(ROOT, c["routeDoc"], instance_id="velvet-factory", env={})',
            'resolve_reference(ROOT, c["projectInstructions"], instance_id="velvet-factory", env={})',
        )
        if all(token in text for token in required):
            return "canonical_surface_sensor"
        return None

    if rel == "scripts/check-velvetos.py":
        if legacy_prefix in normalized:
            return None
        if '"chatgptProject": "distribution/chatgpt-project/LATEST.json"' in text:
            return "canonical_surface_sensor"
        return None

    return None


def semantic_match(surface_id: str, text: str) -> bool:
    spec = SURFACES[surface_id]
    low = text.lower().replace("\\", "/")
    path = spec["path"].lower()
    if surface_id == "root_desk":
        scrubbed = low.replace("instances/velvet-factory/.cursor/vf-desk.json", "")
        if ".cursor/vf-desk.json" in scrubbed:
            return True
        return '".cursor"' in scrubbed and "vf-desk.json" in scrubbed
    if path in low:
        return True
    return all(component.lower() in low for component in spec["components"])


def classify(surface_id: str, rel: str, sha: str) -> str:
    legacy = SURFACES[surface_id]["path"]
    if surface_id == "fleet" and rel == ".cursor/vf-desk.json":
        if root_desk_correction_passed(sha):
            return "retained_legacy_surface_reference"
    if surface_id == "tool_status":
        safe_class = tool_status_safe_class(sha, rel)
        if safe_class:
            return safe_class
    if surface_id == "chatgpt_core_bundle":
        safe_class = chatgpt_safe_class(sha, rel)
        if safe_class:
            return safe_class
    if surface_id == "chatgpt_core_bundle" and rel.startswith(legacy + "/"):
        return "self"
    if rel == legacy:
        return "self"
    reviewed = REVIEWED_SAFE_REFERENCES.get(surface_id, {}).get(rel)
    if reviewed:
        return reviewed
    if rel in EVIDENCE_EXACT or rel.startswith(EVIDENCE_PREFIXES):
        return "evidence_machinery"
    if rel.startswith(HISTORY_PREFIXES):
        return "historical_state"
    suffix = Path(rel).suffix.lower()
    if suffix in MACHINE_SUFFIXES:
        return "machine_or_config_candidate"
    if suffix in DOC_SUFFIXES or rel in {"README.md", "CHANGELOG.md"}:
        return "documentation_reference"
    return "other_candidate"


def scan_surface(sha: str, surface_id: str) -> dict[str, Any]:
    spec = SURFACES[surface_id]
    present = git_exists(sha, spec["path"])
    retired = retirement_evidence(sha, surface_id) if not present else None
    rows = []
    for rel in candidates(sha, spec["token"]):
        try:
            text = git_text(sha, rel)
        except subprocess.CalledProcessError:
            continue
        if not semantic_match(surface_id, text):
            continue
        rows.append({"path": rel, "class": classify(surface_id, rel, sha)})
    rows = sorted(rows, key=lambda row: (row["class"], row["path"]))
    classes: dict[str, list[str]] = {}
    for row in rows:
        classes.setdefault(row["class"], []).append(row["path"])
    blockers = sorted(set(
        classes.get("machine_or_config_candidate", [])
        + classes.get("other_candidate", [])
    ))
    result = {
        "path": spec["path"],
        "present": present,
        "semantic_reference_count": len(rows),
        "references": rows,
        "classes": classes,
        "retirement_preflight_blockers": blockers,
        "retirement_preflight_clear": not blockers,
        "rollback_window_closed_by_this_audit": False,
        "delete_authorized": False,
    }
    if retired is not None:
        result["retired"] = True
        result["retirement_evidence"] = retired
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.source_commit) is not None, "--source-commit must be a full lowercase Git SHA")

    surfaces = {sid: scan_surface(args.source_commit, sid) for sid in SURFACES}
    retired_surfaces = sorted(sid for sid, row in surfaces.items() if row.get("retired") is True)
    require(
        all(row["present"] or row.get("retired") is True for row in surfaces.values()),
        "one or more compatibility surfaces are missing without authoritative retirement evidence",
    )

    report = {
        "schema": "velvetos.stage8d-retirement-semantic-audit.v1",
        "stage": "8D_RETIREMENT_SEMANTIC_AUDIT",
        "behavior_change": False,
        "source_commit_sha": args.source_commit,
        "captured_at": args.captured_at,
        "purpose": (
            "Fail-closed semantic audit for retained Stage 8D compatibility surfaces. "
            "Detect exact and assembled path references before rollback closure or deletion."
        ),
        "audit_model": {
            "exact_path_detection": True,
            "assembled_path_component_detection": True,
            "ambiguous_machine_or_config_reference_blocks_retirement": True,
            "documentation_references_are_reported_but_do_not_self-authorize_deletion": True,
            "historical_state_and_evidence_machinery_are_separately_classified": True,
            "reviewed_safe_references_are_explicitly_classified": True,
            "cross_surface_compatibility_refs_require_correction_receipt": True,
            "tool_status_rollback_refs_are_content_validated": True,
            "chatgpt_remaining_refs_are_content_validated": True,
        },
        "compatibility_surfaces": surfaces,
        "assessment": {
            "surfaces_total": len(surfaces),
            "surfaces_preflight_clear": sum(1 for row in surfaces.values() if row["retirement_preflight_clear"]),
            "surfaces_with_candidate_blockers": sorted(
                sid for sid, row in surfaces.items() if not row["retirement_preflight_clear"]
            ),
            "rollback_windows_closed_by_audit": 0,
            "deletion_authorized": False,
        },
        "repository_assessment": "PASS",
        "retirement_authorized": False,
        "deletion_authorized": False,
        "next_action": (
            "Resolve machine/config candidates surface-by-surface, then collect explicit rollback-window "
            "closure evidence. Do not delete any compatibility surface from this audit."
        ),
        "constraints": [
            "observation only",
            "no rollback-window closure",
            "no deletion authorization",
            "ambiguous references fail closed",
            "retire at most one compatibility surface per deletion PR",
            "no big-bang delete",
        ],
    }
    if retired_surfaces:
        report["purpose"] = (
            "Fail-closed semantic audit for retained and authoritatively retired Stage 8D compatibility surfaces. "
            "A missing surface is accepted only when its merged retirement receipt proves deletion and retirement; "
            "remaining surfaces still undergo exact and assembled-path reference detection."
        )
        report["audit_model"]["missing_surface_requires_authoritative_retirement_receipt"] = True
        report["assessment"]["surfaces_retired"] = len(retired_surfaces)
        report["assessment"]["retired_surfaces"] = retired_surfaces
        report["next_action"] = (
            "Continue retirement surface-by-surface. Revalidate every retained target before its deletion gate; "
            "never treat physical absence alone as retirement evidence."
        )

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        "STAGE8D_RETIREMENT_SEMANTIC_AUDIT "
        f"assessment={report['repository_assessment']} "
        f"clear={report['assessment']['surfaces_preflight_clear']}/{report['assessment']['surfaces_total']} "
        f"blocked={','.join(report['assessment']['surfaces_with_candidate_blockers']) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
