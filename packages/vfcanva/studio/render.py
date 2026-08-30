#!/usr/bin/env python3
"""Render an Instagram frame to PNG with Chrome. No Canva, no git, no send."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
FRAME = ROOT / "frame.html"
CHROME = Path("/usr/bin/google-chrome-stable")
SIZES = {
    "ig_feed_square": (1080, 1080),
    "ig_feed_portrait": (1080, 1350),
    "ig_story": (1080, 1920),
    "ig_reel_cover": (1080, 1920),
    "ig_carousel_square": (1080, 1080),
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--format", default="ig_feed_square", choices=sorted(SIZES))
    p.add_argument("--hook", default="הדפסה בתלת־ממד · שדרות")
    p.add_argument("--job", default="")
    p.add_argument("--name", default="")
    args = p.parse_args()

    if not CHROME.is_file():
        print("FAIL chrome not found", file=sys.stderr)
        return 1

    OUT.mkdir(exist_ok=True)
    w, h = SIZES[args.format]
    qs = urlencode({"format": args.format, "hook": args.hook, "job": args.job})
    url = FRAME.resolve().as_uri() + "?" + qs
    stem = args.name or args.format
    dest = OUT / f"{stem}.png"

    cmd = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-sandbox",
        f"--window-size={w},{h}",
        f"--screenshot={dest}",
        url,
    ]
    run = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if run.returncode != 0 or not dest.is_file():
        print(run.stderr or run.stdout or "FAIL screenshot", file=sys.stderr)
        return 1
    print(f"OK {dest} {w}x{h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
