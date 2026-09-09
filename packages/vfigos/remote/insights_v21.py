"""Graph API v21+ Insights helpers for VelvetOS Instagram MCP.

Upstream adelaidasofia-instagram-mcp 0.1.2 defaults still request deprecated
`impressions` and send mixed metric_type cohorts in one call. Production Graph
(v21.0) rejects that. This module:

1. Corrects default account metrics for v21+
2. Splits time_series vs total_value metric cohorts into separate Graph calls
3. Partitions account metrics by official period compatibility (no fabricated
   28-day values from daily series)
4. Picks media-insight defaults by media_type / media_product_type
5. Keeps media `saved` vs account `saves` distinct (Graph names differ)
6. Merges results into one MCP response and surfaces Meta / compatibility
   errors as structured partials without inventing metrics

Applied by `apply_insights_patch(mcp)` from the Cloud Run HTTP entry.
"""

from __future__ import annotations

from typing import Any, Callable

# ChatGPT-verified failure: default included impressions (invalid on live Graph).
# Useful snapshot without requiring callers to know metric_type.
DEFAULT_ACCOUNT_METRICS_V21 = "reach,follower_count,profile_views,total_interactions"

# Account-only aliases — never invent values; remap only when Meta documents it.
# IMPORTANT: media insights use `saved`, not `saves`. Do not apply this map to media.
ACCOUNT_METRIC_ALIASES = {
    "impressions": "views",  # Meta replacement for impressions (total_value)
    "saved": "saves",
}

