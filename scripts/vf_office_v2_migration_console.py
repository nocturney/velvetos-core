#!/usr/bin/env python3
"""Read-only Office v2 Phase 0 Migration Console/report."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return rows


def build_report(
    capability_manifest: dict[str, Any],
    ledger: list[dict[str, Any]],
    project_state: dict[str, Any],
) -> dict[str, Any]:
    capabilities = capability_manifest.get("capabilities") or []
    status_counts = Counter(row.get("status", "UNKNOWN") for row in capabilities)
    verdict_counts = Counter(row.get("verdict", "UNKNOWN") for row in ledger)

    critical_not_available = sorted(
        row.get("capability_id")
        for row in capabilities
        if row.get("critical") is True
        and row.get("status") not in {"AVAILABLE", "PROHIBITED", "N_A"}
        and row.get("capability_id")
    )
    mutation_blockers = sorted(
        row.get("capability_id")
        for row in capabilities
        if row.get("side_effect") is True
        and row.get("status") in {"BLOCKED", "UNVERIFIED"}
        and row.get("capability_id")
    )

    last_smoke = None
    for row in reversed(ledger):
        smoke = row.get("smoke_result") or {}
        if smoke.get("status") not in {None, "NOT_RUN"}:
            last_smoke = {
                "change_id": row.get("change_id"),
                "status": smoke.get("status"),
                "evidence_ref": smoke.get("evidence_ref"),
            }
            break

    rollback = project_state.get("rollback_point") or {}
    report = {
        "schema": "velvetos.office-v2.migration-console-report.v0",
        "mode": "READ_ONLY",
        "generated_at": now_iso(),
        "current_phase": project_state.get("migration_phase"),
        "phase_gate": project_state.get("gate_status"),
        "production_capability_snapshot_id": capability_manifest.get("snapshot_id"),
        "production_capability_health": dict(sorted(status_counts.items())),
        "critical_not_available": critical_not_available,
        "mutation_blockers": mutation_blockers,
        "active_authorities": project_state.get("authority_refs") or [],
        "active_experiments": project_state.get("active_experiments") or [],
        "latest_smoke_result": last_smoke,
        "blockers": project_state.get("blockers") or [],
        "rollback_point": rollback,
        "evidence_links": sorted(set(
            list(project_state.get("receipt_refs") or [])
            + list(project_state.get("production_snapshot_refs") or [])
        )),
        "migration_verdict_counts": dict(sorted(verdict_counts.items())),
        "migration_entries": [
            {
                "change_id": row.get("change_id"),
                "owner": row.get("owner"),
                "change_class": row.get("change_class"),
                "verdict": row.get("verdict"),
                "target": row.get("target"),
                "smoke_result": row.get("smoke_result"),
                "evidence_refs": row.get("evidence_refs") or [],
            }
            for row in ledger
        ],
        "writes_performed": 0,
    }
    return report


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Office v2 Migration Console — read-only",
        "",
        f"Generated: {report['generated_at']}",
        f"Current phase: {report.get('current_phase')}",
        f"Gate: {(report.get('phase_gate') or {}).get('verdict')}",
        f"Capability snapshot: {report.get('production_capability_snapshot_id')}",
        "",
        "## Production capability health",
    ]
    for key, value in report.get("production_capability_health", {}).items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Critical gaps"])
    lines.extend([f"- {x}" for x in report.get("critical_not_available") or []] or ["- none"])

    lines.extend(["", "## Mutation blockers"])
    lines.extend([f"- {x}" for x in report.get("mutation_blockers") or []] or ["- none"])

    lines.extend(["", "## Active authorities"])
    lines.extend([f"- {x}" for x in report.get("active_authorities") or []] or ["- none"])

    lines.extend(["", "## Active experiments"])
    lines.extend([f"- {x}" for x in report.get("active_experiments") or []] or ["- none"])

    lines.extend(["", "## Latest smoke"])
    smoke = report.get("latest_smoke_result")
    lines.append(f"- {smoke}" if smoke else "- none")

    lines.extend(["", "## Blockers"])
    lines.extend([f"- {x}" for x in report.get("blockers") or []] or ["- none"])

    lines.extend(["", "## Rollback point", f"- {report.get('rollback_point')}"])

    lines.extend(["", "## Evidence links"])
    lines.extend([f"- {x}" for x in report.get("evidence_links") or []] or ["- none"])

    lines.extend(["", "## Migration ledger"])
    for row in report.get("migration_entries") or []:
        lines.append(
            f"- {row['change_id']} · {row['change_class']} · {row['verdict']} · {row['target']}"
        )
    lines.extend(["", "Writes performed by this report: 0", ""])
    return "\n".join(lines)


def self_test() -> dict[str, Any]:
    manifest = {
        "snapshot_id": "self-test",
        "capabilities": [
            {"capability_id": "read.ok", "critical": True, "status": "AVAILABLE", "side_effect": False},
            {"capability_id": "write.blocked", "critical": True, "status": "BLOCKED", "side_effect": True},
            {"capability_id": "print.command", "critical": True, "status": "PROHIBITED", "side_effect": True},
        ],
    }
    ledger = [{
        "change_id": "m1",
        "owner": "self-test",
        "change_class": "WORKTREE",
        "verdict": "VERIFIED",
        "target": "worktree://office-v2",
        "smoke_result": {"status": "PASS", "evidence_ref": "evidence://git"},
        "evidence_refs": ["evidence://git"],
    }]
    state = {
        "migration_phase": "PHASE_0",
        "gate_status": {"phase": "PHASE_0", "verdict": "PARTIAL", "reasons": ["test"]},
        "authority_refs": ["policy-registry"],
        "active_experiments": [],
        "blockers": ["write.blocked"],
        "rollback_point": {"available": True, "reference": "git://base", "instructions": "drop branch"},
        "receipt_refs": ["evidence://git"],
        "production_snapshot_refs": ["state://capabilities"],
    }
    report = build_report(manifest, ledger, state)
    ok = (
        report["mode"] == "READ_ONLY"
        and report["writes_performed"] == 0
        and report["current_phase"] == "PHASE_0"
        and report["mutation_blockers"] == ["write.blocked"]
        and "write.blocked" in report["critical_not_available"]
        and "print.command" not in report["critical_not_available"]
        and report["latest_smoke_result"]["status"] == "PASS"
    )
    return {"status": "PASS" if ok else "FAIL", "report": report}


def main() -> int:
    parser = argparse.ArgumentParser(description="Office v2 read-only migration console")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--capability-manifest")
    parser.add_argument("--ledger")
    parser.add_argument("--project-state")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()

    if args.self_test:
        payload = self_test()
        print(json.dumps(payload, ensure_ascii=False) if args.json else json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] == "PASS" else 1

    if not args.capability_manifest or not args.ledger or not args.project_state:
        parser.error("--capability-manifest, --ledger and --project-state are required")

    report = build_report(
        read_json(Path(args.capability_manifest)),
        read_jsonl(Path(args.ledger)),
        read_json(Path(args.project_state)),
    )
    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        out = Path(args.output_md)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(to_markdown(report), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False) if args.json else to_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
