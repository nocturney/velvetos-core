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
import tempfile
import time
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
_cleanup_registered = False
SPAWN_HOME_STALE_HOURS = 24
_WINDOWS_SPAWN_DRIVE = "D"
_SPAWN_DIR_PREFIXES = ("vf-spawn-home-", "vf-spawn-tmp-")
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400
# Write rights a non-owner must not hold on the Windows spawn base.
_WRITE_MASK = (
    0x0002  # FILE_WRITE_DATA / FILE_ADD_FILE
    | 0x0004  # FILE_APPEND_DATA / FILE_ADD_SUBDIRECTORY
    | 0x0010  # FILE_WRITE_EA
    | 0x0100  # FILE_WRITE_ATTRIBUTES
    | 0x00010000  # DELETE
    | 0x00040000  # WRITE_DAC
    | 0x00080000  # WRITE_OWNER
    | 0x40000000  # GENERIC_WRITE
    | 0x10000000  # GENERIC_ALL
)


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


def _stat_is_reparse(info: os.stat_result) -> bool:
    if stat.S_ISLNK(info.st_mode):
        return True
    attrs = getattr(info, "st_file_attributes", 0) or 0
    return bool(attrs & _FILE_ATTRIBUTE_REPARSE_POINT)


def _path_is_reparse(path: str) -> bool:
    try:
        info = os.lstat(path)
    except OSError:
        return False
    return _stat_is_reparse(info)


def posix_base_verdict(
    *,
    uid: int,
    mode: int,
    is_symlink: bool,
    is_dir: bool,
    is_reparse: bool,
) -> str:
    """POSIX spawn base: a real directory owned by root with the sticky bit."""
    if is_symlink or is_reparse or not is_dir:
        return "SPAWN_HOME_ROOT_REFUSED"
    if uid != 0 or not (mode & stat.S_ISVTX):
        return "SPAWN_HOME_ACL_REFUSED"
    return "ok"


def _classify_posix_base(path: Path) -> str:
    try:
        info = path.lstat()
    except OSError:
        return "missing"
    return posix_base_verdict(
        uid=info.st_uid,
        mode=info.st_mode,
        is_symlink=stat.S_ISLNK(info.st_mode),
        is_dir=stat.S_ISDIR(info.st_mode),
        is_reparse=_stat_is_reparse(info),
    )


def private_dir_verdict(
    *,
    uid: int,
    mode: int,
    is_symlink: bool,
    is_dir: bool,
    is_reparse: bool,
    readonly: bool,
    current_uid: int,
    check_posix: bool,
) -> str:
    """Private spawn directory: owner-only mode on POSIX, never a link."""
    if is_symlink or is_reparse:
        return "SPAWN_HOME_REPARSE_REFUSED"
    if not is_dir:
        return "SPAWN_HOME_ROOT_REFUSED"
    if not check_posix:
        return "ok"
    if uid != current_uid:
        return "SPAWN_HOME_ACL_REFUSED"
    bits = stat.S_IMODE(mode)
    if bits & 0o077:
        return "SPAWN_HOME_ACL_REFUSED"
    if readonly and bits & 0o222:
        return "SPAWN_HOME_ACL_REFUSED"
    return "ok"


def _classify_private_dir(info: os.stat_result, *, readonly: bool) -> str:
    return private_dir_verdict(
        uid=info.st_uid,
        mode=info.st_mode,
        is_symlink=stat.S_ISLNK(info.st_mode),
        is_dir=stat.S_ISDIR(info.st_mode),
        is_reparse=_stat_is_reparse(info),
        readonly=readonly,
        current_uid=os.getuid() if os.name != "nt" else 0,
        check_posix=os.name != "nt",
    )


def windows_acl_verdict(
    *,
    owner_is_current_user: bool,
    aces: list[tuple[int, bool, int]],
) -> str:
    """Owner-only write. aces are (ace_type, sid_is_owner, mask)."""
    if not owner_is_current_user:
        return "SPAWN_HOME_ACL_REFUSED"
    owner_write = False
    for ace_type, sid_is_owner, mask in aces:
        # ACCESS_ALLOWED_ACE_TYPE is 0. Any other allow-like ACE fails closed.
        if ace_type != 0:
            return "SPAWN_HOME_ACL_REFUSED"
        if mask & _WRITE_MASK:
            if not sid_is_owner:
                return "SPAWN_HOME_ACL_REFUSED"
            owner_write = True
    if not owner_write:
        return "SPAWN_HOME_ACL_REFUSED"
    return "ok"


