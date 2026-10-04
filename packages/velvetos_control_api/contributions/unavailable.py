"""Fail-closed fallback envelopes for operational domains when adapters cannot project their SoT."""

from __future__ import annotations

from typing import Any

from velvetos_control_api.schema import collection_unavailable


# Fallback metadata. OperationalDomainsContribution runs after this contribution
# and replaces these envelopes only when the canonical source is readable.
V1_UNAVAILABLE = {
    "production": {
        "reason": "projection_unavailable — production source could not be adapted",
        "hintSource": "packages/vfprod/hq/cards + packages/vfprod/data/print-events.jsonl",
    },
    "content": {
        "reason": "projection_unavailable — content source could not be adapted",
        "hintSource": "packages/vfgrowth/CALENDAR.md + packages/vfgrowth/data/approval-queue.json",
    },
    "files": {
        "reason": "projection_unavailable — media catalog could not be adapted",
        "hintSource": "packages/vfmedia/catalog.json",
    },
    "agents": {
        "reason": "projection_unavailable — agent desk could not be adapted",
        "hintSource": "instance:surface:toolDesk",
    },
    "models": {
        "reason": "projection_unavailable — model shelf could not be adapted",
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
