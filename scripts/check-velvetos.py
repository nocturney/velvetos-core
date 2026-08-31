#!/usr/bin/env python3
"""Validate VelvetOS kernel + tenants. Keeps velvet-factory compat. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "velvetos"
ACTIVE = PACK / "ACTIVE.json"
SCHEMA = PACK / "schema" / "tenant.schema.json"
TENANTS = PACK / "tenants"
EXAMPLES = TENANTS / "_examples"
MANIFEST = ROOT / "packages" / "manifest.json"
DESK = ROOT / ".cursor" / "vf-desk.json"
STUDIO = ROOT / "constitution" / "STUDIO.md"
AGENTS = ROOT / "AGENTS.md"
KERNEL = PACK / "KERNEL.md"
REQUIRED_FILES = (
    "KERNEL.md",
    "PIPELINE.md",
    "CHANNELS.md",
    "LOCK.md",
    "EMBED.md",
    "SKILL.md",
    "ORIGIN.md",
    "ACTIVE.json",
    "schema/tenant.schema.json",
)
CANONICAL_STAGE_IDS = ["lead", "talk", "offer", "fulfill", "close"]
SEAT_IDS = ["lead", "studio", "growth", "ops", "production"]
COMPLIANCE_TRUE = (
    "noInventedPrices",
    "noInventedInsights",
    "noAutoDm",
    "noBoostWithoutLead",
    "hqSendViaTools",
)


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_tenant(data: dict, *, allow_example: bool) -> None:
    tid = data.get("id")
    if not tid:
        fail("tenant missing id")
    status = data.get("status")
    if allow_example:
        if status != "example":
            fail(f"{tid}: examples must have status=example, got {status}")
    elif status not in {"active", "ready", "archived"}:
        fail(f"{tid}: bad status {status}")

    for key in (
        "displayName",
        "vertical",
        "locale",
        "timezone",
        "pipeline",
        "fulfillment",
        "production",
        "channels",
        "cta",
        "close",
        "compliance",
        "seats",
    ):
        if key not in data:
            fail(f"{tid}: missing {key}")

    stages = data["pipeline"].get("stages") or []
    if len(stages) != 5:
        fail(f"{tid}: pipeline must have 5 stages")
    ids = [s.get("id") for s in stages]
    if ids != CANONICAL_STAGE_IDS:
        fail(f"{tid}: stage ids must be {CANONICAL_STAGE_IDS}, got {ids}")
    for s in stages:
        if not s.get("label"):
            fail(f"{tid}: stage {s.get('id')} missing label")

    if data["fulfillment"].get("mode") not in {
        "pickup",
        "appointment",
        "document",
        "hybrid",
    }:
        fail(f"{tid}: bad fulfillment.mode")
    if data["production"].get("kind") not in {
        "print",
        "appointment",
        "document",
        "custom",
    }:
        fail(f"{tid}: bad production.kind")

    compliance = data["compliance"]
    for key in COMPLIANCE_TRUE:
        if compliance.get(key) is not True:
            fail(f"{tid}: compliance.{key} must be true")

    seats = data["seats"]
    if len(seats) != 5:
        fail(f"{tid}: must have exactly 5 seats")
    seat_ids = [s.get("id") for s in seats]
    if seat_ids != SEAT_IDS:
        fail(f"{tid}: seat ids must be {SEAT_IDS}")

    ig = data["channels"].get("instagram")
    if not isinstance(ig, list):
        fail(f"{tid}: channels.instagram must be a list")
    primaries = [c for c in ig if c.get("primary") is True]
    if ig and len(primaries) != 1:
        fail(f"{tid}: exactly one primary Instagram account required when list non-empty")
    for c in ig:
        for need in ("id", "handle", "purpose", "primary"):
            if need not in c:
                fail(f"{tid}: ig channel missing {need}")

    forbidden = data["cta"].get("forbidden") or []
    if not any("DM" in x or "dm" in x for x in forbidden):
        fail(f"{tid}: cta.forbidden must block DM-style CTAs")


def check_vf_compat(active: dict, desk: dict, studio_text: str) -> None:
    """While velvet-factory is active, desk + STUDIO facts must match the tenant."""
    if active.get("id") != "velvet-factory":
        return
    studio = desk.get("studio") or {}
    if studio.get("name") != "Velvet Factory":
        fail("desk.studio.name must stay Velvet Factory while tenant active")
    if studio.get("instagram") != "@velvets_cloud":
        fail("desk.studio.instagram must stay @velvets_cloud while VF active")
    if studio.get("whatsapp") != "050-2517000":
        fail("desk.studio.whatsapp must stay 050-2517000 while VF active")
    if studio.get("pickupOnly") is not True:
        fail("desk.studio.pickupOnly must be true while VF active")
    pipeline = desk.get("pipeline") or []
    labels = [s["label"] for s in active["pipeline"]["stages"]]
    if pipeline != labels:
        fail(f"desk.pipeline {pipeline} != tenant labels {labels}")
    ig = active["channels"]["instagram"]
    if not ig or ig[0].get("handle") != "@velvets_cloud":
        fail("VF tenant primary IG must be @velvets_cloud")
    if active["fulfillment"].get("mode") != "pickup":
        fail("VF tenant fulfillment.mode must be pickup")
    if active["fulfillment"].get("nationalShipping") is not False:
        fail("VF tenant must set nationalShipping false")
    if active["production"].get("kind") != "print":
        fail("VF tenant production.kind must be print")
    if "050-2517000" not in studio_text:
        fail("STUDIO.md must still list WhatsApp 050-2517000")
    if "@velvets_cloud" not in studio_text and "velvets_cloud" not in studio_text:
        fail("STUDIO.md must still list @velvets_cloud")
    if "שדרות" not in studio_text:
        fail("STUDIO.md must still list שדרות")


def main() -> None:
    for rel in REQUIRED_FILES:
        path = PACK / rel
        if not path.is_file():
            fail(f"missing packages/velvetos/{rel}")

    if not MANIFEST.is_file():
        fail("missing packages/manifest.json")
    if not DESK.is_file():
        fail("missing .cursor/vf-desk.json")
    if not STUDIO.is_file():
        fail("missing constitution/STUDIO.md")
    if not AGENTS.is_file():
        fail("missing AGENTS.md")

    manifest = load(MANIFEST)
    pack_names = {p["name"] for p in manifest.get("packs", [])}
    if "velvetos" not in pack_names:
        fail("velvetos missing from packages/manifest.json")

    agents = AGENTS.read_text(encoding="utf-8")
    if "VelvetOS" not in agents:
        fail("AGENTS.md must mention VelvetOS")
    if "velvet-factory" not in agents and "Velvet Factory" not in agents:
        fail("AGENTS.md must still mention Velvet Factory / velvet-factory")

    if "VelvetOS" not in KERNEL.read_text(encoding="utf-8"):
        fail("KERNEL.md must name VelvetOS")

    # schema file present (lightweight structural check — no jsonschema dep)
    schema = load(SCHEMA)
    if schema.get("title") != "VelvetOS tenant profile":
        fail("tenant.schema.json title mismatch")

    active_meta = load(ACTIVE)
    if active_meta.get("product") != "VelvetOS":
        fail("ACTIVE.json product must be VelvetOS")
    tid = active_meta.get("activeTenant")
    if not tid:
        fail("ACTIVE.json missing activeTenant")
    active_path = TENANTS / f"{tid}.json"
    if not active_path.is_file():
        fail(f"active tenant file missing: tenants/{tid}.json")
    if tid.startswith("_") or "example" in tid:
        fail("active tenant must not be an example id")

    active = load(active_path)
    if active.get("id") != tid:
        fail(f"tenant id {active.get('id')} != ACTIVE {tid}")
    if active.get("status") != "active":
        fail(f"active tenant {tid} must have status=active")
    validate_tenant(active, allow_example=False)

    # non-example tenants
    for path in sorted(TENANTS.glob("*.json")):
        data = load(path)
        if data.get("id") != path.stem:
            fail(f"{path.name}: id must match filename")
        if data.get("status") == "example":
            fail(f"{path.name}: example status not allowed outside _examples/")
        validate_tenant(data, allow_example=False)

    # examples
    if not EXAMPLES.is_dir():
        fail("missing tenants/_examples/")
    example_ids = set()
    for path in sorted(EXAMPLES.glob("*.json")):
        data = load(path)
        if data.get("id") != path.stem:
            fail(f"example {path.name}: id must match filename")
        validate_tenant(data, allow_example=True)
        example_ids.add(data["id"])
        if data["id"] == tid:
            fail("example tenant id collides with ACTIVE")
    for need in ("nails-tattoos", "psychiatrist-legal"):
        if need not in example_ids:
            fail(f"missing example tenant {need}")

    nails = load(EXAMPLES / "nails-tattoos.json")
    if len(nails["channels"]["instagram"]) < 2:
        fail("nails-tattoos example must demonstrate multi-IG")
    psych = load(EXAMPLES / "psychiatrist-legal.json")
    if psych["fulfillment"]["mode"] != "document":
        fail("psychiatrist-legal must use document fulfillment")
    if psych["production"]["kind"] != "document":
        fail("psychiatrist-legal must use document production")

    desk = load(DESK)
    studio_text = STUDIO.read_text(encoding="utf-8")
    check_vf_compat(active, desk, studio_text)

    # default must remain velvet-factory unless explicitly changed in ACTIVE
    # (compat gate above already enforces desk sync when it is)
    if tid == "velvet-factory" and "velvetos" not in (
        desk.get("seats", [{}])[0].get("packs") or []
    ):
        # soft: lead seat should list velvetos for discoverability
        lead = next((s for s in desk.get("seats", []) if s.get("id") == "lead"), None)
        if not lead or "velvetos" not in (lead.get("packs") or []):
            fail("desk lead seat must include pack velvetos")

    skill = ROOT / ".cursor" / "skills" / "vf-velvetos" / "SKILL.md"
    if not skill.is_file():
        fail("missing .cursor/skills/vf-velvetos/SKILL.md")
    docs = ROOT / "docs" / "VELVETOS.md"
    if not docs.is_file():
        fail("missing docs/VELVETOS.md")
    tenant_doc = ROOT / "constitution" / "TENANT.md"
    if not tenant_doc.is_file():
        fail("missing constitution/TENANT.md")

    print(
        f"OK velvetos active={tid} tenants={len(list(TENANTS.glob('*.json')))} "
        f"examples={len(example_ids)}"
    )


if __name__ == "__main__":
    main()
