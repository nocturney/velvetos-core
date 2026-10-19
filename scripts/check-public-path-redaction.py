#!/usr/bin/env python3
"""Refuse a new private LAN address, Chris home path, or redacted machine id.

Historical receipts whose bytes are hash-pinned, live host launchers, and the
Windows path-contract needle stay on the allowlist. Each allowlisted file
exempts only the sha256 of the sensitive lines already in it. A new sensitive
line, a repeated exempt line, or a missing exempt line fails. A tracked file
outside that list fails when it contains a private LAN address, a Chris home
prefix in any case, or the redacted Desktop Commander id prefix.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAN = re.compile(r"192\.168\.\d{1,3}\.\d{1,3}")
# Drive letter plus the Chris profile folder, either slash, any case, plus the
# POSIX form. The pattern is split so this file does not contain the path.
_HOME_BODY = (
    "[a-z]:[/\\\\]+"
    + "users[/\\\\]+"
    + "chris|"
    + "/users/"
    + "chris"
)
HOME = re.compile("(?:%s)\\b" % _HOME_BODY, re.IGNORECASE)
# Device ids removed from the public tree. This is not a general UUID match.
# 516b9b39 is the Desktop Commander id replaced with <chris-machine-id>.
REDACTED_MACHINE_PREFIXES = (
    "516b9b39",
)
MACHINE = re.compile(
    r"\b(?:%s)-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
    % "|".join(REDACTED_MACHINE_PREFIXES),
    re.IGNORECASE,
)

# sha256 of each existing sensitive line. Sorted, with duplicates preserved.
# Do not add a hash to hide a new line. Remove a row when its pin is gone.
EXEMPT: dict[str, tuple[str, ...]] = {
    ".cursor/rules/threat-intelligence-analyst.mdc": (
        "9176ca2cd32da2fa363022485a55db6a08198179bcd352d47f9e2441ef8098fe",
    ),
    "docs/implementation/office-v2/phase2/p0-authenticated-two-host-external-fs-receiver-lab-2026-10-10.json": (
        "207b62fa9dac66fc67df6e96f156e41cf86db5f7e5080233eb72b2db3df0f025",
        "982ba8f50fc7a307ae5a6b3b5dfcaa6849d6770457635685e21718f7acfe7f38",
    ),
    "docs/implementation/office-v2/phase2/p0-authenticated-two-host-external-fs-receiver-lab-2026-10-10.md": (
        "0bb1d29756ee1d6b312ff4ba4046ff63cee9f56f03500ffcdd770b5a8e45f8a0",
    ),
    "docs/implementation/office-v2/phase2/p0-dagu-fleet-idle-cleanup-2026-10-10.json": (
        "559eda21be2ff0d4131c803e4037193088871d403afc40b1ff6b05a56a181662",
    ),
    "docs/implementation/office-v2/phase2/p0-etcd-two-host-real-provider-atomic-kv-2026-10-10.json": (
        "dd4f0f889690bf264a5fe41bccbcb279fd6f43d101998507e7cb023fd31c3913",
    ),
    "docs/implementation/office-v2/phase2/p0-local-agent-envelope-lab-2026-10-08.json": (
        "06034287f8fc1162e30e54fce1732e76a3d985f340ed9977604ddd2961e54a34",
        "19e8db5252c2401b8182cf4df4a7b3f10e7140ccfdbe6cdc4795bb96cee605b9",
        "899bb6353a189f07a7d3f346c03d4c46cd39ce726069ea735795fdf8cad5bdec",
        "c80627c71e86bef61e8d8f1479060343319d2ad8183453bf477324d61581e0db",
        "dd9f48aa08edbfbbc6cbfde235c8ac9b39179b0d765e0d2f49ee71e067d49e67",
        "e4cd6dcaace50a6e11e6761feba17e05b7fdba3c0122a7f6381a29c080759e0c",
    ),
    "docs/implementation/office-v2/phase2/p0-mac-origin-windows-real-github-ref-cas-2026-10-10.json": (
        "473d0a5e5b1305c4609546af3d595f9e3d409514ad0d86e9e4f7c32cf52033a8",
    ),
    "docs/implementation/office-v2/phase2/p0-mac-origin-windows-real-github-ref-cas-2026-10-10.md": (
        "4f27150880dd5ed1280938db481b587b2a82cd1ef8b1faac8cea0c3f04063af2",
        "b9cba4e778431e38886e8ff1e37ef0292eed4a3af3230d50390e4d26060d3ad9",
    ),
    "docs/implementation/office-v2/phase2/p0-real-etcd-expiry-github-epoch-cutover-2026-10-10.json": (
        "256bcebf0bf560681b6559f31e2754f5639b3ed7f0b82a6167d4700546ce6e57",
    ),
    "docs/implementation/office-v2/phase2/p0-real-etcd-expiry-github-epoch-cutover-2026-10-10.md": (
        "21afdc069819353dc692d4b88c5d4ff69938e13882ae7adfb1e07c7bb4e8bcca",
    ),
    "packages/vfharness/devtools/creative-craft/creative-craft-registry.json": (
        "dee0ed2e5513c0630a15c96b18a2f7983f34912ec9c2267a273cf7d6b75b97c6",
    ),
    "packages/vfharness/devtools/creative-tools/AffinitySafeAdapter.py": (
        "d7c9e1fd46236ef2df665778e43df71e7433b8286cb67b53f5ed82656481dabd",
    ),
    "packages/vfharness/devtools/creative-tools/Start-VelvetResolveHost.ps1": (
        "8c27ab781a593aa4f5ae301370a612b4884e1b002fea1106a31e464f1a89b421",
    ),
    "packages/vfharness/devtools/creative-tools/fusion-mcp-bridge.json": (
        "40e5dd014af985c54625c16958869c596b1b0860aaf92e94a2d0966475a45d7e",
        "8075dd5b79b5c9e41625e1ff76c6bbdb6a821ede3ff3651f9af2e29149656fe3",
    ),
    "packages/vfharness/devtools/creative-tools/update-sentinel/dcc-adobe-update-sentinel.json": (
        "2bc006ed00fa6836d3f4efef1eb2c1c29229eef5cc662e9a5adb158a1fff43d9",
        "9b69a649bdbe0f03ed16968e94c55cf73e36d81d162dba4fa2e704809b7d2e3e",
        "ae713c3b37f44d137cce9b6ce767fb47c2ec549b3d3a5a0890f7fb61c6e136a1",
    ),
    "packages/vfharness/devtools/dcc-adobe-runtime-persistence/Start-VelvetMayaHeadless.ps1": (
        "ad43e6aec652bd19d6394d628f0db6fd543b3fbd443a1518934e812ea582ea84",
    ),
    "packages/vfharness/devtools/dcc-adobe-runtime-persistence/dcc-desktop-hosts.json": (
        "cdc8b6abf165735707eefdfa80a3aff5a1ab6d7daded0c2ebf4b55a4a26f9c6e",
    ),
    "packages/vfharness/devtools/dcc-mcp-illustrator-0.3.1-adobepy-0.9.0-bootstrap.py": (
        "2921ce74fce8891dfafbd49bf6141c8915d00190242916d7a54ad6c482d4b265",
    ),
    "packages/vfharness/state/memory-rationalization-phase7-2026-09-27.json": (
        "81504dd006d0d174a7d82f1aa4b37b02cf35faf7959f432f5443f73b6f917ff0",
    ),
    "packages/vfigos/failover/failover_watch.py": (
        "38d620d442ac9e3e06c27a031e097f825587212f36dcd7dc34a31ef19bf8dcda",
        "e344c8a73dfa01a7325409841d476b82c9767b18b1858f62751b272da652495b",
        "ec96843b66961c591dc8d439521bef950f415b69c5743837f1855f0b3c085115",
        "f886cadf4ff476d9c943edc56b963e434eae028856dbf9ca7f81caaeb3d776b9",
    ),
    "packages/vfigos/failover/grok_instagram_failover.py": (
        "485def74a5a33a3feb9be1381319ea712c467cf215563ed424288c65e7089f89",
        "c470194d8374e0863c27e3126f1cea0bc16481f9fa2716b6640cd2a7cc910e7e",
        "d7c1e0b1cb4451e0c17d0c643f8b30207aef9588e37036a75ccd41d94db8cfcf",
        "da5c8872bc9167f90cf7ae49971d299ef665d82b81d91fb001dd2f17217f6ae6",
        "fd22446883972c57681e0897e10814736ac4876811dfc4ccfab17408d885a55a",
    ),
    "scripts/check-crewai-reviewed-runner.py": (
        "77589cb800f5e932149ebcac23cd77b9b0ca380adaa86b77c61b9118fb6f4f6a",
    ),
    "scripts/check-windows-path-contract.py": (
        "23c49514ec8ba0a9344ca52e9d5dabceee97254dad02bd471fc4606ec626203b",
        "23dd9ca1be48ea9dbe48759cab5d8daed64c9537f03b4178ead69ee59a4aad3d",
        "62beb4a31bcde98545825286b31bedacd5619049c6a72d3db005da4f91fccdb2",
    ),
    "scripts/generate-stage8c-windows-host-binding.py": (
        "8aaf9a6572869629c30879a7d284d0c26b53dd95de619cfa4ec08e28df26c369",
    ),
    "scripts/validate_ai3d_phase7_reverse_engineering.py": (
        "10a895a8852420e469ffcd0c3a0fb49e192b05c6d8d9f56903bd33017396b16b",
    ),
    "scripts/vf_office_v2_604_authenticated_artifact_client_lab.py": (
        "b8f60e1a2cc37b920ac1fac9f0cf918e55eb56b513a396a2363376a0bf7f39ab",
    ),
    "scripts/vf_office_v2_604_authenticated_artifact_receiver_lab.py": (
        "e70ec7ec81587836bd1f138c3ee9dfb4d0f4cb802ef781bc89ee182b314fb5df",
    ),
    "scripts/vf_office_v2_604_authenticated_receiver_receipt_gate.py": (
        "744eddd9f284160616cb3a8e4ed9889f347535daeb6f254aedab85e5227ab184",
        "c1b63432d00bf872979c6da7616e4ff8aa13713c667638175edc34259ba24aee",
    ),
    "scripts/vf_office_v2_604_dagu_cleanup_gate.py": (
        "335df705394950d414d7da2b2828296b8497f9522e5171a334e3cee9b8d7fe79",
    ),
    "scripts/vf_office_v2_604_epoch_cutover_receipt_gate.py": (
        "85e422a37d8d32f6ea7950f88f0f94df8be13352fbb609100fb2723b6405df27",
    ),
    "scripts/vf_office_v2_604_epoch_mtls_fixture_lab.py": (
        "b2da7f5794780c2dc2a8114e84f8cd68924d5eddf176abe1bde71035bee979ab",
    ),
    "scripts/vf_office_v2_604_epoch_native_git_sink_lab.py": (
        "786fcae7feb37622ebf0961915bc8cf2972ab3ff19734630790f1ba8f10ca398",
    ),
    "scripts/vf_office_v2_604_etcd_pending_intent_native_localgit_lab.py": (
        "88029211fd8127bf37afc54595ba2e486e064004106edca6c9154db1409ea1ec",
    ),
    "scripts/vf_office_v2_604_etcd_provider_pilot.py": (
        "49137cf537adeec63d69b24a2aa246c4c080218de94dd484834a9809d375fa00",
        "62e1d447d720a727c9eb3c2ea7f41a5c2a4238048420e92d5bf008253645810e",
    ),
    "scripts/vf_office_v2_604_etcd_receipt_gate.py": (
        "ebe30b369a452c59f73fe35ef5bd84750b34db3cbdf20e2336ff41ae7e6f7f2e",
    ),
    "scripts/vf_office_v2_604_mac_fixture_mtls_lab.py": (
        "0ef4ddb5d84671cadc9260b03412962f96f06f2cb629250e6140de1723f0aa8d",
    ),
    "scripts/vf_office_v2_604_mac_origin_native_git_cas_receipt_gate.py": (
        "20058603769fc364835b9f726700f4b7b42f2598b13628b7a6e7eedd189a873c",
    ),
    "scripts/vf_office_v2_604_sameuid_sink_key_bypass_lab.py": (
        "873cf13d7b87bbd0b1fd0bc7568a8c98db9f3528c4228dbed505d1e8be7fddb6",
    ),
    "scripts/vf_office_v2_604_windows_native_git_cas_sink_lab.py": (
        "9fcd405eba19d8ac363922242d28e7e302d1abb8ae9c6e4ddea59fcebf7a69f4",
    ),
    "scripts/vf_office_v2_node_manifest.py": (
        "cf6de580cd6a979082e92ac0612c0d71fbf5788a9bd8252f1ac06b90aeb93d5b",
    ),
    "scripts/vf_office_v2_p0_fenced_effect_consumer_lab.py": (
        "50262acd4c3ace31b188786637d2e97dc9217c7104d02b6a6442c4e38e0f602f",
        "f559df519f0e8667e07bd2cb6419ec2d7a4c80828d83c8c413707688deff3a3d",
    ),
    "scripts/vf_office_v2_p0_ollama_runner_resource_lab.py": (
        "7693d2d8a8781b95d672433d71405b20f9c886d9dfa78b2903e29c68a1dee79a",
    ),
}
ALLOWLIST = frozenset(EXEMPT)


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


def line_digest(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def problems_for(
    rel: str,
    text: str,
    exempt: tuple[str, ...] | None = None,
) -> list[str]:
    if exempt is None and rel in EXEMPT:
        exempt = EXEMPT[rel]
    found = kinds(text)
    line_kinds: set[str] = set()
    digests: list[str] = []
    for line in text.splitlines():
        hit = kinds(line)
        if not hit:
            continue
        line_kinds |= hit
        digests.append(line_digest(line))
    if found - line_kinds:
        return [f"{rel}: sensitive match spans lines"]
    if exempt is not None:
        if not exempt and not digests:
            return [f"{rel}: allowlist entry no longer matches"]
        expected = Counter(exempt)
        actual = Counter(digests)
        problems: list[str] = []
        if actual - expected:
            problems.append(f"{rel}: new sensitive line")
        if expected - actual:
            problems.append(f"{rel}: exempt line missing")
        return problems
    if found:
        return [f"{rel}: {'+'.join(sorted(found))}"]
    return []


def selftest() -> None:
    if set(EXEMPT) != ALLOWLIST:
        fail("selftest exempt map does not match the allowlist")
    if any(not row for row in EXEMPT.values()):
        fail("selftest empty exempt row")
    private_lan = "192" + ".168.9.9"
    doc_lan = "192" + ".0.2.10"
    win_home = "C:" + "\\Users\\" + "Chris\\Desktop"
    fwd_home = "C:" + "/Users/" + "Chris/Desktop"
    posix_home = "/Users/" + "Chris/Velvet"
    lower_home = "/users/" + "chris/Velvet"
    lower_win = "c:" + "\\users\\" + "chris\\Desktop"
    fwd_lower = "c:" + "/users/" + "chris/Desktop"
    upper_win = "C:" + "\\USERS\\" + "CHRIS\\Desktop"
    if kinds(private_lan) != {"lan"}:
        fail("selftest missed a private LAN address")
    if kinds(doc_lan):
        fail("selftest flagged the documentation address")
    for sample in (
        win_home, fwd_home, posix_home, lower_home, lower_win, fwd_lower, upper_win,
    ):
        if kinds(sample) != {"home"}:
            fail("selftest missed a home prefix")
    prefix = REDACTED_MACHINE_PREFIXES[0]
    redacted = prefix + "-92b7-4a73-8d4b-901cc1a70a98"
    other_tail = prefix + "-aaaa-bbbb-cccc-ddddeeeeffff"
    if kinds(redacted) != {"machine"} or kinds(other_tail) != {"machine"}:
        fail("selftest missed a redacted machine id")
    if kinds(prefix) or kinds(prefix.upper()):
        fail("selftest flagged a bare machine prefix")
    worker = "4a3ca6d2" + "-f2c3-4cba-8c96-8bb63d6160b2"
    live_pin_id = "db0e4d78" + "-3b27-46d9-8c2b-453049eb3933"
    if kinds(worker) or kinds(live_pin_id):
        fail("selftest flagged a machine id that was not redacted")
    source = Path(__file__).read_text(encoding="utf-8")
    if "192" + ".168." in source:
        fail("this sensor must not embed a private LAN literal")
    if MACHINE.search(source):
        fail("this sensor must not embed a redacted machine id")
    if HOME.search(source) or LAN.search(source):
        fail("this sensor must not embed a home path or LAN address")
    sample_line = "192" + ".168.1.2"
    digest = line_digest(sample_line)
    base = "note\n" + sample_line + "\n"
    if problems_for("synthetic.txt", base, exempt=(digest,)):
        fail("selftest rejected an exact exempt line")
    added = base + ("192" + ".168.9.9") + "\n"
    if problems_for("synthetic.txt", added, exempt=(digest,)) != [
        "synthetic.txt: new sensitive line"
    ]:
        fail("selftest missed a new sensitive line")
    repeated = base + sample_line + "\n"
    if problems_for("synthetic.txt", repeated, exempt=(digest,)) != [
        "synthetic.txt: new sensitive line"
    ]:
        fail("selftest missed a repeated exempt line")
    if problems_for("synthetic.txt", "note\n", exempt=(digest,)) != [
        "synthetic.txt: exempt line missing"
    ]:
        fail("selftest missed a dropped exempt line")
    replaced = "note\n" + ("192" + ".168.8.8") + "\n"
    if problems_for("synthetic.txt", replaced, exempt=(digest,)) != [
        "synthetic.txt: new sensitive line",
        "synthetic.txt: exempt line missing",
    ]:
        fail("selftest missed a replaced exempt line")
    if problems_for("synthetic.txt", base + "plain\n", exempt=(digest,)):
        fail("selftest flagged an unrelated line")
    if problems_for("synthetic.txt", "plain\n", exempt=()) != [
        "synthetic.txt: allowlist entry no longer matches"
    ]:
        fail("selftest let an empty allowlist row rot")
    rel = "scripts/vf_office_v2_node_manifest.py"
    current = (ROOT / rel).read_text(encoding="utf-8")
    if problems_for(rel, current):
        fail("selftest rejected the current node manifest")
    mutants = (
        ("192" + ".168.9.9", "lan"),
        ("c:" + "\\users\\" + "chris\\x", "home"),
        (prefix + "-92b7-4a73-8d4b-901cc1a70a98", "machine"),
    )
    for extra, label in mutants:
        got = problems_for(rel, current + "\n" + extra + "\n")
        if got != [f"{rel}: new sensitive line"]:
            fail(f"selftest missed a {label} addition on an allowlisted file")
        if extra in got[0] or prefix in got[0]:
            fail("selftest leaked a sensitive line in the failure")
    if problems_for(rel, current + "\n# unrelated\n"):
        fail("selftest flagged an unrelated edit of an allowlisted file")
    pin_rel = "packages/vfharness/state/runtime/sderot-windows.json"
    pin = (ROOT / pin_rel).read_text(encoding="utf-8")
    if pin_rel in EXEMPT or kinds(pin) or problems_for(pin_rel, pin):
        fail("selftest flagged the live windows pin")
    memory_rel = "packages/vfops/data/owner-memory.md"
    memory = (ROOT / memory_rel).read_text(encoding="utf-8")
    if problems_for(memory_rel, memory):
        fail("selftest flagged a machine id that stayed in owner memory")
    fresh_home = problems_for("fresh.txt", "c:" + "\\users\\" + "chris")
    if fresh_home != ["fresh.txt: home"]:
        fail("selftest missed a home path outside the allowlist")
    fresh_id = problems_for(
        "fresh.txt", prefix + "-1111-2222-3333-444455556666"
    )
    if fresh_id != ["fresh.txt: machine"]:
        fail("selftest missed a machine id outside the allowlist")


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
    rows = tracked_text()
    seen = {rel for rel, _text in rows if rel in EXEMPT}
    problems: list[str] = []
    for rel, text in rows:
        problems.extend(problems_for(rel, text))
    for rel in sorted(set(EXEMPT) - seen):
        problems.append(f"{rel}: allowlist entry is not a tracked text file")
    if problems:
        print("FAIL public-path-redaction")
        for row in problems:
            print(row)
        return 1
    line_count = sum(len(row) for row in EXEMPT.values())
    print(
        "OK public-path-redaction "
        f"allowlist={len(EXEMPT)} lines={line_count} tracked_text={len(rows)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
