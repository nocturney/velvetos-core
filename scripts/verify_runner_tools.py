#!/usr/bin/env python3
"""Record versions of tools the runner image already installed.

git, GitHub CLI, curl, and Docker come with the image. A difference from
the last recorded version is a warning, and the job still passes. Downloads
this workflow fetches itself, such as the hashed ffmpeg archive and the
Node toolchain, stay hard pins in their own verifiers. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

# Last versions observed on the hosted images. Not a hard pin.
RECORDED = {
    "linux-git": "git version 2.55.0",
    "linux-gh": "gh version 2.102.0",
    "linux-curl": "8.5.0-2ubuntu10.15",
    "linux-docker-client": "28.0.4",
    "linux-docker-server": "28.0.4",
    "windows-git": "git version 2.56.0.windows.2",
    "windows-gh": "gh version 2.102.0",
    "windows-docker-client": "29.7.2",
    "windows-docker-server": "29.7.2",
}


def versions_match(observed: str, recorded: str) -> bool:
    return observed == recorded or observed.startswith(recorded + " ")


def drift_line(name: str, observed: str, recorded: str) -> tuple[str, bool]:
    """Return (report, hard_fail). Image version drift, including absence, only warns."""
    if observed and versions_match(observed, recorded):
        return f"runner tool name={name} observed={observed!r} recorded={recorded!r}", False
    shown = observed or "not observed"
    return (
        f"WARN runner tool drift name={name} observed={shown!r} recorded={recorded!r}",
        False,
    )


def finish(problems: list[str], notes: list[str]) -> int:
    for note in notes:
        print(note, file=sys.stderr)
    if problems:
        print("FAIL runner tools: " + "; ".join(problems), file=sys.stderr)
        return 1
    drift = sum(note.startswith("WARN runner tool drift") for note in notes)
    print(f"OK runner tools drift={drift}")
    return 0


def command_text(args: list[str]) -> str:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"not observed: {exc}"
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        return f"not observed: {detail}" if detail else "not observed"
    return (proc.stdout or "").strip()


def first_line(text: str) -> str:
    return text.splitlines()[0].strip() if text else ""


def docker_versions() -> tuple[str, str]:
    try:
        proc = subprocess.run(
            ["docker", "version", "--format", "{{json .}}"],
            text=True,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        detail = f"not observed: {exc}"
        return detail, detail
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        detail = f"not observed: {detail}" if detail else "not observed"
        return detail, detail
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return "not observed: docker version was not json", "not observed: docker version was not json"
    client = str((data.get("Client") or {}).get("Version") or "") or "not observed"
    server = str((data.get("Server") or {}).get("Version") or "") or "not observed"
    return client, server


def linux_observations() -> list[tuple[str, str]]:
    client, server = docker_versions()
    return [
        ("linux-git", first_line(command_text(["git", "--version"]))),
        ("linux-gh", first_line(command_text(["gh", "--version"]))),
        ("linux-curl", command_text(["dpkg-query", "-W", "-f", "${Version}", "curl"])),
        ("linux-docker-client", client),
        ("linux-docker-server", server),
    ]


def windows_observations() -> list[tuple[str, str]]:
    client, server = docker_versions()
    return [
        ("windows-git", first_line(command_text(["git", "--version"]))),
        ("windows-gh", first_line(command_text(["gh", "--version"]))),
        ("windows-docker-client", client),
        ("windows-docker-server", server),
    ]


def collect(observations: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    notes: list[str] = []
    for name, observed in observations:
        line, hard = drift_line(name, observed, RECORDED[name])
        if hard:
            problems.append(line)
        else:
            notes.append(line)
    return problems, notes


def self_test() -> int:
    recorded = RECORDED["windows-git"]
    drifted, hard = drift_line("windows-git", "git version 2.99.0.windows.1", recorded)
    if hard or not drifted.startswith("WARN runner tool drift") or "2.99.0.windows.1" not in drifted:
        print("FAIL runner tools: version drift was a hard failure", file=sys.stderr)
        return 1
    if finish([], [drifted]) != 0:
        print("FAIL runner tools: drift warning failed the job", file=sys.stderr)
        return 1
    same, same_hard = drift_line("windows-git", recorded, recorded)
    if same_hard or same.startswith("WARN "):
        print("FAIL runner tools: recorded version was a warning", file=sys.stderr)
        return 1
    prefixed, prefixed_hard = drift_line(
        "linux-gh", "gh version 2.102.0 (2026-01-01)", RECORDED["linux-gh"],
    )
    if prefixed_hard or prefixed.startswith("WARN "):
        print("FAIL runner tools: version suffix was a warning", file=sys.stderr)
        return 1
    missing, missing_hard = drift_line("windows-docker-client", "", RECORDED["windows-docker-client"])
    if missing_hard or "not observed" not in missing or not missing.startswith("WARN "):
        print("FAIL runner tools: a missing image tool was a hard failure", file=sys.stderr)
        return 1
    if finish([], [missing]) != 0:
        print("FAIL runner tools: a missing image tool failed the job", file=sys.stderr)
        return 1
    if finish(["runner tool windows-git was not observed"], []) == 0:
        print("FAIL runner tools: a hard problem did not fail", file=sys.stderr)
        return 1
    print("OK runner tools self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=("linux", "windows"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.platform is None:
        print("FAIL runner tools: platform is required", file=sys.stderr)
        return 1
    observed = linux_observations() if args.platform == "linux" else windows_observations()
    problems, notes = collect(observed)
    return finish(problems, notes)


if __name__ == "__main__":
    raise SystemExit(main())
