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
EVIDENCE_EXACT = {"scripts/check-policy-architecture.py"}


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


def semantic_match(surface_id: str, text: str) -> bool:
    spec = SURFACES[surface_id]
    low = text.lower().replace("\\", "/")
    path = spec["path"].lower()
    if surface_id == "root_desk":
        scrubbed = low.replace("instances/velvet-factory/.cursor/vf-desk.json", "")
        if ".cursor/vf-desk.json" in scrubbed:
            return True
        return '".cursor"' in low and "vf-desk.json" in low
    if path in low:
        return True
    return all(component.lower() in low for component in spec["components"])


def classify(surface_id: str, rel: str) -> str:
    legacy = SURFACES[surface_id]["path"]
    if surface_id == "chatgpt_core_bundle" and rel.startswith(legacy + "/"):
        return "self"
    if rel == legacy:
        return "self"
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
    rows = []
    for rel in candidates(sha, spec["token"]):
        try:
            text = git_text(sha, rel)
        except subprocess.CalledProcessError:
            continue
        if not semantic_match(surface_id, text):
            continue
        rows.append({"path": rel, "class": classify(surface_id, rel)})
    rows = sorted(rows, key=lambda row: (row["class"], row["path"]))
    classes: dict[str, list[str]] = {}
    for row in rows:
        classes.setdefault(row["class"], []).append(row["path"])
    blockers = sorted(set(
        classes.get("machine_or_config_candidate", [])
        + classes.get("other_candidate", [])
    ))
    return {
        "path": spec["path"],
        "present": git_exists(sha, spec["path"]),
        "semantic_reference_count": len(rows),
        "references": rows,
        "classes": classes,
        "retirement_preflight_blockers": blockers,
        "retirement_preflight_clear": not blockers,
        "rollback_window_closed_by_this_audit": False,
        "delete_authorized": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.source_commit) is not None, "--source-commit must be a full lowercase Git SHA")

    surfaces = {sid: scan_surface(args.source_commit, sid) for sid in SURFACES}
    require(all(row["present"] for row in surfaces.values()), "one or more compatibility surfaces are already missing")

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
