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
    counted = [0]
    with contextlib.redirect_stdout(io.StringIO()):
        rc = _selftest(bad, counted)
    if rc == 0:
        print(f"OK changelog-contract selftest cases={counted[0]}")
    return rc


def _expect_bullet_error(text: str, needle: str, bad: list[str], what: str) -> None:
    try:
        bullets_in(text, what)
    except ValueError as exc:
        if needle not in str(exc):
            bad.append(f"{what} raised the wrong error: {exc}")
    else:
        bad.append(f"{what} was accepted")


def _capture_call(fn) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn()
    return rc, out.getvalue() + err.getvalue()


def _negative_checks(bad: list[str]) -> int:
    """Each check has a probe that passes only while that check is present."""
    sample = "- 2026-10-18 - **Example:** one line.\n"
    _expect_bullet_error(sample[:-1], "must end with LF", bad, "missing final LF")
    _expect_bullet_error(sample.replace("\n", "\r\n"), "contains CR", bad, "CR")
    _expect_bullet_error("not a bullet\n", "not a bullet", bad, "non-bullet line")
    _expect_bullet_error("\n", "has no bullets", bad, "empty fragment")
    _expect_bullet_error("<<<<<<< HEAD\n", "conflict marker", bad, "conflict start")
    _expect_bullet_error(">>>>>>> other\n", "conflict marker", bad, "conflict end")
    _expect_bullet_error("=======\n", "conflict marker", bad, "conflict middle")
    try:
        kept = bullets_in("- a\n\n- b\n", "blank lines")
    except ValueError as exc:
        bad.append(f"blank lines rejected: {exc}")
        kept = []
    if kept != ["- a", "- b"]:
        bad.append(f"blank lines were not skipped: {kept}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            rc, text = _capture_call(lambda: validate_committed(root))
        except Exception as exc:
            bad.append(f"missing changelog.d raised {type(exc).__name__}: {exc}")
        else:
            if rc != 0 or "none committed" not in text:
                bad.append("missing changelog.d must pass as none committed")
        folder = root / "changelog.d"
        folder.mkdir()
        (folder / "nested").mkdir()
        try:
            rc, text = _capture_call(lambda: validate_committed(root))
        except Exception as exc:
            bad.append(f"a directory in changelog.d raised {type(exc).__name__}: {exc}")
        else:
            if rc != 1 or "is not a file" not in text:
                bad.append("a directory in changelog.d must fail")
        (folder / "nested").rmdir()
        (folder / "Not-A-Slug.md").write_text(sample, encoding="utf-8")
        rc, text = _capture_call(lambda: validate_committed(root))
        if rc != 1 or "slug" not in text:
            bad.append("invalid fragment filename must fail")
        (folder / "Not-A-Slug.md").unlink()
        (folder / "example-pr.md").write_text("not a bullet\n", encoding="utf-8")
        rc, text = _capture_call(lambda: validate_committed(root))
        if rc != 1 or "not a bullet" not in text:
            bad.append("validate_committed accepted a non-bullet fragment")
        (folder / "example-pr.md").write_text(sample, encoding="utf-8")
        rc, text = _capture_call(lambda: validate_committed(root))
        if rc != 0:
            bad.append(f"valid fragment must pass: {text}")

        changelog = root / "CHANGELOG.md"
        try:
            rc, text = _capture_call(lambda: compile_tree(root))
        except Exception as exc:
            bad.append(f"compile without CHANGELOG.md raised {type(exc).__name__}: {exc}")
        else:
            if rc != 1 or "CHANGELOG.md is missing" not in text:
                bad.append("compile without CHANGELOG.md must fail")
        changelog.write_text("## [Unreleased]\n\n", encoding="utf-8")
        (folder / "example-pr.md").unlink()
        (folder / "Not-A-Slug.md").write_text(sample, encoding="utf-8")
        try:
            rc, text = _capture_call(lambda: compile_tree(root))
        except Exception as exc:
            bad.append(f"compile slug check raised {type(exc).__name__}: {exc}")
        else:
            if rc != 1 or "slug" not in text:
                bad.append("compile must refuse an invalid fragment filename")
        slug_path = folder / "Not-A-Slug.md"
        if slug_path.exists():
            slug_path.unlink()
        (folder / "example-pr.md").write_text("<<<<<<< HEAD\n", encoding="utf-8")
        try:
            rc, text = _capture_call(lambda: compile_tree(root))
        except Exception as exc:
            bad.append(f"compile conflict check raised {type(exc).__name__}: {exc}")
        else:
            if rc != 1 or "conflict marker" not in text:
                bad.append("compile must refuse a conflict marker")

    released = "- 2026-10-18 - **Released:** stays in 1.0.0."
    history = (
        "intro\n\n## [Unreleased]\n\n- 2026-10-01 - **Kept:** stays.\n\n"
        "## [1.0.0]\n\n" + released + "\n"
    )
    folded = fold(history, [released])
    if folded.count(released) != 2:
        bad.append("fold treated a released bullet as already in Unreleased")
    if not folded.split("## [1.0.0]", 1)[0].count(released):
        bad.append("fold did not copy a released bullet under Unreleased")
    if history.split("## [1.0.0]\n", 1)[1] != folded.split("## [1.0.0]\n", 1)[1]:
        bad.append("fold rewrote the released section while copying a bullet")
    repeated = "- 2026-10-18 - **Twice:** one line."
    if fold(history, [repeated, repeated]).count(repeated) != 1:
        bad.append("fold duplicated one bullet inside a single call")
    try:
        fold("no header\n", [repeated])
        bad.append("fold without Unreleased was accepted")
    except ValueError as exc:
        if "Unreleased" not in str(exc):
            bad.append(f"missing Unreleased raised the wrong error: {exc}")
    crlf = history.replace("\n", "\r\n")
    crlf_folded = fold(crlf, [repeated])
    if "\r\n" + repeated + "\r\n" not in crlf_folded:
        bad.append("fold dropped CRLF on a CRLF changelog")

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = live_gate(base="refs/no-such-changelog-base-6919")
    if rc != 0 or "SKIP" not in out.getvalue():
        bad.append("a missing git base must skip the live gate")
    previous = os.environ.get("GITHUB_ACTIONS")
    os.environ["GITHUB_ACTIONS"] = "true"
    try:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = live_gate()
        if rc != 0 or "SKIP" not in out.getvalue():
            bad.append("GITHUB_ACTIONS must skip the live gate")
    finally:
        if previous is None:
            os.environ.pop("GITHUB_ACTIONS", None)
        else:
            os.environ["GITHUB_ACTIONS"] = previous
    try:
        changed_files("refs/no-such-changelog-base-6919", "HEAD")
        bad.append("a bad git diff must fail closed")
    except SystemExit:
        pass
    if gate(["scripts\\tool.py", "changelog.d\\example-pr.md"]) != 0:
        bad.append("backslash fragment paths must pass")
    return 26


def _selftest(bad: list[str], counted: list[int]) -> int:
    probes = [
        (gate(["scripts/tool.py", "changelog.d/example-pr.md"]) == 0, "fragment-only capability PR must pass"),
        (gate(["scripts/tool.py"]) == 1, "capability PR with neither must fail"),
        (gate(["scripts\\tool.py"]) == 1, "windows capability path without a fragment must fail"),
        (gate(["scripts/tool.py", "CHANGELOG.md"]) == 0, "CHANGELOG.md edit must still pass"),
        (gate(["docs/NOTE.md"]) == 0, "docs-only PR must pass without a fragment"),
        (gate(["changelog.d/example-pr.md"]) == 0, "fragment file alone must pass"),
    ]
    sample = "- 2026-10-18 - **Example:** one line.\n"
    try:
        bullets_in(sample, "sample")
        probes.append((True, "valid bullet"))
    except ValueError as exc:
        probes.append((False, f"valid bullet rejected: {exc}"))
    history = (
        "intro\n\n## [Unreleased]\n\n- 2026-10-01 - **Kept:** stays.\n\n"
        "## [1.0.0]\n\n- released line must stay byte for byte.\n"
    )
    once = fold(history, ["- 2026-10-18 - **Example:** one line."])
    twice = fold(once, ["- 2026-10-18 - **Example:** one line."])
    probes.extend([
        (once == twice, "fold is not idempotent"),
        (history.split("## [1.0.0]\n", 1)[1] == once.split("## [1.0.0]\n", 1)[1], "fold rewrote released history"),
        (once.count("- 2026-10-18 - **Example:** one line.") == 1, "fold duplicated a bullet"),
        ("- 2026-10-01 - **Kept:** stays." in once, "fold dropped an existing Unreleased bullet"),
    ])
    negative_cases = _negative_checks(bad)
    git_errors = git_fixture()
    probes.append((not git_errors, "git fixture"))
    bad.extend(git_errors)
    counted[0] = len(probes) + negative_cases
    for ok, message in probes:
        if not ok and message not in bad:
            bad.append(message)
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
