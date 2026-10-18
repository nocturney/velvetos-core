#!/usr/bin/env python3
"""Set up the pinned CLI-Anything FreeCAD pilot and its portable FreeCAD backend."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from vf_spawn import (
    GIT_TIMEOUT_SECONDS,
    SpawnRefusal,
    allowlisted_git_errors,
    revision_form_errors,
    run_git,
    user_arg_separator_errors,
    windows_pin_case_errors,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "vfharness" / "devtools" / "cli-anything.json"
PATCH_PATH = ROOT / "packages" / "vfharness" / "devtools" / "cli-anything-freecad-overlay.patch"
LOCAL_ROOT = ROOT / ".local-devtools" / "phase5"
CLONE = LOCAL_ROOT / "cli-anything"
VENV = LOCAL_ROOT / "venv"
TOOLS_ROOT = Path.home() / "Documents" / "VelvetPrintLab" / "tools"
FREECAD_NAME = "FreeCAD_1.1.3-Windows-x86_64-py311"
FREECAD_ROOT = TOOLS_ROOT / FREECAD_NAME
FREECAD_CMD = FREECAD_ROOT / "FreeCADCmd.exe"
FREECAD_ARCHIVE = TOOLS_ROOT / f"{FREECAD_NAME}.7z"
FREECAD_URL = (
    "https://github.com/FreeCAD/FreeCAD/releases/download/1.1.3/"
    "FreeCAD_1.1.3-Windows-x86_64-py311.7z"
)
FREECAD_SHA256 = "9c6959dc9c4dba64dd818a62447e3dfedb4221d776fb044b239d462f150bcec4"
GIT_FETCH_TIMEOUT_SECONDS = 120


def run(args: list[str], *, cwd: Path | None = None, check: bool = True,
        env: dict[str, str] | None = None, user_args: list[str] | None = None,
        revisions: list[str] | None = None) -> subprocess.CompletedProcess:
    if args and args[0] == "git":
        if env is not None:
            raise SystemExit("FAIL git spawn refuses a caller environment")
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
    else:
        proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, env=env)
    if check and proc.returncode:
        raise SystemExit(
            f"FAIL {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def remove_tree(path: Path) -> None:
    def clear_readonly(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=clear_readonly)


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))


def validate_cost_preflights(registry: dict) -> None:
    rels = [
        registry["cost_preflight"],
        registry["freecad"]["cost_preflight"],
    ]
    for rel in rels:
        run([
            sys.executable,
            str(ROOT / "scripts" / "vf_cost_preflight.py"),
            "validate",
            str(ROOT / rel),
        ], cwd=ROOT)
        print(f"OK cost preflight {rel}")


def ensure_clone(registry: dict) -> None:
    pin = registry["pin"]
    if (CLONE / ".git").is_dir():
        head = run(["git", "rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=CLONE).stdout.strip()
        if head != pin:
            remove_tree(CLONE)
    if not (CLONE / ".git").is_dir():
        CLONE.parent.mkdir(parents=True, exist_ok=True)
        CLONE.mkdir(parents=True, exist_ok=True)
        run(["git", "init", "-q"], cwd=CLONE)
        run(["git", "remote", "add", "origin"], user_args=[registry["source"]], cwd=CLONE)
        run(["git", "fetch", "-q", "--depth", "1", "origin"], user_args=[pin], cwd=CLONE)
        run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=CLONE)
    head = run(["git", "rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=CLONE).stdout.strip()
    if head != pin:
        raise SystemExit(f"FAIL CLI-Anything pin mismatch: {head}")
    print(f"OK CLI-Anything source {head[:12]}")
def overlay_applied() -> bool:
    return run(
        ["git", "apply", "--unidiff-zero", "--reverse", "--check"],
        user_args=[str(PATCH_PATH)],
        cwd=CLONE,
        check=False,
    ).returncode == 0


def apply_overlay() -> None:
    if overlay_applied():
        print("OK FreeCAD boolean/export overlay already applied")
        return
    dirty = run(["git", "status", "--porcelain"], cwd=CLONE).stdout.strip()
    if dirty:
        raise SystemExit(
            "FAIL CLI-Anything clone has unexpected local changes; "
            "refusing to overwrite before overlay"
        )
    check = run(
        ["git", "apply", "--unidiff-zero", "--check"],
        user_args=[str(PATCH_PATH)],
        cwd=CLONE,
        check=False,
    )
    if check.returncode:
        raise SystemExit(f"FAIL overlay no longer applies:\n{check.stderr}")
    run(["git", "apply", "--unidiff-zero"], user_args=[str(PATCH_PATH)], cwd=CLONE)
    if not overlay_applied():
        raise SystemExit("FAIL overlay applied but reverse check did not pass")
    print("OK FreeCAD boolean/export overlay applied")


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_venv() -> None:
    py = venv_python()
    if not py.is_file():
        VENV.parent.mkdir(parents=True, exist_ok=True)
        run([sys.executable, "-m", "venv", str(VENV)])
    packages = [
        "click==8.5.0",
        "prompt-toolkit==3.0.53",
        "pytest==9.1.1",
        "Pillow==12.3.0",
    ]
    run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check",
         "--no-input", *packages])
    harness = CLONE / "freecad" / "agent-harness"
    run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check",
         "--no-input", "--no-deps", "-e", str(harness)])
    run([str(py), "-m", "pip", "check"])
    print("OK isolated CLI-Anything FreeCAD venv")
def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_freecad() -> None:
    TOOLS_ROOT.mkdir(parents=True, exist_ok=True)
    part = FREECAD_ARCHIVE.with_suffix(FREECAD_ARCHIVE.suffix + ".part")
    with urllib.request.urlopen(FREECAD_URL) as response, part.open("wb") as out:
        shutil.copyfileobj(response, out)
    actual = file_sha256(part)
    if actual != FREECAD_SHA256:
        part.unlink(missing_ok=True)
        raise SystemExit(f"FAIL FreeCAD SHA256 mismatch: {actual}")
    part.replace(FREECAD_ARCHIVE)
    print(f"OK downloaded FreeCAD archive sha256={actual}")


def ensure_freecad() -> None:
    if FREECAD_CMD.is_file():
        version = run([str(FREECAD_CMD), "--version"]).stdout.strip()
        if "FreeCAD 1.1.3" not in version:
            raise SystemExit(f"FAIL unexpected FreeCAD version: {version}")
        print(f"OK {version}")
        return
    if not FREECAD_ARCHIVE.is_file() or file_sha256(FREECAD_ARCHIVE) != FREECAD_SHA256:
        download_freecad()
    else:
        print("OK existing FreeCAD archive hash")
    run(["tar", "-xf", str(FREECAD_ARCHIVE)], cwd=TOOLS_ROOT)
    if not FREECAD_CMD.is_file():
        raise SystemExit(f"FAIL FreeCADCmd missing after extraction: {FREECAD_CMD}")
    version = run([str(FREECAD_CMD), "--version"]).stdout.strip()
    if "FreeCAD 1.1.3" not in version:
        raise SystemExit(f"FAIL unexpected FreeCAD version: {version}")
    print(f"OK {version}")
def uninstall(remove_freecad: bool) -> None:
    if CLONE.exists():
        remove_tree(CLONE)
        print(f"OK removed {CLONE}")
    if VENV.exists():
        remove_tree(VENV)
        print(f"OK removed {VENV}")
    if remove_freecad and FREECAD_ROOT.exists():
        remove_tree(FREECAD_ROOT)
        print(f"OK removed {FREECAD_ROOT}")
    if remove_freecad and FREECAD_ARCHIVE.exists():
        FREECAD_ARCHIVE.unlink()
        print(f"OK removed {FREECAD_ARCHIVE}")


def prove_git_hygiene() -> list[str]:
    """Git is absolute and allowlisted. Other tools keep their own spawn."""
    import vf_spawn

    errors: list[str] = []
    previous = {
        "VF_SPAWN_SENTINEL": os.environ.get("VF_SPAWN_SENTINEL"),
        "GIT_EXEC_PATH": os.environ.get("GIT_EXEC_PATH"),
        "GIT_CONFIG_COUNT": os.environ.get("GIT_CONFIG_COUNT"),
    }
    os.environ["VF_SPAWN_SENTINEL"] = "nope"
    os.environ["GIT_EXEC_PATH"] = "/evil/git-core"
    os.environ["GIT_CONFIG_COUNT"] = "1"
    captured: list[tuple[list[str], dict]] = []
    original = vf_spawn.subprocess.run

    def fake_run(argv, **kwargs):
        captured.append((list(argv), kwargs))
        return vf_spawn.subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    vf_spawn.subprocess.run = fake_run
    try:
        run(["git", "status"], cwd=ROOT, check=False)
        run(
            ["git", "fetch", "-q", "--depth", "1", "origin"],
            user_args=["pin"],
            cwd=ROOT,
            check=False,
        )
        run([sys.executable, "-c", "print(1)"], check=False)
        try:
            run(["git", "status"], env={"PATH": "/evil"}, check=False)
        except SystemExit:
            pass
        else:
            errors.append("git accepted a caller environment")
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
                run(
                    ["git", "rev-parse", "--verify", "-q"],
                    revisions=[token],
                    cwd=ROOT,
                    check=False,
                )
            except SystemExit as exc:
                if "GIT_REV_REFUSED" not in str(exc):
                    errors.append(f"{label} revision refused as {exc}")
            else:
                errors.append(f"{label} revision was accepted")
        if len(captured) != before:
            errors.append("control-byte revision spawned git")
        held = len(captured)
        for label, caller, code in (
            ("empty argv", lambda: run(["git", ""], check=False), "GIT_ARGV_REFUSED"),
            ("non-string argv", lambda: run(["git", "status", None], check=False), "GIT_ARGV_REFUSED"),
            (
                "empty user arg",
                lambda: run(["git", "status"], user_args=[""], check=False),
                "GIT_USER_ARG_REFUSED",
            ),
            (
                "non-string user arg",
                lambda: run(["git", "status"], user_args=[None], check=False),
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
    finally:
        vf_spawn.subprocess.run = original
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    if errors:
        return errors
    if len(captured) != 3:
        return [f"expected 3 spawns, saw {len(captured)}"]
    errors.extend(allowlisted_git_errors(captured[0][0], captured[0][1], timeout=GIT_TIMEOUT_SECONDS))
    errors.extend(
        allowlisted_git_errors(captured[1][0], captured[1][1], timeout=GIT_FETCH_TIMEOUT_SECONDS)
    )
    errors.extend(user_arg_separator_errors(captured[1][0], ["pin"]))
    other_argv, other_kwargs = captured[2]
    if not other_argv or other_argv[0] != sys.executable:
        errors.append(f"non-git command was rewritten: {other_argv}")
    if other_kwargs.get("timeout") is not None or other_kwargs.get("env") is not None:
        errors.append("non-git command was forced through the git allowlist")
    errors.extend(windows_pin_case_errors())
    return errors


def prove_git_real() -> list[str]:
    """A real git remote add. ``--`` keeps a dash-leading url from being an option."""
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        try:
            run(["git", "init", "-q", "-b", "main"], cwd=repo)
            run(
                ["git", "remote", "add", "origin"],
                user_args=["--upload-pack=not-an-option"],
                cwd=repo,
            )
            url = run(
                ["git", "remote", "get-url"],
                user_args=["origin"],
                cwd=repo,
            ).stdout.strip()
        except SystemExit as exc:
            return [f"real git remote add failed: {exc}"]
    if url != "--upload-pack=not-an-option":
        errors.append(f"user url was parsed as a git option: {url!r}")
    return errors


def _bare_commit(root: Path) -> tuple[Path, str, Path, Path]:
    """Local bare repo plus an upload-pack script that would write a marker."""
    wt = root / "wt"
    wt.mkdir()
    run(["git", "init", "-q", "-b", "main"], cwd=wt)
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=wt)
    run(["git", "config", "user.name", "fixture"], cwd=wt)
    (wt / "f").write_text("hi\n", encoding="utf-8")
    run(["git", "add"], user_args=["f"], cwd=wt)
    run(["git", "commit", "-qm", "c"], cwd=wt)
    sha = run(
        ["git", "rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=wt
    ).stdout.strip()
    bare = root / "bare.git"
    run(["git", "clone", "--bare", "-q"], user_args=[str(wt), str(bare)])
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
    """The real ensure_clone path, not only the fixture run() calls."""
    global CLONE
    errors: list[str] = []
    previous = CLONE
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            bare, sha, script, marker = _bare_commit(root)
        except SystemExit as exc:
            return [f"bare repo setup failed: {exc}"]
        hostile = f"--upload-pack={script}"

        def check_out(name: str, source: str, pin: str) -> SystemExit | None:
            global CLONE
            CLONE = root / name
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    ensure_clone({"pin": pin, "source": source})
            except SystemExit as exc:
                return exc
            return None

        try:
            failed = check_out("src", str(bare), sha)
            if failed is not None:
                errors.append(f"ensure_clone did not fetch the bare repo: {failed}")
            else:
                head = run(
                    ["git", "rev-parse", "--verify", "-q"],
                    revisions=["HEAD"],
                    cwd=root / "src",
                ).stdout.strip()
                if head != sha:
                    errors.append(f"ensure_clone checked out {head!r}, not {sha}")
            marker.unlink(missing_ok=True)
            failed = check_out("hostile-source", hostile, sha)
            if failed is None:
                errors.append("hostile source fetch succeeded")
            if marker.exists():
                errors.append("hostile source executed upload-pack")
            try:
                url = run(
                    ["git", "remote", "get-url"],
                    user_args=["origin"],
                    cwd=root / "hostile-source",
                ).stdout.strip()
            except SystemExit as exc:
                errors.append(f"hostile source was not stored after --: {exc}")
            else:
                if url != hostile:
                    errors.append(f"source was parsed as a git option: {url!r}")
            marker.unlink(missing_ok=True)
            failed = check_out("hostile-pin", str(bare), hostile)
            if failed is None:
                errors.append("hostile pin fetch succeeded")
            if marker.exists():
                errors.append("hostile pin executed upload-pack")
        finally:
            CLONE = previous
    return errors


def prove_ensure_clone_rev_parse() -> list[str]:
    """Both ensure_clone HEAD reads keep the revision immediately before --."""
    import vf_spawn

    global CLONE
    errors: list[str] = []
    previous = CLONE
    sha = "a" * 40
    captured: list[list[str]] = []
    original = vf_spawn.subprocess.run

    def fake_run(argv, **kwargs):
        captured.append(list(argv))
        return vf_spawn.subprocess.CompletedProcess(argv, 0, stdout=sha + "\n", stderr="")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "clone"
        (root / ".git").mkdir(parents=True)
        CLONE = root
        vf_spawn.subprocess.run = fake_run
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                ensure_clone({"pin": sha, "source": "unused"})
        except SystemExit as exc:
            errors.append(f"ensure_clone rev-parse fixture exited: {exc}")
        finally:
            vf_spawn.subprocess.run = original
            CLONE = previous
    parses = [argv for argv in captured if "rev-parse" in argv]
    if len(parses) != 2:
        return errors + [f"ensure_clone rev-parse count {len(parses)}: {captured}"]
    for argv in parses:
        errors.extend(revision_form_errors(argv, ["HEAD"]))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--remove-freecad", action="store_true")
    args = parser.parse_args()

    if args.uninstall:
        uninstall(args.remove_freecad)
        return

    registry = load_registry()
    validate_cost_preflights(registry)
    ensure_clone(registry)
    apply_overlay()
    ensure_venv()
    ensure_freecad()
    print("OK CLI-Anything FreeCAD pilot setup cost=0 gui-preview=disabled")


if __name__ == "__main__":
    main()
