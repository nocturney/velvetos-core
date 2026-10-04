#!/usr/bin/env python3
"""VelvetOS Core helper — core / modules / presets / instances. No network. No send."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "velvetos"
CORE = PACK / "CORE.json"
CATALOG = PACK / "modules" / "catalog.json"
PRESETS = PACK / "presets"
INSTANCES = ROOT / "instances"
if str(PACK) not in sys.path:
    sys.path.insert(0, str(PACK))
from instance_resolver import InstanceResolutionError, resolve_surface  # type: ignore


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def selected_profile(instance_id: str | None = None) -> dict | None:
    requested = instance_id or os.environ.get("VELVETOS_INSTANCE_ID")
    if not requested:
        return None
    try:
        path = resolve_surface(ROOT, "profile", instance_id=requested, env={})
    except InstanceResolutionError as exc:
        raise SystemExit(f"instance profile resolution failed: {exc}") from exc
    return load(path)


def cmd_core() -> int:
    meta = load(CORE)
    print(f"product: {meta['product']}")
    print(f"role: {meta['role']}")
    print(f"display: {meta['displayName']}")
    print(f"metaphor.core: {meta['metaphor']['core']}")
    print(f"metaphor.instance: {meta['metaphor']['instance']}")
    for row in meta.get("repos", {}).get("instances", []):
        print(
            f"instance-plan: {row['id']:24} status={row.get('status')} "
            f"{row.get('displayName')}"
        )
    return 0


def cmd_modules(instance_id: str | None = None) -> int:
    cat = load(CATALOG)
    profile = selected_profile(instance_id)
    enabled = set((profile or {}).get("modulesEnabled", []))
    selected = (profile or {}).get("id")
    if selected:
        print(f"modules (*=enabled in selected instance {selected}):")
    else:
        print("modules (no instance selected; use --instance-id or VELVETOS_INSTANCE_ID for enabled marks):")
    for row in cat["modules"]:
        mark = "*" if row["id"] in enabled else " "
        print(f" {mark} {row['id']:28} [{row['group']}] {row['summary']}")
    return 0


def cmd_presets() -> int:
    print("presets (blueprints for frontend instance repos):")
    for path in sorted(PRESETS.glob("*.json")):
        data = load(path)
        print(
            f"   {data['id']:28} modules={len(data['modulesEnabled'])} "
            f"{data.get('titleHe') or data['title']}"
        )
    return 0


def cmd_instances() -> int:
    print("frontend scaffolds under instances/:")
    for path in sorted(INSTANCES.iterdir() if INSTANCES.is_dir() else []):
        if not path.is_dir():
            continue
        meta_path = path / "INSTANCE.json"
        if not meta_path.is_file():
            print(f"   {path.name:24} (incomplete)")
            continue
        meta = load(meta_path)
        print(f"   {path.name:24} {meta.get('displayName')} → publish via scripts/publish-instance.sh")
    return 0


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    instance_id: str | None = None
    if "--instance-id" in args:
        index = args.index("--instance-id")
        if index + 1 >= len(args):
            print("--instance-id requires a value", file=sys.stderr)
            return 1
        instance_id = args[index + 1]
        del args[index:index + 2]
    if not args or args[0] in {"-h", "--help", "help"}:
        print("usage: velvetos.py [--instance-id ID] core|modules|presets|instances")
        print(" legacy: instance|active → core ; list → modules+presets+instances")
        return 0
    cmd = args[0]
    if cmd in {"instance", "active"}:
        cmd = "core"
    if cmd == "list":
        cmd_modules(instance_id)
        print()
        cmd_presets()
        print()
        return cmd_instances()
    if cmd == "core":
        return cmd_core()
    if cmd == "modules":
        return cmd_modules(instance_id)
    if cmd == "presets":
        return cmd_presets()
    if cmd == "instances":
        return cmd_instances()
    print("usage: velvetos.py [--instance-id ID] core|modules|presets|instances", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
