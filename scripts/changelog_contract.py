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
import sys
import tempfile
from pathlib import Path

from vf_spawn import SpawnRefusal, revision_form_errors, run_git, same_pinned_directory, git_revision

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT_RE = re.compile(r"^changelog\.d/([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
CAPABILITY_RE = re.compile(r"^(packages/|office/|scripts/|\.github/workflows/|constitution/)")
UNRELEASED = "## [Unreleased]"


def fragment_name(path: str) -> bool:
    return FRAGMENT_RE.match(path.replace("\\", "/")) is not None


def _entry(item: str | tuple) -> tuple[str, str]:
    """A plain path counts as a modification. A tuple is (status, path) or (status, path, text)."""
    if isinstance(item, tuple):
        status, path = item[0], item[1]
        return status, str(path).replace("\\", "/")
    return "M", str(item).replace("\\", "/")


def _supplied_text(item: str | tuple) -> str | None:
    if isinstance(item, tuple) and len(item) >= 3:
        return item[2]
    return None


def needs_note(paths: list) -> list[str]:
    """Capability paths that must ship with a changelog note."""
    found = []
    for item in paths:
        _status, normal = _entry(item)
        if fragment_name(normal):
            continue
        if CAPABILITY_RE.search(normal):
            found.append(normal)
    return found


def show_blob(repo: Path, rev: str, path: str) -> str | None:
    """File bytes at rev. None when git cannot show that path."""
    spec = f"{git_revision(rev)}:{path.replace(chr(92), '/')}"
    proc = run_git(["show"], revisions=[spec], cwd=repo)
    if proc.returncode != 0:
        return None
    return proc.stdout


def fragment_text(item, repo: Path | None, base: str | None, head: str | None) -> str | None:
    """Head bytes for an added or modified fragment. Base bytes for a deletion."""
    supplied = _supplied_text(item)
    if supplied is not None:
        return supplied
    if repo is None or isinstance(item, str):
        return None
    status, path = _entry(item)
    rev = base if status.startswith("D") else head
    if not rev:
        return None
    return show_blob(repo, rev, path)


def fragment_covers(item, repo: Path | None = None, base: str | None = None, head: str | None = None) -> bool:
    """Only an added fragment with a valid non-empty bullet covers.

    A bare path string is the older name-only probe. Status M is an existing
    fragment overwritten in place and does not cover.
    """
    status, normal = _entry(item)
    if not fragment_name(normal):
        return False
    if isinstance(item, str):
        return True
    if not status.startswith("A"):
        return False
    text = fragment_text(item, repo, base, head)
    if text is None:
        return False
    try:
        bullets_in(text, normal)
    except ValueError:
        return False
    return True


def fragment_problems(paths: list, repo: Path | None, base: str | None, head: str | None) -> list[str]:
    """An added or modified fragment must contain a valid bullet."""
    problems = []
    for item in paths:
        status, normal = _entry(item)
        if not fragment_name(normal) or not (status.startswith("A") or status.startswith("M")):
            continue
        if isinstance(item, str):
            continue
        text = fragment_text(item, repo, base, head)
        if text is None:
            problems.append(f"{normal} has no readable bullet")
            continue
        try:
            bullets_in(text, normal)
        except ValueError as exc:
            problems.append(str(exc))
    return problems


def changelog_text(paths: list, repo: Path | None, head: str | None) -> str | None:
    for item in paths:
        status, normal = _entry(item)
        if normal == "CHANGELOG.md" and not status.startswith("D"):
            supplied = _supplied_text(item)
            if supplied is not None:
                return supplied
    if repo is not None and head:
        return show_blob(repo, head, "CHANGELOG.md")
    return None


def compile_step(paths: list, repo: Path | None = None, base: str | None = None, head: str | None = None) -> bool:
    """True when the diff only folds fragments into CHANGELOG.md and deletes them."""
    deleted = []
    for item in paths:
        status, normal = _entry(item)
        if fragment_name(normal) and status.startswith("D"):
            deleted.append(item)
            continue
        if normal == "CHANGELOG.md" and not status.startswith("D"):
            continue
        return False
    if not deleted:
        return False
    changelog = changelog_text(paths, repo, head)
    if changelog is None:
        return False
    for item in deleted:
        text = fragment_text(item, repo, base, head)
        if text is None:
            return False
        try:
            bullets = bullets_in(text, _entry(item)[1])
        except ValueError:
            return False
        folded = unreleased_lines(changelog)
        if any(bullet not in folded for bullet in bullets):
            return False
    return True


def _line_text(line: str) -> str:
    return line.strip("\r\n")


def _fence_marker(line: str) -> bool:
    text = _line_text(line).lstrip()
    return text.startswith("```") or text.startswith("~~~")


def _section_heading(line: str) -> bool:
    """A level-2 heading. ``###`` stays inside the Unreleased section."""
    text = _line_text(line)
    return text == "##" or text.startswith("## ") or text.startswith("##\t")


def _unreleased_region(lines: list[str]) -> tuple[int, int, set[str]] | None:
    """Header index, next heading index, and lines that count as folded.

    The section ends at the next ``##`` heading outside a fence. A missing
    Unreleased heading yields None. Bullets inside a fence are omitted.
    """
    texts = [_line_text(line) for line in lines]
    try:
        header = texts.index(UNRELEASED)
    except ValueError:
        return None
    present: set[str] = set()
    fenced = False
    end = len(lines)
    for index in range(header + 1, len(lines)):
        if _fence_marker(lines[index]):
            fenced = not fenced
            continue
        if fenced:
            continue
        if _section_heading(lines[index]):
            end = index
            break
        present.add(texts[index])
    return header, end, present


def unreleased_lines(changelog: str) -> set[str]:
    """Whole lines between ``## [Unreleased]`` and the next ``##`` heading.

    A bullet inside a fenced code block is not folded. ``splitlines`` drops a
    trailing CR, so a CRLF changelog still matches an LF bullet. No Unreleased
    heading yields an empty set.
    """
    found = _unreleased_region(changelog.splitlines())
    if found is None:
        return set()
    return found[2]


def covered(paths: list, repo: Path | None = None, base: str | None = None, head: str | None = None) -> bool:
    """A valid fragment covers the gate. Deleting CHANGELOG.md or a fragment does not."""
    for item in paths:
        if fragment_covers(item, repo, base, head):
            return True
        status, normal = _entry(item)
        if normal == "CHANGELOG.md" and not status.startswith("D"):
            return True
    return False


def gate(paths: list, repo: Path | None = None, base: str | None = None, head: str | None = None) -> int:
    deleted = [
        _entry(item)[1]
        for item in paths
        if fragment_name(_entry(item)[1]) and _entry(item)[0].startswith("D")
    ]
    if deleted and not compile_step(paths, repo, base, head):
        print(
            "FAIL deleting changelog.d fragments is only the compile step. "
            "The diff may contain CHANGELOG.md and those deletions, and each deleted "
            "bullet must be in CHANGELOG.md. See docs/CHANGELOG-FRAGMENTS.md."
        )
        for path in deleted:
            print(f"  - {path}")
        return 1
    problems = fragment_problems(paths, repo, base, head)
    if problems:
        for item in problems:
            print(f"FAIL changelog fragment: {item}")
        return 1
    need = needs_note(paths)
    if not need:
        print("OK changelog fragment contract (no capability change)")
        return 0
    if covered(paths, repo, base, head):
        how = "fragment" if any(fragment_covers(p, repo, base, head) for p in paths) else "CHANGELOG.md"
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


def _rename_new_status(status: str, new_normal: str) -> str:
    """A rename into a fragment or into CHANGELOG.md is an add."""
    if new_normal == "CHANGELOG.md" or fragment_name(new_normal):
        return "A"
    return status[:1]


def changed_files(base: str, head: str, repo: Path = ROOT) -> list[tuple[str, str]]:
    """Name and status. A rename of CHANGELOG.md away is a delete of that file."""
    spec = f"{git_revision(base)}...{git_revision(head)}"
    proc = run_git(
        ["diff", "--name-status", "--find-renames"], revisions=[spec], cwd=repo
    )
    if proc.returncode != 0:
        raise SystemExit(f"FAIL git diff {base}...{head}: {proc.stderr.strip()}")
    entries: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status[:1] in {"R", "C"} and len(parts) >= 3:
            old, new = parts[1], parts[2]
            old_normal = old.replace("\\", "/")
            new_normal = new.replace("\\", "/")
            if old_normal == "CHANGELOG.md" and new_normal != "CHANGELOG.md":
                entries.append(("D", old))
            if status[:1] == "R" and fragment_name(old_normal) and old_normal != new_normal:
                entries.append(("D", old))
            entries.append((_rename_new_status(status, new_normal), new))
            continue
        entries.append((status, parts[-1]))
    return entries


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
        if not line[2:].strip():
            raise ValueError(f"{label} bullet is empty")
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
    lines = changelog.splitlines(keepends=True)
    found = _unreleased_region(lines)
    if found is None:
        raise ValueError("CHANGELOG.md is missing ## [Unreleased]")
    header, nxt, present = found
    section = lines[header + 1:nxt]
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


def write_bytes_atomic(path: Path, data: bytes) -> None:
    """Replace path only after the new bytes are on disk. A failed replace keeps the old file."""
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".changelog.", suffix=".tmp")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        if tmp.exists():
            tmp.unlink()
        raise


