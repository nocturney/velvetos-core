"""Read-only projections for operational Velvet Factory domains.

Each adapter reads an existing canonical source and keeps missing/unknown values
explicit. No writes, no inferred prices, and no fabricated telemetry.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from velvetos_control_api.schema import collection_ready, collection_unavailable


def _json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _unavailable(source: str, reason: str) -> dict[str, Any]:
    return collection_unavailable(reason=reason, source=source)


def project_production(root: Path) -> dict[str, Any]:
    fleet_path = root / "packages" / "vfprod" / "FLEET.json"
    fleet = _json(fleet_path)
    if fleet is None:
        return _unavailable("packages/vfprod/FLEET.json", "production fleet source missing")

    items: list[dict[str, Any]] = []
    for raw in fleet.get("printers") or []:
        if not isinstance(raw, dict):
            continue
        items.append({
            "kind": "printer",
            "id": raw.get("id"),
            "brand": raw.get("brand"),
            "model": raw.get("model"),
            "status": raw.get("status") or "unknown",
            "enclosure": raw.get("enclosure"),
            "watchtowerProtocol": raw.get("watchtowerProtocol"),
        })

    events_path = root / "packages" / "vfprod" / "data" / "print-events.jsonl"
    event_count = 0
    if events_path.is_file():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = raw.get("payload") if isinstance(raw, dict) else None
            if not isinstance(payload, dict):
                payload = {}
            items.append({
                "kind": "print_event",
                "id": payload.get("event_id") or raw.get("correlationId"),
                "name": raw.get("name"),
                "producedAt": raw.get("producedAt"),
                "printer": payload.get("printer"),
                "status": payload.get("status"),
                "sku": payload.get("sku"),
                "productName": payload.get("product_name"),
                "approvalState": payload.get("approval_state"),
                "note": payload.get("note"),
            })
            event_count += 1

    maintenance = _json(root / "packages" / "vfprod" / "data" / "maintenance-snapshot.json") or {}
    out = collection_ready(
        items,
        source="packages/vfprod/FLEET.json + packages/vfprod/data/print-events.jsonl",
        verified_at=fleet.get("updatedAt"),
        extra={
            "printerCount": len(fleet.get("printers") or []),
            "eventCount": event_count,
            "maintenanceCount": len(maintenance.get("printers") or []),
            "hqPrints": fleet.get("hqPrints"),
            "materials": fleet.get("materials") or [],
        },
    )
    return out


def project_content(root: Path) -> dict[str, Any]:
    path = root / "packages" / "vfgrowth" / "data" / "approval-queue.json"
    data = _json(path)
    if data is None:
        return _unavailable("packages/vfgrowth/data/approval-queue.json", "content approval queue missing")

    items: list[dict[str, Any]] = []
    for raw in data.get("items") or []:
        if not isinstance(raw, dict):
            continue
        items.append({
            "id": raw.get("content_id"),
            "format": raw.get("format"),
            "gate": raw.get("gate"),
            "disposition": raw.get("disposition"),
            "ownerSurface": raw.get("ownerSurface"),
            "slot": raw.get("slot"),
            "calendarRule": raw.get("calendar_rule"),
            "humanMarked": raw.get("human_marked"),
            "missingGates": raw.get("missing_gates") or [],
            "reconcileNote": raw.get("reconcileNote"),
        })
    return collection_ready(
        items,
        source="packages/vfgrowth/data/approval-queue.json",
        verified_at=data.get("updatedAt"),
    )


def project_files(root: Path) -> dict[str, Any]:
    path = root / "packages" / "vfmedia" / "catalog.json"
    data = _json(path)
    if data is None:
        return _unavailable("packages/vfmedia/catalog.json", "media catalog missing")

    all_items = [item for item in (data.get("items") or []) if isinstance(item, dict)]
    # Keep the snapshot bounded; totalCount always reflects the entire canonical catalog.
    latest = sorted(all_items, key=lambda item: str(item.get("uploadedAt") or ""), reverse=True)[:60]
    items: list[dict[str, Any]] = []
    for raw in latest:
        source_file = raw.get("sourceFile") if isinstance(raw.get("sourceFile"), dict) else {}
        approval = raw.get("versionApproval") if isinstance(raw.get("versionApproval"), dict) else {}
        intake = raw.get("intake") if isinstance(raw.get("intake"), dict) else {}
        items.append({
            "id": raw.get("id"),
            "sourceFileId": source_file.get("id"),
            "status": raw.get("status"),
            "uploadedAt": raw.get("uploadedAt"),
            "productLink": raw.get("productLink"),
            "approvalState": approval.get("state"),
            "approvedAt": approval.get("approvedAt"),
            "intakePhase": intake.get("phase"),
            "verifiedAt": intake.get("verifiedAt"),
            "derivativeCount": len(raw.get("derivativeIds") or []),
        })

    status_counts: dict[str, int] = {}
    for raw in all_items:
        status = str(raw.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    out = collection_ready(
        items,
        source="packages/vfmedia/catalog.json",
        verified_at=data.get("updatedAt"),
        extra={
            "totalCount": len(all_items),
            "projectedCount": len(items),
            "truncated": len(items) < len(all_items),
            "statusCounts": status_counts,
        },
    )
    out["count"] = len(all_items)
    return out


def _desk_path(root: Path) -> Path:
    instance_id = (os.environ.get("VELVETOS_INSTANCE_ID") or "velvet-factory").strip()
    return root / "instances" / instance_id / ".cursor" / "vf-desk.json"


def project_agents(root: Path) -> dict[str, Any]:
    path = _desk_path(root)
    data = _json(path)
    if data is None:
        return _unavailable(str(path), "instance agent desk missing")

    specialist_to_seat: dict[str, str] = {}
    for seat in data.get("seats") or []:
        if not isinstance(seat, dict):
            continue
        for slug in seat.get("specialists") or []:
            specialist_to_seat[str(slug)] = str(seat.get("id") or "")

    items: list[dict[str, Any]] = []
    for raw in data.get("desk") or []:
        if not isinstance(raw, dict):
            continue
        slug = str(raw.get("slug") or "")
        items.append({
            "id": slug,
            "seat": specialist_to_seat.get(slug),
            "job": raw.get("job"),
            "packs": raw.get("packs") or [],
            "tools": raw.get("tools") or [],
        })
    return collection_ready(
        items,
        source=f"instances/{data.get('instanceId') or 'velvet-factory'}/.cursor/vf-desk.json#desk",
        verified_at=data.get("updatedAt"),
        extra={"seatCount": len(data.get("seats") or [])},
    )


def project_models(root: Path) -> dict[str, Any]:
    path = root / "packages" / "vfsku" / "SHELF.json"
    data = _json(path)
    if data is None:
        return _unavailable("packages/vfsku/SHELF.json", "model shelf missing")

    items: list[dict[str, Any]] = []
    for raw in data.get("slots") or []:
        if not isinstance(raw, dict):
            continue
        items.append({
            "id": raw.get("id"),
            "status": raw.get("status"),
            "name": raw.get("name"),
            "sourceId": raw.get("sourceId"),
            "license": raw.get("license"),
            "licenseChecked": raw.get("licenseChecked"),
            "hardware": raw.get("hardware"),
            "sliceGrams": raw.get("sliceGrams"),
            "sliceMinutes": raw.get("sliceMinutes"),
            "material": raw.get("material"),
            "shelfCount": raw.get("shelfCount"),
            "israeliBrandStop": raw.get("israeliBrandStop"),
        })

    occupied = sum(1 for item in items if item.get("status") != "empty")
    ready = sum(1 for item in items if item.get("status") == "ready")
    return collection_ready(
        items,
        source="packages/vfsku/SHELF.json",
        verified_at=data.get("updatedAt"),
        extra={
            "maxSlots": data.get("maxSlots"),
            "occupiedCount": occupied,
            "readyCount": ready,
        },
    )


class OperationalDomainsContribution:
    id = "operational_domains"
    domain = "operations"

    def project(self, ctx: Any) -> dict[str, Any]:
        return {
            "collections": {
                "production": project_production(ctx.root),
                "content": project_content(ctx.root),
                "files": project_files(ctx.root),
                "agents": project_agents(ctx.root),
                "models": project_models(ctx.root),
            }
        }

    def search(self, query: str, ctx: Any) -> list[dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return []
        hits: list[dict[str, Any]] = []
        projections = {
            "production": project_production(ctx.root),
            "content": project_content(ctx.root),
            "files": project_files(ctx.root),
            "agents": project_agents(ctx.root),
            "models": project_models(ctx.root),
        }
        for domain, envelope in projections.items():
            if envelope.get("state") != "ready":
                continue
            for item in envelope.get("items") or []:
                blob = json.dumps(item, ensure_ascii=False, sort_keys=True).lower()
                if q not in blob:
                    continue
                item_id = item.get("id")
                hits.append({
                    "id": f"{domain}.{item_id}",
                    "type": domain,
                    "module": domain,
                    "title": item.get("name") or item.get("job") or str(item_id),
                    "source": envelope.get("provenance", {}).get("source"),
                    "status": item.get("status") or item.get("gate") or "ready",
                    "destination": f"/{domain}/{item_id}",
                })
                if len(hits) >= 20:
                    return hits
        return hits
