#!/usr/bin/env python3
"""Fail-closed spawn helpers for absolute tools and allowlisted environments.

Does not replace the git runner in check-all.py or the gh spawns claimed by
subprocess hygiene slice 2. Stage 8 generators stay on their historical
policy-manifest hashes.
"""
from __future__ import annotations

import atexit
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
_owned_dirs: list[str] = []


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

    A bare name is looked up once on the ambient PATH, then pinned.
    Later spawns do not search that PATH again.
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
        owned = str(path)
        _remember_spawn_dir(owned)
        return owned
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


def _remember_spawn_dir(path: str) -> None:
    if path not in _owned_dirs:
        _owned_dirs.append(path)


def _remove_spawn_dir(path: str) -> None:
    target = Path(path)
    try:
        info = target.lstat()
    except OSError:
        return
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        target.unlink(missing_ok=True)
        return
    if os.name != "nt":
        try:
            os.chmod(target, 0o700)
        except OSError:
            pass
    shutil.rmtree(target, ignore_errors=True)


def release_spawn_dirs() -> None:
    """Remove every home and temp this process created, then drop the cache."""
    global _home_dir, _temp_dir
    for path in list(_owned_dirs):
        _remove_spawn_dir(path)
    _owned_dirs.clear()
    _home_dir = None
    _temp_dir = None


atexit.register(release_spawn_dirs)


def sandbox_directories() -> tuple[str, str]:
    """The controlled home and temp. Ambient HOME and TMPDIR are not used."""
    return controlled_home(), controlled_temp()


def _write_fsmonitor_hook(directory: Path, marker: Path) -> str:
    """A command that creates marker when this OS runs it."""
    if os.name == "nt":
        command = directory / "hook.cmd"
        command.write_text(
            '@echo off\r\n> "' + str(marker) + '" echo hooked\r\n',
            encoding="utf-8",
        )
        return str(command)
    command = directory / "hook.sh"
    command.write_text(
        "#!/bin/sh\nprintf hooked > '" + str(marker) + "'\n",
        encoding="utf-8",
    )
    command.chmod(0o755)
    return str(command)


def _execute_hook_command(command: str) -> None:
    if os.name == "nt":
        shell = os.environ.get("COMSPEC") or "cmd.exe"
        subprocess.run([shell, "/d", "/c", command], check=False, timeout=15, capture_output=True)
        return
    subprocess.run([command], check=False, timeout=15, capture_output=True)


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
    home, temp = sandbox_directories()
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
    """Errors when one captured git spawn is not absolute, timed, and allowlisted."""
    errors: list[str] = []
    if not argv or not executable_is_absolute(argv[0]):
        return [f"git was not absolute: {argv}"]
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


def _prove_hook_command() -> list[str]:
    """The fsmonitor command for this OS creates a marker when it is executed."""
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="vf-spawn-hook-") as tmp:
        root = Path(tmp)
        marker = root / "hook-ran"
        command = _write_fsmonitor_hook(root, marker)
        try:
            _execute_hook_command(command)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return [f"fsmonitor hook command did not run: {exc}"]
        if not marker.is_file():
            errors.append("fsmonitor hook command did not create a marker")
    return errors


def _prove_poisoned_child() -> list[str]:
    """A poisoned home, temp, or COMSPEC does not reach the child or git config."""
    import json

    errors: list[str] = []
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
        command = _write_fsmonitor_hook(root, marker)
        hook = Path(command)
        config = "[core]\n\tfsmonitor = " + command + "\n"
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


def _private_dir_follows_tmpdir(prefix: str, *, readonly: bool) -> str:
    """Mutant: create the directory with mkdtemp, which follows ambient TMPDIR."""
    del readonly
    return tempfile.mkdtemp(prefix=prefix)


def _home_is_clean_keep(path: str) -> bool:
    """Mutant: reuse a home after a gitconfig was written into it."""
    del path
    return True


def _write_fsmonitor_hook_noop(directory: Path, marker: Path) -> str:
    """Mutant: a shell stub that does not create the marker on any OS."""
    del marker
    command = directory / "hook.sh"
    command.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    try:
        command.chmod(0o755)
    except OSError:
        pass
    return str(command)


def sandbox_directories_ambient() -> tuple[str, str]:
    """Mutant: hand the child the ambient home and temp."""
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE") or ""
    temp = os.environ.get("TMPDIR") or os.environ.get("TEMP") or os.environ.get("TMP") or ""
    return home, temp


def _release_spawn_dirs_noop() -> None:
    """Mutant: leave the controlled directories on disk."""
    return None


