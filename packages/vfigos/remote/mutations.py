"""Honest Instagram Graph mutation tools for VelvetOS.

Official Meta Graph (Business/Creator) as of 2026-09 research:

| Operation | Official Graph? | Notes |
|---|---|---|
| Update biography | NO | IG User Updating unsupported |
| Update website | NO | same |
| Update name/display | NO | same |
| Update published caption (feed/Reel) | NO | POST /{ig-media-id} only toggles comment_enabled |
| Delete media | YES | DELETE /{ig-media-id} · needs instagram_manage_contents |
| Archive media | NO separate archive API | delete ≠ archive |

STRICT: no browser automation / private API.

Unsupported profile/caption mutations are **NOT** registered as MCP write tools
(agents must not interpret them as available mutations). Source of truth for
capability discovery is `graph_mutation_matrix` only.
"""

from __future__ import annotations

from typing import Any

MATRIX = {
    "update_biography": {
        "supported": False,
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "mcp_tool": None,
        "limitations": "IG User Updating operation is not supported by Instagram Graph API.",
    },
    "update_website": {
        "supported": False,
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "mcp_tool": None,
        "limitations": "IG User Updating operation is not supported by Instagram Graph API.",
    },
    "update_name": {
        "supported": False,
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "mcp_tool": None,
        "limitations": "IG User Updating operation is not supported by Instagram Graph API.",
    },
    "update_media_caption": {
        "supported": False,
        "status": "unsupported_by_official_graph",
        "endpoint": "POST /{ig-media-id}",
        "permissions": ["instagram_basic"],
        "allowed_fields": ["comment_enabled"],
        "mcp_tool": None,
        "limitations": (
            "Official Updating on IG Media only enables/disables comments. "
            "caption parameter is ignored. Feed posts and Reels cannot have captions "
            "edited via Graph. No MCP write tool is exposed for this."
        ),
    },
    "update_profile": {
        "supported": False,
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "mcp_tool": None,
        "covers": ["update_biography", "update_website", "update_name"],
        "limitations": (
            "No official Graph profile write. Not exposed as an MCP write tool. "
            "Human edit via Instagram app; see PROFILE-DESIRED.json."
        ),
    },
    "delete_media": {
        "supported": True,
        "status": "supported_gated",
        "endpoint": "DELETE /{ig-media-id}",
        "permissions": ["instagram_manage_contents"],
        "allowed_fields": [],
        "mcp_tool": "delete_media",
        "limitations": (
            "Destructive/irreversible. Deletes posts, carousels, reels, stories. "
            "Cannot delete individual carousel children. Requires App Review scope "
            "instagram_manage_contents. Requires confirm_irreversible=true + explicit "
            "account. Not exercised live by VelvetOS HQ automation."
        ),
    },
    "archive_media": {
        "supported": False,
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "mcp_tool": None,
        "limitations": "No official archive endpoint distinct from delete.",
    },
}

# Ops that must never appear as MCP tool names (misleading write surface).
NEVER_EXPOSE_AS_WRITE_TOOLS = frozenset(
    {
        "update_profile",
        "update_media_caption",
        "update_biography",
        "update_website",
        "update_name",
        "archive_media",
    }
)


def _unsupported(op: str) -> dict[str, Any]:
    row = MATRIX[op]
    return {
        "ok": False,
        "supported": False,
        "status": "unsupported_by_official_graph",
        "operation": op,
        "matrix": row,
        "mutated": False,
        "note": "Use Instagram app / human edit. MCP will not browser-automate or scrape.",
    }


def apply_mutation_tools(mcp: Any) -> None:
    """Register mutation-related tools.

    Only:
      - graph_mutation_matrix (read-only SoT)
      - delete_media (officially supported, gated)

    Intentionally does NOT register update_profile / update_media_caption so
    agents cannot treat them as available write capabilities.
    """
    from instagram_mcp import auth
    from instagram_mcp import validators as V
    from instagram_mcp.server import _guard

    # Defense: if an older overlay registered misleading write stubs, remove them.
    for name in NEVER_EXPOSE_AS_WRITE_TOOLS:
        try:
            mcp.local_provider.remove_tool(name)
        except Exception:
            try:
                mcp.remove_tool(name)
            except Exception:
                pass

    @mcp.tool()
    def graph_mutation_matrix() -> dict[str, Any]:
        """SOURCE OF TRUTH for Instagram Graph mutation capabilities (read-only).

        Returns supported=true|false per operation. Profile/bio/website/name and
        caption edits are unsupported_by_official_graph and are NOT exposed as
        MCP write tools. Do not invent private-API workarounds. For deletes see
        delete_media (gated, destructive).
        """
        return {
            "ok": True,
            "supported_write_tools": ["delete_media"],
            "unsupported_write_tools_not_exposed": sorted(NEVER_EXPOSE_AS_WRITE_TOOLS),
            "matrix": MATRIX,
            "source": "Meta Instagram Graph API docs 2026-09",
            "law": "graph_mutation_matrix is the capability SoT — do not infer writes from tool name wishlists",
        }

    @mcp.tool()
    def delete_media(
        media_id: str,
        account: str | None = None,
        *,
        confirm_irreversible: bool = False,
    ) -> dict[str, Any]:
        """Delete published IG media via official DELETE /{ig-media-id}.

        DESTRUCTIVE and irreversible. Requires confirm_irreversible=true AND an
        explicit account label. Requires Meta permission instagram_manage_contents.
        VelvetOS HQ must not call this for routine CTA cleanup — prefer human gate.
        Profile/caption edits are NOT available — see graph_mutation_matrix.
        """

        def _impl() -> dict[str, Any]:
            if not confirm_irreversible:
                return {
                    "ok": False,
                    "supported": True,
                    "error": "Refusing delete: set confirm_irreversible=true explicitly.",
                    "error_class": "validation",
                    "mutated": False,
                    "matrix": MATRIX["delete_media"],
                }
            if not account:
                return {
                    "ok": False,
                    "supported": True,
                    "error": "Refusing delete: account label is required (no silent default).",
                    "error_class": "validation",
                    "mutated": False,
                }
            client, acct = auth.client_for(account)
            mid = V.validate_graph_id(media_id, field="media_id")
            data = client.delete(mid)
            return {
                "ok": True,
                "supported": True,
                "account": acct.label,
                "media_id": mid,
                "deleted": True,
                "graph": data,
                "warning": "irreversible",
                "matrix": MATRIX["delete_media"],
            }

        return _guard(
            "delete_media",
            {
                "media_id": media_id,
                "account": account,
                "confirm_irreversible": confirm_irreversible,
            },
            _impl,
        )
