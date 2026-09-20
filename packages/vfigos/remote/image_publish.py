"""Patch Instagram MCP publish_image so feed images wait for FINISHED.

Upstream adelaidasofia/instagram-mcp publishes image containers immediately after
creation. Meta can still be fetching/processing the public image_url at that point,
which returns Graph error 9007 ("Media ID is not available").

Applied by apply_image_publish_patch(mcp) from the Cloud Run HTTP entry.
The existing VelvetOS delivery-approval guard remains the write boundary.
"""

from __future__ import annotations

from typing import Any, Callable


def apply_image_publish_patch(mcp: Any) -> None:
    """Replace publish_image so image containers poll to FINISHED before media_publish."""
    import instagram_mcp.server as ig_server
    from instagram_mcp import auth, validators as V

    remove: Callable[..., Any] | None = None
    provider = getattr(mcp, "local_provider", None)
    if provider is not None and hasattr(provider, "remove_tool"):
        remove = provider.remove_tool
    elif hasattr(mcp, "remove_tool"):
        remove = mcp.remove_tool
    if remove is not None:
        try:
            remove("publish_image")
        except Exception:
            pass

    @mcp.tool()
    def publish_image(
        image_url: str,
        caption: str | None = None,
        account: str | None = None,
        delivery_approval: dict | str | None = None,
        content_id: str | None = None,
        package_sha256: str | None = None,
    ) -> dict[str, Any]:
        """Publish a single image to the feed after its container is ready.

        Requires signed velvet.delivery_approval.v1 receipt before Graph publish.
        """

        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            url = V.validate_public_https_url(image_url, field="image_url")
            cap = V.validate_caption(caption)
            container = client.post(
                f"{acct.ig_user_id}/media",
                image_url=url,
                caption=cap,
            )
            cid = container.get("id")
            ig_server._wait_container_ready(client, cid)
            return {
                "account": acct.label,
                **ig_server._publish_container(client, acct.ig_user_id, cid),
            }

        return ig_server._guard(
            "publish_image",
            {
                "image_url": image_url,
                "caption": caption,
                "account": account,
                "delivery_approval": delivery_approval,
                "content_id": content_id,
                "package_sha256": package_sha256,
            },
            _impl,
        )
