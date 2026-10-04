"""Read-only bridge to the canonical VelvetOS instance resolver.

Loads packages/velvetos/instance_resolver.py by absolute file path to avoid
name collisions with scripts/velvetos.py. No business default is introduced.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Mapping


class InstanceSourceError(RuntimeError):
    pass


def _load_resolver(repository_root: Path):
    path = repository_root / "packages" / "velvetos" / "instance_resolver.py"
    if not path.is_file():
        raise InstanceSourceError(f"instance resolver missing: {path}")
    name = "velvetos_control_api_instance_resolver"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise InstanceSourceError(f"cannot load instance resolver: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def resolve_instance_surface(
    repository_root: str | Path,
    surface: str,
    *,
    env: Mapping[str, str] | None = None,
) -> Path:
    root = Path(repository_root).resolve()
    resolver = _load_resolver(root)
    env_map = os.environ if env is None else env
    try:
        return resolver.resolve_surface(root, surface, env=env_map)
    except resolver.InstanceResolutionError as exc:
        raise InstanceSourceError(str(exc)) from exc
