#!/usr/bin/env python3
"""Fail-closed spawn helpers for absolute tools and allowlisted environments.

Does not replace the git runner in check-all.py or the gh spawns claimed by
subprocess hygiene slice 2. Stage 8 generators stay on their historical
policy-manifest hashes.
"""
from __future__ import annotations

import os
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

GIT_TIMEOUT_SECONDS = 30
_AMBIENT_ENV_KEYS = (
    "SYSTEMROOT",
    "SystemRoot",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
)
_BASE_ENV_KEYS = _AMBIENT_ENV_KEYS
FORCED_ENV_KEYS = (
    "HOME",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "XDG_CONFIG_HOME",
    "XDG_CONFIG_DIRS",
    "TEMP",
    "TMP",
    "TMPDIR",
    "GIT_CONFIG_NOSYSTEM",
)
_LOCKED_EXTRA_KEYS = {key.upper() for key in FORCED_ENV_KEYS}
_home_dir: str | None = None
_temp_dir: str | None = None


class SpawnRefusal(RuntimeError):
    """A spawn was not an absolute tool with an allowlisted environment."""


def executable_is_absolute(path: str) -> bool:
    if os.path.isabs(path):
        return True
    return len(path) >= 3 and path[0].isalpha() and path[1] == ":" and path[2] in "\\/"


def same_pinned_directory(
    actual: str,
    expected: str,
    *,
    realpath=os.path.realpath,
    fold_case: bool | None = None,
    separator: str | None = None,
) -> bool:
    """True when both strings are one directory and name the same real path.

    A search PATH is not a pin. Windows compares case-insensitively.
    realpath expands an 8.3 temp directory to its long name.
    """
    if fold_case is None:
        fold_case = os.name == "nt"
    if separator is None:
        separator = os.pathsep
    if not isinstance(actual, str) or not isinstance(expected, str):
        return False
    if not actual or not expected:
        return False
    if separator in actual or separator in expected:
        return False
    left = realpath(actual)
    right = realpath(expected)
    if fold_case:
        left = os.path.normcase(left).casefold()
        right = os.path.normcase(right).casefold()
    return left == right


def _lookup_git() -> str:
    """The git executable visible when this process started."""
    found = shutil.which("git")
    if not found or not executable_is_absolute(found):
        return ""
    try:
        resolved = os.path.realpath(found)
    except OSError:
        return ""
    if not executable_is_absolute(resolved):
        return ""
    return resolved


PINNED_GIT = _lookup_git()
_GIT_BASENAMES = {"git", "git.exe"}


def names_git_tool(token: str) -> bool:
    """True for ``git``, ``git.exe``, and any absolute path with that basename."""
    if not isinstance(token, str) or not token.strip() or token.startswith("-"):
        return False
    return Path(token).name.casefold() in _GIT_BASENAMES


def git_pin_matches(resolved: str) -> bool:
    """True when ``resolved`` is the process-start git, not a later PATH entry."""
    if not PINNED_GIT or not isinstance(resolved, str) or not resolved:
        return False
    return same_pinned_directory(resolved, PINNED_GIT)


def require_pinned_git(token: str) -> None:
    """Refuse an absolute git path that is not the process-start executable."""
    if not executable_is_absolute(token):
        raise SpawnRefusal("GIT_PIN_REFUSED")
    try:
        resolved = os.path.realpath(token)
    except OSError as exc:
        raise SpawnRefusal("GIT_PIN_REFUSED") from exc
    if not git_pin_matches(resolved):
        raise SpawnRefusal("GIT_PIN_REFUSED")


def join_tool_path(dirs: list[str]) -> str:
    """Join absolute tool directories. A copied search PATH is refused."""
    cleaned: list[str] = []
    for entry in dirs:
        if not isinstance(entry, str) or not entry or os.pathsep in entry:
            raise SpawnRefusal("SPAWN_PATH_REFUSED")
        if not executable_is_absolute(entry):
            raise SpawnRefusal("SPAWN_PATH_REFUSED")
        resolved = str(Path(entry).resolve())
        if resolved not in cleaned:
            cleaned.append(resolved)
    if not cleaned:
        raise SpawnRefusal("SPAWN_PATH_REFUSED")
    return os.pathsep.join(cleaned)


