"""Enforce the E3 accept-risk conditions. Does not import crewai."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from office_v2_crewai.contract import (
    CREWAI_TOOLS_NA,
    CREWAI_VERSION,
    E3_CONDITIONS,
    LOCK_SHA256,
    LOCK_WHEEL_COUNT,
    MCP_ADVISORY,
    MCP_INSTALLED,
    MCP_NOT_AFFECTED,
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
_PS_OBSERVE = (
    "$ErrorActionPreference = 'Stop'\n"
    "$processes = New-Object System.Collections.Generic.List[object]\n"
    "foreach ($row in @(Get-CimInstance -ClassName Win32_Process -ErrorAction Stop)) {\n"
    "  $processes.Add(@{ pid = [int]$row.ProcessId; ppid = [int]$row.ParentProcessId })\n"
    "}\n"
    "$tcp = New-Object System.Collections.Generic.List[object]\n"
    "$udp = New-Object System.Collections.Generic.List[object]\n"
    "$source = 'Get-Net'\n"
    "try {\n"
    "  foreach ($connection in @(Get-NetTCPConnection -ErrorAction Stop)) {\n"
    "    $tcp.Add(@{ pid = [int]$connection.OwningProcess; state = [string]$connection.State })\n"
    "  }\n"
    "  foreach ($endpoint in @(Get-NetUDPEndpoint -ErrorAction Stop)) {\n"
    "    $udp.Add(@{ pid = [int]$endpoint.OwningProcess })\n"
    "  }\n"
    "} catch {\n"
    "  $source = 'netstat'\n"
    "  $raw = & netstat.exe -ano | Out-String\n"
    "  if ($LASTEXITCODE -ne 0 -or -not $raw) { throw 'NETSTAT_FAILED' }\n"
    "  @{ processes = $processes.ToArray(); netstat = $raw; source = $source } | ConvertTo-Json -Depth 6 -Compress\n"
    "  exit 0\n"
    "}\n"
    "@{ processes = $processes.ToArray(); tcp = $tcp.ToArray(); udp = $udp.ToArray(); source = $source } | "
    "ConvertTo-Json -Depth 6 -Compress\n"
)


class UsageRefusal(RuntimeError):
    """A pilot usage condition failed closed. No PASS is recorded."""


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
    except UsageRefusal:
        if receipt is not None:
            teardown = receipt.setdefault("teardown", {})
            teardown["listener_count"] = None
            teardown["listener_source"] = "UNPROVEN"
        raise
    if receipt is not None:
        teardown = receipt.setdefault("teardown", {})
        teardown["listener_count"] = ports
        teardown["listener_source"] = "OBSERVED"
    if ports != 0:
        raise UsageRefusal("PILOT_LISTENER_PRESENT")
    return ports


def assert_no_pythonpath(env: dict, modules: dict | None = None) -> None:
    """Refuse PYTHONPATH and a sitecustomize that is not the interpreter's own.

    A distro sitecustomize under sys.prefix is left alone. A module with no
    file, or a file outside that prefix, is how a PYTHONPATH hook loaded
    chromadb.server before the runner in LAB-4 attempt 07.
    """
    if isinstance(env, dict):
        value = env.get("PYTHONPATH")
        if isinstance(value, str) and value.strip():
            raise UsageRefusal("PYTHONPATH_REFUSED")
    loaded = sys.modules if modules is None else modules
    module = loaded.get("sitecustomize") if isinstance(loaded, dict) else None
    if module is None:
        return
    path = getattr(module, "__file__", None)
    if not isinstance(path, str) or not path:
        raise UsageRefusal("SITECUSTOMIZE_REFUSED")
    norm = path.replace("\\", "/").casefold()
    if "/site-packages/" in norm:
        raise UsageRefusal("SITECUSTOMIZE_REFUSED")
    bases = []
    for base in (getattr(sys, "base_prefix", ""), getattr(sys, "prefix", "")):
        if isinstance(base, str) and base:
            bases.append(base.replace("\\", "/").casefold().rstrip("/") + "/")
    if not any(norm.startswith(base) for base in bases):
        raise UsageRefusal("SITECUSTOMIZE_REFUSED")


def assert_kickoff_cites_rows(text: str) -> None:
    """Refuse an empty N/A table. CrewAI would still save that text as kickoff.md."""
    if not isinstance(text, str) or not text.strip():
        raise UsageRefusal("KICKOFF_EMPTY_TABLE")
    folded = " ".join(text.split()).casefold()
    if "no rows were provided" in folded:
        raise UsageRefusal("KICKOFF_EMPTY_TABLE")
    if _empty_na_table(text):
        raise UsageRefusal("KICKOFF_EMPTY_TABLE")


def _empty_na_table(text: str) -> bool:
    allowed = {"n/a", "unknown", "na", ""}
    data = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if all(cell and set(cell) <= set("-: ") for cell in cells):
            continue
        data.append(cells)
    if not data:
        return False
    header_is_real = any(cell.casefold() not in allowed for cell in data[0])
    body = data[1:] if header_is_real else data
    if not body:
        return False
    return all(all(cell.casefold() in allowed for cell in row) for row in body)


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
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
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


def _windows_observe() -> dict:
    """Get-NetTCPConnection and Get-NetUDPEndpoint, or netstat -ano. Never guess zero."""
    import subprocess

    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _PS_OBSERVE],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
    if proc.returncode != 0 or not proc.stdout.strip():
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise UsageRefusal("PILOT_LISTENER_UNPROVEN") from exc
    return _normalize_windows(payload)


def count_listening_sockets(pid: int, platform: str | None = None, observation: dict | None = None,
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
        return str(exc) == "PILOT_LISTENER_PRESENT"
    return False
