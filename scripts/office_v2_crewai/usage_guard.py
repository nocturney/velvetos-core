"""Enforce the E3 accept-risk conditions. Does not import crewai."""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

from office_v2_crewai.contract import (
    APPROVED_MODEL,
    CREWAI_TOOLS_NA,
    CREWAI_VERSION,
    E3_CONDITIONS,
    LOCK_SHA256,
    LOCK_WHEEL_COUNT,
    MCP_ADVISORY,
    MCP_INSTALLED,
    MCP_NOT_AFFECTED,
    PUBLIC_ISSUE_PREFIX,
    PYSEC_CVE_MAP,
    TRACE_USER_BYTES,
    ZDI_FROM_REPOSITORY,
    ZDI_FROM_REPOSITORY_CVE,
)

# Packages that must stay out of the pilot. fastapi is already an E3 module
# refusal; the others are the drift set from comment 6250954627.
DRIFT_FORBIDDEN_MODULES = ("litellm", "tiktoken", "posthog", "crewai_tools", "fastapi")

# Redirected profile leftovers. The expected state is that none of these exist.
LEFTOVER_RELS = (
    ".config\\crewai\\settings.json",
    "tmp\\crewai_settings.json",
    "crewai_settings.json",
    ".cache\\chroma\\telemetry_user_id",
)

_LISTEN_STATES = {"listen", "listening"}
# Absolute OS paths only. A name on PATH is not proof: an earlier fake can
# report zero listeners. Missing files stay unproven.
DARWIN_LSOF = "/usr/sbin/lsof"
DARWIN_NETSTAT = "/usr/bin/netstat"
WINDOWS_NETSTAT = "C:\\Windows\\System32\\netstat.exe"
WINDOWS_POWERSHELL = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
WINDOWS_LISTENER_PATH = "C:\\Windows\\System32;C:\\Windows\\System32\\WindowsPowerShell\\v1.0"
WINDOWS_SYSTEM_ROOT = "C:\\Windows"