def resolve_executable(name_or_path: str) -> str:
    """Return one absolute executable.

    ``git`` must be the executable recorded at process start. A later PATH
    entry, or an absolute path to a different file, is refused.
    """
    if not isinstance(name_or_path, str) or not name_or_path.strip():
        raise SpawnRefusal("SPAWN_ARGV_REFUSED")
    if name_or_path.startswith("-"):
        raise SpawnRefusal("SPAWN_ARGV_REFUSED")
    candidate = name_or_path
    if not executable_is_absolute(candidate):
        found = shutil.which(candidate)
        if not found or not executable_is_absolute(found):
            raise SpawnRefusal("SPAWN_PATH_LOOKUP_REFUSED")
        candidate = found
    resolved = str(Path(candidate).resolve())
    if not executable_is_absolute(resolved):
        raise SpawnRefusal("SPAWN_PATH_LOOKUP_REFUSED")
    if names_git_tool(name_or_path) or names_git_tool(resolved):
        if not git_pin_matches(resolved):
            raise SpawnRefusal("GIT_PIN_REFUSED")
    return resolved


def pinned_path(executable: str) -> str:
    """PATH for one tool. Windows git also gets its sibling tool directories."""
    parent = Path(executable).resolve().parent
    entries = [parent]
    if os.name == "nt" and parent.name.lower() in {"cmd", "bin"} and parent.parent.name.lower() == "git":
        for parts in (("..", "bin"), ("..", "usr", "bin"), ("..", "mingw64", "bin")):
            candidate = (parent.joinpath(*parts)).resolve()
            if candidate.is_dir() and candidate not in entries:
                entries.append(candidate)
    return os.pathsep.join(str(entry) for entry in entries)


def _fixed_trusted_roots() -> list[Path]:
    """Temp roots that do not come from TMPDIR, TEMP, TMP, or tempfile.tempdir."""
    if os.name == "nt":
        system = _system_root()
        return [Path(system) / "Temp"] if system else []
    return [Path("/tmp"), Path("/var/tmp")]


def _trusted_dir(path: Path) -> bool:
    """A spawn root is a real directory. A symlink is refused."""
    try:
        info = path.lstat()
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        return False
    if os.name == "nt":
        return True
    return info.st_uid == 0 and bool(info.st_mode & stat.S_ISVTX)


def _spawn_root() -> Path:
    for root in _fixed_trusted_roots():
        if _trusted_dir(root):
            return root
    raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")


def _under_fixed_root(path: Path) -> bool:
    parent = path.parent
    for root in _fixed_trusted_roots():
        if os.name == "nt":
            if os.path.normcase(str(parent)) == os.path.normcase(str(root)):
                return True
        elif parent == root:
            return True
    return False


def _private_dir(prefix: str, *, readonly: bool) -> str:
    """Create one owner-only directory under the fixed root. Never uses TMPDIR."""
    root = _spawn_root()
    last_error: Exception | None = None
    for _ in range(8):
        path = root / f"{prefix}{secrets.token_hex(8)}"
        try:
            os.mkdir(path, 0o700)
        except FileExistsError:
            continue
        except OSError as exc:
            last_error = exc
            continue
        info = path.lstat()
        if (
            stat.S_ISLNK(info.st_mode)
            or not stat.S_ISDIR(info.st_mode)
            or not _under_fixed_root(path)
            or (os.name != "nt" and info.st_uid != os.getuid())
        ):
            raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")
        if os.name != "nt":
            os.chmod(path, 0o500 if readonly else 0o700)
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")
        if os.name != "nt" and readonly and mode & 0o222:
            raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")
        if os.name != "nt" and not readonly and mode & 0o077:
            raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")
        return str(path)
    raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED") from last_error


