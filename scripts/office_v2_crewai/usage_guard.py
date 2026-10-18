"""Enforce the E3 accept-risk conditions. Does not import crewai."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from office_v2_crewai.contract import E3_CONDITIONS

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
    "  @{ processes = @($processes); netstat = $raw; source = $source } | ConvertTo-Json -Depth 6 -Compress\n"
    "  exit 0\n"
    "}\n"
    "@{ processes = @($processes); tcp = @($tcp); udp = @($udp); source = $source } | "
    "ConvertTo-Json -Depth 6 -Compress\n"
)


class UsageRefusal(RuntimeError):
    """A pilot usage condition failed closed. No PASS is recorded."""


def module_is_forbidden(name: str) -> bool:
    """Flag server stacks only. The chromadb package itself is not forbidden."""
    if not isinstance(name, str) or not name:
        return False
    if name == "chromadb.server" or name.startswith("chromadb.server."):
        return True
    for prefix in E3_CONDITIONS["forbid_loaded_modules"]:
        if prefix == "chromadb.server":
            continue
        if name == prefix or name.startswith(prefix + "."):
            return True
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


def assert_post_run(modules: dict, listening_ports: int, commands: list | None = None) -> None:
    for argv in commands or []:
        assert_not_chroma_cli(argv)
    if any(module_is_forbidden(name) for name in modules):
        raise UsageRefusal("FORBIDDEN_MODULE_LOADED")
    if listening_ports != 0:
        raise UsageRefusal("PILOT_LISTENER_PRESENT")


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
    for name in ("chromadb.server", "chromadb.server.app", "fastapi", "uvicorn", "mcp", "mcp.server"):
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
