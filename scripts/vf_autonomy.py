#!/usr/bin/env python3
"""VelvetOS autonomy composition — projections over existing Office/HQ sources of truth.

No network. No send. No second queue/database/runtime.

CLI:
  python3 scripts/vf_autonomy.py status
  python3 scripts/vf_autonomy.py next-action
  python3 scripts/vf_autonomy.py blockers
  python3 scripts/vf_autonomy.py approvals
  python3 scripts/vf_autonomy.py context <id>
  python3 scripts/vf_autonomy.py quiet-plan
  python3 scripts/vf_autonomy.py snapshot
  python3 scripts/vf_autonomy.py selftest
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Jerusalem")

CONFIG = ROOT / "packages" / "velvetos" / "living-studio" / "AUTONOMY.json"
OUT = ROOT / "packages" / "velvetos" / "living-studio" / "data" / "autonomy-latest.json"
INBOX = ROOT / "office" / "control" / "inbox.json"
FOLLOWUPS = ROOT / "office" / "control" / "followups.json"
DEAD = ROOT / "office" / "control" / "dead-letter.json"
DECISIONS = ROOT / "office" / "control" / "decisions.jsonl"
APPROVAL_QUEUE = ROOT / "packages" / "vfgrowth" / "data" / "approval-queue.json"
JOBS = ROOT / "office" / "ledger" / "live" / "jobs.csv"
JOBS_TEMPLATE = ROOT / "office" / "ledger" / "templates" / "jobs.csv"
POLICY = ROOT / "office" / "control" / "POLICY.md"
CONTROL_PLANE = ROOT / "office" / "control-plane.json"

RISK_ORDER = {"red": 0, "orange": 1, "yellow": 2, "green": 3, "": 4}
CLOSED_STATES = {"closed", "closed_verified", "completed", "done", "resolved"}
WAITING_PREFIXES = ("waiting_", "blocked")


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            rows.append(json.loads(raw))
    return rows


def jobs_path() -> Path:
    return JOBS if JOBS.is_file() else JOBS_TEMPLATE


def load_jobs() -> list[dict[str, str]]:
    path = jobs_path()
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def flatten_inbox() -> list[dict[str, Any]]:
    data = load_json(INBOX, {"buckets": {}})
    rows: list[dict[str, Any]] = []
    for bucket, items in (data.get("buckets") or {}).items():
        for item in items or []:
            rows.append({**item, "bucket": bucket, "_source": "office/control/inbox.json"})
    return rows


def open_dead_letters() -> list[dict[str, Any]]:
    data = load_json(DEAD, {"items": []})
    rows = []
    for item in data.get("items") or []:
        state = str(item.get("status") or item.get("state") or "open").lower()
        if state not in CLOSED_STATES:
            rows.append({**item, "_source": "office/control/dead-letter.json"})
    return rows


def blockers() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    followups = load_json(FOLLOWUPS, {"items": []}).get("items") or []
    for item in followups:
        state = str(item.get("state") or "").lower()
        if state in CLOSED_STATES:
            continue
        if state.startswith(WAITING_PREFIXES) or item.get("next_action"):
            rows.append(
                {
                    "id": item.get("id"),
                    "state": item.get("state"),
                    "waiting_for": item.get("waiting_for") or _waiting_from_state(state),
                    "blocked_item": item.get("blocked_item") or item.get("contentId") or item.get("jobId") or item.get("sku"),
                    "since": item.get("since") or item.get("created_at"),
                    "safe_until": item.get("safe_until"),
                    "next_action": item.get("next_action"),
                    "risk": item.get("risk") or "",
                    "source": "office/control/followups.json",
                }
            )
    for item in flatten_inbox():
        if item.get("bucket") == "blocked":
            rows.append(
                {
                    "id": item.get("id"),
                    "state": item.get("state") or "blocked",
                    "waiting_for": item.get("waiting_for"),
                    "blocked_item": item.get("blocked_item") or item.get("title"),
                    "since": item.get("since") or item.get("created_at") or item.get("updatedAt"),
                    "safe_until": item.get("safe_until"),
                    "next_action": item.get("next_action"),
                    "risk": item.get("risk") or "orange",
                    "source": "office/control/inbox.json",
                }
            )
    for item in open_dead_letters():
        rows.append(
            {
                "id": item.get("id"),
                "state": item.get("status") or item.get("state") or "dead_letter",
                "waiting_for": item.get("waiting_for") or "exception_resolution",
                "blocked_item": item.get("title") or item.get("kind") or item.get("id"),
                "since": item.get("created_at") or item.get("updatedAt"),
                "safe_until": item.get("safe_until"),
                "next_action": item.get("next_action") or "reconcile_before_retry",
                "risk": item.get("risk") or "orange",
                "source": "office/control/dead-letter.json",
            }
        )
    return _dedupe(rows)


def _waiting_from_state(state: str) -> str | None:
    if state.startswith("waiting_for_"):
        return state.removeprefix("waiting_for_")
    if state == "blocked":
        return "blocker_resolution"
    return None


def approval_bundle() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in flatten_inbox():
        risk = str(item.get("risk") or "").lower()
        if item.get("bucket") == "approvals" or risk in {"orange", "red"}:
            rows.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title") or item.get("kind") or item.get("id"),
                    "risk": risk or "orange",
                    "action": item.get("next_action") or item.get("action"),
                    "source": "office/control/inbox.json",
                }
            )
    queue = load_json(APPROVAL_QUEUE, {"items": []})
    for item in queue.get("items") or []:
        gate = str(item.get("gate") or "")
        if gate and gate not in {"approved", "approved_for_manual_posting", "live_verified", "closed"}:
            rows.append(
                {
                    "id": item.get("content_id") or item.get("id"),
                    "title": f"Content approval · {item.get('format') or 'content'}",
                    "risk": "orange",
                    "action": gate,
                    "slot": item.get("slot"),
                    "source": "packages/vfgrowth/data/approval-queue.json",
                }
            )
    rows.sort(key=lambda r: (RISK_ORDER.get(str(r.get("risk") or ""), 4), str(r.get("id") or "")))
    return _dedupe(rows)


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = (str(row.get("source") or row.get("_source") or ""), str(row.get("id") or row.get("blocked_item") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def next_action() -> dict[str, Any]:
    approvals = approval_bundle()
    if approvals:
        top = approvals[0]
        return {
            "kind": "approval",
            "id": top.get("id"),
            "action": top.get("action") or "review_approval",
            "reason": "highest-gated owner decision currently present in canonical approval sources",
            "risk": top.get("risk"),
            "source": top.get("source"),
        }

    waiting = blockers()
    actionable = [row for row in waiting if row.get("next_action") and row.get("next_action") not in {"wait", "none"}]
    if actionable:
        top = sorted(actionable, key=lambda r: (RISK_ORDER.get(str(r.get("risk") or ""), 4), str(r.get("since") or "")))[0]
        return {
            "kind": "blocker",
            "id": top.get("id"),
            "action": top.get("next_action"),
            "reason": "canonical waiting item already declares a next action",
            "risk": top.get("risk"),
            "source": top.get("source"),
        }

    inbox = [i for i in flatten_inbox() if str(i.get("state") or "").lower() not in CLOSED_STATES]
    if inbox:
        top = inbox[0]
        return {
            "kind": "inbox",
            "id": top.get("id"),
            "action": top.get("next_action") or "review_current_state",
            "reason": "open canonical inbox item; no stronger approval/blocker action exists",
            "risk": top.get("risk") or "green",
            "source": top.get("_source"),
        }

    return {"kind": "none", "action": "no_action", "reason": "no open canonical action found"}


def context_pack(identifier: str) -> dict[str, Any]:
    needle = identifier.strip().lower()
    if not needle:
        raise SystemExit("FAIL context requires a non-empty id")

    found: dict[str, list[dict[str, Any]]] = {
        "inbox": [],
        "followups": [],
        "dead_letter": [],
        "approvals": [],
        "jobs": [],
        "decisions": [],
    }

    def matches(row: dict[str, Any]) -> bool:
        hay = json.dumps(row, ensure_ascii=False).lower()
        return needle in hay

    for row in flatten_inbox():
        if matches(row):
            found["inbox"].append(row)
    for row in load_json(FOLLOWUPS, {"items": []}).get("items") or []:
        if matches(row):
            found["followups"].append(row)
    for row in load_json(DEAD, {"items": []}).get("items") or []:
        if matches(row):
            found["dead_letter"].append(row)
    for row in load_json(APPROVAL_QUEUE, {"items": []}).get("items") or []:
        if matches(row):
            found["approvals"].append(row)
    for row in load_jobs():
        if matches(row):
            found["jobs"].append(row)
    for row in load_jsonl(DECISIONS):
        if matches(row):
            found["decisions"].append(row)

    return {
        "id": identifier,
        "generatedAt": now_iso(),
        "rule": "source-linked retrieval only; absence is unknown, not permission to invent",
        "sources": found,
        "counts": {key: len(value) for key, value in found.items()},
    }


def quiet_plan() -> dict[str, Any]:
    cfg = load_json(CONFIG, {})
    bg = next((c for c in cfg.get("components") or [] if c.get("id") == "background-executor-policy"), {})
    candidates: list[dict[str, Any]] = []
    for row in blockers():
        action = str(row.get("next_action") or "")
        if action in {"reconcile_before_retry", "wait_matching_print_done"}:
            candidates.append({"id": row.get("id"), "action": action, "source": row.get("source")})
    candidates.append({"id": "autonomy-snapshot", "action": "projection refresh", "source": "AUTONOMY.json"})
    return {
        "generatedAt": now_iso(),
        "mode": "quiet-hours-safe-plan",
        "allowed": bg.get("allowed") or [],
        "forbidden": bg.get("forbidden") or [],
        "candidates": candidates,
        "note": "plan/projection only; this command performs no external action and makes no business commitment",
    }


def snapshot() -> dict[str, Any]:
    cfg = load_json(CONFIG, {})
    data = {
        "name": "velvetos-autonomy-snapshot",
        "generatedAt": now_iso(),
        "contract": cfg.get("executionContract") or {},
        "componentStatus": {c.get("id"): c.get("status") for c in cfg.get("components") or []},
        "nextBestAction": next_action(),
        "blockers": blockers(),
        "approvalBundle": approval_bundle(),
        "quietPlan": quiet_plan(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def selftest() -> tuple[bool, list[str]]:
    errors: list[str] = []
    cfg = load_json(CONFIG, {})
    if not cfg:
        errors.append("missing AUTONOMY.json")
    if not CONTROL_PLANE.is_file():
        errors.append("missing office/control-plane.json")
    if not POLICY.is_file():
        errors.append("missing office/control/POLICY.md")
    ids = [c.get("id") for c in cfg.get("components") or []]
    expected = {
        "foundation-runtime-contract",
        "router-context-engine",
        "blocker-waiting-engine",
        "project-lifecycle-engine",
        "approval-system",
        "reliability-exception-engine",
        "work-prioritization",
        "background-executor-policy",
    }
    missing = sorted(expected - set(ids))
    if missing:
        errors.append("missing components: " + ", ".join(missing))
    contract = cfg.get("executionContract") or {}
    for required in ("run_id", "idempotency_key", "correlation_id"):
        if required not in (contract.get("requiredIds") or []):
            errors.append(f"execution contract missing {required}")
    states = set(contract.get("states") or [])
    if not {"queued", "running", "waiting_approval", "completed", "failed"}.issubset(states):
        errors.append("execution contract states incomplete")
    return not errors, errors


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS autonomy composition")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("next-action")
    sub.add_parser("blockers")
    sub.add_parser("approvals")
    ctx = sub.add_parser("context")
    ctx.add_argument("identifier")
    sub.add_parser("quiet-plan")
    sub.add_parser("snapshot")
    sub.add_parser("selftest")
    args = parser.parse_args()

    if args.cmd == "status":
        cfg = load_json(CONFIG, {})
        print_json(
            {
                "name": cfg.get("name"),
                "updatedAt": cfg.get("updatedAt"),
                "components": [{"id": c.get("id"), "status": c.get("status")} for c in cfg.get("components") or []],
                "nextBestAction": next_action(),
                "blockerCount": len(blockers()),
                "approvalCount": len(approval_bundle()),
            }
        )
        return 0
    if args.cmd == "next-action":
        print_json(next_action())
        return 0
    if args.cmd == "blockers":
        print_json(blockers())
        return 0
    if args.cmd == "approvals":
        print_json(approval_bundle())
        return 0
    if args.cmd == "context":
        print_json(context_pack(args.identifier))
        return 0
    if args.cmd == "quiet-plan":
        print_json(quiet_plan())
        return 0
    if args.cmd == "snapshot":
        print_json(snapshot())
        return 0
    if args.cmd == "selftest":
        ok, errors = selftest()
        if not ok:
            print_json({"ok": False, "errors": errors})
            return 1
        print_json({"ok": True, "nextBestAction": next_action()})
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