def _home_is_clean(path: str) -> bool:
    """True when this home is still an empty, non-writable directory we created."""
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        return False
    if not _under_fixed_root(Path(path)):
        return False
    if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o222:
        return False
    try:
        if any(Path(path).iterdir()):
            return False
    except OSError:
        return False
    return True


def _temp_is_clean(path: str) -> bool:
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        return False
    if not _under_fixed_root(Path(path)):
        return False
    if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
        return False
    return True


def controlled_home() -> str:
    """Empty read-only directory used as HOME. Replaced when it is no longer clean."""
    global _home_dir
    if _home_dir is None or not _home_is_clean(_home_dir):
        _home_dir = _private_dir("vf-spawn-home-", readonly=True)
    return _home_dir


def controlled_temp() -> str:
    """Private temp directory under the fixed root. Inherited TEMP, TMP, and TMPDIR are not copied."""
    global _temp_dir
    if _temp_dir is None or not _temp_is_clean(_temp_dir):
        _temp_dir = _private_dir("vf-spawn-tmp-", readonly=False)
    return _temp_dir


def _system_root() -> str:
    for key in ("SYSTEMROOT", "SystemRoot"):
        value = os.environ.get(key)
        if isinstance(value, str) and value and executable_is_absolute(value):
            try:
                return str(Path(value).resolve())
            except OSError:
                continue
    return ""


def _comspec_is_trusted(value: str, system_root: str) -> bool:
    if not system_root or not value:
        return False
    try:
        resolved = str(Path(value).resolve())
    except OSError:
        return False
    return resolved == system_root or resolved.startswith(system_root + os.sep)


