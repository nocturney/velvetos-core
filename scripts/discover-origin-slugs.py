#!/usr/bin/env python3
"""Report Origin slug status. Never invent or write slugs. No send."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
NAMESPACE = "christian-velvet"


def load_packs() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return list(data.get("packs") or [])


def origin_repo_list() -> tuple[list[str], str]:
    """Return (slugs, note). Empty list is a valid scoped-HQ result."""
    origin = shutil.which("origin")
    if not origin:
        return [], "origin CLI not on PATH"
    proc = subprocess.run(
        [origin, "repo", "list", "--namespace", NAMESPACE],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        proc = subprocess.run(
            [origin, "repo", "list"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
        )
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    slugs: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("http") or line.startswith("Hint:"):
            continue
        if "/" in line and " " not in line:
            slugs.append(line)
    if proc.returncode != 0 and not slugs:
        return [], f"origin repo list failed: {(proc.stderr or proc.stdout or '').strip()[:200]}"
    if slugs == [f"{NAMESPACE}/velvet-factory-headquarters-os"]:
        return slugs, "list is HQ-only (token not scoped for tmp-* trees)"
    if not slugs:
        return [], "origin repo list returned no slugs"
    return slugs, "list ok"


def classify(pack: dict) -> str:
    status = pack.get("vendorStatus") or ""
    slug = pack.get("originSlug")
    if status == "hq-native":
        return "hq-native"
    if slug:
        return "known"
    return "unknown"


def main() -> int:
    packs = load_packs()
    listed, list_note = origin_repo_list()
    listed_set = set(listed)

    print("ORIGIN SLUG DISCOVERY — report only, do not invent")
    print(f"list: {list_note}")
    if listed:
        print("listed:")
        for slug in listed:
            print(f"  {slug}")
    print()

    unknown = 0
    known_missing = 0
    for pack in packs:
        name = pack["name"]
        kind = classify(pack)
        slug = pack.get("originSlug") or ""
        if kind == "hq-native":
            print(f"HQ     {name}")
            continue
        if kind == "known":
            if slug in listed_set:
                print(f"LISTED {name}  {slug}")
            else:
                known_missing += 1
                print(f"SCOPED {name}  {slug}  (not in this token's list — do not rewrite)")
            continue
        unknown += 1
        print(f"UNKNOWN {name}  bcId={pack.get('bcId')}  (keep unknown)")

    extras = sorted(
        s
        for s in listed_set
        if s.startswith(f"{NAMESPACE}/tmp-")
        and s not in {p.get("originSlug") for p in packs}
    )
    if extras:
        print()
        print("unmapped tmp slugs from list (human assign only):")
        for slug in extras:
            print(f"  {slug}")

    print()
    print(
        f"OK report unknown={unknown} known-not-in-list={known_missing} "
        f"listed={len(listed)} — no slugs written"
    )
    print("Fill path: docs/ORIGIN-SLUGS.md + docs/BACKUP.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
