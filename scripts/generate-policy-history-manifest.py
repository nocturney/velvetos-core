#!/usr/bin/env python3
"""Build/check immutable integrity manifest for historical Reform v2 policy receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "packages" / "velvetos" / "policy" / "reports"
OUTPUT = ROOT / "packages" / "velvetos" / "policy" / "historical-policy-manifest.json"
STAGE_RE = re.compile(r"^stage[4-8].*\.json$")
GENERATOR_RE = re.compile(r"^generate-stage[4-8].*\.py$")
HASH_KEYS = {"sha256", "canonical_json_sha256"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def referenced_hashed_paths(obj: object) -> set[str]:
    found: set[str] = set()
    if isinstance(obj, dict):
        has_hash = any(isinstance(obj.get(key), str) and len(str(obj.get(key))) == 64 for key in HASH_KEYS)
        if has_hash:
            for key in ("path", "artifact"):
                value = obj.get(key)
                if isinstance(value, str) and value and not value.startswith(("http://", "https://")):
                    candidate = ROOT / value
                    if candidate.is_file():
                        found.add(candidate.relative_to(ROOT).as_posix())
        for value in obj.values():
            found.update(referenced_hashed_paths(value))
    elif isinstance(obj, list):
        for value in obj:
            found.update(referenced_hashed_paths(value))
    return found


def build() -> dict:
    paths: set[str] = set()

    report_paths = sorted(p for p in REPORTS.glob("*.json") if STAGE_RE.match(p.name))
    for path in report_paths:
        paths.add(repo_rel(path))
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            raise ValueError(f"invalid historical report {repo_rel(path)}: {exc}") from exc
        paths.update(referenced_hashed_paths(data))

    for path in sorted((ROOT / "scripts").glob("generate-stage*.py")):
        if GENERATOR_RE.match(path.name):
            paths.add(repo_rel(path))
    for rel in (
        "scripts/generate-policy-history-manifest.py",
        "scripts/check-policy-history-replay.py",
    ):
        paths.add(rel)

    entries = []
    for rel in sorted(paths):
        path = ROOT / rel
        if not path.is_file():
            raise ValueError(f"historical manifest input missing: {rel}")
        entries.append({"path": rel, "sha256": sha256(path)})

    return {
        "schema": "velvetos.policy-history-manifest.v1",
        "purpose": "immutable_integrity_for_completed_stage4_stage8_policy_history",
        "routine_execution": "HASH_ONLY",
        "explicit_replay": "scripts/check-policy-history-replay.py",
        "entry_count": len(entries),
        "entries": entries,
    }


def render(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--output", type=Path, default=OUTPUT)
    args = ap.parse_args()

    try:
        payload = build()
    except ValueError as exc:
        print(f"FAIL policy-history-manifest: {exc}", file=sys.stderr)
        return 1
    rendered = render(payload)

    if args.check:
        if not args.output.is_file():
            print(f"FAIL policy-history-manifest missing {repo_rel(args.output)}", file=sys.stderr)
            return 1
        current = args.output.read_text(encoding="utf-8")
        if current != rendered:
            print("FAIL policy-history-manifest drift; run generator explicitly after historical replay", file=sys.stderr)
            return 1
        print(f"OK policy-history-manifest entries={payload['entry_count']} hash_only=PASS")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"WROTE {repo_rel(args.output)} entries={payload['entry_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
