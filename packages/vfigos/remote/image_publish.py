"""VelvetOS feed-image publish patch with provider-ready polling + safe diagnostics.

Upstream adelaidasofia/instagram-mcp can publish an image container before Meta has
finished fetching/processing image_url. This patch waits for FINISHED before
media_publish and preserves safe provider error metadata for OpenPost recovery.

The existing VelvetOS delivery-approval middleware remains the write boundary.
No token, receipt signature, raw provider response, or credential-bearing URL is
returned by this tool.
"""

from __future__ import annotations

import time
from typing import Any, Callable


_SAFE_ERROR_ATTRS: tuple[tuple[str, str], ...] = (
    ("code", "provider_code"),
    ("subcode", "provider_subcode"),
    ("http_status", "http_status"),
    ("type", "provider_type"),
)


def _safe_graph_error(exc: BaseException, *, stage: str) -> dict[str, Any]:
    """Return a bounded, sanitized provider failure safe for the MCP seam."""
    from instagram_mcp import audit

    error_class = audit.classify_error(exc)
    out: dict[str, Any] = {
        "ok": False,
        "error": audit.sanitize_error(str(exc)),
        "error_class": error_class,
        "stage": stage,
    }
    for attr, key in _SAFE_ERROR_ATTRS:
        value = getattr(exc, attr, None)
        if isinstance(value, (int, str)) and not isinstance(value, bool):
            out[key] = value

    # Before media_publish there is no possible live post. During media_publish,
    # timeout/network means the provider outcome is ambiguous and must be
    # reconciled before another write. Explicit provider responses are rejected.
    if stage != "media_publish":
        out["write_outcome"] = "not_sent"
        out["retry_safety"] = "safe_with_fresh_approval"
    elif error_class in {"timeout", "network"}:
        out["write_outcome"] = "unknown"
        out["retry_safety"] = "reconcile_only"
    else:
        out["write_outcome"] = "rejected"
        out["retry_safety"] = "safe_with_fresh_approval"
    return out


def apply_image_publish_patch(mcp: Any) -> None:
    """Replace publish_image so image containers poll to FINISHED before publish."""
    import instagram_mcp.server as ig_server
    from instagram_mcp import audit, auth, validators as V

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
        started = time.perf_counter()
        safe_input = audit.sanitize_payload(
            {
                "image_url": image_url,
                "caption": caption,
                "account": account,
                "delivery_approval": delivery_approval,
                "content_id": content_id,
                "package_sha256": package_sha256,
            }
        )
        stage = "create_container"
        try:
            client, acct = auth.client_for(account)
            url = V.validate_public_https_url(image_url, field="image_url")
            cap = V.validate_caption(caption)
            container = client.post(
                f"{acct.ig_user_id}/media",
                image_url=url,
                caption=cap,
            )
            cid = container.get("id")
            stage = "container_processing"
            ig_server._wait_container_ready(client, cid)
            stage = "media_publish"
            result = {
                "account": acct.label,
                **ig_server._publish_container(client, acct.ig_user_id, cid),
            }
            audit.record(
                "publish_image",
                execution_time_ms=int((time.perf_counter() - started) * 1000),
                io={"input": safe_input, "output": ig_server._summarize(result)},
            )
            return result
        except Exception as exc:  # noqa: BLE001 - MCP boundary shapes all failures
            failure = _safe_graph_error(exc, stage=stage)
            audit.record(
                "publish_image",
                execution_time_ms=int((time.perf_counter() - started) * 1000),
                io={
                    "input": safe_input,
                    "output": {
                        "ok": False,
                        "error": failure["error"],
                        "stage": stage,
                    },
                },
                error_class=failure["error_class"],
                extra={
                    k: failure[k]
                    for k in (
                        "stage",
                        "provider_code",
                        "provider_subcode",
                        "http_status",
                        "provider_type",
                        "write_outcome",
                        "retry_safety",
                    )
                    if k in failure
                },
            )
            return failure
