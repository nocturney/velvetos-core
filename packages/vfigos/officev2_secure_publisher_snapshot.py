#!/usr/bin/env python3
"""Office v2 production-authorized read-only Instagram Publisher schedule snapshot."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

DEFAULT_RESOLVER = Path(
    os.environ.get(
        "VELVET_OFFICEV2_PUBLISHER_SNAPSHOT_RESOLVER",
        r"D:\Velvet\Runtime\OfficeV2Lab\Resolve-Phase3B-ProductionSnapshot.ps1",
    )
)


def secure_snapshot(resolver: Path, mode: str) -> dict:
    if os.name != "nt":
        raise RuntimeError("Office v2 production snapshot resolver requires the trusted Windows owner runtime")
    if not resolver.is_file():
        raise RuntimeError(f"Office v2 production snapshot resolver missing: {resolver}")
    proc = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-WindowStyle",
            "Hidden",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(resolver),
            "-Mode",
            mode,
        ],
        text=True,
        capture_output=True,
        timeout=90,
        encoding="utf-8",
    )
    if proc.returncode:
        detail=(proc.stderr or "").strip().splitlines()
        safe=detail[-1] if detail else "resolver denied"
        raise RuntimeError(f"Office v2 production snapshot unavailable: {safe}")
    payload=(proc.stdout or "").strip()
    if not payload:
        raise RuntimeError("Office v2 production snapshot resolver returned no payload")
    data=json.loads(payload)
    if data.get("schema") != "vf.instagram.schedule-snapshot.v1":
        raise RuntimeError("Office v2 production snapshot schema mismatch")
    if data.get("source") != "cloudflare-instagram-publisher":
        raise RuntimeError("Office v2 production snapshot source mismatch")
    return data


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--resolver", type=Path, default=DEFAULT_RESOLVER)
    ap.add_argument("--mode", choices=("Probe", "Production"), default="Production")
    args=ap.parse_args()
    data=secure_snapshot(args.resolver, args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"OK source={data['source']} scheduled={len(data.get('scheduled') or [])} security=office-v2-production-read mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
