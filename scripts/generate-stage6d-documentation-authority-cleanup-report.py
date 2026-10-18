#!/usr/bin/env python3
"""Generate/check Reform v2 Stage 6D documentation-authority cleanup evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6d-documentation-authority-cleanup.json"

GROUPS = {
    "seats": [
        "constitution/README.md",
        "constitution/TEAM.md",
        "constitution/STUDIO.md",
        "packages/velvetos/LOCK.md",
        "packages/vfgraft/MAP.md",
        "packages/vfharness/EMBED.md",
        "packages/vfmem/README.md",
        ".agents/product-marketing.md",
    ],
    "morning_brief": [
        ".cursor/rules/velvet-factory-desk.mdc",
        ".cursor/skills/vf-morning-brief/SKILL.md",
        ".cursor/skills/vf-organic-growth/SKILL.md",
        "instances/velvet-factory/.cursor/vf-desk.json",
        "constitution/CONSTITUTION.md",
        "constitution/ORCHESTRA.md",
        "constitution/ORGANIC_GROWTH.md",
        "constitution/README.md",
        "constitution/SEND.md",
        "docs/500-AGENTS.md",
        "docs/FAILOVER.md",
        "docs/ORCHESTRATORS.md",
        "docs/SHARE-EMBED-he.md",
        "docs/chief-of-staff/LOOPS.md",
        "docs/chief-of-staff/PACKS-CATALOG.md",
        "packages/manifest.json",
        "packages/vfagents/playbooks/daily-research.md",
        "packages/vfagents/playbooks/meeting-notes.md",
        "packages/vfbooks/LEDGER.md",
        "packages/vfbooks/ORDERS.md",
        "packages/vfbooks/SKILL.md",
        "packages/vfbriefux/SKILL.md",
        "packages/vfbriefux/hq/GROWTH-BRIEF.md",
        "packages/vfbriefux/hq/PACKET.md",
        "packages/vfbriefux/hq/brief-email.html",
        "packages/vfcopy/SOFT-TOOLS-CONTRACT.md",
        "packages/vfcopy/hq/reader-first-he.md",
        "packages/vfcovers/DRAFT.md",
        "packages/vfe2b/DEER-FLOW-PATTERNS.md",
        "packages/vfe2b/EMBED.md",
        "packages/vfe2b/ORCHESTRATORS.md",
        "packages/vfe2b/orchestrators.json",
        "packages/vfgraft/graph/morning-job.md",
        "packages/vfgrowth/ORGANIC-GROWTH.md",
        "packages/vfgrowth/PRODUCTION-CONTENT.md",
        "packages/vfgrowth/hq/PROFILE-TO-WHATSAPP.md",
        "packages/vfharness/PERMISSIONS.md",
        "packages/vfharness/playbooks/grok-failover.md",
        "packages/vfharness/playbooks/grok-outage-tools.md",
        "packages/vfinsights/SKILL.md",
        "packages/vfops/BRIEF.md",
        "packages/vfops/data/ARTIFACT-INDEX.md",
        "packages/vfops/data/owner-memory.md",
        "packages/vfops/hq/DAILY-RETRO.md",
        "packages/vfops/hq/GATES.md",
        "packages/vfops/hq/RETRO-SIGNALS.md",
        "packages/vfresearch/hq/MAKERWORLD-SCAN.md",
    ],
    "public_cta": [
        ".cursor/rules/ui-finish-gate-reviewer.mdc",
        ".cursor/skills/vf-fcc-offload/SKILL.md",
        ".cursor/skills/vf-makers/SKILL.md",
        ".cursor/skills/vf-openmontage/SKILL.md",
        "instances/velvet-factory/.cursor/vf-desk.json",
        "constitution/ORCHESTRA.md",
        "constitution/tags.md",
        "docs/FAILOVER.md",
        "packages/vfagents/playbooks/reflection-before-send.md",
        "packages/vfbriefux/hq/references/excalidraw-patterns.md",
        "packages/vfcopy/BIO.md",
        "packages/vfcopy/hq/templates/organic-story-poll.md",
        "packages/vfe2b/crews/run.md",
        "packages/vfharness/layers.json",
        "packages/vfharness/playbooks/agent-architecture-audit.md",
        "packages/vfmakers/EMBED.md",
        "packages/vfmakers/EXAMPLES.md",
        "packages/vfmakers/LOCK.md",
        "packages/vfmakers/catalog.json",
        "packages/vfmakers/crews/content-rotation.md",
        "packages/vfmem/catalog.json",
        "packages/vfmskill/catalog.json",
        "packages/vfmskill/hq/PLAYBOOK.md",
        "packages/vfom/crews/reference-plan.md",
        "packages/vfops/BRIEF.md",
        "packages/vfops/data/owner-memory.md",
        "packages/vfops/hq/PIPELINE-BOARD.md",
    ],
    "send_authority": [
        ".agents/product-marketing.md",
        "docs/500-AGENTS.md",
        "docs/MARKETING-SKILLS.md",
        "docs/OPENMONTAGE.md",
        "docs/SHARE-EMBED-he.md",
        "packages/vfagents/SKIP.md",
        "packages/vfagents/fit.json",
        "packages/vfagents/playbooks/caption-draft.md",
        "packages/vfagents/playbooks/email-draft.md",
        "packages/vfbiz/CHAIN.md",
        "packages/vfbriefux/SKILL.md",
        "packages/vfbriefux/hq/BENTO.md",
        "packages/vfdsh/EMBED.md",
        "packages/vfdsh/LOCK.md",
        "packages/vfdsh/catalog.json",
        "packages/vfdsh/crews/design-assets.md",
        "packages/vfgrowth/hq/PLAYBOOK.md",
        "packages/vfgrowth/hq/rotation/INDEX.md",
        "packages/vfigos/SKIP.md",
        "packages/vfmakers/LOCK.md",
        "packages/vfmakers/README.md",
        "packages/vfmakers/catalog.json",
        "packages/vfmakers/crews/content-rotation.md",
        "packages/vfmskill/README.md",
        "packages/vfmskill/SKILL.md",
        "packages/vfmskill/catalog.json",
        "packages/vfmskill/hq/PLAYBOOK.md",
        "packages/vfresearch/hq/PLAYBOOK.md",
        "packages/vfdsh/ORIGIN.md",
        "packages/vffcc/ORIGIN.md",
        "packages/vfgraft/ORIGIN.md",
        "packages/vfharness/ORIGIN.md",
        "packages/vfmakers/ORIGIN.md",
        "packages/vfmem/ORIGIN.md",
        "packages/vfmskill/ORIGIN.md",
        "packages/vfom/ORIGIN.md",
    ],
    "instance_identity": [
        "README.md",
        "constitution/TENANT.md",
        "constitution/INSTANCE.md",
        "docs/chief-of-staff/GATES-AND-ESCALATION.md",
        "docs/chief-of-staff/SYSTEM-MAP.md",
        "packages/README.md",
        "packages/manifest.json",
        "packages/velvetos/CHANNELS.md",
        "packages/velvetos/PIPELINE.md",
        "packages/velvetos/PROJECT-REQUEST-GATE.md",
        "packages/vfgraft/graph/pipeline.md",
    ],
}

FORBIDDEN = {
    "seats": [
        r"חמישה מושבים", r"5 seats", r"five seats", r"5 מושבים",
    ],
    "morning_brief": [
        r"בריף 07:00", r"07:00 brief", r"brief 07:00",
        r"07:00 approval pack",
    ],
    "public_cta": [
        r"CTA is WhatsApp 050-2517000", r"CTA הוא וואטסאפ",
        r"CTA: WhatsApp", r"CTA: וואטסאפ", r"CTA וואטסאפ 050",
        r"הוק = וואטסאפ", r"Hook = WhatsApp",
    ],
    "send_authority": [
        r"Grok sends", r"Grok Bot sends", r"Grok שולח",
        r"stay on Grok Bot", r"HQ לא שולח Instagram",
        r"HQ לא שולח.*Gmail",
    ],
    "instance_identity": [
        r"Active tenant:", r"active tenant remains", r"Tenant ייחוס פעיל",
        r"tenant profiles", r"packages/velvetos/tenants/<id>\.json",
        r"הריפו = \*\*VelvetOS — Velvet Factory\*\*",
    ],
}

CANONICAL = {
    "seats": {
        "path": "constitution/TEAM.md",
        "markers": ["# שישה מושבים"],
    },
    "morning_brief": {
        "path": "packages/vfops/ROUTINE.md",
        "markers": ["Velvet Morning Brief", "manual/event-driven", "Morning Green"],
    },
    "public_cta": {
        "path": "constitution/PUBLIC_CTA.md",
        "markers": ["PUBLIC_CURRENT_CTA", "Instagram"],
    },
    "send_authority": {
        "path": "constitution/SEND.md",
        "markers": ["HQ", "Grok Bot", "גיבוי אופציונלי"],
    },
    "instance_identity": {
        "path": "constitution/TENANT.md",
        "markers": ["legacy redirect", "VelvetOS Core", "אינו"],
    },
}

HISTORICAL_REQUIRED = {
    "packages/vfops/OUTAGE-5D.md": ["HISTORICAL / SUPERSEDED", "Historical evidence only"],
}

STAGE6C = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6c-dcc-capability-gating.json"


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    return path.read_text(encoding="utf-8", errors="strict")


def build_report() -> dict:
    violations: list[dict[str, str]] = []
    checked_files: set[str] = set()

    for group, files in GROUPS.items():
        for rel in files:
            checked_files.add(rel)
            try:
                text = read(rel)
            except Exception as exc:
                violations.append({"group": group, "path": rel, "rule": "missing_or_unreadable", "detail": str(exc)})
                continue
            for pattern in FORBIDDEN[group]:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    violations.append({"group": group, "path": rel, "rule": "forbidden_active_wording", "detail": pattern})

    canonical_checks: dict[str, bool] = {}
    for group, spec in CANONICAL.items():
        try:
            text = read(spec["path"])
            ok = all(marker in text for marker in spec["markers"])
        except Exception:
            ok = False
        canonical_checks[group] = ok
        if not ok:
            violations.append({"group": group, "path": spec["path"], "rule": "canonical_marker_missing", "detail": " | ".join(spec["markers"])})

    historical_checks: dict[str, bool] = {}
    for rel, markers in HISTORICAL_REQUIRED.items():
        try:
            text = read(rel)
            ok = all(marker in text for marker in markers)
        except Exception:
            ok = False
        historical_checks[rel] = ok
        if not ok:
            violations.append({"group": "historical_boundary", "path": rel, "rule": "historical_marker_missing", "detail": " | ".join(markers)})

    dcc_ok = False
    try:
        stage6c = json.loads(STAGE6C.read_text(encoding="utf-8"))
        acc = stage6c.get("acceptance") or {}
        dcc_ok = (
            stage6c.get("repository_acceptance") == "PASS"
            and acc.get("recovery_baseline_is_not_allowlist") is True
            and acc.get("exact_version_match_is_not_required") is True
        )
    except Exception:
        dcc_ok = False
    if not dcc_ok:
        violations.append({
            "group": "dcc_wording_boundary",
            "path": str(STAGE6C.relative_to(ROOT)).replace("\\", "/"),
            "rule": "stage6c_recovery_baseline_contract_missing",
            "detail": "Creative/DCC version truth must remain recovery-baseline, not known-good allowlist",
        })

    acceptance = {
        "canonical_team_is_six_seats": canonical_checks.get("seats", False) and not any(v["group"] == "seats" for v in violations),
        "owner_morning_brief_is_0900_and_0700_is_readiness_only": canonical_checks.get("morning_brief", False) and not any(v["group"] == "morning_brief" for v in violations),
        "public_cta_is_instagram_message_not_whatsapp": canonical_checks.get("public_cta", False) and not any(v["group"] == "public_cta" for v in violations),
        "hq_is_gmail_instagram_sender_and_grok_is_optional_backup": canonical_checks.get("send_authority", False) and not any(v["group"] == "send_authority" for v in violations),
        "instance_identity_is_context_binding_not_parallel_policy_authority": canonical_checks.get("instance_identity", False) and not any(v["group"] == "instance_identity" for v in violations),
        "superseded_failover_doc_is_explicitly_historical": all(historical_checks.values()),
        "dcc_docs_use_stage6c_recovery_baseline_semantics": dcc_ok,
    }

    return {
        "schema": "velvetos.stage6d-documentation-authority-cleanup.v1",
        "stage": "6D",
        "behavior_change": False,
        "scope": "active documentation/skill/pack authority wording; historical evidence remains historical",
        "canonical_sources": {
            "team": "constitution/TEAM.md",
            "morning_brief_clock": "packages/vfops/ROUTINE.md",
            "public_cta": "constitution/PUBLIC_CTA.md",
            "send": "constitution/SEND.md",
            "core_instance_identity": ["packages/velvetos/CORE.json", "constitution/INSTANCE.md", "packages/velvetos/REPOS.md"],
            "dcc_version_semantics": "packages/velvetos/policy/reports/stage6c-dcc-capability-gating.json",
        },
        "historical_policy": {
            "rewrite_dated_evidence": False,
            "active_superseded_docs_must_be_marked_historical": True,
            "known_historical_doc_markers": HISTORICAL_REQUIRED,
        },
        "checked_file_count": len(checked_files),
        "checked_groups": {name: len(files) for name, files in GROUPS.items()},
        "canonical_checks": canonical_checks,
        "historical_checks": historical_checks,
        "violations": violations,
        "acceptance": acceptance,
        "repository_acceptance": "PASS" if all(acceptance.values()) and not violations else "FAIL",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--output", type=Path, default=OUT)
    ns = ap.parse_args()
    report = build_report()
    rendered = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    out = ns.output if ns.output.is_absolute() else ROOT / ns.output

    if ns.check:
        if not out.is_file():
            print(f"FAIL missing Stage 6D report: {out.relative_to(ROOT)}", file=sys.stderr)
            return 1
        if out.read_bytes() != rendered:
            print("FAIL Stage 6D report is stale; regenerate it", file=sys.stderr)
            return 1
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(rendered)

    print(
        "STAGE6D_DOC_AUTHORITY "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(1 for value in report['acceptance'].values() if value)}/{len(report['acceptance'])} "
        f"files={report['checked_file_count']} violations={len(report['violations'])}"
    )
    if report["violations"]:
        for row in report["violations"]:
            print(f"FAIL {row['group']} {row['path']}: {row['rule']} {row['detail']}", file=sys.stderr)
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