def allowlisted_env(executable: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    """Copy a fixed key list, pin PATH, and replace home and temp.

    GIT_* and NODE_OPTIONS are never copied. This function sets
    GIT_CONFIG_NOSYSTEM=1 itself. HOME, USERPROFILE, HOMEDRIVE, HOMEPATH,
    XDG_CONFIG_HOME, XDG_CONFIG_DIRS, TEMP, TMP, and TMPDIR come from a
    controlled directory, not from the caller. extra cannot replace those,
    PATH, or smuggle GIT_* / NODE_OPTIONS back in. COMSPEC is copied only
    when it resolves inside SYSTEMROOT.
    """
    env: dict[str, str] = {}
    system_root = _system_root()
    for key in _AMBIENT_ENV_KEYS:
        upper = key.upper()
        if upper.startswith("GIT_") or upper == "NODE_OPTIONS":
            continue
        value = os.environ.get(key)
        if not value:
            continue
        if upper == "COMSPEC" and not _comspec_is_trusted(value, system_root):
            continue
        env[key] = value
    if extra:
        for key, value in extra.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise SpawnRefusal("SPAWN_ENV_REFUSED")
            upper = key.upper()
            if (
                upper.startswith("GIT_")
                or upper == "NODE_OPTIONS"
                or upper == "PATH"
                or upper in _LOCKED_EXTRA_KEYS
            ):
                raise SpawnRefusal("SPAWN_ENV_REFUSED")
            env[key] = value
    home = controlled_home()
    temp = controlled_temp()
    drive, tail = os.path.splitdrive(home)
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["HOMEDRIVE"] = drive
    env["HOMEPATH"] = tail or home
    env["XDG_CONFIG_HOME"] = home
    env["XDG_CONFIG_DIRS"] = home
    env["TEMP"] = temp
    env["TMP"] = temp
    env["TMPDIR"] = temp
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["PATH"] = pinned_path(executable)
    return env


def run_tool(
    argv: list[str],
    *,
    timeout: float,
    extra_env: dict[str, str] | None = None,
    cwd: Path | str | None = None,
    check: bool = False,
    input: str | None = None,
    path_dirs: list[str] | None = None,
    close_stdin: bool = False,
) -> subprocess.CompletedProcess[str]:
    if not argv or not isinstance(argv[0], str):
        raise SpawnRefusal("SPAWN_ARGV_REFUSED")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise SpawnRefusal("SPAWN_TIMEOUT_REFUSED")
    executable = resolve_executable(argv[0])
    env = allowlisted_env(executable, extra_env)
    if path_dirs is not None:
        env["PATH"] = join_tool_path([str(Path(executable).resolve().parent), *path_dirs])
    call: dict = {
        "cwd": cwd,
        "env": env,
        "timeout": timeout,
        "check": check,
        "capture_output": True,
        "text": True,
    }
    if input is None and close_stdin:
        call["stdin"] = subprocess.DEVNULL
    elif input is not None:
        call["input"] = input
    return subprocess.run([executable, *argv[1:]], **call)


def git_revision(token: str) -> str:
    """A revision git must see before ``--``.

    Git reads tokens after ``--`` as paths, not revisions. A leading dash is
    an option, and a newline, CR, or NUL is an argument break, so both are
    refused before git runs.
    """
    if (
        not isinstance(token, str)
        or not token
        or token.startswith("-")
        or any(char in token for char in "\n\r\x00")
    ):
        raise SpawnRefusal("GIT_REV_REFUSED")
    return token


def run_git(
    args: list[str],
    *,
    cwd: Path | str | None = None,
    check: bool = False,
    timeout: float = GIT_TIMEOUT_SECONDS,
    input: str | None = None,
    user_args: list[str] | None = None,
    revisions: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Absolute git with a timeout and an allowlisted environment.

    ``user_args`` (urls, refspecs, paths) are placed after ``--`` so git does
    not parse them as options. ``revisions`` stay before ``--`` because git
    would otherwise treat them as paths; ``git_revision`` refuses a leading
    dash and a newline, CR, or NUL. With no ``input``, stdin is ``DEVNULL``
    so ``git apply --check`` cannot wait on an inherited pipe.
    """
    if any(not isinstance(arg, str) or arg == "" for arg in args):
        raise SpawnRefusal("GIT_ARGV_REFUSED")
    argv = list(args)
    if revisions:
        argv.extend(git_revision(rev) for rev in revisions)
    if user_args is not None or revisions:
        operands = [] if user_args is None else list(user_args)
        for item in operands:
            if not isinstance(item, str) or item == "":
                raise SpawnRefusal("GIT_USER_ARG_REFUSED")
        argv.append("--")
        argv.extend(operands)
    return run_tool(
        ["git", *argv],
        cwd=cwd,
        check=check,
        timeout=timeout,
        input=input,
        close_stdin=input is None,
    )


def user_arg_separator_errors(argv: list[str], user_args: list[str]) -> list[str]:
    """Errors when ``--`` is not the separator immediately before user args."""
    if len(argv) < 2 or "--" not in argv[1:]:
        return ["git missing -- before user args"]
    idx = argv.index("--")
    if argv[idx + 1:] != list(user_args):
        return [f"git -- was not before the user args: {argv}"]
    return []


def revision_form_errors(argv: list[str], revisions: list[str]) -> list[str]:
    """Errors when revisions are not the tokens immediately before ``--``."""
    if len(argv) < 2 or "--" not in argv[1:]:
        return ["git missing -- after revisions"]
    idx = argv.index("--")
    if argv[idx - len(revisions):idx] != list(revisions):
        return [f"git revisions were not directly before --: {argv}"]
    if argv[idx + 1:]:
        return [f"git revision form gained pathspecs: {argv}"]
    return []


def allowlisted_git_errors(argv: list[str], kwargs: dict, *, timeout: float) -> list[str]:
    """Errors when one captured git spawn is not the pinned git, timed, and allowlisted."""
    errors: list[str] = []
    if not argv or not executable_is_absolute(argv[0]):
        return [f"git was not absolute: {argv}"]
    try:
        resolved_git = os.path.realpath(argv[0])
    except OSError:
        return [f"git was not the pinned executable: {argv}"]
    if not git_pin_matches(resolved_git):
        return [f"git was not the pinned executable: {argv}"]
    if kwargs.get("timeout") != timeout:
        errors.append("git timeout missing")
    env = kwargs.get("env")
    git_keys = [str(key).upper() for key in (env or {}) if str(key).upper().startswith("GIT_")]
    if (
        not isinstance(env, dict)
        or "VF_SPAWN_SENTINEL" in env
        or set(git_keys) != {"GIT_CONFIG_NOSYSTEM"}
        or env.get("GIT_CONFIG_NOSYSTEM") != "1"
    ):
        return errors + ["git environment was not allowlisted"]
    home = controlled_home()
    temp = controlled_temp()
    if (
        env.get("HOME") != home
        or env.get("USERPROFILE") != home
        or env.get("XDG_CONFIG_HOME") != home
        or env.get("XDG_CONFIG_DIRS") != home
        or env.get("TEMP") != temp
        or env.get("TMP") != temp
        or env.get("TMPDIR") != temp
    ):
        errors.append("git home or temp was not the sandbox")
    parts = env.get("PATH", "").split(os.pathsep)
    first = parts[0] if parts else ""
    if not same_pinned_directory(first, str(Path(argv[0]).resolve().parent)):
        errors.append("git PATH was not the executable directory")
    install = Path(argv[0]).resolve().parent
    root = install.parent if os.name == "nt" and install.parent.name.lower() == "git" else install
    for entry in parts[1:]:
        resolved = Path(entry).resolve()
        if resolved != root and root not in resolved.parents:
            errors.append(f"git PATH escaped the install: {entry}")
    return errors


def _decoy_git_path(directory: Path) -> Path:
    name = "git.exe" if os.name == "nt" else "git"
    path = directory / name
    path.write_text("#!/bin/sh\necho decoy\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def prove_decoy_git() -> list[str]:
    """A git placed earlier on PATH, or an absolute path to it, is refused."""
    errors: list[str] = []
    if not PINNED_GIT:
        return ["pinned git is missing"]
    with tempfile.TemporaryDirectory(prefix="vf-decoy-git-") as tmp:
        decoy = _decoy_git_path(Path(tmp))
        previous = os.environ.get("PATH")
        os.environ["PATH"] = str(tmp) + os.pathsep + (previous or "")
        try:
            try:
                found = resolve_executable("git")
            except SpawnRefusal as exc:
                if "GIT_PIN_REFUSED" not in str(exc):
                    errors.append(f"decoy git refused as {exc}")
            else:
                errors.append(f"decoy git was accepted: {found}")
            try:
                found = resolve_executable(str(decoy))
            except SpawnRefusal as exc:
                if "GIT_PIN_REFUSED" not in str(exc):
                    errors.append(f"absolute decoy refused as {exc}")
            else:
                errors.append(f"absolute decoy git was accepted: {found}")
        finally:
            if previous is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = previous
    return errors


def _git_pin_matches_any(resolved: str) -> bool:
    """Mutant: any absolute path counts as the pinned git."""
    del resolved
    return True


def prove_git_identity() -> list[str]:
    """The live pin refuses a decoy, and a mutant that accepts every path is caught."""
    errors = prove_decoy_git()
    original = git_pin_matches
    globals()["git_pin_matches"] = _git_pin_matches_any
    try:
        found = prove_decoy_git()
    finally:
        globals()["git_pin_matches"] = original
    if not any("decoy git was accepted" in item or "absolute decoy git was accepted" in item for item in found):
        errors.append("decoy git mutant was not caught")
    return errors


def _left_hardened_path(argv: list[str], kwargs: dict) -> bool:
    """True when a recorded spawn is the caller's raw ``subprocess.run``."""
    if kwargs.get("timeout") != GIT_TIMEOUT_SECONDS:
        return True
    if not argv or not executable_is_absolute(argv[0]):
        return True
    try:
        resolved = os.path.realpath(argv[0])
    except OSError:
        return True
    return not git_pin_matches(resolved)


def prove_git_tool_spelling(invoke) -> list[str]:
    """``git``, ``git.exe``, ``GIT``, and the pinned path stay on the hardened runner.

    The adapter and ``subprocess`` share one module object, so the raw
    fallthrough is the recorded call that has no git timeout.
    """
    errors: list[str] = []
    if not PINNED_GIT:
        return ["pinned git is missing"]
    captured: list[tuple[list[str], dict]] = []
    original_spawn = subprocess.run

    def fake_spawn(argv, **kwargs):
        captured.append((list(argv), kwargs))
        return subprocess.CompletedProcess(argv, 0, stdout="abc\n", stderr="")

    def exercise(active_errors: list[str]) -> None:
        for token in (PINNED_GIT, "git.exe", "GIT"):
            before = len(captured)
            try:
                invoke([token, "rev-parse", "--help"], None)
            except SystemExit as exc:
                active_errors.append(f"{token} git spelling refused: {exc}")
                continue
            if len(captured) != before + 1:
                active_errors.append(f"{token} did not spawn pinned git")
                continue
            argv, kwargs = captured[-1]
            if _left_hardened_path(argv, kwargs):
                active_errors.append(f"{token} left the hardened path")
                continue
            active_errors.extend(
                allowlisted_git_errors(argv, kwargs, timeout=GIT_TIMEOUT_SECONDS)
            )
        before = len(captured)
        try:
            invoke(
                [PINNED_GIT, "status"],
                {"GIT_EXEC_PATH": "/evil/injected", "VF_SPAWN_SENTINEL": "leaked"},
            )
        except SystemExit as exc:
            if "refuses a caller environment" not in str(exc):
                active_errors.append(f"absolute git caller env refused as {exc}")
        else:
            active_errors.append("absolute git accepted a caller environment")
        if len(captured) != before:
            active_errors.append("absolute git caller env spawned")
        with tempfile.TemporaryDirectory(prefix="vf-decoy-spell-") as tmp:
            decoy = str(_decoy_git_path(Path(tmp)))
            before = len(captured)
            try:
                invoke([decoy, "status"], None)
            except SystemExit as exc:
                if "GIT_PIN_REFUSED" not in str(exc):
                    active_errors.append(f"absolute decoy spelling refused as {exc}")
            else:
                active_errors.append("absolute decoy spelling was accepted")
            if len(captured) != before:
                active_errors.append("absolute decoy left the hardened path")

    subprocess.run = fake_spawn
    try:
        exercise(errors)
        if not errors:
            def exact_git(token: str) -> bool:
                return token == "git"

            original_name = names_git_tool
            globals()["names_git_tool"] = exact_git
            try:
                before = len(captured)
                try:
                    invoke([PINNED_GIT, "rev-parse", "--help"], None)
                except SystemExit:
                    pass
                fell_through = any(
                    call[0] and call[0][0] == PINNED_GIT and call[1].get("timeout") is None
                    for call in captured[before:]
                )
            finally:
                globals()["names_git_tool"] = original_name
            if not fell_through:
                errors.append("spelling mutant was not caught")
    finally:
        subprocess.run = original_spawn
    return errors


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except (OSError, ValueError):
        return False
    return True


def _prove_home_anchor() -> list[str]:
    """QA #872: ambient TMPDIR does not hold the home, and global gitconfig does not survive."""
    errors: list[str] = []
    poison = Path(tempfile.mkdtemp(prefix="vf-spawn-ambient-"))
    saved_tempdir = tempfile.tempdir
    saved_env = {key: os.environ.get(key) for key in ("TMPDIR", "TEMP", "TMP")}
    global _home_dir, _temp_dir
    previous_home, previous_temp = _home_dir, _temp_dir
    try:
        target = poison / "target"
        target.mkdir()
        ambient = target
        link = poison / "link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            link = None
        if link is not None:
            if _trusted_dir(link):
                errors.append("symlinked temp root was trusted")
            ambient = link
        tempfile.tempdir = None
        os.environ["TMPDIR"] = str(ambient)
        os.environ["TEMP"] = str(ambient)
        os.environ["TMP"] = str(ambient)
        tempfile.tempdir = str(ambient)
        _home_dir = None
        _temp_dir = None
        home = controlled_home()
        temp = controlled_temp()
        home_path = Path(home)
        if _inside(home_path, poison) or _inside(Path(temp), poison):
            errors.append(f"controlled home followed ambient TMPDIR: home={home} temp={temp}")
        if not _under_fixed_root(home_path) or not _under_fixed_root(Path(temp)):
            errors.append(f"controlled home is not under a fixed root: home={home} temp={temp}")
        if os.name != "nt":
            mode = stat.S_IMODE(home_path.lstat().st_mode)
            if mode & 0o222:
                errors.append(f"spawn home is writable: {oct(mode)}")
        marker = "vf-spawn-cross-spawn-marker"
        run_git(["config", "--global", "core.fsmonitor", marker])
        shown = run_git(["config", "--global", "--get", "core.fsmonitor"])
        if marker in (shown.stdout or ""):
            errors.append(f"global gitconfig survived across spawns: {shown.stdout!r}")
        current = Path(controlled_home())
        current.chmod(0o700)
        (current / ".gitconfig").write_text(
            "[core]\n\tfsmonitor = /evil/planted-hook\n",
            encoding="utf-8",
        )
        planted = run_git(["config", "--global", "--get", "core.fsmonitor"])
        if "/evil/planted-hook" in (planted.stdout or ""):
            errors.append(f"planted gitconfig was reused: {planted.stdout!r}")
        if Path(controlled_home()) == current:
            errors.append("dirty spawn home was reused")
        if os.name != "nt":
            live = Path(controlled_home())
            aside = Path(str(live) + "-aside")
            evil = Path(tempfile.mkdtemp(prefix="vf-spawn-evil-home-"))
            try:
                (evil / ".gitconfig").write_text(
                    "[core]\n\tfsmonitor = /evil/link-hook\n",
                    encoding="utf-8",
                )
                live.rename(aside)
                live.symlink_to(evil, target_is_directory=True)
                linked = run_git(["config", "--global", "--get", "core.fsmonitor"])
                if "/evil/link-hook" in (linked.stdout or ""):
                    errors.append(f"symlinked spawn home was reused: {linked.stdout!r}")
            finally:
                if live.is_symlink():
                    live.unlink()
                if aside.exists():
                    aside.chmod(0o700)
                    shutil.rmtree(aside, ignore_errors=True)
                shutil.rmtree(evil, ignore_errors=True)
            if not _home_is_clean(_home_dir or ""):
                _home_dir = None
            controlled_home()
    except SpawnRefusal as exc:
        errors.append(f"spawn home anchor refused: {exc}")
    finally:
        tempfile.tempdir = saved_tempdir
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if previous_home is not None and _home_is_clean(previous_home):
            _home_dir = previous_home
        shutil.rmtree(poison, ignore_errors=True)
        if previous_temp is not None and _temp_is_clean(previous_temp):
            _temp_dir = previous_temp
    return errors


def prove_controlled_home() -> list[str]:
    """A poisoned home, temp, or COMSPEC does not reach the child or git config."""
    import json
    import sys

    errors: list[str] = _prove_home_anchor()
    keys = (
        "HOME",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "XDG_CONFIG_HOME",
        "XDG_CONFIG_DIRS",
        "TEMP",
        "TMP",
        "TMPDIR",
        "COMSPEC",
    )
    previous = {key: os.environ.get(key) for key in keys}
    with tempfile.TemporaryDirectory(prefix="vf-spawn-poison-") as tmp:
        root = Path(tmp)
        poison_home = root / "poison-home"
        poison_xdg = root / "poison-xdg"
        poison_tmp = root / "poison-tmp"
        poison_home.mkdir()
        (poison_xdg / "git").mkdir(parents=True)
        poison_tmp.mkdir()
        marker = root / "hook-ran"
        hook = root / "hook.sh"
        hook.write_text(f"#!/bin/sh\nprintf hooked > '{marker}'\n", encoding="utf-8")
        hook.chmod(0o755)
        config = f"[core]\n\tfsmonitor = {hook}\n"
        (poison_home / ".gitconfig").write_text(config, encoding="utf-8")
        (poison_xdg / "git" / "config").write_text(config, encoding="utf-8")
        evil_cmd = root / "evil-cmd"
        evil_cmd.write_text("#!/bin/sh\n", encoding="utf-8")
        poisoned = {
            "HOME": str(poison_home),
            "USERPROFILE": str(poison_home),
            "HOMEDRIVE": "Z:",
            "HOMEPATH": "\\PoisonUsers\\attacker",
            "XDG_CONFIG_HOME": str(poison_xdg),
            "XDG_CONFIG_DIRS": str(poison_xdg),
            "TEMP": str(poison_tmp),
            "TMP": str(poison_tmp),
            "TMPDIR": str(poison_tmp),
            "COMSPEC": str(evil_cmd),
        }
        os.environ.update(poisoned)
        repo = root / "repo"
        repo.mkdir()
        try:
            report_keys = keys + ("GIT_CONFIG_NOSYSTEM",)
            shown = run_tool(
                [
                    sys.executable,
                    "-c",
                    "import json,os; keys=" + repr(report_keys) + "; "
                    "print(json.dumps({key: os.environ.get(key) for key in keys}))",
                ],
                timeout=30,
            )
            listed = run_git(["config", "--global", "--get", "core.fsmonitor"])
            run_git(["init", "-q", "-b", "main"], cwd=repo)
            status = run_git(["status"], cwd=repo)
            try:
                run_tool([sys.executable, "-c", "print(1)"], timeout=30, extra_env={"HOME": str(poison_home)})
            except SpawnRefusal as exc:
                if "SPAWN_ENV_REFUSED" not in str(exc):
                    errors.append(f"extra HOME refused as {exc}")
            else:
                errors.append("extra HOME was accepted")
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        if shown.returncode != 0:
            return errors + [f"child env probe failed: {shown.stderr}"]
        try:
            child = json.loads(shown.stdout)
        except json.JSONDecodeError as exc:
            return errors + [f"child env was not JSON: {exc}"]
        home = controlled_home()
        temp = controlled_temp()
        if child.get("HOME") != home or child.get("USERPROFILE") != home:
            errors.append(f"poisoned home reached the child: {child}")
        if child.get("XDG_CONFIG_HOME") != home or child.get("XDG_CONFIG_DIRS") != home:
            errors.append(f"poisoned XDG config reached the child: {child}")
        if child.get("TEMP") != temp or child.get("TMP") != temp or child.get("TMPDIR") != temp:
            errors.append(f"poisoned temp reached the child: {child}")
        if child.get("COMSPEC") == str(evil_cmd):
            errors.append("poisoned COMSPEC reached the child")
        if child.get("GIT_CONFIG_NOSYSTEM") != "1":
            errors.append(f"GIT_CONFIG_NOSYSTEM was not forced: {child}")
        for key, value in poisoned.items():
            if value and value in shown.stdout:
                errors.append(f"poisoned {key} reached the child")
        if hook.name in (listed.stdout or "") or (listed.stdout or "").strip():
            errors.append(f"poisoned global gitconfig was read: {listed.stdout!r}")
        if marker.is_file():
            errors.append("poisoned core.fsmonitor ran")
        if status.returncode != 0:
            errors.append(f"git status failed under the sandbox: {status.stderr}")
    return errors


def windows_pin_case_errors() -> list[str]:
    """8.3 and case-fold pin checks. A search PATH is not one directory."""
    errors: list[str] = []
    short = "C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\tool-abc"
    long = "C:\\Users\\runneradmin\\AppData\\Local\\Temp\\tool-abc"

    def expand_short(path: str) -> str:
        return str(path).replace("/", "\\").replace("RUNNER~1", "runneradmin")

    if not same_pinned_directory(short, long, realpath=expand_short, fold_case=True, separator=";"):
        errors.append("8.3 directory did not match its long path")
    if not same_pinned_directory(short, long.upper(), realpath=expand_short, fold_case=True, separator=";"):
        errors.append("pin comparison stayed case-sensitive")
    if same_pinned_directory(short, long + "\\other", realpath=expand_short, fold_case=True, separator=";"):
        errors.append("a different directory was accepted as the pin")
    if same_pinned_directory(long + ";" + short, long, realpath=expand_short, fold_case=True, separator=";"):
        errors.append("a search PATH was accepted as the pin")
    return errors
