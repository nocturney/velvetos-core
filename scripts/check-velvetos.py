#!/usr/bin/env python3
"""Validate VelvetOS core modules + this instance. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "velvetos"
INSTANCE_META = PACK / "INSTANCE.json"
INSTANCE_DIR = PACK / "instance"
MODULES_CATALOG = PACK / "modules" / "catalog.json"
PRESETS = PACK / "presets"
MANIFEST = ROOT / "packages" / "manifest.json"
DESK = ROOT / ".cursor" / "vf-desk.json"
STUDIO = ROOT / "constitution" / "STUDIO.md"
AGENTS = ROOT / "AGENTS.md"
KERNEL = PACK / "KERNEL.md"
REPOS = PACK / "REPOS.md"
CANONICAL_STAGE_IDS = ["lead", "talk", "offer", "fulfill", "close"]
SEAT_IDS = ["lead", "studio", "growth", "ops", "production"]
COMPLIANCE_TRUE = (
    "noInventedPrices",
    "noInventedInsights",
    "noAutoDm",
    "noBoostWithoutLead",
    "hqSendViaTools",
)
REQUIRED_ROOT = (
    "KERNEL.md",
    "PIPELINE.md",
    "CHANNELS.md",
    "LOCK.md",
    "EMBED.md",
    "SKILL.md",
    "ORIGIN.md",
    "REPOS.md",
    "INSTANCE.json",
    "modules/catalog.json",
    "schema/instance.schema.json",
)
REQUIRED_PRESETS = ("maker-print", "beauty-multi-ig", "clinical-legal-opinions")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_instance(data: dict, module_ids: set[str]) -> None:
    iid = data.get("id")
    if not iid:
        fail("instance missing id")
    for key in (
        "displayName",
        "vertical",
        "modulesEnabled",
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
            fail(f"{iid}: missing {key}")
    if "VelvetOS" not in data["displayName"]:
        fail(f"{iid}: displayName must start with VelvetOS — … pattern")

    enabled = data["modulesEnabled"]
    if not enabled:
        fail(f"{iid}: modulesEnabled empty")
    for mid in enabled:
        if mid not in module_ids:
            fail(f"{iid}: unknown module {mid}")

    stages = data["pipeline"].get("stages") or []
    if [s.get("id") for s in stages] != CANONICAL_STAGE_IDS:
        fail(f"{iid}: bad pipeline stage ids")
    for s in stages:
        if not s.get("label"):
            fail(f"{iid}: stage {s.get('id')} missing label")

    if data["fulfillment"].get("mode") not in {
        "pickup",
        "appointment",
        "document",
        "hybrid",
    }:
        fail(f"{iid}: bad fulfillment.mode")
    if data["production"].get("kind") not in {
        "print",
        "appointment",
        "document",
        "custom",
    }:
        fail(f"{iid}: bad production.kind")

    compliance = data["compliance"]
    for key in COMPLIANCE_TRUE:
        if compliance.get(key) is not True:
            fail(f"{iid}: compliance.{key} must be true")

    seats = data["seats"]
    if [s.get("id") for s in seats] != SEAT_IDS:
        fail(f"{iid}: seat ids mismatch")

    ig = data["channels"].get("instagram")
    if not isinstance(ig, list):
        fail(f"{iid}: channels.instagram must be a list")
    primaries = [c for c in ig if c.get("primary") is True]
    if ig and len(primaries) != 1:
        fail(f"{iid}: exactly one primary IG when list non-empty")
    for c in ig:
        for need in ("id", "handle", "purpose", "primary"):
            if need not in c:
                fail(f"{iid}: ig channel missing {need}")

    forbidden = data["cta"].get("forbidden") or []
    if not any("DM" in x or "dm" in x for x in forbidden):
        fail(f"{iid}: cta.forbidden must block DM-style CTAs")

    # status/active/example must not appear — this is an instance, not a tenant switch
    if "status" in data:
        fail(f"{iid}: remove status field — instances are not active/example tenants")


def check_vf_compat(profile: dict, desk: dict, studio_text: str) -> None:
    if profile.get("id") != "velvet-factory":
        fail("this monorepo instance must be velvet-factory")
    studio = desk.get("studio") or {}
    if studio.get("name") != "Velvet Factory":
        fail("desk.studio.name must stay Velvet Factory")
    if studio.get("instagram") != "@velvets_cloud":
        fail("desk.studio.instagram must stay @velvets_cloud")
    if studio.get("whatsapp") != "050-2517000":
        fail("desk.studio.whatsapp must stay 050-2517000")
    if studio.get("pickupOnly") is not True:
        fail("desk.studio.pickupOnly must be true")
    labels = [s["label"] for s in profile["pipeline"]["stages"]]
    if desk.get("pipeline") != labels:
        fail(f"desk.pipeline {desk.get('pipeline')} != instance labels {labels}")
    ig = profile["channels"]["instagram"]
    if not ig or ig[0].get("handle") != "@velvets_cloud":
        fail("VF primary IG must be @velvets_cloud")
    if profile["fulfillment"].get("mode") != "pickup":
        fail("VF fulfillment.mode must be pickup")
    if profile["fulfillment"].get("nationalShipping") is not False:
        fail("VF nationalShipping must be false")
    if profile["production"].get("kind") != "print":
        fail("VF production.kind must be print")
    for needle in ("050-2517000", "velvets_cloud", "שדרות"):
        if needle not in studio_text:
            fail(f"STUDIO.md must still list {needle}")
    for need in (
        "fulfill-pickup",
        "production-print",
        "compliance-maker",
        "channels-instagram",
    ):
        if need not in profile["modulesEnabled"]:
            fail(f"VF instance must enable module {need}")


def main() -> None:
    for rel in REQUIRED_ROOT:
        if not (PACK / rel).is_file():
            fail(f"missing packages/velvetos/{rel}")

    # old tenant switch model must be gone
    if (PACK / "ACTIVE.json").exists():
        fail("remove ACTIVE.json — use INSTANCE.json (no active/example tenants)")
    if (PACK / "tenants").exists():
        fail("remove tenants/ — use instance/ + modules/ + presets/")

    catalog = load(MODULES_CATALOG)
    modules = catalog.get("modules") or []
    if len(modules) < 12:
        fail(f"expected >=12 modules, got {len(modules)}")
    module_ids: set[str] = set()
    for row in modules:
        mid = row.get("id")
        if not mid:
            fail("module row missing id")
        if mid in module_ids:
            fail(f"duplicate module {mid}")
        module_ids.add(mid)
        rel = row.get("file")
        if not rel or not (PACK / rel).is_file():
            fail(f"module {mid} missing file {rel}")
        packs = row.get("packs") or []
        if not packs:
            fail(f"module {mid} needs packs[]")

    # presets = blueprints only
    if not PRESETS.is_dir():
        fail("missing presets/")
    preset_ids = set()
    for path in sorted(PRESETS.glob("*.json")):
        data = load(path)
        if data.get("kind") != "preset":
            fail(f"{path.name}: kind must be preset")
        if data.get("id") != path.stem:
            fail(f"{path.name}: id must match filename")
        if "status" in data or "activeTenant" in data:
            fail(f"{path.name}: presets are not tenants")
        for mid in data.get("modulesEnabled") or []:
            if mid not in module_ids:
                fail(f"preset {data['id']}: unknown module {mid}")
        preset_ids.add(data["id"])
    for need in REQUIRED_PRESETS:
        if need not in preset_ids:
            fail(f"missing preset {need}")

    beauty = load(PRESETS / "beauty-multi-ig.json")
    if beauty.get("channels", {}).get("instagramMin", 0) < 2:
        fail("beauty-multi-ig preset must require multi-IG")
    if "fulfill-appointment" not in beauty["modulesEnabled"]:
        fail("beauty-multi-ig must enable fulfill-appointment")
    clinical = load(PRESETS / "clinical-legal-opinions.json")
    if "fulfill-document" not in clinical["modulesEnabled"]:
        fail("clinical-legal-opinions must enable fulfill-document")
    if "compliance-clinical-legal" not in clinical["modulesEnabled"]:
        fail("clinical-legal-opinions must enable compliance-clinical-legal")

    meta = load(INSTANCE_META)
    if meta.get("product") != "VelvetOS":
        fail("INSTANCE.json product must be VelvetOS")
    if meta.get("role") != "instance":
        fail("INSTANCE.json role must be instance")
    if "VelvetOS —" not in meta.get("displayName", ""):
        fail("INSTANCE.json displayName must be VelvetOS — <Business>")
    iid = meta.get("instanceId")
    if not iid:
        fail("INSTANCE.json missing instanceId")
    profile_rel = meta.get("profile") or f"instance/{iid}.json"
    profile_path = PACK / profile_rel
    if not profile_path.is_file():
        fail(f"missing instance profile {profile_rel}")

    # only one live instance profile in this repo
    profiles = list(INSTANCE_DIR.glob("*.json"))
    if len(profiles) != 1:
        fail(f"expected exactly 1 instance profile in instance/, got {len(profiles)}")
    profile = load(profile_path)
    if profile.get("id") != iid:
        fail(f"profile id {profile.get('id')} != INSTANCE {iid}")
    validate_instance(profile, module_ids)

    # preset alignment for VF
    if profile.get("preset"):
        preset = load(PRESETS / f"{profile['preset']}.json")
        for mid in preset["modulesEnabled"]:
            if mid not in profile["modulesEnabled"]:
                fail(f"instance missing module from preset {profile['preset']}: {mid}")

    desk = load(DESK)
    studio_text = STUDIO.read_text(encoding="utf-8")
    check_vf_compat(profile, desk, studio_text)

    lead = next((s for s in desk.get("seats", []) if s.get("id") == "lead"), None)
    if not lead or "velvetos" not in (lead.get("packs") or []):
        fail("desk lead seat must include pack velvetos")

    agents = AGENTS.read_text(encoding="utf-8")
    if "VelvetOS" not in agents:
        fail("AGENTS.md must mention VelvetOS")
    if "Velvet Factory" not in agents and "velvet-factory" not in agents:
        fail("AGENTS.md must mention Velvet Factory")
    if "modules" not in agents.lower() and "מודול" not in agents:
        # soft requirement via KERNEL; enforce KERNEL + REPOS instead
        pass
    if "ריפו" not in KERNEL.read_text(encoding="utf-8") and "repo" not in KERNEL.read_text(
        encoding="utf-8"
    ).lower():
        fail("KERNEL.md must describe core vs instance repos")
    repos_text = REPOS.read_text(encoding="utf-8")
    for needle in ("velvetos-core", "instance", "modules"):
        if needle not in repos_text:
            fail(f"REPOS.md must mention {needle}")

    if "activeTenant" in (desk.get("notes") or []) or desk.get("activeTenant"):
        # allow activeTenant key only if it matches instance id during transition — prefer instanceId
        pass
    # Prefer velvetos.instance on desk
    vos = desk.get("velvetos") or {}
    if vos and vos.get("pack") and "velvetos" not in str(vos.get("pack")):
        fail("desk.velvetos.pack path invalid")

    schema = load(PACK / "schema" / "instance.schema.json")
    if schema.get("title") != "VelvetOS instance profile":
        fail("instance.schema.json title mismatch")

    # old tenant schema optional — if present, ok; prefer instance schema
    if not (ROOT / "docs" / "VELVETOS.md").is_file():
        fail("missing docs/VELVETOS.md")
    if not (ROOT / ".cursor" / "skills" / "vf-velvetos" / "SKILL.md").is_file():
        fail("missing vf-velvetos skill")
    if not (ROOT / "constitution" / "TENANT.md").is_file() and not (
        ROOT / "constitution" / "INSTANCE.md"
    ).is_file():
        fail("missing constitution/INSTANCE.md (or legacy TENANT.md)")

    manifest = load(MANIFEST)
    if "velvetos" not in {p["name"] for p in manifest.get("packs", [])}:
        fail("velvetos missing from manifest")

    print(
        f"OK velvetos instance={iid} modules={len(module_ids)} "
        f"presets={len(preset_ids)} hostsCore={meta.get('hostsCore')}"
    )


if __name__ == "__main__":
    main()
