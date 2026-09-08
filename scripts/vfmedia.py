#!/usr/bin/env python3
"""Validate the single VelvetOS media catalog. No network. No Drive writes."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "vfmedia"
CATALOG = PACK / "catalog.json"
SCHEMA = PACK / "catalog.schema.json"
FOLDERS = PACK / "FOLDERS.json"
ROOT_ID = "1Yg3Rj0hKWTa86EXjaeu-f7CQXswSRMCv"
STAGE_IDS = {
    "inbox": "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
    "source": "1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6",
    "in_progress": "13H42Kpif3GPNaHlnI24YiHn-m1IS1k5a",
    "approved": "1LitaCUDgVk7njkWAvC-MX-noQOkyr-ib",
}
ITEM_FIELDS = (
    "id",
    "sourceFile",
    "viewDescription",
    "uploadedAt",
    "productLink",
    "status",
    "assignee",
    "derivativeIds",
    "sourceLinks",
    "versionApproval",
)
ILS_NUMBER = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")
SKU_KEY = re.compile(r"(?i)^(sku|skus|מק״ט|מק\"ט)$")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_no_ils(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for m in ILS_NUMBER.finditer(text):
        snippet = text[max(0, m.start() - 20) : m.end() + 8]
        if "X ₪" in snippet:
            continue
        if re.search(r"(בלי|אין|לא)\s*₪|₪\s*רק", snippet):
            continue
        fail(f"possible invented ILS in {path.relative_to(ROOT)}: {snippet!r}")


def validate_drive_ref(label: str, ref: object) -> None:
    if not isinstance(ref, dict):
        fail(f"{label} must be an object with id+url")
    if not ref.get("id") or not ref.get("url"):
        fail(f"{label} needs source file id+url")
    if "example" in str(ref["id"]).lower() or str(ref["id"]) in {"TODO", "xxx", "placeholder"}:
        fail(f"{label} invented Drive id")


def validate_item(item: dict, index: int) -> None:
    missing = [k for k in ITEM_FIELDS if k not in item]
    if missing:
        fail(f"items[{index}] missing fields {missing}")
    extra = [k for k in item if k not in ITEM_FIELDS]
    if extra:
        fail(f"items[{index}] unknown fields {extra} — do not invent SKU keys")
    for key in item:
        if SKU_KEY.match(str(key)):
            fail(f"items[{index}] has SKU field {key!r} — catalog is not a SKU shelf")
    validate_drive_ref(f"items[{index}].sourceFile", item["sourceFile"])
    if not str(item.get("viewDescription") or "").strip():
        fail(f"items[{index}].viewDescription empty — describe what is visible")
    if not str(item.get("uploadedAt") or "").strip():
        fail(f"items[{index}].uploadedAt missing")
    if item["status"] not in STAGE_IDS:
        fail(f"items[{index}].status {item['status']!r} not a vault stage")
    if item["productLink"] is not None and not isinstance(item["productLink"], str):
        fail(f"items[{index}].productLink must be string or null")
    if not isinstance(item["derivativeIds"], list):
        fail(f"items[{index}].derivativeIds must be a list")
    for j, der in enumerate(item["derivativeIds"]):
        validate_drive_ref(f"items[{index}].derivativeIds[{j}]", der)
    if not isinstance(item["sourceLinks"], list):
        fail(f"items[{index}].sourceLinks must be a list")
    approval = item["versionApproval"]
    if not isinstance(approval, dict) or approval.get("state") not in {
        "none",
        "pending",
        "approved",
        "rejected",
    }:
        fail(f"items[{index}].versionApproval.state invalid")
    if item["status"] == "approved" and approval.get("state") != "approved":
        fail(
            f"items[{index}] status=approved but versionApproval is not approved "
            "(approved folder alone is not proof)"
        )


def cmd_validate(_args: argparse.Namespace) -> int:
    for path in (CATALOG, SCHEMA, FOLDERS):
        assert_no_ils(path)
    catalog = load_json(CATALOG)
    schema = load_json(SCHEMA)
    folders = load_json(FOLDERS)
    if catalog.get("name") != "vfmedia-catalog":
        fail("catalog.json name must be vfmedia-catalog")
    if catalog.get("oneCatalog") is not True:
        fail("catalog.json oneCatalog must be true")
    if catalog.get("vaultRootId") != ROOT_ID:
        fail("catalog.json vaultRootId mismatch")
    if folders.get("root", {}).get("id") != ROOT_ID:
        fail("FOLDERS.json root id mismatch")
    by_status = {row["status"]: row["id"] for row in folders.get("stages") or []}
    if by_status != STAGE_IDS:
        fail(f"FOLDERS.json stage ids mismatch: {by_status}")
    required = set(schema.get("required") or [])
    if not {"name", "oneCatalog", "vaultRootId", "items"} <= required:
        fail("catalog.schema.json missing required document keys")
    item_req = set(
        ((schema.get("$defs") or {}).get("mediaItem") or {}).get("required") or []
    )
    if set(ITEM_FIELDS) != item_req:
        fail(f"schema mediaItem fields mismatch: {sorted(item_req)}")
    items = catalog.get("items")
    if not isinstance(items, list):
        fail("catalog.json items must be a list")
    seen: set[str] = set()
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            fail(f"items[{i}] must be an object")
        rid = item.get("id")
        if rid in seen:
            fail(f"duplicate catalog id {rid!r}")
        seen.add(rid)
        validate_item(item, i)
    print(f"OK vfmedia catalog items={len(items)} oneCatalog=true")
    return 0


def cmd_folders(_args: argparse.Namespace) -> int:
    folders = load_json(FOLDERS)
    print(f"root\t{folders['root']['id']}\t{folders['root']['title']}")
    for row in folders.get("stages") or []:
        print(f"{row['status']}\t{row['id']}\t{row['title']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS shared media catalog (no Drive writes).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="validate catalog.json against the locked schema").set_defaults(
        func=cmd_validate
    )
    sub.add_parser("folders", help="print locked Drive folder ids").set_defaults(func=cmd_folders)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
