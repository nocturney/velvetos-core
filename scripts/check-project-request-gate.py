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
GATE = ROOT / "packages/velvetos/PROJECT-REQUEST-GATE.md"
MANIFEST = ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"
CLI = ROOT / "scripts/vf_project_preflight.py"


def fail(msg: str) -> None:
    print(f"FAIL project-request-gate: {msg}", file=sys.stderr)
    raise SystemExit(1)

for path in (GATE, MANIFEST, CLI):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

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

project_authority = ROOT / bundle["authority"]
asset_manifest = ROOT / bundle["assetManifest"]
project_instructions = ROOT / bundle["instructions"]
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
if project_preflight.PROJECT_AUTHORITY != Path(bundle["authority"]):
    fail("active preflight Project Authority does not match chatgptProjectBundle")
if project_preflight.PROJECT_ASSET_MANIFEST != Path(bundle["assetManifest"]):
    fail("active preflight asset manifest does not match chatgptProjectBundle")
if project_preflight.PROJECT_INSTRUCTIONS != Path(bundle["instructions"]):
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
if Path(publication_evidence.AUTHORITY) != Path(bundle["authority"]):
    fail("publication evidence Project Authority does not match chatgptProjectBundle")
if Path(publication_evidence.ASSETS) != Path(bundle["assetManifest"]):
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
for cfg in manifest["domains"].values():
    all_paths.extend(cfg.get("authorities", []))
missing = sorted({p for p in all_paths if not (ROOT / p).is_file()})
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
    ("create a customer success story for the owner brief", "general_business"),
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

print(f"OK project-request-gate domains={len(manifest['domains'])} authority_paths={len(set(all_paths))} creative_without_evidence=BLOCKED creative_tool_authorization=fail_closed")
