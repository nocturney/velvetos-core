#!/usr/bin/env python3
"""Thin wrapper — canonical dead-letter is office/control/dead-letter.json via vf_control_plane.

Do not maintain a second queue under packages/vfharness/dead-letter/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vf_control_plane import (  # noqa: E402
    DEAD,
    list_dead_letters,
    load_json,
    now_iso,
    record_dead_letter,
    resolve_dead_letter,
    today,
    write_json,
)


def cmd_list(_: argparse.Namespace) -> int:
    open_items = list_dead_letters(open_only=True)
    print(
        json.dumps(
            {
                "sourceOfTruth": "office/control/dead-letter.json",
                "open": len(open_items),
                "items": open_items,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    risk = (args.risk or "YELLOW").lower()
    item = record_dead_letter(
        action=args.action_id,
        source=args.tool,
        reason=args.summary,
        risk=risk,
        owner_required=bool(args.christian),
        correlation_id=args.job or None,
        attempts=int(args.retries),
        last_error=args.summary,
        next_safe_action=args.next,
    )
    # Preserve legacy field aliases on the same canonical item (still one store)
    data = load_json(DEAD, {"items": []})
    for row in data.get("items") or []:
        if row.get("id") == item["id"]:
            row["actionId"] = args.action_id
            row["jobOrContentId"] = args.job
            row["attemptedTool"] = args.tool
            row["time"] = args.time or now_iso()
            row["failureSummary"] = args.summary
            row["retries"] = args.retries
            row["fallbackAttempted"] = bool(args.fallback)
            row["currentState"] = args.state
            row["nextSafeAction"] = args.next
            row["riskColor"] = (args.risk or "YELLOW").upper()
            row["christianRequired"] = bool(args.christian)
            break
    data["updatedAt"] = today()
    write_json(DEAD, data)
    print(f"OK added {args.action_id} → office/control/dead-letter.json ({item['id']})")
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    ok = resolve_dead_letter(args.action_id, note=args.note or "resolved")
    if not ok:
        print(f"FAIL actionId/id not found: {args.action_id}", file=sys.stderr)
        return 1
    print(f"OK resolved {args.action_id}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("list")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("add")
    s.add_argument("--action-id", required=True)
    s.add_argument("--job", required=True)
    s.add_argument("--tool", required=True)
    s.add_argument("--summary", required=True)
    s.add_argument("--retries", type=int, default=2)
    s.add_argument("--fallback", action="store_true")
    s.add_argument("--state", default="deadLetter")
    s.add_argument("--next", required=True)
    s.add_argument("--risk", default="YELLOW", choices=["GREEN", "YELLOW", "ORANGE", "RED"])
    s.add_argument("--christian", action="store_true")
    s.add_argument("--time", default="")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("resolve")
    s.add_argument("--action-id", required=True)
    s.add_argument("--note", default="")
    s.set_defaults(func=cmd_resolve)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
