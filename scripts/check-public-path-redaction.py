#!/usr/bin/env python3
"""Refuse a new private LAN address or Chris home path in tracked files.

Historical receipts whose bytes are hash-pinned, live host launchers, and the
Windows path-contract needle stay on the allowlist. A tracked file outside
that list fails when it contains an RFC1918 address or a Chris home prefix.
An allowlist entry that no longer matches fails too, so the list cannot rot.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAN = re.compile(
    r"(?<![\d.])(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
    r"|192\.168\.\d{1,3}\.\d{1,3})(?!\d)"
)
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


# Historic vendor training samples/negative test inputs contain synthetic
# private IP literals. Unlike the legacy file-wide allowlist, ANY edit to a
# fixture requires an explicit digest review before it is permitted again.
STATIC_PRIVATE_FIXTURE_SHA256 = {
    ".cursor/rules/infrastructure-maintainer.mdc": "a3d9468a8c380ddaa6338ebc1019a199478bf713f660d7f5e9cb3cf7620ba183",
    ".cursor/rules/network-engineer.mdc": "16d324a8e3f066fe5822337335040b86f2d967cc8b8e7bb845da1f90fc5bbec5",
    ".cursor/rules/penetration-tester.mdc": "c4e27bb32b0e7429729e06eb813ba8318cd9a6daecdf55834d0cc125656041f4",
    "scripts/check-crewai-e5-network.py": "db25ff691e16bbb44955e3ce51e0c3c80460e88fcef11e5815e9686dc9df326a",
    "scripts/office_v2_crewai/inputs/adversarial.json": "ddd444af9f7dbaede5f2ba98f36cb39de5f847094d5b06cebab8d45e04b70497",
}


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
    for sample in (
        "10" + ".22.33.44",
        "172" + ".16.5.4",
        "172" + ".31.255.255",
    ):
        if kinds(sample) != {"lan"}:
            fail("selftest missed an RFC1918 range")
    if kinds("172" + ".32.5.4"):
        fail("selftest flagged a public 172 address")
    latin_payload = ("Caf" + chr(233) + " host 10" + ".22.33.44").encode("latin-1")
    if kinds(decode_tracked_bytes(latin_payload) or "") != {"lan"}:
        fail("selftest skipped a non-UTF-8 private address")
    utf16_payload = ("host " + win_home).encode("utf-16")
    if kinds(decode_tracked_bytes(utf16_payload) or "") != {"home"}:
        fail("selftest skipped a UTF-16 tracked text payload")
    from sensor_selector import load_json, select_for_paths
    policy = ROOT / "packages" / "velvetos" / "policy"
    selected = select_for_paths(
        ["docs/implementation/office-v2/phase2/dagu-two-host-lab-2026-10-08.json"],
        load_json(policy / "sensor-registry.json"),
        load_json(policy / "sensor-selection.json"),
    )
    if "check-public-path-redaction" not in selected["selected_sensor_ids"]:
        fail("redaction sensor was not selected for PR-time doc-only changes")
    for sample in (win_home, fwd_home, posix_home, lower_home):
        if kinds(sample) != {"home"}:
            fail("selftest missed a home prefix")
    if kinds("%USERPROFILE%\\Desktop") or kinds("$HOME/Velvet"):
        fail("selftest flagged a placeholder home")
    if "192" + ".168." in Path(__file__).read_text(encoding="utf-8"):
        fail("this sensor must not embed a private LAN literal")


def decode_tracked_bytes(blob: bytes) -> str | None:
    # Windows PowerShell text can be UTF-16, including literal NUL bytes.
    if blob.startswith((bytes([255, 254]), bytes([254, 255]))):
        return blob.decode("utf-16", errors="replace")
    if bytes([0]) in blob:
        return None  # genuine binary payload, not a tracked text candidate
    return blob.decode("utf-8", errors="replace")


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
        text = decode_tracked_bytes(blob)
        if text is None:
            continue
        rows.append((rel, text))
    return rows


def main() -> int:
    selftest()
    seen: set[str] = set()
    seen_fixtures: set[str] = set()
    problems: list[str] = []
    for rel, text in tracked_text():
        found = kinds(text)
        if rel in STATIC_PRIVATE_FIXTURE_SHA256:
            seen_fixtures.add(rel)
            actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            if actual != STATIC_PRIVATE_FIXTURE_SHA256[rel]:
                problems.append(f"{rel}: pinned synthetic fixture changed")
            if not found:
                problems.append(f"{rel}: fixture private-range example missing")
            continue
        if rel in ALLOWLIST:
            seen.add(rel)
            if not found:
                problems.append(f"{rel}: allowlist entry no longer matches")
            continue
        if found:
            problems.append(f"{rel}: {'+'.join(sorted(found))}")
    missing_fixtures = sorted(set(STATIC_PRIVATE_FIXTURE_SHA256) - seen_fixtures)
    for rel in missing_fixtures:
        problems.append(f"{rel}: pinned fixture is not tracked text")
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
        f"allowlist={len(ALLOWLIST)} fixtures={len(STATIC_PRIVATE_FIXTURE_SHA256)} "
        f"tracked_text={len(tracked_text())}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
