"""Patch Instagram MCP publish_story so image Stories wait for FINISHED.

Upstream adelaidasofia/instagram-mcp polls `_wait_container_ready` for video
Stories only. Image Stories call media_publish immediately, which frequently
returns Graph error 9007 ("Media ID is not available") while Meta is still
fetching/processing the public image_url.

Applied by `apply_story_publish_patch(mcp)` from the Cloud Run HTTP entry —
same overlay style as insights_v21. Does not invent a second publisher.
"""

from __future__ import annotations

from typing import Any, Callable


def apply_story_publish_patch(mcp: Any) -> None:
    """Replace publish_story so both image and video Stories poll to FINISHED."""
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
            remove("publish_story")
        except Exception:
            pass

    @mcp.tool()
    def publish_story(
        image_url: str | None = None,
        video_url: str | None = None,
        account: str | None = None,
    ) -> dict[str, Any]:
        """Publish a Story (image OR video). Exactly one of image_url / video_url, PUBLIC https.

        VelvetOS overlay: always poll container status_code=FINISHED before media_publish
        (image Stories included). Upstream image path skipped that wait and hit 9007.
        """

        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            if bool(image_url) == bool(video_url):
                raise V.ValidationError("pass exactly one of image_url or video_url")
            if image_url:
                url = V.validate_public_https_url(image_url, field="image_url")
                container = client.post(
                    f"{acct.ig_user_id}/media", media_type="STORIES", image_url=url
                )
            else:
                url = V.validate_public_https_url(video_url, field="video_url")
                container = client.post(
                    f"{acct.ig_user_id}/media", media_type="STORIES", video_url=url
                )
            cid = container.get("id")
            ig_server._wait_container_ready(client, cid)
            return {"account": acct.label, **ig_server._publish_container(client, acct.ig_user_id, cid)}

        return ig_server._guard(
            "publish_story",
            {"image_url": image_url, "video_url": video_url, "account": account},
            _impl,
        )
