#!/usr/bin/env python3
"""Check runner image tools against the versions already in use.

Linux versions are ubuntu-24.04 image ubuntu24/20261012.334.
Windows git is 2.56.0.windows.2, the version windows-latest reported on 2026-10-19.
Official checksum files are fetched and the artifact bytes are hashed.
Docker static archives have no published checksum; those two hashes are TOFU.
The installed binaries are not replaced. Stdlib only.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import urllib.request

LINUX_GIT_VERSION = "git version 2.55.0"
LINUX_GIT_SHA = "457fdb04dc8728e007d4688695e6912e6f680727920f2a40bf11eacc17505357"
LINUX_GIT_NAME = "git-2.55.0.tar.xz"
LINUX_GIT_SUMS = "https://mirrors.kernel.org/pub/software/scm/git/sha256sums.asc"
LINUX_GIT_URL = "https://mirrors.kernel.org/pub/software/scm/git/git-2.55.0.tar.xz"

LINUX_GH_VERSION = "gh version 2.102.0"
LINUX_GH_SHA = "bb766f710eef8ede859c18578c72c327597cd4c8a85b06001b1f3843c6019386"
LINUX_GH_NAME = "gh_2.102.0_linux_amd64.tar.gz"
LINUX_GH_SUMS = "https://github.com/cli/cli/releases/download/v2.102.0/gh_2.102.0_checksums.txt"
LINUX_GH_URL = "https://github.com/cli/cli/releases/download/v2.102.0/gh_2.102.0_linux_amd64.tar.gz"

LINUX_CURL_VERSION = "8.5.0-2ubuntu10.15"
LINUX_CURL_SHA = "4358c023e3c1a74bb1e77935807ea2088b137a898167fca278a1767c353ac1c5"
LINUX_CURL_NAME = "curl"
LINUX_CURL_SUMS = "https://archive.ubuntu.com/ubuntu/dists/noble-updates/main/binary-amd64/Packages.gz"
LINUX_CURL_URL = "https://archive.ubuntu.com/ubuntu/pool/main/c/curl/curl_8.5.0-2ubuntu10.15_amd64.deb"

LINUX_DOCKER_VERSION = "28.0.4"
LINUX_DOCKER_SHA = "6b130fa5fb13516620d5ece0b63f63a495cede428bb2f9e24449022e9d72e0cb"
LINUX_DOCKER_URL = "https://download.docker.com/linux/static/stable/x86_64/docker-28.0.4.tgz"
LINUX_DOCKER_CHECKSUM = "TOFU"

WINDOWS_GIT_VERSION = "git version 2.56.0.windows.2"
WINDOWS_GIT_SHA = "52188f917b378f00c70ec136bcf090005f30d44fbc4eba0bce759cc6592d60f6"
WINDOWS_GIT_NAME = "Git-2.56.0.2-64-bit.exe"
WINDOWS_GIT_SUMS = "https://api.github.com/repos/git-for-windows/git/releases/tags/v2.56.0.windows.2"
WINDOWS_GIT_URL = "https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.2/Git-2.56.0.2-64-bit.exe"

WINDOWS_GH_VERSION = "gh version 2.102.0"
WINDOWS_GH_SHA = "ae64e556ecc240b200f7eba60d550e4bb60d78e860e69dd88c449405b86067f4"
WINDOWS_GH_NAME = "gh_2.102.0_windows_amd64.zip"
WINDOWS_GH_URL = "https://github.com/cli/cli/releases/download/v2.102.0/gh_2.102.0_windows_amd64.zip"

WINDOWS_DOCKER_VERSION = "29.7.2"
WINDOWS_DOCKER_SHA = "ed9222f478a5d143ac90e8e2fd3209b5076382cdb4b210321f97aa4b68bc6811"
WINDOWS_DOCKER_URL = "https://download.docker.com/win/static/stable/x86_64/docker-29.7.2.zip"
WINDOWS_DOCKER_CHECKSUM = "TOFU"


def column_sha(text: str, filename: str) -> str:
    found: str | None = None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2 or parts[1] != filename:
            continue
        if found is not None:
            raise ValueError(f"duplicate checksum for {filename}")
        found = parts[0].lower()
    if found is None:
        raise ValueError(f"checksum file has no {filename}")
    return found


def package_sha(text: str, package: str, version: str) -> str:
    for block in text.split("\n\n"):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            if not line or line.startswith(" ") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields[key] = value.strip()
        if fields.get("Package") == package and fields.get("Version") == version:
            sha = fields.get("SHA256", "").lower()
            if len(sha) != 64:
                raise ValueError(f"{package} {version} has no sha256")
            return sha
    raise ValueError(f"Packages index has no {package} {version}")


def release_sha(body: str, filename: str) -> str:
    prefix = filename + " | "
    found: str | None = None
    for line in body.splitlines():
        if not line.startswith(prefix):
            continue
        if found is not None:
            raise ValueError(f"duplicate release checksum for {filename}")
        found = line[len(prefix):].strip().lower()
    if found is None or len(found) != 64:
        raise ValueError(f"release notes have no sha256 for {filename}")
    return found


def match_pin(
    actual: str,
    expected: str,
    got_sha: str,
    expected_sha: str,
    published: str | None,
) -> list[str]:
    problems: list[str] = []
    if actual != expected and not actual.startswith(expected + " "):
        problems.append(f"version {actual!r} != {expected}")
    if published is not None and published != expected_sha:
        problems.append(f"published checksum {published} != {expected_sha}")
    if got_sha != expected_sha:
        problems.append(f"artifact sha256 {got_sha} != {expected_sha}")
    return problems


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "velvetos-runner-pin"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read()


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def command_text(args: list[str]) -> str:
    proc = subprocess.run(args, text=True, capture_output=True, timeout=30)
    text = proc.stdout if proc.returncode == 0 else proc.stderr
    return (text or "").strip()


def first_line(text: str) -> str:
    return text.splitlines()[0].strip() if text else ""


def docker_versions() -> tuple[str, str]:
    proc = subprocess.run(
        ["docker", "version", "--format", "{{json .}}"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "docker version failed").strip()
        return detail, ""
    data = json.loads(proc.stdout)
    client = str((data.get("Client") or {}).get("Version") or "")
    server = str((data.get("Server") or {}).get("Version") or "")
    return client, server


def check_linux() -> list[str]:
    problems: list[str] = []
    git_line = first_line(command_text(["git", "--version"]))
    gh_line = first_line(command_text(["gh", "--version"]))
    curl_line = command_text(["dpkg-query", "-W", "-f", "${Version}", "curl"])
    docker_client, docker_server = docker_versions()
    git_sums = fetch(LINUX_GIT_SUMS).decode("utf-8", "replace")
    git_blob = fetch(LINUX_GIT_URL)
    problems.extend(match_pin(
        git_line, LINUX_GIT_VERSION, sha256(git_blob), LINUX_GIT_SHA,
        column_sha(git_sums, LINUX_GIT_NAME),
    ))
    gh_sums = fetch(LINUX_GH_SUMS).decode("utf-8", "replace")
    gh_blob = fetch(LINUX_GH_URL)
    problems.extend(match_pin(
        gh_line, LINUX_GH_VERSION, sha256(gh_blob), LINUX_GH_SHA,
        column_sha(gh_sums, LINUX_GH_NAME),
    ))
    packages = gzip.decompress(fetch(LINUX_CURL_SUMS)).decode("utf-8", "replace")
    curl_blob = fetch(LINUX_CURL_URL)
    problems.extend(match_pin(
        curl_line, LINUX_CURL_VERSION, sha256(curl_blob), LINUX_CURL_SHA,
        package_sha(packages, LINUX_CURL_NAME, LINUX_CURL_VERSION),
    ))
    docker_blob = fetch(LINUX_DOCKER_URL)
    problems.extend(match_pin(
        docker_client, LINUX_DOCKER_VERSION, sha256(docker_blob), LINUX_DOCKER_SHA, None,
    ))
    problems.extend(match_pin(
        docker_server, LINUX_DOCKER_VERSION, sha256(docker_blob), LINUX_DOCKER_SHA, None,
    ))
    return problems


def check_windows() -> list[str]:
    problems: list[str] = []
    git_line = first_line(command_text(["git", "--version"]))
    gh_line = first_line(command_text(["gh", "--version"]))
    docker_client, docker_server = docker_versions()
    release = json.loads(fetch(WINDOWS_GIT_SUMS).decode("utf-8"))
    git_blob = fetch(WINDOWS_GIT_URL)
    problems.extend(match_pin(
        git_line, WINDOWS_GIT_VERSION, sha256(git_blob), WINDOWS_GIT_SHA,
        release_sha(str(release.get("body") or ""), WINDOWS_GIT_NAME),
    ))
    gh_sums = fetch(LINUX_GH_SUMS).decode("utf-8", "replace")
    gh_blob = fetch(WINDOWS_GH_URL)
    problems.extend(match_pin(
        gh_line, WINDOWS_GH_VERSION, sha256(gh_blob), WINDOWS_GH_SHA,
        column_sha(gh_sums, WINDOWS_GH_NAME),
    ))
    docker_blob = fetch(WINDOWS_DOCKER_URL)
    problems.extend(match_pin(
        docker_client, WINDOWS_DOCKER_VERSION, sha256(docker_blob), WINDOWS_DOCKER_SHA, None,
    ))
    problems.extend(match_pin(
        docker_server, WINDOWS_DOCKER_VERSION, sha256(docker_blob), WINDOWS_DOCKER_SHA, None,
    ))
    return problems


def self_test() -> int:
    text = f"{'ab' * 32}  git-2.55.0.tar.xz\n-----BEGIN PGP SIGNATURE-----\n"
    if column_sha(text, "git-2.55.0.tar.xz") != "ab" * 32:
        print("FAIL runner tools: column checksum parser", file=sys.stderr)
        return 1
    packages = "Package: curl\nVersion: 8.5.0-2ubuntu10.15\nSHA256: " + ("cd" * 32) + "\n\n"
    if package_sha(packages, "curl", "8.5.0-2ubuntu10.15") != "cd" * 32:
        print("FAIL runner tools: package checksum parser", file=sys.stderr)
        return 1
    body = "Git-2.56.0-64-bit.exe | " + ("ef" * 32) + "\n"
    if release_sha(body, "Git-2.56.0-64-bit.exe") != "ef" * 32:
        print("FAIL runner tools: release checksum parser", file=sys.stderr)
        return 1
    digest = hashlib.sha256(b"bytes").hexdigest()
    if match_pin("28.0.4", "28.0.4", digest, digest, None):
        print("FAIL runner tools: TOFU match was refused", file=sys.stderr)
        return 1
    swapped = match_pin("28.0.4", "28.0.4", digest, "0" * 64, None)
    if not any("artifact sha256" in item for item in swapped):
        print("FAIL runner tools: swapped TOFU hash was not caught", file=sys.stderr)
        return 1
    bad = match_pin(LINUX_GIT_VERSION, LINUX_GIT_VERSION, digest, digest, "0" * 64)
    if not any("published checksum" in item for item in bad):
        print("FAIL runner tools: swapped published hash was not caught", file=sys.stderr)
        return 1
    if LINUX_DOCKER_CHECKSUM != "TOFU" or WINDOWS_DOCKER_CHECKSUM != "TOFU":
        print("FAIL runner tools: docker checksum kind drifted", file=sys.stderr)
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
    problems = check_linux() if args.platform == "linux" else check_windows()
    if problems:
        print("FAIL runner tools: " + "; ".join(problems), file=sys.stderr)
        return 1
    print(f"OK runner tools platform={args.platform}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
