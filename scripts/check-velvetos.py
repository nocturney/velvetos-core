#!/usr/bin/env python3
"""Validate VelvetOS Core + instance scaffolds. No network. No send."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packages" / "velvetos"
CORE = PACK / "CORE.json"
INSTANCE_RESOLVER = PACK / "instance_resolver.py"
TOOL_STATUS_RESOLVER = PACK / "tool_status_resolver.py"
TOOL_STATUS_CONTRACT = PACK / "tool-status-contract.json"
LEGACY_TOOL_STATUS = PACK / "TOOL-STATUS.json"
INSTANCE_MANIFEST_SCHEMA = PACK / "schema" / "instance-manifest.schema.json"
TOOL_STATUS_CONTRACT_SCHEMA = PACK / "schema" / "tool-status-contract.schema.json"
INSTANCE_TOOL_STATUS_SCHEMA = PACK / "schema" / "instance-tool-status.schema.json"
MODULES_CATALOG = PACK / "modules" / "catalog.json"
PRESETS = PACK / "presets"
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
    "instance_resolver.py",
    "tool_status_resolver.py",
    "tool-status-contract.json",
    "modules/catalog.json",
    "schema/instance.schema.json",
    "schema/instance-manifest.schema.json",
    "schema/tool-status-contract.schema.json",
    "schema/instance-tool-status.schema.json",
    "schema/events.catalog.json",
    "schema/event-envelope.schema.json",
)
REQUIRED_PRESETS = ("maker-print", "beauty-multi-ig", "clinical-legal-opinions")


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_instance_resolver():
    spec = importlib.util.spec_from_file_location("velvetos_instance_resolver", INSTANCE_RESOLVER)
    if spec is None or spec.loader is None:
        fail("cannot load packages/velvetos/instance_resolver.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_tool_status_resolver():
    spec = importlib.util.spec_from_file_location("velvetos_tool_status_resolver", TOOL_STATUS_RESOLVER)
    if spec is None or spec.loader is None:
        fail("cannot load packages/velvetos/tool_status_resolver.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check_instance_resolver_contract(vf_inst: Path, meta: dict) -> None:
    surfaces = meta.get("surfaces") or {}
    expected = {
        "profile": "instance/velvet-factory.json",
        "toolDesk": ".cursor/vf-desk.json",
        "fleet": "instance/fleet.json",
        "toolStatus": "instance/tool-status.json",
        "chatgptProject": "distribution/chatgpt-project/LATEST.json",
    }
    if meta.get("surfaceContractVersion") != 1:
        fail("instance surfaceContractVersion must be 1")
    if surfaces != expected:
        fail(f"instance surfaces drift: {surfaces!r}")
    if meta.get("profile") != surfaces.get("profile"):
        fail("INSTANCE.json legacy profile alias must match surfaces.profile")

    manifest_schema = load(INSTANCE_MANIFEST_SCHEMA)
    expected_manifest_required = {
        "product",
        "role",
        "displayName",
        "instanceId",
        "profile",
        "surfaceContractVersion",
        "surfaces",
        "core",
    }
    if set(manifest_schema.get("required") or []) != expected_manifest_required:
        fail("instance-manifest schema top-level required fields drift")
    surface_schema = ((manifest_schema.get("properties") or {}).get("surfaces") or {})
    if surface_schema.get("required") != ["profile"]:
        fail("generic instance manifest must require profile only; domain surfaces stay optional")
    surface_props = surface_schema.get("properties") or {}
    if not {"profile", "toolDesk", "fleet", "toolStatus", "chatgptProject"} <= set(surface_props):
        fail("instance-manifest schema must expose profile/toolDesk/fleet/toolStatus/chatgptProject surface vocabulary")

    canonical_fleet = load(vf_inst / surfaces["fleet"])
    legacy_fleet = load(ROOT / "packages" / "vfprod" / "FLEET.json")
    if canonical_fleet != legacy_fleet:
        fail("Stage 8B canonical instance fleet must remain parity-equal to legacy vfprod/FLEET.json")
    if len(canonical_fleet.get("printers") or []) != 4:
        fail("Stage 8B canonical instance fleet printer count drift")

    contract = load(TOOL_STATUS_CONTRACT)
    if contract.get("schema") != "velvetos.tool-status-contract.v1":
        fail("generic tool-status contract schema drift")
    if contract.get("role") != "CORE_GENERIC_SCHEMA_INTERFACE_ALGORITHM":
        fail("tool-status contract must remain generic Core semantics")
    if contract.get("instanceStateSurface") != "toolStatus":
        fail("tool-status contract instance surface drift")
    if (contract.get("composition") or {}).get("consumerCutover") is not False:
        fail("Stage 8B tool-status split must not claim consumer cutover")

    contract_schema = load(TOOL_STATUS_CONTRACT_SCHEMA)
    if contract_schema.get("$id") != "velvetos.tool-status-contract.v1":
        fail("tool-status contract schema id drift")
    state_schema = load(INSTANCE_TOOL_STATUS_SCHEMA)
    if state_schema.get("$id") != "velvetos.instance-tool-status.v1":
        fail("instance tool-status schema id drift")

    instance_tool_status = load(vf_inst / surfaces["toolStatus"])
    if instance_tool_status.get("schema") != "velvetos.instance-tool-status.v1":
        fail("instance tool-status schema drift")
    if instance_tool_status.get("instanceId") != "velvet-factory":
        fail("instance tool-status identity drift")
    if instance_tool_status.get("contract") != "packages/velvetos/tool-status-contract.json":
        fail("instance tool-status contract binding drift")

    tool_status_resolver = load_tool_status_resolver()
    try:
        composed_tool_status = tool_status_resolver.compose_tool_status(
            ROOT, instance_id="velvet-factory", env={}
        )
    except Exception as exc:
        fail(f"tool-status composition failed: {exc}")
    legacy_tool_status = load(LEGACY_TOOL_STATUS)
    if composed_tool_status != legacy_tool_status:
        fail("generic contract + instance tool status must remain parity-equal to legacy TOOL-STATUS.json")

    core = load(CORE)
    tool_resolution = core.get("toolStatusResolution") or {}
    if tool_resolution != {
        "contract": "packages/velvetos/tool-status-contract.json",
        "resolver": "packages/velvetos/tool_status_resolver.py",
        "instanceSurface": "toolStatus",
        "legacyCompatibilityPath": "packages/velvetos/TOOL-STATUS.json",
        "consumerCutover": False,
        "silentBusinessDefaultForbidden": True,
    }:
        fail("Core toolStatusResolution contract drift")

    resolver = load_instance_resolver()
    try:
        from_core = resolver.resolve_instance(ROOT, instance_id="velvet-factory", env={})
    except Exception as exc:
        fail(f"instance resolver explicit Core resolution failed: {exc}")
    if from_core.mode != "core-explicit-instance":
        fail("instance resolver Core mode drift")
    if from_core.instance_root != vf_inst.resolve():
        fail("instance resolver Core instance root mismatch")
    for key, rel in expected.items():
        if from_core.surface(key) != (vf_inst / rel).resolve():
            fail(f"instance resolver surface mismatch: {key}")

    try:
        from_env = resolver.resolve_instance(ROOT, env={"VELVETOS_INSTANCE_ID": "velvet-factory"})
    except Exception as exc:
        fail(f"instance resolver env resolution failed: {exc}")
    if from_env.instance_id != "velvet-factory":
        fail("instance resolver env instance id mismatch")

    try:
        current = resolver.resolve_instance(vf_inst, env={})
    except Exception as exc:
        fail(f"instance resolver current-workspace resolution failed: {exc}")
    if current.mode != "current-instance-workspace" or current.instance_id != "velvet-factory":
        fail("instance resolver current workspace identity/mode drift")

    try:
        resolver.resolve_instance(ROOT, env={})
    except resolver.InstanceResolutionError:
        pass
    else:
        fail("Core resolver must fail closed when no instance id is supplied")

    if "velvet-factory" in INSTANCE_RESOLVER.read_text(encoding="utf-8").lower():
        fail("generic instance resolver must not contain a Velvet Factory business default")

    with tempfile.TemporaryDirectory() as td:
        fake_core = Path(td)
        fake = fake_core / "instances" / "fixture"
        fake.mkdir(parents=True)
        (fake / "profile.json").write_text("{}\n", encoding="utf-8")
        manifest = {
            "product": "VelvetOS",
            "role": "instance",
            "displayName": "Fixture Instance",
            "instanceId": "fixture",
            "profile": "profile.json",
            "surfaceContractVersion": 1,
            "surfaces": {
                "profile": "profile.json",
            },
            "core": {
                "github": "example/core",
                "vendorPath": "vendor/core",
                "attach": "scripts/attach-core.sh",
            },
        }
        (fake / "INSTANCE.json").write_text(
            json.dumps(manifest) + "\n",
            encoding="utf-8",
        )

        try:
            generic = resolver.resolve_instance(fake_core, instance_id="fixture", env={})
        except Exception as exc:
            fail(f"generic non-VF instance resolution failed: {exc}")
        if generic.instance_id != "fixture" or generic.mode != "core-explicit-instance":
            fail("generic non-VF instance identity/mode drift")
        if set(generic.surfaces) != {"profile"}:
            fail("generic instance resolver must not require VF-only surfaces")

        bad_version = dict(manifest)
        bad_version["surfaceContractVersion"] = 2
        (fake / "INSTANCE.json").write_text(json.dumps(bad_version) + "\n", encoding="utf-8")
        try:
            resolver.resolve_instance(fake_core, instance_id="fixture", env={})
        except resolver.InstanceResolutionError:
            pass
        else:
            fail("modern instance manifest must fail closed on unsupported surfaceContractVersion")

        outside = fake_core / "outside-stage8b.json"
        outside.write_text("{}\n", encoding="utf-8")
        traversal = dict(manifest)
        traversal["surfaces"] = {
            "profile": "profile.json",
            "escape": "../../outside-stage8b.json",
        }
        (fake / "INSTANCE.json").write_text(json.dumps(traversal) + "\n", encoding="utf-8")
        try:
            resolver.resolve_instance(fake_core, instance_id="fixture", env={})
        except resolver.InstanceResolutionError:
            pass
        else:
            fail("instance resolver must reject parent traversal")


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
        fail("canonical instance profile must be velvet-factory")
    studio = desk.get("studio") or {}
    if studio.get("instagram") != "@velvets_cloud":
        fail("desk.studio.instagram must stay @velvets_cloud during compat")
    if studio.get("whatsapp") != "050-2517000":
        fail("desk.studio.whatsapp must stay 050-2517000 during compat")
    labels = [s["label"] for s in profile["pipeline"]["stages"]]
    if desk.get("pipeline") != labels:
        fail("desk.pipeline mismatch vs canonical instance profile")
    for needle in ("050-2517000", "velvets_cloud", "שדרות"):
        if needle not in studio_text:
            fail(f"STUDIO.md must still list {needle} (compat reference)")
    for need in ("fulfill-pickup", "production-print", "compliance-maker"):
        if need not in profile["modulesEnabled"]:
            fail(f"VF canonical instance profile must enable {need}")
    bind = profile.get("mcpBind") or {}
    wa = bind.get("whatsapp") or {}
    if wa.get("send") is not False:
        fail("VF mcpBind.whatsapp.send must be false")
    hub = bind.get("studiomcphub") or {}
    if "print_ready" not in (hub.get("skip") or []):
        fail("VF mcpBind.studiomcphub must skip print_ready")
    ig = bind.get("instagram") or {}
    if not ig.get("enabled"):
        fail("VF mcpBind.instagram must be enabled (Instagram MCP mapped)")
    if ig.get("dm") is not False:
        fail("VF mcpBind.instagram.dm must be false")
    if "CONNECT-IG.md" not in (ig.get("connect") or ""):
        fail("VF mcpBind.instagram.connect must point at CONNECT-IG.md")


def check_offering_shape(front: dict, studio_text: str) -> None:
    """Owner correction 2026-09-14: two public tracks; quantity/customer type are job facts."""
    offering = (ROOT / "packages" / "vfbiz" / "OFFERING.md").read_text(encoding="utf-8")
    inst_studio = (INSTANCES / "velvet-factory" / "constitution" / "STUDIO.md").read_text(encoding="utf-8")
    for label, text in (("OFFERING.md", offering), ("STUDIO.md", studio_text), ("instance STUDIO.md", inst_studio)):
        for needle in ("מוצרים מוכנים", "התאמה אישית"):
            if needle not in text:
                fail(f"{label} must keep clear two-track offering: missing {needle}")
    compliance = front.get("compliance") or {}
    if compliance.get("noCustomerTypeServicePillar") is not True:
        fail("frontend-profile must lock noCustomerTypeServicePillar")
    if compliance.get("offeringAuthority") != "packages/vfbiz/OFFERING.md":
        fail("frontend-profile offeringAuthority mismatch")
    old_paths = [
        ROOT / "packages" / "vfbiz" / ("LOCAL-" + "B2" + "B.md"),
        ROOT / "packages" / "vfsales" / "hq" / ("B2" + "B-QUOTE.md"),
    ]
    if any(x.exists() for x in old_paths):
        fail("retired customer-type service-line artifact still exists")


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
    resolution = core.get("instanceResolution") or {}
    if resolution.get("resolver") != "packages/velvetos/instance_resolver.py":
        fail("CORE.json instance resolver path drift")
    if resolution.get("instanceIdEnvironment") != "VELVETOS_INSTANCE_ID":
        fail("CORE.json instance id environment drift")
    if resolution.get("manifestPattern") != "instances/{instanceId}/INSTANCE.json":
        fail("CORE.json manifest pattern drift")
    if resolution.get("surfaceMap") != "INSTANCE.json#surfaces":
        fail("CORE.json surface map contract drift")
    if resolution.get("requireExplicitInstanceIdWhenRunningFromCore") is not True:
        fail("CORE.json must require explicit instance id from Core")
    if resolution.get("silentBusinessDefaultForbidden") is not True:
        fail("CORE.json must forbid silent business defaults")

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

    # instance scaffold (frontend) is the canonical runtime/business profile.
    vf_inst = INSTANCES / "velvet-factory"
    for rel in (
        "INSTANCE.json",
        "README.md",
        "AGENTS.md",
        "instance/velvet-factory.json",
        "instance/fleet.json",
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
    check_instance_resolver_contract(vf_inst, meta)
    front = load(vf_inst / "instance" / "velvet-factory.json")
    validate_profile(front, module_ids, label="frontend-profile")
    if front["channels"]["instagram"][0]["handle"] != "@velvets_cloud":
        fail("frontend VF IG must be @velvets_cloud")

    desk = load(DESK)
    studio_text = STUDIO.read_text(encoding="utf-8")
    check_reference_vf(front, desk, studio_text)
    check_offering_shape(front, studio_text)

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
    sync_sh = (ROOT / "scripts" / "sync-instance-scaffold.sh").read_text(encoding="utf-8")
    for needle in ("CHECK-ONLY", "--skip-if-inaccessible", "--check", "GIT_TERMINAL_PROMPT=0", "-x .git"):
        if needle not in sync_sh:
            fail(f"sync-instance-scaffold.sh must keep {needle}")
    for line in sync_sh.splitlines():
        code = line.split("#", 1)[0].strip()
        if not code or code.startswith("echo "):
            continue
        if "git push" in code or "publish-instance.sh" in code or "git commit" in code:
            fail(f"sync-instance-scaffold.sh must stay check-only: {code}")
    # control-center/ is the frontend's own Control Center app (added 2026-09-28, owner-approved sync).
    if 'INSTANCE_ONLY_ALLOWED=(".github" "docs" ".cursor/mcp.json" "control-center")' not in sync_sh:
        fail("sync-instance-scaffold.sh instance-only allowlist drifted (keep it explicit and minimal)")
    vf = INSTANCES / "velvet-factory"
    vf_desk = json.loads((vf / ".cursor" / "vf-desk.json").read_text(encoding="utf-8"))
    vf_prof = json.loads((vf / "instance" / "velvet-factory.json").read_text(encoding="utf-8"))
    vf_auto = vf_prof.get("creativeAutonomy") or {}
    for gate in ("brandAssetLock", "creativeTransformationLock", "projectRequestGate"):
        if (vf_desk.get(gate) or {}).get("mode") != "fail_closed" or (vf_auto.get(gate) or {}).get("mode") != "fail_closed":
            fail(f"velvet-factory template lost fail-closed {gate} (vf-desk + profile)")
    for flag in ("requireOwnerApprovedVisualStandard", "requireBrandAssetLock", "requireCreativeTransformationLock", "requireProjectRequestGate", "requireLiveVerification"):
        if (vf_auto.get("publish") or {}).get(flag) is not True:
            fail(f"velvet-factory template publish gate lost {flag}")
    if not {"050-2517000", "wa.me"} <= set((vf_prof.get("cta") or {}).get("forbiddenPublic") or []):
        fail("velvet-factory template lost cta.forbiddenPublic phone/wa.me")
    vf_verify = (vf / "scripts" / "verify-core.sh").read_text(encoding="utf-8")
    for needle in ("check-vf-offering.py", "check-publication-prep-execution.py", "check-brand-asset-cta-lock.py", "check-creative-transformation-lock.py", "check-project-request-gate.py", "check-instance-visual-bootstrap.py"):
        if needle not in vf_verify:
            fail(f"velvet-factory verify-core.sh must run {needle}")
    if "verify_attached" not in attach or 'verify-core.sh" focused' not in attach:
        fail("velvet-factory attach-core.sh must verify an online attach (fail-closed)")
    for rel in ("AGENTS.md", ".cursor/rules/velvetos-instance-desk.mdc"):
        body = (vf / rel).read_text(encoding="utf-8")
        for needle in ("VF_PUBLICATION_ROUTE_V1", "OFFERING SHAPE", "BRAND ASSET + PUBLIC CTA LOCK", "CREATIVE TRANSFORMATION LOCK", "UNIVERSAL PROJECT REQUEST GATE", "visual_standard_unavailable"):
            if needle not in body:
                fail(f"velvet-factory {rel} lost gate section {needle!r}")
    lock = (INSTANCES / "velvet-factory" / "core.lock.yml").read_text(encoding="utf-8")
    lock_ref = next((l.split(":", 1)[1].strip() for l in lock.splitlines() if l.startswith("ref:")), "")
    if "refPolicy: track-main" not in lock or lock_ref != "main" or "Intentionally NOT a SHA pin" not in lock:
        fail("instances/velvet-factory/core.lock.yml must state ref: main + refPolicy: track-main explicitly")
    for script in ("attach-core.sh", "verify-core.sh"):
        body = (INSTANCES / "velvet-factory" / "scripts" / script).read_text(encoding="utf-8")
        if f'CORE_REF="${{VELVETOS_CORE_REF:-{lock_ref}}}"' not in body:
            fail(f"instances/velvet-factory/scripts/{script} default ref must match core.lock.yml ref={lock_ref}")
    check_all_wf = (ROOT / ".github" / "workflows" / "check-all.yml").read_text(encoding="utf-8")
    if "sync-instance-scaffold.sh --skip-if-inaccessible" not in check_all_wf:
        fail("check-all.yml must run sync-instance-scaffold.sh --skip-if-inaccessible")
    inst_readme = (INSTANCES / "README.md").read_text(encoding="utf-8")
    if "velvetos-velvet-factory` are **public**" in inst_readme or "`nocturney/velvetos-velvet-factory` is **private**" not in inst_readme:
        fail("instances/README.md must state the frontend repo is private")

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
        "content.policy_checked",
        "content.approved_for_manual_posting",
        "content.posted_manually",
        "community.work_order",
        "lead.attributed",
    ):
        if need not in event_ids:
            fail(f"events.catalog.json missing event {need}")
    for gate in (
        "sale-ils",
        "customer-whatsapp-send",
        "boost",
        "print-from-hq",
        "ig-autopost",
        "auto-dm",
        "user-tag-without-optin",
    ):
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
