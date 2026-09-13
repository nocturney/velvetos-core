#!/usr/bin/env python3
"""Canonical VelvetOS media toolchain version loader."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "vfmcp" / "TOOLCHAIN-VERSIONS.json"


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise RuntimeError("invalid toolchain manifest")
    return data


def get_value(path: str) -> Any:
    value: Any = load_manifest()
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(path)
        value = value[part]
    return value


def component(name: str) -> dict[str, Any]:
    value = get_value(f"components.{name}")
    if not isinstance(value, dict):
        raise TypeError(f"component {name} must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    get_p = sub.add_parser("get")
    get_p.add_argument("path")
    sub.add_parser("json")
    args = parser.parse_args()
    if args.command == "json":
        print(json.dumps(load_manifest(), ensure_ascii=False, indent=2))
        return 0
    try:
        value = get_value(args.path)
    except (KeyError, RuntimeError, TypeError) as exc:
        print(f"FAIL {exc}")
        return 1
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False))
    elif isinstance(value, bool):
        print("true" if value else "false")
    else:
        print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
