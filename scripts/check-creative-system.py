#!/usr/bin/env python3
"""Validate Velvet creative specialist + manifest architecture. No network. No send."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VFOM = ROOT / "packages" / "vfom"
FOUNDRY = VFOM / "FOUNDRY.json"
STAGE6B_REPORT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6b-creative-readiness.json"
STAGE6B_GENERATOR = ROOT / "scripts" / "generate-stage6b-creative-readiness-report.py"
INSTANCE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
CONTENT_SPRINT = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"
IG_MUSIC_SKILL = ROOT / ".cursor" / "skills" / "vf-ig-music" / "SKILL.md"
MUSIC_PLAYBOOK = ROOT / "packages" / "vfresearch" / "MUSIC.md"
VFCOPY_ROUTER = ROOT / ".cursor" / "skills" / "vf-hebrew-copy" / "SKILL.md"
VFCOPY_AUTHORITY = ROOT / "packages" / "vfcopy" / "skills" / "velvet-hebrew-copy" / "SKILL.md"
VFCOPY_PIPELINE = ROOT / "packages" / "vfcopy" / "skills" / "velvet-hebrew-copy" / "PIPELINE.md"
READER_FIRST = ROOT / "packages" / "vfcopy" / "hq" / "reader-first-he.md"
AI_TELLS = ROOT / "packages" / "vfcopy" / "hq" / "ai-tells-he.md"
CREATIVE_CRAFT_REGISTRY = ROOT / "packages" / "vfharness" / "devtools" / "creative-craft" / "creative-craft-registry.json"
RESOLVE_SAFE_SERVER = ROOT / "packages" / "vfharness" / "devtools" / "creative-tools" / "ResolveSafeServer.py"
SPECIALISTS = {
    "creativeDirector": ROOT / ".cursor" / "skills" / "velvet-creative-director" / "SKILL.md",
    "brandGuardian": ROOT / ".cursor" / "skills" / "velvet-brand-guardian" / "SKILL.md",
    "mediaLibrarian": ROOT / ".cursor" / "skills" / "velvet-media-librarian" / "SKILL.md",
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def must_contain(path: Path, needles: tuple[str, ...]) -> None:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")


def load_literal_assignment(path: Path, name: str):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError) as exc:
                fail(f"{path.relative_to(ROOT)} {name} must remain literal: {exc}")
    fail(f"{path.relative_to(ROOT)} missing literal assignment {name}")


def main() -> None:
    foundry = load_json(VFOM / "FOUNDRY.json")
    if foundry.get("version", 0) < 2:
        fail("FOUNDRY version must include creative-system MVP")
    manifest_policy = foundry.get("creativeManifest") or {}
    if manifest_policy.get("enabled") is not True:
        fail("Creative Manifest must be enabled")
    if manifest_policy.get("notASecondStateMachine") is not True or manifest_policy.get("notAMediaCatalog") is not True:
        fail("Creative Manifest must not become a second state machine/catalog")
    for key in (
        "coordinationOnly", "notAClaimAuthority", "notApprovalDatabase",
        "cannotAuthorizeExternalEffects", "statusIsEvidenceProjection", "productTruthAuthorityHigher",
    ):
        if manifest_policy.get(key) is not True:
            fail(f"Creative Manifest Stage 6B boundary missing: {key}")
    if manifest_policy.get("policyDecisionSource") != "packages/velvetos/policy/policy-registry.json":
        fail("Creative Manifest policy-decision source drift")
    if "never creates that state" not in str(manifest_policy.get("rule", "")):
        fail("Creative Manifest must state that status writes cannot mint authorization")

    quality = foundry.get("creativeQualitySystem") or {}
    expected_quality_specialists = [
        ".cursor/skills/vf-cad-design-craft/SKILL.md",
        ".cursor/skills/vf-dcc-modeling-craft/SKILL.md",
        ".cursor/skills/vf-material-lookdev/SKILL.md",
        ".cursor/skills/vf-product-visualization-craft/SKILL.md",
        ".cursor/skills/vf-post-production-craft/SKILL.md",
        ".cursor/skills/vf-vfx-compositing-craft/SKILL.md",
        ".cursor/skills/vf-image-design-craft/SKILL.md",
        ".cursor/skills/vf-technical-illustration-craft/SKILL.md",
    ]
    if quality.get("enabled") is not True or quality.get("version") != "2.0.0":
        fail("Creative Craft quality system must be active at 2.0.0")
    if quality.get("role") != "authoring_and_quality_system_not_policy_hierarchy":
        fail("Creative Craft must remain a quality system, not a policy hierarchy")
    if quality.get("router") != "packages/vfharness/devtools/creative-craft/skill/SKILL.md":
        fail("Creative Craft quality router binding drift")
    if quality.get("specialists") != expected_quality_specialists:
        fail("Creative Craft quality specialist set drift")
    if quality.get("produceCritiqueTargetedRefine") != "internal" or quality.get("ordinaryAestheticChoice") != "office":
        fail("Creative Craft ordinary produce/critique/refine choices must stay internal")
    if quality.get("qualityFailure") != "targeted_auto_repair_first" or quality.get("ownerEscalation") != "exception-only":
        fail("Creative Craft quality/escalation contract drift")
    for key in ("mayAuthorizeExternalEffects", "mayOverrideProductTruth", "mayCreatePolicyHierarchy"):
        if quality.get(key) is not False:
            fail(f"Creative Craft must keep {key}=false")
    if quality.get("manifestWritesAreEvidenceOnly") is not True or quality.get("completionRequiresExactFinalQa") is not True:
        fail("Creative Craft evidence/final-QA boundary drift")
    if quality.get("productTruthAuthority") != "higher_than_aesthetic_and_quality_system":
        fail("Product Truth must remain higher authority than the creative quality system")

    standing = foundry.get("ownerApprovedVisualStandard") or {}
    if standing.get("approvalScope") != "standing_visual_standard_not_per_job_owner_approval" or standing.get("perJobOwnerApprovalRequired") is not False:
        fail("owner-approved visual standard must remain standing authority, not per-job approval")

    human = foundry.get("humanSurface") or {}
    if human.get("mode") != "exception-only" or human.get("routineCreativeChoice") != "office" or human.get("ordinaryAestheticChoice") != "office":
        fail("ordinary aesthetic decisions must stay inside the office")
    if human.get("ownerApprovalForAestheticChoice") is not False or human.get("ownerApprovalForRoutineQualityRepair") is not False:
        fail("routine aesthetics/quality repair must not require owner approval")

    audio = foundry.get("audioPolicy") or {}
    if audio.get("requiredForVideo") is not True:
        fail("FOUNDRY audioPolicy.requiredForVideo must be true")
    if audio.get("defaultSilence") != "fail" or audio.get("nearSilent") != "fail":
        fail("FOUNDRY must fail accidental silence and near-silence")
    if audio.get("intentionalSilenceRequiresReason") is not True:
        fail("intentional silence must require a documented reason")
    required_audio_checks = {"stream_presence", "loudness", "sync", "story_fit"}
    if not required_audio_checks.issubset(set(audio.get("checks") or [])):
        fail("FOUNDRY audioPolicy missing required audio checks")
    if audio.get("skill") != ".cursor/skills/vf-ig-music/SKILL.md":
        fail("FOUNDRY audioPolicy must bind vf-ig-music skill")

    visual_copy = foundry.get("visualCopyPolicy") or {}
    if visual_copy.get("requiredForHebrewVisualText") is not True:
        fail("FOUNDRY visualCopyPolicy.requiredForHebrewVisualText must be true")
    if visual_copy.get("noTextBaselineRequired") is not True:
        fail("visual-copy gate must compare against NO_TEXT")
    if visual_copy.get("defaultWhenTextAddsNoValue") != "NO_TEXT":
        fail("visual-copy default must be NO_TEXT when copy adds no value")
    if visual_copy.get("skill") != ".cursor/skills/vf-hebrew-copy/SKILL.md":
        fail("visualCopyPolicy must bind vf-hebrew-copy router")
    if visual_copy.get("authority") != "packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md":
        fail("visualCopyPolicy must bind canonical Hebrew-copy authority")
    if visual_copy.get("readerFirst") != "packages/vfcopy/hq/reader-first-he.md":
        fail("visualCopyPolicy must bind reader-first")
    if visual_copy.get("humanizer") != "packages/vfcopy/hq/ai-tells-he.md":
        fail("visualCopyPolicy must bind Humanizer/AI-tells")
    if visual_copy.get("candidateMin") != 3 or visual_copy.get("candidateMax") != 5:
        fail("visual-copy gate must use 3-5 text candidates")

    rights = foundry.get("rightsPolicy") or {}
    if rights.get("modelLicenseDefault") != "not-a-showcase-publish-gate":
        fail("showcase model-license policy must not be a blanket publish gate")

    schema = load_json(VFOM / "CREATIVE-MANIFEST.schema.json")
    schema_description = str(schema.get("description", ""))
    if "not an approval database" not in schema_description or "not" not in schema_description or "Product Truth" not in schema_description:
        fail("Creative Manifest schema must declare coordination/evidence authority boundary")
    required = set(schema.get("required") or [])
    needed = {"jobId", "format", "status", "sourceEvidence", "visualStandard", "concept", "hook", "shots", "edit", "visualCopy", "cover", "qa"}
    if not needed.issubset(required):
        fail(f"Creative Manifest required fields missing {sorted(needed - required)}")
    props = schema.get("properties") or {}
    for name in ("visualStandard", "overlays", "visualCopy", "feed", "derivativeRefs", "rightsNotes"):
        if name not in props:
            fail(f"Creative Manifest missing {name}")
    visual_copy_schema = props.get("visualCopy") or {}
    visual_copy_required = set(visual_copy_schema.get("required") or [])
    expected_visual_copy_required = {"decision", "noTextCompared", "pipeline", "candidates"}
    if not expected_visual_copy_required.issubset(visual_copy_required):
        fail(f"Creative Manifest visualCopy required fields missing {sorted(expected_visual_copy_required - visual_copy_required)}")

    must_contain(VFOM / "MOTION-PRESETS.md", ("VELVET_HARD_CUT", "VELVET_PROOF_FREEZE", "VELVET_STRESS_SLOWMO"))
    must_contain(VFOM / "FORMAT-GENOMES.md", ("PROOF_UNDER_PRESSURE", "FAIL_FIX_PROVE", "PROBLEM_TO_PART"))
    must_contain(VFOM / "VISUAL-OS.md", ("## Audio Gate", "near-silence", "vf-ig-music", "אינו gate רישיון-מודל אוטומטי"))
    must_contain(IG_MUSIC_SKILL, ("Instagram music researcher", "MUSIC.md"))
    must_contain(MUSIC_PLAYBOOK, ("## Audio Gate", "audio_repair", "stream presence", "loudness"))

    must_contain(VFCOPY_ROUTER, ("cover headline", "overlay", "NO_TEXT", "reader-first-he.md", "ai-tells-he.md"))
    must_contain(VFCOPY_AUTHORITY, ("Cover / Overlay microcopy", "NO_TEXT", "מבחן מאפייה", "reader-first-he.md", "ai-tells-he.md"))
    must_contain(VFCOPY_PIPELINE, ("Reader-first", "Humanizer", "NO_TEXT", "TEXT_WINS"))
    must_contain(READER_FIRST, ("שתי שאלות לפני מילה", "מה האדם מרגיש", "הדרך הכי פשוטה"))
    must_contain(AI_TELLS, ("כל משפט מרוויח מקום", "מבחן מאפייה", "תיאור תמונה"))

    must_contain(CONTENT_SPRINT, ("Creative Manifest", "velvet-creative-director", "velvet-brand-guardian", "velvet-media-librarian", "OWNER-APPROVED-GRID-STANDARD-2026-09-14.md", "visualStandard.gate=PASS"))
    must_contain(SPECIALISTS["creativeDirector"], ("first-frame", "shotRequest", "EDL", "Creative Manifest", "NO_TEXT", "velvet-hebrew-copy", "reader-first-he.md", "OWNER-APPROVED-GRID-STANDARD-2026-09-14.md", "visualStandard"))
    must_contain(SPECIALISTS["brandGuardian"], ("Brand", "Originality", "feed", "Creative Manifest", "NO_TEXT", "velvet-hebrew-copy", "ai-tells-he.md", "visualStandard.gate=PASS"))
    must_contain(SPECIALISTS["mediaLibrarian"], ("Media Vault", "Asset Truth", "Claim Truth", "Creative Manifest"))

    for path in SPECIALISTS.values():
        agent = path.parent / "agents" / "openai.yaml"
        if not agent.is_file():
            fail(f"missing {agent.relative_to(ROOT)}")

    instance = load_json(INSTANCE)
    autonomy = instance.get("creativeAutonomy") or {}
    expected = {
        "creativeManifestSchema": "packages/vfom/CREATIVE-MANIFEST.schema.json",
        "motionPresets": "packages/vfom/MOTION-PRESETS.md",
        "formatGenomes": "packages/vfom/FORMAT-GENOMES.md",
    }
    for key, value in expected.items():
        if autonomy.get(key) != value:
            fail(f"creativeAutonomy.{key} must be {value}")
    if autonomy.get("creativeManifestRequired") is not True:
        fail("creativeAutonomy.creativeManifestRequired must be true")

    visual_standard = autonomy.get("ownerApprovedVisualStandard") or {}
    if visual_standard.get("required") is not True or visual_standard.get("document") != "packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md":
        fail("creativeAutonomy owner-approved visual standard binding missing/mismatched")
    if (autonomy.get("publish") or {}).get("requireOwnerApprovedVisualStandard") is not True:
        fail("publish must require owner-approved visual standard")

    specialists = autonomy.get("specialists") or {}
    foundry_specialists = foundry.get("specialists") or {}
    expected_specialists = {
        "creativeDirector": ".cursor/skills/velvet-creative-director/SKILL.md",
        "brandGuardian": ".cursor/skills/velvet-brand-guardian/SKILL.md",
        "mediaLibrarian": ".cursor/skills/velvet-media-librarian/SKILL.md",
    }
    for key, value in expected_specialists.items():
        if specialists.get(key) != value or foundry_specialists.get(key) != value:
            fail(f"specialist binding mismatch for {key}")

    # Production-truth guard: the Creative Craft registry must not claim
    # Resolve authoring operations that the accepted safe surface does not expose.
    creative_craft = load_json(CREATIVE_CRAFT_REGISTRY)
    if creative_craft.get("version") != "0.4.1":
        fail("Creative Craft registry must be 0.4.1 after production-acceptance truth correction")
    long_edit_rules = [
        rule for rule in (creative_craft.get("intent_rules") or [])
        if rule.get("pipeline") == "long-edit-heavy-video"
    ]
    if len(long_edit_rules) != 1 or not {"long interview", "edit a long"}.issubset(set(long_edit_rules[0].get("keywords") or [])):
        fail("long-edit-heavy-video must route natural English long-edit requests")
    resolve = (creative_craft.get("tools") or {}).get("resolve") or {}
    required_resolve_gaps = {
        "timeline-edit-authoring",
        "grade-node-authoring",
        "lut-apply",
        "render-job-authoring",
        "fusion-compositing-authoring",
    }
    if resolve.get("readiness") != "PARTIAL_TYPED_AUTOMATION":
        fail("Creative Craft Resolve readiness must remain PARTIAL_TYPED_AUTOMATION until authoring gaps close")
    if not required_resolve_gaps.issubset(set(resolve.get("typed_gaps") or [])):
        fail("Creative Craft Resolve typed gaps understate the accepted safe surface")
    for pipeline_name in ("long-edit-heavy-video", "color-finish", "video-edit", "video-finish"):
        pipeline = (creative_craft.get("pipelines") or {}).get(pipeline_name) or {}
        if pipeline.get("readiness") != "PARTIAL_TYPED_AUTOMATION":
            fail(f"{pipeline_name} must remain PARTIAL_TYPED_AUTOMATION on the current Resolve surface")

    resolve_policy = load_literal_assignment(RESOLVE_SAFE_SERVER, "POLICY")
    if "color_group" in resolve_policy or "fusion_comp" in resolve_policy:
        fail("Resolve safe surface changed color/Fusion authority; review Creative Craft readiness before promotion")
    render_actions = set(resolve_policy.get("render") or [])
    if any(action.startswith(("set_", "add_", "start_", "delete_", "create_")) for action in render_actions):
        fail("Resolve render authoring appeared; review Creative Craft typed gaps before promotion")
    if set(resolve_policy.get("lut") or []) - {"path", "list", "read", "capabilities"}:
        fail("Resolve LUT mutation appeared; review Creative Craft typed gaps before promotion")
    timeline_actions = set(resolve_policy.get("timeline") or [])
    if any(token in action for action in timeline_actions for token in ("append", "insert", "trim", "ripple", "create_timeline")):
        fail("Resolve timeline edit authoring appeared; review Creative Craft typed gaps before promotion")

    if not STAGE6B_REPORT.is_file() or not STAGE6B_GENERATOR.is_file():
        fail("Stage 6B report/generator missing")
    stage6b = load_json(STAGE6B_REPORT)
    if stage6b.get("schema") != "velvetos.stage6b-creative-readiness.v1" or stage6b.get("stage") != "6B":
        fail("Stage 6B creative-readiness schema/stage mismatch")
    if stage6b.get("behavior_change") is not True:
        fail("Stage 6B must record the creative authority/readiness behavior clarification")
    if stage6b.get("prepared_against_main_sha") != "36a873248f02c24201ebfdf386636f2a96a3db43":
        fail("Stage 6B base main SHA drift")
    if stage6b.get("repository_acceptance") != "PASS":
        fail("Stage 6B repository acceptance is not PASS")
    before6b = stage6b.get("before") or {}
    if before6b.get("creative_quality_system_machine_contract_present") is not False:
        fail("Stage 6B baseline must record no pre-existing Creative Craft machine contract")
    missing6b = before6b.get("missing_explicit_manifest_boundary_fields") or {}
    if set(missing6b) != {
        "coordinationOnly", "notApprovalDatabase", "cannotAuthorizeExternalEffects",
        "statusIsEvidenceProjection", "productTruthAuthorityHigher", "policyDecisionSource",
    } or any(value is not None for value in missing6b.values()):
        fail("Stage 6B pre-change manifest-boundary baseline drift")
    after6b = stage6b.get("after") or {}
    current_foundry_hash = hashlib.sha256(FOUNDRY.read_bytes()).hexdigest()
    current_manifest_hash = hashlib.sha256((VFOM / "CREATIVE-MANIFEST.schema.json").read_bytes()).hexdigest()
    if after6b.get("foundry_sha256") != current_foundry_hash or after6b.get("manifest_schema_sha256") != current_manifest_hash:
        fail("Stage 6B current creative authority artifact hash drift")
    quality6b = after6b.get("creative_quality_system") or {}
    if quality6b.get("version") != "2.0.0" or quality6b.get("role") != "authoring_and_quality_system_not_policy_hierarchy":
        fail("Stage 6B Creative Craft quality-system receipt drift")
    if quality6b.get("mayAuthorizeExternalEffects") is not False or quality6b.get("mayOverrideProductTruth") is not False:
        fail("Stage 6B Creative Craft authority boundary drift")
    if quality6b.get("produceCritiqueTargetedRefine") != "internal" or quality6b.get("ownerEscalation") != "exception-only":
        fail("Stage 6B internal refine/escalation receipt drift")
    human6b = after6b.get("human_surface") or {}
    if human6b.get("ownerApprovalForAestheticChoice") is not False or human6b.get("ownerApprovalForRoutineQualityRepair") is not False:
        fail("Stage 6B routine creative owner-approval boundary drift")
    if human6b.get("humanRequired") != ((before6b.get("human_surface") or {}).get("humanRequired") or []):
        fail("Stage 6B owner exception set changed unexpectedly")
    auth6b = stage6b.get("authorization_semantics") or {}
    if auth6b.get("external_effect_policy_registry_unchanged") is not True:
        fail("Stage 6B external-effect policy registry drift")
    if auth6b.get("creative_manifest_is_policy_authority") is not False or auth6b.get("creative_craft_is_policy_authority") is not False:
        fail("Stage 6B creative surfaces must not become policy authority")
    acceptance6b = stage6b.get("acceptance") or {}
    if len(acceptance6b) != 10 or not all(value is True for value in acceptance6b.values()):
        fail("Stage 6B acceptance criteria drift/fail")
    with tempfile.TemporaryDirectory(prefix="stage6b-creative-") as td:
        regenerated6b = Path(td) / "stage6b.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(STAGE6B_GENERATOR),
                "--prepared-against", stage6b["prepared_against_main_sha"],
                "--captured-at", stage6b["captured_at"],
                "--output", str(regenerated6b),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        if proc.returncode != 0:
            fail("Stage 6B report regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()))
        if regenerated6b.read_bytes() != STAGE6B_REPORT.read_bytes():
            fail("Stage 6B creative-readiness report is not reproducible")

    print("OK creative-system manifest specialists motion-genomes audio-gate visual-copy-gate + Resolve runtime-truth bound")


if __name__ == "__main__":
    main()
