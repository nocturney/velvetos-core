#!/usr/bin/env python3
"""Install/remove Phase 4 local engineering-quality sources and diagram profiles."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import stat
import tempfile
from datetime import date
from pathlib import Path

from vf_spawn import (
    GIT_TIMEOUT_SECONDS,
    SpawnRefusal,
    allowlisted_git_errors,
    run_git,
    user_arg_separator_errors,
    windows_pin_case_errors,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "vfharness" / "devtools" / "components.json"
LOCAL = ROOT / ".local-devtools" / "phase4"
PROFILE_DIR = Path.home() / ".diagram-design" / "profiles"

ACTIVE = ("impeccable", "diagram-design")


GIT_FETCH_TIMEOUT_SECONDS = 120


def run(*args: str, cwd: Path | None = None, user_args: list[str] | None = None,
        revisions: list[str] | None = None) -> str:
    if not args or args[0] != "git":
        raise SystemExit("FAIL engineering-quality setup only runs git")
    timeout = GIT_FETCH_TIMEOUT_SECONDS if "fetch" in args else GIT_TIMEOUT_SECONDS
    try:
        proc = run_git(
            list(args[1:]),
            cwd=cwd,
            check=False,
            timeout=timeout,
            user_args=user_args,
            revisions=revisions,
        )
    except SpawnRefusal as exc:
        raise SystemExit(f"FAIL git spawn: {exc}") from exc
    if proc.returncode:
        raise SystemExit(f"FAIL {' '.join(args)}\n{proc.stdout}{proc.stderr}")
    return proc.stdout.strip()


def prove_git_hygiene() -> list[str]:
    """Every setup git command is absolute, timed, and allowlisted."""
    import vf_spawn

    errors: list[str] = []
    previous = {
        "VF_SPAWN_SENTINEL": os.environ.get("VF_SPAWN_SENTINEL"),
        "GIT_EXEC_PATH": os.environ.get("GIT_EXEC_PATH"),
    }
    os.environ["VF_SPAWN_SENTINEL"] = "nope"
    os.environ["GIT_EXEC_PATH"] = "/evil/git-core"
    captured: list[tuple[list[str], dict]] = []
    original = vf_spawn.subprocess.run

    def fake_run(argv, **kwargs):
        captured.append((list(argv), kwargs))
        return vf_spawn.subprocess.CompletedProcess(argv, 0, stdout="abc\n", stderr="")

    vf_spawn.subprocess.run = fake_run
    try:
        status = run("git", "status", cwd=ROOT)
        fetched = run(
            "git", "fetch", "-q", "--depth", "1", "origin", user_args=["pin"], cwd=ROOT
        )
        before = len(captured)
        for label, token in (
            ("newline and nul", "rev\n\x00"),
            ("newline", "rev\nmore"),
            ("nul", "rev\x00more"),
            ("cr", "rev\rmore"),
            ("leading newline", "\nrev"),
            ("leading nul", "\x00rev"),
            ("leading cr", "\rrev"),
            ("bare newline", "\n"),
            ("bare cr", "\r"),
            ("bare nul", "\x00"),
        ):
            try:
                run("git", "rev-parse", "--verify", "-q", revisions=[token], cwd=ROOT)
            except SystemExit as exc:
                if "GIT_REV_REFUSED" not in str(exc):
                    errors.append(f"{label} revision refused as {exc}")
            else:
                errors.append(f"{label} revision was accepted")
        if len(captured) != before:
            errors.append("control-byte revision spawned git")
        held = len(captured)
        for label, caller, code in (
            ("empty argv", lambda: run("git", "", cwd=ROOT), "GIT_ARGV_REFUSED"),
            ("non-string argv", lambda: run("git", None, cwd=ROOT), "GIT_ARGV_REFUSED"),
            ("empty user arg", lambda: run("git", "status", user_args=[""], cwd=ROOT), "GIT_USER_ARG_REFUSED"),
            (
                "non-string user arg",
                lambda: run("git", "status", user_args=[None], cwd=ROOT),
                "GIT_USER_ARG_REFUSED",
            ),
        ):
            try:
                caller()
            except SystemExit as exc:
                if code not in str(exc):
                    errors.append(f"{label} refused as {exc}")
            else:
                errors.append(f"{label} was accepted")
        if len(captured) != held:
            errors.append("refused git argv spawned git")
    except (SpawnRefusal, SystemExit) as exc:
        errors.append(f"git spawn refused: {exc}")
        status = fetched = ""
    finally:
        vf_spawn.subprocess.run = original
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    if errors:
        return errors
    if status != "abc" or fetched != "abc" or len(captured) != 2:
        return [f"git spawn did not return captured output: {captured!r}"]
    errors.extend(allowlisted_git_errors(captured[0][0], captured[0][1], timeout=GIT_TIMEOUT_SECONDS))
    errors.extend(
        allowlisted_git_errors(captured[1][0], captured[1][1], timeout=GIT_FETCH_TIMEOUT_SECONDS)
    )
    errors.extend(user_arg_separator_errors(captured[1][0], ["pin"]))
    errors.extend(windows_pin_case_errors())
    return errors


def prove_git_real() -> list[str]:
    """A real git remote add. ``--`` keeps a dash-leading url from being an option."""
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        try:
            run("git", "init", "-q", "-b", "main", cwd=repo)
            run(
                "git", "remote", "add", "origin",
                user_args=["--upload-pack=not-an-option"],
                cwd=repo,
            )
            url = run("git", "remote", "get-url", user_args=["origin"], cwd=repo)
        except SystemExit as exc:
            return [f"real git remote add failed: {exc}"]
    if url != "--upload-pack=not-an-option":
        errors.append(f"user url was parsed as a git option: {url!r}")
    return errors


def _bare_commit(root: Path) -> tuple[Path, str, Path, Path]:
    """Local bare repo plus an upload-pack script that would write a marker."""
    wt = root / "wt"
    wt.mkdir()
    run("git", "init", "-q", "-b", "main", cwd=wt)
    run("git", "config", "user.email", "fixture@example.invalid", cwd=wt)
    run("git", "config", "user.name", "fixture", cwd=wt)
    (wt / "f").write_text("hi\n", encoding="utf-8")
    run("git", "add", user_args=["f"], cwd=wt)
    run("git", "commit", "-qm", "c", cwd=wt)
    sha = run("git", "rev-parse", "--verify", "-q", revisions=["HEAD"], cwd=wt)
    bare = root / "bare.git"
    run("git", "clone", "--bare", "-q", user_args=[str(wt), str(bare)])
    marker = root / "PWN"
    script = root / "upload-pack.sh"
    script.write_text(
        "#!/bin/sh\n"
        f"echo pwned > {marker}\n"
        "exec git-upload-pack \"$@\"\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bare, sha, script, marker


def prove_ensure_clone() -> list[str]:
    """The real ensure_clone path, not only the fixture run() calls.

    A local bare repo must check out. A `--upload-pack=` source is stored as
    the url. A `--upload-pack=` pin is a refspec, so the script does not run.
    """
    global ROOT
    errors: list[str] = []
    previous = ROOT
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            bare, sha, script, marker = _bare_commit(root)
        except SystemExit as exc:
            return [f"bare repo setup failed: {exc}"]
        hostile = f"--upload-pack={script}"
        ROOT = root / "office"
        try:
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    ensure_clone({
                        "id": "fixture",
                        "local_source": "src",
                        "pin": sha,
                        "source": str(bare),
                    })
            except SystemExit as exc:
                errors.append(f"ensure_clone did not fetch the bare repo: {exc}")
            else:
                head = run(
                    "git", "rev-parse", "--verify", "-q",
                    revisions=["HEAD"], cwd=ROOT / "src",
                )
                if head != sha:
                    errors.append(f"ensure_clone checked out {head!r}, not {sha}")
            marker.unlink(missing_ok=True)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    ensure_clone({
                        "id": "fixture",
                        "local_source": "hostile-source",
                        "pin": sha,
                        "source": hostile,
                    })
            except SystemExit:
                pass
            else:
                errors.append("hostile source fetch succeeded")
            if marker.exists():
                errors.append("hostile source executed upload-pack")
            try:
                url = run(
                    "git", "remote", "get-url",
                    user_args=["origin"], cwd=ROOT / "hostile-source",
                )
            except SystemExit as exc:
                errors.append(f"hostile source was not stored after --: {exc}")
            else:
                if url != hostile:
                    errors.append(f"source was parsed as a git option: {url!r}")
            marker.unlink(missing_ok=True)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    ensure_clone({
                        "id": "fixture",
                        "local_source": "hostile-pin",
                        "pin": hostile,
                        "source": str(bare),
                    })
            except SystemExit:
                pass
            else:
                errors.append("hostile pin fetch succeeded")
            if marker.exists():
                errors.append("hostile pin executed upload-pack")
        finally:
            ROOT = previous
    return errors


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8-sig"))


def remove_tree(path: Path) -> None:
    def clear_readonly(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=clear_readonly)


def ensure_clone(component: dict) -> None:
    target = ROOT / component["local_source"]
    pin = component["pin"]
    if (target / ".git").is_dir():
        head = run("git", "rev-parse", "--verify", "-q", revisions=["HEAD"], cwd=target)
        if head == pin:
            print(f"OK source {component['id']} {pin[:12]}")
            return
        remove_tree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    run("git", "init", "-q", cwd=target)
    run("git", "remote", "add", "origin", user_args=[component["source"]], cwd=target)
    run("git", "fetch", "-q", "--depth", "1", "origin", user_args=[pin], cwd=target)
    run("git", "checkout", "-q", "--detach", "FETCH_HEAD", cwd=target)
    head = run("git", "rev-parse", "--verify", "-q", revisions=["HEAD"], cwd=target)
    if head != pin:
        raise SystemExit(f"FAIL pin mismatch {component['id']}: {head}")
    print(f"OK source {component['id']} {pin[:12]}")


ROLE_OVERRIDES = {
    "velvetos": {
        "paper": ("#F4F6FB", "#101828"),
        "paper-2": ("#FFFFFF", "#151D2E"),
        "ink": ("#171D2C", "#F4F6FB"),
        "ink-strong": ("#101828", "#FFFFFF"),
        "muted": ("#697287", "#BFC6D4"),
        "soft": ("#8A94A8", "#ADB7C9"),
        "rule": ("rgba(16,24,40,0.12)", "rgba(244,246,251,0.12)"),
        "rule-solid": ("#C6CDDC", "rgba(244,246,251,0.25)"),
        "accent": ("#6C7CFF", "#8794FF"),
        "accent-tint": ("rgba(108,124,255,0.10)", "rgba(135,148,255,0.12)"),
        "link": ("#45D7FF", "#78E4FF"),
    },
    "velvet-factory": {
        "paper": ("#F4F6FB", "#101828"),
        "paper-2": ("#FFFFFF", "#151D2E"),
        "ink": ("#171D2C", "#F4F6FB"),
        "ink-strong": ("#101828", "#FFFFFF"),
        "muted": ("#697287", "#BFC6D4"),
        "soft": ("#8A94A8", "#ADB7C9"),
        "rule": ("rgba(16,24,40,0.12)", "rgba(244,246,251,0.12)"),
        "rule-solid": ("#C6CDDC", "rgba(244,246,251,0.25)"),
        "accent": ("#FF4F91", "#FF7AAF"),
        "accent-tint": ("rgba(255,79,145,0.10)", "rgba(255,122,175,0.12)"),
        "link": ("#6C7CFF", "#8794FF"),
    },
}

PURPOSES = {
    "paper": "Page background, default node fill",
    "paper-2": "Diagram container bg, secondary fill",
    "ink": "Primary text, primary stroke",
    "ink-strong": "High-contrast text on accent fills",
    "muted": "Secondary text, default arrow stroke",
    "soft": "Sublabels, boundary labels",
    "rule": "Hairline borders",
    "rule-solid": "Stronger borders, baselines",
    "accent": "Focal / 1-2 max per diagram",
    "accent-tint": "Fill for accent-bordered boxes",
    "link": "HTTP/API calls, external arrows",
}
def render_profile(source: str, slug: str) -> str:
    overrides = ROLE_OVERRIDES[slug]
    tick = chr(96)
    lines = source.splitlines()
    out: list[str] = []
    for line in lines:
        replaced = False
        for role, (light, dark) in overrides.items():
            if line.startswith(f"| {tick}{role}{tick} |"):
                out.append(f"| {tick}{role}{tick} | {PURPOSES[role]} | {tick}{light}{tick} | {tick}{dark}{tick} |")
                replaced = True
                break
        if not replaced:
            out.append(line)
    display = "VelvetOS" if slug == "velvetos" else "Velvet Factory"
    header = (
        "<!-- diagram-design-profile\n"
        f"name: {display}\n"
        f"slug: {slug}\n"
        "source-url: none\n"
        f"created: {date.today().isoformat()}\n"
        f"updated: {date.today().isoformat()}\n"
        "notes: Generated from VelvetOS canonical Ink & Candy documentation tokens\n"
        "-->\n"
    )
    return header + "\n".join(out).rstrip() + "\n"


def install_profiles(diagram: dict) -> None:
    source_path = ROOT / diagram["local_source"] / "skills" / "diagram-design" / "references" / "style-guide.md"
    source = source_path.read_text(encoding="utf-8")
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    for slug in diagram["profiles"]:
        target = PROFILE_DIR / f"{slug}.md"
        target.write_text(render_profile(source, slug), encoding="utf-8")
        print(f"OK profile {slug} {target}")
def uninstall() -> None:
    if LOCAL.exists():
        remove_tree(LOCAL)
        print(f"OK removed {LOCAL}")
    for slug in ("velvetos", "velvet-factory"):
        target = PROFILE_DIR / f"{slug}.md"
        if target.exists():
            text = target.read_text(encoding="utf-8", errors="replace")
            if f"slug: {slug}" in text[:500]:
                target.unlink()
                print(f"OK removed {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    registry = load_registry()
    by_id = {row["id"]: row for row in registry["components"]}
    if args.uninstall:
        uninstall()
        return
    for component_id in ACTIVE:
        ensure_clone(by_id[component_id])
    install_profiles(by_id["diagram-design"])
    print("OK engineering-quality local install cost=0 hooks=disabled")


if __name__ == "__main__":
    main()