def _windows_drive(path: str) -> str:
    if len(path) >= 2 and path[0].isalpha() and path[1] == ":":
        return path[:2]
    return ""


def _windows_component_paths(text: str) -> list[str]:
    """Existing path prefixes from the drive root through text. Does not resolve links."""
    if len(text) < 3 or text[2] != "\\":
        raise SpawnRefusal("SPAWN_HOME_DRIVE_REFUSED")
    rest = text[3:]
    paths = [text[:3]]
    acc = text[:3]
    for part in rest.split("\\"):
        if not part:
            continue
        if part in {".", ".."}:
            raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")
        acc = acc + part if acc.endswith("\\") else acc + "\\" + part
        paths.append(acc)
    return paths


def resolve_windows_spawn_base(
    raw: str | None,
    *,
    is_reparse,
    acl_owner_only,
    exists,
    realpath,
    mkdir,
) -> str:
    """Windows spawn base: <VELVETOS_RUNTIME_ROOT>\\spawn-home on drive D:."""
    if raw is None or not str(raw).strip():
        raise SpawnRefusal("SPAWN_HOME_ROOT_UNSET")
    text = str(raw).strip().replace("/", "\\")
    while len(text) > 3 and text.endswith("\\"):
        text = text[:-1]
    drive = _windows_drive(text)
    if len(drive) != 2 or drive[0].upper() != _WINDOWS_SPAWN_DRIVE or len(text) < 3 or text[2] != "\\":
        raise SpawnRefusal("SPAWN_HOME_DRIVE_REFUSED")
    for component in _windows_component_paths(text):
        if not exists(component):
            raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")
        if is_reparse(component):
            raise SpawnRefusal("SPAWN_HOME_REPARSE_REFUSED")
    try:
        resolved = realpath(text)
    except OSError as exc:
        raise SpawnRefusal("SPAWN_HOME_REPARSE_REFUSED") from exc
    resolved_text = str(resolved).replace("/", "\\")
    if _windows_drive(resolved_text).upper() != drive.upper():
        raise SpawnRefusal("SPAWN_HOME_REPARSE_REFUSED")
    base = text + "\\spawn-home"
    if exists(base):
        if is_reparse(base):
            raise SpawnRefusal("SPAWN_HOME_REPARSE_REFUSED")
    else:
        mkdir(base)
        if is_reparse(base):
            raise SpawnRefusal("SPAWN_HOME_REPARSE_REFUSED")
    if not acl_owner_only(base):
        raise SpawnRefusal("SPAWN_HOME_ACL_REFUSED")
    return base


def _lstat_exists(path: str) -> bool:
    try:
        os.lstat(path)
    except OSError:
        return False
    return True


def _windows_current_sid() -> bytes:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    advapi32.GetTokenInformation.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.GetTokenInformation.restype = wintypes.BOOL
    advapi32.GetLengthSid.argtypes = [ctypes.c_void_p]
    advapi32.GetLengthSid.restype = wintypes.DWORD
    advapi32.CopySid.argtypes = [wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p]
    advapi32.CopySid.restype = wintypes.BOOL
    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        needed = wintypes.DWORD(0)
        advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
        if not needed.value:
            raise ctypes.WinError(ctypes.get_last_error())
        buf = ctypes.create_string_buffer(needed.value)
        if not advapi32.GetTokenInformation(token, 1, buf, needed, ctypes.byref(needed)):
            raise ctypes.WinError(ctypes.get_last_error())
        sid_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
        length = advapi32.GetLengthSid(sid_ptr)
        if not length:
            raise ctypes.WinError(ctypes.get_last_error())
        copy = ctypes.create_string_buffer(length)
        if not advapi32.CopySid(length, copy, sid_ptr):
            raise ctypes.WinError(ctypes.get_last_error())
        return copy.raw[:length]
    finally:
        kernel32.CloseHandle(token)


