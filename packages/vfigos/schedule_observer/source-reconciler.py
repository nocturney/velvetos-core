#!/usr/bin/env python3
"""VelvetOS read-only publication source reconciliation.

Discovers every configured source, keeps authority and observation separate,
deduplicates a virtualized Meta table, and fails visible on missing/stale data.
No provider credentials, network calls, publishing effects, or scheduled tasks.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from typing import Any
from zoneinfo import ZoneInfo

SCHEMA = "velvet.instagram.source_reconciliation.v1"
DEFAULT_TZ = "Asia/Jerusalem"
DATE_RX = re.compile(
    r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s+\d{1,2},\s+\d{1,2}:\d{2}(?:am|pm)\b", re.IGNORECASE
)
META_KIND_RX = re.compile(r"\b(Photo|Reel|Video|Carousel)\s*[\u00b7.]\s*velvets_cloud\b", re.IGNORECASE)
SECRETS_RX = re.compile(r"(?i)(authorization|cookie|bearer|access_token|secret_token)\s*[:=]")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be string")
    dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path | None, max_bytes: int = 8_000_000) -> dict | None:
    if path is None or not path.is_file():
        return None
    if path.stat().st_size > max_bytes or path.stat().st_size <= 0:
        raise ValueError("source JSON invalid size")
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError("source JSON must be an object")
    return obj


def short_error(exc: Exception) -> str:
    msg = str(exc).splitlines()[0]
    msg = SECRETS_RX.sub("[REDACTED_FIELD]=", msg)
    return msg[:200]


def normalize_text(text: str) -> str:
    return " ".join(str(text).split()).strip()


def source_status(spec: dict, doc: dict | None, *, asof: datetime) -> dict:
    result = {
        "source_id": spec["id"], "capability": spec["capability"],
        "reader": spec["reader"], "authority": spec["source_of_truth_for"],
        "state": "UNAVAILABLE", "observed_at": None, "age_seconds": None,
        "count": None, "reason": None, "evidence": None
    }
    if not spec.get("active", False):
        result.update(state="DISABLED", reason="not an active production reader")
        return result
    if spec["reader"] == "not_integrated":
        result.update(state="UNSUPPORTED", reason="native app schedule not accessible to configured reader")
        return result
    if doc is None:
        result.update(state="UNAVAILABLE", reason="no authenticated source snapshot provided")
        return result
    observed = doc.get("observed_at") or doc.get("captured_at")
    if not observed:
        result.update(state="INVALID", reason="missing observed_at")
        return result
    try:
        seen = parse_time(observed)
    except (ValueError, TypeError) as exc:
        result.update(state="INVALID", reason=short_error(exc))
        return result
    age = max(0, int((asof - seen).total_seconds()))
    result.update(observed_at=iso(seen), age_seconds=age)
    if seen > asof + timedelta(minutes=5):
        result.update(state="INVALID", reason="source clock is in the future")
    elif age > int(spec["max_age_seconds"]):
        result.update(state="STALE", reason="age exceeds configured max_age_seconds")
    else:
        result.update(state="AVAILABLE", reason="fresh authenticated observation")
    return result


def parse_meta_date(label: str, observed: datetime, tz_name: str) -> str:
    local = observed.astimezone(ZoneInfo(tz_name))
    parsed = datetime.strptime(label, "%a %b %d, %I:%M%p")
    candidate = parsed.replace(year=local.year, tzinfo=ZoneInfo(tz_name))
    # End-of-year publication plans may fall in the next calendar year.
    if candidate < local - timedelta(days=90):
        candidate = candidate.replace(year=candidate.year + 1)
    elif candidate > local + timedelta(days=330):
        candidate = candidate.replace(year=candidate.year - 1)
    return iso(candidate)


def meta_records(doc: dict, *, tz_name: str, asof: datetime) -> tuple[list[dict], dict]:
    if doc.get("schema") != "velvet.meta_planner_reader.scheduled.v3":
        raise ValueError("unsupported Meta snapshot schema")
    url = str(doc.get("page_url") or "")
    if not (url.startswith("https://business.facebook.com/latest/posts/")
            and doc.get("scheduled_selected") is True):
        raise ValueError("Meta Scheduled tab not verified")
    if doc.get("account_expected") not in (None, "velvets_cloud"):
        raise ValueError("Meta source account mismatch")
    observed = parse_time(doc["observed_at"])
    rows = doc.get("unique_rows")
    if not isinstance(rows, list):
        raise ValueError("Meta snapshot rows missing")
    out: dict[str, dict] = {}
    skipped = 0
    for raw in rows:
        if not isinstance(raw, str):
            raise ValueError("Meta row must be text")
        date_match = DATE_RX.search(raw)
        if not date_match:
            skipped += 1
            continue
        scheduled = parse_meta_date(date_match.group(0), observed, tz_name)
        before = raw[:date_match.start()]
        kind = META_KIND_RX.search(before)
        format_name = kind.group(1).lower() if kind else "unknown"
        caption = normalize_text(before[:kind.start()] if kind else before)
        if not caption:
            skipped += 1
            continue
        # The virtualized Meta list may render the same row several times with
        # or without a Boost button; neither variant is a second publication.
        exact = "\0".join((scheduled, format_name, caption))
        row_id = sha256(exact.encode("utf-8")).hexdigest()[:24]
        out[row_id] = {
            "observation_id": "meta:" + row_id, "source_id": "meta-business-suite",
            "scheduled_at": scheduled, "status": "scheduled",
            "format": format_name, "caption_preview": caption[:220],
            "caption_sha256": sha256(caption.encode("utf-8")).hexdigest(),
            "original_time_label": date_match.group(0), "native_post_id": None,
            "identity_strength": "time_and_exact_visible_caption",
        }
    items = sorted(out.values(), key=lambda x: (x["scheduled_at"], x["observation_id"]))
    return items, {
        "input_rows": len(rows), "skipped_non_items": skipped,
        "deduplicated_rows": len(items), "duplicate_rows": len(rows)-skipped-len(items),
        "coverage": "LOWER_BOUND",
        "coverage_note": "Meta UI virtualized table; screenshot/DOM cannot prove undisplayed pages do not exist",
        "account_proof": "row labels show expected handle; capture must be reviewed if handle changes",
        "observation_fresh": observed <= asof + timedelta(minutes=5)
    }


def publisher_records(doc: dict) -> tuple[list[dict], dict]:
    if doc.get("schema") != "vf.instagram.schedule-snapshot.v1" or doc.get("source") != "cloudflare-instagram-publisher":
        raise ValueError("wrong Cloudflare publisher snapshot schema")
    health = doc.get("meta_health") or {}
    rt = doc.get("runtime") or {}
    if health.get("ok") is not True or health.get("username") != "velvets_cloud":
        raise ValueError("publisher Meta account health not verified")
    age = rt.get("heartbeat_age_seconds")
    if not isinstance(age, (int, float)) or age > 180 or age < 0:
        raise ValueError("publisher cron heartbeat unavailable or stale")
    jobs = doc.get("scheduled")
    if not isinstance(jobs, list):
        raise ValueError("publisher scheduled list missing")
    records = []
    seen_ids = set()
    for row in jobs:
        if not isinstance(row, dict):
            raise ValueError("publisher record must be object")
        ident = str(row.get("publication_id") or "")
        if not ident or ident in seen_ids:
            raise ValueError("publisher id missing or duplicated")
        seen_ids.add(ident)
        records.append({
            "observation_id": "publisher:" + ident,
            "source_id": "cloudflare-publisher",
            "native_post_id": ident, "title": str(row.get("title") or "")[:240],
            "scheduled_at": iso(parse_time(row["scheduled_at"])),
            "format": str(row.get("content_profile") or "unknown"),
            "status": str(row.get("status") or "unknown"),
            "identity_strength": "native_provider_job_id",
        })
    return sorted(records, key=lambda x: x["scheduled_at"]), {"heartbeat_age_seconds": age}


def calendar_records(doc: dict) -> tuple[list[dict], dict]:
    if doc.get("schema") != "velvet.google_calendar.instagram_snapshot.v1":
        raise ValueError("calendar import schema mismatch")
    events = doc.get("events")
    if not isinstance(events, list):
        raise ValueError("calendar events list absent")
    records = []
    for event in events:
        if not isinstance(event, dict):
            continue
        description = str(event.get("description") or "")
        job_match = re.search(r"\bjob_id\s*:\s*([a-z0-9-]+)", description, re.IGNORECASE)
        start = event.get("start") or {}
        when = start.get("dateTime") or start.get("date_time")
        if not when:
            continue
        records.append({
            "observation_id": "calendar:" + str(event.get("id") or sha256(description.encode()).hexdigest()[:18]),
            "source_id": "google-calendar-mirror",
            "native_post_id": job_match.group(1) if job_match else None,
            "scheduled_at": iso(parse_time(when)),
            "title": str(event.get("summary") or "")[:200],
            "status": "mirror_observation",
            "identity_strength": "publisher_job_id_in_event" if job_match else "unlinked_mirror_event",
        })
    return records, {"calendar_id": str(doc.get("calendar_id") or ""), "mirror_only": True}


def graph_records(doc: dict) -> tuple[list[dict], dict]:
    if doc.get("schema") != "velvet.instagram_graph.media_snapshot.v1":
        raise ValueError("Instagram Graph import schema mismatch")
    media = doc.get("media")
    if not isinstance(media, list):
        raise ValueError("Graph published media list absent")
    records = []
    for row in media:
        if not isinstance(row, dict) or not row.get("id") or not row.get("timestamp"):
            continue
        records.append({
            "observation_id": "graph:" + str(row["id"]),
            "source_id": "instagram-graph",
            "native_post_id": str(row["id"]),
            "published_at": iso(parse_time(row["timestamp"])),
            "permalink": str(row.get("permalink") or "")[:400],
            "status": "published",
        })
    return records, {"published_only": True, "no_scheduled_read_capability": True}


def external_records(doc: dict, source_id: str) -> tuple[list[dict], dict]:
    """Generic *approved* read-source adapter for future connected providers.

    A provider may report independent scheduled items with explicit identities;
    it never inherits publisher write authority and never reads arbitrary URLs.
    """
    if doc.get("schema") != "velvet.read_source_snapshot.v1" or doc.get("source_id") != source_id:
        raise ValueError("external source schema or registered identity mismatch")
    rows = doc.get("scheduled")
    if not isinstance(rows, list) or len(rows) > 5000:
        raise ValueError("external scheduled list missing or oversized")
    out = []
    ids = set()
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("external scheduled record must be object")
        native = str(item.get("native_id") or "")
        if not native or native in ids:
            raise ValueError("external native id missing or duplicated")
        ids.add(native)
        out.append({
            "observation_id": source_id + ":" + native,
            "source_id": source_id,
            "native_post_id": native,
            "scheduled_at": iso(parse_time(item["scheduled_at"])),
            "status": str(item.get("status") or "scheduled")[:50],
            "format": str(item.get("format") or "unknown")[:50],
            "title": str(item.get("title") or "")[:200],
            "identity_strength": "native_provider_id",
        })
    return out, {"generic_registered_adapter": True}


def reconcile(
    registry: dict, documents: dict[str, dict | None], *,
    asof: datetime | None = None
) -> dict:
    asof = asof or utcnow()
    if registry.get("schema") != "velvet.read_source_registry.v1":
        raise ValueError("invalid source registry schema")
    if registry.get("policy", {}).get("allow_side_effects") is not False:
        raise ValueError("reader must disallow external effects")
    if registry.get("policy", {}).get("authoritative_writer") != "cloudflare-publisher":
        raise ValueError("canonical writer must not change in a reader")
    specs = registry.get("sources")
    if not isinstance(specs, list) or len(set(s.get("id") for s in specs)) != len(specs):
        raise ValueError("source registry missing or contains duplicate ids")
    tz_name = registry.get("user_timezone") or DEFAULT_TZ
    scheduled, published, mirrors, states, diagnostics = [], [], [], [], {}
    parsers = {
        "meta-business-suite": meta_records,
        "cloudflare-publisher": publisher_records,
        "google-calendar-mirror": calendar_records,
        "instagram-graph": graph_records,
    }
    for spec in specs:
        sid = spec["id"]
        doc = documents.get(sid)
        state = source_status(spec, doc, asof=asof)
        states.append(state)
        # Stale documents are not suitable for claims about what is scheduled now.
        if state["state"] != "AVAILABLE":
            continue
        if sid not in parsers and spec.get("reader") != "extensible_source_snapshot":
            state.update(state="UNSUPPORTED", reason="no admitted read adapter for this registered source")
            continue
        try:
            if sid == "meta-business-suite":
                rows, extra = meta_records(doc, tz_name=tz_name, asof=asof)
            elif spec.get("reader") == "extensible_source_snapshot":
                rows, extra = external_records(doc, sid)
            else:
                rows, extra = parsers[sid](doc)
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            state.update(state="INVALID", count=None, reason=short_error(exc))
            continue
        state.update(count=len(rows), evidence=doc.get("evidence_path"))
        diagnostics[sid] = extra
        if sid == "instagram-graph":
            published.extend(rows)
        elif sid == "google-calendar-mirror":
            mirrors.extend(rows)
        else:
            scheduled.extend(rows)
        state["state"] = "EMPTY" if not rows else "AVAILABLE"
    canonical = [r for r in scheduled if r["source_id"] == "cloudflare-publisher"]
    meta = [r for r in scheduled if r["source_id"] == "meta-business-suite"]
    # Only an exact provider ID or exact timestamp + content identity is strong enough
    # to merge independent sources. Same time alone is NOT a duplicate.
    canonical_keys = {(r["scheduled_at"], r.get("caption_sha256")) for r in canonical if r.get("caption_sha256")}
    meta_not_correlated = [r for r in meta if (r["scheduled_at"], r["caption_sha256"]) not in canonical_keys]
    alerts = []
    publisher_state = next((s["state"] for s in states if s["source_id"] == "cloudflare-publisher"), "UNAVAILABLE")
    if meta and publisher_state == "EMPTY":
        alerts.append({"code": "EXTERNAL_SCHEDULES_NOT_IN_CANONICAL_QUEUE", "severity": "high",
                       "observed_meta_at_least": len(meta), "canonical_jobs": 0,
                       "description": "Meta Business Suite holds future posts not present in Cloudflare publisher. No write authority changed."})
    elif meta_not_correlated and canonical and publisher_state == "AVAILABLE":
        alerts.append({"code": "SCHEDULES_WITHOUT_CONFIRMED_CROSS_SOURCE_MATCH", "severity": "info",
                       "observed_meta_at_least": len(meta_not_correlated),
                       "description": "Lack of exact shared ID/caption hash; not evidence of duplicate publish."})
    publisher_ok = next((s for s in states if s["source_id"] == "cloudflare-publisher"), {})
    calendar_ok = next((s for s in states if s["source_id"] == "google-calendar-mirror"), {})
    if publisher_ok.get("state") in ("EMPTY", "AVAILABLE") and calendar_ok.get("state") in ("EMPTY", "AVAILABLE"):
        ids = {r["native_post_id"] for r in canonical}
        mirror_ids = {r["native_post_id"] for r in mirrors if r["native_post_id"]}
        if ids - mirror_ids:
            alerts.append({"code": "CALENDAR_MIRROR_MISSING_PUBLISHER_JOBS", "severity": "warning",
                           "missing_count": len(ids - mirror_ids)})
    missing = [s["source_id"] for s in states if s["state"] in ("UNAVAILABLE", "INVALID", "STALE", "UNSUPPORTED")]
    if missing:
        alerts.append({"code": "INCOMPLETE_SOURCE_COVERAGE", "severity": "warning",
                       "sources": missing, "description": "Never interpret missing reads as empty queues."})
    scheduled.sort(key=lambda r: (r["scheduled_at"], r["source_id"]))
    published.sort(key=lambda r: r["published_at"], reverse=True)
    return {
        "schema": SCHEMA, "observed_at": iso(asof), "tenant": registry["tenant"],
        "policy": {"authoritative_writer": "cloudflare-publisher", "read_only": True,
                   "external_mutations_performed": False},
        "source_health": states, "scheduled": scheduled, "published": published,
        "calendar_mirror": mirrors,
        "counts": {"observed_scheduled": len(scheduled), "meta_scheduled_lower_bound": len(meta),
                   "cloudflare_scheduled": len(canonical), "calendar_mirror": len(mirrors),
                   "graph_published": len(published), "missing_or_unverified_sources": len(missing)},
        "alerts": alerts, "diagnostics": diagnostics,
        "coverage": "PARTIAL" if missing or meta else "CONFIGURED_SOURCES_ONLY",
        "coverage_note": "Configured-source inventory, never proof that every external scheduling surface is covered.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unify all configured Instagram publication read sources.")
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--meta", type=Path)
    parser.add_argument("--publisher", type=Path)
    parser.add_argument("--calendar", type=Path)
    parser.add_argument("--graph", type=Path)
    parser.add_argument("--source", action="append", default=[], metavar="REGISTERED_ID=JSON", help="Additional approved source snapshot; id must exist in registry")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--as-of", help="UTC ISO timestamp, for deterministic verification")
    args = parser.parse_args(argv)
    source_files = {
        "meta-business-suite": args.meta, "cloudflare-publisher": args.publisher,
        "google-calendar-mirror": args.calendar, "instagram-graph": args.graph
    }
    registry = read_json(args.registry)
    if registry is None:
        parser.error("source registry missing")
    admitted = {s["id"] for s in registry.get("sources", []) if s.get("active") and s.get("reader") == "extensible_source_snapshot"}
    for option in args.source:
        if "=" not in option:
            parser.error("source adapter expected REGISTERED_ID=JSON")
        sid, filename = option.split("=", 1)
        if sid not in admitted or sid in source_files or not filename:
            parser.error("unregistered, duplicate or empty external source adapter")
        source_files[sid] = Path(filename)
    # Do not silently drop registered readers: every source receives a health status.
    docs = {}
    for source_id, path in source_files.items():
        try:
            docs[source_id] = read_json(path)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            docs[source_id] = {"observed_at": "invalid", "evidence_path": str(path), "error": short_error(exc)}
    result = reconcile(registry, docs, asof=parse_time(args.as_of) if args.as_of else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("RECONCILIATION: meta_at_least={meta_scheduled_lower_bound} cloudflare={cloudflare_scheduled} "
          "published={graph_published} missing_sources={missing_or_unverified_sources}".format(**result["counts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