# Media-only aliases. Live Graph #100 for Reel 17873372004572489 lists `saved`
# (not `saves`) among legal media metrics. Account callers often say `saves`.
MEDIA_METRIC_ALIASES = {
    "saves": "saved",
    "impressions": "views",
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

# Official Meta IG User Insights period matrix (docs table) + live Graph v21 probes
# on @velvets_cloud (2026-09-09). Do NOT invent days_28 by multiplying day values.
# `reach` still accepts week/days_28 as time_series on live Graph; most total_value
# interaction metrics are day-only per Meta's table.
ACCOUNT_METRIC_PERIODS: dict[str, frozenset[str]] = {
    "reach": frozenset({"day", "week", "days_28"}),
    "follower_count": frozenset({"day"}),
    "online_followers": frozenset({"lifetime"}),
    "profile_views": frozenset({"day"}),
    "likes": frozenset({"day"}),
    "comments": frozenset({"day"}),
    "shares": frozenset({"day"}),
    "saves": frozenset({"day"}),
    "total_interactions": frozenset({"day"}),
    "views": frozenset({"day"}),
    "accounts_engaged": frozenset({"day"}),
    "replies": frozenset({"day"}),
    "website_clicks": frozenset({"day"}),
    "profile_links_taps": frozenset({"day"}),
    "follows_and_unfollows": frozenset({"day"}),
    "content_views": frozenset({"day"}),
    "reposts": frozenset({"day"}),
    "quotes": frozenset({"day"}),
    "engaged_audience_demographics": frozenset({"lifetime"}),
    "reached_audience_demographics": frozenset({"lifetime"}),
    "follower_demographics": frozenset({"lifetime"}),
}

# Media insight defaults by type — live-verified common FEED/REELS set.
# Include `saved` (media Graph name). Never default to account `saves`.
_FEED_LIKE = "reach,likes,comments,shares,saved,total_interactions,views"
DEFAULT_MEDIA_METRICS_IMAGE = _FEED_LIKE
DEFAULT_MEDIA_METRICS_CAROUSEL = _FEED_LIKE
DEFAULT_MEDIA_METRICS_VIDEO = _FEED_LIKE
DEFAULT_MEDIA_METRICS_REELS = _FEED_LIKE
DEFAULT_MEDIA_METRICS_STORY = "reach,replies,shares,navigation,profile_visits"
# Conservative fallback when media meta is missing (ChatGPT still needs a shot).
DEFAULT_MEDIA_METRICS_UNKNOWN = "reach,likes,comments,shares,total_interactions,views"


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


def normalize_media_metrics(metrics: str) -> list[str]:
    """Normalize media metric names — keep `saved`, remap account `saves` → `saved`."""
    names: list[str] = []
    seen: set[str] = set()
    for part in metrics.split(","):
        name = part.strip().lower()
        if not name:
            continue
        name = MEDIA_METRIC_ALIASES.get(name, name)
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def periods_for_account_metric(name: str) -> frozenset[str]:
    if name in ACCOUNT_METRIC_PERIODS:
        return ACCOUNT_METRIC_PERIODS[name]
    if name in TOTAL_VALUE_ONLY_ACCOUNT:
        return frozenset({"day"})
    if name in TIME_SERIES_ACCOUNT:
        return frozenset({"day"})
    return frozenset()


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


def partition_account_metrics_by_period(
    names: list[str], period: str
) -> tuple[list[str], list[dict[str, Any]]]:
    """Split metrics into those legal for `period` vs structured incompatibles.

    Does not rewrite period or fabricate multi-day totals from day series.
    """
    compatible: list[str] = []
    incompat: list[dict[str, Any]] = []
    for name in names:
        supported = periods_for_account_metric(name)
        if period in supported:
            compatible.append(name)
            continue
        incompat.append(
            {
                "metrics": [name],
                "ok": False,
                "error_class": "period_incompatible",
                "period_requested": period,
                "periods_supported": sorted(supported),
                "error": (
                    f"The following periods ({period}) are incompatible with "
                    f"the metric ({name})"
                ),
            }
        )
    return compatible, incompat


def media_default_metrics(media: dict[str, Any] | None) -> str:
    """Pick a conservative default metric string from media type fields."""
    if not media:
        return DEFAULT_MEDIA_METRICS_UNKNOWN
    product = (media.get("media_product_type") or "").upper()
    mtype = (media.get("media_type") or "").upper()
    if product == "STORY" or mtype == "STORY":
        return DEFAULT_MEDIA_METRICS_STORY
    if product == "REELS" or mtype == "REELS":
        return DEFAULT_MEDIA_METRICS_REELS
    if mtype == "CAROUSEL_ALBUM":
        return DEFAULT_MEDIA_METRICS_CAROUSEL
    if mtype == "IMAGE":
        return DEFAULT_MEDIA_METRICS_IMAGE
    if mtype == "VIDEO":
        # Feed VIDEO vs REELS — product REELS already handled above.
        return DEFAULT_MEDIA_METRICS_VIDEO
    return DEFAULT_MEDIA_METRICS_UNKNOWN


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

    # Period gate before Graph — ChatGPT days_28 + follower_count/profile_views
    # must not fail the whole snapshot when reach (etc.) is still legal.
    compatible, period_partials = partition_account_metrics_by_period(names, period)
    ts_names = [n for n in ts_names if n in compatible]
    tv_names = [n for n in tv_names if n in compatible]

    merged: list[dict[str, Any]] = []
    requests_made: list[dict[str, Any]] = []
    partial_errors: list[dict[str, Any]] = list(period_partials)

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
            if not merged and not period_partials and len(metric_list) == len(names):
                raise
        requests_made.append(req_meta)

    # Time-series cohort first (reach, follower_count), then total_value cohort.
    _one(ts_names, None)
    _one(tv_names, "total_value")

    if not merged and not compatible:
        # Everything was period-incompatible — structured failure, no fake totals.
        return {
            "ok": False,
            "error": (
                f"No requested account insight metrics are compatible with "
                f"period={period}."
            ),
            "error_class": "period_incompatible",
            "period": period,
            "metrics_requested": names,
            "partial_errors": partial_errors,
            "requests": requests_made,
            "graph_compat": "v21+",
        }

    if not merged and partial_errors:
        # All Graph cohorts failed — return the first Meta error cleanly.
        err = next(
            (
                p.get("error")
                for p in partial_errors
                if p.get("error") and p.get("error_class") != "period_incompatible"
            ),
            None,
        ) or partial_errors[0].get("error") or "insights request failed"
        return {
            "ok": False,
            "error": err,
            "error_class": "invalid_param",
            "requests": requests_made,
            "partial_errors": partial_errors,
        }

    out: dict[str, Any] = {
        "ok": True,
        "period": period,
        "metrics_requested": names,
        "metrics_fetched": compatible,
        "insights": merged,
        "requests": requests_made,
        "graph_compat": "v21+",
    }
    if partial_errors:
        out["partial"] = True
        out["partial_errors"] = partial_errors
    return out


def fetch_media_insights(
    client: Any,
    media_id: str,
    *,
    metrics: str | None = None,
    get_fn: Callable[..., dict[str, Any]] | None = None,
    account_label: str | None = None,
) -> dict[str, Any]:
    """Fetch per-media insights with type-aware defaults (injectable for tests)."""
    getter = get_fn or client.get
    media_meta: dict[str, Any] | None = None
    try:
        media_meta = getter(media_id, fields="id,media_type,media_product_type")
    except Exception:
        media_meta = None
    raw = metrics or media_default_metrics(media_meta)
    names = normalize_media_metrics(raw)
    metric_str = ",".join(names)
    try:
        data = getter(f"{media_id}/insights", metric=metric_str)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
            "error_class": "invalid_param",
            "account": account_label,
            "media_id": media_id,
            "media_type": (media_meta or {}).get("media_type"),
            "media_product_type": (media_meta or {}).get("media_product_type"),
            "metrics_requested": names,
        }
    return {
        "ok": True,
        "account": account_label,
        "media_id": media_id,
        "media_type": (media_meta or {}).get("media_type"),
        "media_product_type": (media_meta or {}).get("media_product_type"),
        "metrics_requested": names,
        "insights": data.get("data", []),
    }


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
        Also partitions by period compatibility — e.g. follower_count and
        profile_views are day-only; days_28 returns reach (etc.) plus structured
        partial errors for incompatible metrics (no fabricated 28-day totals).
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

        Media Graph metric for saves is `saved` (not account `saves`). Override
        `metrics` when needed. Does not invent metric availability — Meta errors
        surface cleanly when a metric is invalid for that media type.
        """

        def _impl() -> dict[str, Any]:
            client, acct = auth.client_for(account)
            mid = V.validate_graph_id(media_id, field="media_id")
            return fetch_media_insights(
                client, mid, metrics=metrics, account_label=acct.label
            )

        return _guard(
            "get_media_insights",
            {"media_id": media_id, "account": account, "metrics": metrics},
            _impl,
        )
