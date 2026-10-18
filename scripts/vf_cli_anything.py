#!/usr/bin/env python3
"""VelvetOS adapter for the pinned, headless CLI-Anything FreeCAD pilot."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
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
CLONE = ROOT / ".local-devtools" / "phase5" / "cli-anything"
VENV = ROOT / ".local-devtools" / "phase5" / "venv"
VENV_SCRIPTS = VENV / ("Scripts" if os.name == "nt" else "bin")
CLI = VENV_SCRIPTS / ("cli-anything-freecad.exe" if os.name == "nt" else "cli-anything-freecad")
FREECAD_ROOT = (
    Path.home() / "Documents" / "VelvetPrintLab" / "tools"
    / "FreeCAD_1.1.3-Windows-x86_64-py311"
)
FREECAD_CMD = FREECAD_ROOT / "FreeCADCmd.exe"
BLOCKED_GROUPS = {"preview", "motion", "repl"}


def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))


def run(args: list[str], *, cwd: Path | None = None,
        env: dict[str, str] | None = None, user_args: list[str] | None = None,
        revisions: list[str] | None = None) -> subprocess.CompletedProcess:
    if args and args[0] == "git":
        if env is not None:
            raise SystemExit("FAIL git spawn refuses a caller environment")
        try:
            return run_git(
                list(args[1:]),
                cwd=cwd,
                check=False,
                timeout=GIT_TIMEOUT_SECONDS,
                user_args=user_args,
                revisions=revisions,
            )
        except SpawnRefusal as exc:
            raise SystemExit(f"FAIL git spawn: {exc}") from exc
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)


def detect_group(args: list[str]) -> str | None:
    index = 0
    while index < len(args):
        token = args[index]
        if token in {"--json", "--dry-run"}:
            index += 1
            continue
        if token in {"-p", "--project"}:
            index += 2
            continue
        if token.startswith("--project="):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token
    return None
def tool_env() -> dict[str, str]:
    env = os.environ.copy()
    env["FREECAD_PATH"] = str(FREECAD_CMD)
    env["CLI_ANYTHING_FORCE_INSTALLED"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PATH"] = os.pathsep.join(
        [str(VENV_SCRIPTS), str(FREECAD_ROOT), env.get("PATH", "")]
    )
    return env


def doctor(patch_name: str | None = None) -> int:
    data = registry()
    issues: list[str] = []
    head = ""
    if (CLONE / ".git").is_dir():
        try:
            proc = run(
                ["git", "rev-parse", "--verify", "-q"],
                revisions=["HEAD"],
                cwd=CLONE,
            )
        except SystemExit as exc:
            issues.append(str(exc))
        else:
            head = proc.stdout.strip()
            if proc.returncode or head != data["pin"]:
                issues.append(f"CLI-Anything pin mismatch: {head or 'unreadable'}")
    else:
        issues.append("CLI-Anything local clone missing")

    if not CLI.is_file():
        issues.append(f"FreeCAD CLI entry point missing: {CLI}")
    if not FREECAD_CMD.is_file():
        issues.append(f"FreeCADCmd missing: {FREECAD_CMD}")

    freecad_version = ""
    if FREECAD_CMD.is_file():
        proc = run([str(FREECAD_CMD), "--version"])
        freecad_version = proc.stdout.strip()
        if proc.returncode or "FreeCAD 1.1.3" not in freecad_version:
            issues.append(f"Unexpected FreeCAD version: {freecad_version}")

    patch_ok = False
    overlay_patch = ""
    if (CLONE / ".git").is_dir():
        overlay_patch = patch_name if patch_name is not None else str(ROOT / data["overlay"])
        try:
            applied = run(
                ["git", "apply", "--unidiff-zero", "--reverse", "--check"],
                user_args=[overlay_patch],
                cwd=CLONE,
            )
        except SystemExit as exc:
            issues.append(str(exc))
        else:
            blob = applied.stdout + applied.stderr
            if "unknown option" in blob or "unrecognized option" in blob:
                issues.append("overlay path was parsed as a git option")
            patch_ok = applied.returncode == 0
            if not patch_ok:
                issues.append("FreeCAD boolean/export overlay is not applied")

    payload = {
        "status": "PASS" if not issues else "BLOCKED",
        "cli_anything_pin": head,
        "freecad_version": freecad_version,
        "overlay_applied": patch_ok,
        "overlay_patch": overlay_patch,
        "blocked_groups": sorted(BLOCKED_GROUPS),
        "canonical_cad_route": data["authority"]["canonical_cad_route"],
        "slicer_authority": "scripts/vf_cad.py + VelvetPrintLab printer_matrix.json",
        "printer_control": False,
        "incremental_recurring_cost_ils": 0,
        "issues": issues,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not issues else 2
def freecad(args: list[str]) -> int:
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        args = ["--help"]

    group = detect_group(args)
    if group in BLOCKED_GROUPS:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": f"CLI-Anything FreeCAD group '{group}' is disabled by VelvetOS scope",
            "allowed_route": "headless structured CAD; use other visual tools only when GUI automation is actually required",
        }, indent=2), file=sys.stderr)
        return 2

    if not CLI.is_file() or not FREECAD_CMD.is_file():
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "CLI-Anything pilot is not installed",
            "repair": "python scripts/setup-cli-anything-pilot.py",
        }, indent=2), file=sys.stderr)
        return 2

    call_args = list(args)
    if "--help" not in call_args and "-h" not in call_args and "--json" not in call_args:
        call_args.insert(0, "--json")
    proc = subprocess.run([str(CLI), *call_args], env=tool_env(), text=True)
    return proc.returncode


def prove_git_hygiene() -> list[str]:
    """Doctor git is absolute, timed, and allowlisted. Other commands stay put."""
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
        rev = run(["git", "rev-parse", "--verify", "-q"], revisions=["HEAD"], cwd=ROOT)
        applied = run(
            ["git", "apply", "--unidiff-zero", "--reverse", "--check"],
            user_args=["--overlay.patch"],
            cwd=ROOT,
        )
        run([sys.executable, "-V"])
        before = len(captured)
        try:
            run(["git", "status"], env={"PATH": "/evil"})
        except SystemExit as exc:
            if "refuses a caller environment" not in str(exc):
                errors.append(f"caller env refused as {exc}")
        else:
            errors.append("git accepted a caller environment")
        if len(captured) != before:
            errors.append("caller env spawned git")
    except (SpawnRefusal, SystemExit) as exc:
        errors.append(f"git spawn refused: {exc}")
        rev = applied = None
    finally:
        vf_spawn.subprocess.run = original
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    if errors:
        return errors
    if rev is None or applied is None or rev.stdout.strip() != "abc" or len(captured) != 3:
        return [f"git spawn did not return captured output: {captured!r}"]
    errors.extend(allowlisted_git_errors(captured[0][0], captured[0][1], timeout=GIT_TIMEOUT_SECONDS))
    errors.extend(allowlisted_git_errors(captured[1][0], captured[1][1], timeout=GIT_TIMEOUT_SECONDS))
    for index in (0, 1):
        if captured[index][1].get("stdin") is not subprocess.DEVNULL:
            errors.append("git stdin was not closed")
    errors.extend(revision_form_errors(captured[0][0], ["HEAD"]))
    errors.extend(user_arg_separator_errors(captured[1][0], ["--overlay.patch"]))
    other_argv, other_kwargs = captured[2]
    if not other_argv or other_argv[0] != sys.executable:
        errors.append(f"non-git command was rewritten: {other_argv}")
    if other_kwargs.get("timeout") is not None or other_kwargs.get("env") is not None:
        errors.append("non-git command was forced through the git allowlist")
    if other_kwargs.get("stdin") is subprocess.DEVNULL:
        errors.append("non-git stdin was closed")
    errors.extend(windows_pin_case_errors())
    return errors


def prove_apply_stdin() -> list[str]:
    """``git apply --check`` with no path fails while stdin stays an open pipe.

    ``communicate()`` would close that pipe. CI's closed stdin hides the hang,
    so the parent only ``wait()``s.
    """
    script = (
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from vf_spawn import run_git\n"
        "repo = Path(sys.argv[2])\n"
        "try:\n"
        "    proc = run_git(['apply', '--check'], cwd=repo, timeout=3)\n"
        "except Exception as exc:\n"
        "    sys.stderr.write(f'apply --check raised {type(exc).__name__}: {exc}\\n')\n"
        "    raise SystemExit(1)\n"
        "blob = (proc.stderr or '') + (proc.stdout or '')\n"
        "if proc.returncode == 0 or 'valid patches' not in blob.lower():\n"
        "    sys.stderr.write(f'apply --check did not fail closed: rc={proc.returncode} {blob!r}\\n')\n"
        "    raise SystemExit(1)\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        init = subprocess.run(
            ["git", "init", "-q", "-b", "main"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if init.returncode:
            return [f"stdin fixture repo failed: {init.stderr}"]
        child_path = Path(tmp) / "child.py"
        child_path.write_text(script, encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, str(child_path), str(ROOT / "scripts"), str(repo)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            rc = proc.wait(timeout=12)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            return ["git apply --check hung on an open stdin pipe"]
        text = b""
        if proc.stdout is not None:
            text += proc.stdout.read()
        if proc.stderr is not None:
            text += proc.stderr.read()
        decoded = text.decode("utf-8", "replace")
        if rc != 0 or "Traceback" in decoded:
            return [f"git apply --check did not fail closed on an open pipe: rc={rc} {decoded.strip()}"]
    return []


def prove_git_real() -> list[str]:
    """doctor() uses patch_name, including a dash-leading path that reverse-checks."""
    global CLONE
    errors: list[str] = list(prove_apply_stdin())
    previous = CLONE
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        try:
            run(["git", "init", "-q", "-b", "main"], cwd=repo)
            run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repo)
            run(["git", "config", "user.name", "fixture"], cwd=repo)
            target = repo / "f"
            target.write_text("hi\n", encoding="utf-8")
            run(["git", "add"], user_args=["f"], cwd=repo)
            run(["git", "commit", "-qm", "c"], cwd=repo)
            target.write_text("hi\nyo\n", encoding="utf-8")
            diff = run(["git", "diff"], user_args=["f"], cwd=repo)
        except SystemExit as exc:
            return errors + [f"repo setup failed: {exc}"]
        if diff.returncode or not diff.stdout.startswith("diff --git"):
            return errors + [f"fixture patch was not a diff: rc={diff.returncode} {diff.stderr}"]
        (repo / "--overlay.patch").write_text(diff.stdout, encoding="utf-8")
        CLONE = repo
        try:
            import contextlib
            import io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                doctor(patch_name="--overlay.patch")
        finally:
            CLONE = previous
        raw = buf.getvalue()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return errors + [f"doctor did not return JSON: {exc}"]
    issues = payload.get("issues") or []
    joined = "\n".join(str(item) for item in issues)
    if payload.get("overlay_patch") != "--overlay.patch":
        errors.append(f"doctor ignored patch_name: {payload.get('overlay_patch')!r}")
    if payload.get("overlay_applied") is not True:
        errors.append(f"doctor did not apply patch_name: {issues}")
    if "overlay path was parsed as a git option" in joined or "unknown option" in joined:
        errors.append("overlay path was parsed as a git option")
    if not any(
        len(part) == 40 and all(char in "0123456789abcdef" for char in part)
        for item in issues
        for part in str(item).split()
    ):
        errors.append(f"doctor did not read HEAD: {issues}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    fc = sub.add_parser("freecad")
    fc.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor()
    if args.command == "freecad":
        return freecad(args.args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
