#!/usr/bin/env python3
"""Validate the locked VelvetOS shared media vault. No network. No Drive writes."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "MEDIA-VAULT.md"
SWC = ROOT / "docs" / "SHARED-WORK-COORDINATION.md"
PACK = ROOT / "packages" / "vfmedia"
CATALOG = PACK / "catalog.json"
SCHEMA = PACK / "catalog.schema.json"
FOLDERS = PACK / "FOLDERS.json"
CATALOG_MD = PACK / "CATALOG.md"
LOCK = PACK / "LOCK.md"
SKILL = PACK / "SKILL.md"
ORIGIN = PACK / "ORIGIN.md"
CLI = ROOT / "scripts" / "vfmedia.py"
LOOP = ROOT / "packages" / "vfops" / "LOOP.json"
MANIFEST = ROOT / "packages" / "manifest.json"
AGENTS = ROOT / "AGENTS.md"
DESK = ROOT / ".cursor" / "vf-desk.json"
MEM = ROOT / "packages" / "vfmem" / "catalog.json"
SLOTS = ROOT / "packages" / "vfops" / "hq" / "BRIEF-SLOTS.md"

ROOT_ID = "1Yg3Rj0hKWTa86EXjaeu-f7CQXswSRMCv"
FOLDER_IDS = {
    "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
    "1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6",
    "13H42Kpif3GPNaHlnI24YiHn-m1IS1k5a",
    "1LitaCUDgVk7njkWAvC-MX-noQOkyr-ib",
}
NEEDLES_DOCS = (
    ROOT_ID,
    "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
    "1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6",
    "13H42Kpif3GPNaHlnI24YiHn-m1IS1k5a",
    "1LitaCUDgVk7njkWAvC-MX-noQOkyr-ib",
    "קטלוג אחד",
    "תפעול",
    "העלאה ≠ אישור",
    "תיקיית «מאושר לפרסום» לבד ≠ הוכחת אישור",
    "לא ממציאים ₪",
    "אין שינוי הרשאות שיתוף",
    "GrokBot",
    "Cursor",
    "Drive MCP",
)
NEEDLES_SWC = (
    "vfmedia",
    "Drive MCP",
    "תפעול",
    "Cursor",
    "GrokBot",
)
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def assert_no_ils(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for m in ILS_NUMBER.finditer(text):
        snippet = text[max(0, m.start() - 20) : m.end() + 8]
        if "X ₪" in snippet:
            continue
        if re.search(r"(בלי|אין|לא)\s*₪|₪\s*רק", snippet):
            continue
        fail(f"possible invented ILS in {path.relative_to(ROOT)}: {snippet!r}")


def main() -> None:
    for path in (
        DOCS,
        SWC,
        CATALOG,
        SCHEMA,
        FOLDERS,
        CATALOG_MD,
        LOCK,
        SKILL,
        ORIGIN,
        CLI,
        LOOP,
        MANIFEST,
        AGENTS,
        DESK,
        MEM,
        SLOTS,
    ):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    for path in (DOCS, CATALOG_MD, LOCK, SKILL, ORIGIN, CATALOG, FOLDERS, SWC, SLOTS):
        assert_no_ils(path)

    docs = DOCS.read_text(encoding="utf-8")
    for needle in NEEDLES_DOCS:
        if needle not in docs:
            fail(f"MEDIA-VAULT.md missing {needle!r}")
    if "מק״ט" not in docs and "SKU" not in docs:
        fail("MEDIA-VAULT.md must forbid invented SKUs")

    swc = SWC.read_text(encoding="utf-8")
    for needle in NEEDLES_SWC:
        if needle not in swc:
            fail(f"SHARED-WORK-COORDINATION.md missing {needle!r}")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("items") not in ([],):
        # Rows are allowed later; each must still pass vfmedia.py validate.
        pass
    if catalog.get("oneCatalog") is not True:
        fail("catalog.json must lock oneCatalog")
    blob = json.dumps(catalog, ensure_ascii=False)
    if re.search(r'"sku"', blob, re.I):
        fail("catalog.json must not invent SKU fields")

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    item_req = ((schema.get("$defs") or {}).get("mediaItem") or {}).get("required") or []
    for field in (
        "sourceFile",
        "viewDescription",
        "uploadedAt",
        "productLink",
        "status",
        "assignee",
        "derivativeIds",
        "sourceLinks",
        "versionApproval",
    ):
        if field not in item_req:
            fail(f"catalog.schema.json mediaItem missing {field}")

    folders = json.loads(FOLDERS.read_text(encoding="utf-8"))
    if folders.get("sharePermissionChanges") != "forbidden":
        fail("FOLDERS.json must forbid share permission changes")
    if folders.get("deleteFiles") != "forbidden":
        fail("FOLDERS.json must forbid deletes")
    ids = {row["id"] for row in folders.get("stages") or []}
    if ids != FOLDER_IDS:
        fail(f"FOLDERS.json ids mismatch {ids}")

    lock = LOCK.read_text(encoding="utf-8")
    for needle in ("קטלוג אחד", "העלאה ≠ אישור", "לא ממציאים", "שיתוף"):
        if needle not in lock:
            fail(f"LOCK.md missing {needle!r}")

    origin = ORIGIN.read_text(encoding="utf-8")
    if "hq-native" not in origin:
        fail("ORIGIN.md must stay hq-native")
    if re.search(r"christian-velvet/tmp-", origin):
        fail("ORIGIN.md must not invent an Origin slug")

    loop = json.loads(LOOP.read_text(encoding="utf-8"))
    ids_loop = [p["id"] for p in loop.get("packs") or []]
    if "vfmedia" not in ids_loop:
        fail("LOOP.json must consume vfmedia")
    media = next(p for p in loop["packs"] if p["id"] == "vfmedia")
    if "vfmedia.py" not in (media.get("consume") or ""):
        fail("vfmedia consume must be vfmedia.py validate")

    packs = {p["name"] for p in json.loads(MANIFEST.read_text(encoding="utf-8")).get("packs") or []}
    if "vfmedia" not in packs:
        fail("vfmedia missing from packages/manifest.json")

    if "check-vfmedia.py" not in AGENTS.read_text(encoding="utf-8"):
        fail("AGENTS.md sensor table must list check-vfmedia.py")

    desk = json.loads(DESK.read_text(encoding="utf-8"))
    ops = next((s for s in desk.get("seats") or [] if s.get("id") == "ops"), None)
    if not ops or "vfmedia" not in (ops.get("packs") or []):
        fail("desk ops seat must include vfmedia")
    drive = (desk.get("tools") or {}).get("drive") or {}
    if ROOT_ID not in json.dumps(drive, ensure_ascii=False):
        fail("desk drive tool must name the locked vault root id")

    mem = json.loads(MEM.read_text(encoding="utf-8"))
    if not any(r.get("pack") == "vfmedia" for r in mem.get("routes") or []):
        fail("vfmem catalog must route media vault to vfmedia")

    if "vfmedia" not in SLOTS.read_text(encoding="utf-8"):
        fail("BRIEF-SLOTS.md must mention vfmedia")

    other_catalogs = list((ROOT / "packages").glob("**/media-catalog.json"))
    if other_catalogs:
        fail(f"parallel media catalog files: {other_catalogs}")

    for legacy in ("constitution/MEDIA-VAULT.md", "scripts/check-media-vault.py"):
        if (ROOT / legacy).exists():
            fail(f"parallel media procedure/sensor: {legacy}")
    # The merge can be textually clean while routing tools to a second catalog.
    for relative in (
        "AGENTS.md", "constitution/CONSTITUTION.md",
        "packages/vfigos/SKILL.md", "packages/vfigos/SEND.md",
        "packages/vfops/LOOP.json", ".cursor/vf-desk.json",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for legacy in ("constitution/MEDIA-VAULT.md", "media-catalog.json", "check-media-vault.py", "needs-appointment"):
            if legacy in text:
                fail(f"stale media vault reference in {relative}: {legacy}")
        if relative != ".cursor/vf-desk.json":
            for canonical in ("docs/MEDIA-VAULT.md", "packages/vfmedia/catalog.json"):
                if canonical not in text:
                    fail(f"missing canonical media vault reference in {relative}: {canonical}")

    proc = subprocess.run(
        [sys.executable, str(CLI), "validate"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        fail(f"vfmedia.py validate: {proc.stderr or proc.stdout}")

    print("OK vfmedia vault+catalog locked (one catalog, no Drive writes)")


if __name__ == "__main__":
    main()
