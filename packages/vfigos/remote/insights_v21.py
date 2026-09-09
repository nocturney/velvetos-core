"""Graph API v21+ Insights helpers for VelvetOS Instagram MCP.

Upstream adelaidasofia-instagram-mcp 0.1.2 defaults still request deprecated
`impressions` and send mixed metric_type cohorts in one call. Production Graph
(v21.0) rejects that. This module:

1. Corrects default account metrics for v21+
2. Splits time_series vs total_value metric cohorts into separate Graph calls
3. Merges results into one MCP response
4. Surfaces Meta errors cleanly without inventing metrics
5. Picks media-insight defaults by media_product_type / media_type without inventing

Applied by `apply_insights_patch(mcp)` from the Cloud Run HTTP entry.
"""

from __future__ import annotations

from typing import Any, Callable

# ChatGPT-verified failure: default included impressions (invalid on live Graph).
# Useful snapshot without requiring callers to know metric_type.
DEFAULT_ACCOUNT_METRICS_V21 = "reach,follower_count,profile_views,total_interactions"

# Deprecated / renamed aliases — never invent values; remap only when Meta documents it.
ACCOUNT_METRIC_ALIASES = {
    "impressions": "views",  # Meta replacement for impressions (total_value)
    "saved": "saves",
}

# Metrics that MUST use metric_type=total_value on Graph v21+ (account insights).
# Sourced from Meta IG User Insights docs + live (#100) errors from production.
TOTAL_VALUE_ONLY_ACCOUNT = frozenset(
    {
        "profile_views",
        "total_interactions",
        "accounts_engaged",
        "likes",
        "comments",
        "shares",
        "saves",
        "replies",
        "views",
        "website_clicks",
        "profile_links_taps",
        "follows_and_unfollows",
        "content_views",
        "reposts",
        "quotes",
        "threads_likes",
        "threads_replies",
        "threads_views",
        "threads_clicks",
        "threads_reposts",
        "threads_followers",
        "threads_follower_demographics",
        "engaged_audience_demographics",
        "reached_audience_demographics",
        "follower_demographics",
    }
)

# Metrics that support time_series (or historically work without metric_type=total_value).
TIME_SERIES_ACCOUNT = frozenset(
    {
        "reach",
        "follower_count",
        "online_followers",
    }
)

# Media insight defaults by product — only documented common sets; callers may override.
# Do not invent platform-specific undocumented metrics.
DEFAULT_MEDIA_METRICS_FEED = "reach,likes,comments,saves,shares,total_interactions,views"
DEFAULT_MEDIA_METRICS_REELS = "reach,likes,comments,shares,saved,total_interactions,views"
DEFAULT_MEDIA_METRICS_STORY = "reach,replies,shares,navigation,profile_visits"


