"""D: sandbox environment for the CrewAI pilot. Does not import crewai."""
from __future__ import annotations

import os
from pathlib import Path

from office_v2_crewai.contract import APPROVED_OLLAMA_HOST, SANDBOX_ROOT


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


def assert_proxy_env(env: dict) -> None:
    """E5 tripwire. Anything other than the dead loopback proxy is a refusal."""
    if not isinstance(env, dict):
        raise StorageRefusal("E5_PROXY_ABSENT")
    for key, want in PROXY_KEYS.items():
        for name in (key, key.lower()):
            value = env.get(name)
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


def bind_process_sandbox(env: dict | None = None, root: str = SANDBOX_ROOT) -> dict:
    """Install the sandbox variables. Refuse before any assignment when the root is off D:."""
    if not on_drive_d(root):
        raise StorageRefusal("SANDBOX_NOT_ON_D:ROOT")
    if not _same(root, SANDBOX_ROOT):
        raise StorageRefusal("SANDBOX_OUTSIDE_ROOT:ROOT")
    ready = {} if env is None else dict(env)
    ready.update(approved_environment(root))
    assert_sandbox_env(ready, root)
    for key, value in approved_environment(root).items():
        os.environ[key] = value
    for key in FORBIDDEN_ENV:
        os.environ.pop(key, None)
    return ready
