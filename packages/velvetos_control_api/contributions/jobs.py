"""Jobs collection via existing vf_jobs_adapter — never invent zero jobs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from velvetos_control_api.schema import (
    collection_ready,
    collection_unavailable,
    now_iso,
    provenance,
)


class JobsContribution:
    id = "jobs"
    domain = "jobs"

    def project(self, ctx: Any) -> dict[str, Any]:
        root: Path = ctx.root
        scripts = root / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        try:
            import vf_jobs_adapter as jobs  # noqa: WPS433
        except Exception as exc:
            return {
                "jobs": collection_unavailable(
                    reason=f"jobs adapter import failed: {type(exc).__name__}",
                    source="scripts/vf_jobs_adapter.py",
                    state="unavailable",
                )
            }

        # status() is non-mutating; consumer_view may attempt pull — prefer status
        # then read cache only when hydrated.
        try:
            st = jobs.status()
        except Exception as exc:
            return {
                "jobs": collection_unavailable(
                    reason=f"jobs status failed: {type(exc).__name__}",
                    source="scripts/vf_jobs_adapter.py#status",
                    state="unavailable",
                )
            }

        state = st.get("jobs_state") or "unknown"
        verified_at = st.get("lastPullAt")
        source = "scripts/vf_jobs_adapter.py (Sheet canonical; local CSV cache)"

        if state == "ready" and st.get("readyForConsumers"):
            rows = jobs.read_cache() if st.get("cacheExists") else []
            items = [_job_item(r, verified_at=verified_at) for r in rows]
            return {
                "jobs": collection_ready(
                    items,
                    source=source,
                    verified_at=verified_at or now_iso(),
                    freshness="fresh",
                    extra={
                        "jobs_state": "ready",
                        "canonical": st.get("canonical"),
                        "rule": st.get("rule"),
                    },
                )
            }

        # needs_sync / conflict / unknown — never claim zero jobs
        mapped = {
            "needs_sync": "needs_sync",
            "conflict": "conflict",
            "unknown": "unknown",
        }.get(state, "unavailable")
        return {
            "jobs": collection_unavailable(
                reason=st.get("rule")
                or f"jobs_state={state} — unhydrated/unavailable cache ≠ zero jobs",
                source=source,
                verified_at=verified_at,
                state=mapped,
                extra={
                    "jobs_state": state,
                    "canonical": st.get("canonical"),
                    "dirty": st.get("dirty"),
                    "cacheExists": st.get("cacheExists"),
                    "cacheRowCountUntrusted": st.get("cacheRowCountUntrusted"),
                },
            )
        }

    def search(self, query: str, ctx: Any) -> list[dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return []
        env = self.project(ctx).get("jobs") or {}
        if env.get("state") != "ready" or not env.get("items"):
            return []
        hits: list[dict[str, Any]] = []
        for it in env["items"]:
            blob = " ".join(
                str(it.get(k) or "")
                for k in ("id", "title", "client", "sku", "stage", "status")
            ).lower()
            if q in blob:
                hits.append(
                    {
                        "id": it.get("id"),
                        "type": "job",
                        "module": "jobs",
                        "title": it.get("title") or it.get("id"),
                        "source": (it.get("provenance") or {}).get("source"),
                        "status": it.get("stage") or it.get("status"),
                        "destination": f"/jobs/{it.get('id')}",
                    }
                )
        return hits


def _job_item(row: dict[str, str], *, verified_at: str | None) -> dict[str, Any]:
    jid = row.get("job_id") or ""
    what = row.get("what_asked") or ""
    client = row.get("client_label") or ""
    title = what or client or jid
    # Price stays as stored string — never invent; may be empty / X ₪
    price = row.get("price") or None
    return {
        "id": jid,
        "title": title,
        "client": client or None,
        "sku": row.get("sku") or None,
        "stage": row.get("stage") or None,
        "status": row.get("stage") or row.get("file_status") or None,
        "due": row.get("due") or None,
        "price": price,  # may be None — UI must not treat missing as 0
        "channel": row.get("channel") or None,
        "provenance": provenance(
            source="office/ledger/live/jobs.csv (adapter cache; Sheet canonical)",
            verified_at=verified_at,
            freshness="fresh",
            authority="adapter-cache",
        ),
    }
