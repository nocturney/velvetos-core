"""Project the canonical Velvet Factory tool desk into the Control API.

This contribution does not create a second registry. It reads the instance desk
already used by the office frontend and normalizes only runtime availability.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from velvetos_control_api.instance_sources import InstanceSourceError, resolve_instance_surface
from velvetos_control_api.schema import now_iso, provenance


_READY = {"ready", "hq-native"}
_NEEDS_AUTH = {"needsauth"}
_BLOCKED = {"not-relevant"}


def _normalized_status(raw_status: str | None, namespace: str | None) -> str:
    raw = (raw_status or "").strip().lower()
    ns = (namespace or "").strip().lower()
    if raw in _BLOCKED:
        return "BLOCKED"
    if raw in _NEEDS_AUTH:
        return "NEEDS_AUTH"
    if raw in _READY:
        return "AVAILABLE"
    if raw == "skill-installed":
        return "AVAILABLE"
    if raw == "plugin-installed" and ns != "not-on-this-cloud-agent":
        return "AVAILABLE"
    if raw in {"plugin-installed", "not-on-this-cloud-agent", "desktop-credentials", "desktop-optional"}:
        return "UNAVAILABLE"
    return "UNAVAILABLE"


def normalize_integrations(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        path = resolve_instance_surface(root, "toolDesk", env=os.environ)
    except InstanceSourceError as exc:
        return [], {
            "state": "unavailable",
            "items": None,
            "count": None,
            "reason": f"instance tool desk unavailable: {exc}",
            "provenance": provenance(
                source="instance:surface:toolDesk",
                verified_at=None,
                freshness="unknown",
                authority="canonical",
            ),
        }
    if not path.is_file():
        return [], {
            "state": "unavailable",
            "items": None,
            "count": None,
            "reason": f"instance tool desk not found: {path.relative_to(root) if path.is_relative_to(root) else path}",
            "provenance": provenance(
                source=str(path),
                verified_at=None,
                freshness="unknown",
                authority="canonical",
            ),
        }

    data = json.loads(path.read_text(encoding="utf-8"))
    tools = data.get("tools") or {}
    rows: list[dict[str, Any]] = []
    for tool_id, raw in tools.items():
        if not isinstance(raw, dict):
            continue
        source_status = raw.get("status")
        namespace = raw.get("namespace")
        rows.append(
            {
                "id": tool_id,
                "label": raw.get("label") or tool_id,
                "status": _normalized_status(source_status, namespace),
                "sourceStatus": source_status,
                "namespace": namespace,
                "mode": raw.get("mode"),
                "useWhen": raw.get("useWhen"),
                "rule": raw.get("rule"),
                "failover": raw.get("failover"),
                "allowed": raw.get("allowed") or [],
                "forbidden": raw.get("forbidden") or [],
                "account": raw.get("account"),
                "verifiedAt": raw.get("verifiedAt") or data.get("updatedAt"),
                "provenance": provenance(
                    source=f"instances/{data.get('instanceId') or 'unknown-instance'}/.cursor/vf-desk.json#tools.{tool_id}",
                    verified_at=str(raw.get("verifiedAt") or data.get("updatedAt") or now_iso()),
                    freshness="fresh",
                    authority="canonical",
                ),
            }
        )

    envelope = {
        "state": "ready",
        "items": rows,
        "count": len(rows),
        "provenance": provenance(
            source=f"instances/{data.get('instanceId') or 'unknown-instance'}/.cursor/vf-desk.json#tools",
            verified_at=str(data.get("updatedAt") or now_iso()),
            freshness="fresh",
            authority="canonical",
        ),
    }
    return rows, envelope


class IntegrationsContribution:
    id = "integrations"
    domain = "integrations"

    def project(self, ctx: Any) -> dict[str, Any]:
        rows, envelope = normalize_integrations(ctx.root)
        return {"integrations": rows, "collections": {"integrations": envelope}}

    def search(self, query: str, ctx: Any) -> list[dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return []
        rows, envelope = normalize_integrations(ctx.root)
        if envelope.get("state") != "ready":
            return []
        hits: list[dict[str, Any]] = []
        for row in rows:
            blob = " ".join(
                str(row.get(key) or "")
                for key in ("id", "label", "namespace", "mode", "useWhen", "status", "sourceStatus")
            ).lower()
            if q in blob:
                hits.append(
                    {
                        "id": f"integration.{row['id']}",
                        "type": "integration",
                        "module": "integrations",
                        "title": row.get("label") or row["id"],
                        "source": row.get("provenance", {}).get("source"),
                        "status": row.get("status"),
                        "destination": f"/integrations/{row['id']}",
                    }
                )
        return hits
