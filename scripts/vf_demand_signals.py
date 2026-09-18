#!/usr/bin/env python3
"""Normalize external public demand evidence for VelvetOS. No network. No send.

Acquisition stays provider-specific. This helper accepts already-acquired public facts,
normalizes them into a stable DemandSignalPacket, and refuses synthetic demand scores.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ALLOWED_KINDS = {
    "search_interest",
    "search_suggestion",
    "marketplace_observation",
    "serp_observation",
}


def fail(msg: str, code: int = 2) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def is_public_http_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def finite_number(value: Any) -> float | int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return value
    if isinstance(value, str):
        s = value.strip().replace(",", "")
        if not s:
            return None
        try:
            f = float(s)
        except ValueError:
            return None
        if math.isfinite(f):
            return int(f) if f.is_integer() else f
    return None


def normalize_metrics(raw: Any) -> dict[str, float | int | None]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float | int | None] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            continue
        out[key.strip()] = None if value is None else finite_number(value)
    return out

def normalize_series(raw: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for row in raw:
        if not isinstance(row, dict):
            continue
        date = row.get("date") or row.get("time") or row.get("timestamp")
        value = finite_number(row.get("value") if "value" in row else row.get("interest"))
        if date is None:
            continue
        out.append({"date": str(date), "value": value})
    return out


def normalize_terms(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if isinstance(item, dict):
            item = item.get("term") or item.get("query") or item.get("title")
        if not isinstance(item, str):
            continue
        term = item.strip()
        if term and term not in seen:
            seen.add(term)
            out.append(term)
    return out


def normalize_signal(raw: dict[str, Any], provider: str, kind: str | None, geo: str | None) -> dict[str, Any]:
    url = raw.get("source_url") or raw.get("url")
    if not is_public_http_url(url):
        fail("signal requires public http(s) source_url")
    resolved_kind = str(raw.get("kind") or kind or "search_interest").strip()
    if resolved_kind not in ALLOWED_KINDS:
        fail(f"unsupported signal kind: {resolved_kind}")
    query = raw.get("query") or raw.get("term") or raw.get("keyword")
    if not isinstance(query, str) or not query.strip():
        fail("signal requires query")
    series = raw.get("series")
    if series is None:
        series = raw.get("interest_over_time")
    terms = raw.get("related_terms")
    if terms is None:
        terms = raw.get("related_queries")
    return {
        "source_url": str(url).strip(),
        "provider": str(raw.get("provider") or provider or "unknown").strip() or "unknown",
        "kind": resolved_kind,
        "query": query.strip(),
        "geo": raw.get("geo") or geo,
        "observed_at": str(raw.get("observed_at") or raw.get("scraped_at") or now_utc()),
        "metrics": normalize_metrics(raw.get("metrics") or {}),
        "series": normalize_series(series),
        "related_terms": normalize_terms(terms),
        "note": raw.get("note"),
    }


def normalize_packet(raw: Any, window_start: str, window_end: str, provider: str,
                     kind: str | None, geo: str | None) -> dict[str, Any]:
    rows = raw.get("signals") if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        fail("input must be a list or object with signals[]")
    signals = [normalize_signal(row, provider, kind, geo) for row in rows if isinstance(row, dict)]
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for signal in signals:
        key = (signal["source_url"], signal["provider"])
        if key in seen:
            continue
        seen.add(key)
        sources.append({"url": key[0], "provider": key[1], "observed_at": signal["observed_at"]})
    return {
        "schemaVersion": "1.0",
        "window": {"start": window_start, "end": window_end},
        "geo": geo,
        "sources": sources,
        "signals": signals,
        "rules": {
            "publicExternalOnly": True,
            "missingMetricIsNotZero": True,
            "syntheticDemandScoreForbidden": True,
            "noAutomaticSkuPromotion": True,
            "licenseGateRequiredBeforePrintCandidate": True,
        },
    }


def validate_packet(packet: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet must be object"]
    if packet.get("schemaVersion") != "1.0":
        errors.append("schemaVersion must be 1.0")
    window = packet.get("window")
    if not isinstance(window, dict) or not window.get("start") or not window.get("end"):
        errors.append("window.start and window.end required")
    if not isinstance(packet.get("sources"), list) or not isinstance(packet.get("signals"), list):
        errors.append("sources and signals must be arrays")
    for i, signal in enumerate(packet.get("signals") or []):
        if not isinstance(signal, dict):
            errors.append(f"signals[{i}] must be object")
            continue
        if "demand_score" in signal or "virality_score" in signal:
            errors.append(f"signals[{i}] synthetic demand_score/virality_score forbidden")
        if not is_public_http_url(signal.get("source_url")):
            errors.append(f"signals[{i}].source_url must be public http(s)")
        if signal.get("kind") not in ALLOWED_KINDS:
            errors.append(f"signals[{i}].kind unsupported")
        if not signal.get("provider") or not signal.get("query") or not signal.get("observed_at"):
            errors.append(f"signals[{i}] provider/query/observed_at required")
        metrics = signal.get("metrics")
        if not isinstance(metrics, dict):
            errors.append(f"signals[{i}].metrics must be object")
        else:
            for key, value in metrics.items():
                if value is not None and finite_number(value) is None:
                    errors.append(f"signals[{i}].metrics.{key} must be numeric or null")
        for j, point in enumerate(signal.get("series") or []):
            if not isinstance(point, dict) or not point.get("date"):
                errors.append(f"signals[{i}].series[{j}] date required")
            elif point.get("value") is not None and finite_number(point.get("value")) is None:
                errors.append(f"signals[{i}].series[{j}].value must be numeric or null")
    return errors


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def self_test() -> int:
    sample = [{"source_url": "https://example.com/trends?q=owl", "provider": "fixture",
               "kind": "search_interest", "query": "3d owl", "geo": "IL",
               "metrics": {"count": "4", "missing": None},
               "series": [{"date": "2026-09-01", "value": "50"}],
               "related_terms": ["owl decor"]}]
    packet = normalize_packet(sample, "2026-09-01", "2026-09-18", "fixture", None, "IL")
    errors = validate_packet(packet)
    if errors:
        print("FAIL self-test", errors, file=sys.stderr)
        return 1
    signal = packet["signals"][0]
    if signal["metrics"]["count"] != 4 or signal["metrics"]["missing"] is not None:
        print("FAIL metric semantics", file=sys.stderr)
        return 1
    if signal["series"][0]["value"] != 50 or signal["related_terms"] != ["owl decor"]:
        print("FAIL series/terms semantics", file=sys.stderr)
        return 1
    signal["demand_score"] = 1
    if not any("demand_score" in e for e in validate_packet(packet)):
        print("FAIL synthetic-score guard", file=sys.stderr)
        return 1
    print("OK demand-signals self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="cmd")
    n = sub.add_parser("normalize")
    n.add_argument("--input", required=True)
    n.add_argument("--output", required=True)
    n.add_argument("--window-start", required=True)
    n.add_argument("--window-end", required=True)
    n.add_argument("--provider", default="unknown")
    n.add_argument("--kind", choices=sorted(ALLOWED_KINDS))
    n.add_argument("--geo")
    v = sub.add_parser("validate")
    v.add_argument("path")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.cmd == "normalize":
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
        packet = normalize_packet(raw, args.window_start, args.window_end, args.provider, args.kind, args.geo)
        errors = validate_packet(packet)
        if errors:
            fail("; ".join(errors))
        save_json(Path(args.output), packet)
        print(f"OK wrote {args.output} signals={len(packet['signals'])}")
        return 0
    if args.cmd == "validate":
        packet = json.loads(Path(args.path).read_text(encoding="utf-8"))
        errors = validate_packet(packet)
        if errors:
            for error in errors:
                print(f"FAIL {error}", file=sys.stderr)
            return 1
        print(f"OK packet valid signals={len(packet['signals'])}")
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
