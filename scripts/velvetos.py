#!/usr/bin/env python3
"""VelvetOS tenant helper — active / list / show. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "velvetos"
ACTIVE = PACK / "ACTIVE.json"
TENANTS = PACK / "tenants"
EXAMPLES = TENANTS / "_examples"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def active_id() -> str:
    return load_json(ACTIVE)["activeTenant"]


def tenant_path(tid: str) -> Path:
    p = TENANTS / f"{tid}.json"
    if p.is_file():
        return p
    ex = EXAMPLES / f"{tid}.json"
    if ex.is_file():
        return ex
    raise FileNotFoundError(tid)


def cmd_active() -> int:
    tid = active_id()
    data = load_json(tenant_path(tid))
    stages = " → ".join(s["label"] for s in data["pipeline"]["stages"])
    ig = ", ".join(c["handle"] for c in data["channels"].get("instagram", [])) or "(none)"
    print(f"product: VelvetOS")
    print(f"active: {tid}")
    print(f"display: {data.get('displayNameHe') or data['displayName']}")
    print(f"vertical: {data['vertical']}")
    print(f"fulfillment: {data['fulfillment']['mode']}")
    print(f"production: {data['production']['kind']}")
    print(f"pipeline: {stages}")
    print(f"instagram: {ig}")
    print(f"cta: {data['cta']['primary']}")
    return 0


def cmd_list() -> int:
    print("tenants:")
    for path in sorted(TENANTS.glob("*.json")):
        data = load_json(path)
        mark = "*" if data["id"] == active_id() else " "
        print(f" {mark} {data['id']:24} status={data['status']:8} {data['displayName']}")
    print("examples:")
    if EXAMPLES.is_dir():
        for path in sorted(EXAMPLES.glob("*.json")):
            data = load_json(path)
            print(f"   {data['id']:24} status={data['status']:8} {data['displayName']}")
    return 0


def cmd_show(tid: str) -> int:
    path = tenant_path(tid)
    print(json.dumps(load_json(path), ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help", "help"}:
        print("usage: velvetos.py active|list|show <id>")
        return 0
    cmd = argv[1]
    try:
        if cmd == "active":
            return cmd_active()
        if cmd == "list":
            return cmd_list()
        if cmd == "show" and len(argv) >= 3:
            return cmd_show(argv[2])
    except FileNotFoundError as exc:
        print(f"FAIL unknown tenant {exc}", file=sys.stderr)
        return 1
    print("usage: velvetos.py active|list|show <id>", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
