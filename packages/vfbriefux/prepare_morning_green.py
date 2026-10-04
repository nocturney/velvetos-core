#!/usr/bin/env python3
"""Prepare Morning Green artifacts and a fail-closed Gmail send request."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "packages" / "vfbriefux"
OUT = ROOT / "packages" / "vfops" / "out"


def extract_date(brief_json: Path) -> tuple[str, str]:
    data = json.loads(brief_json.read_text(encoding="utf-8"))
    line = str(data.get("date_line") or "")
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", line)
    if m:
        dd, mm, yyyy = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return f"{yyyy:04d}-{mm:02d}-{dd:02d}", f"{dd}.{mm}.{yyyy}"
    iso = str(data.get("date") or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", iso)
    if not m:
        raise ValueError("brief has neither DD.MM.YYYY date_line nor YYYY-MM-DD date")
    yyyy, mm, dd = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return f"{yyyy:04d}-{mm:02d}-{dd:02d}", f"{dd}.{mm}.{yyyy}"


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout or "command failed").strip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief-json", type=Path, required=True)
    ap.add_argument("--brief-txt", type=Path, required=True)
    ap.add_argument("--schedule-snapshot", type=Path)
    ap.add_argument("--thumbnail-dir", type=Path, help="Optional local cache for snapshot thumbnail_cid assets")
    ap.add_argument("--request", type=Path, default=OUT / "gmail-send-request.json")
    ap.add_argument("--enable", action="store_true", help="Explicitly arm the one-shot Gmail request")
    args = ap.parse_args()

    iso, display = extract_date(args.brief_json)
    # Stage 7D retention: one rolling transport bundle in Git.
    # Historical dated bundles are audit history, not a reason to add a new
    # rendered copy every day.
    green_json = OUT / "morning-green-current.json"
    green_txt = OUT / "morning-green-current.txt"
    green_html = OUT / "morning-green-current.html"
    assets_out = OUT / "morning-green-assets-current"

    if assets_out.exists():
        shutil.rmtree(assets_out)
    shutil.copytree(PACK / "assets" / "morning-green", assets_out)

    snapshot_path = args.schedule_snapshot
    if snapshot_path:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        for row in snapshot.get("scheduled") or []:
            cid = str(row.get("thumbnail_cid") or "").strip()
            if not cid:
                continue
            if not args.thumbnail_dir:
                raise ValueError(f"snapshot requires thumbnail {cid} but --thumbnail-dir is missing")
            src = args.thumbnail_dir / cid
            if not src.is_file():
                raise FileNotFoundError(f"materialized thumbnail missing: {src}")
            shutil.copy2(src, assets_out / cid)

    build = [
        sys.executable,
        str(PACK / "build_morning_green.py"),
        "--brief-json",
        str(args.brief_json),
        "--brief-txt",
        str(args.brief_txt),
        "--output",
        str(green_json),
        "--visible-text",
        str(green_txt),
    ]
    if snapshot_path:
        build += ["--schedule-snapshot", str(snapshot_path)]
    run(build)
    run([sys.executable, str(PACK / "render_morning_green.py"), str(green_json), "-o", str(green_html)])

    def rel(p: Path) -> str:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()

    req = {
        "enabled": bool(args.enable),
        "requestId": f"morning-green-{iso}",
        "to": "nocturney@gmail.com",
        "subject": f"Velvet Factory · Morning Brief · {display}",
        "html": rel(green_html),
        "visibleText": rel(green_txt),
        "images": rel(assets_out),
        "embedRemoteImages": True,
        "remoteImageLimit": 8,
        "artifactDate": iso,
        "retentionMode": "rolling-current-transport",
    }
    args.request.parent.mkdir(parents=True, exist_ok=True)
    args.request.write_text(json.dumps(req, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "date": iso, "enabled": req["enabled"], "html": req["html"], "visibleText": req["visibleText"], "request": rel(args.request)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
