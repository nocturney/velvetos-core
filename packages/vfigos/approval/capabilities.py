"""Load Instagram mutation/read tool ids from canonical SoT files.

Sources (no second handwritten write-tool list):
- packages/vfigos/CAPABILITIES.json
- packages/vfmcp/core-mcp.json
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_HERE = Path(__file__).resolve()
# packages/vfigos/approval → packages/
_PACKAGES = _HERE.parents[2]
_DEFAULT_CAPS = _PACKAGES / "vfigos" / "CAPABILITIES.json"
_DEFAULT_CORE = _PACKAGES / "vfmcp" / "core-mcp.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=8)
def _tool_classes(
    caps_path: str,
    core_path: str,
) -> tuple[frozenset[str], frozenset[str]]:
    mutation: set[str] = set()
    read_only: set[str] = set()
    caps_file = Path(caps_path)
    core_file = Path(core_path)
    if caps_file.is_file():
        caps = _load_json(caps_file)
        for row in caps.get("capabilities") or []:
            if not isinstance(row, dict):
                continue
            tools = [t for t in (row.get("tools") or []) if isinstance(t, str) and t]
            if not tools:
                continue
            cap_id = str(row.get("id") or "")
            supported = row.get("supported", True)
            if "graph_mutation_matrix" in tools:
                read_only.add("graph_mutation_matrix")
            write_tools = [t for t in tools if t != "graph_mutation_matrix"]
            if supported is False:
                continue
            if cap_id.startswith("instagram.publish.") or cap_id == "instagram.media.delete":
                mutation.update(write_tools)
            elif write_tools:
                read_only.update(write_tools)
    if core_file.is_file():
        core = _load_json(core_file)
        for server in core.get("servers") or []:
            if not isinstance(server, dict) or server.get("id") != "instagram":
                continue
            for t in server.get("allowedWriteAfterGates") or []:
                if isinstance(t, str) and t:
                    mutation.add(t)
            for t in server.get("allowedRead") or []:
                if isinstance(t, str) and t:
                    read_only.add(t)
            break
    # Mutation ids are never also treated as read-only for gating.
    read_only -= mutation
    return frozenset(mutation), frozenset(read_only)


def mutation_tool_ids(
    *,
    caps_path: Path | None = None,
    core_path: Path | None = None,
) -> frozenset[str]:
    caps = str(caps_path or _DEFAULT_CAPS)
    core = str(core_path or _DEFAULT_CORE)
    return _tool_classes(caps, core)[0]


def read_only_tool_ids(
    *,
    caps_path: Path | None = None,
    core_path: Path | None = None,
) -> frozenset[str]:
    caps = str(caps_path or _DEFAULT_CAPS)
    core = str(core_path or _DEFAULT_CORE)
    return _tool_classes(caps, core)[1]


def is_mutation_tool(tool_id: str, **kwargs: Path | None) -> bool:
    return tool_id in mutation_tool_ids(
        caps_path=kwargs.get("caps_path"),  # type: ignore[arg-type]
        core_path=kwargs.get("core_path"),  # type: ignore[arg-type]
    )
