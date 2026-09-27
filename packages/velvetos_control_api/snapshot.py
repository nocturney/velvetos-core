"""Assemble velvetos.control.v1 snapshot from registered contributions."""

from __future__ import annotations

from typing import Any

from velvetos_control_api import SCHEMA, SERVICE_NAME
from velvetos_control_api.registry import ProjectContext, load_contributions, repo_root
from velvetos_control_api.schema import now_iso


def build_snapshot(*, root=None) -> dict[str, Any]:
    root = root or repo_root()
    ctx = ProjectContext(root=root, generated_at=now_iso())
    contribs = load_contributions()

    modules: list[Any] = []
    capabilities: list[Any] = []
    integrations: list[Any] = []
    health: list[Any] = []
    attention: list[Any] = []
    activity: list[Any] = []
    flags: dict[str, Any] = {}
    collections: dict[str, Any] = {}
    system_meta: dict[str, Any] = {}
    freshness_candidates: list[str] = []

    for c in contribs:
        slice_ = c.project(ctx)
        if not isinstance(slice_, dict):
            continue

        if "modules" in slice_:
            modules.extend(slice_["modules"] or [])
        if "flags" in slice_ and isinstance(slice_["flags"], dict):
            flags.update(slice_["flags"])
        if "health" in slice_:
            health.extend(slice_["health"] or [])
        if "system" in slice_:
            system_meta = slice_["system"]
        if "capabilities" in slice_:
            capabilities = slice_["capabilities"] or []
        if "integrations" in slice_:
            integrations = slice_["integrations"] or []
        if "attention" in slice_:
            att = slice_["attention"]
            if isinstance(att, dict) and att.get("state") == "ready" and att.get("items") is not None:
                attention = att["items"]
                flags["attentionCollection"] = {
                    "state": att.get("state"),
                    "count": att.get("count"),
                    "provenance": att.get("provenance"),
                }
            else:
                flags["attentionCollection"] = att
                attention = []  # UI list; state is in flags — see also collections
                collections["attention"] = att
        if "activity" in slice_:
            act = slice_["activity"]
            if isinstance(act, dict) and act.get("state") == "ready" and act.get("items") is not None:
                activity = act["items"]
                flags["activityCollection"] = {
                    "state": act.get("state"),
                    "count": act.get("count"),
                    "provenance": act.get("provenance"),
                }
            else:
                flags["activityCollection"] = act
        if "jobs" in slice_:
            collections["jobs"] = slice_["jobs"]
            st = (slice_["jobs"] or {}).get("state")
            if st:
                freshness_candidates.append(st)
        if "collections" in slice_ and isinstance(slice_["collections"], dict):
            collections.update(slice_["collections"])

    # Ensure unavailable domains always present
    for key in ("production", "content", "files", "agents", "models", "jobs"):
        collections.setdefault(
            key,
            {
                "state": "unknown",
                "items": None,
                "count": None,
                "reason": "contribution did not project this domain",
                "provenance": {
                    "source": "velvetos_control_api",
                    "verifiedAt": None,
                    "freshness": "unknown",
                    "receipt": None,
                    "authority": "projection",
                },
            },
        )

    # Top-level attention: if we stored envelope only in collections, expose items honestly
    if "attention" in collections and not attention:
        # Keep attention array empty only when envelope says unavailable — UI must read flags
        pass

    velvetos_health = _derive_velvetos_health(health, collections)
    freshness = _derive_freshness(collections, system_meta)

    return {
        "schema": SCHEMA,
        "generatedAt": ctx.generated_at,
        "connection": "connected",
        "service": SERVICE_NAME,
        "freshness": freshness,
        "flags": {
            **flags,
            "system": system_meta,
            "velvetosHealth": velvetos_health,
        },
        "modules": modules,
        "capabilities": capabilities,
        "integrations": integrations,
        "health": health,
        "attention": attention if flags.get("attentionCollection", {}).get("state") == "ready" else [],
        "activity": activity,
        "collections": collections,
    }


def _derive_velvetos_health(health: list[dict], collections: dict) -> str:
    """Aggregate VelvetOS projection health — not 'all integrations healthy'."""
    statuses = [h.get("status") for h in health]
    if any(s == "unavailable" for s in statuses):
        return "degraded"
    if any(s in {"degraded", "unknown"} for s in statuses):
        return "degraded"
    jobs = collections.get("jobs") or {}
    if jobs.get("state") in {"needs_sync", "conflict", "unavailable", "unknown"}:
        return "degraded"
    return "ok"


def _derive_freshness(collections: dict, system_meta: dict) -> dict[str, Any]:
    jobs = collections.get("jobs") or {}
    verified = None
    if isinstance(jobs.get("provenance"), dict):
        verified = jobs["provenance"].get("verifiedAt")
    if not verified and isinstance(system_meta.get("provenance"), dict):
        verified = system_meta["provenance"].get("verifiedAt")

    state = "unknown"
    jstate = jobs.get("state")
    if jstate == "ready" and system_meta.get("state") == "ready":
        state = "fresh"
    elif jstate in {"needs_sync", "conflict"}:
        state = "stale"
    elif system_meta.get("state") == "ready":
        state = "fresh"

    return {
        "state": state,
        "verifiedAt": verified or now_iso(),
    }
