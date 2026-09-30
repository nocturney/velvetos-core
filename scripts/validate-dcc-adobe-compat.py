#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVTOOLS = ROOT / "packages" / "vfharness" / "devtools"
OVERLAYS = DEVTOOLS / "dcc-mcp-overlays.json"
BRIDGES = DEVTOOLS / "adobe-first-party-bridges.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hash(path: Path, expected: str, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"missing file: {path.relative_to(ROOT)}")
        return
    actual = sha256(path)
    if actual.lower() != str(expected).lower():
        errors.append(f"sha256 mismatch: {path.relative_to(ROOT)} expected={expected} actual={actual}")


def main() -> int:
    errors: list[str] = []
    overlays = load_json(OVERLAYS)
    bridges = load_json(BRIDGES)
    overlay_ids: set[str] = set()
    for row in overlays.get("overlays") or []:
        overlay_id = str(row.get("id") or "")
        if not overlay_id:
            errors.append("overlay missing id")
            continue
        if overlay_id in overlay_ids:
            errors.append(f"duplicate overlay id: {overlay_id}")
        overlay_ids.add(overlay_id)
        patch = row.get("patch")
        expected = row.get("patch_sha256")
        if patch and expected:
            check_hash(ROOT / str(patch), str(expected), errors)

    record_ids: set[str] = set()
    for row in overlays.get("supporting_records") or []:
        record_id = str(row.get("id") or "")
        if not record_id:
            errors.append("supporting record missing id")
            continue
        if record_id in record_ids:
            errors.append(f"duplicate supporting record id: {record_id}")
        record_ids.add(record_id)
        record = row.get("record")
        expected = row.get("record_sha256")
        if record and expected:
            check_hash(ROOT / str(record), str(expected), errors)

    bridge_ids: set[str] = set()
    literal_secret = re.compile(r"""(?i)token\s*[:=]\s*["'][A-Za-z0-9_+/=-]{20,}["']""")
    for bridge in bridges.get("bridges") or []:
        bridge_id = str(bridge.get("id") or "")
        version = str(bridge.get("version") or "")
        if not bridge_id or not version:
            errors.append("bridge missing id/version")
            continue
        if bridge_id in bridge_ids:
            errors.append(f"duplicate bridge id: {bridge_id}")
        bridge_ids.add(bridge_id)

        source_dir = ROOT / str(bridge.get("source_dir") or "")
        if not source_dir.is_dir():
            errors.append(f"{bridge_id}: missing source_dir")
            continue
        if (source_dir / "adobepy.config.js").exists():
            errors.append(f"{bridge_id}: runtime secret config must not be committed")

        source_files = bridge.get("source_files") or {}
        for relative, expected in source_files.items():
            check_hash(source_dir / str(relative), str(expected), errors)

        manifest_path = source_dir / "manifest.json"
        main_path = source_dir / "main.js"
        if not manifest_path.is_file() or not main_path.is_file():
            continue
        manifest = load_json(manifest_path)
        main_text = main_path.read_text(encoding="utf-8")
        if str(manifest.get("version")) != version:
            errors.append(f"{bridge_id}: manifest version does not match registry")
        if manifest.get("id") != f"com.velvetos.{bridge_id}.bridge":
            errors.append(f"{bridge_id}: unexpected manifest id")
        if not re.search(r"""bridgeVersion\s*:\s*["']""" + re.escape(version) + r"""["']""", main_text):
            errors.append(f"{bridge_id}: main.js bridgeVersion does not match registry")
        permissions = manifest.get("requiredPermissions") or {}
        network = permissions.get("network") or {}
        if network.get("domains") != "all":
            errors.append(f"{bridge_id}: loopback broker network permission missing")
        if literal_secret.search(main_text):
            errors.append(f"{bridge_id}: literal token-like secret found in main.js")

        for candidate in source_dir.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() not in {".js", ".json", ".html", ".md"}:
                continue
            if literal_secret.search(candidate.read_text(encoding="utf-8", errors="ignore")):
                errors.append(f"{bridge_id}: literal token-like secret found in {candidate.relative_to(source_dir)}")

        if bridge_id == "premiere":
            if version != "0.1.3":
                errors.append("premiere: canonical source must be 0.1.3")
            if "hostUIContext" in manifest or "hideFromMenu" in manifest:
                errors.append("premiere: 26.3.2 production source must not use invisible hideFromMenu route")
        if bridge_id == "photoshop":
            data = (manifest.get("host") or {}).get("data") or {}
            if data.get("loadEvent") != "startup":
                errors.append("photoshop: startup loadEvent missing")

    if errors:
        for error in errors:
            print("DCC/ADOBE COMPAT FAIL: " + error, file=sys.stderr)
        return 1
    print(
        f"DCC/ADOBE COMPAT PASS overlays={len(overlay_ids)} "
        f"records={len(record_ids)} bridges={len(bridge_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