def _windows_owner_is_current_user(path: str) -> bool:
    """Owner SID of path, opened without following a junction."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    advapi32.GetSecurityInfo.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi32.GetSecurityInfo.restype = wintypes.DWORD
    advapi32.EqualSid.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    advapi32.EqualSid.restype = wintypes.BOOL
    handle = kernel32.CreateFileW(
        path,
        0x80000000,
        0x7,
        None,
        3,
        0x02000000 | 0x00200000,
        None,
    )
    invalid = ctypes.c_void_p(-1).value
    if not handle or handle == invalid:
        return False
    security = ctypes.c_void_p()
    try:
        owner = ctypes.c_void_p()
        status = advapi32.GetSecurityInfo(
            handle, 1, 0x1, ctypes.byref(owner), None, None, None, ctypes.byref(security),
        )
        if status != 0 or not owner.value:
            return False
        sid = _windows_current_sid()
        sid_buf = ctypes.create_string_buffer(sid)
        return bool(advapi32.EqualSid(owner, sid_buf))
    except OSError:
        return False
    finally:
        kernel32.CloseHandle(handle)
        if security.value:
            kernel32.LocalFree(security)


def _windows_read_acl(path: str) -> tuple[bool, list[tuple[int, bool, int]]]:
    """Return (owner is current user, allow-style ACE rows) without following a reparse point."""
    import ctypes
    from ctypes import wintypes

    if _path_is_reparse(path):
        raise SpawnRefusal("SPAWN_HOME_REPARSE_REFUSED")
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32.GetNamedSecurityInfoW.argtypes = [
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi32.GetAclInformation.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]
    advapi32.GetAclInformation.restype = wintypes.BOOL
    advapi32.GetAce.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p)]
    advapi32.GetAce.restype = wintypes.BOOL
    advapi32.EqualSid.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    advapi32.EqualSid.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    class _AclSize(ctypes.Structure):
        _fields_ = (
            ("AceCount", wintypes.DWORD),
            ("AclBytesInUse", wintypes.DWORD),
            ("AclBytesFree", wintypes.DWORD),
        )

    owner = ctypes.c_void_p()
    dacl = ctypes.c_void_p()
    security = ctypes.c_void_p()
    status = advapi32.GetNamedSecurityInfoW(
        path,
        1,
        0x1 | 0x4,
        ctypes.byref(owner),
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(security),
    )
    if status != 0:
        raise ctypes.WinError(status)
    try:
        sid = _windows_current_sid()
        sid_buf = ctypes.create_string_buffer(sid)
        owner_ok = bool(owner.value) and bool(advapi32.EqualSid(owner, sid_buf))
        if not dacl.value:
            return owner_ok, []
        info = _AclSize()
        if not advapi32.GetAclInformation(dacl, ctypes.byref(info), ctypes.sizeof(info), 2):
            raise ctypes.WinError(ctypes.get_last_error())
        aces: list[tuple[int, bool, int]] = []
        for index in range(info.AceCount):
            ace = ctypes.c_void_p()
            if not advapi32.GetAce(dacl, index, ctypes.byref(ace)) or not ace.value:
                raise ctypes.WinError(ctypes.get_last_error())
            header = ctypes.string_at(ace.value, 4)
            ace_type = header[0]
            ace_size = int.from_bytes(header[2:4], "little")
            if ace_size < 8:
                aces.append((ace_type, False, _WRITE_MASK))
                continue
            mask = int.from_bytes(ctypes.string_at(ace.value + 4, 4), "little")
            sid_is_owner = bool(advapi32.EqualSid(ace.value + 8, sid_buf))
            aces.append((ace_type, sid_is_owner, mask))
        return owner_ok, aces
    finally:
        if security.value:
            kernel32.LocalFree(security)


def _windows_lock_owner_only(path: str) -> None:
    """Replace the DACL with one allow ACE for the current user. Do not follow a junction."""
    import ctypes
    from ctypes import wintypes

    if _path_is_reparse(path):
        raise SpawnRefusal("SPAWN_HOME_REPARSE_REFUSED")
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    sid = _windows_current_sid()
    sid_buf = ctypes.create_string_buffer(sid)
    acl_size = 8 + 8 + len(sid) + 64
    acl = ctypes.create_string_buffer(acl_size)
    advapi32.InitializeAcl.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]
    advapi32.InitializeAcl.restype = wintypes.BOOL
    advapi32.AddAccessAllowedAce.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    advapi32.AddAccessAllowedAce.restype = wintypes.BOOL
    advapi32.SetNamedSecurityInfoW.argtypes = [
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    advapi32.SetNamedSecurityInfoW.restype = wintypes.DWORD
    if not advapi32.InitializeAcl(acl, acl_size, 2):
        raise SpawnRefusal("SPAWN_HOME_ACL_REFUSED") from ctypes.WinError(ctypes.get_last_error())
    file_all = 0x1F01FF
    if not advapi32.AddAccessAllowedAce(acl, 2, file_all, sid_buf):
        raise SpawnRefusal("SPAWN_HOME_ACL_REFUSED") from ctypes.WinError(ctypes.get_last_error())
    status = advapi32.SetNamedSecurityInfoW(
        path,
        1,
        0x4 | 0x80000000,
        None,
        None,
        acl,
        None,
    )
    if status != 0:
        raise SpawnRefusal("SPAWN_HOME_ACL_REFUSED") from ctypes.WinError(status)


def _windows_acl_is_owner_only(path: str) -> bool:
    try:
        owner_ok, aces = _windows_read_acl(path)
    except SpawnRefusal:
        raise
    except OSError as exc:
        raise SpawnRefusal("SPAWN_HOME_ACL_REFUSED") from exc
    return windows_acl_verdict(owner_is_current_user=owner_ok, aces=aces) == "ok"


def _windows_mkdir(path: str) -> None:
    if _path_is_reparse(path):
        raise SpawnRefusal("SPAWN_HOME_REPARSE_REFUSED")
    os.mkdir(path, 0o700)
    _windows_lock_owner_only(path)


def _windows_spawn_base() -> str:
    """Spawn base from VELVETOS_RUNTIME_ROOT. The Windows system directory is not a root."""
    raw = os.environ.get("VELVETOS_RUNTIME_ROOT")
    return resolve_windows_spawn_base(
        raw,
        is_reparse=_path_is_reparse,
        acl_owner_only=_windows_acl_is_owner_only,
        exists=_lstat_exists,
        realpath=os.path.realpath,
        mkdir=_windows_mkdir,
    )


def _posix_ok_roots() -> list[Path]:
    return [path for path in (Path("/tmp"), Path("/var/tmp")) if _classify_posix_base(path) == "ok"]


def _fixed_trusted_roots() -> list[Path]:
    """Directories that do not come from the ambient temp variables."""
    if os.name == "nt":
        return [Path(_windows_spawn_base())]
    return _posix_ok_roots()


def _trusted_dir(path: Path) -> bool:
    """A spawn root is a real directory. A symlink or junction is refused."""
    if os.name == "nt":
        try:
            info = path.lstat()
        except OSError:
            return False
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or _stat_is_reparse(info):
            return False
        return True
    return _classify_posix_base(path) == "ok"


def _spawn_root() -> Path:
    if os.name == "nt":
        base = Path(_windows_spawn_base())
        if not _trusted_dir(base):
            raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")
        return base
    roots = _posix_ok_roots()
    if roots:
        return roots[0]
    saw_acl = any(
        _classify_posix_base(path) == "SPAWN_HOME_ACL_REFUSED" for path in (Path("/tmp"), Path("/var/tmp"))
    )
    raise SpawnRefusal("SPAWN_HOME_ACL_REFUSED" if saw_acl else "SPAWN_HOME_ROOT_REFUSED")


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
        try:
            if not _under_fixed_root(path):
                raise SpawnRefusal("SPAWN_HOME_ROOT_REFUSED")
            if os.name != "nt":
                os.chmod(path, 0o500 if readonly else 0o700)
            info = path.lstat()
            verdict = _classify_private_dir(info, readonly=readonly and os.name != "nt")
            if verdict != "ok":
                raise SpawnRefusal(verdict)
            if os.name == "nt":
                _windows_lock_owner_only(str(path))
                if not _windows_acl_is_owner_only(str(path)):
                    raise SpawnRefusal("SPAWN_HOME_ACL_REFUSED")
            _register_spawn_cleanup()
            return str(path)
        except Exception:
            try:
                remove_spawn_tree(path)
            except OSError:
                pass
            raise
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


def remove_spawn_tree(path: Path) -> None:
    """Remove a spawn directory. A symlink or reparse point is unlinked and not followed."""
    try:
        info = os.lstat(path)
    except OSError:
        return
    if stat.S_ISLNK(info.st_mode) or _stat_is_reparse(info):
        os.unlink(path)
        return
    if not stat.S_ISDIR(info.st_mode):
        os.unlink(path)
        return
    if os.name != "nt":
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        directory = getattr(os, "O_DIRECTORY", 0)
        try:
            fd = os.open(os.fspath(path), os.O_RDONLY | directory | nofollow)
        except OSError:
            return
        try:
            try:
                os.fchmod(fd, 0o700)
            except OSError:
                pass
            names = os.listdir(fd)
        finally:
            os.close(fd)
    else:
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass
        try:
            names = os.listdir(path)
        except OSError:
            return
    for name in names:
        remove_spawn_tree(path / name)
    try:
        os.rmdir(path)
    except OSError:
        pass


def prune_stale_spawn_dirs(
    root: Path,
    *,
    now: float,
    max_age_seconds: float,
    owner_id: int | None = None,
) -> list[str]:
    """Delete this user's stale spawn dirs. Never follow a symlink onto another tree."""
    removed: list[str] = []
    try:
        entries = list(os.scandir(root))
    except OSError:
        return removed
    for entry in entries:
        if not entry.name.startswith(_SPAWN_DIR_PREFIXES):
            continue
        try:
            info = os.lstat(entry.path)
        except OSError:
            continue
        if owner_id is not None:
            owned = info.st_uid == owner_id
        elif os.name == "nt":
            owned = _windows_owner_is_current_user(entry.path)
        else:
            owned = info.st_uid == os.getuid()
        if not owned:
            continue
        if now - info.st_mtime < max_age_seconds:
            continue
        remove_spawn_tree(Path(entry.path))
        removed.append(entry.path)
    return removed


