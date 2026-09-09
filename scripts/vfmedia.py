#!/usr/bin/env python3
"""VelvetOS shared media catalog CLI.

Subcommands:
  validate — schema/locks check only. No network. No Drive writes. Not a monitor.
  folders  — print locked Drive folder ids
  intake   — durable auto-intake runner (scan inbox → catalog → verify → source)
"""
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
OPTIONAL_ITEM_FIELDS = ("intake", "visualReview")
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


def validate_intake_block(item: dict, index: int) -> None:
    intake = item.get("intake")
    if intake is None:
        return
    if not isinstance(intake, dict):
        fail(f"items[{index}].intake must be an object")
    phase = intake.get("phase")
    if phase not in {"registered", "verified"}:
        fail(f"items[{index}].intake.phase invalid: {phase!r}")
    # Visual review must not be required for verified
    visual = item.get("visualReview")
    if visual is None:
        return
    if not isinstance(visual, dict):
        fail(f"items[{index}].visualReview must be an object")
    if visual.get("state") not in {"none", "pending", "done"}:
        fail(f"items[{index}].visualReview.state invalid")


def validate_item(item: dict, index: int) -> None:
    missing = [k for k in ITEM_FIELDS if k not in item]
    if missing:
        fail(f"items[{index}] missing fields {missing}")
    allowed = set(ITEM_FIELDS) | set(OPTIONAL_ITEM_FIELDS)
    extra = [k for k in item if k not in allowed]
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
    validate_intake_block(item, index)


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
    props = ((schema.get("$defs") or {}).get("mediaItem") or {}).get("properties") or {}
    for opt in OPTIONAL_ITEM_FIELDS:
        if opt not in props:
            fail(f"schema mediaItem missing optional {opt}")
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
    print(f"OK vfmedia catalog items={len(items)} oneCatalog=true (validate≠monitor)")
    return 0


def cmd_folders(_args: argparse.Namespace) -> int:
    folders = load_json(FOLDERS)
    print(f"root\t{folders['root']['id']}\t{folders['root']['title']}")
    for row in folders.get("stages") or []:
        print(f"{row['status']}\t{row['id']}\t{row['title']}")
    return 0


def _intake_ns(args: argparse.Namespace) -> argparse.Namespace:
    return args


def cmd_intake(args: argparse.Namespace) -> int:
    # Load pack-local module (packages/ is not a Python package root)
    if str(PACK) not in sys.path:
        sys.path.insert(0, str(PACK))
    from intake import runner as intake_runner  # type: ignore

    if args.intake_cmd == "status":
        return intake_runner.cmd_status(args)
    if args.intake_cmd == "selftest":
        return intake_runner.run_selftest(args)
    if args.intake_cmd == "apply-moves":
        if not args.confirmed:
            fail("apply-moves requires --confirmed PATH")
        return intake_runner.apply_confirmed_moves(Path(args.confirmed))
    if args.intake_cmd == "run":
        return intake_runner.run_intake(args)
    fail(f"unknown intake command {args.intake_cmd}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="VelvetOS shared media catalog. validate=check only; intake=auto runner."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "validate",
        help="validate catalog.json against the locked schema (no Drive; not a monitor)",
    ).set_defaults(func=cmd_validate)
    sub.add_parser("folders", help="print locked Drive folder ids").set_defaults(func=cmd_folders)

    intake = sub.add_parser("intake", help="durable auto-intake (inbox→catalog→verify→source)")
    intake_sub = intake.add_subparsers(dest="intake_cmd", required=True)

    p_run = intake_sub.add_parser("run", help="scan inbox and intake")
    p_run.add_argument(
        "--provider",
        choices=("google", "listing", "fixture"),
        default="google",
        help="google=API credentials; listing=MCP export; fixture=selftest data",
    )
    p_run.add_argument("--listing", help="path to inbox listing JSON (listing/fixture)")
    p_run.add_argument(
        "--move-mode",
        choices=("pending", "memory"),
        default="pending",
        help="listing provider: pending writes Drive actions for MCP apply; memory for tests",
    )
    p_run.add_argument("--page-size", type=int, default=50)
    p_run.add_argument("--page-token", default=None)
    p_run.add_argument("--reset-pagination", action="store_true")
    p_run.add_argument("--max-files", type=int, default=50)
    p_run.add_argument("--register-only", action="store_true")
    p_run.add_argument("--only-file-id", default=None)
    p_run.add_argument(
        "--mark-activation",
        action="store_true",
        help="mark activation.proven when this run processes a new file",
    )
    p_run.set_defaults(func=cmd_intake)

    p_apply = intake_sub.add_parser("apply-moves", help="confirm pending moves after Drive MCP/API")
    p_apply.add_argument("--confirmed", required=True, help="JSON with movedFileIds[]")
    p_apply.set_defaults(func=cmd_intake)

    intake_sub.add_parser("status", help="print runner + phase counts").set_defaults(func=cmd_intake)
    intake_sub.add_parser("selftest", help="offline intake proof (no Drive)").set_defaults(
        func=cmd_intake
    )

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
