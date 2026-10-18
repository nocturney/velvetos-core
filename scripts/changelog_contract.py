#!/usr/bin/env python3
"""Changelog fragment gate for pull requests.

A capability change under packages/, office/, scripts/, .github/workflows/
or constitution/ must include CHANGELOG.md or one changelog.d/<slug>.md
fragment. A fragment satisfies the gate. A diff with neither fails.
Docs outside those roots are not a changelog gate.

  python3 scripts/changelog_contract.py --base <sha> --head <sha>
  python3 scripts/changelog_contract.py --files a b
  python3 scripts/changelog_contract.py --selftest
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT_RE = re.compile(r"^changelog\.d/([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
CAPABILITY_RE = re.compile(r"^(packages/|office/|scripts/|\.github/workflows/|constitution/)")
UNRELEASED = "## [Unreleased]"


def fragment_name(path: str) -> bool:
    return FRAGMENT_RE.match(path.replace("\\", "/")) is not None


def needs_note(paths: list[str]) -> list[str]:
    """Capability paths that must ship with a changelog note."""
    found = []
    for path in paths:
        normal = path.replace("\\", "/")
        if fragment_name(normal):
            continue
        if CAPABILITY_RE.search(normal):
            found.append(normal)
    return found


def covered(paths: list[str]) -> bool:
    for path in paths:
        normal = path.replace("\\", "/")
        if normal == "CHANGELOG.md" or fragment_name(normal):
            return True
    return False


def gate(paths: list[str]) -> int:
    need = needs_note(paths)
    if not need:
        print("OK changelog fragment contract (no capability change)")
        return 0
    if covered(paths):
        how = "fragment" if any(fragment_name(p.replace("\\", "/")) for p in paths) else "CHANGELOG.md"
        print(f"OK changelog fragment contract ({how})")
        return 0
    print(
        "FAIL capability change with neither CHANGELOG.md nor changelog.d/<slug>.md. "
        "Add one fragment. Do not edit CHANGELOG.md for a normal PR. "
        "See docs/CHANGELOG-FRAGMENTS.md."
    )
    for path in need:
        print(f"  - {path}")
    return 1


def changed_files(base: str, head: str, repo: Path = ROOT) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=repo, text=True, capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"FAIL git diff {base}...{head}: {proc.stderr.strip()}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def bullets_in(text: str, label: str) -> list[str]:
    if "\r" in text:
        raise ValueError(f"{label} contains CR")
    if not text.endswith("\n"):
        raise ValueError(f"{label} must end with LF")
    bullets = []
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith("<<<<<<<") or line.startswith(">>>>>>>") or line == "=======":
            raise ValueError(f"{label} contains a conflict marker")
        if not line.startswith("- "):
            raise ValueError(f"{label} line is not a bullet: {line[:80]}")
        bullets.append(line)
    if not bullets:
        raise ValueError(f"{label} has no bullets")
    return bullets


def validate_committed(root: Path = ROOT) -> int:
    folder = root / "changelog.d"
    if not folder.is_dir():
        print("OK changelog fragments (none committed)")
        return 0
    problems = []
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            problems.append(f"{path.name} is not a file")
            continue
        rel = f"changelog.d/{path.name}"
        if not fragment_name(rel):
            problems.append(f"{rel} slug must be lowercase words separated by hyphens")
            continue
        try:
            bullets_in(path.read_text(encoding="utf-8"), rel)
        except ValueError as exc:
            problems.append(str(exc))
    if problems:
        for item in problems:
            print(f"FAIL changelog fragment: {item}", file=sys.stderr)
        return 1
    print(f"OK changelog fragments committed={len(list(folder.glob('*.md')))}")
    return 0


def fold(changelog: str, bullets: list[str]) -> str:
    """Insert missing bullets under Unreleased. Leave every other byte in place."""
    if UNRELEASED not in changelog.splitlines():
        raise ValueError("CHANGELOG.md is missing ## [Unreleased]")
    lines = changelog.splitlines(keepends=True)
    header = next(i for i, line in enumerate(lines) if line.strip("\r\n") == UNRELEASED)
    nxt = next(
        (i for i in range(header + 1, len(lines)) if lines[i].startswith("## [")),
        len(lines),
    )
    section = lines[header + 1:nxt]
    present = {line.strip("\r\n") for line in section}
    fresh = []
    for bullet in bullets:
        if bullet in present or bullet in fresh:
            continue
        fresh.append(bullet)
    if not fresh:
        return changelog
    nl = "\r\n" if lines[header].endswith("\r\n") else "\n"
    body = section[1:] if section and section[0].strip("\r\n") == "" else section
    chunk = [nl]
    for bullet in fresh:
        chunk.append(bullet + nl)
        chunk.append(nl)
    return "".join(lines[:header + 1] + chunk + body + lines[nxt:])


def compile_tree(root: Path) -> int:
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.is_file():
        print("FAIL CHANGELOG.md is missing", file=sys.stderr)
        return 1
    original = changelog_path.read_text(encoding="utf-8")
    folder = root / "changelog.d"
    paths = sorted(folder.glob("*.md")) if folder.is_dir() else []
    bullets: list[str] = []
    ready: list[Path] = []
    for path in paths:
        rel = f"changelog.d/{path.name}"
        if not fragment_name(rel):
            print(f"FAIL {rel} slug must be lowercase words separated by hyphens", file=sys.stderr)
            return 1
        try:
            found = bullets_in(path.read_text(encoding="utf-8"), rel)
        except ValueError as exc:
            print(f"FAIL {exc}", file=sys.stderr)
            return 1
        bullets.extend(found)
        ready.append(path)
    try:
        folded = fold(original, bullets)
    except ValueError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    if folded != original:
        changelog_path.write_bytes(folded.encode("utf-8"))
    for path in ready:
        path.unlink()
    print(f"OK changelog compile fragments={len(ready)} changed={str(folded != original).lower()}")
    return 0


def live_gate(repo: Path = ROOT, base: str = "origin/main", head: str = "HEAD") -> int:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("SKIP changelog-contract (hosted workflow runs the fragment gate as its own step)")
        return 0
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "-q", f"{base}^{{commit}}"],
        cwd=repo, text=True, capture_output=True,
    )
    if probe.returncode != 0:
        print(f"SKIP changelog-contract (no git base {base})")
        return 0
    return gate(changed_files(base, head, repo))


def selftest() -> int:
    bad: list[str] = []
    with contextlib.redirect_stdout(io.StringIO()):
        rc = _selftest(bad)
    if rc == 0:
        print("OK changelog-contract selftest cases=10")
    return rc


def _selftest(bad: list[str]) -> int:
    if gate(["scripts/tool.py", "changelog.d/example-pr.md"]) != 0:
        bad.append("fragment-only capability PR must pass")
    if gate(["scripts/tool.py"]) != 1:
        bad.append("capability PR with neither must fail")
    if gate(["scripts/tool.py", "CHANGELOG.md"]) != 0:
        bad.append("CHANGELOG.md edit must still pass")
    if gate(["docs/NOTE.md"]) != 0:
        bad.append("docs-only PR must pass without a fragment")
    if gate(["changelog.d/example-pr.md"]) != 0:
        bad.append("fragment file alone must pass")
    sample = "- 2026-10-18 - **Example:** one line.\n"
    try:
        bullets_in(sample, "sample")
    except ValueError as exc:
        bad.append(f"valid bullet rejected: {exc}")
    try:
        bullets_in(sample.replace("\n", "\r\n"), "crlf")
        bad.append("CRLF fragment must fail")
    except ValueError:
        pass
    history = (
        "intro\n\n## [Unreleased]\n\n- 2026-10-01 - **Kept:** stays.\n\n"
        "## [1.0.0]\n\n- released line must stay byte for byte.\n"
    )
    once = fold(history, ["- 2026-10-18 - **Example:** one line."])
    twice = fold(once, ["- 2026-10-18 - **Example:** one line."])
    if once != twice:
        bad.append("fold is not idempotent")
    if history.split("## [1.0.0]\n", 1)[1] != once.split("## [1.0.0]\n", 1)[1]:
        bad.append("fold rewrote released history")
    if once.count("- 2026-10-18 - **Example:** one line.") != 1:
        bad.append("fold duplicated a bullet")
    if "- 2026-10-01 - **Kept:** stays." not in once:
        bad.append("fold dropped an existing Unreleased bullet")
    bad.extend(git_fixture())
    if bad:
        for item in bad:
            print(f"FAIL changelog-contract selftest: {item}", file=sys.stderr)
        return 1
    return 0


def git_fixture() -> list[str]:
    """A real commit range: fragment-only passes, neither fails."""
    errors: list[str] = []

    def git(repo: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "user.name", "changelog-fixture")
        git(repo, "config", "commit.gpgsign", "false")
        (repo / "scripts").mkdir()
        (repo / "scripts" / "tool.py").write_text("print(1)\n", encoding="utf-8")
        (repo / "CHANGELOG.md").write_text("## [Unreleased]\n\n- base.\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "base")
        base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

        (repo / "scripts" / "tool.py").write_text("print(2)\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "neither")
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        if gate(changed_files(base, head, repo)) != 1:
            errors.append("git PR with neither must fail")

        git(repo, "reset", "--hard", base)
        (repo / "scripts" / "tool.py").write_text("print(3)\n", encoding="utf-8")
        folder = repo / "changelog.d"
        folder.mkdir()
        (folder / "example-pr.md").write_text("- 2026-10-18 - **Example:** one line.\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "fragment only")
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        names = changed_files(base, head, repo)
        if "CHANGELOG.md" in names:
            errors.append("fragment fixture must not touch CHANGELOG.md")
        if gate(names) != 0:
            errors.append("git fragment-only PR must pass")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.files is not None:
        return gate(args.files)
    if not (args.base and args.head):
        ap.error("--base and --head are required (or --files / --selftest)")
    return gate(changed_files(args.base, args.head, args.repo))


if __name__ == "__main__":
    raise SystemExit(main())
