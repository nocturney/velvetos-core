"""Honest unavailable domains for v1 — never fake empty collections."""

from __future__ import annotations

from typing import Any

from velvetos_control_api.schema import collection_unavailable


# Domains intentionally not projected in Control API v1.
# Canonical SoTs exist elsewhere; this gateway does not yet adapt them.
V1_UNAVAILABLE = {
    "production": {
        "reason": "not_yet_projected — production cards live under packages/vfprod (print.done); no Control API adapter in v1",
        "hintSource": "packages/vfprod/hq/cards + packages/vfprod/data/print-events.jsonl",
    },
    "content": {
        "reason": "not_yet_projected — content calendar/approval remain packages/vfgrowth; no Control API adapter in v1",
        "hintSource": "packages/vfgrowth/CALENDAR.md + packages/vfgrowth/data/approval-queue.json",
    },
    "files": {
        "reason": "not_yet_projected — media vault stays packages/vfmedia/catalog.json; no Control API adapter in v1",
        "hintSource": "packages/vfmedia/catalog.json",
    },
    "agents": {
        "reason": "not_yet_projected — desk specialists are .cursor/vf-desk.json; no Control API agent roster in v1",
        "hintSource": ".cursor/vf-desk.json",
    },
    "models": {
        "reason": "not_yet_projected — 3D/model pipelines stay vfprod/vfsku; no Control API models domain in v1",
        "hintSource": "packages/vfsku + packages/vfprod",
    },
}


class UnavailableDomainsContribution:
    id = "unavailable_domains"
    domain = "unavailable"

    def project(self, ctx: Any) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name, meta in V1_UNAVAILABLE.items():
            out[name] = collection_unavailable(
                reason=meta["reason"],
                source=meta["hintSource"],
                state="unavailable",
            )
        return {"collections": out}

    def search(self, query: str, ctx: Any) -> list[dict[str, Any]]:
        # Unavailable domains are not searchable — do not invent hits
        return []
