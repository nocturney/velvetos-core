"""Normalize existing capability registries — no competing registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from velvetos_control_api.schema import (
    normalize_cap_status,
    normalize_risk,
    now_iso,
    provenance,
)


class CapabilitiesContribution:
    id = "capabilities"
    domain = "capabilities"

    def project(self, ctx: Any) -> dict[str, Any]:
        caps = normalize_all_capabilities(ctx.root)
        return {
            "capabilities": caps,
            "envelope": {
                "state": "ready",
                "count": len(caps),
                "provenance": provenance(
                    source="packages/vfops/hq/capabilities.json + packages/vfigos/CAPABILITIES.json",
                    verified_at=now_iso(),
                    freshness="fresh",
                    authority="canonical",
                ),
            },
        }

    def search(self, query: str, ctx: Any) -> list[dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return []
        hits: list[dict[str, Any]] = []
        for cap in normalize_all_capabilities(ctx.root):
            blob = f"{cap.get('id','')} {cap.get('label','')} {cap.get('domain','')}".lower()
            if q in blob:
                hits.append(
                    {
                        "id": cap["id"],
                        "type": "capability",
                        "module": "capabilities",
                        "title": cap.get("label") or cap["id"],
                        "source": cap.get("provenance", {}).get("source"),
                        "status": cap.get("status"),
                        "destination": f"/capabilities/{cap['id']}",
                    }
                )
        return hits


def normalize_all_capabilities(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    out.extend(_from_office(root))
    out.extend(_from_instagram(root))
    # Dedupe by id — office registry wins on collision
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for cap in out:
        cid = cap["id"]
        if cid in seen:
            continue
        seen.add(cid)
        deduped.append(cap)
    return deduped


def _from_office(root: Path) -> list[dict[str, Any]]:
    path = root / "packages" / "vfops" / "hq" / "capabilities.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    verified = data.get("version") or data.get("updatedAt")
    rows: list[dict[str, Any]] = []
    for raw in data.get("capabilities") or []:
        gate = raw.get("gate")
        status = normalize_cap_status(gate=gate)
        risk = normalize_risk(None, gate=gate)
        rows.append(
            {
                "id": raw.get("id"),
                "domain": _domain_from_id(raw.get("id") or ""),
                "label": raw.get("label") or raw.get("id"),
                "status": status,
                "risk": risk,
                "provider": raw.get("tool"),
                "reason": raw.get("notes"),
                "verifiedAt": verified,
                "gate": gate,
                "packs": raw.get("packs") or [],
                "provenance": provenance(
                    source="packages/vfops/hq/capabilities.json",
                    verified_at=str(verified) if verified else None,
                    freshness="fresh",
                    authority="canonical",
                ),
            }
        )
    return rows


def _from_instagram(root: Path) -> list[dict[str, Any]]:
    path = root / "packages" / "vfigos" / "CAPABILITIES.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    auth = data.get("auth") or data.get("currentStatus")
    verified = None
    rv = data.get("remoteVerify") or {}
    if isinstance(rv, dict):
        verified = rv.get("chatgptVerifiedAt") or rv.get("date")
        ig = rv.get("insightsGraphCompat") or {}
        if isinstance(ig, dict) and ig.get("verifiedAt"):
            verified = ig.get("verifiedAt")
    rows: list[dict[str, Any]] = []
    for raw in data.get("capabilities") or []:
        supported = raw.get("supported")
        raw_status = raw.get("status")
        status = normalize_cap_status(
            raw_status=raw_status,
            supported=supported if isinstance(supported, bool) else None,
            auth=auth if isinstance(auth, str) else None,
        )
        # IG write/publish stays approval-sensitive per constitution
        cid = raw.get("id") or ""
        risk = "GREEN"
        if "publish" in cid or "update" in cid or "delete" in cid or "dm" in cid:
            risk = "ORANGE"
            if status == "AVAILABLE":
                status = "APPROVAL_REQUIRED"
        if raw_status == "unsupported_by_official_graph" or supported is False:
            risk = "RED"
            status = "UNAVAILABLE"
        rows.append(
            {
                "id": cid,
                "domain": "instagram",
                "label": raw.get("he") or cid,
                "status": status,
                "risk": risk,
                "provider": data.get("providerPreference") or "instagram-mcp",
                "reason": raw.get("note"),
                "verifiedAt": verified,
                "tools": raw.get("tools") or [],
                "provenance": provenance(
                    source="packages/vfigos/CAPABILITIES.json",
                    verified_at=str(verified) if verified else None,
                    freshness="fresh" if verified else "unknown",
                    authority="canonical",
                ),
            }
        )
    return rows


def _domain_from_id(cid: str) -> str:
    if "." in cid:
        return cid.split(".", 1)[0]
    return "office"
