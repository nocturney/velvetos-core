"""Lightweight federated search over currently projected domains — no search DB."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

from velvetos_control_api.errors import BAD_REQUEST, ControlApiError
from velvetos_control_api.registry import ProjectContext, load_contributions, repo_root
from velvetos_control_api.schema import ALLOWED_DESTINATION_PREFIXES, MAX_QUERY_LEN, now_iso

_SAFE_DEST = re.compile(r"^/[a-z0-9][a-z0-9_/\-]*$", re.IGNORECASE)


def validate_destination(dest: str) -> bool:
    if not dest or not isinstance(dest, str):
        return False
    if "://" in dest or dest.startswith("//"):
        return False
    if any(x in dest for x in ("..", "\\", "\n", "\r", " ", "<", ">", "'", '"', "`")):
        return False
    if not _SAFE_DEST.match(dest):
        return False
    return any(dest == p.rstrip("/") or dest.startswith(p) for p in ALLOWED_DESTINATION_PREFIXES)


def search(query: str, *, root=None, limit: int = 50) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        raise ControlApiError(BAD_REQUEST, "query parameter q is required", status=400)
    if len(q) > MAX_QUERY_LEN:
        raise ControlApiError(BAD_REQUEST, f"query exceeds {MAX_QUERY_LEN} characters", status=400)
    # Reject path/command injection attempts in the query itself (search is lexical only)
    if any(tok in q for tok in ("\x00", "`", "$(", "${", ";", "|", "&&")):
        raise ControlApiError(BAD_REQUEST, "query contains forbidden characters", status=400)

    root = root or repo_root()
    ctx = ProjectContext(root=root, generated_at=now_iso())
    results: list[dict[str, Any]] = []
    domains_searched: list[str] = []

    for c in load_contributions():
        domains_searched.append(getattr(c, "domain", c.id))
        try:
            hits = c.search(q, ctx) or []
        except Exception:
            continue
        for hit in hits:
            dest = hit.get("destination") or ""
            if not validate_destination(dest):
                # Drop illegal destinations rather than inventing a redirect
                continue
            results.append(
                {
                    "id": hit.get("id"),
                    "type": hit.get("type"),
                    "module": hit.get("module"),
                    "title": hit.get("title"),
                    "source": hit.get("source"),
                    "status": hit.get("status"),
                    "destination": dest,
                }
            )
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    return {
        "schema": "velvetos.control.v1.search",
        "generatedAt": now_iso(),
        "query": q,
        "results": results,
        "meta": {
            "domainsSearched": domains_searched,
            "note": "Federated over projected domains only — no search database",
        },
    }


def decode_query_param(raw: str | None) -> str:
    if raw is None:
        return ""
    return unquote(raw).strip()
