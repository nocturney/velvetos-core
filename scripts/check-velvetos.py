#!/usr/bin/env python3
"""Validate VelvetOS Core + instance scaffolds. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "velvetos"
CORE = PACK / "CORE.json"
MODULES_CATALOG = PACK / "modules" / "catalog.json"
PRESETS = PACK / "presets"
SAMPLES = PACK / "samples"
INSTANCES = ROOT / "instances"
MANIFEST = ROOT / "packages" / "manifest.json"
DESK = ROOT / ".cursor" / "vf-desk.json"
STUDIO = ROOT / "constitution" / "STUDIO.md"
AGENTS = ROOT / "AGENTS.md"
KERNEL = PACK / "KERNEL.md"
REPOS = PACK / "REPOS.md"
PUBLISH = ROOT / "scripts" / "publish-instance.sh"
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
    "LAYERS.md",
    "ADR-THREE-LAYERS.md",
    "CORE.json",
    "modules/catalog.json",
    "schema/instance.schema.json",
    "schema/events.catalog.json",
    "schema/event-envelope.schema.json",
)
REQUIRED_PRESETS = ("maker-print", "beauty-multi-ig", "clinical-legal-opinions")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_profile(data: dict, module_ids: set[str], *, label: str) -> None:
    iid = data.get("id")
    if not iid:
        fail(f"{label}: missing id")
    for key in (
        "displayName",
        "vertical",
        "modulesEnabled",
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
            fail(f"{label}: missing {key}")
    if "VelvetOS" not in data["displayName"]:
        fail(f"{label}: displayName must include VelvetOS")
    for mid in data["modulesEnabled"]:
        if mid not in module_ids:
            fail(f"{label}: unknown module {mid}")
    stages = data["pipeline"].get("stages") or []
    if [s.get("id") for s in stages] != CANONICAL_STAGE_IDS:
        fail(f"{label}: bad pipeline ids")
    if [s.get("id") for s in data["seats"]] != SEAT_IDS:
        fail(f"{label}: bad seats")
    for key in COMPLIANCE_TRUE:
        if data["compliance"].get(key) is not True:
            fail(f"{label}: compliance.{key} must be true")
    ig = data["channels"].get("instagram")
    if not isinstance(ig, list):
        fail(f"{label}: instagram must be list")
    if ig and sum(1 for c in ig if c.get("primary") is True) != 1:
        fail(f"{label}: exactly one primary IG when non-empty")
    forbidden = data["cta"].get("forbidden") or []
    if not any("DM" in x or "dm" in x for x in forbidden):
        fail(f"{label}: cta.forbidden must block DM")
    if data.get("status") in {"active", "example"}:
        fail(f"{label}: remove active/example status — use core/sample/instance roles")


def check_reference_vf(profile: dict, desk: dict, studio_text: str) -> None:
    if profile.get("id") != "velvet-factory":
        fail("core sample must be velvet-factory")
    studio = desk.get("studio") or {}
    if studio.get("instagram") != "@velvets_cloud":
        fail("desk.studio.instagram must stay @velvets_cloud during compat")
    if studio.get("whatsapp") != "050-2517000":
        fail("desk.studio.whatsapp must stay 050-2517000 during compat")
    labels = [s["label"] for s in profile["pipeline"]["stages"]]
    if desk.get("pipeline") != labels:
        fail("desk.pipeline mismatch vs sample")
    for needle in ("050-2517000", "velvets_cloud", "שדרות"):
        if needle not in studio_text:
            fail(f"STUDIO.md must still list {needle} (compat reference)")
    for need in ("fulfill-pickup", "production-print", "compliance-maker"):
        if need not in profile["modulesEnabled"]:
            fail(f"VF sample must enable {need}")
    bind = profile.get("mcpBind") or {}
    wa = bind.get("whatsapp") or {}
    if wa.get("send") is not False:
        fail("VF mcpBind.whatsapp.send must be false")
    hub = bind.get("studiomcphub") or {}
    if "print_ready" not in (hub.get("skip") or []):
        fail("VF mcpBind.studiomcphub must skip print_ready")
    ig = bind.get("instagram") or {}
    if not ig.get("enabled"):
        fail("VF mcpBind.instagram must be enabled (ig-mcp mapped)")
    if ig.get("dm") is not False:
        fail("VF mcpBind.instagram.dm must be false")
    if "CONNECT-IG.md" not in (ig.get("connect") or ""):
        fail("VF mcpBind.instagram.connect must point at CONNECT-IG.md")


def check_b2b_examples_not_catalog(sample: dict, front: dict, studio_text: str) -> None:
    """Owner correction 2026-09-07: logo/QR/napkins were examples, not a closed three-SKU B2B catalog."""
    lock = (ROOT / "packages" / "vfbiz" / "LOCK.md").read_text(encoding="utf-8")
    skill = (ROOT / "packages" / "vfbiz" / "SKILL.md").read_text(encoding="utf-8")
    local = (ROOT / "packages" / "vfbiz" / "LOCAL-B2B.md").read_text(encoding="utf-8")
    inst_studio = (INSTANCES / "velvet-factory" / "constitution" / "STUDIO.md").read_text(encoding="utf-8")
    for label, text in (
        ("packages/vfbiz/LOCK.md", lock),
        ("packages/vfbiz/SKILL.md", skill),
        ("packages/vfbiz/LOCAL-B2B.md", local),
        ("constitution/STUDIO.md", studio_text),
        ("instances/velvet-factory/constitution/STUDIO.md", inst_studio),
    ):
        if "B2B" not in text:
            fail(f"{label} must keep the B2B lock")
        if "דוגמאות" not in text:
            fail(f"{label} must say logo/QR/napkins are examples, not a closed catalog")
        if "נעול" not in text:
            fail(f"{label} must keep B2B locked until lead opens it")
    for label, profile in (("sample", sample), ("frontend-profile", front)):
        extra = (profile.get("compliance") or {}).get("extraLocks") or []
        if "b2b-logo-qr-napkins-locked" in extra:
            fail(f"{label} extraLocks must not treat logo/QR/napkins as the closed B2B catalog")
        if "b2b-line-locked" not in extra:
            fail(f"{label} extraLocks must include b2b-line-locked")


def main() -> None:
    for rel in REQUIRED_ROOT:
        if not (PACK / rel).is_file():
            fail(f"missing packages/velvetos/{rel}")

    if (PACK / "ACTIVE.json").exists():
        fail("remove ACTIVE.json — Core uses CORE.json")
    if (PACK / "INSTANCE.json").exists():
        fail("remove INSTANCE.json from core — instances live under instances/")
    if (PACK / "tenants").exists():
        fail("remove tenants/")

    if not PUBLISH.is_file():
        fail("missing scripts/publish-instance.sh")

    core = load(CORE)
    if core.get("role") != "core":
        fail("CORE.json role must be core")
    if core.get("displayName") != "VelvetOS Core":
        fail("CORE.json displayName must be VelvetOS Core")
    if "backend" not in json.dumps(core.get("metaphor", {})).lower():
        fail("CORE.json must describe backend metaphor")

    catalog = load(MODULES_CATALOG)
    modules = catalog.get("modules") or []
    if len(modules) < 12:
        fail(f"expected >=12 modules, got {len(modules)}")
    module_ids: set[str] = set()
    for row in modules:
        mid = row["id"]
        if mid in module_ids:
            fail(f"duplicate module {mid}")
        module_ids.add(mid)
        if not (PACK / row["file"]).is_file():
            fail(f"missing module file {row['file']}")

    for path in sorted(PRESETS.glob("*.json")):
        data = load(path)
        if data.get("kind") != "preset":
            fail(f"{path.name}: kind must be preset")
        for mid in data["modulesEnabled"]:
            if mid not in module_ids:
                fail(f"preset {data['id']}: unknown module {mid}")
    for need in REQUIRED_PRESETS:
        if not (PRESETS / f"{need}.json").is_file():
            fail(f"missing preset {need}")

    sample_path = SAMPLES / "velvet-factory.json"
    if not sample_path.is_file():
        fail("missing samples/velvet-factory.json")
    sample = load(sample_path)
    validate_profile(sample, module_ids, label="sample")

    # instance scaffold (frontend)
    vf_inst = INSTANCES / "velvet-factory"
    for rel in (
        "INSTANCE.json",
        "README.md",
        "AGENTS.md",
        "instance/velvet-factory.json",
        "constitution/STUDIO.md",
        "constitution/ORCHESTRA.md",
        "constitution/SEND.md",
        "scripts/attach-core.sh",
        ".cursor/vf-desk.json",
        ".cursor/environment.json",
    ):
        if not (vf_inst / rel).is_file():
            fail(f"missing instances/velvet-factory/{rel}")
    meta = load(vf_inst / "INSTANCE.json")
    if meta.get("role") != "instance":
        fail("instances/velvet-factory INSTANCE.json role must be instance")
    if meta.get("displayName") != "VelvetOS — Velvet Factory":
        fail("instance displayName mismatch")
    front = load(vf_inst / "instance" / "velvet-factory.json")
    validate_profile(front, module_ids, label="frontend-profile")
    if front["channels"]["instagram"][0]["handle"] != "@velvets_cloud":
        fail("frontend VF IG must be @velvets_cloud")

    desk = load(DESK)
    studio_text = STUDIO.read_text(encoding="utf-8")
    check_reference_vf(sample, desk, studio_text)
    check_reference_vf(front, desk, studio_text)
    check_b2b_examples_not_catalog(sample, front, studio_text)

    # desk should identify as core hosting reference front
    if desk.get("product") != "VelvetOS":
        fail("desk.product must be VelvetOS")
    vos = desk.get("velvetos") or {}
    if "CORE.json" not in str(vos) and "core" not in json.dumps(vos).lower():
        fail("desk.velvetos must point at core")

    lead = next((s for s in desk.get("seats", []) if s.get("id") == "lead"), None)
    if not lead or "velvetos" not in (lead.get("packs") or []):
        fail("desk lead seat must include velvetos")

    agents = AGENTS.read_text(encoding="utf-8")
    if "VelvetOS Core" not in agents:
        fail("AGENTS.md must say VelvetOS Core")
    if "frontend" not in agents.lower() and "פרונט" not in agents:
        fail("AGENTS.md must mention frontend instances")

    repos = REPOS.read_text(encoding="utf-8")
    for needle in ("backend", "frontend", "velvetos-velvet-factory", "attach-core", "environment.json"):
        if needle not in repos:
            fail(f"REPOS.md must mention {needle}")

    env_path = vf_inst / ".cursor" / "environment.json"
    env = load(env_path)
    if env.get("install") != "./scripts/attach-core.sh":
        fail("instances/velvet-factory environment.json install must run attach-core")
    deps = env.get("repositoryDependencies") or []
    if not any("velvetos-core" in d for d in deps):
        fail("instances/velvet-factory environment.json must list velvetos-core dependency")

    attach = (vf_inst / "scripts" / "attach-core.sh").read_text(encoding="utf-8")
    for needle in (
        "VELVETOS_CORE_OFFLINE",
        "VELVETOS_CORE_PATH",
        "--offline",
        "ok-stale",
        ".attach-stamp",
        "vendor_usable",
    ):
        if needle not in attach:
            fail(f"instances/velvet-factory/scripts/attach-core.sh must support {needle}")
    tmpl_attach = (INSTANCES / "_template" / "scripts" / "attach-core.sh").read_text(encoding="utf-8")
    for needle in ("VELVETOS_CORE_OFFLINE", "VELVETOS_CORE_PATH", ".attach-stamp"):
        if needle not in tmpl_attach:
            fail(f"instances/_template/scripts/attach-core.sh must support {needle}")
    inst_env = (PACK / "INSTANCE-ENV.md").read_text(encoding="utf-8")
    for needle in ("Offline", "VELVETOS_CORE_OFFLINE", "VELVETOS_CORE_PATH", ".attach-stamp"):
        if needle not in inst_env:
            fail(f"INSTANCE-ENV.md must document offline attach ({needle})")

    if not (PACK / "INSTANCE-ENV.md").is_file():
        fail("missing packages/velvetos/INSTANCE-ENV.md")

    kernel = KERNEL.read_text(encoding="utf-8")
    if "backend" not in kernel.lower() and "באקאנד" not in kernel:
        fail("KERNEL.md must state backend role")
    for needle in ("LAYERS.md", "ADR-THREE-LAYERS", "Kernel", "nervous-system"):
        if needle not in kernel:
            fail(f"KERNEL.md must mention three-layer SoC needle {needle!r}")

    layers_doc = (PACK / "LAYERS.md").read_text(encoding="utf-8")
    for needle in ("Edge", "Kernel", "Office", "component_state", "Degraded", "human"):
        if needle not in layers_doc:
            fail(f"LAYERS.md missing {needle!r}")

    adr = (PACK / "ADR-THREE-LAYERS.md").read_text(encoding="utf-8")
    for needle in (
        "מקובל",
        "runtime שני",
        "nervous-system",
        "events.catalog",
        "WhatsApp",
        "vf_retro_signals",
        "component_state",
    ):
        if needle not in adr:
            fail(f"ADR-THREE-LAYERS.md missing {needle!r}")

    events_cat = load(PACK / "schema" / "events.catalog.json")
    if events_cat.get("name") != "velvetos-events":
        fail("events.catalog.json name must be velvetos-events")
    event_ids = {e.get("id") for e in events_cat.get("events") or []}
    for need in (
        "inquiry.received",
        "task.state_changed",
        "sensor.degraded",
        "tool.failover",
        "retro.anomaly",
        "mail.sent",
        "print.done",
        "print.maintenance_due",
        "print.route_suggested",
        "print.filament_short",
        "brief.gate_applied",
        "content.draft_ready",
        "shelf.scan_pass",
        "books.integrity_flag",
    ):
        if need not in event_ids:
            fail(f"events.catalog.json missing event {need}")
    for gate in ("sale-ils", "customer-whatsapp-send", "boost", "print-from-hq"):
        if gate not in (events_cat.get("humanGates") or []):
            fail(f"events.catalog.json humanGates missing {gate}")

    envelope = load(PACK / "schema" / "event-envelope.schema.json")
    if "layer" not in (envelope.get("properties") or {}):
        fail("event-envelope.schema.json must require layer property definition")
    layer_enum = (envelope.get("properties") or {}).get("layer", {}).get("enum") or []
    if set(layer_enum) != {"edge", "kernel", "office"}:
        fail("event-envelope layer enum must be edge/kernel/office")

    core_layers = core.get("layers") or {}
    if "kernel" not in json.dumps(core_layers).lower():
        fail("CORE.json must describe layers.kernel")
    if "nervous-system runtime" not in json.dumps(core.get("metaphor", {})).lower():
        fail("CORE.json metaphor must reject nervous-system runtime rename")

    lock_txt = (PACK / "LOCK.md").read_text(encoding="utf-8")
    for needle in ("שלוש שכבות", "Human gates", "Degraded Mode"):
        if needle not in lock_txt:
            fail(f"LOCK.md missing {needle!r}")

    if "velvetos" not in {p["name"] for p in load(MANIFEST).get("packs", [])}:
        fail("velvetos missing from manifest")

    if not (ROOT / "docs" / "VELVETOS.md").is_file():
        fail("missing docs/VELVETOS.md")

    print(
        f"OK velvetos-core modules={len(module_ids)} "
        f"presets={len(list(PRESETS.glob('*.json')))} "
        f"frontend_scaffold=velvet-factory "
        f"events={len(event_ids)}"
    )


if __name__ == "__main__":
    main()
