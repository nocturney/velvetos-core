"""MCP tools: read-only live CTA / constitution audit."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_REPO = _HERE.parents[2] if len(_HERE.parents) >= 3 else None
if _REPO and str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

try:
    from cta_audit import audit_list_media_payload, audit_profile
except ImportError:  # pragma: no cover — repo layout
    from packages.vfigos.cta_audit import audit_list_media_payload, audit_profile


def apply_cta_audit_tools(mcp: Any) -> None:
    from instagram_mcp import auth
    from instagram_mcp import validators as V
    from instagram_mcp.server import MEDIA_FIELDS, PROFILE_FIELDS, _guard

    @mcp.tool()
    def audit_public_cta(account: str | None = None, *, limit: int = 25) -> dict[str, Any]:
        """Audit live captions + bio against PUBLIC_CURRENT_CTA (read-only).

        Flags WhatsApp/phone public CTA, >5 hashtags, and obvious constitution
        violations. Historical live items are reported separately from publish
        candidates. Never mutates captions or bio (Graph does not support caption/
        bio edits anyway).
        """

        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            lim = V.validate_limit(limit)
            profile = client.get(acct.ig_user_id, fields=PROFILE_FIELDS)
            items = client.get_paginated(
                f"{acct.ig_user_id}/media",
                fields=MEDIA_FIELDS,
                limit=lim,
                max_items=lim,
            )
            report = audit_list_media_payload({"media": items}, profile=profile)
            report["account"] = acct.label
            return report

        return _guard("audit_public_cta", {"account": account, "limit": limit}, _impl)

    @mcp.tool()
    def audit_profile_cta(account: str | None = None) -> dict[str, Any]:
        """Audit live profile bio/name/website against PUBLIC_CURRENT_CTA (read-only)."""

        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            profile = client.get(acct.ig_user_id, fields=PROFILE_FIELDS)
            out = audit_profile(profile)
            out["ok"] = True
            out["account"] = acct.label
            return out

        return _guard("audit_profile_cta", {"account": account}, _impl)
