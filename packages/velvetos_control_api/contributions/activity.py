"""Activity / projection metadata from handoff, decisions, living-studio pulses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from velvetos_control_api.schema import collection_ready, now_iso, provenance


class ActivityContribution:
    id = "activity"
    domain = "activity"

    def project(self, ctx: Any) -> dict[str, Any]:
        root: Path = ctx.root
        items: list[dict[str, Any]] = []

        handoff = root / "office" / "control" / "HANDOFF.json"
        if handoff.is_file():
            data = json.loads(handoff.read_text(encoding="utf-8"))
            items.append(
                {
                    "id": f"handoff-{data.get('date') or 'latest'}",
                    "type": "handoff",
                    "title": "Manager handoff",
                    "status": "ready",
                    "summary": {
                        "waiting": len(data.get("waiting") or []),
                        "failed": len(data.get("failed") or []),
                        "owner_blocked": len(data.get("owner_blocked") or []),
                        "next": (data.get("next") or [])[:5],
                    },
                    "provenance": provenance(
                        source="office/control/HANDOFF.json",
                        verified_at=data.get("updatedAt"),
                        freshness="fresh",
                        authority="canonical",
                    ),
                }
            )

        decisions = root / "office" / "control" / "decisions.jsonl"
        if decisions.is_file():
            lines = [ln for ln in decisions.read_text(encoding="utf-8").splitlines() if ln.strip()]
            # Last 5 decisions as activity (not inventing counts of "work done")
            recent: list[dict[str, Any]] = []
            for ln in lines[-5:]:
                try:
                    recent.append(json.loads(ln))
                except json.JSONDecodeError:
                    continue
            for d in recent:
                items.append(
                    {
                        "id": d.get("decision_id") or d.get("id") or f"dec-{hash(ln) & 0xFFFF:x}",
                        "type": "decision",
                        "title": d.get("summary") or d.get("title") or d.get("decision_id"),
                        "status": d.get("status") or "recorded",
                        "provenance": provenance(
                            source="office/control/decisions.jsonl",
                            verified_at=d.get("at") or d.get("created_at"),
                            freshness="fresh",
                            authority="canonical",
                        ),
                    }
                )

        pulse = root / "packages" / "velvetos" / "living-studio" / "data" / "pulse-latest.json"
        if pulse.is_file():
            data = json.loads(pulse.read_text(encoding="utf-8"))
            items.append(
                {
                    "id": "studio-pulse-latest",
                    "type": "studio-pulse",
                    "title": "Studio Pulse projection",
                    "status": "projection",
                    "summary": {
                        "stuck": data.get("what_stuck") or [],
                        "requiresChristian": data.get("what_requires_christian") or [],
                    },
                    "provenance": provenance(
                        source="packages/velvetos/living-studio/data/pulse-latest.json",
                        verified_at=data.get("generatedAt"),
                        freshness="stale",  # disk projection, not live floor
                        authority="projection",
                    ),
                }
            )

        autonomy = (
            root / "packages" / "velvetos" / "living-studio" / "data" / "autonomy-latest.json"
        )
        if autonomy.is_file():
            data = json.loads(autonomy.read_text(encoding="utf-8"))
            items.append(
                {
                    "id": "autonomy-snapshot-latest",
                    "type": "autonomy-snapshot",
                    "title": "Autonomy composition snapshot",
                    "status": "projection",
                    "jobs_state": data.get("jobs_state"),
                    "provenance": provenance(
                        source="packages/velvetos/living-studio/data/autonomy-latest.json",
                        verified_at=data.get("generatedAt"),
                        freshness="stale",
                        authority="projection",
                    ),
                }
            )

        return {
            "activity": collection_ready(
                items,
                source="office/control + living-studio projections",
                verified_at=now_iso(),
                freshness="fresh",
            )
        }

    def search(self, query: str, ctx: Any) -> list[dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return []
        env = self.project(ctx).get("activity") or {}
        if env.get("items") is None:
            return []
        hits: list[dict[str, Any]] = []
        for it in env["items"]:
            blob = f"{it.get('id','')} {it.get('title','')} {it.get('type','')}".lower()
            if q in blob:
                hits.append(
                    {
                        "id": it.get("id"),
                        "type": it.get("type") or "activity",
                        "module": "activity",
                        "title": it.get("title") or it.get("id"),
                        "source": (it.get("provenance") or {}).get("source"),
                        "status": it.get("status"),
                        "destination": f"/activity/{it.get('id')}",
                    }
                )
        return hits
