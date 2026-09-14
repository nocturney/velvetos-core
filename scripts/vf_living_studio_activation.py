#!/usr/bin/env python3
"""Activation/evidence sweep for Living Studio capabilities.

This is connective tissue only. It calls the existing Living Studio functions and
writes one canonical activation receipt; it does not create a second Control Plane
or business database.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vf_living_studio as studio  # noqa: E402

TZ = ZoneInfo("Asia/Jerusalem")
LATEST = ROOT / "packages" / "velvetos" / "living-studio" / "data" / "activation-latest.json"
HISTORY = ROOT / "packages" / "velvetos" / "living-studio" / "data" / "activation-history.jsonl"


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _cap(state: str, verification: str, evidence: dict) -> dict:
    return {"state": state, "verification": verification, "evidence": evidence}


def sweep(*, write: bool = False) -> dict:
    """Exercise the six formerly-partial Living Studio surfaces.

    Empty result sets are valid. The proof is that the canonical route executed
    against current SoTs and returned an evidence-bearing result without inventing
    business facts.
    """
    caps: dict[str, dict] = {}

    pe = studio.print_engineering()
    pe_ok = pe.get("hq_print") is False and bool(pe.get("cli")) and bool(pe.get("router"))
    caps["print-engineering"] = _cap(
        "equivalent" if pe_ok else "failed",
        "vfprod_router_resolved" if pe_ok else "router_invalid",
        {"router": pe.get("router"), "cli": pe.get("cli"), "hq_print": pe.get("hq_print")},
    )

    fm = studio.failure_museum()
    fm_ok = isinstance(fm.get("entries"), list) and isinstance(fm.get("count"), int)
    caps["failure-museum"] = _cap(
        "complete" if fm_ok else "failed",
        "dead_letter_projection_executed" if fm_ok else "projection_invalid",
        {"count": fm.get("count"), "sources": fm.get("sources")},
    )

    lab = studio.lab_list()
    lab_ok = isinstance(lab.get("experiments"), list) and isinstance(lab.get("count"), int)
    caps["velvet-lab"] = _cap(
        "complete" if lab_ok else "failed",
        "canonical_experiment_event_stream_readable" if lab_ok else "lab_log_invalid",
        {"count": lab.get("count"), "rule": lab.get("rule")},
    )

    devil = studio.commercial_qa("devil", None, "שלחו DM במחיר 99 ₪ עכשיו")
    quote = studio.commercial_qa("quote-confidence", None, "הצעה ללקוח בלי מספרים")
    qa_ok = bool(devil.get("blocked_fields")) and "grams" in (quote.get("missing_inputs") or [])
    caps["commercial-qa"] = _cap(
        "equivalent" if qa_ok else "failed",
        "behavioral_fail_closed_probe" if qa_ok else "qa_probe_failed",
        {
            "devil_blocked_fields": devil.get("blocked_fields"),
            "quote_missing_inputs": quote.get("missing_inputs"),
            "note": "diagnostic Living Studio mode; production quote/public gates remain vfcost/vfcopy/PREFLIGHT",
        },
    )

    opps = studio.opportunity_intelligence(write=write)
    opp_ok = isinstance(opps, list)
    caps["opportunity-intelligence"] = _cap(
        "complete" if opp_ok else "failed",
        "canonical_radar_executed" if opp_ok else "radar_invalid",
        {"count": len(opps) if opp_ok else None, "sample": opps[:1] if opp_ok else []},
    )

    invisible = studio.invisible_work(write=write)
    inv_ok = isinstance(invisible, list)
    caps["invisible-work-detector"] = _cap(
        "complete" if inv_ok else "failed",
        "current_sots_scanned" if inv_ok else "detector_invalid",
        {"count": len(invisible) if inv_ok else None, "high": [x.get("id") for x in invisible if x.get("impact") == "high"][:10] if inv_ok else []},
    )

    ok = all(v["state"] in {"complete", "equivalent"} for v in caps.values())
    receipt = {
        "schema": "vf.living-studio.activation.v1",
        "generatedAt": now_iso(),
        "status": "verified" if ok else "failed",
        "capabilities": caps,
        "rule": "activation evidence comes from canonical functions/SoTs; empty findings are valid; no second runtime",
    }
    if write:
        LATEST.parent.mkdir(parents=True, exist_ok=True)
        LATEST.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _append_jsonl(HISTORY, receipt)
    return receipt


def lab_result(experiment_id: str, status: str, result: str, evidence: str) -> dict:
    """Append an evidence-bearing result event to the existing LAB_LOG event stream."""
    if status not in {"adopted", "rejected", "inconclusive"}:
        raise ValueError("status must be adopted|rejected|inconclusive")
    if not result.strip() or not evidence.strip():
        raise ValueError("result and evidence are required; no evidence-free experiment close")
    lab = studio.lab_list()
    known = {row.get("experimentId") for row in lab.get("experiments") or []}
    if experiment_id not in known:
        raise ValueError(f"unknown experimentId {experiment_id}")
    row = {
        "event": "experiment_result",
        "experimentId": experiment_id,
        "timestamp": now_iso(),
        "status": status,
        "result": result.strip(),
        "evidence": [evidence.strip()],
        "rule": "result requires explicit evidence; no invented success",
    }
    studio.append_jsonl(studio.LAB_LOG, row)
    studio.emit_signal("lab.experiment.result", "velvet-lab", experiment_id, status=status)
    studio.receipt(
        action="lab_result",
        source="velvet-lab",
        affected=experiment_id,
        resulting_state=status,
        verification="evidence_recorded",
        evidence={"evidence": evidence.strip()},
    )
    return row


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sweep")
    s.add_argument("--write", action="store_true")
    lr = sub.add_parser("lab-result")
    lr.add_argument("--id", required=True)
    lr.add_argument("--status", required=True, choices=["adopted", "rejected", "inconclusive"])
    lr.add_argument("--result", required=True)
    lr.add_argument("--evidence", required=True)
    args = p.parse_args()
    try:
        if args.cmd == "sweep":
            out = sweep(write=args.write)
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0 if out["status"] == "verified" else 1
        out = lab_result(args.id, args.status, args.result, args.evidence)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
