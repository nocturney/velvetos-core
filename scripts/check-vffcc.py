#!/usr/bin/env python3
"""Check vffcc catalog against HQ packs and playbooks. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
CATALOG = ROOT / "packages" / "vffcc" / "catalog.json"
PACK = ROOT / "packages" / "vffcc"
WRITEUP = ROOT / "docs" / "FCC-FIT.md"
VERDICTS = {"local", "later", "skip"}
REQUIRED_LOCKS = {
    "no-send-instagram",
    "no-send-gmail",
    "no-send-discord-telegram",
    "no-invented-prices",
    "no-invented-insights",
    "no-invented-quotas",
    "no-secrets-in-git",
    "no-fcc-on-cloud-agent",
    "no-vendor-fcc-tree",
    "no-second-coding-office",
}
REQUIRED_PLAYBOOKS = {
    "playbooks/route.md",
    "playbooks/cursor-thrift.md",
    "playbooks/local-offload.md",
}
FORBIDDEN_INSTALL_MARKERS = (
    "src/free_claude_code",
    "fcc-server.pid",
    "uv.lock",
)


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not MANIFEST.is_file():
        fail(f"missing {MANIFEST}")
    if not CATALOG.is_file():
        fail(f"missing {CATALOG}")
    if not WRITEUP.is_file():
        fail(f"missing {WRITEUP.relative_to(ROOT)}")

    manifest = json.loads(MANIFEST.read_text())
    catalog = json.loads(CATALOG.read_text())
    pack_names = {p["name"] for p in manifest["packs"]}

    if catalog.get("name") != "vffcc":
        fail("catalog name must be vffcc")
    source_url = (catalog.get("source") or {}).get("url")
    if source_url != "https://github.com/Alishahryar1/free-claude-code":
        fail(f"unexpected source url {source_url!r}")

    locks = set(catalog.get("locks") or [])
    missing_locks = REQUIRED_LOCKS - locks
    if missing_locks:
        fail(f"missing locks {sorted(missing_locks)}")

    if "vffcc" not in pack_names:
        fail("vffcc missing from packages/manifest.json")

    providers = catalog.get("providers") or []
    if len(providers) < 8:
        fail(f"expected at least 8 providers, got {len(providers)}")

    local_count = 0
    skip_count = 0
    for i, row in enumerate(providers):
        name = row.get("name") or row.get("id") or f"#{i}"
        verdict = row.get("verdict")
        if verdict not in VERDICTS:
            fail(f"{name}: verdict {verdict!r} not in {sorted(VERDICTS)}")
        if verdict == "local":
            local_count += 1
        if verdict == "skip":
            skip_count += 1
        packs = row.get("packs") or []
        if not packs:
            fail(f"{name}: no packs")
        for pack in packs:
            if pack not in pack_names:
                fail(f"{name}: unknown pack {pack!r}")
        playbook = row.get("playbook")
        if not playbook:
            fail(f"{name}: missing playbook")
        if not (PACK / playbook).is_file():
            fail(f"{name}: playbook missing {playbook}")

    if local_count < 3:
        fail(f"expected at least 3 local providers, got {local_count}")
    if skip_count < 2:
        fail(f"expected at least 2 skip providers, got {skip_count}")

    playbook_rows = catalog.get("playbooks") or []
    listed = {row.get("path") for row in playbook_rows}
    if listed != REQUIRED_PLAYBOOKS:
        fail(f"playbooks mismatch listed={sorted(listed)}")
    for row in playbook_rows:
        path = row.get("path")
        if not (PACK / path).is_file():
            fail(f"missing {path}")
        for pack in row.get("packs") or []:
            if pack not in pack_names:
                fail(f"{path}: unknown pack {pack!r}")

    on_disk = {f"playbooks/{p.name}" for p in (PACK / "playbooks").glob("*.md")}
    if on_disk != REQUIRED_PLAYBOOKS:
        fail(f"unexpected playbook files: disk={sorted(on_disk)}")

    for marker in FORBIDDEN_INSTALL_MARKERS:
        if (PACK / marker).exists():
            fail(f"FCC runtime marker must not live in the pack: {marker}")

    lock_text = (PACK / "LOCK.md").read_text()
    for needle in ("fcc-server", "Cloud Agent", "מפתחות"):
        if needle not in lock_text:
            fail(f"LOCK.md must mention {needle!r}")

    print(
        f"OK providers={len(providers)} local={local_count} skip={skip_count} "
        f"playbooks={len(REQUIRED_PLAYBOOKS)} locks={len(locks)} packs={len(pack_names)}"
    )


if __name__ == "__main__":
    main()
