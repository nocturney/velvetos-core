#!/usr/bin/env python3
"""Refuse a new private LAN address, Chris home path, or redacted machine id.

Historical receipts whose bytes are hash-pinned, live host launchers, and the
Windows path-contract needle stay on the allowlist. A tracked file outside
that list fails when it contains an RFC1918 address, a Chris home prefix in
any letter case, or the redacted Desktop Commander id prefix.
An allowlist entry that no longer matches fails too, so the list cannot rot.
Unreadable tracked content fails closed; it is never skipped.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAN = re.compile(
    r"(?<!\d)(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
    r"|192\.168\.\d{1,3}\.\d{1,3})(?!\d)"
)
HOME = re.compile(
    r"(?:[A-Za-z]:[/\\]+Users[/\\]+Chris|/[Uu]sers/[Cc]hris)\b",
    re.IGNORECASE,
)
# Redacted Desktop Commander device id. The public tree keeps only this prefix,
# replaced with <chris-machine-id>. This is not a general UUID match.
REDACTED_MACHINE_PREFIXES = ("516b9b39",)
MACHINE = re.compile(
    r"\b(?:%s)-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
    % "|".join(REDACTED_MACHINE_PREFIXES),
    re.IGNORECASE,
)

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
# The precise sensitive occurrences in each historical exception are hash
# locked. Ordinary changes elsewhere in those files do not invalidate this
# contract, but new private host literals do.
ALLOWLIST_MATCH_SHA256 = {
    '.cursor/rules/threat-intelligence-analyst.mdc': '43853de210171dfb650a348a3175fc893fb0fbb94844505b6307dc3caf080ae5',
    'docs/implementation/office-v2/phase2/p0-authenticated-two-host-external-fs-receiver-lab-2026-10-10.json': '5026cd36f0ecdb83506880219b70c7ad7df8453e6e5c4394253c8e35dc07c0c6',
    'docs/implementation/office-v2/phase2/p0-authenticated-two-host-external-fs-receiver-lab-2026-10-10.md': 'a41f4f6d73d3d2a53d0b981ed9796a63d2c521ae100eadef8056a9e4ce4bc480',
    'docs/implementation/office-v2/phase2/p0-dagu-fleet-idle-cleanup-2026-10-10.json': 'ed8f5bf930c8f0fd882d01ac7daecbf84158f7f487c803fe0691ec01b9da450b',
    'docs/implementation/office-v2/phase2/p0-etcd-two-host-real-provider-atomic-kv-2026-10-10.json': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'docs/implementation/office-v2/phase2/p0-local-agent-envelope-lab-2026-10-08.json': 'de692a032fb1802df9c3259747a1d9b558ec060f8c0a5a7f6d439a0267ccb991',
    'docs/implementation/office-v2/phase2/p0-mac-origin-windows-real-github-ref-cas-2026-10-10.json': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'docs/implementation/office-v2/phase2/p0-mac-origin-windows-real-github-ref-cas-2026-10-10.md': '5026cd36f0ecdb83506880219b70c7ad7df8453e6e5c4394253c8e35dc07c0c6',
    'docs/implementation/office-v2/phase2/p0-real-etcd-expiry-github-epoch-cutover-2026-10-10.json': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'docs/implementation/office-v2/phase2/p0-real-etcd-expiry-github-epoch-cutover-2026-10-10.md': '5026cd36f0ecdb83506880219b70c7ad7df8453e6e5c4394253c8e35dc07c0c6',
    'packages/vfharness/devtools/creative-craft/creative-craft-registry.json': 'ed8f5bf930c8f0fd882d01ac7daecbf84158f7f487c803fe0691ec01b9da450b',
    'packages/vfharness/devtools/creative-tools/AffinitySafeAdapter.py': '0e5970555d458c315619af4d29c54c41c0fbbc6bb89ecb570b59bd0689dc6ddf',
    'packages/vfharness/devtools/creative-tools/Start-VelvetResolveHost.ps1': '0e5970555d458c315619af4d29c54c41c0fbbc6bb89ecb570b59bd0689dc6ddf',
    'packages/vfharness/devtools/creative-tools/fusion-mcp-bridge.json': '7d17699f2f7d48f38037aee54de1df10eadfb0262942c6ff0d9821a0f151e50e',
    'packages/vfharness/devtools/creative-tools/update-sentinel/dcc-adobe-update-sentinel.json': '7f5ba47f3fcd52350fc0a3d0ed7095f059d8889666ffd3af1986859de7a99729',
    'packages/vfharness/devtools/dcc-adobe-runtime-persistence/Start-VelvetMayaHeadless.ps1': '0e5970555d458c315619af4d29c54c41c0fbbc6bb89ecb570b59bd0689dc6ddf',
    'packages/vfharness/devtools/dcc-adobe-runtime-persistence/dcc-desktop-hosts.json': 'ed8f5bf930c8f0fd882d01ac7daecbf84158f7f487c803fe0691ec01b9da450b',
    'packages/vfharness/devtools/dcc-mcp-illustrator-0.3.1-adobepy-0.9.0-bootstrap.py': '0e5970555d458c315619af4d29c54c41c0fbbc6bb89ecb570b59bd0689dc6ddf',
    'packages/vfharness/state/memory-rationalization-phase7-2026-09-27.json': 'ed8f5bf930c8f0fd882d01ac7daecbf84158f7f487c803fe0691ec01b9da450b',
    'packages/vfigos/failover/failover_watch.py': 'c23900b812abd65bb8e12ed325937d6b911561f7814509e8179bfc129d95ae2f',
    'packages/vfigos/failover/grok_instagram_failover.py': 'e2240790275ad6a94574e6758619032757bcddf058291fd960203ab391bc577b',
    'scripts/check-crewai-reviewed-runner.py': '801b3500f91ca12aa548f0dbf104c9202eff2079eadb1e86b15612b7542b4dd8',
    'scripts/check-windows-path-contract.py': 'b081e8283c55696f9e7b13fc3cecea3135186bde28e275ff6b9e19f66cced18d',
    'scripts/generate-stage8c-windows-host-binding.py': '0e5970555d458c315619af4d29c54c41c0fbbc6bb89ecb570b59bd0689dc6ddf',
    'scripts/validate_ai3d_phase7_reverse_engineering.py': '0e5970555d458c315619af4d29c54c41c0fbbc6bb89ecb570b59bd0689dc6ddf',
    'scripts/vf_office_v2_604_authenticated_artifact_client_lab.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_604_authenticated_artifact_receiver_lab.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_604_authenticated_receiver_receipt_gate.py': '5026cd36f0ecdb83506880219b70c7ad7df8453e6e5c4394253c8e35dc07c0c6',
    'scripts/vf_office_v2_604_dagu_cleanup_gate.py': '0e5970555d458c315619af4d29c54c41c0fbbc6bb89ecb570b59bd0689dc6ddf',
    'scripts/vf_office_v2_604_epoch_cutover_receipt_gate.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_604_epoch_mtls_fixture_lab.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_604_epoch_native_git_sink_lab.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_604_etcd_pending_intent_native_localgit_lab.py': 'da2f221532619427b05999b678eeba1ee1d607e4b0db4cfa54c3ffc098d1880f',
    'scripts/vf_office_v2_604_etcd_provider_pilot.py': '5026cd36f0ecdb83506880219b70c7ad7df8453e6e5c4394253c8e35dc07c0c6',
    'scripts/vf_office_v2_604_etcd_receipt_gate.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_604_mac_fixture_mtls_lab.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_604_mac_origin_native_git_cas_receipt_gate.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_604_sameuid_sink_key_bypass_lab.py': 'da2f221532619427b05999b678eeba1ee1d607e4b0db4cfa54c3ffc098d1880f',
    'scripts/vf_office_v2_604_windows_native_git_cas_sink_lab.py': '8fc7a12d566653e9c56e33095a7af8504628a0cf2f7a3d53b14bd133108fad70',
    'scripts/vf_office_v2_node_manifest.py': '2d2fad6b5694a71d78d77cccf009a3a03fd162387f33f3cb9123e723658bc1bd',
    'scripts/vf_office_v2_p0_fenced_effect_consumer_lab.py': 'e8b20b9c84c4333c36abb5c9cdb8c419e3d71a148978224ef858664098bb5faf',
    'scripts/vf_office_v2_p0_ollama_runner_resource_lab.py': '2d2fad6b5694a71d78d77cccf009a3a03fd162387f33f3cb9123e723658bc1bd',
}

# Changing the exception or fixture count is a reviewed edit to this sensor.
EXPECTED_ALLOWLIST_SIZE = 42
EXPECTED_FIXTURE_COUNT = 5


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
    if MACHINE.search(text):
        found.add("machine")
    return found


UTF32_BOMS = (b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")
BOMLESS_WIDE_CODECS = ("utf-32-le", "utf-32-be", "utf-16-le", "utf-16-be")


def decode_tracked_bytes(blob: bytes) -> str:
    """Scan BOTH raw bytes and decoded text; refuse malformed BOM input.

    A BOM-less NUL-bearing blob is decoded leniently in every wide codec at
    every byte offset, so odd length or UTF-32 alignment cannot hide evidence.
    """
    raw = blob.decode("latin-1")
    decoded = [raw]
    if blob.startswith(UTF32_BOMS):
        try:
            decoded.append(blob.decode("utf-32"))
        except UnicodeDecodeError as exc:
            raise ValueError("malformed UTF-32 BOM payload") from exc
    elif blob.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            decoded.append(blob.decode("utf-16"))
        except UnicodeDecodeError as exc:
            raise ValueError("malformed UTF-16 BOM payload") from exc
    elif b"\x00" in blob:
        # Guessing one BOM-less byte order can miss evidence. Scan every view.
        for offset in range(4):
            for codec in BOMLESS_WIDE_CODECS:
                decoded.append(blob[offset:].decode(codec, errors="replace"))
    else:
        try:
            decoded.append(blob.decode("utf-8"))
        except UnicodeDecodeError:
            pass
    return "\n".join(decoded)


def sensitive_match_digest(text: str) -> str:
    """Pin sensitive occurrences, not whole-file bytes; other edits remain safe."""
    tokens = sorted(
        ["LAN:" + match.group(0).casefold() for match in LAN.finditer(text)]
        + ["HOME:" + match.group(0).casefold() for match in HOME.finditer(text)]
        + ["MACHINE:" + match.group(0).casefold() for match in MACHINE.finditer(text)]
    )
    return hashlib.sha256("\x00".join(tokens).encode("utf-8")).hexdigest()


def audit(
    rows: list[tuple[str, bytes]],
    allowlist: frozenset[str] = ALLOWLIST,
    pins: dict[str, str] = STATIC_PRIVATE_FIXTURE_SHA256,
    allowlist_digests: dict[str, str] | None = None,
) -> list[str]:
    """Return one problem row per violation for the given (path, bytes) rows."""
    problems: list[str] = []
    if allowlist_digests is None:
        allowlist_digests = ALLOWLIST_MATCH_SHA256
    seen: set[str] = set()
    seen_fixtures: set[str] = set()
    for rel, blob in rows:
        if rel in pins:
            seen_fixtures.add(rel)
            # Git on Windows may check out tracked text with CRLF when
            # core.autocrlf=true. Pin the canonical LF content, so these
            # same historical fixtures verify on macOS, Linux and Windows.
            if hashlib.sha256(blob.replace(b"\r\n", b"\n")).hexdigest() != pins[rel]:
                problems.append(f"{rel}: pinned synthetic fixture changed")
        try:
            found = kinds(decode_tracked_bytes(blob))
        except ValueError:
            problems.append(f"{rel}: unreadable tracked text")
            continue
        if rel in pins:
            if not found:
                problems.append(f"{rel}: fixture private-range example missing")
            continue
        if rel in allowlist:
            seen.add(rel)
            if not found:
                problems.append(f"{rel}: allowlist entry no longer matches")
            elif sensitive_match_digest(decode_tracked_bytes(blob)) != allowlist_digests.get(rel):
                problems.append(f"{rel}: allowlist sensitive matches changed")
            continue
        if found:
            problems.append(f"{rel}: {'+'.join(sorted(found))}")
    for rel in sorted(set(pins) - seen_fixtures):
        problems.append(f"{rel}: pinned fixture is not tracked text")
    for rel in sorted(allowlist - seen):
        problems.append(f"{rel}: allowlist entry is not a tracked text file")
    return problems


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
    if kinds("172" + ".32.5.4") or kinds("172" + ".15.5.4"):
        fail("selftest flagged a public 172 address")
    if kinds("110" + ".22.33.44"):
        fail("selftest flagged an RFC1918 literal embedded in a longer number")

    def scan(blob: bytes) -> list[str]:
        return audit([("docs/sample.md", blob)], allowlist=frozenset(), pins={})

    lan_row = ["docs/sample.md: lan"]
    home_row = ["docs/sample.md: home"]
    unreadable_row = ["docs/sample.md: unreadable tracked text"]
    for sample in ("10" + ".22.33.44", "172" + ".16.5.4", "172" + ".31.255.255", private_lan):
        if scan(sample.encode("ascii")) != lan_row:
            fail("selftest missed an RFC1918 range in UTF-8 text")
    if scan(doc_lan.encode("ascii")):
        fail("selftest flagged the documentation address in UTF-8 text")
    if scan(("host " + private_lan).encode("utf-16")) != lan_row:
        fail("selftest missed a private address in a UTF-16 BOM payload")
    if scan(("host " + private_lan).encode("utf-16-le")) != lan_row:
        fail("selftest missed a private address in BOM-less UTF-16LE text")
    if scan(("host " + private_lan).encode("utf-16-be")) != lan_row:
        fail("selftest missed a private address in BOM-less UTF-16BE text")
    if scan(b"\xff\xfe" + b"\x31") != unreadable_row:
        fail("selftest skipped a broken UTF-16 BOM payload instead of failing closed")
    host_text = "host " + private_lan
    wide_blobs = (
        host_text.encode("utf-16-le") + b"\x0a",
        host_text.encode("utf-16-be") + b"\x0a",
        host_text.encode("utf-32-le"),
        host_text.encode("utf-32-be"),
        host_text.encode("utf-32-le") + b"\x0a",
        host_text.encode("utf-32"),
        b"\x00\x00\xfe\xff" + host_text.encode("utf-32-be"),
    )
    for blob in wide_blobs:
        if scan(blob) != lan_row:
            fail("selftest missed a private address in odd-length or UTF-32 text")
    for blob in (b"\xff\xfe\x00\x00" + b"\x31", b"\x00\x00\xfe\xff" + b"\xff\xff\xff\xff"):
        if scan(blob) != unreadable_row:
            fail("selftest skipped a broken UTF-32 BOM payload instead of failing closed")
    benign_wide = (
        ("host " + doc_lan).encode("utf-32"),
        ("docs/readme 8.8.8.8").encode("utf-16-le") + b"\x0a",
        ("C:" + "\\Users\\alice\\Desktop").encode("utf-32-be"),
        ("C:" + "\\Users\\alice\\Desktop").encode("utf-16-le") + b"\x0a",
    )
    for blob in benign_wide:
        if scan(blob):
            fail("selftest flagged benign UTF-16 or UTF-32 text")
    for blob in (win_home.encode("utf-16-le") + b"\x0a", posix_home.encode("utf-32-be")):
        if scan(blob) != home_row:
            fail("selftest missed a home prefix in odd-length or UTF-32 text")
    if not scan(b"\xff\xfe\xfd note " + private_lan.encode("ascii")):
        fail("selftest skipped ASCII private text after a malformed BOM")
    if scan(b"note\x00 private " + private_lan.encode("ascii")) != lan_row:
        fail("selftest skipped private text after a NUL")
    if scan(("host." + private_lan).encode("ascii")) != lan_row:
        fail("selftest missed a private literal after hostname punctuation")
    if scan(("Caf" + chr(233) + " host " + "10" + ".22.33.44").encode("latin-1")) != lan_row:
        fail("selftest skipped a non-UTF-8 private address")
    if scan(bytes(range(256))):
        fail("selftest flagged a binary blob with no private literal")
    for sample in (win_home, fwd_home, posix_home, lower_home):
        if scan(sample.encode("ascii")) != home_row:
            fail("selftest missed a home prefix")
    if scan(("%USERPROFILE%\\Desktop $HOME/Velvet").encode("ascii")):
        fail("selftest flagged a placeholder home")
    lower_win_home = "c:" + "\\users\\" + "chris\\Desktop"
    upper_posix_home = "/USERS/" + "CHRIS/Velvet"
    machine_lower = REDACTED_MACHINE_PREFIXES[0] + "-1234-5678-9abc-def012345678"
    machine_upper = machine_lower.upper()
    for sample in (lower_win_home, upper_posix_home):
        if kinds(sample) != {"home"} or scan(sample.encode("ascii")) != home_row:
            fail("selftest missed a Chris home prefix in a non-canonical letter case")
    for sample in (machine_lower, machine_upper):
        if kinds(sample) != {"machine"} or scan(sample.encode("ascii")) != ["docs/sample.md: machine"]:
            fail("selftest missed the redacted machine id prefix")
    if kinds("3f2504e0-4f89-11d3-9a0c-0305e82c3301") or kinds("/Users/" + "alice/Projects/velvet"):
        fail("selftest flagged an unrelated GUID or user path")

    clean = b"no private address here"
    private = ("host " + private_lan).encode("ascii")
    pinned_match = {"docs/sample.md": sensitive_match_digest(decode_tracked_bytes(private))}
    if audit([("docs/sample.md", private)], allowlist=frozenset({"docs/sample.md"}), pins={}, allowlist_digests=pinned_match):
        fail("selftest flagged a pinned historical private address")
    if audit(
        [("docs/sample.md", private + b" and 10" + b".9.8.7")],
        allowlist=frozenset({"docs/sample.md"}), pins={}, allowlist_digests=pinned_match,
    ) != ["docs/sample.md: allowlist sensitive matches changed"]:
        fail("selftest allowed a NEW private literal in an exempt file")
    if audit([("docs/sample.md", clean)], allowlist=frozenset({"docs/sample.md"}), pins={}) != [
        "docs/sample.md: allowlist entry no longer matches"
    ]:
        fail("selftest accepted a stale allowlist entry")
    if audit([], allowlist=frozenset({"docs/missing.md"}), pins={}) != [
        "docs/missing.md: allowlist entry is not a tracked text file"
    ]:
        fail("selftest accepted an allowlist entry that is not tracked")
    if audit([("docs/sample.md", private)], allowlist=frozenset(), pins={"docs/sample.md": hashlib.sha256(private).hexdigest()}):
        fail("selftest rejected a correctly pinned fixture")
    if audit([("docs/sample.md", private)], allowlist=frozenset(), pins={"docs/sample.md": "0" * 64}) != [
        "docs/sample.md: pinned synthetic fixture changed"
    ]:
        fail("selftest accepted a changed pinned fixture")
    lf_fixture = b"header\n" + private + b"\n"
    lf_sha = hashlib.sha256(lf_fixture).hexdigest()
    crlf_fixture = lf_fixture.replace(b"\n", b"\r\n")
    hidden_wide = ("10" + ".9.8.7").encode("utf-32-le")
    if audit(
        [("docs/sample.md", lf_fixture + hidden_wide)],
        allowlist=frozenset(), pins={"docs/sample.md": lf_sha},
    ) != ["docs/sample.md: pinned synthetic fixture changed"]:
        fail("selftest let a UTF-32 literal ride on a pinned fixture")
    if audit(
        [("docs/sample.md", private + hidden_wide)],
        allowlist=frozenset({"docs/sample.md"}), pins={}, allowlist_digests=pinned_match,
    ) != ["docs/sample.md: allowlist sensitive matches changed"]:
        fail("selftest let a UTF-32 literal ride on a historical exception")
    if audit([("docs/sample.md", crlf_fixture)], allowlist=frozenset(), pins={"docs/sample.md": lf_sha}):
        fail("selftest refused a Windows CRLF checkout of the same pinned fixture")
    if audit(
        [("docs/sample.md", crlf_fixture + b"extra")],
        allowlist=frozenset(), pins={"docs/sample.md": lf_sha},
    ) != ["docs/sample.md: pinned synthetic fixture changed"]:
        fail("selftest accepted a tampered CRLF fixture")
    if audit([("docs/sample.md", clean)], allowlist=frozenset(), pins={"docs/sample.md": hashlib.sha256(clean).hexdigest()}) != [
        "docs/sample.md: fixture private-range example missing"
    ]:
        fail("selftest accepted a pinned fixture without its private example")
    if audit([], allowlist=frozenset(), pins={"docs/sample.md": "0" * 64}) != [
        "docs/sample.md: pinned fixture is not tracked text"
    ]:
        fail("selftest accepted a pinned fixture that is not tracked")
    if len(ALLOWLIST) != EXPECTED_ALLOWLIST_SIZE:
        fail(f"allowlist size drifted from {EXPECTED_ALLOWLIST_SIZE}")
    if set(ALLOWLIST_MATCH_SHA256) != set(ALLOWLIST):
        fail("historical private exception digest inventory drifted")
    if len(STATIC_PRIVATE_FIXTURE_SHA256) != EXPECTED_FIXTURE_COUNT:
        fail(f"pinned fixture count drifted from {EXPECTED_FIXTURE_COUNT}")

    from sensor_selector import load_json, select_for_paths
    policy = ROOT / "packages" / "velvetos" / "policy"
    registry = load_json(policy / "sensor-registry.json")
    registry_rows = registry["sensors"] if isinstance(registry, dict) else registry
    rows = [row for row in registry_rows if isinstance(row, dict) and row.get("id") == "check-public-path-redaction"]
    if len(rows) != 1 or (rows[0].get("fallback_scope"), rows[0].get("lifecycle"), rows[0].get("risk")) != ("ALWAYS_ON", "CORE", "critical"):
        fail("redaction sensor is not registered as CORE/critical ALWAYS_ON")
    selected = select_for_paths(
        ["docs/implementation/office-v2/phase2/dagu-two-host-lab-2026-10-08.json"],
        registry,
        load_json(policy / "sensor-selection.json"),
    )
    if "check-public-path-redaction" not in selected["selected_sensor_ids"]:
        fail("redaction sensor was not selected for PR-time doc-only changes")
    if "192" + ".168." in Path(__file__).read_text(encoding="utf-8"):
        fail("this sensor must not embed a private LAN literal")


def tracked_rows() -> tuple[list[tuple[str, bytes]], list[str]]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail("git ls-files failed")
    rows: list[tuple[str, bytes]] = []
    problems: list[str] = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8")
        path = ROOT / rel
        if path.is_dir():
            continue  # submodule gitlink, not file content
        try:
            rows.append((rel, path.read_bytes()))
        except OSError:
            problems.append(f"{rel}: unreadable tracked file")
    return rows, problems


def main() -> int:
    selftest()
    rows, problems = tracked_rows()
    problems += audit(rows)
    if problems:
        print("FAIL public-path-redaction")
        for row in problems:
            print(row)
        return 1
    print(
        "OK public-path-redaction "
        f"allowlist={len(ALLOWLIST)} fixtures={len(STATIC_PRIVATE_FIXTURE_SHA256)} "
        f"tracked_files={len(rows)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
