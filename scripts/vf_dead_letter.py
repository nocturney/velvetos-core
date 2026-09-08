#!/usr/bin/env python3
"""Dead-letter queue helpers. No network. No send."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "packages" / "vfharness" / "dead-letter" / "queue.json"
SCHEMA_KEYS = (
    "actionId",
    "jobOrContentId",
    "attemptedTool",
    "time",
    "failureSummary",
    "retries",
    "fallbackAttempted",
    "currentState",
    "nextSafeAction",
    "riskColor",
    "christianRequired",
)


def load() -> dict:
    return json.loads(QUEUE.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    QUEUE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def cmd_list(_: argparse.Namespace) -> int:
    data = load()
    open_items = [i for i in data.get("items") or [] if not i.get("resolved")]
    print(json.dumps({"open": len(open_items), "items": open_items}, ensure_ascii=False, indent=2))
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    data = load()
    item = {
        "actionId": args.action_id,
        "jobOrContentId": args.job,
        "attemptedTool": args.tool,
        "time": args.time or datetime.now(timezone.utc).isoformat(),
        "failureSummary": args.summary,
        "retries": args.retries,
        "fallbackAttempted": args.fallback,
        "currentState": args.state,
        "nextSafeAction": args.next,
        "riskColor": args.risk,
        "christianRequired": args.christian,
        "resolved": False,
        "resolvedAt": None,
    }
    for k in SCHEMA_KEYS:
        if item.get(k) is None or item.get(k) == "":
            print(f"FAIL missing {k}", file=sys.stderr)
            return 1
    data.setdefault("items", []).append(item)
    save(data)
    print(f"OK added {item['actionId']}")
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    data = load()
    found = False
    for item in data.get("items") or []:
        if item.get("actionId") == args.action_id:
            item["resolved"] = True
            item["resolvedAt"] = datetime.now(timezone.utc).isoformat()
            item["resolveNote"] = args.note or "resolved"
            found = True
            break
    if not found:
        print(f"FAIL actionId not found: {args.action_id}", file=sys.stderr)
        return 1
    save(data)
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
