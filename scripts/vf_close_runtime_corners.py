#!/usr/bin/env python3
"""One deterministic migration for the 2026-09-14 runtime closeout.

Safe to re-run. It edits existing authorities only; it does not create a second
scheduler, Control Plane, skill registry, or business database.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "velvetos" / "living-studio" / "REGISTRY.json"
BEST = ROOT / "packages" / "vfresearch" / "BEST-SKILLS.json"
OWNER_ACTIONS = ROOT / "docs" / "OWNER-ACTIONS-he.md"
LEDGER_README = ROOT / "office" / "ledger" / "README.md"

WRITER_MARKERS = {
    ".github/workflows/vfmedia-intake.yml": "packages/vfmedia/catalog.json packages/vfmedia/state packages/vfmedia/data office/control/inbox.json",
    ".github/workflows/readme-system-pulse.yml": "README.md",
    ".github/workflows/publish-bridge-cleanup.yml": "publish-bridge/assets publish-bridge/archive",
    ".github/workflows/velvetos-weekly-deck.yml": "docs/weekly-deck packages/vfbriefux/hq/weekly-deck.bento-doc.json",
}


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def close_registry() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    data["updatedAt"] = "2026-09-14"
    for skill in data.get("skills") or []:
        if skill.get("id") == "order-state-manager":
            skill["status"] = "EXISTING_COMPLETE"
            skill["activation"] = ".github/workflows/jobs-write-through.yml + vf_office.py jobs pull|push"
            skill["verification"] = "office/ledger/live/sync-receipt.json status=written dirty=false canonical_changed=true verifiedFrom=sheets_values_get"
            skill["note"] = "Google Sheet write-through commissioned with GitHub OIDC/WIF; canonical read-back is mandatory. Price changes remain red/human-authorized."
        if skill.get("id") == "daily-ops-commander" and "success" in skill:
            skill["success"] = "09:00 brief + Office Loop consume current Studio Pulse without inventing figures"

    wanted = {
        "print-engineering": (
            "EXISTING_EQUIVALENT",
            "python3 scripts/vf_living_studio_activation.py sweep --write",
            "vfprod router resolves; HQ Print remains false; activation receipt state=equivalent",
        ),
        "failure-museum": (
            "EXISTING_COMPLETE",
            "Office Control Plane activation sweep",
            "dead-letter projection executes and activation receipt records count/sources",
        ),
        "velvet-lab": (
            "EXISTING_COMPLETE",
            "product_idea intake + vf_living_studio_activation.py lab-result",
            "canonical experiments.jsonl event stream; result requires explicit evidence",
        ),
        "commercial-qa": (
            "EXISTING_EQUIVALENT",
            "production gates vfcost/vfcopy/PREFLIGHT + Living Studio behavioral probe",
            "fail-closed probe blocks bare DM/unverified ILS and requires quote inputs",
        ),
        "opportunity-intelligence": (
            "EXISTING_COMPLETE",
            "Office Control Plane activation sweep + Studio Pulse",
            "canonical radar executes against current jobs/media/followups and writes signal evidence",
        ),
        "invisible-work-detector": (
            "EXISTING_COMPLETE",
            "Studio Pulse + Office Control Plane activation sweep",
            "current jobs/followups/media/dead-letter/decisions scanned; signal evidence emitted",
        ),
    }
    for cap in data.get("livingCapabilities") or []:
        cid = cap.get("id")
        if cid in wanted:
            status, activation, verification = wanted[cid]
            cap["status"] = status
            cap["activation"] = activation
            cap["verification"] = verification
            cap["evidencePath"] = "packages/velvetos/living-studio/data/activation-latest.json"
    save_json(REGISTRY, data)


def close_best_skills() -> None:
    data = json.loads(BEST.read_text(encoding="utf-8"))
    data["schedulerAuthority"] = "Velvet Research Seat"
    data["timerName"] = "research-seat:best-skills-48h"
    data["standingNote"] = (
        "Owner standing order remains active. Research Seat is the canonical scheduler authority: "
        "run a Best Skills pass when lastPass is about 48h old; no external timer renewal is required."
    )
    data["lastTimerStatus"] = (
        "PROVEN_BY_RESEARCH_SEAT: lastPass/data artifact is the evidence; external Cursor subscriptions are not an authority."
    )
    data["freshnessContract"] = {
        "targetHours": 48,
        "graceHours": 4,
        "evidence": ["lastPass", "lastArtifact", "lastResult"],
        "onStale": "Research Seat executes the pass; do not create a second recurring automation",
    }
    save_json(BEST, data)


def add_skill_verification() -> int:
    roots = [ROOT / "packages", ROOT / ".agents", ROOT / ".claude", ROOT / ".codex", ROOT / ".cursor" / "skills"]
    changed = 0
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("SKILL.md"):
            rel = path.relative_to(ROOT).as_posix()
            if "/vendor/" in f"/{rel}" or "/third_party/" in f"/{rel}" or "/reference/" in f"/{rel}":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            low = text.lower()
            if any(token in low for token in ("verify", "verification", "check-", "proof", "evidence")):
                continue
            text = text.rstrip() + (
                "\n\n## Verification\n\n"
                "Before claiming completion, verify the routed target state or run the existing package/route sensor. "
                "Configuration, a draft, a command exit, or an agent statement alone is not success. "
                "If live/provider evidence is unavailable, report the state as `UNPROVEN`/blocked rather than COMPLETE.\n"
            )
            path.write_text(text, encoding="utf-8")
            changed += 1
    return changed


def add_writer_contracts() -> int:
    changed = 0
    for rel, allowed in WRITER_MARKERS.items():
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"missing machine writer workflow {rel}")
        text = path.read_text(encoding="utf-8")
        if "VELVET_MACHINE_WRITER_ALLOW:" in text:
            continue
        lines = text.splitlines()
        insert_at = 1 if lines and lines[0].startswith("name:") else 0
        lines.insert(insert_at, f"# VELVET_MACHINE_WRITER_ALLOW: {allowed}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        changed += 1
    return changed


def update_docs() -> None:
    if OWNER_ACTIONS.is_file():
        lines = OWNER_ACTIONS.read_text(encoding="utf-8").splitlines()
        out = []
        for line in lines:
            if line.startswith("| Jobs **write-through** |"):
                out.append(
                    "| Jobs **write-through** | **LIVE_PROVEN** via GitHub OIDC/WIF → Sheets API; `push_write_through` must write, read back, refresh cache and leave `dirty=false`. `write_pending_provider` remains a truthful degraded state on hosts without provider auth. |"
                )
            else:
                out.append(line)
        OWNER_ACTIONS.write_text("\n".join(out) + "\n", encoding="utf-8")
    if LEDGER_README.is_file():
        text = LEDGER_README.read_text(encoding="utf-8")
        marker = "GitHub OIDC/WIF write-through"
        if marker not in text:
            text = text.rstrip() + (
                "\n\n## GitHub OIDC/WIF write-through\n\n"
                "The canonical background writer is `.github/workflows/jobs-write-through.yml`. It mints a short-lived Google token with Drive + Sheets scopes, runs `jobs pull --force` before commissioning writes, runs `jobs push`, requires post-write read-back evidence, and persists `sync-receipt.json`. No long-lived Google JSON key is stored in the repository.\n"
            )
            LEDGER_README.write_text(text, encoding="utf-8")


def main() -> int:
    close_registry()
    close_best_skills()
    skills_changed = add_skill_verification()
    writers_changed = add_writer_contracts()
    update_docs()
    print(f"OK runtime closeout migration skill_verification_added={skills_changed} writer_contracts_added={writers_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
