#!/usr/bin/env python3
"""Refuse a new private LAN address or Chris home path in tracked files.

Historical receipts whose bytes are hash-pinned, live host launchers, and the
Windows path-contract needle stay on the allowlist. A tracked file outside
that list fails when it contains a 192.168 address or a Chris home prefix.
An allowlist entry that no longer matches fails too, so the list cannot rot.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAN = re.compile(r"192\.168\.\d{1,3}\.\d{1,3}")
HOME = re.compile(r"(?:[A-Za-z]:[/\\]+Users[/\\]+Chris|/[Uu]sers/[Cc]hris)\b")

# Hash-pinned receipts and lab scripts, live runtime paths, and detectors.
# Do not add a file here to hide a new occurrence. Remove a row when its
# pin or live path is gone.
ALLOWLIST = frozenset({
    ".cursor/rules/threat-intelligence-analyst.mdc",
    "docs/implementation/office-v2/phase2/p0-authenticated-two-host-external-fs-receiver-lab-2026-10-10.json",
    "docs/implementation/office-v2/phase2/p0-authenticated-two-host-external-fs-receiver-lab-2026-10-10.md",
    "docs/implementation/office-v2/phase2/p0-dagu-fleet-idle-cleanup-2026-10-10.json",
    "docs/implementation/office-v2/phase2/p0-etcd-two-host-real-provider-atomic-kv-2026-10-10.json",
    "docs/implementation/office-v2/phase2/p0-local-agent-envelope-lab-2026-10-08.json",
    "docs/implementation/office-v2/phase2/p0-mac-origin-windows-real-github-ref-cas-2026-10-10.json",
    "docs/implementation/office-v2/phase2/p0-mac-origin-windows-real-github-ref-cas-2026-10-10.md",
    "docs/implementation/office-v2/phase2/p0-real-etcd-expiry-github-epoch-cutover-2026-10-10.json",
    "docs/implementation/office-v2/phase2/p0-real-etcd-expiry-github-epoch-cutover-2026-10-10.md",
    "packages/vfharness/devtools/creative-craft/creative-craft-registry.json",
    "packages/vfharness/devtools/creative-tools/AffinitySafeAdapter.py",
    "packages/vfharness/devtools/creative-tools/Start-VelvetResolveHost.ps1",
    "packages/vfharness/devtools/creative-tools/fusion-mcp-bridge.json",
    "packages/vfharness/devtools/creative-tools/update-sentinel/dcc-adobe-update-sentinel.json",
    "packages/vfharness/devtools/dcc-adobe-runtime-persistence/Start-VelvetMayaHeadless.ps1",
    "packages/vfharness/devtools/dcc-adobe-runtime-persistence/dcc-desktop-hosts.json",
    "packages/vfharness/devtools/dcc-mcp-illustrator-0.3.1-adobepy-0.9.0-bootstrap.py",
    "packages/vfharness/state/memory-rationalization-phase7-2026-09-27.json",
    "packages/vfigos/failover/failover_watch.py",
    "packages/vfigos/failover/grok_instagram_failover.py",
    "scripts/check-crewai-reviewed-runner.py",
    "scripts/check-windows-path-contract.py",
    "scripts/generate-stage8c-windows-host-binding.py",
    "scripts/validate_ai3d_phase7_reverse_engineering.py",
    "scripts/vf_office_v2_604_authenticated_artifact_client_lab.py",
    "scripts/vf_office_v2_604_authenticated_artifact_receiver_lab.py",
    "scripts/vf_office_v2_604_authenticated_receiver_receipt_gate.py",
    "scripts/vf_office_v2_604_dagu_cleanup_gate.py",
    "scripts/vf_office_v2_604_epoch_cutover_receipt_gate.py",
    "scripts/vf_office_v2_604_epoch_mtls_fixture_lab.py",
    "scripts/vf_office_v2_604_epoch_native_git_sink_lab.py",
    "scripts/vf_office_v2_604_etcd_pending_intent_native_localgit_lab.py",
    "scripts/vf_office_v2_604_etcd_provider_pilot.py",
    "scripts/vf_office_v2_604_etcd_receipt_gate.py",
    "scripts/vf_office_v2_604_mac_fixture_mtls_lab.py",
    "scripts/vf_office_v2_604_mac_origin_native_git_cas_receipt_gate.py",
    "scripts/vf_office_v2_604_sameuid_sink_key_bypass_lab.py",
    "scripts/vf_office_v2_604_windows_native_git_cas_sink_lab.py",
    "scripts/vf_office_v2_node_manifest.py",
    "scripts/vf_office_v2_p0_fenced_effect_consumer_lab.py",
    "scripts/vf_office_v2_p0_ollama_runner_resource_lab.py",
})


def fail(message: str) -> None:
    raise SystemExit(f"FAIL {message}")


def kinds(text: str) -> set[str]:
    found: set[str] = set()
    if LAN.search(text):
        found.add("lan")
    if HOME.search(text):
        found.add("home")
    return found


def selftest() -> None:
    private_lan = "192" + ".168.9.9"
    doc_lan = "192" + ".0.2.10"
    win_home = "C:" + "\\Users\\" + "Chris\\Desktop"
    fwd_home = "C:" + "/Users/" + "Chris/Desktop"
    posix_home = "/Users/" + "Chris/Velvet"
    lower_home = "/users/" + "chris/Velvet"
    if kinds(private_lan) != {"lan"}:
        fail("selftest missed a private LAN address")
    if kinds(doc_lan):
        fail("selftest flagged the documentation address")
    for sample in (win_home, fwd_home, posix_home, lower_home):
        if kinds(sample) != {"home"}:
            fail("selftest missed a home prefix")
    if kinds("%USERPROFILE%\\Desktop") or kinds("$HOME/Velvet"):
        fail("selftest flagged a placeholder home")
    if "192" + ".168." in Path(__file__).read_text(encoding="utf-8"):
        fail("this sensor must not embed a private LAN literal")


def tracked_text() -> list[tuple[str, str]]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail("git ls-files failed")
    rows: list[tuple[str, str]] = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8")
        path = ROOT / rel
        if not path.is_file():
            continue
        blob = path.read_bytes()
        if b"\0" in blob:
            continue
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            continue
        rows.append((rel, text))
    return rows


def main() -> int:
    selftest()
    seen: set[str] = set()
    problems: list[str] = []
    for rel, text in tracked_text():
        found = kinds(text)
        if rel in ALLOWLIST:
            seen.add(rel)
            if not found:
                problems.append(f"{rel}: allowlist entry no longer matches")
            continue
        if found:
            problems.append(f"{rel}: {'+'.join(sorted(found))}")
    missing = sorted(ALLOWLIST - seen)
    for rel in missing:
        problems.append(f"{rel}: allowlist entry is not a tracked text file")
    if problems:
        print("FAIL public-path-redaction")
        for row in problems:
            print(row)
        return 1
    print(
        "OK public-path-redaction "
        f"allowlist={len(ALLOWLIST)} tracked_text={len(tracked_text())}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
