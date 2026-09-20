#!/usr/bin/env python3
"""Register and verify a file-backed Velvet Factory creative master.

This utility is deliberately local-only: it never downloads remote URLs and never
chooses a provider. The caller must first materialize/fetch provider output through
an authorized route, then register those exact local bytes here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from vf_media_integrity import inspect_media

VERSION = 1
ALLOWED_ORIGIN_KINDS = {"LOCAL_RENDER", "PROVIDER_FETCHED_FILE", "TOOL_EXPORT"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inside(root: Path, value: str | Path, label: str) -> Path:
    root = root.resolve()
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside workspace root") from exc
    return path


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def register(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    source = inside(root, args.input, "input")
    if not source.is_file():
        raise ValueError("input file missing")
    media = inspect_media(source, "creative master candidate")
    source_sha = digest(source)
    forbidden = {x.lower() for x in (args.forbid_sha or [])}
    if source_sha in forbidden:
        raise ValueError("creative master candidate matches a forbidden raw/reference SHA")
    if args.origin_kind not in ALLOWED_ORIGIN_KINDS:
        raise ValueError("unsupported origin kind")

    workspace = inside(root, args.workspace, "workspace")
    master_dir = workspace / "creative-master"
    master_dir.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    dest = master_dir / f"master{suffix}"
    receipt_path = master_dir / "materialization.json"

    if dest.exists():
        if digest(dest) != source_sha:
            raise ValueError("creative master destination already exists with different bytes")
    else:
        shutil.copyfile(source, dest)
    dest_sha = digest(dest)
    if dest_sha != source_sha:
        raise ValueError("creative master exact-byte copy mismatch")

    receipt = {
        "version": VERSION,
        "materialization_method": "LOCAL_EXACT_COPY",
        "exact_bytes_copied": True,
        "origin": {
            "kind": args.origin_kind,
            "provider": args.provider or None,
            "id": args.origin_id or None,
            "path": rel(root, source),
            "sha256": source_sha,
        },
        "materialized": {
            "path": rel(root, dest),
            "sha256": dest_sha,
            "bytes": dest.stat().st_size,
            "media": media,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt_sha = digest(receipt_path)
    return {
        "ok": True,
        "creative_master": {"path": rel(root, dest), "sha256": dest_sha},
        "creative_master_materialization": {"path": rel(root, receipt_path), "sha256": receipt_sha},
        "origin_sha256": source_sha,
    }


def verify(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    receipt_path = inside(root, args.receipt, "receipt")
    if not receipt_path.is_file():
        raise ValueError("materialization receipt missing")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("version") != VERSION:
        raise ValueError("unsupported materialization receipt version")
    if receipt.get("materialization_method") != "LOCAL_EXACT_COPY" or receipt.get("exact_bytes_copied") is not True:
        raise ValueError("receipt does not prove exact-byte local materialization")

    origin = receipt.get("origin")
    materialized = receipt.get("materialized")
    if not isinstance(origin, dict) or not isinstance(materialized, dict):
        raise ValueError("receipt origin/materialized fields missing")
    if origin.get("kind") not in ALLOWED_ORIGIN_KINDS:
        raise ValueError("receipt origin kind unsupported")

    source = inside(root, origin.get("path", ""), "origin path")
    master = inside(root, materialized.get("path", ""), "materialized path")
    if not source.is_file() or not master.is_file():
        raise ValueError("origin or materialized creative master file missing")
    source_sha, master_sha = digest(source), digest(master)
    if source_sha != origin.get("sha256"):
        raise ValueError("origin bytes no longer match materialization receipt")
    if master_sha != materialized.get("sha256"):
        raise ValueError("materialized master bytes do not match receipt")
    if source_sha != master_sha:
        raise ValueError("materialized master is not an exact-byte handoff from origin artifact")
    if master.stat().st_size != materialized.get("bytes"):
        raise ValueError("materialized master byte count mismatch")
    media = inspect_media(master, "materialized creative master")
    return {
        "ok": True,
        "creative_master": {"path": rel(root, master), "sha256": master_sha},
        "creative_master_materialization": {"path": rel(root, receipt_path), "sha256": digest(receipt_path)},
        "media": media,
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    reg = sub.add_parser("register")
    reg.add_argument("--root", default=".")
    reg.add_argument("--input", required=True)
    reg.add_argument("--workspace", required=True)
    reg.add_argument("--origin-kind", choices=sorted(ALLOWED_ORIGIN_KINDS), required=True)
    reg.add_argument("--provider")
    reg.add_argument("--origin-id")
    reg.add_argument("--forbid-sha", action="append", default=[])
    ver = sub.add_parser("verify")
    ver.add_argument("--root", default=".")
    ver.add_argument("--receipt", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        result = register(args) if args.command == "register" else verify(args)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)[:1000]}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
