#!/usr/bin/env python3
"""Check vfmskill catalog against vendored skills, HQ overlay, and packs. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
CATALOG = ROOT / "packages" / "vfmskill" / "catalog.json"
VENDOR = ROOT / "packages" / "vfmskill" / "vendor"
CONTEXT = ROOT / ".agents" / "product-marketing.md"
SKILL = ROOT / ".cursor" / "skills" / "vf-marketing-skills" / "SKILL.md"
VERDICTS = {"embed", "later", "skip"}
REQUIRED_LOCKS = {
    "no-send-instagram",
    "no-send-gmail",
    "no-invented-prices",
    "no-invented-insights",
    "no-ads-without-lead",
    "human-on-whatsapp",
}
REQUIRED_DOCS = {
    "packages/vfmskill/ORIGIN.md",
    "packages/vfmskill/EMBED.md",
    "packages/vfmskill/LOCK.md",
    "packages/vfmskill/SKILL.md",
    "packages/vfmskill/VENDOR.md",
    "packages/vfmskill/hq/PLAYBOOK.md",
    "packages/vfmskill/README.md",
    "packages/vfmskill/CONTEXT.md",
}


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (MANIFEST, CATALOG, CONTEXT, SKILL):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    for rel in REQUIRED_DOCS:
        if not (ROOT / rel).is_file():
            fail(f"missing {rel}")

    manifest = json.loads(MANIFEST.read_text())
    catalog = json.loads(CATALOG.read_text())
    pack_names = {p["name"] for p in manifest["packs"]}

    if catalog.get("name") != "vfmskill":
        fail("catalog name must be vfmskill")
    listed = catalog.get("source", {}).get("listedCount")
    if listed != 50:
        fail(f"listedCount expected 50, got {listed}")
    if not catalog.get("source", {}).get("commit"):
        fail("catalog source.commit is empty — run scripts/install-marketing-skills.sh")

    picks = catalog.get("picks") or []
    if len(picks) != 50:
        fail(f"expected 50 picks, got {len(picks)}")

    names = [p.get("name") for p in picks]
    if len(names) != len(set(names)):
        fail("duplicate pick names")

    embed: list[str] = []
    later = skip = 0
    for pick in picks:
        name = pick.get("name") or "?"
        verdict = pick.get("verdict")
        if verdict not in VERDICTS:
            fail(f"{name}: verdict {verdict!r} not in {sorted(VERDICTS)}")
        if verdict == "embed":
            embed.append(name)
        elif verdict == "later":
            later += 1
        else:
            skip += 1
        packs = pick.get("packs") or []
        if not packs:
            fail(f"{name}: no packs")
        for p in packs:
            if p not in pack_names:
                fail(f"{name}: unknown pack {p!r}")
        if not pick.get("note"):
            fail(f"{name}: missing note")

    expected_embed = catalog.get("embedCount")
    if expected_embed != len(embed):
        fail(f"embedCount {expected_embed} != embed picks {len(embed)}")
    if len(embed) != 15:
        fail(f"expected 15 embed skills, got {len(embed)}")

    for skill in embed:
        skill_md = VENDOR / skill / "SKILL.md"
        if not skill_md.is_file():
            fail(f"vendored SKILL.md missing for {skill}")
        if (VENDOR / skill / "evals").exists():
            fail(f"evals must not be vendored: {skill}")

    extra = sorted(
        p.name
        for p in VENDOR.iterdir()
        if p.is_dir() and p.name not in embed
    )
    if extra:
        fail(f"unexpected vendor dirs: {extra}")

    locks = set(catalog.get("locks") or [])
    for need in REQUIRED_LOCKS:
        if need not in locks:
            fail(f"missing lock {need}")

    if "vfmskill" not in pack_names:
        fail("vfmskill missing from packages/manifest.json")

    context = CONTEXT.read_text()
    for needle in ("050-2517000", "שדרות", "@velvets_cloud", "X ₪", "חסר"):
        if needle not in context:
            fail(f"product-marketing.md missing {needle!r}")

    skill = SKILL.read_text()
    if "send_message" in skill and "Never" not in skill and "does not send" not in skill:
        fail("Cursor skill must not invite Gmail send")
    if "שלחו DM" not in skill:
        fail("Cursor skill must ban שלחו DM")
    if "050-2517000" not in skill:
        fail("Cursor skill must keep WhatsApp CTA")

    print(
        f"OK picks={len(picks)} embed={len(embed)} later={later} skip={skip} "
        f"vendor={len(embed)} listed={listed} pin={catalog['source']['commitShort']}"
    )


if __name__ == "__main__":
    main()