def _prune_spawn_roots() -> None:
    now = time.time()
    max_age = SPAWN_HOME_STALE_HOURS * 3600
    if os.name == "nt":
        try:
            roots = [Path(_windows_spawn_base())]
        except SpawnRefusal:
            return
    else:
        roots = _posix_ok_roots()
    for root in roots:
        prune_stale_spawn_dirs(root, now=now, max_age_seconds=max_age)


def _release_process_spawn_dirs() -> None:
    """Drop this process's home and temp, then prune stale homes. Runs at exit."""
    global _home_dir, _temp_dir
    home, temp = _home_dir, _temp_dir
    _home_dir = None
    _temp_dir = None
    try:
        for path in (home, temp):
            if path:
                try:
                    remove_spawn_tree(Path(path))
                except OSError:
                    pass
    finally:
        _prune_spawn_roots()


def _register_spawn_cleanup() -> None:
    global _cleanup_registered
    if _cleanup_registered:
        return
    atexit.register(_release_process_spawn_dirs)
    _cleanup_registered = True


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
        cause = f" ({exc.__cause__})" if exc.__cause__ else ""
        errors.append(f"spawn home anchor refused: {exc}{cause}")
    finally:
        tempfile.tempdir = saved_tempdir
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        orphan_home, orphan_temp = _home_dir, _temp_dir
        if previous_home is not None and _home_is_clean(previous_home):
            _home_dir = previous_home
        else:
            _home_dir = None
        if previous_temp is not None and _temp_is_clean(previous_temp):
            _temp_dir = previous_temp
        else:
            _temp_dir = None
        for orphan, kept in ((orphan_home, _home_dir), (orphan_temp, _temp_dir)):
            if orphan and orphan != kept:
                try:
                    remove_spawn_tree(Path(orphan))
                except OSError:
                    pass
        shutil.rmtree(poison, ignore_errors=True)
    return errors