def normalize_account_metrics(metrics: str | None) -> list[str]:
    raw = (metrics or DEFAULT_ACCOUNT_METRICS_V21).strip()
    names: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        name = part.strip().lower()
        if not name:
            continue
        name = ACCOUNT_METRIC_ALIASES.get(name, name)
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def partition_account_metrics(names: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Return (time_series_metrics, total_value_metrics, unknown_metrics).

    `reach` supports both metric types; we keep it in the time_series cohort so a
    mixed ChatGPT-style request (reach + follower_count + profile_views +
    total_interactions) becomes two legal Graph calls.
    """
    ts: list[str] = []
    tv: list[str] = []
    unknown: list[str] = []
    for name in names:
        if name in TOTAL_VALUE_ONLY_ACCOUNT:
            tv.append(name)
        elif name in TIME_SERIES_ACCOUNT:
            ts.append(name)
        else:
            # Refuse undocumented metrics rather than guessing metric_type.
            unknown.append(name)
    return ts, tv, unknown


def media_default_metrics(media: dict[str, Any] | None) -> str:
    """Pick a conservative default metric string from media type fields."""
    if not media:
        return DEFAULT_MEDIA_METRICS_FEED
    product = (media.get("media_product_type") or "").upper()
    mtype = (media.get("media_type") or "").upper()
    if product == "REELS" or mtype == "REELS" or (mtype == "VIDEO" and product == "REELS"):
        return DEFAULT_MEDIA_METRICS_REELS
    if product == "STORY" or mtype == "STORY":
        return DEFAULT_MEDIA_METRICS_STORY
    # IMAGE / CAROUSEL_ALBUM / FEED
    return DEFAULT_MEDIA_METRICS_FEED


def fetch_account_insights(
    client: Any,
    ig_user_id: str,
    *,
    metrics: str | None,
    period: str,
    get_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute split Graph insights requests and merge.

    `get_fn` is injectable for unit tests (defaults to client.get).
    """
    getter = get_fn or client.get
    names = normalize_account_metrics(metrics)
    ts_names, tv_names, unknown = partition_account_metrics(names)
    if unknown:
        return {
            "ok": False,
            "error": (
                f"Unsupported or undocumented account insight metrics for Graph v21+: "
                f"{','.join(unknown)}. Pass only Meta-documented metrics."
            ),
            "error_class": "invalid_param",
            "unsupported_metrics": unknown,
        }

    merged: list[dict[str, Any]] = []
    requests_made: list[dict[str, Any]] = []
    partial_errors: list[dict[str, Any]] = []

    def _one(metric_list: list[str], metric_type: str | None) -> None:
        if not metric_list:
            return
        params: dict[str, Any] = {
            "metric": ",".join(metric_list),
            "period": period,
        }
        if metric_type:
            params["metric_type"] = metric_type
        req_meta = {"metrics": list(metric_list), "metric_type": metric_type or "time_series_default"}
        try:
            data = getter(f"{ig_user_id}/insights", **params)
            rows = data.get("data") or []
            merged.extend(rows)
            req_meta["ok"] = True
            req_meta["count"] = len(rows)
        except Exception as exc:  # noqa: BLE001 — surface Meta error; keep other cohort
            req_meta["ok"] = False
            req_meta["error"] = str(exc)
            partial_errors.append(req_meta)
            # follower_count / online_followers often fail under Meta's >=100 floor.
            # Keep other cohort results when possible.
            if not merged and len(metric_list) == len(names):
                raise
        requests_made.append(req_meta)

    # Time-series cohort first (reach, follower_count), then total_value cohort.
    _one(ts_names, None)
    _one(tv_names, "total_value")

    if not merged and partial_errors:
        # All cohorts failed — return the first Meta error cleanly.
        err = partial_errors[0].get("error") or "insights request failed"
        return {
            "ok": False,
            "error": err,
            "error_class": "invalid_param",
            "requests": requests_made,
        }

    out: dict[str, Any] = {
        "ok": True,
        "period": period,
        "metrics_requested": names,
        "insights": merged,
        "requests": requests_made,
        "graph_compat": "v21+",
    }
    if partial_errors:
        out["partial"] = True
        out["partial_errors"] = partial_errors
    return out


def apply_insights_patch(mcp: Any) -> None:
    """Replace get_account_insights / get_media_insights on the FastMCP instance."""
    from instagram_mcp import auth
    from instagram_mcp import validators as V
    from instagram_mcp.server import _guard

    # Remove upstream broken tools (same names — ChatGPT keeps calling them).
    for name in ("get_account_insights", "get_media_insights"):
        removed = False
        try:
            mcp.local_provider.remove_tool(name)
            removed = True
        except Exception:
            pass
        if not removed:
            try:
                mcp.remove_tool(name)
            except Exception:
                pass

    @mcp.tool()
    def get_account_insights(
        account: str | None = None,
        *,
        metrics: str | None = None,
        period: str = "day",
    ) -> dict[str, Any]:
        """Account-level analytics compatible with Instagram Graph API v21+.

        Default metrics: reach, follower_count, profile_views, total_interactions.
        Automatically splits time_series vs total_value cohorts (Meta requires
        metric_type=total_value for profile_views / total_interactions / views / …).
        Deprecated `impressions` is remapped to `views`. Does not invent metrics.
        follower_count may fail below Meta's ~100-follower privacy floor — returned
        as a clean partial/error without fabricating counts.
        """

        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            per = V.validate_enum(
                period, {"day", "week", "days_28", "lifetime"}, field="period", default="day"
            )
            result = fetch_account_insights(
                client, acct.ig_user_id, metrics=metrics, period=per
            )
            result["account"] = acct.label
            return result

        return _guard(
            "get_account_insights",
            {"account": account, "metrics": metrics, "period": period},
            _impl,
        )

    @mcp.tool()
    def get_media_insights(
        media_id: str,
        account: str | None = None,
        *,
        metrics: str | None = None,
    ) -> dict[str, Any]:
        """Per-media analytics. Defaults depend on IMAGE / CAROUSEL / REELS / STORY.

        Does not invent metric availability — Meta errors surface cleanly when a
        metric is invalid for that media type. Override `metrics` when needed.
        """

        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            mid = V.validate_graph_id(media_id, field="media_id")
            media_meta: dict[str, Any] | None = None
            try:
                media_meta = client.get(
                    mid, fields="id,media_type,media_product_type"
                )
            except Exception:
                media_meta = None
            m = metrics or media_default_metrics(media_meta)
            # Remap saved↔saves alias for feed callers.
            parts = []
            for part in m.split(","):
                p = part.strip()
                if not p:
                    continue
                parts.append(ACCOUNT_METRIC_ALIASES.get(p.lower(), p))
            m = ",".join(parts)
            data = client.get(f"{mid}/insights", metric=m)
            return {
                "ok": True,
                "account": acct.label,
                "media_id": mid,
                "media_type": (media_meta or {}).get("media_type"),
                "media_product_type": (media_meta or {}).get("media_product_type"),
                "metrics_requested": m.split(","),
                "insights": data.get("data", []),
            }

        return _guard(
            "get_media_insights",
            {"media_id": media_id, "account": account, "metrics": metrics},
            _impl,
        )
