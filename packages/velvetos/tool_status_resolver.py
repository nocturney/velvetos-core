#!/usr/bin/env python3
"""Compose generic Core tool-status semantics with instance-owned tool state.

Stage 8D consumer cutover: active tool authority resolves from the selected
instance ``toolStatus`` surface. The retained legacy composite is rollback/parity
evidence only. This module contains no business-instance default and performs no
network or write action.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from instance_resolver import InstanceResolutionError, resolve_instance  # noqa: E402

CONTRACT_REL = Path("packages/velvetos/tool-status-contract.json")


class ToolStatusResolutionError(RuntimeError):
    pass


def _load_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ToolStatusResolutionError(f"missing JSON document: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ToolStatusResolutionError(f"invalid JSON document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ToolStatusResolutionError(f"JSON document must be an object: {path}")
    return value


def _validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != "velvetos.tool-status-contract.v1":
        raise ToolStatusResolutionError("tool status contract schema mismatch")
    if contract.get("legacyCompositeSchema") != "velvetos.tool-status.v1":
        raise ToolStatusResolutionError("legacy composite schema binding mismatch")
    if contract.get("role") != "CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM":
        raise ToolStatusResolutionError("tool status contract must remain generic Core semantics")
    rules = contract.get("rules")
    if not isinstance(rules, dict):
        raise ToolStatusResolutionError("tool status contract rules missing")
    required_rules = {
        "active",
        "frozen",
        "forbidden",
        "watch",
        "desired_not_connected",
        "version_default",
        "exact_version_exception",
        "upgrade_application",
        "upstream_registry",
    }
    if set(rules) != required_rules:
        raise ToolStatusResolutionError("tool status contract rule vocabulary drift")
    if contract.get("instanceStateSurface") != "toolStatus":
        raise ToolStatusResolutionError("tool status instance surface binding drift")
    composition = contract.get("composition")
    if not isinstance(composition, dict):
        raise ToolStatusResolutionError("tool status composition contract missing")
    if composition.get("consumerCutover") is not True:
        raise ToolStatusResolutionError("tool-status consumer cutover must be active")
    if composition.get("activeAuthority") != "instance:surface:toolStatus":
        raise ToolStatusResolutionError("tool-status active authority must be the selected instance surface")
    if composition.get("rollbackCompatibilityPath") != "packages/velvetos/TOOL-STATUS.json":
        raise ToolStatusResolutionError("rollback compatibility path drift")
    if composition.get("rollbackCompatibilityRetained") is not True:
        raise ToolStatusResolutionError("rollback compatibility must remain retained during Stage 8D")


def _validate_state(state: dict[str, Any], *, instance_id: str) -> None:
    if state.get("schema") != "velvetos.instance-tool-status.v1":
        raise ToolStatusResolutionError("instance tool status schema mismatch")
    if state.get("instanceId") != instance_id:
        raise ToolStatusResolutionError("instance tool status identity mismatch")
    if state.get("contract") != CONTRACT_REL.as_posix():
        raise ToolStatusResolutionError("instance tool status contract binding mismatch")
    if not isinstance(state.get("updated_at"), str) or not state["updated_at"].strip():
        raise ToolStatusResolutionError("instance tool status updated_at missing")
    if not isinstance(state.get("authority"), str) or not state["authority"].strip():
        raise ToolStatusResolutionError("instance tool status authority missing")
    tools = state.get("tools")
    if not isinstance(tools, dict) or not tools:
        raise ToolStatusResolutionError("instance tool status tools missing")
    for tool_id, row in tools.items():
        if not isinstance(tool_id, str) or not tool_id:
            raise ToolStatusResolutionError("invalid tool id")
        if not isinstance(row, dict) or not isinstance(row.get("status"), str) or not row["status"]:
            raise ToolStatusResolutionError(f"{tool_id}: tool status missing")


def compose_tool_status(
    repository_root: str | Path,
    *,
    instance_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    contract = _load_object(root / CONTRACT_REL)
    _validate_contract(contract)

    try:
        instance = resolve_instance(root, instance_id=instance_id, env=env)
    except InstanceResolutionError as exc:
        raise ToolStatusResolutionError(str(exc)) from exc

    surface_name = str(contract["instanceStateSurface"])
    try:
        state_path = instance.surface(surface_name)
    except InstanceResolutionError as exc:
        raise ToolStatusResolutionError(
            f"instance {instance.instance_id!r} has no {surface_name!r} surface"
        ) from exc
    state = _load_object(state_path)
    _validate_state(state, instance_id=instance.instance_id)

    return {
        "schema": contract["legacyCompositeSchema"],
        "updated_at": state["updated_at"],
        "authority": state["authority"],
        "rules": contract["rules"],
        "tools": state["tools"],
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--instance-id")
    parser.add_argument("command", choices=("show", "legacy-parity"))
    args = parser.parse_args()

    try:
        composed = compose_tool_status(
            args.root,
            instance_id=args.instance_id,
            env=os.environ,
        )
    except ToolStatusResolutionError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2

    if args.command == "show":
        print(json.dumps(composed, ensure_ascii=False, indent=2))
        return 0

    root = Path(args.root).resolve()
    contract = _load_object(root / CONTRACT_REL)
    legacy_rel = Path(contract["composition"]["rollbackCompatibilityPath"])
    legacy = _load_object(root / legacy_rel)
    if composed != legacy:
        print("FAIL composed tool status differs from legacy compatibility document", file=sys.stderr)
        return 1
    print("OK tool-status legacy parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
