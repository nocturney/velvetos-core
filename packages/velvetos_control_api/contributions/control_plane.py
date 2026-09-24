"""Control-plane / system projection — not a second SoT."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from velvetos_control_api.schema import now_iso, provenance


class ControlPlaneContribution:
    id = "control_plane"
    domain = "system"

    def project(self, ctx: Any) -> dict[str, Any]:
        root: Path = ctx.root
        plane_path = root / "office" / "control-plane.json"
        policy_path = root / "office" / "control" / "POLICY.md"
        generated_at = now_iso()

        if not plane_path.is_file():
            return {
                "system": {
                    "state": "unavailable",
                    "reason": "missing office/control-plane.json",
                    "provenance": provenance(
                        source="office/control-plane.json",
                        verified_at=None,
                        freshness="unknown",
                    ),
                },
                "modules": [],
                "flags": {},
                "health": [
                    {
                        "id": "control-plane",
                        "status": "unavailable",
                        "detail": "control-plane.json missing",
                        "provenance": provenance(source="office/control-plane.json"),
                    }
                ],
            }

        plane = json.loads(plane_path.read_text(encoding="utf-8"))
        modules = []
        # Living studio + autonomy as module descriptors from plane metadata
        ls = plane.get("livingStudio") or {}
        if ls:
            modules.append(
                {
                    "id": "living-studio",
                    "label": "Living Studio",
                    "status": "projection",
                    "cli": ls.get("cli"),
                    "layer": ls.get("layer"),
                    "provenance": provenance(
                        source="office/control-plane.json#livingStudio",
                        verified_at=plane.get("updatedAt"),
                        freshness="fresh",
                        authority="projection",
                    ),
                }
            )
        auto = plane.get("autonomyComposition") or {}
        if auto:
            modules.append(
                {
                    "id": "autonomy",
                    "label": "Autonomy composition",
                    "status": "projection",
                    "cli": auto.get("cli"),
                    "provenance": provenance(
                        source="office/control-plane.json#autonomyComposition",
                        verified_at=plane.get("updatedAt"),
                        freshness="fresh",
                        authority="projection",
                    ),
                }
            )
        modules.append(
            {
                "id": "office-control-plane",
                "label": plane.get("title") or "Office Control Plane",
                "status": "canonical-map",
                "cli": plane.get("cli"),
                "sensor": plane.get("sensor"),
                "provenance": provenance(
                    source="office/control-plane.json",
                    verified_at=plane.get("updatedAt"),
                    freshness="fresh",
                    authority="canonical",
                ),
            }
        )

        flags = {
            "dontBotherChristian": bool(plane.get("dontBotherChristian")),
            "locks": list(plane.get("locks") or []),
            "policyPresent": policy_path.is_file(),
            "sourcesOfTruthCount": len(plane.get("sourcesOfTruth") or {}),
        }

        # Health of the Control Plane map itself (not all VelvetOS integrations)
        health_items = [
            {
                "id": "control-plane-map",
                "status": "ok",
                "detail": f"sources={flags['sourcesOfTruthCount']}",
                "provenance": provenance(
                    source="office/control-plane.json",
                    verified_at=plane.get("updatedAt"),
                    freshness="fresh",
                    authority="canonical",
                ),
            }
        ]
        if not policy_path.is_file():
            health_items.append(
                {
                    "id": "risk-policy",
                    "status": "degraded",
                    "detail": "POLICY.md missing",
                    "provenance": provenance(source="office/control/POLICY.md"),
                }
            )
        else:
            health_items.append(
                {
                    "id": "risk-policy",
                    "status": "ok",
                    "detail": "Don't Bother Christian policy present",
                    "provenance": provenance(
                        source="office/control/POLICY.md",
                        freshness="fresh",
                        authority="canonical",
                    ),
                }
            )

        # Soft read of watchdog without mutating — import carefully
        watchdog_health = _watchdog_health(root)
        if watchdog_health:
            health_items.append(watchdog_health)

        return {
            "system": {
                "state": "ready",
                "name": plane.get("name"),
                "title": plane.get("title"),
                "updatedAt": plane.get("updatedAt"),
                "controlDir": plane.get("controlDir"),
                "provenance": provenance(
                    source="office/control-plane.json",
                    verified_at=plane.get("updatedAt") or generated_at,
                    freshness="fresh",
                    authority="canonical",
                ),
            },
            "modules": modules,
            "flags": flags,
            "health": health_items,
        }

    def search(self, query: str, ctx: Any) -> list[dict[str, Any]]:
        q = query.lower().strip()
        if not q:
            return []
        hits: list[dict[str, Any]] = []
        data = self.project(ctx)
        for mod in data.get("modules") or []:
            blob = f"{mod.get('id','')} {mod.get('label','')}".lower()
            if q in blob:
                hits.append(
                    {
                        "id": mod.get("id"),
                        "type": "module",
                        "module": "control-plane",
                        "title": mod.get("label") or mod.get("id"),
                        "source": "office/control-plane.json",
                        "status": mod.get("status"),
                        "destination": f"/modules/{mod.get('id')}",
                    }
                )
        return hits


def _watchdog_health(root: Path) -> dict[str, Any] | None:
    """Best-effort non-mutating health signal from control plane issues."""
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        import vf_control_plane as cp  # noqa: WPS433
    except Exception:
        return {
            "id": "control-plane-watchdog",
            "status": "unknown",
            "detail": "vf_control_plane import failed",
            "provenance": provenance(source="scripts/vf_control_plane.py"),
        }
    try:
        issues = cp.watchdog_issues()
        red = [i for i in issues if i.get("level") == "red"]
        status = "degraded" if red else "ok"
        return {
            "id": "control-plane-watchdog",
            "status": status,
            "detail": f"issues={len(issues)} red={len(red)}",
            "provenance": provenance(
                source="scripts/vf_control_plane.py#watchdog_issues",
                verified_at=now_iso(),
                freshness="live",
                authority="projection",
            ),
        }
    except Exception as exc:
        return {
            "id": "control-plane-watchdog",
            "status": "unknown",
            "detail": f"watchdog_issues failed: {type(exc).__name__}",
            "provenance": provenance(source="scripts/vf_control_plane.py"),
        }
