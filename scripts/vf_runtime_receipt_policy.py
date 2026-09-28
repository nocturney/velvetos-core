#!/usr/bin/env python3
"""Age policy for runtime receipts in packages/vfharness/state/runtime/.

Only age-based expiry is context-dependent. Missing, malformed, mismatched,
future-dated or non-healthy receipts are failures in every context.

Strict (expired receipt = FAIL):
  * VF_RUNTIME_RECEIPTS_STRICT=1 (explicit override, any context);
  * GitHub Actions push, schedule, workflow_dispatch and any other event
    that is not pull_request.
Soft (expired receipt = WARN, exit unaffected):
  * GitHub Actions pull_request;
  * local runs (no GITHUB_ACTIONS / GITHUB_EVENT_NAME).
"""
from __future__ import annotations

import os
from collections.abc import Mapping

OVERRIDE_ENV = "VF_RUNTIME_RECEIPTS_STRICT"
STRICT_HINT = "strict on push/schedule/workflow_dispatch or with VF_RUNTIME_RECEIPTS_STRICT=1"


def receipt_age_policy(env: Mapping[str, str] | None = None) -> tuple[bool, str]:
    """Return (strict, context) for age-based receipt expiry."""
    env = os.environ if env is None else env
    if env.get(OVERRIDE_ENV, "").strip() == "1":
        return True, f"{OVERRIDE_ENV}=1"
    event = env.get("GITHUB_EVENT_NAME", "").strip()
    in_actions = env.get("GITHUB_ACTIONS", "").strip().lower() == "true"
    if in_actions or event:
        if event == "pull_request":
            return False, "pull_request CI"
        return True, f"GitHub event {event or 'unknown'}"
    return False, "local run"


def warn_line(stale: list[str], context: str) -> str:
    return (
        "WARN runtime receipts expired (age-only, warning in " + context + "; " + STRICT_HINT + "): "
        + "; ".join(stale)
    )
