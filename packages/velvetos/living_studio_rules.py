#!/usr/bin/env python3
"""Read-only Living Studio business-rule projection from canonical instance config.

No business-instance default. Callers from a Core checkout must select an
instance explicitly or via VELVETOS_INSTANCE_ID. The returned legacy-shaped
businessRules object is a projection only; canonical values stay in the
instance profile and generic safety semantics stay in Core code/policy.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from instance_resolver import InstanceResolutionError, resolve_surface  # noqa: E402


class LivingStudioRuleResolutionError(RuntimeError):
    pass


def _load_profile(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise LivingStudioRuleResolutionError(f"instance profile missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise LivingStudioRuleResolutionError(f"invalid instance profile {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LivingStudioRuleResolutionError("instance profile must be an object")
    return value


def _public_cta_label(channel: object) -> str:
    value = str(channel or "").strip()
    if value == "instagram-message":
        return "Instagram message"
    if not value:
        raise LivingStudioRuleResolutionError("instance profile cta.channel missing")
    return value


def effective_business_rules(
    repository_root: str | Path,
    *,
    instance_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    try:
        profile_path = resolve_surface(
            root,
            "profile",
            instance_id=instance_id,
            env=os.environ if env is None else env,
        )
    except InstanceResolutionError as exc:
        raise LivingStudioRuleResolutionError(str(exc)) from exc

    profile = _load_profile(profile_path)
    fulfillment = profile.get("fulfillment") or {}
    cta = profile.get("cta") or {}
    compliance = profile.get("compliance") or {}
    mcp_bind = profile.get("mcpBind") or {}
    whatsapp = mcp_bind.get("whatsapp") or {}

    if fulfillment.get("mode") != "pickup":
        pickup_only: str | None = None
    else:
        location = str(profile.get("where") or "").strip()
        if not location:
            raise LivingStudioRuleResolutionError("pickup instance requires profile.where")
        pickup_only = location

    nationwide = fulfillment.get("nationalShipping")
    if not isinstance(nationwide, bool):
        raise LivingStudioRuleResolutionError("fulfillment.nationalShipping must be boolean")

    no_invented_prices = compliance.get("noInventedPrices")
    no_invented_insights = compliance.get("noInventedInsights")
    if not isinstance(no_invented_prices, bool) or not isinstance(no_invented_insights, bool):
        raise LivingStudioRuleResolutionError(
            "compliance.noInventedPrices/noInventedInsights must be boolean"
        )

    whatsapp_send = whatsapp.get("send")
    if not isinstance(whatsapp_send, bool):
        raise LivingStudioRuleResolutionError("mcpBind.whatsapp.send must be boolean")
    customer_send = "tool" if whatsapp_send else "human"

    return {
        "pickupOnly": pickup_only,
        "nationwideShipping": nationwide,
        "publicCTA": _public_cta_label(cta.get("channel")),
        "customerWhatsAppSend": customer_send,
        "inventSaleILS": not no_invented_prices,
        "inventInsights": not no_invented_insights,
        # Generic safety invariant: destructive autonomy is never enabled by an instance value.
        "destructiveAutonomy": False,
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--instance-id")
    args = parser.parse_args()
    try:
        rules = effective_business_rules(args.root, instance_id=args.instance_id)
    except LivingStudioRuleResolutionError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2
    print(json.dumps(rules, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
