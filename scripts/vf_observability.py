#!/usr/bin/env python3
"""Local-only OpenTelemetry/OpenInference helpers for VelvetOS.

Telemetry is evidence for debugging, never action authority. Only allowlisted
metadata is persisted; payload bodies, prompts, secrets and connector data are not.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools" / "observability" / "python"
POLICY = ROOT / "packages" / "vfharness" / "observability" / "trace-policy.json"

if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from openinference.instrumentation import OITracer, TraceConfig
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

def load_policy() -> dict[str, Any]:
    data = json.loads(POLICY.read_text(encoding="utf-8"))
    if data.get("role") != "LOCAL_NON_AUTHORITATIVE_TELEMETRY":
        raise RuntimeError("observability policy role mismatch")
    if data.get("authority") is not False or data.get("remote_exporters") != []:
        raise RuntimeError("telemetry must remain non-authoritative and local-only")
    return data


def _plain(value: Any) -> bool:
    if isinstance(value, (str, bool, int, float)):
        return True
    if isinstance(value, (list, tuple)):
        return all(isinstance(x, (str, bool, int, float)) for x in value)
    return False


def sanitize_attributes(attrs: dict[str, Any] | None) -> dict[str, Any]:
    policy = load_policy()
    allowed = set(policy["allowed_attributes"])
    forbidden = tuple(x.casefold() for x in policy["forbidden_attribute_fragments"])
    clean: dict[str, Any] = {}
    for key, value in (attrs or {}).items():
        folded = key.casefold()
        if key not in allowed:
            raise ValueError(f"telemetry attribute not allowlisted: {key}")
        if any(fragment in folded for fragment in forbidden):
            raise ValueError(f"sensitive telemetry attribute key: {key}")
        if not _plain(value):
            raise ValueError(f"unsupported telemetry attribute value: {key}")
        if isinstance(value, str) and len(value) > 160:
            raise ValueError(f"telemetry string too long: {key}")
        clean[key] = value
    return clean


class LocalTrace:
    def __init__(self) -> None:
        policy = load_policy()
        resource = Resource.create({"service.name": policy["service_name"]})
        self.provider = TracerProvider(resource=resource)
        self.exporter = InMemorySpanExporter()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        wrapped = self.provider.get_tracer("velvetos.observability")
        self.tracer = OITracer(wrapped, TraceConfig())

    def span(self, name: str, oi_kind, attrs: dict[str, Any] | None = None):
        return self.tracer.start_as_current_span(
            name,
            attributes=sanitize_attributes(attrs),
            openinference_span_kind=oi_kind,
            record_exception=False,
            set_status_on_exception=False,
        )

    def snapshot(self) -> list[dict[str, Any]]:
        self.provider.force_flush()
        rows: list[dict[str, Any]] = []
        for span in self.exporter.get_finished_spans():
            ctx = span.context
            parent = span.parent
            attrs = dict(span.attributes or {})
            rows.append({
                "name": span.name,
                "trace_id": f"{ctx.trace_id:032x}",
                "span_id": f"{ctx.span_id:016x}",
                "parent_span_id": f"{parent.span_id:016x}" if parent else None,
                "start_time_ns": span.start_time,
                "end_time_ns": span.end_time,
                "attributes": attrs,
            })
        return rows


def write_receipt(path: Path, *, flow_status: str, spans: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    policy = load_policy()
    body = {
        "schema": 1,
        "role": policy["role"],
        "authority": False,
        "deployment": policy["deployment"],
        "remote_exporters": [],
        "flow_status": flow_status,
        "required_flow": policy["required_flow"],
        "span_count": len(spans),
        "spans": spans,
    }
    path.write_text(
        json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
