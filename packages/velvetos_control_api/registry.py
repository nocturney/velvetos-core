"""Contribution registry — modules extend the projection without a giant switch."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from velvetos_control_api.schema import now_iso

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "CONTRIBUTIONS.json"


@dataclass
class ProjectContext:
    """Read-only context passed to contributions. No network side effects required."""

    root: Path
    generated_at: str = field(default_factory=now_iso)
    extras: dict[str, Any] = field(default_factory=dict)


class Contribution(Protocol):
    """A domain contribution to the Control API projection."""

    id: str
    domain: str

    def project(self, ctx: ProjectContext) -> dict[str, Any]:
        """Return a collection envelope or domain slice for the snapshot."""
        ...

    def search(self, query: str, ctx: ProjectContext) -> list[dict[str, Any]]:
        """Federated search hits for this domain (empty if not searchable)."""
        ...


def _default_registry() -> list[dict[str, Any]]:
    return [
        {
            "id": "control_plane",
            "module": "velvetos_control_api.contributions.control_plane",
            "class": "ControlPlaneContribution",
            "domains": ["system", "health", "modules", "flags"],
        },
        {
            "id": "capabilities",
            "module": "velvetos_control_api.contributions.capabilities",
            "class": "CapabilitiesContribution",
            "domains": ["capabilities"],
        },
        {
            "id": "integrations",
            "module": "velvetos_control_api.contributions.integrations",
            "class": "IntegrationsContribution",
            "domains": ["integrations"],
        },
        {
            "id": "attention",
            "module": "velvetos_control_api.contributions.attention",
            "class": "AttentionContribution",
            "domains": ["attention"],
        },
        {
            "id": "activity",
            "module": "velvetos_control_api.contributions.activity",
            "class": "ActivityContribution",
            "domains": ["activity"],
        },
        {
            "id": "jobs",
            "module": "velvetos_control_api.contributions.jobs",
            "class": "JobsContribution",
            "domains": ["jobs"],
        },
        {
            "id": "unavailable_domains",
            "module": "velvetos_control_api.contributions.unavailable",
            "class": "UnavailableDomainsContribution",
            "domains": ["production", "content", "files", "agents", "models"],
        },
    ]


def load_registry() -> list[dict[str, Any]]:
    if REGISTRY_PATH.is_file():
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        entries = data.get("contributions") or []
        if entries:
            return entries
    return _default_registry()


def load_contributions() -> list[Any]:
    loaded: list[Any] = []
    for entry in load_registry():
        mod = importlib.import_module(entry["module"])
        cls = getattr(mod, entry["class"])
        loaded.append(cls())
    return loaded


def repo_root() -> Path:
    # packages/velvetos_control_api → packages → repo
    return HERE.parent.parent
