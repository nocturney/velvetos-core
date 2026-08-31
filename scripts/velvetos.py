#!/usr/bin/env python3
"""VelvetOS helper — instance / modules / presets. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "velvetos"
INSTANCE = PACK / "INSTANCE.json"
CATALOG = PACK / "modules" / "catalog.json"
PRESETS = PACK / "presets"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def profile() -> dict:
    meta = load(INSTANCE)
    return load(PACK / meta["profile"])


def cmd_instance() -> int:
    meta = load(INSTANCE)
    data = profile()
    stages = " → ".join(s["label"] for s in data["pipeline"]["stages"])
    ig = ", ".join(c["handle"] for c in data["channels"].get("instagram", [])) or "(none)"
    print(f"product: {meta['product']}")
    print(f"display: {meta['displayName']}")
    print(f"instance: {meta['instanceId']}")
    print(f"hostsCore: {meta.get('hostsCore')}")
    print(f"vertical: {data['vertical']}")
    print(f"preset: {data.get('preset')}")
    print(f"modules: {len(data['modulesEnabled'])}")
    print(f"fulfillment: {data['fulfillment']['mode']}")
    print(f"production: {data['production']['kind']}")
    print(f"pipeline: {stages}")
    print(f"instagram: {ig}")
    print(f"cta: {data['cta']['primary']}")
    return 0


def cmd_modules() -> int:
    cat = load(CATALOG)
    enabled = set(profile()["modulesEnabled"])
    print("modules (*=enabled on this instance):")
    for row in cat["modules"]:
        mark = "*" if row["id"] in enabled else " "
        print(f" {mark} {row['id']:28} [{row['group']}] {row['summary']}")
    return 0


def cmd_presets() -> int:
    print("presets (blueprints for future instance repos — not live here):")
    for path in sorted(PRESETS.glob("*.json")):
        data = load(path)
        used = " ← this instance" if data.get("usedByInstance") else ""
        print(
            f"   {data['id']:28} modules={len(data['modulesEnabled'])} "
            f"{data.get('titleHe') or data['title']}{used}"
        )
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help", "help"}:
        print("usage: velvetos.py instance|modules|presets")
        print(" legacy: active → instance, list → modules+presets")
        return 0
    cmd = argv[1]
    # legacy aliases from earlier tenant wording
    if cmd == "active":
        cmd = "instance"
    if cmd == "list":
        cmd_modules()
        print()
        return cmd_presets()
    if cmd == "instance":
        return cmd_instance()
    if cmd == "modules":
        return cmd_modules()
    if cmd == "presets":
        return cmd_presets()
    print("usage: velvetos.py instance|modules|presets", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