def compile_tree(root: Path) -> int:
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.is_file():
        print("FAIL CHANGELOG.md is missing", file=sys.stderr)
        return 1
    # read_bytes keeps CRLF. Path.read_text() translates newlines before fold().
    original = changelog_path.read_bytes().decode("utf-8")
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
        write_bytes_atomic(changelog_path, folded.encode("utf-8"))
    for path in ready:
        path.unlink()
    print(f"OK changelog compile fragments={len(ready)} changed={str(folded != original).lower()}")
    return 0


def live_gate(repo: Path = ROOT, base: str = "origin/main", head: str = "HEAD") -> int:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("SKIP changelog-contract (hosted workflow runs the fragment gate as its own step)")
        return 0
    probe = run_git(
        ["rev-parse", "--verify", "-q"],
        revisions=[f"{git_revision(base)}^{{commit}}"],
        cwd=repo,
    )
    if probe.returncode != 0:
        print(f"SKIP changelog-contract (no git base {base})")
        return 0
    return gate(changed_files(base, head, repo), repo, base, head)


def prove_git_hygiene() -> list[str]:
    """Absolute git, a timeout, and no inherited GIT_* or parent environment."""
    import vf_spawn

    errors: list[str] = []
    sentinel = "VF_SPAWN_SENTINEL"
    previous = {
        sentinel: os.environ.get(sentinel),
        "GIT_EXEC_PATH": os.environ.get("GIT_EXEC_PATH"),
        "GIT_CONFIG_COUNT": os.environ.get("GIT_CONFIG_COUNT"),
    }
    os.environ[sentinel] = "nope"
    os.environ["GIT_EXEC_PATH"] = "/evil/git-core"
    os.environ["GIT_CONFIG_COUNT"] = "1"
    captured: list[tuple[list[str], dict]] = []
    original = vf_spawn.subprocess.run

    def fake_run(argv, **kwargs):
        captured.append((list(argv), kwargs))
        return vf_spawn.subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    vf_spawn.subprocess.run = fake_run
    try:
        run_git(["status"])
        changed_files("a", "b", ROOT)
        try:
            changed_files("--output=/tmp/pwn", "b", ROOT)
        except SpawnRefusal as exc:
            if str(exc) != "GIT_REV_REFUSED":
                errors.append(f"dash revision refused as {exc}")
        else:
            errors.append("leading-dash revision was accepted")
        before = len(captured)
        for label, token in (
            ("newline and nul", "rev\n\x00"),
            ("newline", "rev\nmore"),
            ("nul", "rev\x00more"),
            ("cr", "rev\rmore"),
        ):
            try:
                changed_files(token, "b", ROOT)
            except SpawnRefusal as exc:
                if str(exc) != "GIT_REV_REFUSED":
                    errors.append(f"{label} revision refused as {exc}")
            else:
                errors.append(f"{label} revision was accepted")
        if len(captured) != before:
            errors.append("control-byte revision spawned git")
    except (SpawnRefusal, SystemExit) as exc:
        errors.append(f"git spawn refused: {exc}")
    finally:
        vf_spawn.subprocess.run = original
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    if errors:
        return errors
    if len(captured) != 2:
        return ["git spawn did not run"]
    for argv, kwargs in captured:
        if not argv or not os.path.isabs(argv[0]):
            errors.append(f"git was not absolute: {argv}")
        if kwargs.get("timeout") != vf_spawn.GIT_TIMEOUT_SECONDS:
            errors.append("git timeout missing")
        env = kwargs.get("env")
        git_keys = {
            str(key).upper()
            for key in (env or {})
            if str(key).upper().startswith("GIT_")
        }
        if (
            not isinstance(env, dict)
            or sentinel in env
            or git_keys != {"GIT_CONFIG_NOSYSTEM"}
            or env.get("GIT_CONFIG_NOSYSTEM") != "1"
        ):
            errors.append(f"git environment was not allowlisted: {env}")
            return errors
        first, *rest = env.get("PATH", "").split(os.pathsep)
        if not same_pinned_directory(first, str(Path(argv[0]).resolve().parent)):
            errors.append(f"git PATH was not the executable directory: {env.get('PATH')}")
        install = Path(argv[0]).resolve().parent
        root = install.parent if os.name == "nt" and install.parent.name.lower() == "git" else install
        for entry in rest:
            resolved = Path(entry).resolve()
            if resolved != root and root not in resolved.parents:
                errors.append(f"git PATH escaped the install: {entry}")
    errors.extend(revision_form_errors(captured[1][0], ["a...b"]))
    short = "C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\git-abc"
    long = "C:\\Users\\runneradmin\\AppData\\Local\\Temp\\git-abc"

    def expand_short(path: str) -> str:
        return str(path).replace("/", "\\").replace("RUNNER~1", "runneradmin")

    if not same_pinned_directory(short, long, realpath=expand_short, fold_case=True, separator=";"):
        errors.append("8.3 git directory did not match its long path")
    if not same_pinned_directory(short, long.upper(), realpath=expand_short, fold_case=True, separator=";"):
        errors.append("git pin comparison stayed case-sensitive")
    if same_pinned_directory(short, long + "\\other", realpath=expand_short, fold_case=True, separator=";"):
        errors.append("a different directory was accepted as the git pin")
    if same_pinned_directory(long + ";" + short, long, realpath=expand_short, fold_case=True, separator=";"):
        errors.append("a search PATH was accepted as the git pin")
    return errors


