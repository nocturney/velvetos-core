#!/usr/bin/env python3
"""Normalize external public social evidence for VelvetOS. No network. No send.

This helper deliberately does not scrape. Acquisition is provider-specific and happens
through authorized web/provider tools. This file normalizes the resulting public facts
into stable research contracts.

Examples:
  python3 scripts/vf_social_intelligence.py normalize-signals --input raw.json --output packet.json --window-start 2026-09-07 --window-end 2026-09-14
  python3 scripts/vf_social_intelligence.py validate-packet packet.json
  python3 scripts/vf_social_intelligence.py reference-pattern --input reference-observations.json --output reference-pattern.json
  python3 scripts/vf_social_intelligence.py watch-delta --previous previous-packet.json --current current-packet.json --output watch-delta.json
  python3 scripts/vf_social_intelligence.py --self-test
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

ROOT = Path(__file__).resolve().parents[1]
PACKET_SCHEMA = ROOT / "packages" / "vfresearch" / "social-research-packet.schema.json"
REFERENCE_SCHEMA = ROOT / "packages" / "vfresearch" / "reference-pattern.schema.json"

SIGNAL_KEYS = (
    "source_url",
    "provider",
    "author",
    "published_at",
    "observed_at",
    "media_type",
    "topic",
    "hook_mechanic",
    "visual_mechanic",
    "narrative_mechanic",
    "outlier_score",
    "evidence_quality",
    "metrics",
)


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
        if not math.isfinite(f):
            return None
        return int(f) if f.is_integer() else f
    return None


def normalize_metrics(raw: Any) -> dict[str, float | int | None]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float | int | None] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            continue
        if value is None:
            out[key.strip()] = None
            continue
        parsed = finite_number(value)
        if parsed is not None:
            out[key.strip()] = parsed
    return out


def normalize_signal(raw: dict[str, Any], default_provider: str = "unknown") -> dict[str, Any]:
    url = raw.get("source_url") or raw.get("url") or raw.get("permalink")
    if not is_public_http_url(url):
        fail("signal requires public http(s) source_url")
    provider = str(raw.get("provider") or default_provider or "unknown").strip() or "unknown"
    observed_at = str(raw.get("observed_at") or raw.get("scraped_at") or now_utc()).strip()
    out = {
        "source_url": str(url).strip(),
        "provider": provider,
        "author": raw.get("author") or raw.get("username") or raw.get("handle"),
        "published_at": raw.get("published_at") or raw.get("date") or raw.get("timestamp"),
        "observed_at": observed_at,
        "media_type": raw.get("media_type") or raw.get("type"),
        "topic": raw.get("topic"),
        "hook_mechanic": raw.get("hook_mechanic"),
        "visual_mechanic": raw.get("visual_mechanic"),
        "narrative_mechanic": raw.get("narrative_mechanic"),
        "outlier_score": finite_number(raw.get("outlier_score")),
        "evidence_quality": raw.get("evidence_quality"),
        "metrics": normalize_metrics(raw.get("metrics") or {}),
    }
    return {k: out.get(k) for k in SIGNAL_KEYS}


def packet_from_raw(raw: Any, window_start: str, window_end: str, provider: str) -> dict[str, Any]:
    if isinstance(raw, dict) and isinstance(raw.get("signals"), list):
        rows = raw["signals"]
        opportunities = raw.get("opportunities") or []
        risks = raw.get("risks") or []
    elif isinstance(raw, list):
        rows = raw
        opportunities = []
        risks = []
    else:
        fail("input must be a list of signals or an object with signals[]")
    signals = [normalize_signal(row, provider) for row in rows if isinstance(row, dict)]
    sources = []
    seen = set()
    for s in signals:
        key = (s["source_url"], s["provider"])
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "url": s["source_url"],
            "provider": s["provider"],
            "observed_at": s["observed_at"],
            "note": None,
        })
    return {
        "schemaVersion": "1.0",
        "window": {"start": window_start, "end": window_end},
        "sources": sources,
        "signals": signals,
        "opportunities": opportunities,
        "risks": risks,
        "rules": {
            "ownAccountCanonical": "instagram_mcp",
            "publicExternalOnly": True,
            "missingMetricIsNotZero": True,
            "globalViralityScoreForbidden": True,
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
    for key in ("sources", "signals", "opportunities", "risks"):
        if not isinstance(packet.get(key), list):
            errors.append(f"{key} must be array")
    for i, signal in enumerate(packet.get("signals") or []):
        if not isinstance(signal, dict):
            errors.append(f"signals[{i}] must be object")
            continue
        if not is_public_http_url(signal.get("source_url")):
            errors.append(f"signals[{i}].source_url must be public http(s)")
        if not signal.get("provider"):
            errors.append(f"signals[{i}].provider required")
        if not signal.get("observed_at"):
            errors.append(f"signals[{i}].observed_at required")
        metrics = signal.get("metrics")
        if not isinstance(metrics, dict):
            errors.append(f"signals[{i}].metrics must be object")
        else:
            for mk, mv in metrics.items():
                if mv is not None and finite_number(mv) is None:
                    errors.append(f"signals[{i}].metrics.{mk} must be numeric or null")
    return errors


def _segments(raw: Any, key: str) -> list[dict[str, Any]]:
    value = raw.get(key) if isinstance(raw, dict) else None
    return [x for x in (value or []) if isinstance(x, dict)]


def _time_values(items: list[dict[str, Any]], keys: tuple[str, ...]) -> list[float]:
    out = []
    for item in items:
        for key in keys:
            val = finite_number(item.get(key))
            if val is not None:
                out.append(float(val))
                break
    return out


def build_reference_pattern(raw: dict[str, Any]) -> dict[str, Any]:
    url = raw.get("source_url") or raw.get("url")
    if not is_public_http_url(url):
        fail("reference requires public http(s) source_url")
    transcript = _segments(raw, "transcript_segments")
    events = _segments(raw, "visual_events")
    duration = finite_number(raw.get("duration_seconds"))
    if duration is None:
        ends = _time_values(transcript, ("end", "end_seconds", "at")) + _time_values(events, ("end", "end_seconds", "at"))
        duration = max(ends) if ends else None
    spoken_starts = _time_values(transcript, ("start", "start_seconds", "at"))
    visual_change_starts = [
        float(v)
        for e in events
        if str(e.get("kind") or "").lower() in {"cut", "visual_change", "shot", "scene_change"}
        for v in [finite_number(e.get("at") if e.get("at") is not None else e.get("start"))]
        if v is not None
    ]
    reveal_times = [
        float(v)
        for e in events
        if str(e.get("kind") or "").lower() == "reveal"
        for v in [finite_number(e.get("at") if e.get("at") is not None else e.get("start"))]
        if v is not None
    ]
    overlay_count = sum(1 for e in events if str(e.get("kind") or "").lower() in {"overlay", "text_overlay"})
    mechanics = raw.get("mechanics") if isinstance(raw.get("mechanics"), dict) else {}
    return {
        "schemaVersion": "1.0",
        "source_url": str(url).strip(),
        "observed": {
            "duration_seconds": duration,
            "first_spoken_at_seconds": min(spoken_starts) if spoken_starts else None,
            "first_visual_change_at_seconds": min(visual_change_starts) if visual_change_starts else None,
            "event_count": len(events),
            "overlay_count": overlay_count,
            "reveal_at_seconds": min(reveal_times) if reveal_times else None,
        },
        "mechanics": {
            "hook_mechanic": mechanics.get("hook_mechanic") or raw.get("hook_mechanic"),
            "visual_mechanic": mechanics.get("visual_mechanic") or raw.get("visual_mechanic"),
            "narrative_mechanic": mechanics.get("narrative_mechanic") or raw.get("narrative_mechanic"),
            "cta_type": mechanics.get("cta_type") or raw.get("cta_type"),
        },
        "provenance": {
            "provider": str(raw.get("provider") or "unknown"),
            "captured_at": raw.get("captured_at") or now_utc(),
            "raw_ref": raw.get("raw_ref"),
        },
        "copyingForbidden": True,
        "rules": {
            "mechanicsOnly": True,
            "doNotCopyWording": True,
            "doNotCopyBrandingOrFootage": True,
        },
    }


def _signal_key(signal: Any) -> tuple[str, str] | None:
    if not isinstance(signal, dict):
        return None
    url = signal.get("source_url")
    provider = signal.get("provider")
    if not is_public_http_url(url) or not isinstance(provider, str) or not provider.strip():
        return None
    return (str(url).strip(), provider.strip())


def build_watch_delta(previous: Any, current: Any) -> dict[str, Any]:
    previous_errors = validate_packet(previous)
    current_errors = validate_packet(current)
    if previous_errors:
        fail("previous packet invalid: " + "; ".join(previous_errors))
    if current_errors:
        fail("current packet invalid: " + "; ".join(current_errors))

    prev_map = {
        key: signal
        for signal in (previous.get("signals") or [])
        if (key := _signal_key(signal)) is not None
    }
    curr_map = {
        key: signal
        for signal in (current.get("signals") or [])
        if (key := _signal_key(signal)) is not None
    }

    new_signals = []
    metric_deltas = []
    author_counts: dict[str, int] = {}

    for key, signal in curr_map.items():
        author = signal.get("author")
        if isinstance(author, str) and author.strip():
            author_counts[author.strip()] = author_counts.get(author.strip(), 0) + 1

        if key not in prev_map:
            new_signals.append({
                "source_url": key[0],
                "provider": key[1],
                "author": signal.get("author"),
                "published_at": signal.get("published_at"),
                "observed_at": signal.get("observed_at"),
            })
            continue

        before_metrics = prev_map[key].get("metrics") if isinstance(prev_map[key].get("metrics"), dict) else {}
        after_metrics = signal.get("metrics") if isinstance(signal.get("metrics"), dict) else {}
        deltas = {}
        for metric in sorted(set(before_metrics) | set(after_metrics)):
            before = before_metrics.get(metric)
            after = after_metrics.get(metric)
            before_num = finite_number(before)
            after_num = finite_number(after)
            if before_num is None or after_num is None:
                continue
            delta = after_num - before_num
            if delta != 0:
                deltas[metric] = {
                    "previous": before_num,
                    "current": after_num,
                    "delta": delta,
                }
        if deltas:
            metric_deltas.append({
                "source_url": key[0],
                "provider": key[1],
                "author": signal.get("author"),
                "metrics": deltas,
            })

    return {
        "schemaVersion": "1.0",
        "previousWindow": previous.get("window"),
        "currentWindow": current.get("window"),
        "newSignals": sorted(new_signals, key=lambda x: (x.get("provider") or "", x.get("source_url") or "")),
        "metricDeltas": sorted(metric_deltas, key=lambda x: (x.get("provider") or "", x.get("source_url") or "")),
        "currentAuthorCounts": [
            {"author": author, "signal_count": count}
            for author, count in sorted(author_counts.items())
        ],
        "rules": {
            "sameSourceProviderOnly": True,
            "missingMetricIsNotZero": True,
            "crossAccountRankingForbidden": True,
            "globalViralityScoreForbidden": True,
        },
    }


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def self_test() -> int:
    sample = [{
        "url": "https://example.com/reel/1",
        "provider": "fixture",
        "metrics": {"views": "123", "likes": None, "comments": "4"},
    }]
    packet = packet_from_raw(sample, "2026-09-07", "2026-09-14", "fixture")
    errors = validate_packet(packet)
    if errors:
        print("FAIL self-test packet", errors, file=sys.stderr)
        return 1
    sig = packet["signals"][0]
    if sig["metrics"]["views"] != 123 or sig["metrics"]["likes"] is not None:
        print("FAIL self-test metric semantics", file=sys.stderr)
        return 1
    ref = build_reference_pattern({
        "source_url": "https://example.com/reel/1",
        "provider": "fixture",
        "duration_seconds": 12,
        "transcript_segments": [{"start": 0.4, "end": 3.0, "text": "x"}],
        "visual_events": [{"kind": "cut", "at": 0.8}, {"kind": "reveal", "at": 8.2}, {"kind": "text_overlay", "at": 1.0}],
    })
    if ref["observed"]["first_visual_change_at_seconds"] != 0.8 or ref["observed"]["overlay_count"] != 1:
        print("FAIL self-test reference pattern", file=sys.stderr)
        return 1
    previous = packet_from_raw([{
        "url": "https://example.com/reel/1",
        "provider": "fixture",
        "author": "maker_a",
        "metrics": {"views": 100, "likes": None},
    }], "2026-09-01", "2026-09-07", "fixture")
    current = packet_from_raw([{
        "url": "https://example.com/reel/1",
        "provider": "fixture",
        "author": "maker_a",
        "metrics": {"views": 150, "likes": 10},
    }, {
        "url": "https://example.com/reel/2",
        "provider": "fixture",
        "author": "maker_a",
        "metrics": {"views": 20},
    }], "2026-09-08", "2026-09-14", "fixture")
    delta = build_watch_delta(previous, current)
    if len(delta["newSignals"]) != 1:
        print("FAIL self-test watch delta newSignals", file=sys.stderr)
        return 1
    if delta["metricDeltas"][0]["metrics"]["views"]["delta"] != 50:
        print("FAIL self-test watch delta metric", file=sys.stderr)
        return 1
    if "likes" in delta["metricDeltas"][0]["metrics"]:
        print("FAIL self-test watch delta null semantics", file=sys.stderr)
        return 1
    if delta["currentAuthorCounts"] != [{"author": "maker_a", "signal_count": 2}]:
        print("FAIL self-test watch delta author counts", file=sys.stderr)
        return 1
    print("OK social-intelligence self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    n = sub.add_parser("normalize-signals")
    n.add_argument("--input", required=True)
    n.add_argument("--output", required=True)
    n.add_argument("--window-start", required=True)
    n.add_argument("--window-end", required=True)
    n.add_argument("--provider", default="unknown")

    v = sub.add_parser("validate-packet")
    v.add_argument("path")

    r = sub.add_parser("reference-pattern")
    r.add_argument("--input", required=True)
    r.add_argument("--output", required=True)

    w = sub.add_parser("watch-delta")
    w.add_argument("--previous", required=True)
    w.add_argument("--current", required=True)
    w.add_argument("--output", required=True)

    args = p.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.cmd == "normalize-signals":
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
        packet = packet_from_raw(raw, args.window_start, args.window_end, args.provider)
        errors = validate_packet(packet)
        if errors:
            fail("; ".join(errors))
        save_json(Path(args.output), packet)
        print(f"OK wrote {args.output} signals={len(packet['signals'])}")
        return 0
    if args.cmd == "validate-packet":
        packet = json.loads(Path(args.path).read_text(encoding="utf-8"))
        errors = validate_packet(packet)
        if errors:
            for e in errors:
                print(f"FAIL {e}", file=sys.stderr)
            return 1
        print(f"OK packet valid signals={len(packet['signals'])}")
        return 0
    if args.cmd == "reference-pattern":
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
        payload = build_reference_pattern(raw)
        save_json(Path(args.output), payload)
        print(f"OK wrote {args.output}")
        return 0
    if args.cmd == "watch-delta":
        previous = json.loads(Path(args.previous).read_text(encoding="utf-8"))
        current = json.loads(Path(args.current).read_text(encoding="utf-8"))
        payload = build_watch_delta(previous, current)
        save_json(Path(args.output), payload)
        print(f"OK wrote {args.output} new={len(payload['newSignals'])} changed={len(payload['metricDeltas'])}")
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