def _expect_refusal(call, code: str) -> str | None:
    try:
        call()
    except SpawnRefusal as exc:
        if str(exc) != code:
            return f"expected {code} got {exc}"
        return None
    return f"expected {code} but the call succeeded"


def prove_spawn_home_policy() -> list[str]:
    """Windows drive, reparse, and ACL gates, plus the POSIX owner and mode gates."""
    import inspect

    errors: list[str] = []
    roots_src = inspect.getsource(_fixed_trusted_roots)
    windows_src = inspect.getsource(_windows_spawn_base)
    resolve_src = inspect.getsource(resolve_windows_spawn_base)
    for label, src in (
        ("_fixed_trusted_roots", roots_src),
        ("_windows_spawn_base", windows_src),
        ("resolve_windows_spawn_base", resolve_src),
    ):
        for banned in ("_system_root", "SYSTEMROOT", "gettempdir", "TMPDIR"):
            if banned in src:
                errors.append(f"{label} derives a spawn root from {banned}")
    if "posix_base_verdict(" not in inspect.getsource(_classify_posix_base):
        errors.append("posix base no longer uses the owner and sticky verdict")
    if "private_dir_verdict(" not in inspect.getsource(_classify_private_dir):
        errors.append("private dir no longer uses the mode and owner verdict")
    if "windows_acl_verdict(" not in inspect.getsource(_windows_acl_is_owner_only):
        errors.append("windows acl check no longer uses the owner-only verdict")
    if "_register_spawn_cleanup(" not in inspect.getsource(_private_dir):
        errors.append("spawn home is not registered for exit cleanup")
    if "atexit.register" not in inspect.getsource(_register_spawn_cleanup):
        errors.append("exit cleanup is not an atexit hook")
    if "finally" not in inspect.getsource(_release_process_spawn_dirs):
        errors.append("exit cleanup has no finally")
    if "realpath" in inspect.getsource(remove_spawn_tree) or "rmtree" in inspect.getsource(remove_spawn_tree):
        errors.append("spawn removal follows a real path")
    if "_windows_owner_is_current_user(" not in inspect.getsource(prune_stale_spawn_dirs):
        errors.append("windows prune no longer checks the owner sid")

    def identity(path: str) -> str:
        return path

    def absent(_path: str) -> bool:
        return False

    def no_reparse(_path: str) -> bool:
        return False

    def allow_acl(_path: str) -> bool:
        return True

    def refuse_acl(_path: str) -> bool:
        return False

    def record_mkdir(seen: set[str]):
        def mkdir(path: str) -> None:
            seen.add(path)
        return mkdir

    saved_system = os.environ.get("SYSTEMROOT")
    os.environ["SYSTEMROOT"] = r"C:\evil"
    try:
        for raw in (None, "", "   "):
            message = _expect_refusal(
                lambda raw=raw: resolve_windows_spawn_base(
                    raw, is_reparse=no_reparse, acl_owner_only=allow_acl,
                    exists=lambda _path: True, realpath=identity, mkdir=record_mkdir(set()),
                ),
                "SPAWN_HOME_ROOT_UNSET",
            )
            if message:
                errors.append(f"unset runtime root: {message}")
        for raw in (r"C:\Windows\Temp", r"E:\Velvet\Runtime", r"D:relative"):
            seen: set[str] = set()
            message = _expect_refusal(
                lambda raw=raw, seen=seen: resolve_windows_spawn_base(
                    raw, is_reparse=no_reparse, acl_owner_only=allow_acl,
                    exists=lambda _path: True, realpath=identity, mkdir=record_mkdir(seen),
                ),
                "SPAWN_HOME_DRIVE_REFUSED",
            )
            if message:
                errors.append(f"drive {raw}: {message}")
            if seen:
                errors.append(f"refused drive still created a spawn base: {raw}")
        runtime = r"D:\Velvet\Runtime\VelvetOS"
        base = runtime + r"\spawn-home"

        def exists_until_base(path: str) -> bool:
            return path != base

        seen = set()
        try:
            got = resolve_windows_spawn_base(
                runtime, is_reparse=no_reparse, acl_owner_only=allow_acl,
                exists=exists_until_base, realpath=identity, mkdir=record_mkdir(seen),
            )
        except SpawnRefusal as exc:
            errors.append(f"D: runtime root was refused: {exc}")
        else:
            if got != base or seen != {base}:
                errors.append(f"spawn base was {got!r} created={seen!r}")
            if got.upper().startswith("C:") or "evil" in got.lower():
                errors.append(f"spawn base followed the system directory: {got}")
        reparse_at = {r"D:\Velvet"}
        message = _expect_refusal(
            lambda: resolve_windows_spawn_base(
                runtime, is_reparse=lambda path: path in reparse_at, acl_owner_only=allow_acl,
                exists=lambda _path: True, realpath=identity, mkdir=record_mkdir(set()),
            ),
            "SPAWN_HOME_REPARSE_REFUSED",
        )
        if message:
            errors.append(f"junction component: {message}")
        message = _expect_refusal(
            lambda: resolve_windows_spawn_base(
                runtime, is_reparse=no_reparse, acl_owner_only=allow_acl,
                exists=lambda _path: True, realpath=lambda _path: r"C:\relocated\VelvetOS",
                mkdir=record_mkdir(set()),
            ),
            "SPAWN_HOME_REPARSE_REFUSED",
        )
        if message:
            errors.append(f"realpath left D:: {message}")
        message = _expect_refusal(
            lambda: resolve_windows_spawn_base(
                runtime, is_reparse=no_reparse, acl_owner_only=refuse_acl,
                exists=lambda _path: True, realpath=identity, mkdir=record_mkdir(set()),
            ),
            "SPAWN_HOME_ACL_REFUSED",
        )
        if message:
            errors.append(f"open acl: {message}")
        message = _expect_refusal(
            lambda: resolve_windows_spawn_base(
                runtime, is_reparse=no_reparse, acl_owner_only=allow_acl,
                exists=absent, realpath=identity, mkdir=record_mkdir(set()),
            ),
            "SPAWN_HOME_ROOT_REFUSED",
        )
        if message:
            errors.append(f"missing runtime root: {message}")
    finally:
        if saved_system is None:
            os.environ.pop("SYSTEMROOT", None)
        else:
            os.environ["SYSTEMROOT"] = saved_system

    sticky = stat.S_IFDIR | stat.S_ISVTX | 0o755
    if posix_base_verdict(uid=0, mode=sticky, is_symlink=False, is_dir=True, is_reparse=False) != "ok":
        errors.append("root sticky base was refused")
    if posix_base_verdict(uid=1000, mode=sticky, is_symlink=False, is_dir=True, is_reparse=False) != "SPAWN_HOME_ACL_REFUSED":
        errors.append("non-root sticky base was accepted")
    if posix_base_verdict(uid=0, mode=stat.S_IFDIR | 0o755, is_symlink=False, is_dir=True, is_reparse=False) != "SPAWN_HOME_ACL_REFUSED":
        errors.append("root base without the sticky bit was accepted")
    if posix_base_verdict(uid=0, mode=sticky, is_symlink=True, is_dir=True, is_reparse=False) != "SPAWN_HOME_ROOT_REFUSED":
        errors.append("symlinked posix base was accepted")
    if os.name != "nt":
        user_dir = Path(tempfile.mkdtemp(prefix="vf-spawn-acl-"))
        link = Path(str(user_dir) + "-link")
        try:
            os.chmod(user_dir, 0o755)
            if _classify_posix_base(user_dir) != "SPAWN_HOME_ACL_REFUSED":
                errors.append("live non-root base was accepted")
            link.symlink_to(Path("/tmp"), target_is_directory=True)
            if _trusted_dir(link):
                errors.append("live symlinked base was trusted")
            if _classify_posix_base(Path("/tmp")) != "ok" and _classify_posix_base(Path("/var/tmp")) != "ok":
                errors.append("no root-owned sticky temp directory")
            outside = Path("/workspace") / f"vf-spawn-outside-{secrets.token_hex(4)}"
            outside.mkdir()
            try:
                os.chmod(outside, 0o500)
                if _home_is_clean(str(outside)):
                    errors.append("home outside the fixed root was clean")
            finally:
                os.chmod(outside, 0o700)
                outside.rmdir()
        finally:
            if link.is_symlink():
                link.unlink()
            shutil.rmtree(user_dir, ignore_errors=True)
    uid = os.getuid() if os.name != "nt" else 0
    if private_dir_verdict(
        uid=uid, mode=stat.S_IFDIR | 0o500, is_symlink=False, is_dir=True, is_reparse=False,
        readonly=True, current_uid=uid, check_posix=True,
    ) != "ok":
        errors.append("owner mode 0500 was refused")
    if private_dir_verdict(
        uid=uid + 1, mode=stat.S_IFDIR | 0o500, is_symlink=False, is_dir=True, is_reparse=False,
        readonly=True, current_uid=uid, check_posix=True,
    ) != "SPAWN_HOME_ACL_REFUSED":
        errors.append("another user's private dir was accepted")
    if private_dir_verdict(
        uid=uid, mode=stat.S_IFDIR | 0o707, is_symlink=False, is_dir=True, is_reparse=False,
        readonly=False, current_uid=uid, check_posix=True,
    ) != "SPAWN_HOME_ACL_REFUSED":
        errors.append("group/other write on a private dir was accepted")
    if private_dir_verdict(
        uid=uid, mode=stat.S_IFDIR | 0o700, is_symlink=False, is_dir=True, is_reparse=False,
        readonly=True, current_uid=uid, check_posix=True,
    ) != "SPAWN_HOME_ACL_REFUSED":
        errors.append("writable spawn home was accepted")
    owner_mask = 0x1F01FF
    if windows_acl_verdict(owner_is_current_user=True, aces=[(0, True, owner_mask)]) != "ok":
        errors.append("owner-only windows acl was refused")
    for mask in (0x0002, 0x0004, 0x0010, 0x0100, 0x00010000, 0x00040000, 0x00080000, 0x40000000, 0x10000000):
        if windows_acl_verdict(
            owner_is_current_user=True, aces=[(0, True, owner_mask), (0, False, mask)],
        ) != "SPAWN_HOME_ACL_REFUSED":
            errors.append(f"non-owner write mask {mask:#x} was accepted")
    if windows_acl_verdict(
        owner_is_current_user=True, aces=[(0, True, owner_mask), (0, False, 0x1)],
    ) != "ok":
        errors.append("non-owner read ace was refused")
    if windows_acl_verdict(owner_is_current_user=False, aces=[(0, True, owner_mask)]) != "SPAWN_HOME_ACL_REFUSED":
        errors.append("windows acl owned by someone else was accepted")
    if windows_acl_verdict(owner_is_current_user=True, aces=[]) != "SPAWN_HOME_ACL_REFUSED":
        errors.append("windows acl with no owner write was accepted")
    return errors


