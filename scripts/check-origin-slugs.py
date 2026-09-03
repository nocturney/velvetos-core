#!/usr/bin/env python3
"""Validate Origin slug catalog: unknown is allowed, invented slugs are not."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
PLAYBOOK = ROOT / "docs" / "ORIGIN-SLUGS.md"
BACKUP = ROOT / "docs" / "BACKUP.md"
README = ROOT / "README.md"
PACK_README = ROOT / "packages" / "README.md"
AGENTS = ROOT / "AGENTS.md"
VENDOR = ROOT / "scripts" / "vendor-origin-packs.sh"
DISCOVER = ROOT / "scripts" / "discover-origin-slugs.py"
CATALOG = ROOT / "packages" / "vfmem" / "catalog.json"

MAY_BE_UNKNOWN: set[str] = set()
HQ_NATIVE_EMBED = {
    "vfops",
    "vfcovers",
    "vfinsights",
    "vfbooks",
    "vfresearch",
    "vfbiz",
    "vfcopy",
    "vlicense",
    "vfseason",
    "vfsku",
    "vfbriefux",
}
KNOWN_SLUGS = {
    "vfigos": "christian-velvet/tmp-20e9908caebda9d0",
    "vfcost": "christian-velvet/tmp-8a55585f5a73bd06",
    "vfconvert": "christian-velvet/tmp-4460086f23171633",
    "vfgrowth": "christian-velvet/tmp-0093db8b6deea44f",
    "vfprod": "christian-velvet/tmp-c9ca74be9225ac7d",
    "vfsales": "christian-velvet/tmp-b467d4882113eabd",
}
SLUG_RE = re.compile(r"^christian-velvet/tmp-[0-9a-f]{8,}$")
FAKE_TMP = re.compile(r"christian-velvet/tmp-[0-9a-fA-F]+")
VENDOR_STATUSES = {
    "hq-native",
    "origin-slug-unknown",
    "origin-unreachable",
    "vendored",
}


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (MANIFEST, PLAYBOOK, BACKUP, README, PACK_README, AGENTS, VENDOR, DISCOVER, CATALOG):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    playbook = PLAYBOOK.read_text(encoding="utf-8")
    for needle in (
        "לא ממציאים Origin slug",
        "origin-slug-unknown",
        "token is not scoped",
        "discover-origin-slugs.py",
        "BACKUP.md",
        "vfops",
        "vfbriefux",
    ):
        if needle not in playbook:
            fail(f"ORIGIN-SLUGS.md missing {needle!r}")

    backup = BACKUP.read_text(encoding="utf-8")
    if "ORIGIN-SLUGS.md" not in backup:
        fail("BACKUP.md must point to ORIGIN-SLUGS.md")
    if "Do not invent slugs" not in backup:
        fail("BACKUP.md must keep Do not invent slugs")

    readme = README.read_text(encoding="utf-8")
    if "docs/ORIGIN-SLUGS.md" not in readme:
        fail("README.md must point to docs/ORIGIN-SLUGS.md")
    if "לא ממציאים" not in readme and "Do not invent" not in readme:
        fail("README.md must forbid inventing Origin slugs")

    pack_readme = PACK_README.read_text(encoding="utf-8")
    if "ORIGIN-SLUGS.md" not in pack_readme:
        fail("packages/README.md must point to ORIGIN-SLUGS.md")

    agents = AGENTS.read_text(encoding="utf-8")
    if "check-origin-slugs.py" not in agents:
        fail("AGENTS.md sensors must list check-origin-slugs.py")
    if "Invented Origin slug" not in agents and "Origin slug" not in agents:
        fail("AGENTS.md must record the Origin-slug anti-pattern")

    vendor = VENDOR.read_text(encoding="utf-8")
    if "SKIP $name: no Origin slug" not in vendor:
        fail("vendor script must SKIP packs with empty slug")
    if "origin repo list" not in vendor:
        fail("vendor script must keep origin repo list discovery")

    discover = DISCOVER.read_text(encoding="utf-8")
    if "Never invent" not in discover:
        fail("discover-origin-slugs.py must say Never invent")
    if "do not invent" not in discover.lower():
        fail("discover-origin-slugs.py must say do not invent")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    adr_ids = {a.get("id") for a in catalog.get("adrs") or []}
    if "no-invented-origin-slug" not in adr_ids:
        fail("vfmem catalog missing ADR no-invented-origin-slug")
    routes = catalog.get("routes") or []
    if not any("origin slug" in (r.get("q") or []) for r in routes):
        fail("vfmem catalog missing origin slug route")

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    packs = {p["name"]: p for p in data.get("packs") or []}
    for name in HQ_NATIVE_EMBED | set(KNOWN_SLUGS):
        if name not in packs:
            fail(f"manifest missing pack {name}")

    notes = " ".join(data.get("notes") or [])
    if "ORIGIN-SLUGS.md" not in notes:
        fail("manifest notes must point to ORIGIN-SLUGS.md")

    unknown_still = 0
    for name, pack in packs.items():
        status = pack.get("vendorStatus")
        slug = pack.get("originSlug")
        origin_md = ROOT / "packages" / name / "ORIGIN.md"
        if not origin_md.is_file():
            fail(f"missing {origin_md.relative_to(ROOT)}")
        text = origin_md.read_text(encoding="utf-8")

        if status not in VENDOR_STATUSES:
            fail(f"{name}: bad vendorStatus {status!r}")

        if name in HQ_NATIVE_EMBED:
            if status != "hq-native":
                fail(f"{name}: HQ embed must be vendorStatus hq-native, got {status!r}")
            if slug is not None:
                fail(f"{name}: hq-native embed must have originSlug null")
            if FAKE_TMP.search(text):
                fail(f"{name}: hq-native ORIGIN.md must not invent a tmp slug")
            continue

        if status == "hq-native":
            if slug is not None:
                fail(f"{name}: hq-native must have originSlug null")
            if FAKE_TMP.search(text):
                fail(f"{name}: hq-native ORIGIN.md must not invent a tmp slug")
            continue

        if name in KNOWN_SLUGS:
            expected = KNOWN_SLUGS[name]
            if slug != expected:
                fail(f"{name}: known slug must stay {expected}, got {slug!r}")
            if expected not in text:
                fail(f"{name}: ORIGIN.md must contain {expected}")
            if status == "origin-slug-unknown":
                fail(f"{name}: known slug cannot be origin-slug-unknown")
            continue

        if slug:
            if not SLUG_RE.match(str(slug)):
                fail(f"{name}: filled slug must look like christian-velvet/tmp-<hex>, got {slug!r}")
            if slug not in text:
                fail(f"{name}: ORIGIN.md must contain filled slug {slug}")
            if status == "origin-slug-unknown":
                fail(f"{name}: filled slug cannot stay origin-slug-unknown")
            continue

        if name in MAY_BE_UNKNOWN:
            if status != "origin-slug-unknown":
                fail(f"{name}: empty slug must be vendorStatus origin-slug-unknown")
            if "`unknown`" not in text and "unknown" not in text:
                fail(f"{name}: ORIGIN.md must say unknown while slug is empty")
            if FAKE_TMP.search(text):
                fail(f"{name}: ORIGIN.md has a tmp slug while manifest originSlug is null")
            unknown_still += 1
            continue

        fail(f"{name}: empty originSlug with vendorStatus {status!r} — set hq-native or origin-slug-unknown")

    for name in HQ_NATIVE_EMBED:
        if name not in playbook:
            fail(f"ORIGIN-SLUGS.md must name {name}")

    print(
        f"OK origin-slugs playbook packs={len(packs)} "
        f"hq-native-embed={len(HQ_NATIVE_EMBED)} still-unknown={unknown_still}"
    )


if __name__ == "__main__":
    main()
