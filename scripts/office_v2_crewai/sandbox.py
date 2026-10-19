"""D: sandbox environment for the CrewAI pilot. Does not import crewai."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from office_v2_crewai.contract import APPROVED_OLLAMA_HOST, SANDBOX_ROOT, VELVET_ROOT


class StorageRefusal(RuntimeError):
    """A containment rule failed closed. No PASS is recorded."""


PATH_KEYS = (
    "CREWAI_STORAGE_DIR",
    "TMP",
    "TEMP",
    "USERPROFILE",
    "HOME",
    "APPDATA",
    "LOCALAPPDATA",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "HF_HOME",
    "PIP_CACHE_DIR",
    "PYTHONPYCACHEPREFIX",
)

VALUE_KEYS = {
    "PIP_NO_CACHE_DIR": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "CREWAI_DISABLE_TELEMETRY": "true",
    "CREWAI_DISABLE_TRACKING": "true",
    "OTEL_SDK_DISABLED": "true",
    "CREWAI_TRACING_ENABLED": "false",
    "LANGSMITH_TRACING": "false",
    "LITELLM_LOCAL_MODEL_COST_MAP": "True",
    "LITELLM_LOCAL_ANTHROPIC_BETA_HEADERS": "True",
    "LITELLM_MODE": "PRODUCTION",
    "HF_HUB_OFFLINE": "1",
    "OLLAMA_HOST": APPROVED_OLLAMA_HOST,
}

# Dead-proxy tripwire. NO_PROXY is only the approved loopback, so a fallback
# to localhost:11434 cannot skip it. ALL_PROXY covers httpx as well as requests.
PROXY_KEYS = {
    "HTTP_PROXY": "http://127.0.0.1:9",
    "HTTPS_PROXY": "http://127.0.0.1:9",
    "ALL_PROXY": "http://127.0.0.1:9",
    "NO_PROXY": "127.0.0.1",
}

FORBIDDEN_ENV = (
    "TIKTOKEN_CACHE_DIR",
    "CUSTOM_TIKTOKEN_CACHE_DIR",
    "CHROMA_ANONYMIZED_TELEMETRY",
)


def _parts(path: str) -> list[str] | None:
    if not isinstance(path, str) or not path.strip():
        return None
    text = path.replace("/", "\\")
    if text.startswith("\\\\") or ":" in text[2:]:
        return None
    raw = [part for part in text.split("\\") if part != "" and part != "."]
    if not raw or not raw[0].endswith(":") or len(raw[0]) != 2:
        return None
    parts = [raw[0].upper()]
    for part in raw[1:]:
        if part == "..":
            if len(parts) == 1:
                return None
            parts.pop()
            continue
        parts.append(part)
    return parts


def on_drive_d(path: str) -> bool:
    parts = _parts(path)
    return bool(parts) and parts[0] == "D:"


def under_root(path: str, root: str = SANDBOX_ROOT) -> bool:
    parts = _parts(path)
    root_parts = _parts(root)
    if not parts or not root_parts:
        return False
    if len(parts) < len(root_parts):
        return False
    return [part.casefold() for part in parts[: len(root_parts)]] == [part.casefold() for part in root_parts]


def _same(path: str, expected: str) -> bool:
    left = _parts(path)
    right = _parts(expected)
    if not left or not right or len(left) != len(right):
        return False
    return [part.casefold() for part in left] == [part.casefold() for part in right]


def approved_environment(root: str = SANDBOX_ROOT) -> dict:
    """Exact CLQ-16 variables. Paths stay under the approved sandbox root."""
    base = root.rstrip("\\/")
    env = {
        "CREWAI_STORAGE_DIR": base + "\\crewai-storage",
        "TMP": base + "\\tmp",
        "TEMP": base + "\\tmp",
        "USERPROFILE": base,
        "HOME": base,
        "APPDATA": base + "\\AppData\\Roaming",
        "LOCALAPPDATA": base + "\\AppData\\Local",
        "XDG_CACHE_HOME": base + "\\.cache",
        "XDG_CONFIG_HOME": base + "\\.config",
        "XDG_DATA_HOME": base + "\\.local\\share",
        "HF_HOME": base + "\\hf",
        "PIP_CACHE_DIR": base + "\\pip-cache",
        "PYTHONPYCACHEPREFIX": base + "\\pycache",
    }
    env.update(VALUE_KEYS)
    for key, value in PROXY_KEYS.items():
        env[key] = value
        env[key.lower()] = value
    return env


def assert_forbidden_env(env: dict) -> None:
    """Refuse cache and removed telemetry variables. Do not set them."""
    if not isinstance(env, dict):
        raise StorageRefusal("SANDBOX_ENV_ABSENT")
    for key in FORBIDDEN_ENV:
        value = env.get(key)
        if value is None or value == "":
            continue
        raise StorageRefusal("FORBIDDEN_ENV:" + key)


def _protected_hits(env: dict, name: str) -> list[tuple[str, object]]:
    """Every spelling of a protected name. POSIX proxy lookup is case-insensitive."""
    upper = name.upper()
    hits = []
    for key, value in env.items():
        if isinstance(key, str) and key.upper() == upper:
            hits.append((key, value))
    return hits


def fold_protected_env(env: dict) -> dict:
    """Keep one canonical spelling for OLLAMA_HOST and the proxy variables."""
    if not isinstance(env, dict):
        raise StorageRefusal("SANDBOX_ENV_ABSENT")
    folded = {}
    held: dict[str, object] = {}
    for key, value in env.items():
        if not isinstance(key, str):
            raise StorageRefusal("SANDBOX_ENV_ABSENT")
        upper = key.upper()
        if upper == "OLLAMA_HOST" or upper in PROXY_KEYS:
            if upper not in held or (isinstance(value, str) and value.strip()):
                held[upper] = value
            continue
        folded[key] = value
    if "OLLAMA_HOST" in held:
        folded["OLLAMA_HOST"] = held["OLLAMA_HOST"]
    for key in PROXY_KEYS:
        if key not in held:
            continue
        folded[key] = held[key]
        folded[key.lower()] = held[key]
    return folded


def assert_proxy_env(env: dict) -> None:
    """E5 tripwire. Anything other than the dead loopback proxy is a refusal."""
    if not isinstance(env, dict):
        raise StorageRefusal("E5_PROXY_ABSENT")
    for key, want in PROXY_KEYS.items():
        hits = _protected_hits(env, key)
        if not hits:
            raise StorageRefusal("E5_PROXY_ABSENT:" + key)
        for name, value in hits:
            if not isinstance(value, str) or not value:
                raise StorageRefusal("E5_PROXY_ABSENT:" + name)
            if value != want:
                raise StorageRefusal("E5_PROXY_MISMATCH:" + name)


def assert_sandbox_env(env: dict, root: str = SANDBOX_ROOT) -> None:
    """Refuse a missing variable, a non-D: path, or a path outside the sandbox."""
    if not isinstance(env, dict):
        raise StorageRefusal("SANDBOX_ENV_ABSENT")
    expected = approved_environment(root)
    for key in PATH_KEYS:
        value = env.get(key)
        if not isinstance(value, str) or not value.strip():
            raise StorageRefusal("SANDBOX_ENV_ABSENT:" + key)
        if not on_drive_d(value):
            raise StorageRefusal("SANDBOX_NOT_ON_D:" + key)
        if not under_root(value, root):
            raise StorageRefusal("SANDBOX_OUTSIDE_ROOT:" + key)
        if not _same(value, expected[key]):
            raise StorageRefusal("SANDBOX_PATH_MISMATCH:" + key)
    for key, want in VALUE_KEYS.items():
        value = env.get(key)
        if not isinstance(value, str) or not value:
            raise StorageRefusal("SANDBOX_ENV_ABSENT:" + key)
        if value != want:
            raise StorageRefusal("SANDBOX_VALUE_MISMATCH:" + key)
    assert_forbidden_env(env)
    assert_proxy_env(env)
    if not on_drive_d(root):
        raise StorageRefusal("SANDBOX_NOT_ON_D:ROOT")


def assert_no_dotenv(directory: Path) -> None:
    """chromadb and litellm read .env from the working directory."""
    if (directory / ".env").exists():
        raise StorageRefusal("SANDBOX_DOTENV_PRESENT")


def enter_sandbox(cwd: str, root: str = SANDBOX_ROOT) -> None:
    """Move the process into the sandbox. Refuse a missing directory or a .env."""
    assert_cwd(cwd, root)
    if not _same(cwd, root):
        raise StorageRefusal("SANDBOX_CWD_OUTSIDE_ROOT")
    path = Path(cwd)
    if path.exists():
        assert_no_dotenv(path)
    if not path.is_dir():
        raise StorageRefusal("SANDBOX_CWD_ABSENT")
    assert_no_dotenv(path)
    os.chdir(path)


def assert_cwd(cwd: str, root: str = SANDBOX_ROOT) -> None:
    if not isinstance(cwd, str) or not on_drive_d(cwd):
        raise StorageRefusal("SANDBOX_CWD_NOT_ON_D")
    if not under_root(cwd, root):
        raise StorageRefusal("SANDBOX_CWD_OUTSIDE_ROOT")


def assert_sandbox_resolution(root: str = SANDBOX_ROOT, home: str | None = None,
                              temp: str | None = None, platform: str | None = None) -> None:
    """Path.home() and tempfile.gettempdir() must stay inside the sandbox.

    Windows Python resolves home from USERPROFILE and ignores HOME. A correct
    HOME with a wrong USERPROFILE is a refusal. Passing home/temp skips the
    live calls so a sensor can simulate that Windows rule.
    """
    profile = os.environ.get("USERPROFILE")
    if not isinstance(profile, str) or not _same(profile, root):
        raise StorageRefusal("SANDBOX_USERPROFILE_OUTSIDE_ROOT")
    if home is None:
        home = str(Path.home())
    if not isinstance(home, str) or (not _same(home, root) and not under_root(home, root)):
        raise StorageRefusal("SANDBOX_HOME_OUTSIDE_ROOT")
    plat = sys.platform if platform is None else platform
    if plat == "win32" and not _same(home, profile):
        raise StorageRefusal("SANDBOX_HOME_OUTSIDE_ROOT")
    if temp is None:
        tempfile.tempdir = None
        temp = tempfile.gettempdir()
    if not isinstance(temp, str) or not under_root(temp, root):
        raise StorageRefusal("SANDBOX_TEMP_OUTSIDE_ROOT")


def _strip_extended(path: str) -> str:
    """Drop the ``\\\\?\\`` prefix GetFinalPathNameByHandle adds."""
    if not isinstance(path, str):
        return path
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[8:]
    if path.startswith("\\\\?\\"):
        return path[4:]
    return path


def _windows_final_path(path: str) -> str | None:
    """Resolve one existing Windows path. None means the final path is unproven.

    FILE_FLAG_BACKUP_SEMANTICS opens a directory. The call does not set
    FILE_FLAG_OPEN_REPARSE_POINT, so a junction or symlink returns its target.
    """
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.GetFinalPathNameByHandleW.argtypes = [
        wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD,
    ]
    kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.CreateFileW(
        path, 0, 1 | 2 | 4, None, 3, 0x02000000, None,
    )
    # INVALID_HANDLE_VALUE is -1. ctypes may surface that as None or as the
    # unsigned pointer width, so every spelling is a failed open.
    invalid = wintypes.HANDLE(-1).value
    if handle in (None, 0, -1, invalid):
        return None
    try:
        buf = ctypes.create_unicode_buffer(32768)
        length = kernel32.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
        if length == 0 or length >= len(buf):
            return None
        return _strip_extended(buf.value)
    finally:
        kernel32.CloseHandle(handle)


def _drive_components(path: str) -> tuple[str, list[str]] | None:
    """Split ``D:\\a\\b`` into ``('D:', ['a', 'b'])``. UNC is not a drive path."""
    if not isinstance(path, str):
        return None
    text = path.replace("/", "\\")
    if text.startswith("\\\\") or len(text) < 2 or text[1] != ":":
        return None
    if not text[0].isalpha() or ":" in text[2:]:
        return None
    rest = text[2:]
    if rest.startswith("\\"):
        rest = rest[1:]
    comps = [part for part in rest.split("\\") if part not in ("", ".")]
    return text[0].upper() + ":", comps


def _posix_components(path: str) -> tuple[str, list[str]] | None:
    if os.name == "nt" or not isinstance(path, str) or not path.startswith("/"):
        return None
    comps = [part for part in path.split("/") if part not in ("", ".")]
    return "/", comps


def _deepest_existing(path: str, probe) -> tuple[str | None, list[str]]:
    """Deepest existing ancestor and the missing tail.

    The bare Windows drive is not an ancestor. ``..`` stays in the tail so a
    junction below it is still opened.
    """
    parsed = _drive_components(path)
    anchor_sep = "\\"
    if parsed is None:
        parsed = _posix_components(path)
        anchor_sep = "/"
    if parsed is None:
        if probe(path):
            return path, []
        return None, []
    anchor, comps = parsed
    for index in range(len(comps), 0, -1):
        head = comps[:index]
        if anchor == "/":
            candidate = "/" + "/".join(head)
        else:
            candidate = anchor + anchor_sep + anchor_sep.join(head)
        if probe(candidate):
            return candidate, comps[index:]
    return None, comps


def _join_tail(final: str, tail: list[str]) -> str:
    """Append unresolved components. A drive path keeps backslashes on any OS."""
    stripped = _strip_extended(final)
    if isinstance(stripped, str) and len(stripped) >= 2 and stripped[1] == ":":
        return stripped.rstrip("\\/") + "\\" + "\\".join(tail)
    joined = Path(stripped)
    for part in tail:
        joined = joined.joinpath(part)
    return str(joined)


def resolve_existing_path(path: str, exists=None, final_path=None) -> str:
    """Resolve the deepest existing ancestor and append any missing tail.

    Windows uses GetFinalPathNameByHandle. POSIX uses os.path.realpath.
    The bare drive is not opened, so a missing ``D:\\Velvet\\...`` tree stays
    lexical. An ancestor that exists but cannot be resolved fails closed.
    """
    if not isinstance(path, str) or not path:
        return path
    probe = os.path.lexists if exists is None else exists
    if final_path is None:
        final_path = _windows_final_path if os.name == "nt" else os.path.realpath
    ancestor, tail = _deepest_existing(path, probe)
    if ancestor is None:
        return path
    try:
        final = final_path(ancestor)
    except OSError as exc:
        raise StorageRefusal("SANDBOX_PATH_UNRESOLVED") from exc
    if not isinstance(final, str) or not final:
        raise StorageRefusal("SANDBOX_PATH_UNRESOLVED")
    if not tail:
        return final
    return _join_tail(final, tail)


def assert_under_velvet(root: str, resolve=None, exists=None, final_path=None) -> None:
    """Require a subdirectory of D:\\Velvet after junctions and symlinks resolve.

    D:\\Velvet itself is refused. The deepest existing ancestor is resolved
    before the drive and prefix checks, so a new directory cannot escape
    through a link that already exists under D:\\Velvet.
    """
    if not isinstance(root, str) or not root.strip():
        raise StorageRefusal("SANDBOX_NOT_ON_D:ROOT")
    try:
        if resolve is not None:
            final = resolve(root)
        else:
            final = resolve_existing_path(root, exists=exists, final_path=final_path)
    except StorageRefusal:
        raise
    except OSError as exc:
        raise StorageRefusal("SANDBOX_PATH_UNRESOLVED") from exc
    if not isinstance(final, str) or not final.strip():
        raise StorageRefusal("SANDBOX_PATH_UNRESOLVED")
    final = _strip_extended(final)
    if not on_drive_d(final):
        raise StorageRefusal("SANDBOX_NOT_ON_D:ROOT")
    if _same(final, VELVET_ROOT):
        raise StorageRefusal("SANDBOX_ROOT_IS_VELVET")
    if not under_root(final, VELVET_ROOT):
        raise StorageRefusal("SANDBOX_OUTSIDE_VELVET")


def sandbox_temp_dir(root: str) -> str:
    return root.rstrip("\\/") + "\\tmp"


def profile_temp_dir(root: str) -> str:
    return root.rstrip("\\/") + "\\AppData\\Local\\Temp"


def assert_temp_will_not_fall_through(root: str, exists) -> None:
    """CPython skips a TEMP that is not there and can land on %SYSTEMROOT%\\Temp."""
    if not exists(sandbox_temp_dir(root)) or not exists(profile_temp_dir(root)):
        raise StorageRefusal("SANDBOX_TEMP_ABSENT")


def prepare_sandbox_temp(root: str, mkdir=None, exists=None, resolve=None) -> None:
    """Create the sandbox temp dirs before import crewai.

    crewai_core.lock_store names its file lock ``crewai:{md5}.lock``. On
    Windows the colon is an NTFS alternate-data-stream separator, so
    portalocker creates a 0-byte file whose name is ``crewai``. If the
    sandbox temp directory does not exist, gettempdir() skips TEMP/TMP and
    a SYSTEM process lands on C:\\Windows\\Temp. Each temp path is resolved
    before mkdir and again after, so a junction ancestor cannot create it
    off D:\\Velvet.
    """
    assert_under_velvet(root, resolve=resolve)
    targets = [sandbox_temp_dir(root), profile_temp_dir(root)]
    # Refuse a junction before mkdir creates through it.
    for path in targets:
        assert_under_velvet(path, resolve=resolve)
    if mkdir is None:
        if os.name != "nt":
            raise StorageRefusal("SANDBOX_TEMP_ABSENT")

        def mkdir(path: str) -> None:
            Path(path).mkdir(parents=True, exist_ok=True)

    for path in targets:
        mkdir(path)
    # The created directory can resolve somewhere else than the lexical name.
    for path in targets:
        assert_under_velvet(path, resolve=resolve)
    if exists is None:
        if os.name != "nt":
            raise StorageRefusal("SANDBOX_TEMP_ABSENT")
        return
    assert_temp_will_not_fall_through(root, exists)


def ads_host_basename(lock_filename: str) -> str:
    """Return the file Windows creates when the lock name contains a colon."""
    base = lock_filename.replace("/", "\\").split("\\")[-1]
    if base.lower().endswith(".lock"):
        base = base[: -len(".lock")]
    if ":" in base:
        base = base.split(":", 1)[0]
    return base


def system_temp_crewai(system_root: str = "C:\\Windows") -> str:
    return system_root.rstrip("\\/") + "\\Temp\\crewai"


def assert_no_system_temp_crewai(exists, system_root: str = "C:\\Windows") -> None:
    """Refuse the 0-byte ADS host file outside the sandbox."""
    if exists(system_temp_crewai(system_root)):
        raise StorageRefusal("WINDOWS_TEMP_CREWAI")


def refuse_operator_env(env: dict) -> None:
    """Refuse a present wrong OLLAMA_HOST or proxy. Absent keys may be filled.

    Names are compared case-insensitively. Https_Proxy is the same variable
    as HTTPS_PROXY, and ollama_host is the same variable as OLLAMA_HOST.
    """
    if not isinstance(env, dict):
        raise StorageRefusal("SANDBOX_ENV_ABSENT")
    for name, value in _protected_hits(env, "OLLAMA_HOST"):
        if isinstance(value, str) and value.strip() and value != APPROVED_OLLAMA_HOST:
            raise StorageRefusal("OLLAMA_HOST_REFUSED")
    for key, want in PROXY_KEYS.items():
        for name, value in _protected_hits(env, key):
            if not isinstance(value, str) or not value.strip():
                continue
            if value != want:
                raise StorageRefusal("E5_PROXY_MISMATCH:" + name)


def bind_process_sandbox(env: dict | None = None, root: str = SANDBOX_ROOT) -> dict:
    """Install the sandbox variables. Refuse before any assignment when the root is off D:."""
    assert_under_velvet(root)
    ready = {} if env is None else dict(env)
    refuse_operator_env(ready)
    ready.update(approved_environment(root))
    assert_sandbox_env(ready, root)
    for key, value in approved_environment(root).items():
        os.environ[key] = value
    for key in FORBIDDEN_ENV:
        os.environ.pop(key, None)
    return ready
