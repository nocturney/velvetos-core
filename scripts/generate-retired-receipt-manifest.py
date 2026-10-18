#!/usr/bin/env python3
"""Build/check immutable hashes for retired sensor receipts and archived checks."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "packages" / "velvetos" / "policy" / "retired-receipt-manifest.json"
PATHS = [
    "packages/vfharness/state/ecosystem-radar-phase9-2026-09-27.json",
    "packages/vfharness/state/zero-cost-agent-stack-2026-09-27.json",
    "packages/vfharness/state/zero-cost-final-acceptance-2026-09-27.json",
    "scripts/check-ecosystem-radar-phase9.py",
    "scripts/check-zero-cost-final-acceptance.py",
    "scripts/check-retired-receipt-integrity.py",
    "scripts/generate-retired-receipt-manifest.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    entries = []
    for rel in PATHS:
        path = ROOT / rel
        if not path.is_file():
            raise ValueError(f"missing retired receipt input: {rel}")
        entries.append({"path": rel, "sha256": sha256(path)})
    return {
        "schema": "velvetos.retired-receipts.v1",
        "purpose": "immutable_integrity_for_retired_sensor_receipts",
        "entries": entries,
    }


def render(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        rendered = render(build())
    except ValueError as exc:
        print(f"FAIL retired-receipt-manifest: {exc}", file=sys.stderr)
        return 1
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print("FAIL retired-receipt-manifest drift", file=sys.stderr)
            return 1
        print(f"OK retired-receipt-manifest entries={len(build()['entries'])}")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"WROTE packages/velvetos/policy/retired-receipt-manifest.json entries={len(build()['entries'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