def selftest() -> int:
    hygiene = prove_git_hygiene()
    if hygiene:
        for item in hygiene:
            print(f"FAIL changelog-contract git spawn: {item}", file=sys.stderr)
        return 1
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
    _expect_bullet_error("-   \n", "bullet is empty", bad, "whitespace bullet")
    _expect_bullet_error("- \t\n", "bullet is empty", bad, "tab bullet")
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
    released_tail = crlf.split("## [1.0.0]\r\n", 1)[1].encode("utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        changelog = root / "CHANGELOG.md"
        changelog.write_bytes(crlf.encode("utf-8"))
        folder = root / "changelog.d"
        folder.mkdir()
        (folder / "example-pr.md").write_text(sample, encoding="utf-8")
        try:
            rc, text = _capture_call(lambda: compile_tree(root))
        except Exception as exc:
            bad.append(f"CRLF compile raised {type(exc).__name__}: {exc}")
        else:
            if rc != 0:
                bad.append(f"CRLF compile failed: {text}")
            written = changelog.read_bytes()
            marker = b"## [1.0.0]\r\n"
            if marker not in written or written.split(marker, 1)[1] != released_tail:
                bad.append("compile rewrote the CRLF released section")
            if list(root.glob(".changelog.*.tmp")):
                bad.append("compile left a changelog temp file")
        changelog.write_bytes(crlf.encode("utf-8"))
        (folder / "example-pr.md").write_text(sample, encoding="utf-8")
        original_replace = os.replace

        def replace_fails(src, dst):
            raise OSError("disk full")

        os.replace = replace_fails
        try:
            try:
                compile_tree(root)
            except OSError as exc:
                if "disk full" not in str(exc):
                    bad.append(f"atomic replace raised the wrong error: {exc}")
            else:
                bad.append("a failed changelog replace was swallowed")
            if changelog.read_bytes() != crlf.encode("utf-8"):
                bad.append("a failed changelog replace rewrote CHANGELOG.md")
            if list(root.glob(".changelog.*.tmp")):
                bad.append("a failed changelog replace left a temp file")
        finally:
            os.replace = original_replace

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
    slash_only = fragment_name
    def fragment_without_backslash_fold(path: str) -> bool:
        return FRAGMENT_RE.match(path) is not None
    globals()["fragment_name"] = fragment_without_backslash_fold
    try:
        if covered(["changelog.d\\foo.md"]) is not True:
            bad.append("windows fragment path must count as a fragment")
    finally:
        globals()["fragment_name"] = slash_only
    if gate(["scripts\\tool.py", "changelog.d\\foo.md"]) != 0:
        bad.append("windows fragment must cover a windows capability path")
    if gate(["scripts\\tool.py"]) != 1:
        bad.append("windows capability path without a fragment must fail")
    return 33


def _selftest(bad: list[str], counted: list[int]) -> int:
    probes = [
        (gate(["scripts/tool.py", "changelog.d/example-pr.md"]) == 0, "fragment-only capability PR must pass"),
        (gate(["scripts/tool.py"]) == 1, "capability PR with neither must fail"),
        (gate(["scripts\\tool.py"]) == 1, "windows capability path without a fragment must fail"),
        (gate(["scripts/tool.py", "CHANGELOG.md"]) == 0, "CHANGELOG.md edit must still pass"),
        (gate([("M", "scripts/tool.py"), ("D", "CHANGELOG.md")]) == 1, "deleting CHANGELOG.md must not cover a capability PR"),
        (gate([("M", "scripts/tool.py"), ("D", "CHANGELOG.md"), ("A", "changelog.d/example-pr.md", "- 2026-10-18 - **Example:** one line.\n")]) == 0, "a fragment still covers a deleted changelog"),
        (gate([("D", "changelog.d/someone-else.md"), ("M", "scripts/check-all.py")]) == 1, "deleting a fragment must not cover a capability PR"),
        (gate([("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n"), ("A", "changelog.d/mine.md", "- 2026-10-18 - **Mine:** one line.\n"), ("M", "scripts/check-all.py")]) == 1, "a new fragment must not excuse deleting an existing one"),
        (gate([("M", "changelog.d/someone-else.md", "-   \n"), ("M", "scripts/check-all.py")]) == 1, "an emptied fragment must not cover a capability PR"),
        (gate([("M", "changelog.d/someone-else.md", "\n"), ("M", "scripts/check-all.py")]) == 1, "an empty fragment file must not cover a capability PR"),
        (gate([("M", "changelog.d/someone-else.md", "-   \n"), ("A", "changelog.d/mine.md", "- 2026-10-18 - **Mine:** one line.\n"), ("M", "scripts/check-all.py")]) == 1, "a new fragment must not excuse emptying an existing one"),
        (gate([("A", "changelog.d/mine.md", "- 2026-10-18 - **Mine:** one line.\n"), ("M", "scripts/check-all.py")]) == 0, "an added fragment with a real bullet must cover"),
        (gate([("M", "CHANGELOG.md", "## [Unreleased]\n\n- 2026-10-18 - **Theirs:** stays.\n"), ("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n")]) == 0, "the compile step may delete a fragment whose bullet is in CHANGELOG.md"),
        (gate([("M", "CHANGELOG.md", "## [Unreleased]\n\n- 2026-10-18 - **Unrelated:** other.\n"), ("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n")]) == 1, "the compile step refuses a deleted bullet that was not folded"),
        (gate([("M", "CHANGELOG.md", "## [Unreleased]\n\n- 2026-10-18 - **Theirs:** stays. extra words.\n"), ("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n")]) == 1, "a longer changelog line is not a folded bullet"),
        (gate([("M", "CHANGELOG.md", "## [Unreleased]\n\n- 2026-10-18 - **Other:** stays.\n\n## [1.0.0]\n\n- 2026-10-18 - **Theirs:** stays.\n"), ("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n")]) == 1, "a bullet only in a released section is not folded"),
        (gate([("M", "CHANGELOG.md", "## [Unreleased]\r\n\r\n- 2026-10-18 - **Theirs:** stays.\r\n\r\n## [1.0.0]\r\n\r\n"), ("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n")]) == 0, "a CRLF Unreleased line still matches the folded bullet"),
        (gate([("M", "changelog.d/someone-else.md", "- 2026-10-18 - **Replacement:** erases theirs.\n"), ("M", "scripts/check-all.py")]) == 1, "overwriting an existing fragment must not cover a capability PR"),
        (gate([("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n")]) == 1, "deleting a fragment without folding it into CHANGELOG.md must fail"),
        (gate([("M", "CHANGELOG.md", "## [Unreleased]\n\n- 2026-10-18 - **Theirs:** stays.\n"), ("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n"), ("M", "docs/NOTE.md")]) == 1, "a docs edit beside a fragment deletion is not the compile step"),
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
    notes_log = (
        "## [Unreleased]\n\n- 2026-10-01 - **Kept:** stays.\n\n"
        "## Notes\n\n- 2026-10-18 - **Theirs:** stays.\n\n"
        "## [1.0.0]\n\n- released line must stay byte for byte.\n"
    )
    folded_notes = fold(notes_log, ["- 2026-10-18 - **Theirs:** stays."])
    fenced_log = (
        "## [Unreleased]\n\n```\n- 2026-10-18 - **Theirs:** stays.\n```\n\n"
        "## [1.0.0]\n\n- released line must stay byte for byte.\n"
    )
    folded_fence = fold(fenced_log, ["- 2026-10-18 - **Theirs:** stays."])
    probes.extend([
        (notes_log.split("## Notes\n", 1)[1] == folded_notes.split("## Notes\n", 1)[1], "fold rewrote the section after a plain heading"),
        ("- 2026-10-18 - **Theirs:** stays." in folded_notes.split("## Notes\n", 1)[0], "fold treated a later heading's bullet as already present"),
        (fenced_log.split("```\n", 1)[1] == folded_fence.split("```\n", 1)[1], "fold rewrote a fenced bullet"),
        (folded_fence.split("```\n", 1)[0].count("- 2026-10-18 - **Theirs:** stays.") == 1, "fold treated a fenced bullet as already present"),
    ])
    bullet = "- 2026-10-18 - **Theirs:** stays.\n"
    deleted = ("D", "changelog.d/someone-else.md", bullet)
    no_heading = [("M", "CHANGELOG.md", "intro\n\n" + bullet), deleted]
    plain_heading = [("M", "CHANGELOG.md", "## [Unreleased]\n\n- 2026-10-18 - **Other:** stays.\n\n## Notes\n\n" + bullet), deleted]
    fenced_bullet = [("M", "CHANGELOG.md", "## [Unreleased]\n\n```\n" + bullet + "```\n\n- 2026-10-18 - **Other:** stays.\n"), deleted]
    after_fence = [
        ("M", "CHANGELOG.md", "## [Unreleased]\n\n```\n## Notes\n" + bullet + "```\n\n- 2026-10-18 - **Other:** stays.\n"),
        ("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Other:** stays.\n"),
    ]
    subsection = [("M", "CHANGELOG.md", "## [Unreleased]\n\n### Notes\n\n" + bullet), deleted]
    probes.extend([
        (gate(no_heading) == 1, "a changelog with no Unreleased heading must refuse"),
        (unreleased_lines("intro\n\n" + bullet) == set(), "missing Unreleased did not yield an empty fold"),
        (gate(plain_heading) == 1, "a bullet under a later heading is not folded"),
        (gate(fenced_bullet) == 1, "a bullet inside a code fence is not folded"),
        (gate(after_fence) == 0, "a heading inside a code fence ended the fold"),
        (gate(subsection) == 0, "a level-3 heading ended the fold"),
    ])
    released_only = [
        ("M", "CHANGELOG.md", "## [Unreleased]\n\n- 2026-10-18 - **Other:** stays.\n\n## [1.0.0]\n\n- 2026-10-18 - **Theirs:** stays.\n"),
        ("D", "changelog.d/someone-else.md", "- 2026-10-18 - **Theirs:** stays.\n"),
    ]
    saved_lines = unreleased_lines
    globals()["unreleased_lines"] = lambda changelog: set(changelog.splitlines())
    try:
        probes.append((
            gate(released_only) == 0,
            "whole-file membership still refused a released bullet",
        ))
    finally:
        globals()["unreleased_lines"] = saved_lines

    def _texts(rows: list[str]) -> list[str]:
        return [line.strip("\r\n") for line in rows]

    def _region_missing_is_whole_file(rows: list[str]) -> tuple[int, int, set[str]] | None:
        texts = _texts(rows)
        if UNRELEASED not in texts:
            return 0, len(rows), set(texts)
        return saved_region(rows)

    def _region_bracket_only(rows: list[str]) -> tuple[int, int, set[str]] | None:
        texts = _texts(rows)
        try:
            header = texts.index(UNRELEASED)
        except ValueError:
            return None
        present: set[str] = set()
        end = len(rows)
        for index in range(header + 1, len(rows)):
            if texts[index].startswith("## ["):
                end = index
                break
            present.add(texts[index])
        return header, end, present

    def _region_keep_fences(rows: list[str]) -> tuple[int, int, set[str]] | None:
        texts = _texts(rows)
        try:
            header = texts.index(UNRELEASED)
        except ValueError:
            return None
        present: set[str] = set()
        end = len(rows)
        for index in range(header + 1, len(rows)):
            if texts[index] == "##" or texts[index].startswith("## ") or texts[index].startswith("##\t"):
                end = index
                break
            present.add(texts[index])
        return header, end, present

    saved_region = _unreleased_region
    mutants = (
        (_region_missing_is_whole_file, no_heading, "missing Unreleased still refused the folded bullet"),
        (_region_bracket_only, plain_heading, "a plain heading still ended the fold"),
        (_region_keep_fences, fenced_bullet, "a fenced bullet was still ignored"),
    )
    for mutant, sample_paths, message in mutants:
        globals()["_unreleased_region"] = mutant
        try:
            probes.append((gate(sample_paths) == 0, message))
        finally:
            globals()["_unreleased_region"] = saved_region
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
        run_git(list(args), cwd=repo, check=True)

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
        base = run_git(
            ["rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=repo, check=True
        ).stdout.strip()

        (repo / "scripts" / "tool.py").write_text("print(2)\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "neither")
        head = run_git(
            ["rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=repo, check=True
        ).stdout.strip()
        if gate(changed_files(base, head, repo), repo, base, head) != 1:
            errors.append("git PR with neither must fail")

        git(repo, "reset", "--hard", base)
        (repo / "scripts" / "tool.py").write_text("print(3)\n", encoding="utf-8")
        folder = repo / "changelog.d"
        folder.mkdir()
        (folder / "example-pr.md").write_text("- 2026-10-18 - **Example:** one line.\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "fragment only")
        head = run_git(
            ["rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=repo, check=True
        ).stdout.strip()
        names = changed_files(base, head, repo)
        if any(path.replace("\\", "/") == "CHANGELOG.md" for _status, path in names):
            errors.append("fragment fixture must not touch CHANGELOG.md")
        if gate(names, repo, base, head) != 0:
            errors.append("git fragment-only PR must pass")

        git(repo, "reset", "--hard", base)
        (repo / "scripts" / "tool.py").write_text("print(4)\n", encoding="utf-8")
        git(repo, "rm", "-q", "CHANGELOG.md")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "delete changelog")
        head = run_git(
            ["rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=repo, check=True
        ).stdout.strip()
        deleted = changed_files(base, head, repo)
        if ("D", "CHANGELOG.md") not in [(status, path.replace("\\", "/")) for status, path in deleted]:
            errors.append(f"name-status did not report the changelog delete: {deleted}")
        if gate(deleted, repo, base, head) != 1:
            errors.append("git PR that deletes CHANGELOG.md must fail")

        git(repo, "reset", "--hard", base)
        theirs = "- 2026-10-18 - **Theirs:** stays.\n"
        folder = repo / "changelog.d"
        folder.mkdir(exist_ok=True)
        (folder / "someone-else.md").write_text(theirs, encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "their fragment")
        parent = run_git(
            ["rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=repo, check=True
        ).stdout.strip()

        def commit_from_parent(message: str) -> str:
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", message)
            return run_git(
                ["rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=repo, check=True
            ).stdout.strip()

        git(repo, "reset", "--hard", parent)
        (repo / "scripts" / "tool.py").write_text("print(5)\n", encoding="utf-8")
        (folder / "someone-else.md").unlink()
        head = commit_from_parent("delete their fragment")
        if gate(changed_files(parent, head, repo), repo, parent, head) != 1:
            errors.append("git PR that deletes a fragment must fail")

        git(repo, "reset", "--hard", parent)
        (repo / "scripts" / "tool.py").write_text("print(6)\n", encoding="utf-8")
        (folder / "someone-else.md").write_text("-   \n", encoding="utf-8")
        head = commit_from_parent("empty their fragment")
        if gate(changed_files(parent, head, repo), repo, parent, head) != 1:
            errors.append("git PR that empties a fragment must fail")

        git(repo, "reset", "--hard", parent)
        (repo / "scripts" / "tool.py").write_text("print(7)\n", encoding="utf-8")
        (folder / "someone-else.md").unlink()
        (folder / "mine.md").write_text("- 2026-10-18 - **Mine:** one line.\n", encoding="utf-8")
        head = commit_from_parent("replace their fragment")
        if gate(changed_files(parent, head, repo), repo, parent, head) != 1:
            errors.append("git PR that deletes a fragment and adds another must fail")

        git(repo, "reset", "--hard", parent)
        changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
        (repo / "CHANGELOG.md").write_text(changelog.replace(
            "## [Unreleased]\n\n", "## [Unreleased]\n\n" + theirs, 1
        ), encoding="utf-8")
        (folder / "someone-else.md").unlink()
        head = commit_from_parent("compile their fragment")
        if gate(changed_files(parent, head, repo), repo, parent, head) != 0:
            errors.append("git compile step that folds a fragment must pass")

        git(repo, "reset", "--hard", parent)
        git(repo, "mv", "changelog.d/someone-else.md", "changelog.d/mine.md")
        (repo / "scripts" / "tool.py").write_text("print(8)\n", encoding="utf-8")
        head = commit_from_parent("rename their fragment")
        raw = run_git(
            ["diff", "--name-status", "--find-renames"],
            revisions=[f"{parent}...{head}"],
            cwd=repo,
            check=True,
        )
        if not any(
            line.split("\t")[0][:1] == "R" and "changelog.d/someone-else.md" in line
            for line in raw.stdout.splitlines()
        ):
            errors.append(f"fixture did not produce a fragment rename: {raw.stdout!r}")
        renamed = changed_files(parent, head, repo)
        normalized = [(status, path.replace("\\", "/")) for status, path in renamed]
        if ("D", "changelog.d/someone-else.md") not in normalized:
            errors.append(f"renaming a fragment must be a deletion: {renamed}")
        if ("A", "changelog.d/mine.md") not in normalized:
            errors.append(f"the new side of a fragment rename must be an add: {renamed}")
        if any(status[:1] == "R" and path.replace("\\", "/") == "changelog.d/mine.md" for status, path in renamed):
            errors.append(f"the new side of a fragment rename kept status R: {renamed}")
        if gate(renamed, repo, parent, head) != 1:
            errors.append("renaming a fragment must not cover a capability PR")
        rename_parent, rename_head = parent, head
        saved_status = _rename_new_status
        globals()["_rename_new_status"] = lambda status, _new: status[:1]
        try:
            mutated = [
                (status, path.replace("\\", "/"))
                for status, path in changed_files(rename_parent, rename_head, repo)
            ]
            if ("R", "changelog.d/mine.md") not in mutated or ("A", "changelog.d/mine.md") in mutated:
                errors.append(
                    f"keeping rename status did not leave the new fragment path as R: {mutated}"
                )
        finally:
            globals()["_rename_new_status"] = saved_status

        git(repo, "reset", "--hard", parent)
        (repo / "docs").mkdir(exist_ok=True)
        (repo / "docs" / "plain.md").write_text("not a bullet\n", encoding="utf-8")
        doc_parent = commit_from_parent("add a plain doc")
        git(repo, "mv", "docs/plain.md", "changelog.d/from-doc.md")
        (repo / "scripts" / "tool.py").write_text("print(10)\n", encoding="utf-8")
        head = commit_from_parent("rename a doc into a fragment")
        raw = run_git(
            ["diff", "--name-status", "--find-renames"],
            revisions=[f"{doc_parent}...{head}"],
            cwd=repo,
            check=True,
        )
        if not any(
            line.split("\t")[0][:1] == "R" and "docs/plain.md" in line
            for line in raw.stdout.splitlines()
        ):
            errors.append(f"fixture did not produce a doc-to-fragment rename: {raw.stdout!r}")
        moved = [
            (status, path.replace("\\", "/"))
            for status, path in changed_files(doc_parent, head, repo)
        ]
        if ("A", "changelog.d/from-doc.md") not in moved:
            errors.append(f"renaming a non-fragment into a fragment must be an add: {moved}")

        git(repo, "reset", "--hard", parent)
        (repo / "scripts" / "tool.py").write_text("print(9)\n", encoding="utf-8")
        (folder / "someone-else.md").write_text(
            "- 2026-10-18 - **Replacement:** erases theirs.\n", encoding="utf-8"
        )
        head = commit_from_parent("overwrite their fragment")
        if gate(changed_files(parent, head, repo), repo, parent, head) != 1:
            errors.append("git PR that overwrites an existing fragment must fail")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    try:
        if args.selftest:
            return selftest()
        if args.files is not None:
            return gate(args.files)
        if not (args.base and args.head):
            ap.error("--base and --head are required (or --files / --selftest)")
        return gate(changed_files(args.base, args.head, args.repo), args.repo, args.base, args.head)
    except SpawnRefusal as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
