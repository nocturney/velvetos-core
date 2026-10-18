"""Enforce the E3 accept-risk conditions. Does not import crewai."""
from __future__ import annotations

import os
from pathlib import Path

from office_v2_crewai.contract import E3_CONDITIONS


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


def count_listening_sockets(pid: int) -> int:
    """Count TCP LISTEN sockets owned by pid. Unproven observation fails closed."""
    proc = Path("/proc")
    tcp_files = [proc / "net" / "tcp"]
    tcp6 = proc / "net" / "tcp6"
    if tcp6.is_file():
        tcp_files.append(tcp6)
    fd_dir = proc / str(pid) / "fd"
    if not tcp_files[0].is_file() or not fd_dir.is_dir():
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
