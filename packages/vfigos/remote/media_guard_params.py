"""Ensure media-bearing publish tools pass COMPLETE args into ``_guard``.

Upstream adelaidasofia-instagram-mcp omits security-relevant fields from the
``_guard`` summary for some writes (e.g. carousel ``image_urls``, reel
``cover_url``). Without those fields the delivery-approval gate cannot bind
immutable media bytes for the exact Graph mutation.

This overlay re-registers the affected tools so ``ig_server._guard`` always
receives the full public mutation args (plus delivery_approval binding fields).
"""

from __future__ import annotations

from typing import Any, Callable


def _remove_tool(mcp: Any, name: str) -> None:
    remove: Callable[..., Any] | None = None
    provider = getattr(mcp, "local_provider", None)
    if provider is not None and hasattr(provider, "remove_tool"):
        remove = provider.remove_tool
    elif hasattr(mcp, "remove_tool"):
        remove = mcp.remove_tool
    if remove is None:
        return
    try:
        remove(name)
    except Exception:
        pass


def apply_complete_media_guard_params(mcp: Any) -> None:
    """Replace publish_image/video/reel/carousel with full-arg ``_guard`` summaries."""
    import instagram_mcp.server as ig_server
    from instagram_mcp import auth, validators as V

    for name in ("publish_image", "publish_video", "publish_reel", "publish_carousel"):
        _remove_tool(mcp, name)

    @mcp.tool()
    def publish_image(
        image_url: str,
        caption: str | None = None,
        account: str | None = None,
        delivery_approval: dict | str | None = None,
        content_id: str | None = None,
        package_sha256: str | None = None,
    ) -> dict[str, Any]:
        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            url = V.validate_public_https_url(image_url, field="image_url")
            cap = V.validate_caption(caption)
            container = client.post(f"{acct.ig_user_id}/media", image_url=url, caption=cap)
            cid = container.get("id")
            return {"account": acct.label, **ig_server._publish_container(client, acct.ig_user_id, cid)}

        return ig_server._guard(
            "publish_image",
            {
                "image_url": image_url,
                "caption": V.truncate(caption or ""),
                "account": account,
                "delivery_approval": delivery_approval,
                "content_id": content_id,
                "package_sha256": package_sha256,
            },
            _impl,
        )

    @mcp.tool()
    def publish_video(
        video_url: str,
        caption: str | None = None,
        account: str | None = None,
        delivery_approval: dict | str | None = None,
        content_id: str | None = None,
        package_sha256: str | None = None,
    ) -> dict[str, Any]:
        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            url = V.validate_public_https_url(video_url, field="video_url")
            cap = V.validate_caption(caption)
            container = client.post(
                f"{acct.ig_user_id}/media", media_type="VIDEO", video_url=url, caption=cap
            )
            cid = container.get("id")
            ig_server._wait_container_ready(client, cid)
            return {"account": acct.label, **ig_server._publish_container(client, acct.ig_user_id, cid)}

        return ig_server._guard(
            "publish_video",
            {
                "video_url": video_url,
                "caption": V.truncate(caption or ""),
                "account": account,
                "delivery_approval": delivery_approval,
                "content_id": content_id,
                "package_sha256": package_sha256,
            },
            _impl,
        )

    @mcp.tool()
    def publish_reel(
        video_url: str,
        caption: str | None = None,
        account: str | None = None,
        *,
        share_to_feed: bool = True,
        cover_url: str | None = None,
        delivery_approval: dict | str | None = None,
        content_id: str | None = None,
        package_sha256: str | None = None,
    ) -> dict[str, Any]:
        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            url = V.validate_public_https_url(video_url, field="video_url")
            cap = V.validate_caption(caption)
            cover = V.validate_public_https_url(cover_url, field="cover_url") if cover_url else None
            container = client.post(
                f"{acct.ig_user_id}/media",
                media_type="REELS",
                video_url=url,
                caption=cap,
                share_to_feed=share_to_feed,
                cover_url=cover,
            )
            cid = container.get("id")
            ig_server._wait_container_ready(client, cid)
            return {"account": acct.label, **ig_server._publish_container(client, acct.ig_user_id, cid)}

        return ig_server._guard(
            "publish_reel",
            {
                "video_url": video_url,
                "caption": V.truncate(caption or ""),
                "account": account,
                "share_to_feed": share_to_feed,
                "cover_url": cover_url,
                "delivery_approval": delivery_approval,
                "content_id": content_id,
                "package_sha256": package_sha256,
            },
            _impl,
        )

    @mcp.tool()
    def publish_carousel(
        image_urls: list[str],
        caption: str | None = None,
        account: str | None = None,
        delivery_approval: dict | str | None = None,
        content_id: str | None = None,
        package_sha256: str | None = None,
    ) -> dict[str, Any]:
        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            if not isinstance(image_urls, list) or not (2 <= len(image_urls) <= 10):
                raise V.ValidationError("image_urls must be a list of 2-10 public https URLs")
            urls = [V.validate_public_https_url(u, field="image_url") for u in image_urls]
            cap = V.validate_caption(caption)
            child_ids: list[str] = []
            for u in urls:
                child = client.post(f"{acct.ig_user_id}/media", image_url=u, is_carousel_item=True)
                child_ids.append(child.get("id"))
            parent = client.post(
                f"{acct.ig_user_id}/media",
                media_type="CAROUSEL",
                children=",".join(child_ids),
                caption=cap,
            )
            cid = parent.get("id")
            return {
                "account": acct.label,
                "child_count": len(child_ids),
                **ig_server._publish_container(client, acct.ig_user_id, cid),
            }

        return ig_server._guard(
            "publish_carousel",
            {
                "image_urls": list(image_urls or []),
                "caption": V.truncate(caption or ""),
                "account": account,
                "delivery_approval": delivery_approval,
                "content_id": content_id,
                "package_sha256": package_sha256,
            },
            _impl,
        )
