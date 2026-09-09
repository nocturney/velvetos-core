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

STRICT: no browser automation / private API. Unsupported ops return
`unsupported_by_official_graph` and do not mutate.
"""

from __future__ import annotations

from typing import Any

MATRIX = {
    "update_biography": {
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "limitations": "IG User Updating operation is not supported by Instagram Graph API.",
    },
    "update_website": {
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "limitations": "IG User Updating operation is not supported by Instagram Graph API.",
    },
    "update_name": {
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "limitations": "IG User Updating operation is not supported by Instagram Graph API.",
    },
    "update_media_caption": {
        "status": "unsupported_by_official_graph",
        "endpoint": "POST /{ig-media-id}",
        "permissions": ["instagram_basic"],
        "allowed_fields": ["comment_enabled"],
        "limitations": (
            "Official Updating on IG Media only enables/disables comments. "
            "caption parameter is ignored. Feed posts and Reels cannot have captions "
            "edited via Graph."
        ),
    },
    "delete_media": {
        "status": "supported",
        "endpoint": "DELETE /{ig-media-id}",
        "permissions": ["instagram_manage_contents"],
        "allowed_fields": [],
        "limitations": (
            "Destructive/irreversible. Deletes posts, carousels, reels, stories. "
            "Cannot delete individual carousel children. Requires App Review scope "
            "instagram_manage_contents. Not exercised live by VelvetOS HQ automation."
        ),
    },
    "archive_media": {
        "status": "unsupported_by_official_graph",
        "endpoint": None,
        "permissions": [],
        "allowed_fields": [],
        "limitations": "No official archive endpoint distinct from delete.",
    },
}


def _unsupported(op: str) -> dict[str, Any]:
    row = MATRIX[op]
    return {
        "ok": False,
        "status": "unsupported_by_official_graph",
        "operation": op,
        "matrix": row,
        "mutated": False,
        "note": "Use Instagram app / human edit. MCP will not browser-automate or scrape.",
    }


def apply_mutation_tools(mcp: Any) -> None:
    from instagram_mcp import auth
    from instagram_mcp import validators as V
    from instagram_mcp.server import _guard

    @mcp.tool()
    def graph_mutation_matrix() -> dict[str, Any]:
        """Return the official Meta Graph support matrix for profile/caption mutations.

        Read-only. Use before attempting update_profile / update_media_caption.
        """
        return {"ok": True, "matrix": MATRIX, "source": "Meta Instagram Graph API docs 2026-09"}

    @mcp.tool()
    def update_profile(
        account: str | None = None,
        *,
        biography: str | None = None,
        website: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Attempt profile field updates — officially unsupported by Instagram Graph.

        Always returns unsupported_by_official_graph. Does not mutate. Does not
        call private APIs. For a compliant bio draft see PROFILE-DESIRED.json.
        """
        _ = (account, biography, website, name)
        fields = [f for f, v in (("biography", biography), ("website", website), ("name", name)) if v is not None]
        if not fields:
            return {
                "ok": False,
                "status": "unsupported_by_official_graph",
                "error": "No fields provided; and Graph does not support profile updates anyway.",
                "mutated": False,
            }
        # Prefer the most specific op code when a single field is requested.
        if fields == ["biography"]:
            return _unsupported("update_biography")
        if fields == ["website"]:
            return _unsupported("update_website")
        if fields == ["name"]:
            return _unsupported("update_name")
        out = _unsupported("update_biography")
        out["requested_fields"] = fields
        out["also"] = ["update_website", "update_name"]
        return out

    @mcp.tool()
    def update_media_caption(
        media_id: str,
        caption: str,
        account: str | None = None,
    ) -> dict[str, Any]:
        """Attempt caption edit on published media — officially unsupported by Graph.

        Always returns unsupported_by_official_graph. Does not mutate live posts.
        """
        _ = (media_id, caption, account)
        return _unsupported("update_media_caption")

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
        """

        def _impl() -> dict[str, Any]:
            if not confirm_irreversible:
                return {
                    "ok": False,
                    "error": "Refusing delete: set confirm_irreversible=true explicitly.",
                    "error_class": "validation",
                    "mutated": False,
                    "matrix": MATRIX["delete_media"],
                }
            if not account:
                return {
                    "ok": False,
                    "error": "Refusing delete: account label is required (no silent default).",
                    "error_class": "validation",
                    "mutated": False,
                }
            client, acct = auth.client_for(account)
            mid = V.validate_graph_id(media_id, field="media_id")
            data = client.delete(mid)
            return {
                "ok": True,
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
