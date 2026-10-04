#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import hashlib
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from vf_project_bundle import ProjectBundleError, resolve as resolve_project_bundle, resolve_reference

def authority_reference_exists(reference: str) -> bool:
    try:
        return resolve_reference(ROOT, reference, instance_id="velvet-factory", env={}).is_file()
    except ProjectBundleError:
        return False

GATE = ROOT / "packages/velvetos/PROJECT-REQUEST-GATE.md"
MANIFEST = ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"
CLI = ROOT / "scripts/vf_project_preflight.py"
FRICTION_BASELINE = ROOT / "packages/velvetos/policy/reports/stage4a-friction-baseline.json"
FAST_PATH_REPORT = ROOT / "packages/velvetos/policy/reports/stage4b-project-request-fast-path.json"
STAGE5A_BASELINE = ROOT / "packages/velvetos/policy/reports/stage5a-context-locality-baseline.json"
STAGE5A_BASELINE_GENERATOR = ROOT / "scripts/generate-stage5a-context-locality-baseline.py"
STAGE5A_REPORT = ROOT / "packages/velvetos/policy/reports/stage5a-context-locality.json"
STAGE5A_GENERATOR = ROOT / "scripts/generate-stage5a-context-locality-report.py"
STAGE5C_REPORT = ROOT / "packages/velvetos/policy/reports/stage5c-workspace-distribution.json"
STAGE5C_GENERATOR = ROOT / "scripts/generate-stage5c-workspace-distribution-report.py"


def fail(msg: str) -> None:
    print(f"FAIL project-request-gate: {msg}", file=sys.stderr)
    raise SystemExit(1)

for path in (GATE, MANIFEST, CLI, FRICTION_BASELINE, FAST_PATH_REPORT, STAGE5A_BASELINE, STAGE5A_BASELINE_GENERATOR, STAGE5A_REPORT, STAGE5A_GENERATOR, STAGE5C_REPORT, STAGE5C_GENERATOR):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

baseline = json.loads(FRICTION_BASELINE.read_text(encoding="utf-8"))
if baseline.get("schema") != "velvetos.stage4a-friction-baseline.v1" or baseline.get("stage") != "4A":
    fail("Stage 4A friction baseline schema/stage mismatch")
if baseline.get("behavior_change") is not False:
    fail("Stage 4A friction baseline must remain observation-only")
if baseline.get("prepared_against_main_sha") != "9989f0ffd11b97a28da732c9fa6ddd234ba51d35":
    fail("Stage 4A friction baseline source main SHA drift")
summary = baseline.get("summary") or {}
expected_stage4a = {
    "sampled_flows": 14,
    "baseline_authorities_loaded_for_every_request": 9,
    "auto_route_aligned": 6,
    "general_business_fallback": 8,
    "project_preflight_blocked": 3,
    "max_required_sources": 22,
    "max_hard_gates": 11,
    "gmail_transport_ready": True,
    "maya_readiness": "READY_ACCEPTED_SURFACE",
}
for key, value in expected_stage4a.items():
    if summary.get(key) != value:
        fail(f"Stage 4A friction baseline drift: {key} expected {value!r}, got {summary.get(key)!r}")
if len(baseline.get("flows") or []) != 14:
    fail("Stage 4A friction baseline must retain exactly 14 sampled flows")
classes = {row.get("disposition") for row in baseline.get("gate_classification", []) if isinstance(row, dict)}
if classes != {"KEEP", "INTERNALIZE", "MERGE", "ACTION_SCOPED", "REMOVE_AS_DUPLICATE"}:
    fail(f"Stage 4A gate classification coverage mismatch: {sorted(classes)}")

stage4b_report = json.loads(FAST_PATH_REPORT.read_text(encoding="utf-8"))
if stage4b_report.get("schema") != "velvetos.stage4b-project-request-fast-path.v1" or stage4b_report.get("stage") != "4B":
    fail("Stage 4B acceptance report schema/stage mismatch")
if stage4b_report.get("behavior_change") is not True or stage4b_report.get("base_main_sha") != "baf8d3492a84568d8351c831e0e2105d5fa7bb36":
    fail("Stage 4B acceptance report base/behavior contract drift")
stage4b_summary = stage4b_report.get("summary") or {}
expected_stage4b_summary = {
    "route_aligned": 14,
    "general_business_fallback": 0,
    "fast_path_count": 7,
    "full_preflight_count": 7,
    "required_tools_populated": 10,
    "owner_surface_internal_unless_true_blocker": 14,
    "creative_flows_fail_closed_without_evidence": 4,
    "fast_path_source_reduction_percent": 52.5,
    "fast_path_gate_reduction_percent": 40.7,
    "cad_readonly_and_build_scope_distinct": True,
    "negative_controls_full": True,
}
for key, value in expected_stage4b_summary.items():
    if stage4b_summary.get(key) != value:
        fail(f"Stage 4B acceptance report drift: {key} expected {value!r}, got {stage4b_summary.get(key)!r}")
if not all(row.get("pass") is True for row in stage4b_report.get("negative_controls") or []):
    fail("Stage 4B acceptance report contains a failed FULL-preflight negative control")

stage5a_baseline = json.loads(STAGE5A_BASELINE.read_text(encoding="utf-8"))
if stage5a_baseline.get("schema") != "velvetos.stage5a-context-locality-baseline.v1" or stage5a_baseline.get("stage") != "5A":
    fail("Stage 5A baseline schema/stage mismatch")
if stage5a_baseline.get("behavior_change") is not False or stage5a_baseline.get("prepared_against_main_sha") != "47f518e9b22bccd4b9fa43cc41336ce28ab701b2":
    fail("Stage 5A baseline identity drift")
if stage5a_baseline.get("source_ref") != "47f518e9b22bccd4b9fa43cc41336ce28ab701b2":
    fail("Stage 5A baseline must be measured from the exact pre-5A Git ref")
if stage5a_baseline.get("root_agents") != {"lines": 180, "words": 3521, "characters": 28419}:
    fail("Stage 5A root baseline drift")
if stage5a_baseline.get("root_domain_leakage_total") != 41 or stage5a_baseline.get("package_local_agents_count") != 0:
    fail("Stage 5A leakage/local-guide baseline drift")
if stage5a_baseline.get("check_scripts_referencing_agents_count") != 25:
    fail("Stage 5A root-consumer baseline drift")