def prove_spawn_home_cleanup() -> list[str]:
    """Exit removes this process's home. Stale homes go; symlink targets stay."""
    errors: list[str] = []
    try:
        home = controlled_home()
        temp = controlled_temp()
    except SpawnRefusal as exc:
        return [f"cleanup spawn refused: {exc}"]
    marker = Path(temp) / "marker.txt"
    marker.write_text("x", encoding="utf-8")
    _release_process_spawn_dirs()
    if os.path.lexists(home) or os.path.lexists(temp):
        errors.append(f"process spawn home was not removed at exit: home={home} temp={temp}")
    if _home_dir is not None or _temp_dir is not None:
        errors.append("process spawn home globals survived exit")
    with tempfile.TemporaryDirectory(prefix="vf-spawn-prune-") as tmp:
        root = Path(tmp)
        old = time.time() - (SPAWN_HOME_STALE_HOURS + 1) * 3600
        canary = root / "canary-target"
        canary.mkdir()
        secret = canary / "keep.txt"
        secret.write_text("keep", encoding="utf-8")
        link = root / "vf-spawn-home-stale"
        try:
            link.symlink_to(canary, target_is_directory=True)
        except OSError as exc:
            if os.name != "nt":
                errors.append(f"posix symlink for prune was refused: {exc}")
        else:
            os.utime(link, (old, old), follow_symlinks=False)
        stale = root / "vf-spawn-home-olddir"
        stale.mkdir()
        (stale / "gone.txt").write_text("x", encoding="utf-8")
        os.utime(stale, (old, old))
        os.chmod(stale, 0o500)
        fresh = root / "vf-spawn-tmp-fresh"
        fresh.mkdir()
        owner = os.getuid() if os.name != "nt" else 0
        try:
            prune_stale_spawn_dirs(
                root, now=time.time(), max_age_seconds=SPAWN_HOME_STALE_HOURS * 3600, owner_id=owner,
            )
        except Exception as exc:
            if not secret.is_file():
                errors.append("prune followed a symlink and deleted the target")
            else:
                errors.append(f"prune raised before finishing: {exc}")
        else:
            if not secret.is_file() or secret.read_text(encoding="utf-8") != "keep":
                errors.append("prune followed a symlink and deleted the target")
        if any("followed a symlink" in item for item in errors):
            return errors
        if os.path.lexists(link):
            errors.append("stale spawn symlink was not removed")
        if stale.exists():
            errors.append("stale spawn directory was not removed")
        if not fresh.is_dir():
            errors.append("fresh spawn directory was pruned")
        foreign = root / "vf-spawn-tmp-foreign"
        foreign.mkdir()
        os.utime(foreign, (old, old))
        prune_stale_spawn_dirs(
            root, now=time.time(), max_age_seconds=SPAWN_HOME_STALE_HOURS * 3600, owner_id=owner + 1,
        )
        if not foreign.is_dir():
            errors.append("prune removed another user's spawn directory")
        prune_stale_spawn_dirs(
            root, now=time.time(), max_age_seconds=SPAWN_HOME_STALE_HOURS * 3600, owner_id=owner,
        )
        if foreign.exists():
            errors.append("owned stale spawn directory survived prune")
    return errors


def prove_controlled_home() -> list[str]:
    """A poisoned home, temp, or COMSPEC does not reach the child or git config."""
    import json
    import sys

    errors: list[str] = []
    errors.extend(prove_spawn_home_policy())
    errors.extend(prove_spawn_home_cleanup())
    errors.extend(_prove_home_anchor())
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
