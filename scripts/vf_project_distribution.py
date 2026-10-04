#!/usr/bin/env python3
"""Resolve the selected instance ChatGPT Project distribution surface."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]


class ProjectDistributionError(RuntimeError):
    pass


def _load_instance_resolver(root: Path):
    path = root / "packages" / "velvetos" / "instance_resolver.py"
    if not path.is_file():
        raise ProjectDistributionError(f"instance resolver missing: {path}")
    name = "vf_project_distribution_instance_resolver"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ProjectDistributionError(f"cannot load instance resolver: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def resolve_distribution(
    root: str | Path = ROOT,
    *,
    instance_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    repo = Path(root).resolve()
    resolver = _load_instance_resolver(repo)
    env_map = os.environ if env is None else env
    try:
        latest = resolver.resolve_surface(
            repo,
            "chatgptProject",
            instance_id=instance_id,
            env=env_map,
        )
        return latest.parent
    except resolver.InstanceResolutionError as exc:
        raise ProjectDistributionError(str(exc)) from exc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--instance-id")
    args = ap.parse_args()
    try:
        path = resolve_distribution(args.root, instance_id=args.instance_id)
    except ProjectDistributionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "path": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