def _swap_global(name: str, replacement, probe):
    original = globals()[name]
    globals()[name] = replacement
    try:
        return probe()
    finally:
        globals()[name] = original


def _require_caught(found: list[str], token: str, missed: str) -> list[str]:
    if any(token in item for item in found):
        return []
    return [missed]


def _prove_note_mutants() -> list[str]:
    """Each #872 note has a mutant the live proof catches."""
    errors: list[str] = []
    found = _swap_global("_private_dir", _private_dir_follows_tmpdir, _prove_home_anchor)
    errors.extend(_require_caught(found, "followed ambient TMPDIR", "ambient TMPDIR mutant was not caught"))
    found = _swap_global("_home_is_clean", _home_is_clean_keep, _prove_home_anchor)
    errors.extend(
        _require_caught(found, "planted gitconfig was reused", "dirty home mutant was not caught")
    )
    found = _swap_global("_write_fsmonitor_hook", _write_fsmonitor_hook_noop, _prove_hook_command)
    errors.extend(
        _require_caught(found, "did not create a marker", "fsmonitor hook mutant was not caught")
    )
    found = _swap_global("sandbox_directories", sandbox_directories_ambient, _prove_poisoned_child)
    errors.extend(_require_caught(found, "poisoned home reached the child", "ambient HOME mutant was not caught"))
    found = _swap_global("release_spawn_dirs", _release_spawn_dirs_noop, _prove_release)
    errors.extend(_require_caught(found, "spawn home was not removed", "cleanup mutant was not caught"))
    release_spawn_dirs()
    return errors


def _prove_release() -> list[str]:
    """release_spawn_dirs removes the home and temp created for this process."""
    global _home_dir, _temp_dir
    _home_dir = None
    _temp_dir = None
    home = controlled_home()
    temp = controlled_temp()
    release_spawn_dirs()
    errors: list[str] = []
    if Path(home).exists() or Path(temp).exists():
        errors.append("spawn home was not removed")
    return errors


def _spawn_child_paths(script_dir: str) -> tuple[int, str, str]:
    env = {
        key: os.environ[key]
        for key in (
            "PATH",
            "SYSTEMROOT",
            "SystemRoot",
            "WINDIR",
            "COMSPEC",
            "PATHEXT",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
        )
        if os.environ.get(key)
    }
    env["PYTHONPATH"] = script_dir
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import vf_spawn\n"
            "home = vf_spawn.controlled_home()\n"
            "temp = vf_spawn.controlled_temp()\n"
            "print(home)\n"
            "print(temp)\n",
        ],
        cwd=script_dir,
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _prove_exit_cleanup() -> list[str]:
    """A child removes its spawn directories at process exit. Skipping registration leaks them."""
    source_path = Path(__file__).resolve()
    source = source_path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    needle = "\natexit.register(release_spawn_dirs)\n"
    if source.count(needle) != 1:
        return ["spawn cleanup registration is not unique"]
    errors: list[str] = []
    mutant = source.replace(needle, "\natexit.unregister(release_spawn_dirs)\n", 1)
    for label, text, should_remain in (("live", source, False), ("mutant", mutant, True)):
        with tempfile.TemporaryDirectory(prefix="vf-spawn-exit-") as tmp:
            script_dir = Path(tmp)
            (script_dir / "vf_spawn.py").write_text(text, encoding="utf-8")
            try:
                code, stdout, stderr = _spawn_child_paths(str(script_dir))
            except (OSError, subprocess.TimeoutExpired) as exc:
                errors.append(f"{label} spawn cleanup child failed: {exc}")
                continue
            paths = [line for line in stdout.splitlines() if line.strip()]
            if code != 0 or len(paths) != 2:
                errors.append(f"{label} spawn cleanup child failed: exit={code} stderr={stderr!r}")
                for path in paths:
                    _remove_spawn_dir(path)
                continue
            remaining = [path for path in paths if Path(path).exists()]
            if should_remain and len(remaining) != 2:
                errors.append("exit cleanup mutant was not caught")
            if not should_remain and remaining:
                errors.append("spawn home leaked after process exit")
            for path in paths:
                _remove_spawn_dir(path)
    return errors


def prove_controlled_home() -> list[str]:
    """QA #872: anchor, private cache, an OS hook command, and cleanup. Each has a mutant."""
    errors: list[str] = []
    errors.extend(_prove_hook_command())
    errors.extend(_prove_home_anchor())
    errors.extend(_prove_poisoned_child())
    errors.extend(_prove_note_mutants())
    errors.extend(_prove_release())
    errors.extend(_prove_exit_cleanup())
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
