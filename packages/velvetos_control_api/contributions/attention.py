"""Attention / blockers — owner surface + autonomy blockers. No invented metrics."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from velvetos_control_api.schema import (
    collection_ready,
    collection_unavailable,
    normalize_risk,
    now_iso,
    provenance,
)


class AttentionContribution:
    id = "attention"
    domain = "attention"

    def project(self, ctx: Any) -> dict[str, Any]:
        root: Path = ctx.root
        items: list[dict[str, Any]] = []
        sources_used: list[str] = []
        errors: list[str] = []

        # Owner surface via control plane (red/orange only)
        scripts = root / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        try:
            import vf_control_plane as cp  # noqa: WPS433

            for row in cp.owner_surface_items():
                items.append(_normalize_attention(row, source="office/control (owner_surface)"))
            sources_used.append("scripts/vf_control_plane.py#owner_surface_items")
        except Exception as exc:
            errors.append(f"owner_surface:{type(exc).__name__}")

        try:
            import vf_autonomy as auto  # noqa: WPS433

            for row in auto.blockers():
                items.append(_normalize_attention(row, source=row.get("source") or "vf_autonomy.blockers"))
            sources_used.append("scripts/vf_autonomy.py#blockers")
        except Exception as exc:
            errors.append(f"blockers:{type(exc).__name__}")

        # Deduplicate by id
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for it in items:
            iid = str(it.get("id") or "")
            if iid and iid in seen:
                continue
            if iid:
                seen.add(iid)
            deduped.append(it)

        if not sources_used:
            return {
                "attention": collection_unavailable(
                    reason="attention adapters unavailable: " + ",".join(errors) or "unknown",
                    source="office/control + vf_autonomy",
                    state="unavailable",
                )
            }

        env = collection_ready(
            deduped,
            source=" + ".join(sources_used),
            verified_at=now_iso(),
            freshness="live",
            extra={"adapterErrors": errors or None},
        )
        return {"attention": env}

    def search(self, query: str, ctx: Any) -> list[dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return []
        env = self.project(ctx).get("attention") or {}
        if env.get("state") != "ready" or env.get("items") is None:
            return []
        hits: list[dict[str, Any]] = []
        for it in env["items"]:
            blob = f"{it.get('id','')} {it.get('title','')} {it.get('status','')}".lower()
            if q in blob:
                hits.append(
                    {
                        "id": it.get("id"),
                        "type": "attention",
                        "module": "attention",
                        "title": it.get("title") or it.get("id"),
                        "source": (it.get("provenance") or {}).get("source"),
                        "status": it.get("status"),
                        "destination": f"/attention/{it.get('id')}",
                    }
                )
        return hits


def _normalize_attention(row: dict[str, Any], *, source: str) -> dict[str, Any]:
    risk = normalize_risk(row.get("risk"))
    title = (
        row.get("title")
        or row.get("blocked_item")
        or row.get("detail")
        or row.get("code")
        or row.get("id")
    )
    return {
        "id": row.get("id") or row.get("code") or f"att-{hash(str(row)) & 0xFFFFFFFF:x}",
        "title": title,
        "status": row.get("state") or row.get("status") or row.get("bucket") or "open",
        "risk": risk,
        "waitingFor": row.get("waiting_for"),
        "nextAction": row.get("next_action"),
        "bucket": row.get("bucket"),
        "provenance": provenance(
            source=source,
            verified_at=row.get("since") or row.get("updated_at") or row.get("created_at"),
            freshness="live",
            authority="projection",
        ),
    }
