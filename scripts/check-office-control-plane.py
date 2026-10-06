#!/usr/bin/env python3
"""Validate Office Control Plane — unify existing SoT. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANE = ROOT / "office" / "control-plane.json"
CONTROL = ROOT / "office" / "control"
CLI = ROOT / "scripts" / "vf_control_plane.py"
AGENTS = ROOT / "packages" / "vfops" / "AGENTS.md"
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"
ORCHESTRA = ROOT / "constitution" / "ORCHESTRA.md"
CONSTITUTION = ROOT / "constitution" / "CONSTITUTION.md"
LEDGER_README = ROOT / "office" / "ledger" / "README.md"
LOOP_MD = ROOT / "packages" / "vfops" / "hq" / "LOOP.md"

REQUIRED_CONTROL = (
    "inbox.json",
    "dead-letter.json",
    "followups.json",
    "decisions.jsonl",
    "POLICY.md",
    "README.md",
)

REQUIRED_SOT_KEYS = (
    "policy",
    "jobs",
    "media",
    "content_calendar",
    "content_approval",
    "production_completion",
    "office_loop",
    "manager_handoff",
    "decisions",
    "dead_letter",
    "followups",
    "public_cta",
    "publication_states",
    "instagram_capabilities",
    "profile_desired",
    "feed_audit",
)


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not PLANE.is_file():
        fail("missing office/control-plane.json")
    if not CLI.is_file():
        fail("missing scripts/vf_control_plane.py")
    for name in REQUIRED_CONTROL:
        path = CONTROL / name
        if not path.is_file():
            fail(f"missing office/control/{name}")

    plane = json.loads(PLANE.read_text(encoding="utf-8"))
    if plane.get("name") != "velvetos-office-control-plane":
        fail("control-plane.json name mismatch")
    sot = plane.get("sourcesOfTruth") or {}
    for key in REQUIRED_SOT_KEYS:
        if key not in sot:
            fail(f"sourcesOfTruth missing {key}")

    # Authoritative paths must exist (globs excluded). The live jobs cache is gitignored,
    # so a read-only sensor accepts the canonical bootstrap template when no cache exists.
    jobs_live = ROOT / "office" / "ledger" / "live" / "jobs.csv"
    jobs_tmpl = ROOT / "office" / "ledger" / "templates" / "jobs.csv"
    if not jobs_live.is_file() and not jobs_tmpl.is_file():
        fail("missing office/ledger/live/jobs.csv and bootstrap template office/ledger/templates/jobs.csv")
    jobs_contract_path = jobs_live if jobs_live.is_file() else jobs_tmpl

    must_exist = [
        ROOT / "constitution" / "CONSTITUTION.md",
        ROOT / "constitution" / "ORCHESTRA.md",
        ROOT / "constitution" / "PUBLIC_CTA.md",
        jobs_contract_path,
        ROOT / "packages" / "vfmedia" / "catalog.json",
        ROOT / "docs" / "MEDIA-VAULT.md",
        ROOT / "packages" / "vfgrowth" / "CALENDAR.md",
        ROOT / "packages" / "vfgrowth" / "data" / "approval-queue.json",
        ROOT / "packages" / "vfgrowth" / "data" / "feed-audit.json",
        ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.json",
        ROOT / "packages" / "vfigos" / "CAPABILITIES.json",
        ROOT / "packages" / "vfigos" / "PROFILE-DESIRED.json",
        ROOT / "packages" / "vfops" / "LOOP.json",
        CONTROL / "dead-letter.json",
        CONTROL / "followups.json",
        CONTROL / "decisions.jsonl",
        CONTROL / "POLICY.md",
    ]
    for path in must_exist:
        if not path.exists():
            fail(f"authoritative path missing: {path.relative_to(ROOT)}")

    # No duplicate dead-letter / followups authority
    harness_q = ROOT / "packages" / "vfharness" / "dead-letter" / "queue.json"
    if harness_q.is_file():
        hq = json.loads(harness_q.read_text(encoding="utf-8"))
        if hq.get("sourceOfTruth") != "office/control/dead-letter.json":
            fail("harness dead-letter queue must pointer to office/control/dead-letter.json")
        if hq.get("items"):
            fail("harness dead-letter queue must not hold authoritative items")
    legacy_fu = ROOT / "packages" / "vfgrowth" / "data" / "production-content-followups.json"
    if legacy_fu.is_file():
        lf = json.loads(legacy_fu.read_text(encoding="utf-8"))
        if lf.get("sourceOfTruth") != "office/control/followups.json":
            fail("production-content-followups.json must pointer to office/control/followups.json")
        if lf.get("followups"):
            fail("legacy followups pointer must keep followups=[]")

    # PUBLIC_CTA + publication states present in SoT map
    if sot.get("public_cta") != "constitution/PUBLIC_CTA.md":
        fail("sourcesOfTruth.public_cta mismatch")
    if sot.get("publication_states") != "packages/vfigos/PUBLICATION-STATES.json":
        fail("sourcesOfTruth.publication_states mismatch")
    pub_states = json.loads(
        (ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.json").read_text(encoding="utf-8")
    )
    state_ids = {s.get("id") for s in pub_states.get("states") or []}
    for need in ("prepared", "scheduled", "uploadAccepted", "publishRequested", "liveVerified"):
        if need not in state_ids:
            fail(f"PUBLICATION-STATES missing {need}")

    # No parallel SoT maps
    for rogue in (
        ROOT / "office" / "sources-of-truth.json",
        ROOT / "packages" / "vfops" / "control-plane.json",
        CONTROL / "sources.json",
    ):
        if rogue.is_file():
            fail(f"duplicate source-of-truth map: {rogue.relative_to(ROOT)}")

    # One media catalog
    cat = json.loads((ROOT / "packages" / "vfmedia" / "catalog.json").read_text(encoding="utf-8"))
    if cat.get("oneCatalog") is not True:
        fail("vfmedia catalog must set oneCatalog true")

    # Inbox buckets
    inbox = json.loads((CONTROL / "inbox.json").read_text(encoding="utf-8"))
    for bucket in ("content", "production", "sales", "admin", "approvals", "blocked", "unknown"):
        if bucket not in (inbox.get("buckets") or {}):
            fail(f"inbox missing bucket {bucket}")

    # Docs / constitution pointers
    for path, needle in (
        (CONSTITUTION, "office/control-plane.json"),
        (ORCHESTRA, "vf_control_plane.py"),
        (LOOP_MD, "vf_control_plane.py"),
        (LEDGER_README, "control-plane"),
    ):
        text = path.read_text(encoding="utf-8")
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} must mention {needle}")

    agents = AGENTS.read_text(encoding="utf-8")
    if "check-office-control-plane.py" not in agents:
        fail("AGENTS.md sensor table must list check-office-control-plane.py")

    loop = json.loads(LOOP.read_text(encoding="utf-8"))
    guide_paths = {g.get("path") for g in loop.get("guides") or []}
    if "office/control-plane.json" not in guide_paths:
        fail("LOOP.json guides must include office/control-plane.json")

    # Execute once, validate once: the workflow owns refresh/mutation commands.
    # This sensor validates CLI wiring and the evidence already produced by that owner.
    cli_src = CLI.read_text(encoding="utf-8")
    for command, function_name in (
        ("status", "cmd_status"),
        ("watchdog", "cmd_watchdog"),
        ("gaps", "cmd_gaps"),
        ("handoff", "cmd_handoff"),
        ("followups", "cmd_followups"),
        ("review", "cmd_review"),
        ("memory-hygiene", "cmd_memory_hygiene"),
        ("simulate", "cmd_simulate"),
        ("selftest", "cmd_selftest"),
    ):
        if f'def {function_name}(' not in cli_src:
            fail(f"vf_control_plane.py missing handler for {command}")
        if f'sub.add_parser("{command}")' not in cli_src:
            fail(f"vf_control_plane.py missing parser wiring for {command}")

    workflow = (ROOT / ".github" / "workflows" / "office-control-plane.yml").read_text(encoding="utf-8")
    for command in ("watchdog", "memory-hygiene", "gaps", "handoff"):
        if f"vf_control_plane.py {command}" not in workflow:
            fail(f"office-control-plane.yml must own {command} execution")

    handoff_json = CONTROL / "HANDOFF.json"
    handoff_he = CONTROL / "HANDOFF-he.md"
    if not handoff_json.is_file():
        fail("missing existing office/control/HANDOFF.json evidence")
    if not handoff_he.is_file():
        fail("missing existing office/control/HANDOFF-he.md evidence")
    handoff = json.loads(handoff_json.read_text(encoding="utf-8"))
    for key in ("updatedAt", "active_now", "waiting", "failed", "authoritative_sources"):
        if key not in handoff:
            fail(f"HANDOFF.json missing {key}")
    if (handoff.get("authoritative_sources") or {}).get("manager_handoff") != "office/control/HANDOFF.json":
        fail("HANDOFF.json manager_handoff authority mismatch")

    # Locks present
    locks = set(plane.get("locks") or [])
    for need in (
        "no-duplicate-sources-of-truth",
        "no-duplicate-dead-letter",
        "no-duplicate-followups",
        "no-invented-prices",
        "no-auto-dm",
        "scheduling-is-not-publication",
        "live-requires-verification",
        "public-cta-instagram-message",
        "ig-needsauth-not-fake-ready",
    ):
        if need not in locks:
            fail(f"control-plane locks missing {need}")

    print("OK office control plane")


if __name__ == "__main__":
    main()