with tempfile.TemporaryDirectory(prefix="stage5a-baseline-") as td:
    regenerated_baseline = Path(td) / "baseline.json"
    proc = subprocess.run(
        [
            sys.executable, str(STAGE5A_BASELINE_GENERATOR),
            "--prepared-against", stage5a_baseline["prepared_against_main_sha"],
            "--source-ref", stage5a_baseline["source_ref"],
            "--captured-at", stage5a_baseline["captured_at"],
            "--output", str(regenerated_baseline),
        ],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=90,
    )
    if proc.returncode != 0:
        fail("Stage 5A baseline regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()))
    if regenerated_baseline.read_bytes() != STAGE5A_BASELINE.read_bytes():
        fail("Stage 5A baseline is not reproducible from the pinned Git ref")

stage5a = json.loads(STAGE5A_REPORT.read_text(encoding="utf-8"))
if stage5a.get("schema") != "velvetos.stage5a-context-locality.v1" or stage5a.get("stage") != "5A":
    fail("Stage 5A acceptance schema/stage mismatch")
if stage5a.get("behavior_change") is not True or stage5a.get("prepared_against_main_sha") != "47f518e9b22bccd4b9fa43cc41336ce28ab701b2":
    fail("Stage 5A acceptance base/behavior drift")
if stage5a.get("repository_acceptance") != "PASS":
    fail("Stage 5A repository acceptance is not PASS")
after5 = stage5a.get("after") or {}
if (after5.get("root_agents") or {}).get("lines") != 56 or (after5.get("root_agents") or {}).get("words") != 453:
    fail("Stage 5A historical root reduction snapshot drift")
if after5.get("root_domain_leakage_total") != 0 or after5.get("package_local_agents_count") != 18:
    fail("Stage 5A historical locality snapshot drift")
if after5.get("root_word_reduction_percent") != 87.1:
    fail("Stage 5A root word-reduction snapshot drift")
locality5 = stage5a.get("instruction_locality") or {}
if locality5.get("domain_count") != 10 or locality5.get("all_domains_have_exactly_one_primary_guide") is not True or locality5.get("all_domain_receipts_pass") is not True:
    fail("Stage 5A locality acceptance drift")
negative5 = stage5a.get("negative_controls") or {}
if negative5.get("system_engineering_loads_only_root_plus_core") is not True or negative5.get("unknown_domain_root_only_full_blocked") is not True or negative5.get("unrelated_specialist_guides_in_system_receipt") != []:
    fail("Stage 5A negative-control drift")
auth5 = stage5a.get("authorization_semantics") or {}
if auth5.get("external_effect_authority_registry_unchanged") is not True or auth5.get("local_guides_are_authority") is not False or auth5.get("project_request_remains_router_only") is not True:
    fail("Stage 5A authorization-semantics snapshot drift")
with tempfile.TemporaryDirectory(prefix="stage5a-acceptance-") as td:
    regenerated_report = Path(td) / "stage5a.json"
    proc = subprocess.run(
        [
            sys.executable, str(STAGE5A_GENERATOR),
            "--prepared-against", stage5a["prepared_against_main_sha"],
            "--captured-at", stage5a["captured_at"],
            "--output", str(regenerated_report),
        ],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=90,
    )
    if proc.returncode != 0:
        fail("Stage 5A acceptance regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()))
    if regenerated_report.read_bytes() != STAGE5A_REPORT.read_bytes():
        fail("Stage 5A acceptance report is not reproducible")

stage5c = json.loads(STAGE5C_REPORT.read_text(encoding="utf-8"))
if stage5c.get("schema") != "velvetos.stage5c-workspace-distribution.v1" or stage5c.get("stage") != "5C":
    fail("Stage 5C workspace-distribution schema/stage mismatch")
if stage5c.get("behavior_change") is not True or stage5c.get("prepared_against_main_sha") != "722005858f06724894d13856e77d79ad9a9ee3a9":
    fail("Stage 5C base/behavior contract drift")
if stage5c.get("repository_acceptance") != "PASS":
    fail("Stage 5C repository acceptance is not PASS")
dist5c = stage5c.get("distribution_binding") or {}
expected_dist5c = {
    "repository": "nocturney/velvetos-workspace-distribution",
    "base_sha": "13e161bb94ad004b431ee451e678a0a74cc7c732",
    "head_sha": "de214771e3c64063f201359c58f918653a0bed05",
    "merge_sha": "4fa715dc78275b87a942658b26b74608932d8d50",
    "pull_request": 3,
    "plugin_version": "1.6.0",
    "verify_bundle": "PASS",
    "desired_skill_count": 35,
    "creative_craft_specialist_count": 8,
}
for key, value in expected_dist5c.items():
    if dist5c.get(key) != value:
        fail(f"Stage 5C distribution binding drift: {key} expected {value!r}, got {dist5c.get(key)!r}")
expected_blobs5c = {
    "inventory/workspace-stack.json": "c858af50d684306727f9fd15fafcde140577b7ba",
    "inventory/workspace-audit.json": "9c1f19c053b478f1a5c9fc8cf65670d5c53b4995",
    "plugins/velvetos-workspace-skills/.codex-plugin/plugin.json": "27dbd4c236ffdd367b118ece3e14d59a1259eea9",
    "scripts/verify-bundle.ps1": "7d42dc69b081bf24e8a2e3f5a55aa5c74c576a69",
}
if dist5c.get("git_blobs") != expected_blobs5c:
    fail("Stage 5C distribution Git-blob binding drift")
eval5c = dist5c.get("creative_craft_eval") or {}
if eval5c != {"score": 56, "max_score": 56, "all_structural_pass": True}:
    fail("Stage 5C Creative Craft structural eval drift")
contract5c = stage5c.get("invocation_contract") or {}
expected_specialists5c = [
    "vf-cad-design-craft",
    "vf-dcc-modeling-craft",
    "vf-material-lookdev",
    "vf-product-visualization-craft",
    "vf-post-production-craft",
    "vf-vfx-compositing-craft",
    "vf-image-design-craft",
    "vf-technical-illustration-craft",
]
if contract5c.get("router") != "creative-craft" or contract5c.get("router_may_auto_invoke") is not True:
    fail("Stage 5C Creative Craft ambient-router contract drift")
if contract5c.get("specialists") != expected_specialists5c:
    fail("Stage 5C routed specialist set drift")
if contract5c.get("specialist_activation") != "ROUTED_ONLY" or contract5c.get("availability") != "DISTRIBUTED_WORKSPACE_WIDE":
    fail("Stage 5C specialist activation/availability drift")
if contract5c.get("warehouse_preload") is not False or contract5c.get("authorization_effect") != "NONE":
    fail("Stage 5C warehouse/auth boundary drift")
core5c = stage5c.get("core_source") or {}
if core5c.get("router_ambient_marker") is not True or set(core5c.get("router_frontmatter_keys") or []) != {"name", "description"}:
    fail("Stage 5C router source contract drift")
specialist_rows5c = core5c.get("specialists") or {}
if set(specialist_rows5c) != set(expected_specialists5c):
    fail("Stage 5C Core specialist evidence set drift")
for name in expected_specialists5c:
    row = specialist_rows5c.get(name) or {}
    if row.get("pass") is not True or row.get("frontmatter_standard") is not True or row.get("routed_only_marker") is not True:
        fail(f"Stage 5C specialist source drift: {name}")
auth5c = stage5c.get("authorization_semantics") or {}
if auth5c.get("external_effect_authority_registry_unchanged") is not True or auth5c.get("workspace_skill_invocation_is_policy_authority") is not False:
    fail("Stage 5C authorization-semantics drift")
acceptance5c = stage5c.get("acceptance") or {}
if not acceptance5c or not all(value is True for value in acceptance5c.values()):
    fail("Stage 5C acceptance criteria drift")
with tempfile.TemporaryDirectory(prefix="stage5c-workspace-") as td:
    regenerated5c = Path(td) / "stage5c.json"
    proc = subprocess.run(
        [
            sys.executable, str(STAGE5C_GENERATOR),
            "--prepared-against", stage5c["prepared_against_main_sha"],
            "--captured-at", stage5c["captured_at"],
            "--distribution-base-sha", dist5c["base_sha"],
            "--distribution-head-sha", dist5c["head_sha"],
            "--distribution-merge-sha", dist5c["merge_sha"],
            "--distribution-pr", str(dist5c["pull_request"]),
            "--distribution-version", dist5c["plugin_version"],
            "--workspace-stack-blob", dist5c["git_blobs"]["inventory/workspace-stack.json"],
            "--workspace-audit-blob", dist5c["git_blobs"]["inventory/workspace-audit.json"],
            "--plugin-manifest-blob", dist5c["git_blobs"]["plugins/velvetos-workspace-skills/.codex-plugin/plugin.json"],
            "--verify-script-blob", dist5c["git_blobs"]["scripts/verify-bundle.ps1"],
            "--eval-score", str(eval5c["score"]),
            "--eval-max-score", str(eval5c["max_score"]),
            "--output", str(regenerated5c),
        ],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=90,
    )
    if proc.returncode != 0:
        fail("Stage 5C report regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()))
    if regenerated5c.read_bytes() != STAGE5C_REPORT.read_bytes():
        fail("Stage 5C workspace-distribution report is not reproducible")

root_agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
root_lines = len(root_agents_text.splitlines())
root_words = len(root_agents_text.split())
if root_lines > 80 or root_words > 1200:
    fail(f"Stage 5A root context budget exceeded: {root_lines} lines / {root_words} words")
for marker in ("REFERENCE_STUDIO:", "Sderot", "050-2517000", "PUBLIC_CURRENT_CTA", "VF_PUBLICATION_ROUTE_V1", "CREATIVE-TRANSFORMATION-LOCK.md", "BRAND-ASSET-LOCK.md", "PUBLICATION-PREP-EXECUTION.md", "FABRICATION-ROUTER.md", "Grok Bot quota failover", "LIVE-PACKET", "ORGANIC_GROWTH.md", "Instagram", "Gmail", "WhatsApp"):
    if marker in root_agents_text:
        fail(f"Stage 5A root domain leakage returned: {marker}")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
if manifest.get("status") != "mandatory" or manifest.get("preflightMode") != "fail_closed":
    fail("manifest is not mandatory fail-closed")
bundle = manifest.get("chatgptProjectBundle")
if not isinstance(bundle, dict):
    fail("chatgptProjectBundle binding missing")
for key in ("contractVersion", "revision", "bundleId", "authority", "assetManifest", "instructions"):
    if not bundle.get(key):
        fail(f"chatgptProjectBundle missing {key}")
if manifest.get("gateDocument") != "packages/velvetos/PROJECT-REQUEST-GATE.md":
    fail("gateDocument mismatch")
required_domains = {
    "creative_publication", "copywriting", "operations", "production",
    "sales_conversion", "finance", "research", "system_engineering", "instagram_action", "general_business"
}
if not required_domains.issubset(set(manifest.get("domains", {}))):
    fail("required domain coverage missing")

fast_path = manifest.get("fastPath")
if not isinstance(fast_path, dict) or fast_path.get("status") != "active":
    fail("Stage 4B fastPath contract missing/inactive")
if fast_path.get("receiptVisibility") != "internal_unless_true_blocker":
    fail("Stage 4B receipt visibility must stay internal unless a true blocker exists")
if set(fast_path.get("eligibleScopes") or []) != {"read_only", "local_routine", "internal_mutation"}:
    fail("Stage 4B fastPath eligible scope contract drift")
expected_full_triggers = {
    "external_mutation", "unknown_domain", "creative_or_publication",
    "commercial_or_spend", "rights_or_privacy", "destructive_or_permission",
    "physical_print", "authority_conflict", "stale_critical_evidence", "new_route",
}
if set(fast_path.get("fullPreflightTriggers") or []) != expected_full_triggers:
    fail("Stage 4B full-preflight trigger contract drift")
fast_profiles = fast_path.get("domainProfiles") or {}
if set(fast_profiles) != {"operations", "production", "research"}:
    fail("Stage 4B fastPath domain profiles must be exactly operations/production/research")
if len(fast_path.get("baselineAuthorities") or []) != 3:
    fail("Stage 4B minimal baseline must contain exactly three authority files")
for rel in fast_path.get("baselineAuthorities") or []:
    if not authority_reference_exists(rel):
        fail(f"Stage 4B fastPath baseline authority missing: {rel}")
for domain, profile in fast_profiles.items():
    if not isinstance(profile, dict) or not profile.get("packs") or not profile.get("authorities") or not profile.get("hardGates"):
        fail(f"Stage 4B fastPath profile incomplete: {domain}")
    for rel in profile.get("authorities") or []:
        if not authority_reference_exists(rel):
            fail(f"Stage 4B fastPath profile authority missing: {domain}:{rel}")
for field in ("request_scope", "preflight_mode", "full_preflight_triggers", "owner_surface", "local_instructions"):
    if field not in set(manifest.get("requiredReceiptFields") or []):
        fail(f"Project Request receipt field missing: {field}")

locality = manifest.get("instructionLocality") or {}
if locality.get("status") != "active" or locality.get("mode") != "root_plus_selected_domain":
    fail("Stage 5A instruction locality must be active root_plus_selected_domain")
if locality.get("rootGuide") != "AGENTS.md" or locality.get("warehouseDefault") != "off":
    fail("Stage 5A root guide / warehouse default drift")
if locality.get("unknownDomain") != "root_only_full_preflight":
    fail("Stage 5A unknown-domain locality drift")
domain_guides = locality.get("domainGuides") or {}
if set(domain_guides) != required_domains:
    fail("Stage 5A instruction locality must cover exactly the 10 routed domains")
for domain, guides in domain_guides.items():
    if not isinstance(guides, list) or len(guides) != 1:
        fail(f"Stage 5A domain {domain} must load exactly one primary local guide")
    rel = guides[0]
    if not isinstance(rel, str) or not rel.endswith("/AGENTS.md") or not (ROOT / rel).is_file():
        fail(f"Stage 5A local guide missing/invalid: {domain}:{rel}")
for needle in (
    "load root guide plus selected domain guide only",
    "do not preload unrelated domain guides or warehouse specialists",
    "local guides provide instructions/evidence only and never become external-effect authorities",
):
    if needle not in (locality.get("rules") or []):
        fail(f"Stage 5A instruction locality rule missing: {needle}")

resolved_bundle = resolve_project_bundle(ROOT, instance_id="velvet-factory", env={})
project_authority = ROOT / resolved_bundle.authority
asset_manifest = ROOT / resolved_bundle.asset_manifest
project_instructions = ROOT / resolved_bundle.instructions
visual_enforcement = ROOT / "packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json"
for path in (project_authority, asset_manifest, project_instructions, visual_enforcement):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
authority_text = project_authority.read_text(encoding="utf-8")
if "creative_execution_authorized: true" not in authority_text:
    fail("Project Authority missing creative execution authorization rule")
for needle in ("orientation label is allowed", "orientation itself adds useful information"):
    if needle not in authority_text:
        fail(f"Project Authority missing reference-aligned camera-label rule: {needle}")
for needle in ("intermediate base/staging visual handed off as if the requested post were complete", "creative_master"):
    if needle not in authority_text:
        fail(f"Project Authority missing first-pass continuity rule: {needle}")
for needle in ("creative_master_materialized=PASS", "Recreating the scene from the raw product source is not materialization"):
    if needle not in authority_text:
        fail(f"Project Authority missing creative-master materialization rule: {needle}")
asset_data = json.loads(asset_manifest.read_text(encoding="utf-8"))
expected_identity = (bundle["contractVersion"], str(bundle["revision"]), bundle["bundleId"])
actual_identity = (asset_data.get("contract_version"), str(asset_data.get("revision")), asset_data.get("bundle_id"))
if actual_identity != expected_identity:
    fail(f"Project asset manifest identity mismatch: expected {expected_identity}, got {actual_identity}")
authority_rows = [x for x in asset_data.get("assets", []) if x.get("filename") == "Velvet-Factory-Project-Authority-v6.txt"]
authority_bytes = project_authority.read_bytes()
authority_sha = hashlib.sha256(authority_bytes).hexdigest()
authority_lf_sha = hashlib.sha256(authority_bytes.replace(b"\r\n", b"\n")).hexdigest()
if len(authority_rows) != 1 or authority_rows[0].get("sha256") not in {authority_sha, authority_lf_sha}:
    fail(f"Project Authority bytes are not bound to the current asset manifest ({bundle['revision']})")
instructions_text = project_instructions.read_text(encoding="utf-8")
instructions_sha = hashlib.sha256(project_instructions.read_bytes()).hexdigest()
instructions_lf_sha = hashlib.sha256(project_instructions.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
instructions_row = asset_data.get("instructions")
if not isinstance(instructions_row, dict):
    fail("Project Instructions binding missing from asset manifest")
if instructions_row.get("sha256") not in {instructions_sha, instructions_lf_sha}:
    fail(f"Project Instructions bytes are not bound to the current asset manifest ({bundle['revision']})")
for needle in (f"Revision: {bundle['revision']}", bundle["bundleId"],
               f"Velvet-Factory-ASSET-MANIFEST-v{bundle['revision']}.json",
               "orientation itself adds useful information", "creative_master", "materialized to local path + SHA-256", "current-chat attachment ingest"):
    if needle not in instructions_text:
        fail(f"Project Instructions missing current binding/rule: {needle}")
route_doc = json.loads(visual_enforcement.read_text(encoding="utf-8"))
route = route_doc.get("publicationRoute", {})

current_refs = asset_data.get("current_references")
if not isinstance(current_refs, dict) or set(current_refs) != {
        "broad_visual", "editorial_layout", "current_direction", "multi_source_composition"}:
    fail("Revision 6.6.4 must bind exactly four current aesthetic references")
policy_refs = (route_doc.get("referenceRoleSeparationPolicy") or {}).get("aestheticReferences")
if not isinstance(policy_refs, list) or set(policy_refs) != set(current_refs.values()):
    fail("visual enforcement aesthetic references do not match Project asset manifest")
multi_policy = route_doc.get("multiSourceCompositionPolicy")
if not isinstance(multi_policy, dict) or multi_policy.get("samePhysicalProductSourceSet") is not True:
    fail("multi-source composition policy missing")
if set(multi_policy.get("insetProvenanceValues") or []) != {"SAME_FRAME_CROP", "ALTERNATE_VERIFIED_SOURCE"}:
    fail("multi-source inset provenance policy mismatch")
camera_labels = route_doc.get("cameraAngleLabelPolicy")
if not isinstance(camera_labels, dict):
    fail("cameraAngleLabelPolicy missing")
if camera_labels.get("blanketBan") is not False:
    fail("camera-angle labels must not be blanket-banned")
if camera_labels.get("orientationLabelsAllowedWhen") != "orientation_itself_adds_useful_information":
    fail("camera-angle label allowance does not match owner reference clarification")
if camera_labels.get("otherwise") != "describe_the_concrete_feature_the_view_reveals":
    fail("camera-angle label fallback must be feature-first copy")
continuity = route_doc.get("creativeContinuityPolicy")
if not isinstance(continuity, dict):
    fail("creativeContinuityPolicy missing")
if continuity.get("intermediateBaseVisualIsCompletion") is not False:
    fail("intermediate base visual must not count as publication completion")
if continuity.get("completeFirstResponseWhenToolsAndSourcesPermit") is not True:
    fail("first-response completion rule missing")
master_policy = continuity.get("creativeMaster") or {}
if master_policy.get("freezeSelectedMaster") is not True:
    fail("creative master freeze rule missing")
if master_policy.get("silentRawSourceRestartForbidden") is not True:
    fail("silent raw-source restart must be forbidden")
no_regression = continuity.get("noRegression") or {}
if no_regression.get("required") is not True or no_regression.get("weakerFinal") != "FAIL_TARGETED_REPAIR":
    fail("final-vs-master no-regression policy missing")
materialization = continuity.get("materialization") or {}
if materialization.get("planBeforeCreativeToolSelectionWhenDeterministicOverlayExpected") is not True:
    fail("creative-master materialization planning rule missing")
if materialization.get("requiredBeforeDeterministicOverlay") is not True:
    fail("creative-master materialization gate missing")
if materialization.get("localPathAndSha256Required") is not True or materialization.get("receiptRequired") is not True:
    fail("creative-master local identity/receipt rule missing")
if materialization.get("rawSourceRecreationCountsAsMaterialization") is not False:
    fail("raw-source recreation must not count as creative-master materialization")
if materialization.get("silentRawFallbackForbidden") is not True:
    fail("unmaterializable master must not silently fall back to raw source")
if materialization.get("bridge") != "scripts/vf_creative_master_bridge.py":
    fail("creative-master bridge binding mismatch")
ingest = route_doc.get("sourceIngestPolicy") or {}
if ingest.get("bridge") != "scripts/vf_source_ingest.py":
    fail("source-ingest bridge binding mismatch")
if ingest.get("currentChatAttachmentLocalIngestBeforeCreativePreflight") is not True:
    fail("chat attachment source ingest rule missing")
if ingest.get("externalInputRequiresExplicitCurrentRequestIntakeRoot") is not True:
    fail("source ingest must require current-request intake root")
if ingest.get("arbitraryFolderScanForbidden") is not True:
    fail("source ingest arbitrary-folder scan must be forbidden")
if ingest.get("unhashedFallbackForbidden") is not True:
    fail("source ingest unhashed fallback must be forbidden")
if ingest.get("chatLocalPreflight") != "scripts/vf_chat_cold_start_preflight.py":
    fail("chat-local preflight policy binding mismatch")
if ingest.get("remoteRepoPreflightMustNotReceiveChatLocalPaths") is not True:
    fail("remote preflight must not receive chat-local paths")
if ingest.get("chatLocalPreflightAuthorizesCreativeOnly") is not True or ingest.get("chatLocalPreflightNeverAuthorizesPublication") is not True:
    fail("chat-local preflight scope mismatch")
entrypoints = route.get("entrypoints", [])
required_entrypoints = {"packages/vfgrowth/STORIES.md", "packages/vfcopy/hq/templates/ig-stories.md"}
if not required_entrypoints.issubset(set(entrypoints)):
    fail("publicationRoute must govern Stories playbook + active story template")
patterns = route.get("deniedDirectivePatterns", [])
if not patterns:
    fail("publicationRoute must declare deniedDirectivePatterns")
legacy_raw = route.get("legacyDeniedToolSurfaces", [])
if not isinstance(legacy_raw, list) or not all(isinstance(x, str) for x in legacy_raw):
    fail("publicationRoute legacyDeniedToolSurfaces must be an array of strings")
legacy_denied = set(legacy_raw)
if set(entrypoints) & legacy_denied:
    fail("publicationRoute active entrypoints overlap legacy denied-tool surfaces")

def active_publication_text(text: str) -> str:
    out: list[str] = []
    skip_legacy_section = False
    for line in text.splitlines():
        if line.startswith("## LEGACY / provenance only"):
            skip_legacy_section = True
            continue
        if skip_legacy_section and line.startswith("## "):
            skip_legacy_section = False
        if skip_legacy_section or "LEGACY / provenance only" in line:
            continue
        out.append(line)
    return "\n".join(out)

for rel in entrypoints:
    path = ROOT / rel
    if not path.is_file():
        fail(f"publicationRoute entrypoint missing: {rel}")
    active = active_publication_text(path.read_text(encoding="utf-8"))
    for forbidden in patterns:
        if forbidden in active:
            fail(f"active publication entrypoint {rel} bypasses deniedTools via {forbidden!r}")

# Behavioral regression: even a hash-consistent stale Project Authority must fail closed.
sys.path.insert(0, str(ROOT / "scripts"))
import vf_project_preflight as project_preflight
import vf_publication_evidence as publication_evidence
if publication_evidence.REJECTED_PRODUCT_TRUTH_REFERENCE_SHA256 not in set(route.get("rejectedArtifactSha256", [])):
    fail("publicationRoute must deny the superseded Product Truth teaching-sheet identity")
if project_preflight.PROJECT_AUTHORITY != Path(resolved_bundle.authority):
    fail("active preflight Project Authority does not match chatgptProjectBundle")
if project_preflight.PROJECT_ASSET_MANIFEST != Path(resolved_bundle.asset_manifest):
    fail("active preflight asset manifest does not match chatgptProjectBundle")
if project_preflight.PROJECT_INSTRUCTIONS != Path(resolved_bundle.instructions):
    fail("active preflight Project Instructions do not match chatgptProjectBundle")
if project_preflight.CREATIVE_MASTER_BRIDGE != Path("scripts/vf_creative_master_bridge.py"):
    fail("active preflight creative-master bridge binding mismatch")
if project_preflight.SOURCE_INGEST_BRIDGE != Path("scripts/vf_source_ingest.py"):
    fail("active preflight source-ingest bridge binding mismatch")
if project_preflight.CHAT_LOCAL_PREFLIGHT != Path("scripts/vf_chat_cold_start_preflight.py"):
    fail("active preflight chat-local gate binding mismatch")
if not (ROOT / project_preflight.CHAT_LOCAL_PREFLIGHT).is_file():
    fail("chat-local preflight implementation missing")
runtime_rows = asset_data.get("chat_runtime")
if not isinstance(runtime_rows, list) or {x.get("repo_path") for x in runtime_rows if isinstance(x, dict)} != {
        "scripts/vf_source_ingest.py", "scripts/vf_chat_cold_start_preflight.py",
        "scripts/vf_media_integrity.py", "scripts/vf_media_limits.py", "scripts/vf_creative_master_bridge.py"}:
    fail("Project dependency-closed chat_runtime manifest binding mismatch")
if not (ROOT / project_preflight.SOURCE_INGEST_BRIDGE).is_file():
    fail("source-ingest bridge implementation missing")
if not (ROOT / project_preflight.CREATIVE_MASTER_BRIDGE).is_file():
    fail("creative-master bridge implementation missing")
if Path(publication_evidence.AUTHORITY) != Path(resolved_bundle.authority):
    fail("publication evidence Project Authority does not match chatgptProjectBundle")
if Path(publication_evidence.ASSETS) != Path(resolved_bundle.asset_manifest):
    fail("publication evidence asset manifest does not match chatgptProjectBundle")
expected_bundle_identity = (bundle["contractVersion"], str(bundle["revision"]), bundle["bundleId"])
if (project_preflight.PROJECT_CONTRACT_VERSION, project_preflight.PROJECT_REVISION,
        project_preflight.PROJECT_BUNDLE_ID) != expected_bundle_identity:
    fail("active preflight bundle identity does not match chatgptProjectBundle")
if (publication_evidence.PROJECT_CONTRACT_VERSION, publication_evidence.PROJECT_REVISION,
        publication_evidence.PROJECT_BUNDLE_ID) != expected_bundle_identity:
    fail("publication evidence bundle identity does not match chatgptProjectBundle")
if project_preflight.PROJECT_ASSET_MANIFEST_SHA256 != publication_evidence.ASSETS_SHA:
    fail("active preflight asset-manifest hash does not match publication evidence binding")
if project_preflight.project_binding_problems(creative=True):
    fail("current Project binding is inconsistent: " + "; ".join(project_preflight.project_binding_problems(creative=True)))
with tempfile.TemporaryDirectory(prefix="vf-project-binding-") as tmp_name:
    tmp = Path(tmp_name)
    for rel in (project_preflight.PROJECT_AUTHORITY, project_preflight.PROJECT_ASSET_MANIFEST,
                project_preflight.PROJECT_INSTRUCTIONS, project_preflight.VISUAL_ENFORCEMENT,
                project_preflight.CREATIVE_MASTER_BRIDGE, project_preflight.SOURCE_INGEST_BRIDGE,
                project_preflight.CHAT_LOCAL_PREFLIGHT, project_preflight.PROJECT_GATE):
        target = tmp / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    stale = tmp / project_preflight.PROJECT_AUTHORITY
    stale.write_text(stale.read_text(encoding="utf-8").replace("creative_execution_authorized: true", "creative_execution_authorized: false"), encoding="utf-8")
    stale_sha = hashlib.sha256(stale.read_bytes()).hexdigest()
    am = json.loads((tmp / project_preflight.PROJECT_ASSET_MANIFEST).read_text(encoding="utf-8"))
    for row in am["assets"]:
        if row.get("filename") == "Velvet-Factory-Project-Authority-v6.txt":
            row["sha256"] = stale_sha
            row["bytes"] = stale.stat().st_size
    (tmp / project_preflight.PROJECT_ASSET_MANIFEST).write_text(json.dumps(am, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    problems = project_preflight.project_binding_problems(tmp, creative=True)
    if not problems:
        fail("hash-consistent stale Project Authority did not fail closed")
    (tmp / project_preflight.PROJECT_ASSET_MANIFEST).write_text("{broken", encoding="utf-8")
    problems = project_preflight.project_binding_problems(tmp, creative=True)
    if not problems or not any("cannot be decoded" in problem for problem in problems):
        fail("malformed Project asset manifest did not fail closed")
    shutil.copyfile(ROOT / project_preflight.PROJECT_AUTHORITY, tmp / project_preflight.PROJECT_AUTHORITY)
    shutil.copyfile(ROOT / project_preflight.PROJECT_ASSET_MANIFEST, tmp / project_preflight.PROJECT_ASSET_MANIFEST)
    am = json.loads((tmp / project_preflight.PROJECT_ASSET_MANIFEST).read_text(encoding="utf-8"))
    am["current_references"]["current_direction"] = am["product_truth"]["guide"]
    (tmp / project_preflight.PROJECT_ASSET_MANIFEST).write_text(
        json.dumps(am, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    problems = project_preflight.project_binding_problems(tmp, creative=True)
    if not problems or not any("asset manifest hash" in problem for problem in problems):
        fail(f"tampered v{bundle['revision']} asset manifest did not fail closed before creative execution")
    shutil.copyfile(ROOT / project_preflight.PROJECT_ASSET_MANIFEST, tmp / project_preflight.PROJECT_ASSET_MANIFEST)
    (tmp / project_preflight.VISUAL_ENFORCEMENT).write_text("[]", encoding="utf-8")
    problems = project_preflight.project_binding_problems(tmp, creative=True)
    if not problems or not any("top-level objects" in problem for problem in problems):
        fail("wrong-shape visual enforcement JSON did not fail closed")
    if project_preflight.project_binding_problems(tmp, creative=False):
        fail("creative visual enforcement drift must not block non-creative domains")
    shutil.copyfile(ROOT / project_preflight.VISUAL_ENFORCEMENT, tmp / project_preflight.VISUAL_ENFORCEMENT)
    am = json.loads((tmp / project_preflight.PROJECT_ASSET_MANIFEST).read_text(encoding="utf-8"))
    am["assets"] = None
    (tmp / project_preflight.PROJECT_ASSET_MANIFEST).write_text(json.dumps(am), encoding="utf-8")
    problems = project_preflight.project_binding_problems(tmp, creative=False)
    if not problems or not any("array of objects" in problem for problem in problems):
        fail("nested malformed asset list did not fail closed")
    shutil.copyfile(ROOT / project_preflight.PROJECT_ASSET_MANIFEST, tmp / project_preflight.PROJECT_ASSET_MANIFEST)
    policy = json.loads((tmp / project_preflight.VISUAL_ENFORCEMENT).read_text(encoding="utf-8"))
    policy["publicationRoute"]["deniedTools"] = None
    (tmp / project_preflight.VISUAL_ENFORCEMENT).write_text(json.dumps(policy), encoding="utf-8")
    problems = project_preflight.project_binding_problems(tmp, creative=True)
    if not problems or not any("deniedTools must be an array" in problem for problem in problems):
        fail("malformed deniedTools did not fail closed")

all_paths = list(manifest.get("baselineAuthorities", []))
all_paths.append((manifest.get("instructionLocality") or {}).get("rootGuide", "AGENTS.md"))
for guides in ((manifest.get("instructionLocality") or {}).get("domainGuides") or {}).values():
    all_paths.extend(guides or [])
for cfg in manifest["domains"].values():
    all_paths.extend(cfg.get("authorities", []))
missing = sorted({p for p in all_paths if not authority_reference_exists(p)})
if missing:
    fail("missing authority path(s): " + ", ".join(missing))

gate = GATE.read_text(encoding="utf-8")
for needle in ("No substantive work starts", "Project Instructions", "route first", "exact-final"):
    if needle.casefold() not in gate.casefold():
        fail(f"gate document missing {needle}")

for rel in ("AGENTS.md", "instances/velvet-factory/AGENTS.md", "instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc"):
    body = (ROOT / rel).read_text(encoding="utf-8")
    if "PROJECT-REQUEST-GATE.md" not in body or "PROJECT-AUTHORITY-MANIFEST.json" not in body:
        fail(f"{rel} not bound to project request gate")
expected_local_guide = {
    domain: guides[0] for domain, guides in domain_guides.items()
}
for sample, expected in (
    ("תכין פוסט לפרסום", "creative_publication"),
    ("caption", "creative_publication"),
    ("כתוב לי כיתוב", "creative_publication"),
    ("write social media copy for our feed", "creative_publication"),
    ("קופי לאינסטגרם", "creative_publication"),
    ("write a social post", "creative_publication"),
    ("make a public post", "creative_publication"),
    ("create a Story for the new product", "creative_publication"),
    ("write an Instagram caption", "creative_publication"),
    ("copy customer feedback into the owner brief", "copywriting"),
    ("create a customer success story for the owner brief", "operations"),
    ("עדכן סטטוס הזמנה", "operations"),
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    expected_code = 2 if expected == "creative_publication" else 0
    if proc.returncode != expected_code:
        fail(f"preflight CLI failed for sample {sample}: {proc.stderr or proc.stdout}")
    receipt = json.loads(proc.stdout)
    expected_state = "BLOCKED" if expected == "creative_publication" else "PASS"
    if receipt.get("project_preflight") != expected_state or expected not in receipt.get("request_domain", []):
        fail(f"preflight CLI did not route {sample} to {expected}")
    if expected == "creative_publication" and receipt.get("creative_execution_authorized") is not False:
        fail("creative request without exact production evidence must not authorize creative tools")
    if expected != "creative_publication" and receipt.get("creative_execution_authorized") is not False:
        fail("non-creative request must not accidentally authorize creative tools")
    routed_domains = [d for d in receipt.get("request_domain", []) if d in expected_local_guide]
    expected_local = ["AGENTS.md"] + list(dict.fromkeys(expected_local_guide[d] for d in routed_domains))
    if receipt.get("local_instructions") != expected_local:
        fail(f"Stage 5A locality mismatch for {sample}: expected {expected_local}, got {receipt.get('local_instructions')}")

# Stage 5A negative control: core/system work must not preload creative/fabrication guides.
system_proc = subprocess.run(
    [sys.executable, str(CLI), "--domain", "system_engineering", "--text", "update VelvetOS core policy registry"],
    cwd=ROOT, text=True, capture_output=True,
)
if system_proc.returncode != 0:
    fail(f"system-engineering locality sample failed: {system_proc.stderr or system_proc.stdout}")
system_receipt = json.loads(system_proc.stdout)
if "system_engineering" not in system_receipt.get("request_domain", []):
    fail("system-engineering locality sample did not route to system_engineering")
if system_receipt.get("local_instructions") != ["AGENTS.md", "packages/velvetos/AGENTS.md"]:
    fail(f"system-engineering locality should load root + Core guide only: {system_receipt.get('local_instructions')}")
for forbidden_guide in ("packages/vfom/AGENTS.md", "packages/vfprod/AGENTS.md", "packages/vfharness/devtools/creative-craft/AGENTS.md"):
    if forbidden_guide in system_receipt.get("local_instructions", []):
        fail(f"system-engineering locality preloaded unrelated guide {forbidden_guide}")

unknown_proc = subprocess.run(
    [sys.executable, str(CLI), "--domain", "not-a-domain", "--text", "unknown route"],
    cwd=ROOT, text=True, capture_output=True,
)
if unknown_proc.returncode != 2:
    fail("unknown-domain locality control must fail closed")
unknown_receipt = json.loads(unknown_proc.stdout)
if unknown_receipt.get("local_instructions") != ["AGENTS.md"] or unknown_receipt.get("preflight_mode") != "FULL":
    fail("unknown-domain locality must load root only and stay FULL")

# Instagram drafting stays on production evidence; publish verbs alone own instagram_action.
ig_draft = subprocess.run(
    [sys.executable, str(CLI), "--text", "write an Instagram caption"],
    cwd=ROOT, text=True, capture_output=True,
)
ig_receipt = json.loads(ig_draft.stdout)
if "instagram_action" in ig_receipt.get("request_domain", []):
    fail("Instagram caption drafting must not route as instagram_action/delivery")
if ig_receipt.get("publication_evidence_phase") != "production":
    fail("Instagram caption drafting must stay on production evidence phase")
ig_pub = subprocess.run(
    [sys.executable, str(CLI), "--text", "publish to Instagram"],
    cwd=ROOT, text=True, capture_output=True,
)
if "instagram_action" not in json.loads(ig_pub.stdout).get("request_domain", []):
    fail("explicit Instagram publish must still route as instagram_action")
for sample in (
    "post this on Instagram",
    "upload this to Instagram",
    "share this on Instagram",
    "put this on Instagram",
    "send this to Instagram",
    "push this live on Instagram",
    "push it live",
    "make this live on Instagram",
    "take this live",
    "put this live on Instagram",
    "publish this live",
    "add this to Instagram",
    "העלה את זה לאוויר באינסטגרם",
    "תעלה את זה לאוויר",
    "תפרסם את זה עכשיו",
    "תעלה את הפוסט לאינסטגרם",
    "תפרסם את זה באינסטגרם",
    "שתף את זה באינסטגרם",
    "delete this from Instagram",
    "delete Instagram media 123; set confirm_irreversible=true for account velvets_cloud",
    "remove this from Instagram",
    "delete the Instagram post",
    "remove that post from Instagram",
    "delete this Reel",
    "remove this Story",
    "take this post down",
    "archive this Instagram post",
    "מחק את הפוסט באינסטגרם",
    "תוריד את הפוסט",
    "תמחק את הריל",
    "הסר את הסטורי",
    "תוריד את זה מהאינסטגרם",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" not in receipt.get("request_domain", []):
        fail(f"Instagram delivery/destructive intent must route as instagram_action: {sample}")
    if receipt.get("publication_evidence_phase") != "delivery":
        fail(f"Instagram action must require delivery evidence: {sample}")
for sample in (
    "analyze this Instagram post",
    "share the Instagram analytics with the owner",
    "send the Instagram analytics to the owner",
    "schedule a meeting about Instagram",
    "prepare a post",
    "תכין פוסט",
    "תכין לפרסום",
    "write an Instagram caption",
    "should we delete this post?",
    "האם כדאי למחוק את הפוסט?",
    "write instructions for deleting a post",
    "how do I delete an Instagram post",
    "what is an Instagram post?",
    "how should an Instagram post be structured?",
    "should we create an Instagram post?",
    "מה זה פוסט באינסטגרם?",
    "האם כדאי להכין פוסט לאינסטגרם?",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" in receipt.get("request_domain", []):
        fail(f"prep/advisory/office Instagram text must not route as instagram_action: {sample}")
for sample in (
    "create an Instagram post",
    "draft an Instagram post",
    "design an Instagram post",
    "make an Instagram post",
    "prepare an Instagram post",
    "create a post for Instagram",
    "draft a post for Instagram",
    "design a post for Instagram",
    "תכין פוסט לאינסטגרם",
    "תיצור פוסט לאינסטגרם",
    "תעצב פוסט לאינסטגרם",
    "תכין לי פוסט באינסטגרם",
    "תכין פרסום לאינסטגרם",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "creative_publication" not in receipt.get("request_domain", []):
        fail(f"Instagram-post draft/prep must route creative_publication: {sample}")
    if "instagram_action" in receipt.get("request_domain", []):
        fail(f"Instagram-post draft/prep must not route as instagram_action: {sample}")
    if receipt.get("project_preflight") != "BLOCKED":
        fail(f"Instagram-post draft without Creative Manifest must BLOCK: {sample}")
    if receipt.get("publication_evidence_phase") != "production":
        fail(f"Instagram-post draft must stay on production evidence (not delivery): {sample}")
    if receipt.get("creative_execution_authorized") is not False:
        fail(f"Instagram-post draft without evidence must keep creative_execution_authorized=false: {sample}")
for sample in (
    "what is an Instagram post?",
    "how should an Instagram post be structured?",
    "should we create an Instagram post?",
    "מה זה פוסט באינסטגרם?",
    "האם כדאי להכין פוסט לאינסטגרם?",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "creative_publication" in receipt.get("request_domain", []):
        fail(f"informational Instagram-post discussion must not route creative_publication: {sample}")
    if "instagram_action" in receipt.get("request_domain", []):
        fail(f"informational Instagram-post discussion must not route instagram_action: {sample}")
# Mixed advisory + real Instagram mutation: keep strictest action route (delivery).
for sample in (
    "Explain how you chose the image, then publish it to Instagram",
    "Tell me why this caption works, then post it",
    "Review this design and then push it live",
    "Explain the layout, then share it on Instagram",
    "Tell me whether the post is good, then publish it",
    "Summarize the caption and then delete the post",
    "Explain what happened, then remove the Reel",
    "Review the Story, then archive it",
    "תסביר למה בחרת בתמונה ואז תפרסם אותה באינסטגרם",
    "תעבור על העיצוב ואז תעלה אותו",
    "תסביר את הכיתוב ואז תפרסם",
    "תסכם לי ואז תמחק את הפוסט",
    "תבדוק את הסטורי ואז תוריד אותו",
    "תסביר ואז תארכב את הפוסט",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" not in receipt.get("request_domain", []):
        fail(f"mixed advisory+action must keep instagram_action: {sample}")
    if receipt.get("publication_evidence_phase") != "delivery":
        fail(f"mixed advisory+action must require delivery evidence: {sample}")
    if receipt.get("project_preflight") != "BLOCKED":
        fail(f"mixed advisory+action without delivery evidence must BLOCK: {sample}")
# Pure advisory / howto with mutation vocabulary but no imperative action clause.
for sample in (
    "Explain how publishing to Instagram works",
    "Should we publish this?",
    "Tell me whether I should delete this post",
    "Explain how to delete an Instagram post",
    "What happens if I archive a Reel?",
    "האם כדאי לפרסם את זה?",
    "איך מוחקים פוסט באינסטגרם?",
    "האם כדאי למחוק את הסטורי?",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" in receipt.get("request_domain", []):
        fail(f"pure advisory must not route instagram_action: {sample}")

# Creative prep + advisory but no live action: creative_publication where applicable, never instagram_action.
for sample, expect_creative in (
    ("design an Instagram post for the launch", True),
    ("Help me refine this Instagram caption draft", True),
    ("Explain how to design an Instagram post", False),
    ("Should we create an Instagram post for the launch?", False),
    ("תכין פוסט לאינסטגרם לאירוע", True),
    ("האם כדאי להכין פוסט לאינסטגרם?", False),
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" in receipt.get("request_domain", []):
        fail(f"creative-prep/advisory without live action must not route instagram_action: {sample}")
    has_creative = "creative_publication" in receipt.get("request_domain", [])
    if expect_creative and not has_creative:
        fail(f"creative prep without live action must route creative_publication: {sample}")
    if not expect_creative and has_creative:
        fail(f"advisory without live action must not route creative_publication: {sample}")
for sample in ("publish this post",):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "creative_publication" not in receipt.get("request_domain", []):
        fail(f"bare English publish/post must route creative_publication: {sample}")
    if "instagram_action" in receipt.get("request_domain", []):
        fail(f"bare publish/post without IG destination must not be instagram_action: {sample}")
    if receipt.get("project_preflight") != "BLOCKED":
        fail(f"bare publish/post must BLOCK without Creative Manifest: {sample}")

# Canonical Instagram mutation MCP tool ids (from CAPABILITIES + core-mcp write binding)
# with execution intent must route instagram_action + delivery fail-closed.
for sample in (
    "Use Instagram publish_image with this asset",
    "Run publish_story",
    "Instagram delete_media 12345",
    "Call the Instagram publish tool",
    "use delete_media on this post",
    "Use publish_carousel now",
    "Run publish_reel",
    "Use reply_to_comment on this thread",
    "השתמש ב-publish_image עם הנכס הזה",
    "תריץ publish_story",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" not in receipt.get("request_domain", []):
        fail(f"mutation-tool execution must route instagram_action: {sample}")
    if receipt.get("publication_evidence_phase") != "delivery":
        fail(f"mutation-tool execution must require delivery evidence: {sample}")
    if receipt.get("project_preflight") != "BLOCKED":
        fail(f"mutation-tool execution without delivery evidence must BLOCK: {sample}")
# Mixed advisory + mutation-tool execution keeps strictest action route.
for sample in (
    "Explain this image and then use publish_image",
    "Review the caption, then run publish_story",
    "תסביר את התמונה ואז תשתמש ב-publish_image",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" not in receipt.get("request_domain", []):
        fail(f"mixed advisory+mutation-tool must keep instagram_action: {sample}")
    if receipt.get("publication_evidence_phase") != "delivery":
        fail(f"mixed advisory+mutation-tool must require delivery evidence: {sample}")
    if receipt.get("project_preflight") != "BLOCKED":
        fail(f"mixed advisory+mutation-tool without delivery evidence must BLOCK: {sample}")
# Pure informational / docs about mutation tool ids stay non-action.
for sample in (
    "Tell me how publish_image works",
    "Should we use publish_story?",
    "Explain delete_media",
    "what does publish_image do?",
    "compare publish_image and publish_story",
    "documentation for publish_carousel",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" in receipt.get("request_domain", []):
        fail(f"tool documentation/advisory must not route instagram_action: {sample}")
# Read-only Instagram tool ids must not action-gate merely by being Instagram tools.
for sample in (
    "Use list_media",
    "Run get_profile",
    "Use Instagram get_account_insights",
    "Call healthcheck",
    "Run graph_mutation_matrix",
    "Use get_media on this id",
):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    receipt = json.loads(proc.stdout)
    if "instagram_action" in receipt.get("request_domain", []):
        fail(f"read-only Instagram tool must not route instagram_action: {sample}")


# Stage 4B fast-path behavioral contract.
def _stage4b_receipt(sample: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(CLI), "--text", sample],
        cwd=ROOT, text=True, capture_output=True,
    )
    try:
        receipt = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        fail(f"Stage 4B preflight returned non-JSON for {sample!r}: {exc}")
    return receipt


stage4b_cases = (
    ("Prepare an Instagram carousel", "creative_publication", "local_routine", "FULL", "BLOCKED"),
    ("Reply to this Gmail thread", "operations", "external_mutation", "FULL", "PASS"),
    ("Send this email to the customer", "operations", "external_mutation", "FULL", "PASS"),
    ("Prepare the owner morning brief", "operations", "internal_mutation", "FAST_PATH", "PASS"),
    ("Save this internal artifact to Google Drive", "operations", "external_mutation", "FULL", "PASS"),
    ("Launch Maya for this modeling task", "production", "local_routine", "FAST_PATH", "PASS"),
    ("Model this part in Maya", "production", "local_routine", "FAST_PATH", "PASS"),
    ("Inspect this CAD model read only", "production", "read_only", "FAST_PATH", "PASS"),
    ("Build a printable CAD model from these verified dimensions", "production", "local_routine", "FAST_PATH", "PASS"),
    ("Research the latest update for this tool", "research", "read_only", "FAST_PATH", "PASS"),
    ("Update internal operational status", "operations", "internal_mutation", "FAST_PATH", "PASS"),
)
stage4b_receipts: dict[str, dict] = {}
for sample, expected_domain, expected_scope, expected_mode, expected_state in stage4b_cases:
    receipt = _stage4b_receipt(sample)
    stage4b_receipts[sample] = receipt
    if expected_domain not in receipt.get("request_domain", []):
        fail(f"Stage 4B route mismatch for {sample}: {receipt.get('request_domain')}")
    if receipt.get("request_scope") != expected_scope:
        fail(f"Stage 4B scope mismatch for {sample}: {receipt.get('request_scope')}")
    if receipt.get("preflight_mode") != expected_mode:
        fail(f"Stage 4B mode mismatch for {sample}: {receipt.get('preflight_mode')}")
    if receipt.get("project_preflight") != expected_state:
        fail(f"Stage 4B state mismatch for {sample}: {receipt.get('project_preflight')}")
    if receipt.get("owner_surface") != "internal_unless_true_blocker":
        fail(f"Stage 4B receipt leaked to owner surface for {sample}")
    for field in manifest["requiredReceiptFields"]:
        if field not in receipt:
            fail(f"Stage 4B receipt missing {field} for {sample}")

gmail_reply = stage4b_receipts["Reply to this Gmail thread"]
if gmail_reply.get("full_preflight_triggers") != ["external_mutation"] or "Gmail.reply" not in gmail_reply.get("required_tools", []):
    fail("Stage 4B Gmail reply must remain FULL external mutation with Gmail.reply tool route")
gmail_send = stage4b_receipts["Send this email to the customer"]
if gmail_send.get("full_preflight_triggers") != ["external_mutation"] or "Gmail.send_message" not in gmail_send.get("required_tools", []):
    fail("Stage 4B Gmail send must remain FULL external mutation with Gmail.send_message tool route")
drive = stage4b_receipts["Save this internal artifact to Google Drive"]
if drive.get("full_preflight_triggers") != ["external_mutation"] or "Google-drive.create_file" not in drive.get("required_tools", []):
    fail("Stage 4B Drive write must remain FULL external mutation with create-file tool route")

owner_brief = stage4b_receipts["Prepare the owner morning brief"]
if len(owner_brief.get("required_sources", [])) != 5 or owner_brief.get("routed_packs") != ["vfops"]:
    fail("Stage 4B owner brief fast path must reduce to 5 sources / vfops")
if "sync_evidence" in owner_brief.get("hard_gates", []):
    fail("Stage 4B owner brief must not pay external sync gate before a delivery action exists")

maya_launch = stage4b_receipts["Launch Maya for this modeling task"]
maya_task = stage4b_receipts["Model this part in Maya"]
for receipt in (maya_launch, maya_task):
    if len(receipt.get("required_sources", [])) != 6:
        fail("Stage 4B Maya fast path must resolve exactly 6 sources")
    if receipt.get("hard_gates") != ["fabrication_tool_route", "specialized_skill_instructions"]:
        fail(f"Stage 4B Maya fast path has unrelated gates: {receipt.get('hard_gates')}")
    if "creative-craft:maya" not in receipt.get("required_tools", []):
        fail("Stage 4B Maya fast path missing canonical Creative Craft route")

cad_read = stage4b_receipts["Inspect this CAD model read only"]
cad_build = stage4b_receipts["Build a printable CAD model from these verified dimensions"]
for forbidden in ("verified_specs", "no_printer_control", "no_invented_price", "print_authority"):
    if forbidden in cad_read.get("hard_gates", []):
        fail(f"Stage 4B CAD read-only retained unrelated gate: {forbidden}")
if "verified_specs" not in cad_build.get("hard_gates", []):
    fail("Stage 4B CAD build must retain verified_specs")
for forbidden in ("no_printer_control", "no_invented_price", "print_authority"):
    if forbidden in cad_build.get("hard_gates", []):
        fail(f"Stage 4B CAD artifact build must not pay physical-print/commercial gate: {forbidden}")
if "scripts/vf_fabrication_router.py" not in cad_build.get("required_tools", []):
    fail("Stage 4B CAD build missing canonical Fabrication Router")

research_fast = stage4b_receipts["Research the latest update for this tool"]
if len(research_fast.get("required_sources", [])) != 4 or research_fast.get("required_tools") != ["WebSearch"]:
    fail("Stage 4B research fast path must reduce to 4 sources and canonical WebSearch route")
internal_status = stage4b_receipts["Update internal operational status"]
if len(internal_status.get("required_sources", [])) != 5 or "office/control-plane" not in internal_status.get("required_tools", []):
    fail("Stage 4B internal-status fast path must reduce to 5 sources and canonical Office route")

carousel = stage4b_receipts["Prepare an Instagram carousel"]
if carousel.get("preflight_mode") != "FULL" or "creative_or_publication" not in carousel.get("full_preflight_triggers", []):
    fail("Stage 4B carousel must fix under-classification without weakening creative evidence")

# High-risk/ambiguous negative controls never enter FAST_PATH.
full_controls = (
    ("Set the customer price in ₪", "commercial_or_spend"),
    ("Purchase a new subscription for this tool", "commercial_or_spend"),
    ("Delete this internal file", "destructive_or_permission"),
    ("Change access permission on this file", "destructive_or_permission"),
    ("Use this private customer data in the artifact", "rights_or_privacy"),
    ("Send this STL to the printer and start printing", "physical_print"),
    ("Summarize this", "unknown_domain"),
)
for sample, required_trigger in full_controls:
    receipt = _stage4b_receipt(sample)
    if receipt.get("preflight_mode") != "FULL":
        fail(f"Stage 4B high-risk/unknown request incorrectly entered FAST_PATH: {sample}")
    if required_trigger not in receipt.get("full_preflight_triggers", []):
        fail(f"Stage 4B FULL trigger {required_trigger} missing for {sample}")

print(f"OK project-request-gate domains={len(manifest['domains'])} authority_paths={len(set(all_paths))} creative_without_evidence=BLOCKED creative_tool_authorization=fail_closed stage4b_fast_path=PASS")
