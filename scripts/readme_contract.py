#!/usr/bin/env python3
"""Living README contract for pull requests.

Material capability/runtime changes under packages/, office/, scripts/,
.github/workflows/ or constitution/ must update README.md in the same PR
(README.md "Living README contract").

Routine *output* is not a capability change. The protected Grok routines
(automation/grok/manifest.json, packages/vfops/ROUTINE.md) and the machine
workflows write dated artifacts, checkpoints and data files; requiring a README
edit for those made every routine PR fail before the real sensors ran. Paths in
ROUTINE_OUTPUT below are exempt. Everything else under the capability roots
(code, config, contracts, playbooks, pack docs) still requires README.md.

Usage:
  python3 scripts/readme_contract.py --base <sha> --head <sha>   # PR gate (merge-base diff)
  python3 scripts/readme_contract.py --files a b c               # classify explicit paths
  python3 scripts/readme_contract.py --selftest
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CAPABILITY_ROOTS = re.compile(r"^(packages/|office/|scripts/|\.github/workflows/|constitution/)")

# (pattern, owner/reason) — routine and machine-workflow outputs only.
ROUTINE_OUTPUT: tuple[tuple[str, str], ...] = (
    (r"^packages/[^/]+/data/", "pack data files (research.md, retro-signals, growth-brief, publications, token-watch, ...)"),
    (r"^packages/[^/]+/state/", "task checkpoints / runtime state (vfharness/state, vfmedia/state)"),
    (r"^packages/vfresearch/sources/", "Research Seat / weekly / Best Skills / MakerWorld artifacts"),
    (r"^packages/vfresearch/(LINKS|BEST-SKILLS)\.json$", "weekly links review + Best Skills pass freshness"),
    (r"^packages/vfops/BRIEF-\d{4}-\d{2}-\d{2}\.md$", "Morning Brief factual artifact"),
    (r"^packages/vfops/hq/brief-\d{4}-\d{2}-\d{2}[^/]*\.json$", "Morning Brief HQ artifact"),
    (r"^packages/vfops/out/", "Morning Green / Gmail send request / brief outputs"),
    (r"^packages/vfmedia/catalog\.json$", "Media Vault intake catalog (vfmedia-intake.yml)"),
    (r"^packages/vfbriefux/hq/weekly-deck\.bento-doc\.json$", "weekly deck output (velvetos-weekly-deck.yml)"),
    (r"^packages/velvetos/living-studio/data/", "Living Studio activation evidence (office-control-plane.yml)"),
    (r"^office/control/(HANDOFF\.json|HANDOFF-he\.md|inbox\.json|followups\.json|dead-letter\.json|decisions\.jsonl)$", "Office Control Plane runtime state"),
    (r"^office/ledger/live/", "Jobs write-through receipt (jobs-write-through.yml)"),
    (r"^office/learning/(failure-museum|lab)/", "office learning evidence"),
)
_COMPILED = tuple((re.compile(p), why) for p, why in ROUTINE_OUTPUT)


def exemption(path: str) -> str | None:
    for rx, why in _COMPILED:
        if rx.search(path):
            return why
    return None


def classify(paths: list[str]) -> tuple[list[str], list[str]]:
    """Return (capability paths that require README.md, exempt routine-output paths)."""
    need, exempt = [], []
    for p in paths:
        if not CAPABILITY_ROOTS.search(p):
            continue
        (exempt if exemption(p) else need).append(p)
    return need, exempt


def changed_files(base: str, head: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"FAIL git diff {base}...{head}: {proc.stderr.strip()}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def gate(paths: list[str]) -> int:
    need, exempt = classify(paths)
    if exempt:
        print(f"Routine-output paths exempt from the README requirement ({len(exempt)}):")
        for p in exempt:
            print(f"  - {p}")
    if need and "README.md" not in paths:
        print("::error::Capability/runtime files changed without README.md. VelvetOS uses a living README; "
              "update the capability/status map in this PR or narrow the change to a documented exemption "
              "(scripts/readme_contract.py ROUTINE_OUTPUT).")
        print("Changed capability-sensitive files:")
        for p in need:
            print(f"  - {p}")
        return 1
    print("OK Living README contract" + (" (README.md updated)" if "README.md" in paths else ""))
    return 0


SELFTEST = {
    # routine outputs -> exempt
    "packages/vfops/data/research.md": False,
    "packages/vfresearch/sources/2026-09-25-weekly-links.md": False,
    "packages/vfresearch/LINKS.json": False,
    "packages/vfresearch/BEST-SKILLS.json": False,
    "packages/vfharness/state/weekly-research-2026-09-25.json": False,
    "packages/vfharness/state/openpost-v4.36.3-staging-2026-09-26/checkpoint.json": False,
    "packages/vfops/BRIEF-2026-09-26.md": False,
    "packages/vfops/hq/brief-2026-09-26.json": False,
    "packages/vfops/hq/brief-2026-09-22-v10.3.json": False,
    "packages/vfops/out/gmail-send-request.json": False,
    "packages/vfmedia/catalog.json": False,
    "packages/vfmedia/state/intake-runner.json": False,
    "packages/vfbriefux/hq/weekly-deck.bento-doc.json": False,
    "packages/velvetos/living-studio/data/activation-latest.json": False,
    "office/control/HANDOFF.json": False,
    "office/ledger/live/sync-receipt.json": False,
    "office/learning/failure-museum/entries.jsonl": False,
    # capability / contract / code -> README still required
    "packages/vfigos/OPENPOST.json": True,
    "packages/vfigos/OPENPOST.md": True,
    "packages/vfops/ROUTINE.md": True,
    "packages/vfops/LOOP.json": True,
    "packages/vfops/gmail_brief_request.py": True,
    "packages/vfops/hq/capabilities.json": True,
    "packages/vfresearch/WEEKLY.md": True,
    "packages/vfresearch/hq/MAKERWORLD-SCAN.md": True,
    "packages/vfprod/TEXT-TO-CAD.md": True,
    "office/control/POLICY.md": True,
    "office/control-plane.json": True,
    "office/learning/SCENARIOS.md": True,
    "scripts/check-all.py": True,
    ".github/workflows/check-all.yml": True,
    "constitution/SEND.md": True,
}


def selftest() -> int:
    bad = []
    for path, requires in SELFTEST.items():
        need, _ = classify([path])
        if bool(need) != requires:
            bad.append(f"{path}: expected {'README required' if requires else 'exempt'}")
    # PR-level behaviour
    if gate(["packages/vfops/data/research.md", "packages/vfresearch/LINKS.json"]) != 0:
        bad.append("routine-only PR must pass")
    if gate(["packages/vfigos/OPENPOST.json", "packages/vfharness/state/x.json"]) != 1:
        bad.append("contract change without README must fail")
    if gate(["packages/vfigos/OPENPOST.json", "README.md"]) != 0:
        bad.append("contract change with README must pass")
    if bad:
        for b in bad:
            print(f"FAIL readme-contract selftest: {b}", file=sys.stderr)
        return 1
    print(f"OK readme-contract selftest cases={len(SELFTEST) + 3} exemptions={len(ROUTINE_OUTPUT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.files is not None:
        return gate(args.files)
    if not (args.base and args.head):
        ap.error("--base and --head are required (or --files / --selftest)")
    return gate(changed_files(args.base, args.head))


if __name__ == "__main__":
    raise SystemExit(main())