class UsageRefusal(RuntimeError):
    """A pilot usage condition failed closed. No PASS is recorded."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.detail = detail


def _unproven(detail: str) -> UsageRefusal:
    """Same refusal code, with a stable detail for the receipt."""
    return UsageRefusal("PILOT_LISTENER_UNPROVEN", detail)


def listener_reason(probe: str, kind: str, rc: object = None, stdout: object = None) -> str:
    """One ASCII refusal line. Output text and environment values stay out.

    ``kind`` is ``missing``, ``open``, ``empty``, ``parse``, ``pid-absent``,
    ``child``, or ``status``. ``status`` records only the exit code and
    whether stdout was empty.
    """
    if probe not in ("netstat", "toolhelp"):
        probe = "listener"
    if kind == "missing":
        return "probe=%s missing" % probe
    if kind == "open":
        return "probe=%s open" % probe
    if kind == "empty":
        return "probe=%s empty" % probe
    if kind == "parse":
        return "probe=%s parse" % probe
    if kind == "pid-absent":
        return "probe=%s pid-absent" % probe
    if kind == "child":
        name = rc if isinstance(rc, str) and rc.isalpha() else "error"
        return "probe=%s child=%s" % (probe, name)
    if kind == "status":
        if isinstance(rc, bool) or not isinstance(rc, int) or rc < 0 or rc > 255:
            code = "bad"
        else:
            code = str(rc)
        empty = "empty" if not isinstance(stdout, str) or not stdout.strip() else "present"
        return "probe=%s rc=%s stdout=%s" % (probe, code, empty)
    return "probe=%s unknown" % probe


def module_is_forbidden(name: str) -> bool:
    """Flag server stacks and drift packages. The chromadb package itself is not forbidden."""
    if not isinstance(name, str) or not name:
        return False
    if name == "chromadb.server" or name.startswith("chromadb.server."):
        return True
    for prefix in E3_CONDITIONS["forbid_loaded_modules"]:
        if prefix == "chromadb.server":
            continue
        if name == prefix or name.startswith(prefix + "."):
            return True
    for prefix in DRIFT_FORBIDDEN_MODULES:
        if name == prefix or name.startswith(prefix + "."):
            return True
    return False


def assert_dependency_drift(find_spec=None) -> None:
    """Refuse a pilot environment that has drifted in a forbidden package.

    find_spec returning a module spec is BLOCKED_SECURITY. A name later found
    in sys.modules is FORBIDDEN_MODULE_LOADED via assert_post_run.
    """
    import importlib.util

    finder = importlib.util.find_spec if find_spec is None else find_spec
    for name in DRIFT_FORBIDDEN_MODULES:
        try:
            spec = finder(name)
        except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
            spec = None
        if spec is not None:
            raise UsageRefusal("BLOCKED_SECURITY")


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, bytes)):
        return False
    try:
        return len(value) == 0
    except TypeError:
        return False


def assert_crew_spec(spec: dict) -> None:
    if spec.get("memory") is not False:
        raise UsageRefusal("MEMORY_NOT_DISABLED")
    if spec.get("knowledge") or spec.get("knowledge_sources") or spec.get("rag"):
        raise UsageRefusal("KNOWLEDGE_OR_RAG_REFUSED")
    if spec.get("tools"):
        raise UsageRefusal("TOOLS_NOT_EMPTY")
    if spec.get("mcps") or spec.get("mcp_servers"):
        raise UsageRefusal("MCP_SERVERS_REFUSED")
    if spec.get("crewai_tools"):
        raise UsageRefusal("CREWAI_TOOLS_REFUSED")
    if spec.get("from_repository") is not None:
        raise UsageRefusal("FROM_REPOSITORY_REFUSED")


def _assert_built_agent(agent) -> None:
    if getattr(agent, "from_repository", "missing") is not None:
        raise UsageRefusal("FROM_REPOSITORY_REFUSED")
    if not _is_empty(getattr(agent, "tools", "missing")):
        raise UsageRefusal("TOOLS_NOT_EMPTY")
    if not _is_empty(getattr(agent, "mcps", None)) or not _is_empty(getattr(agent, "mcp_servers", None)):
        raise UsageRefusal("MCP_SERVERS_REFUSED")
    if not _is_empty(getattr(agent, "knowledge", None)) or not _is_empty(getattr(agent, "knowledge_sources", None)):
        raise UsageRefusal("KNOWLEDGE_OR_RAG_REFUSED")


def assert_built_crew(agents, crew) -> None:
    """Check the constructed Agent and Crew objects, not the spec dict."""
    if not isinstance(agents, (list, tuple)):
        raise UsageRefusal("CREW_SHAPE_REFUSED")
    rows = list(agents)
    attached = getattr(crew, "agents", None)
    if isinstance(attached, (list, tuple)):
        rows.extend(attached)
    if not rows:
        raise UsageRefusal("CREW_SHAPE_REFUSED")
    seen = []
    for agent in rows:
        if any(agent is item for item in seen):
            continue
        seen.append(agent)
        _assert_built_agent(agent)
    if getattr(crew, "memory", True) is not False:
        raise UsageRefusal("MEMORY_NOT_DISABLED")
    if getattr(crew, "tracing", True) is not False:
        raise UsageRefusal("TRACING_NOT_DISABLED")


def assert_trace_consent(path: Path, expected: bytes = TRACE_USER_BYTES) -> None:
    """The first-run file must exist, refuse trace upload, and stay byte-identical."""
    target = Path(path)
    if not target.is_file():
        raise UsageRefusal("TRACE_CONSENT_ABSENT")
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise UsageRefusal("TRACE_CONSENT_ABSENT") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise UsageRefusal("TRACE_CONSENT_CHANGED") from exc
    if isinstance(data, dict) and data.get("trace_consent") is True:
        raise UsageRefusal("TRACE_CONSENT_TRUE")
    if raw != expected:
        raise UsageRefusal("TRACE_CONSENT_CHANGED")


def seed_trace_consent(storage_dir: Path) -> Path:
    """Write the consent file before import. Do not overwrite an opted-in file."""
    root = Path(storage_dir)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise UsageRefusal("TRACE_CONSENT_ABSENT") from exc
    if not root.is_dir():
        raise UsageRefusal("TRACE_CONSENT_ABSENT")
    path = root / ".crewai_user.json"
    if path.is_file():
        try:
            current = json.loads(path.read_bytes().decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            current = None
        if isinstance(current, dict) and current.get("trace_consent") is True:
            raise UsageRefusal("TRACE_CONSENT_TRUE")
    try:
        path.write_bytes(TRACE_USER_BYTES)
    except OSError as exc:
        raise UsageRefusal("TRACE_CONSENT_ABSENT") from exc
    assert_trace_consent(path)
    return path


def assert_no_pilot_leftovers(root: Path | str) -> None:
    """Fail when a redirected settings or chroma telemetry file is present."""
    base = Path(root)
    for rel in LEFTOVER_RELS:
        path = base.joinpath(*rel.split("\\"))
        if path.exists():
            raise UsageRefusal("LEFTOVER_FILE:" + rel)


def _advisory_rows(value) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        raise UsageRefusal("SUPPLY_CHAIN_RECORD_INVALID")
    return value


def assert_supply_chain_record(document: dict) -> None:
    """Advisory hygiene for comment 6250954627. Does not change the lock pin."""
    if not isinstance(document, dict):
        raise UsageRefusal("SUPPLY_CHAIN_RECORD_INVALID")
    if document.get("lock_sha256") != LOCK_SHA256 or document.get("wheel_count") != LOCK_WHEEL_COUNT:
        raise UsageRefusal("LOCK_IDENTITY_MISMATCH")
    if document.get("scan_status") != "RED":
        raise UsageRefusal("MCP_59951_NOT_RED")
    if document.get("cve_map") != PYSEC_CVE_MAP:
        raise UsageRefusal("PYSEC_CVE_MAP_MISMATCH")
    absent = _advisory_rows(document.get("absent_from_lock"))
    if not any(
        isinstance(row, dict) and row.get("package") == "fastapi" and row.get("in_lock") is False
        for row in absent
    ):
        raise UsageRefusal("FASTAPI_NOT_RECORDED")
    na = {}
    for row in _advisory_rows(document.get("not_applicable")):
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            na[row["id"]] = row
    for cve in CREWAI_TOOLS_NA:
        row = na.get(cve)
        if not isinstance(row, dict) or row.get("package") != "crewai-tools" or row.get("status") != "N-A":
            raise UsageRefusal("CREWAI_TOOLS_CVE_NOT_NA")
    unaffected = {}
    for row in _advisory_rows(document.get("not_affected")):
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            unaffected[row["id"]] = row
            if row["id"] == MCP_ADVISORY:
                raise UsageRefusal("MCP_59951_NOT_RED")
    for cve in MCP_NOT_AFFECTED:
        row = unaffected.get(cve)
        if (
            not isinstance(row, dict)
            or row.get("package") != "mcp"
            or row.get("version") != MCP_INSTALLED
            or row.get("status") != "NOT_AFFECTED"
        ):
            raise UsageRefusal("MCP_ADVISORY_STATUS_MISMATCH")
    red = False
    for row in _advisory_rows(document.get("advisories")):
        if not isinstance(row, dict):
            continue
        ids = row.get("ids")
        if isinstance(ids, list) and MCP_ADVISORY in ids:
            red = True
            if row.get("package") != "mcp" or row.get("version") != MCP_INSTALLED:
                raise UsageRefusal("MCP_59951_NOT_RED")
    if not red:
        raise UsageRefusal("MCP_59951_NOT_RED")
    found = False
    for row in _advisory_rows(document.get("present_in_pin")):
        if not isinstance(row, dict) or row.get("id") != ZDI_FROM_REPOSITORY:
            continue
        found = True
        if (
            row.get("cve") != ZDI_FROM_REPOSITORY_CVE
            or row.get("package") != "crewai"
            or row.get("version") != CREWAI_VERSION
            or row.get("reach") != "unreachable"
        ):
            raise UsageRefusal("ZDI_26_706_RECORD_ABSENT")
    if not found:
        raise UsageRefusal("ZDI_26_706_RECORD_ABSENT")


def assert_not_chroma_cli(argv: list) -> None:
    if not isinstance(argv, list):
        raise UsageRefusal("CHROMA_CLI_REFUSED")
    for index, part in enumerate(argv):
        if not isinstance(part, str):
            raise UsageRefusal("CHROMA_CLI_REFUSED")
        base = part.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if base in {"chroma", "chroma.exe", "chroma.cmd", "chroma.bat"}:
            raise UsageRefusal("CHROMA_CLI_REFUSED")
        if part == "-m" and index + 1 < len(argv):
            nxt = argv[index + 1]
            if isinstance(nxt, str) and (
                nxt == "chroma" or nxt.startswith("chromadb.server") or nxt.startswith("chromadb.cli")
            ):
                raise UsageRefusal("CHROMA_CLI_REFUSED")


def assert_loaded_modules(modules: dict) -> None:
    """Refuse forbidden modules before any listener observation is attempted."""
    if any(module_is_forbidden(name) for name in modules):
        raise UsageRefusal("FORBIDDEN_MODULE_LOADED")


def assert_post_run(modules: dict, listening_ports: int, commands: list | None = None) -> None:
    for argv in commands or []:
        assert_not_chroma_cli(argv)
    assert_loaded_modules(modules)
    if listening_ports != 0:
        raise UsageRefusal("PILOT_LISTENER_PRESENT")


def guard_post_run(modules: dict, observe, commands: list | None = None, receipt: dict | None = None) -> int:
    """Check modules first. A listener failure must not hide a forbidden import."""
    for argv in commands or []:
        assert_not_chroma_cli(argv)
    assert_loaded_modules(modules)
    try:
        ports = observe()
    except UsageRefusal as exc:
        if receipt is not None:
            teardown = receipt.setdefault("teardown", {})
            teardown["listener_count"] = None
            teardown["listener_source"] = "UNPROVEN"
            detail = getattr(exc, "detail", None)
            if isinstance(detail, str) and detail:
                teardown["listener_detail"] = detail
        raise
    if receipt is not None:
        teardown = receipt.setdefault("teardown", {})
        teardown["listener_count"] = ports
        teardown["listener_source"] = "OBSERVED"
    if ports != 0:
        raise UsageRefusal("PILOT_LISTENER_PRESENT")
    return ports


def assert_interpreter_isolated(flags=None) -> None:
    """The pilot process must be python -I. User site and environment hooks stay off."""
    current = sys.flags if flags is None else flags
    if (
        not getattr(current, "isolated", 0)
        or not getattr(current, "ignore_environment", 0)
        or not getattr(current, "no_user_site", 0)
    ):
        raise UsageRefusal("PYTHON_ISOLATION_REFUSED")


def _env_value(env: dict, name: str):
    for key, value in env.items():
        if isinstance(key, str) and key.upper() == name:
            if isinstance(value, str) and value.strip():
                return value
    return None


def _prefix_bases() -> list[str]:
    bases = []
    for base in (getattr(sys, "base_prefix", ""), getattr(sys, "prefix", "")):
        if isinstance(base, str) and base:
            bases.append(base.replace("\\", "/").casefold().rstrip("/") + "/")
    return bases


def _under_prefix(path: str) -> bool:
    norm = path.replace("\\", "/").casefold()
    return any(norm.startswith(base) for base in _prefix_bases())


def _assert_customize(module, reason: str) -> None:
    if module is None:
        return
    path = getattr(module, "__file__", None)
    if not isinstance(path, str) or not path:
        raise UsageRefusal(reason)
    norm = path.replace("\\", "/").casefold()
    if norm.endswith(".pth"):
        raise UsageRefusal("PTH_REFUSED")
    if "/site-packages/" in norm or not _under_prefix(path):
        raise UsageRefusal(reason)


def _live_pth_files() -> list[str]:
    found = []
    for entry in sys.path:
        if not isinstance(entry, str) or not entry:
            continue
        path = Path(entry)
        try:
            if path.is_file() and path.suffix.lower() == ".pth" and not _under_prefix(str(path)):
                found.append(str(path))
            if path.is_dir():
                found.extend(str(hit) for hit in path.glob("*.pth") if not _under_prefix(str(hit)))
        except OSError:
            continue
    return found


def assert_no_pythonpath(env: dict, modules: dict | None = None, pth_files: list | None = None) -> None:
    """Refuse interpreter hooks that can load code before the runner's guards.

    python -I is the process boundary. This still refuses PYTHONPATH,
    PYTHONHOME, PYTHONUSERBASE, a foreign sitecustomize or usercustomize,
    and a .pth file outside the interpreter prefix.
    """
    if isinstance(env, dict):
        if _env_value(env, "PYTHONPATH") is not None:
            raise UsageRefusal("PYTHONPATH_REFUSED")
        if _env_value(env, "PYTHONHOME") is not None:
            raise UsageRefusal("PYTHONHOME_REFUSED")
        if _env_value(env, "PYTHONUSERBASE") is not None:
            raise UsageRefusal("PYTHONUSERBASE_REFUSED")
    loaded = sys.modules if modules is None else modules
    if isinstance(loaded, dict):
        _assert_customize(loaded.get("sitecustomize"), "SITECUSTOMIZE_REFUSED")
        _assert_customize(loaded.get("usercustomize"), "USERCUSTOMIZE_REFUSED")
    files = _live_pth_files() if pth_files is None and modules is None else (pth_files or [])
    for path in files:
        if not isinstance(path, str) or not path:
            raise UsageRefusal("PTH_REFUSED")
        if not path.replace("\\", "/").casefold().endswith(".pth") or not _under_prefix(path):
            raise UsageRefusal("PTH_REFUSED")


def assert_kickoff_cites_rows(text: str, rows: object = None) -> None:
    """Require a data row whose URLs are issue URLs from the input rows."""
    if not isinstance(text, str) or not text.strip():
        raise UsageRefusal("KICKOFF_EMPTY_TABLE")
    folded = " ".join(text.split()).casefold()
    if "no rows were provided" in folded:
        raise UsageRefusal("KICKOFF_EMPTY_TABLE")
    data = _table_data_rows(text)
    if not data or _rows_are_blank(data):
        raise UsageRefusal("KICKOFF_EMPTY_TABLE")
    allowed = _input_issue_urls(rows)
    cited = _cited_urls(text)
    if not cited:
        raise UsageRefusal("KICKOFF_UNCITED_ROW")
    for url in cited:
        if url not in allowed or not url.startswith(PUBLIC_ISSUE_PREFIX):
            raise UsageRefusal("KICKOFF_UNCITED_ROW")


_EMPTY_CELLS = {"n/a", "unknown", "na", "none", "-", ""}


def _table_data_rows(text: str) -> list:
    parsed = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if all(cell and set(cell) <= set("-: ") for cell in cells):
            continue
        parsed.append(cells)
    if not parsed:
        return []
    header_is_real = any(cell.casefold() not in _EMPTY_CELLS for cell in parsed[0])
    return parsed[1:] if header_is_real else parsed


def _rows_are_blank(rows: list) -> bool:
    return all(all(cell.casefold() in _EMPTY_CELLS for cell in row) for row in rows)


def _cited_urls(text: str) -> list[str]:
    found = []
    for token in text.replace("|", " ").replace("(", " ").replace(")", " ").split():
        if not token.startswith("https://") and not token.startswith("http://"):
            continue
        found.append(token.rstrip(".,;"))
    return found


def _input_issue_urls(rows: object) -> set[str]:
    if isinstance(rows, str):
        try:
            document = json.loads(rows)
        except json.JSONDecodeError as exc:
            raise UsageRefusal("KICKOFF_UNCITED_ROW") from exc
    elif isinstance(rows, dict):
        document = rows
    else:
        raise UsageRefusal("KICKOFF_UNCITED_ROW")
    issues = document.get("issues") if isinstance(document, dict) else None
    if not isinstance(issues, list):
        raise UsageRefusal("KICKOFF_UNCITED_ROW")
    found = set()
    for row in issues:
        if isinstance(row, dict) and isinstance(row.get("url"), str):
            found.add(row["url"])
    return found


def _as_int(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    return value


def _rows(value) -> list:
    if value is None:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    raise UsageRefusal("PILOT_LISTENER_UNPROVEN")


def process_tree(processes: list, root_pid: int) -> set[int]:
    """Pilot pid plus descendants. A missing root is unproven, not zero."""
    by_parent: dict[int, list[int]] = {}
    seen: set[int] = set()
    for row in processes:
        if not isinstance(row, dict):
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
        pid = _as_int(row.get("pid"))
        ppid = _as_int(row.get("ppid"))
        seen.add(pid)
        by_parent.setdefault(ppid, []).append(pid)
    if root_pid not in seen:
        raise _unproven(listener_reason("toolhelp", "pid-absent"))
    selected = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid in list(selected):
            for child in by_parent.get(pid, []):
                if child not in selected:
                    selected.add(child)
                    changed = True
    return selected


def parse_netstat(text: str) -> dict:
    """Parse `netstat -ano`. A header with no rows is a proven empty set."""
    if not isinstance(text, str) or "Active Connections" not in text:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    tcp = []
    udp = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        proto = parts[0].upper()
        if proto == "TCP":
            if len(parts) < 5:
                raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
            try:
                pid = int(parts[-1])
            except ValueError as exc:
                raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
            tcp.append({"pid": pid, "state": parts[-2]})
        elif proto == "UDP":
            try:
                pid = int(parts[-1])
            except ValueError as exc:
                raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
            udp.append({"pid": pid})
    return {"tcp": tcp, "udp": udp}


def _normalize_windows(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    processes = _rows(payload.get("processes"))
    if "netstat" in payload:
        parsed = parse_netstat(payload.get("netstat"))
        return {"processes": processes, "tcp": parsed["tcp"], "udp": parsed["udp"]}
    if "tcp" not in payload or "udp" not in payload:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    return {"processes": processes, "tcp": _rows(payload.get("tcp")), "udp": _rows(payload.get("udp"))}


def count_windows_listeners(pid: int, observation: dict) -> int:
    """TCP listeners plus UDP endpoints owned by the pilot process tree."""
    root = _as_int(pid)
    if root <= 0:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    normalized = _normalize_windows(observation)
    tree = process_tree(normalized["processes"], root)
    owned = 0
    for row in normalized["tcp"]:
        if not isinstance(row, dict):
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
        owner = _as_int(row.get("pid"))
        state = row.get("state")
        if not isinstance(state, str):
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
        if owner in tree and state.strip().lower() in _LISTEN_STATES:
            owned += 1
    for row in normalized["udp"]:
        if not isinstance(row, dict):
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
        if _as_int(row.get("pid")) in tree:
            owned += 1
    return owned


def _open_trusted_regular(path: str) -> int:
    """Open one absolute regular file and return its fd. Symlinks are refused.

    ``O_NOFOLLOW`` fails the open when the final path entry is a symlink.
    ``fstat`` on that fd must match a later ``stat`` of the same path, so a
    directory entry swapped for a different inode is not the opened file.
    Unix execution uses this fd (``/proc/self/fd`` or ``/dev/fd``). Windows
    has no fd exec, so the path is executed after this check. Replacing
    ``System32\\netstat.exe`` in that remaining gap is the same privilege as
    replacing the OS binary.
    """
    if not isinstance(path, str) or not os.path.isabs(path):
        raise OSError("trusted listener binary missing")
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    # Windows CRT does not implement O_NOFOLLOW. Passing the flag, when a
    # later Python defines it, makes os.open of netstat.exe fail and every
    # live proof becomes PILOT_LISTENER_UNPROVEN. Symlinks are refused below.
    if hasattr(os, "O_NOFOLLOW") and os.name != "nt":
        flags |= os.O_NOFOLLOW
    if os.name == "nt" and hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise OSError("trusted listener binary missing") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError("trusted listener binary missing")
        listed = os.lstat(path)
        if stat.S_ISLNK(listed.st_mode):
            raise OSError("trusted listener binary missing")
        current = os.stat(path)
        if (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino):
            raise OSError("trusted listener binary missing")
        if os.name == "nt":
            final = os.path.normcase(_strip_nt_prefix(os.path.realpath(path)))
            expected = os.path.normcase(_strip_nt_prefix(os.path.abspath(path)))
            if final != expected:
                raise OSError("trusted listener binary missing")
    except OSError:
        os.close(fd)
        raise
    return fd


def _fd_executable(fd: int) -> str | None:
    """Path that executes the opened inode, or None where fd exec is unavailable."""
    if os.name == "nt":
        return None
    if os.path.isdir("/proc/self/fd"):
        return "/proc/self/fd/%d" % fd
    if os.path.isdir("/dev/fd"):
        return "/dev/fd/%d" % fd
    return None


def trusted_listener_binary(tool: str, platform: str | None = None) -> str | None:
    """Return one absolute OS binary, or None when that file is not present.

    Never searches PATH. A symlink at the trusted path is not a binary.
    """
    plat = sys.platform if platform is None else platform
    if tool == "lsof" and plat == "darwin":
        candidate = DARWIN_LSOF
    elif tool == "netstat" and plat == "darwin":
        candidate = DARWIN_NETSTAT
    elif tool == "netstat" and plat == "win32":
        candidate = WINDOWS_NETSTAT
    elif tool == "powershell" and plat == "win32":
        candidate = WINDOWS_POWERSHELL
    else:
        return None
    try:
        fd = _open_trusted_regular(candidate)
    except OSError:
        return None
    os.close(fd)
    return candidate


def _strip_nt_prefix(path: str) -> str:
    """Drop the ``\\\\?\\`` prefix GetFinalPathNameByHandle can leave on."""
    if not isinstance(path, str):
        return path
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[8:]
    if path.startswith("\\\\?\\"):
        return path[4:]
    return path


def windows_tool_env(base: dict) -> dict:
    """Environment for a System32 listener tool.

    The kickoff sensor clears ``os.environ`` down to the sandbox map, which
    drops ``SystemRoot``. ``netstat.exe`` then cannot start, and the proof
    stays unproven. The child always receives ``C:\\Windows`` for
    ``SystemRoot`` and ``windir``. A sandbox value cannot redirect it.
    """
    if not isinstance(base, dict):
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN", "TOOL_ENV")
    env = dict(base)
    env["SystemRoot"] = WINDOWS_SYSTEM_ROOT
    env["SYSTEMROOT"] = WINDOWS_SYSTEM_ROOT
    env["windir"] = WINDOWS_SYSTEM_ROOT
    return env


def run_trusted_listener(binary: str, args: list[str], path_value: str | None = None):
    """Run an absolute listener tool. PATH is only that binary's directory.

    The process image is the inode opened above. A later replacement of the
    path does not change which file runs, except on Windows (see
    ``_open_trusted_regular``). On Windows the child ``SystemRoot`` is
    ``C:\\Windows``.
    """
    import subprocess

    if not isinstance(binary, str) or not args or args[0] != binary:
        raise OSError("trusted listener binary missing")
    fd = _open_trusted_regular(binary)
    env = os.environ.copy()
    env["PATH"] = str(Path(binary).parent) if path_value is None else path_value
    if os.name == "nt":
        env = windows_tool_env(env)
    executable = _fd_executable(fd)
    kwargs = {
        "capture_output": True,
        "text": True,
        "timeout": 30,
        "check": False,
        "env": env,
    }
    if executable is not None:
        kwargs["executable"] = executable
        kwargs["pass_fds"] = (fd,)
    try:
        return subprocess.run(args, **kwargs)
    finally:
        os.close(fd)


def parse_process_lines(text: str) -> list:
    """Parse ``pid ppid`` lines. Empty or non-integer text is unproven."""
    if not isinstance(text, str) or not text.strip():
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError as exc:
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
        rows.append({"pid": pid, "ppid": ppid})
    if not rows:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    return rows


def _windows_processes() -> list:
    """Pid and parent pid from Toolhelp. No PowerShell and no code page.

    ``ULONG_PTR`` is pointer-sized, so the heap field is ``c_size_t``. A
    wrong layout would hide the pilot pid and stay unproven.
    """
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    snap = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    invalid = wintypes.HANDLE(-1).value
    if snap in (None, 0, -1, invalid):
        raise _unproven(listener_reason("toolhelp", "open"))
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snap, ctypes.byref(entry)):
            raise _unproven(listener_reason("toolhelp", "empty"))
        rows = []
        while True:
            rows.append({
                "pid": int(entry.th32ProcessID),
                "ppid": int(entry.th32ParentProcessID),
            })
            if not kernel32.Process32NextW(snap, ctypes.byref(entry)):
                break
        if not rows:
            raise _unproven(listener_reason("toolhelp", "empty"))
        return rows
    finally:
        kernel32.CloseHandle(snap)


def _windows_observe(spawn=None) -> dict:
    """Prove listeners with absolute ``netstat.exe -ano``. Never guess zero.

    Socket rows come from ``C:\\Windows\\System32\\netstat.exe``. The pilot
    tree comes from Toolhelp, not a PowerShell census. A missing binary, a
    nonzero status, or text without the English ``Active Connections`` header
    stays unproven. A localized Windows UI, including Hebrew on Chris, does
    not print that header.
    """
    import subprocess

    if spawn is None:
        netstat = trusted_listener_binary("netstat", "win32")
        if netstat != WINDOWS_NETSTAT:
            raise _unproven(listener_reason("netstat", "missing"))
        try:
            net = run_trusted_listener(
                netstat, [netstat, "-ano"], path_value=str(Path(netstat).parent),
            )
            processes = _windows_processes()
        except UsageRefusal:
            raise
        except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
            raise _unproven(listener_reason("netstat", "child", rc=type(exc).__name__)) from exc
        net_out, net_rc = net.stdout or "", net.returncode
        if isinstance(net_rc, bool) or not isinstance(net_rc, int) or net_rc != 0:
            raise _unproven(listener_reason("netstat", "status", rc=net_rc, stdout=net_out))
        if not isinstance(net_out, str) or "Active Connections" not in net_out:
            raise _unproven(listener_reason("netstat", "parse"))
        try:
            parsed = parse_netstat(net_out)
        except UsageRefusal as exc:
            raise _unproven(listener_reason("netstat", "parse")) from exc
        return {"processes": processes, "tcp": parsed["tcp"], "udp": parsed["udp"]}
    net_out, net_rc, proc_out, proc_rc = spawn(WINDOWS_NETSTAT)
    if isinstance(net_rc, bool) or not isinstance(net_rc, int) or net_rc != 0:
        raise _unproven(listener_reason("netstat", "status", rc=net_rc, stdout=net_out))
    if isinstance(proc_rc, bool) or not isinstance(proc_rc, int) or proc_rc != 0:
        raise _unproven(listener_reason("toolhelp", "empty"))
    try:
        parsed = parse_netstat(net_out)
    except UsageRefusal as exc:
        raise _unproven(listener_reason("netstat", "parse")) from exc
    return {
        "processes": parse_process_lines(proc_out),
        "tcp": parsed["tcp"],
        "udp": parsed["udp"],
    }


def parse_lsof_listen(text: str, pid: int) -> int:
    """Count TCP LISTEN rows for pid in `lsof -nP -iTCP -sTCP:LISTEN` output.

    A header with no data rows is a proven zero. A missing header is unproven.
    """
    if not isinstance(text, str) or isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    header = [part.upper() for part in lines[0].split()]
    if "COMMAND" not in header or "PID" not in header or "NAME" not in header:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    pid_index = header.index("PID")
    name_index = header.index("NAME")
    owned = 0
    for line in lines[1:]:
        parts = line.split()
        if len(parts) <= max(pid_index, name_index):
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
        try:
            row_pid = int(parts[pid_index])
        except ValueError as exc:
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
        name = " ".join(parts[name_index:])
        if "(LISTEN)" not in name.upper():
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
        if row_pid == pid:
            owned += 1
    return owned


def interpret_lsof(pid: int, returncode: int, stdout: str, stderr: str) -> int:
    """lsof exit 1 with empty stdout and stderr is the no-match case, a proven zero.

    Any diagnostic on stderr, or any other status, cannot prove the set is empty.
    """
    if isinstance(returncode, bool) or not isinstance(returncode, int):
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    if returncode == 1 and not stdout.strip() and not stderr.strip():
        return 0
    if returncode != 0:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    return parse_lsof_listen(stdout, pid)


def _darwin_observe(pid: int) -> int:
    """lsof for this pid only. A missing trusted binary or a bad status fails closed."""
    import subprocess

    binary = trusted_listener_binary("lsof", "darwin")
    if binary is None:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    try:
        proc = run_trusted_listener(
            binary,
            [binary, "-nP", "-a", "-p", str(pid), "-iTCP", "-sTCP:LISTEN"],
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
    return interpret_lsof(pid, proc.returncode, proc.stdout or "", proc.stderr or "")


def count_listening_sockets(pid: int, platform: str | None = None, observation: object = None,
                            observe=None) -> int:
    """Count pilot listeners. An unproven observation fails closed."""
    plat = sys.platform if platform is None else platform
    if plat == "win32":
        if observation is None:
            try:
                observation = observe() if observe is not None else _windows_observe()
            except UsageRefusal:
                raise
            except (OSError, ValueError, TypeError) as exc:
                raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
        return count_windows_listeners(pid, observation)
    if plat == "darwin":
        if isinstance(observation, str):
            return parse_lsof_listen(observation, pid)
        if observation is not None:
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
        if observe is None:
            return _darwin_observe(pid)
        try:
            result = observe()
        except UsageRefusal:
            raise
        except (OSError, ValueError, TypeError) as exc:
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
        if isinstance(result, str):
            return parse_lsof_listen(result, pid)
        if isinstance(result, tuple) and len(result) == 3:
            return interpret_lsof(pid, result[0], result[1], result[2])
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    if plat != "linux":
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    if observation is not None or observe is not None:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    return _count_linux_listeners(pid)


def _count_linux_listeners(pid: int) -> int:
    """Count TCP LISTEN sockets owned by pid via /proc. Missing /proc fails closed."""
    proc = Path("/proc")
    tcp_files = [proc / "net" / "tcp"]
    tcp6 = proc / "net" / "tcp6"
    if tcp6.is_file():
        tcp_files.append(tcp6)
    fd_dir = proc / str(pid) / "fd"
    if not isinstance(pid, int) or pid <= 0 or not tcp_files[0].is_file() or not fd_dir.is_dir():
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    inodes = set()
    for entry in fd_dir.iterdir():
        try:
            target = os.readlink(entry)
        except OSError:
            continue
        if target.startswith("socket:[") and target.endswith("]"):
            inodes.add(target[len("socket:["):-1])
    listening = set()
    for path in tcp_files:
        try:
            lines = path.read_text(encoding="ascii", errors="replace").splitlines()
        except OSError as exc:
            raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 10:
                continue
            if parts[3] == "0A" and parts[9] in inodes:
                listening.add(parts[9])
    return len(listening)


def _ok_spec() -> dict:
    return {
        "memory": False,
        "knowledge": None,
        "rag": None,
        "tools": [],
        "mcps": None,
        "crewai_tools": False,
    }


def enforcement_holds() -> bool:
    """True only when every accept-risk condition refuses a violation."""
    spec = _ok_spec()
    try:
        assert_crew_spec(spec)
        assert_post_run(
            {"chromadb": object(), "chromadb.utils.embedding_functions.openai_embedding_function": object()},
            0,
            [["python3", "-c", "print(1)"]],
        )
        assert_not_chroma_cli(["python3", "-c", "print(1)"])
    except UsageRefusal:
        return False
    bad = [
        {**spec, "memory": True},
        {**spec, "knowledge": ["source"]},
        {**spec, "rag": True},
        {**spec, "tools": ["search"]},
        {**spec, "mcps": ["server"]},
        {**spec, "crewai_tools": True},
        {**spec, "from_repository": "x"},
    ]
    for item in bad:
        try:
            assert_crew_spec(item)
        except UsageRefusal:
            continue
        return False
    for name in (
        "chromadb.server",
        "chromadb.server.app",
        "fastapi",
        "uvicorn",
        "mcp",
        "mcp.server",
        *DRIFT_FORBIDDEN_MODULES,
    ):
        try:
            assert_post_run({name: object(), "chromadb": object()}, 0, [])
        except UsageRefusal as exc:
            if str(exc) != "FORBIDDEN_MODULE_LOADED":
                return False
            continue
        return False
    for argv in (["chroma", "run"], ["C:/Tools/chroma.exe"], ["python3", "-m", "chromadb.server"]):
        try:
            assert_not_chroma_cli(argv)
        except UsageRefusal as exc:
            if str(exc) != "CHROMA_CLI_REFUSED":
                return False
            continue
        return False
    try:
        assert_post_run({"chromadb": object()}, 1, [])
    except UsageRefusal as exc:
        if str(exc) != "PILOT_LISTENER_PRESENT":
            return False
    else:
        return False
    guards = (
        lambda: assert_no_pythonpath({"PYTHONPATH": "D:\\evil"}),
        lambda: assert_no_pythonpath({"PYTHONHOME": "D:\\evil"}),
        lambda: assert_no_pythonpath({}, {"usercustomize": object()}),
        lambda: assert_no_pythonpath({}, pth_files=["D:/evil/hook.pth"]),
        lambda: assert_kickoff_cites_rows("| Issue | Status |\n| --- | --- |\n"),
        lambda: assert_interpreter_isolated(type("Flags", (), {"isolated": 0, "ignore_environment": 0, "no_user_site": 0})()),
    )
    for guard in guards:
        try:
            guard()
        except UsageRefusal:
            continue
        return False
    from office_v2_crewai.provider import ProviderRefusal, assert_ollama_bind, digest_from_tags
    try:
        assert_ollama_bind(None)
    except ProviderRefusal as exc:
        if str(exc) != "OLLAMA_BIND_UNPROVEN":
            return False
    else:
        return False
    try:
        digest_from_tags({"models": [
            {"name": APPROVED_MODEL, "digest": "aa"},
            {"name": APPROVED_MODEL, "digest": "bb"},
        ]})
    except ProviderRefusal as exc:
        if str(exc) != "MODEL_DIGEST_MISMATCH":
            return False
    else:
        return False
    return True
