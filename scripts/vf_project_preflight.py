#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from vf_project_bundle import (  # noqa: E402
    ProjectBundleError as _ProjectBundleError,
    resolve as _resolve_project_bundle,
    resolve_reference as _resolve_project_reference,
)

INSTRUCTION_ROOT = Path(__file__).resolve().parents[1]
ROOT = INSTRUCTION_ROOT
MANIFEST = ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"
# Active bundle identity comes from PROJECT-AUTHORITY-MANIFEST.json (chatgptProjectBundle)
# via vf_project_bundle; no revision literals here.
_BUNDLE = _resolve_project_bundle(ROOT, instance_id="velvet-factory", env={})
PROJECT_AUTHORITY = Path(_BUNDLE.authority)
PROJECT_ASSET_MANIFEST = Path(_BUNDLE.asset_manifest)
PROJECT_INSTRUCTIONS = Path(_BUNDLE.instructions)
PROJECT_CONTRACT_VERSION = _BUNDLE.contract_version
PROJECT_REVISION = _BUNDLE.revision
PROJECT_BUNDLE_ID = _BUNDLE.bundle_id
PROJECT_ASSET_MANIFEST_SHA256 = _BUNDLE.asset_manifest_sha256
VISUAL_ENFORCEMENT = Path("packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json")
CREATIVE_MASTER_BRIDGE = Path("scripts/vf_creative_master_bridge.py")
SOURCE_INGEST_BRIDGE = Path("scripts/vf_source_ingest.py")
CHAT_LOCAL_PREFLIGHT = Path("scripts/vf_chat_cold_start_preflight.py")
PROJECT_GATE = Path("packages/velvetos/PROJECT-REQUEST-GATE.md")
# Canonical Instagram tool capability SoT + MCP write/read binding (no parallel registry).
IG_CAPABILITIES = ROOT / "packages/vfigos/CAPABILITIES.json"
CORE_MCP = ROOT / "packages/vfmcp/core-mcp.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _authority_available(reference: str) -> bool:
    try:
        return _resolve_project_reference(
            ROOT, reference, instance_id="velvet-factory", env={}
        ).is_file()
    except _ProjectBundleError:
        return False


def _text_sha256_candidates(path: Path) -> set[str]:
    """Accept canonical bytes or Git CRLF checkout of the same text."""
    raw = path.read_bytes()
    return {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
    }


def project_binding_problems(root: Path = ROOT, *, creative: bool = False) -> list[str]:
    problems: list[str] = []
    paths = [PROJECT_AUTHORITY, PROJECT_ASSET_MANIFEST, PROJECT_INSTRUCTIONS, PROJECT_GATE]
    if creative:
        paths.extend([VISUAL_ENFORCEMENT, CREATIVE_MASTER_BRIDGE, SOURCE_INGEST_BRIDGE, CHAT_LOCAL_PREFLIGHT])
    if any(not (root / rel).is_file() for rel in paths):
        return ["project binding file missing"]
    authority_path = root / PROJECT_AUTHORITY
    instructions_path = root / PROJECT_INSTRUCTIONS
    try:
        authority = authority_path.read_text(encoding="utf-8")
        instructions = instructions_path.read_text(encoding="utf-8")
        gate = (root / PROJECT_GATE).read_text(encoding="utf-8")
        assets = json.loads((root / PROJECT_ASSET_MANIFEST).read_text(encoding="utf-8"))
        policy = json.loads((root / VISUAL_ENFORCEMENT).read_text(encoding="utf-8")) if creative else None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"project binding cannot be decoded: {type(exc).__name__}"]
    if not isinstance(assets, dict) or (creative and not isinstance(policy, dict)):
        return ["project binding JSON must contain top-level objects"]
    asset_rows = assets.get("assets")
    if not isinstance(asset_rows, list) or not all(isinstance(row, dict) for row in asset_rows):
        return ["Project asset manifest assets must be an array of objects"]
    asset_manifest_path = root / PROJECT_ASSET_MANIFEST
    if PROJECT_ASSET_MANIFEST_SHA256 not in _text_sha256_candidates(asset_manifest_path):
        problems.append(f"Project asset manifest hash does not match verified revision {PROJECT_REVISION}")
    authority_identity = (
        f"Contract version: {PROJECT_CONTRACT_VERSION}",
        f"Revision: {PROJECT_REVISION}",
        f"Bundle: {PROJECT_BUNDLE_ID}",
    )
    if not all(x in authority for x in authority_identity):
        problems.append("Project Authority identity mismatch")
    instructions_identity = (
        f"Contract version: {PROJECT_CONTRACT_VERSION} | Revision: {PROJECT_REVISION} | Bundle: {PROJECT_BUNDLE_ID}",
        f"Velvet-Factory-ASSET-MANIFEST-v{PROJECT_REVISION}.json",
        f"Require Contract {PROJECT_CONTRACT_VERSION}, Revision {PROJECT_REVISION}",
        "orientation itself adds useful information",
        "creative_master",
        "materialized to local path + SHA-256",
        "current-chat attachment ingest",
    )
    if not all(x in instructions for x in instructions_identity):
        problems.append("Project Instructions identity/reference-alignment mismatch")
    asset_identity = (
        assets.get("contract_version"),
        str(assets.get("revision")),
        assets.get("bundle_id"),
    )
    if asset_identity != (PROJECT_CONTRACT_VERSION, PROJECT_REVISION, PROJECT_BUNDLE_ID):
        problems.append("Project asset manifest identity mismatch")
    rows = [x for x in asset_rows if x.get("filename") == "Velvet-Factory-Project-Authority-v6.txt"]
    if len(rows) != 1 or rows[0].get("sha256") not in _text_sha256_candidates(authority_path):
        problems.append(f"Project Authority hash does not match ASSET-MANIFEST-v{PROJECT_REVISION}.json")
    instructions_row = assets.get("instructions")
    if not isinstance(instructions_row, dict):
        problems.append("Project Instructions binding missing from asset manifest")
    else:
        if instructions_row.get("filename") != f"Velvet-Factory-Project-Instructions-v{PROJECT_REVISION}.txt":
            problems.append("Project Instructions filename binding mismatch")
        if instructions_row.get("sha256") not in _text_sha256_candidates(instructions_path):
            problems.append(f"Project Instructions hash does not match ASSET-MANIFEST-v{PROJECT_REVISION}.json")
    if creative:
        runtime_rows = assets.get("chat_runtime")
        required_runtime = {
            "scripts/vf_source_ingest.py",
            "scripts/vf_chat_cold_start_preflight.py",
            "scripts/vf_media_integrity.py",
            "scripts/vf_media_limits.py",
            "scripts/vf_creative_master_bridge.py",
        }
        if not isinstance(runtime_rows, list) or {x.get("repo_path") for x in runtime_rows if isinstance(x, dict)} != required_runtime:
            problems.append("Project chat_runtime binding must contain the exact dependency-closed runtime files")
        else:
            for row in runtime_rows:
                rp = root / row["repo_path"]
                if not rp.is_file() or row.get("sha256") not in _text_sha256_candidates(rp):
                    problems.append(f"Project chat runtime hash mismatch: {row.get('repo_path')}")
        route = policy.get("publicationRoute", {})
        if not isinstance(route, dict):
            problems.append("publicationRoute must be an object")
            return problems
        if "creative_execution_authorized: true" not in authority or "creative_execution_authorized: true" not in gate:
            problems.append("pre-tool creative execution receipt is not bound into Project Authority/Gate")
        denied_tools = route.get("deniedTools")
        if not isinstance(denied_tools, list) or not all(isinstance(x, str) for x in denied_tools):
            problems.append("publicationRoute deniedTools must be an array of strings")
        else:
            denied = {x.casefold() for x in denied_tools}
        current_refs = assets.get("current_references")
        current_names: set[str] = set()
        if not isinstance(current_refs, dict):
            problems.append("Project current_references must be an object")
        else:
            required_ref_keys = {"broad_visual", "editorial_layout", "current_direction", "multi_source_composition"}
            if set(current_refs) != required_ref_keys:
                problems.append("Project must bind exactly four current aesthetic references including multi_source_composition")
            current_names = {x for x in current_refs.values() if isinstance(x, str) and x}
            bound_names = {
                row.get("filename") for row in asset_rows
                if row.get("required_for") == "visual_work"
            }
            if not current_names.issubset(bound_names):
                problems.append("Project current aesthetic references are not fully bound in asset manifest")
        separation = policy.get("referenceRoleSeparationPolicy")
        if not isinstance(separation, dict):
            problems.append("referenceRoleSeparationPolicy must be an object")
        else:
            policy_refs = separation.get("aestheticReferences")
            if not isinstance(policy_refs, list) or set(policy_refs) != current_names:
                problems.append("visual enforcement aesthetic references do not match Project asset manifest")
        multi = policy.get("multiSourceCompositionPolicy")
        if not isinstance(multi, dict) or multi.get("samePhysicalProductSourceSet") is not True:
            problems.append("multi-source composition policy missing")
        elif set(multi.get("insetProvenanceValues") or []) != {"SAME_FRAME_CROP", "ALTERNATE_VERIFIED_SOURCE"}:
            problems.append("multi-source inset provenance policy mismatch")
        camera_labels = policy.get("cameraAngleLabelPolicy")
        if not isinstance(camera_labels, dict):
            problems.append("cameraAngleLabelPolicy missing")
        else:
            if camera_labels.get("blanketBan") is not False:
                problems.append("camera-angle labels must not be blanket-banned")
            if camera_labels.get("orientationLabelsAllowedWhen") != "orientation_itself_adds_useful_information":
                problems.append("camera-angle label allowance does not match owner reference clarification")
            if camera_labels.get("otherwise") != "describe_the_concrete_feature_the_view_reveals":
                problems.append("camera-angle label fallback must be feature-first copy")
        continuity = policy.get("creativeContinuityPolicy")
        if not isinstance(continuity, dict):
            problems.append("creativeContinuityPolicy missing")
        else:
            if continuity.get("intermediateBaseVisualIsCompletion") is not False:
                problems.append("intermediate base visual must not count as publication completion")
            if continuity.get("completeFirstResponseWhenToolsAndSourcesPermit") is not True:
                problems.append("first-response publication completion rule missing")
            master = continuity.get("creativeMaster")
            if not isinstance(master, dict) or master.get("freezeSelectedMaster") is not True:
                problems.append("creative master freeze rule missing")
            elif master.get("silentRawSourceRestartForbidden") is not True:
                problems.append("silent raw-source restart must be forbidden")
            no_regression = continuity.get("noRegression")
            if not isinstance(no_regression, dict) or no_regression.get("required") is not True:
                problems.append("final-vs-master no-regression rule missing")
            materialization = continuity.get("materialization")
            if not isinstance(materialization, dict):
                problems.append("creative-master materialization policy missing")
            else:
                if materialization.get("planBeforeCreativeToolSelectionWhenDeterministicOverlayExpected") is not True:
                    problems.append("materialization capability planning rule missing")
                if materialization.get("requiredBeforeDeterministicOverlay") is not True:
                    problems.append("creative-master materialization gate missing")
                if materialization.get("localPathAndSha256Required") is not True or materialization.get("receiptRequired") is not True:
                    problems.append("materialized master local identity/receipt rule missing")
                if materialization.get("rawSourceRecreationCountsAsMaterialization") is not False:
                    problems.append("raw-source recreation must not count as materialization")
                if materialization.get("silentRawFallbackForbidden") is not True:
                    problems.append("unmaterializable master must fail closed against raw fallback")
                if materialization.get("bridge") != CREATIVE_MASTER_BRIDGE.as_posix():
                    problems.append("creative-master materialization bridge binding mismatch")
        ingest = policy.get("sourceIngestPolicy")
        if not isinstance(ingest, dict):
            problems.append("source ingest policy missing")
        else:
            if ingest.get("bridge") != SOURCE_INGEST_BRIDGE.as_posix():
                problems.append("source ingest bridge binding mismatch")
            if ingest.get("currentChatAttachmentLocalIngestBeforeCreativePreflight") is not True:
                problems.append("current-chat attachment ingest rule missing")
            if ingest.get("exactBytesAndSha256Required") is not True or ingest.get("receiptRequired") is not True:
                problems.append("source ingest exact-byte identity/receipt rule missing")
            if ingest.get("externalInputRequiresExplicitCurrentRequestIntakeRoot") is not True:
                problems.append("source ingest intake-root boundary missing")
            if ingest.get("arbitraryFolderScanForbidden") is not True:
                problems.append("arbitrary source folder scanning must be forbidden")
            if ingest.get("unhashedFallbackForbidden") is not True:
                problems.append("unhashed attachment fallback must be forbidden")
            if ingest.get("chatLocalPreflight") != CHAT_LOCAL_PREFLIGHT.as_posix():
                problems.append("chat-local preflight binding mismatch")
            if ingest.get("remoteRepoPreflightMustNotReceiveChatLocalPaths") is not True:
                problems.append("chat-local paths must not be sent to remote repo preflight")
            if ingest.get("chatLocalPreflightAuthorizesCreativeOnly") is not True or ingest.get("chatLocalPreflightNeverAuthorizesPublication") is not True:
                problems.append("chat-local preflight scope must be creative-only")
        reference_rules = assets.get("reference_rules")
        if not isinstance(reference_rules, dict):
            problems.append("Project reference_rules must be an object")
        else:
            for key in (
                    "generic_camera_angle_labels_avoided_by_default",
                    "orientation_labels_allowed_when_orientation_adds_useful_information",
                    "feature_first_copy_preferred_when_orientation_not_informative",
                    "publication_prep_intermediate_visual_is_not_completion",
                    "first_response_completion_required_when_tools_and_sources_permit",
                    "creative_master_freeze_after_product_truth_and_reference_match",
                    "finalization_must_preserve_or_improve_creative_master",
                    "silent_raw_source_restart_after_successful_master_forbidden",
                    "creative_master_replacement_requires_recorded_cause",
                    "creative_master_materialization_required_before_deterministic_overlay",
                    "creative_master_must_be_local_path_plus_sha256",
                    "creative_master_materialization_receipt_required",
                    "creative_tool_materialization_capability_planned_before_generation_when_overlay_expected",
                    "conversation_or_ui_only_image_is_not_file_backed_master",
                    "provider_task_or_remote_url_is_not_file_backed_master_until_exact_bytes_are_materialized",
                    "raw_source_recreation_is_not_creative_master_materialization",
                    "unmaterializable_master_must_not_fall_back_silently_to_raw_source",
                    "current_chat_attachment_local_ingest_required_before_creative_preflight",
                    "source_ingest_exact_bytes_and_sha256_required",
                    "source_ingest_receipt_required",
                    "current_request_intake_root_must_be_explicit",
                    "arbitrary_user_folder_scan_for_sources_forbidden",
                    "visible_attachment_must_not_be_declared_unusable_before_platform_local_ingest_attempt",
                    "attachment_bytes_unavailable_is_bounded_blocker",
                    "unhashed_attachment_source_fallback_forbidden",
                    "chat_local_preflight_required_when_repo_and_attachment_filesystems_differ",
                    "remote_repo_preflight_must_not_receive_chat_local_paths",
                    "chat_local_preflight_creative_only_never_publication",
                    "chat_runtime_files_hash_bound_in_manifest",
                    "chat_runtime_dependency_closed"):
                if reference_rules.get(key) is not True:
                    problems.append(f"Project reference rule missing or false: {key}")
    return problems


def _phrase_in(probe: str, phrase: str) -> bool:
    """Substring match for multi-word / non-ASCII phrases."""
    return phrase.casefold() in probe


def _token_in(probe: str, token: str) -> bool:
    """Word-boundary match so 'feed' does not hit 'feedback' / 'story'≠'history'."""
    return re.search(rf"(?<!\w){re.escape(token.casefold())}(?!\w)", probe) is not None


def _hint_matches(probe: str, hint: str) -> bool:
    """ASCII single-token hints use word boundaries; phrases/Hebrew stay substring."""
    h = str(hint).casefold()
    if " " in h or any(ord(c) > 127 for c in h):
        return h in probe
    return _token_in(probe, h)


def _advisory_only_request(probe: str) -> bool:
    """True for discussion/howto — not authorization to create or execute.

    This flags advisory *language* in a prompt. It must NOT alone erase an
    Instagram action found in another clause of a mixed request.
    """
    return any(
        _phrase_in(probe, p)
        for p in (
            "should we",
            "should i",
            "do we delete",
            "do i delete",
            "how do i",
            "how to delete",
            "how to remove",
            "how can i",
            "how should",
            "what is an",
            "what is a",
            "what's an",
            "what's a",
            "what happens if",
            "what if i",
            "whether i should",
            "whether we should",
            "tell me whether",
            "write instructions",
            "instructions for deleting",
            "instructions for remove",
            "explain how",
            "explain how to",
            "האם כדאי",
            "האם למחוק",
            "איך מוחקים",
            "איך למחוק",
            "מה זה",
            "מה קורה אם",
            "תכתוב הוראות",
        )
    )


def _split_intent_clauses(probe: str) -> list[str]:
    """Split mixed prompts so later action clauses stay visible to gates."""
    parts = re.split(
        r"(?:\b(?:and\s+then|then)\b|,?\s*ואז|,?\s*ואחר כך|,?\s*לאחר מכן)",
        probe,
        flags=re.IGNORECASE,
    )
    return [p.strip(" \t,.;:") for p in parts if p and p.strip(" \t,.;:")]


def _hypothetical_or_howto_clause(clause: str) -> bool:
    """True when a clause itself is advice/howto, not an imperative mutation."""
    return any(
        _phrase_in(clause, p)
        for p in (
            "should we",
            "should i",
            "whether i should",
            "whether we should",
            "how do i",
            "how to",
            "how can i",
            "how should",
            "what happens if",
            "what if i",
            "explain how to",
            "explain how publishing",
            "explain how deleting",
            "write instructions",
            "האם כדאי",
            "איך מוחקים",
            "איך למחוק",
            "מה קורה אם",
            "מה זה",
        )
    )


def _followthrough_mutation_clause(clause: str) -> bool:
    """True for short follow-through publish/delete clauses after 'then' / 'ואז'."""
    if _hypothetical_or_howto_clause(clause):
        return False
    # publish/post/share/push/upload it|this [to Instagram] [live]
    if re.search(
        r"(?<!\w)(?:publish|post|share|push|upload|send)\b"
        r"(?:\W+\w+){0,6}\W+(?:it|this|that|them)\b",
        clause,
    ):
        return True
    if re.search(
        r"(?<!\w)(?:publish|post|share|push|upload|send)\b"
        r"(?:\W+\w+){0,6}\W+(?:to|on)\s+instagram",
        clause,
    ):
        return True
    if _go_live_request(clause):
        return True
    # delete/remove/archive/unpublish + object
    if re.search(
        r"(?<!\w)(?:delete|remove|archive|unpublish)\b"
        r"(?:\W+\w+){0,6}\W+(?:it|this|that|post|reel|story|media)\b",
        clause,
    ):
        return True
    # Hebrew follow-through publish / take-down
    if any(
        _phrase_in(clause, v)
        for v in (
            "תפרסם",
            "תעלה אותו",
            "תעלה אותה",
            "תעלה את זה",
            "תעלה",
            "שתף",
            "פרסם",
            "תמחק",
            "תוריד אותו",
            "תוריד אותה",
            "תוריד את זה",
            "תוריד",
            "תארכב",
            "ארכב",
            "מחק את הפוסט",
            "הסר",
        )
    ):
        return True
    return False


@lru_cache(maxsize=1)
def _instagram_tool_classes() -> tuple[frozenset[str], frozenset[str]]:
    """Return (mutation_tool_ids, read_only_tool_ids) from canonical IG SoT.

    Mutation ids come from supported write capabilities in
    ``packages/vfigos/CAPABILITIES.json`` (publish.* / media.delete) plus
    ``allowedWriteAfterGates`` on the Instagram server in
    ``packages/vfmcp/core-mcp.json`` (comment moderation writes).

    Read-only ids come from supported read capabilities in CAPABILITIES plus
    ``allowedRead`` in core-mcp. ``graph_mutation_matrix`` is always read-only
    even when listed beside delete.
    """
    mutation: set[str] = set()
    read_only: set[str] = set()
    if IG_CAPABILITIES.is_file():
        caps = json.loads(IG_CAPABILITIES.read_text(encoding="utf-8"))
        for row in caps.get("capabilities") or []:
            if not isinstance(row, dict):
                continue
            tools = [t for t in (row.get("tools") or []) if isinstance(t, str) and t]
            if not tools:
                continue
            cap_id = str(row.get("id") or "")
            supported = row.get("supported", True)
            # graph_mutation_matrix is capability discovery SoT — never a mutation.
            if "graph_mutation_matrix" in tools:
                read_only.add("graph_mutation_matrix")
            write_tools = [t for t in tools if t != "graph_mutation_matrix"]
            if supported is False:
                continue
            if cap_id.startswith("instagram.publish.") or cap_id == "instagram.media.delete":
                mutation.update(write_tools)
            elif write_tools:
                read_only.update(write_tools)
    if CORE_MCP.is_file():
        core = json.loads(CORE_MCP.read_text(encoding="utf-8"))
        for server in core.get("servers") or []:
            if not isinstance(server, dict) or server.get("id") != "instagram":
                continue
            for t in server.get("allowedWriteAfterGates") or []:
                if isinstance(t, str) and t:
                    mutation.add(t)
            for t in server.get("allowedRead") or []:
                if isinstance(t, str) and t:
                    read_only.add(t)
            break
    # Never treat a write id as read-only if it also appears on a write surface.
    read_only -= mutation
    return frozenset(mutation), frozenset(read_only)


def _tool_id_in(probe: str, tool_id: str) -> bool:
    """Token-aware match for snake_case MCP tool ids (no substring false hits)."""
    return re.search(rf"(?<!\w){re.escape(tool_id)}(?!\w)", probe, flags=re.IGNORECASE) is not None


def _tool_documentation_or_advisory(probe: str) -> bool:
    """True when the ask is about a tool (docs/compare/advice), not executing it."""
    return any(
        _phrase_in(probe, p)
        for p in (
            "what does",
            "what is",
            "what's",
            "how does",
            "how do",
            "how to use",
            "explain",
            "tell me how",
            "tell me what",
            "compare",
            "difference between",
            "should we use",
            "should i use",
            "documentation",
            "docs for",
            "meaning of",
            "מה זה",
            "מה עושה",
            "איך עובד",
            "הסבר",
            "האם כדאי להשתמש",
            "השווה",
        )
    )


def _generic_instagram_publish_tool_execution(probe: str) -> bool:
    """True for 'call/use the Instagram publish tool' without a specific tool id."""
    if _tool_documentation_or_advisory(probe):
        return False
    if not (_phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")):
        return False
    return (
        re.search(
            r"(?<!\w)(?:use|run|call|invoke|execute|trigger)\b"
            r"(?:\W+\w+){0,6}\W+publish(?:_\w+)?\s+tools?\b",
            probe,
            flags=re.IGNORECASE,
        )
        is not None
        or re.search(
            r"(?<!\w)(?:תשתמש|השתמש|תריץ|הרץ|תפעיל|הפעל|בצע)\b"
            r"(?:\W+\w+){0,6}\W+(?:ב)?כלי\s+ה?פרסום",
            probe,
        )
        is not None
    )


def _mutation_tool_execution_intent(probe: str, tool_id: str) -> bool:
    """True when probe asks to execute a specific mutation tool id."""
    if not _tool_id_in(probe, tool_id):
        return False
    if _tool_documentation_or_advisory(probe):
        return False
    # Explicit execution verbs around the tool id.
    if re.search(
        rf"(?<!\w)(?:use|run|call|invoke|execute|trigger|apply|perform)\b"
        rf"(?:\W+\w+){{0,6}}\W+{re.escape(tool_id)}\b",
        probe,
        flags=re.IGNORECASE,
    ):
        return True
    if re.search(
        rf"(?<!\w)(?:תשתמש|השתמש|תריץ|הרץ|תפעיל|הפעל|בצע|תקרא\s+ל)\b"
        rf"(?:\W+\w+){{0,6}}\W+{re.escape(tool_id)}\b",
        probe,
    ):
        return True
    # Instagram-scoped tool invocation: "Instagram delete_media 123"
    if re.search(
        rf"(?i)(?<!\w)(?:instagram|אינסטגרם)\b(?:\W+\w+){{0,4}}\W+{re.escape(tool_id)}\b",
        probe,
    ):
        return True
    # Imperative tool command with args / target: "publish_image with …", "delete_media 123"
    if re.search(
        rf"(?<!\w){re.escape(tool_id)}\b(?:\W+(?:now|with|on|using|for|this|that|\d))",
        probe,
        flags=re.IGNORECASE,
    ):
        return True
    # "Delete this with delete_media" / Hebrew equivalent already covered by verbs.
    if re.search(
        rf"(?<!\w)(?:delete|remove|publish|post|share)\b(?:\W+\w+){{0,6}}\W+{re.escape(tool_id)}\b",
        probe,
        flags=re.IGNORECASE,
    ):
        return True
    # Bare tool id as the whole command (or leading command token).
    stripped = probe.strip(" \t,.;:!?\"'`")
    if re.fullmatch(rf"{re.escape(tool_id)}(?:\W+\S+)*", stripped, flags=re.IGNORECASE):
        return True
    return False


def _instagram_mutation_tool_request(probe: str) -> bool:
    """True when a canonical IG mutation MCP tool is being invoked/executed."""
    if _generic_instagram_publish_tool_execution(probe):
        return True
    mutation_ids, _read_ids = _instagram_tool_classes()
    return any(_mutation_tool_execution_intent(probe, tool_id) for tool_id in mutation_ids)


def _clause_instagram_action(clause: str, *, allow_followthrough: bool = False) -> bool:
    """Action intent inside one clause (ignores advisory language elsewhere).

    Follow-through mutations (`publish it`, `תמחק את הפוסט`) only count when the
    prompt was split into multiple clauses. Otherwise bare prep like
    `publish this post` would be mis-routed as Instagram delivery.

    Canonical Instagram mutation tool identifiers (from CAPABILITIES / core-mcp
    write binding) with execution intent are always action — including mixed
    advisory+tool clauses.
    """
    if not clause or _hypothetical_or_howto_clause(clause):
        return False
    if _instagram_mutation_tool_request(clause):
        return True
    if _instagram_delivery_request(clause) or _instagram_destructive_request(clause):
        return True
    if allow_followthrough:
        return _followthrough_mutation_clause(clause)
    return False


def _instagram_post_prep_request(probe: str) -> bool:
    """True for creating/drafting/designing an Instagram post (creative prep).

    Not delivery/action: preparation only. Advisory discussion about whether
    to create a post is excluded.
    """
    if _advisory_only_request(probe):
        return False
    if any(
        _phrase_in(probe, h)
        for h in (
            "תכין פוסט לאינסטגרם",
            "תיצור פוסט לאינסטגרם",
            "תעצב פוסט לאינסטגרם",
            "תכין לי פוסט באינסטגרם",
            "תכין פרסום לאינסטגרם",
            "צור פוסט לאינסטגרם",
            "עצב פוסט לאינסטגרם",
        )
    ):
        return True
    has_ig = _phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")
    if not has_ig:
        return False
    # create/draft/design/make/prepare + Instagram + post
    if re.search(
        r"(?<!\w)(?:create|draft|design|make|prepare)\b(?:\W+\w+){0,6}\W+"
        r"instagram\b(?:\W+\w+){0,4}\W+posts?\b",
        probe,
    ):
        return True
    # create/draft/... + post + for/on Instagram
    if re.search(
        r"(?<!\w)(?:create|draft|design|make|prepare)\b(?:\W+\w+){0,4}\W+"
        r"posts?\b(?:\W+\w+){0,6}\W+(?:for|on)\s+instagram",
        probe,
    ):
        return True
    # Hebrew prep verb + פוסט/פרסום with Instagram already present
    if any(_phrase_in(probe, v) for v in ("תכין", "תיצור", "תעצב", "צור", "עצב", "הכן")) and any(
        _phrase_in(probe, o) for o in ("פוסט", "פרסום")
    ):
        return True
    return False


def _go_live_request(probe: str) -> bool:
    """Push/make content live — VF delivery channel is Instagram."""
    if re.search(
        r"(?<!\w)(?:push|make|take|put)\b(?:\W+\w+){0,5}\W+live\b",
        probe,
    ):
        return True
    if re.search(r"(?<!\w)publish\b(?:\W+\w+){0,5}\W+live\b", probe):
        return True
    return any(
        _phrase_in(probe, p)
        for p in (
            "לאוויר",
            "תפרסם את זה עכשיו",
            "פרסם עכשיו",
            "תעלה את זה לאוויר",
            "העלה את זה לאוויר",
        )
    )


def _instagram_delivery_request(probe: str) -> bool:
    """True when the ask is to publish/send content onto Instagram (delivery)."""
    has_ig = _phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")
    if any(
        _phrase_in(probe, h)
        for h in (
            "העלה לאינסטגרם",
            "שלח לאינסטגרם",
            "שתף לאינסטגרם",
            "שתף את זה באינסטגרם",
            "תשתף באינסטגרם",
            "תעלה את הפוסט לאינסטגרם",
            "תעלה לאינסטגרם",
            "תפרסם את זה באינסטגרם",
            "פרסם באינסטגרם",
            "העלה את זה לאוויר באינסטגרם",
        )
    ):
        return True
    # Destination-scoped English delivery (excludes office co-occurrence).
    if has_ig and re.search(
        r"(?<!\w)(?:upload|publish|schedule|put|send|post|share|push|add)\b"
        r"(?:\W+\w+){0,8}\W+(?:on|to|onto|in|from)\s+instagram",
        probe,
    ):
        return True
    # Go-live / push-live family (Instagram is the VF publication channel).
    if _go_live_request(probe):
        return True
    # Hebrew upload token with explicit Instagram destination.
    if has_ig and any(_phrase_in(probe, h) for h in ("העלה", "תעלה", "פרסם", "תפרסם", "שתף")):
        return True
    return False


def _instagram_destructive_request(probe: str) -> bool:
    """True for mutating/deleting Instagram content (Graph DELETE / take-down)."""
    if any(
        _phrase_in(probe, h)
        for h in (
            "מחק מאינסטגרם",
            "הסר מאינסטגרם",
            "תוריד את זה מהאינסטגרם",
            "מחק את הפוסט באינסטגרם",
            "תמחק את הריל",
            "תמחק את הפוסט",
            "הסר את הסטורי",
            "תוריד את הפוסט",
        )
    ):
        return True
    has_ig = _phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")
    if has_ig and re.search(
        r"(?<!\w)(?:delete|remove|unpublish|archive)\b(?:\W+\w+){0,12}\W+instagram"
        r"|(?<!\w)(?:delete|remove|unpublish|archive)\b\W+instagram"
        r"|\binstagram\b(?:\W+\w+){0,6}\W+(?:delete|remove|unpublish|archive)\b",
        probe,
    ):
        return True
    # take down + social object
    if re.search(
        r"(?<!\w)take\s+down\b(?:\W+\w+){0,6}\W+(?:post|reel|story|media)\b"
        r"|(?<!\w)take\s+(?:this|that|the)\s+(?:post|reel|story|media)\s+down\b",
        probe,
    ):
        return True
    # Reel is Instagram-native
    if re.search(r"(?<!\w)(?:delete|remove|archive)\b(?:\W+\w+){0,5}\W+reels?\b", probe):
        return True
    # Story take-down / remove (not narrative success/customer/user story)
    if re.search(r"(?<!\w)(?:delete|remove|archive)\b(?:\W+\w+){0,5}\W+story\b", probe):
        if not any(
            _phrase_in(probe, p)
            for p in ("success story", "customer story", "user story", "case study")
        ):
            return True
    return False


def _instagram_publish_request(probe: str) -> bool:
    """True for Instagram delivery, destructive, or mutation-tool intents.

    Delivery: destination-scoped publish/send (`send this to Instagram`) and
    go-live commands (`push this live`, `תעלה את זה לאוויר`). Preparation
    (`prepare a post`, `תכין פוסט`) is not delivery.

    Destructive: delete/remove/archive/take-down of Instagram media/posts/
    reels/stories.

    Mutation tools: canonical write tool ids from CAPABILITIES.json /
    core-mcp.json (`publish_image`, `publish_story`, `delete_media`, …)
    with execution intent. Read-only ids (`list_media`, `get_profile`, …)
    stay non-action. Docs/advisory about a tool stay non-action.

    Mixed prompts keep the strictest clause: advisory language in one clause
    must not erase a real publish/delete/tool clause later (`explain …, then
    use publish_image`). Pure howto/hypothetical discussion with no
    action clause stays non-action.
    """
    clauses = _split_intent_clauses(probe)
    multi = len(clauses) > 1
    # Mixed prompts: keep the strictest clause. Follow-through publish/delete
    # after then/ואז is action even when an earlier clause is advisory.
    if any(_clause_instagram_action(c, allow_followthrough=multi) for c in clauses):
        return True
    # Single-clause destination/destructive patterns (no advisory short-circuit).
    if len(clauses) == 1 and _hypothetical_or_howto_clause(clauses[0]):
        return False
    if _advisory_only_request(probe) and len(clauses) == 1:
        return False
    return _instagram_delivery_request(probe) or _instagram_destructive_request(probe)


def _bare_publication_request(probe: str) -> bool:
    """Public publication prep without an Instagram destination (not IG delivery)."""
    if _token_in(probe, "publish") or _phrase_in(probe, "פרסם"):
        return True
    if _token_in(probe, "post") and any(
        _phrase_in(probe, p) for p in ("this post", "a post", "the post", "new post", "publish this")
    ):
        return True
    return False


def _contains_phrase(probe: str, phrases: tuple[str, ...]) -> bool:
    return any(_phrase_in(probe, phrase) for phrase in phrases)


def _external_mutation_request(probe: str) -> bool:
    gmail_surface = _contains_phrase(probe, ("gmail", "email", "e-mail", "מייל", "ג׳ימייל", "ג'ימייל"))
    gmail_write = _contains_phrase(
        probe,
        (
            "reply", "respond", "send", "forward",
            "תענה", "השב", "שלח", "תשלח", "העבר",
        ),
    )
    drive_surface = _contains_phrase(probe, ("google drive", "drive artifact", "דרייב"))
    drive_write = _contains_phrase(
        probe,
        ("save", "create", "upload", "write", "persist", "שמור", "צור", "העלה", "כתוב"),
    )
    return (gmail_surface and gmail_write) or (drive_surface and drive_write)


def _physical_print_request(probe: str) -> bool:
    if _contains_phrase(probe, ("printable", "print-ready", "print ready")):
        # Building a printable artifact is still local artifact work; actual printer
        # control remains separately gated below.
        reduced = probe.replace("printable", "").replace("print-ready", "").replace("print ready", "")
    else:
        reduced = probe
    return _contains_phrase(
        reduced,
        (
            "send to printer", "start print", "start printing", "print this",
            "upload to printer", "printer control", "printer network",
            "שלח למדפסת", "התחל הדפסה", "תדפיס", "הדפס את",
        ),
    )


def _commercial_or_spend_request(probe: str, domains: set[str]) -> bool:
    if domains & {"sales_conversion", "finance"}:
        return True
    return _contains_phrase(
        probe,
        (
            "price", "quote", "cost", "payment", "invoice", "purchase",
            "subscription", "billing", "spend", "boost", "ads", "advertising",
            "מחיר", "הצעה", "עלות", "תשלום", "חשבונית", "רכישה", "מנוי", "תקציב", "בוסט",
        ),
    ) or "₪" in probe


def _rights_or_privacy_request(probe: str) -> bool:
    return _contains_phrase(
        probe,
        (
            "copyright", "license right", "rights clearance", "personal data",
            "private data", "private customer data", "customer personal data", "customer data",
            "privacy", "medical", "legal",
            "זכויות", "פרטיות", "מידע אישי", "רפואי", "משפטי",
        ),
    )


def _destructive_or_permission_request(probe: str) -> bool:
    return _contains_phrase(
        probe,
        (
            "delete", "remove", "archive", "revoke", "permission", "grant access",
            "change access", "trash", "destroy",
            "מחק", "תמחק", "הסר", "בטל הרשאה", "הרשאה", "שנה גישה", "אשפה",
        ),
    )


def request_scope_and_triggers(text: str, domains: list[str], manifest: dict) -> tuple[str, list[str]]:
    probe = text.casefold()
    domain_set = set(domains)
    triggers: list[str] = []

    if domain_set & {"creative_publication", "instagram_action"}:
        triggers.append("creative_or_publication")
    if domain_set == {"general_business"}:
        triggers.append("unknown_domain")
    if _external_mutation_request(probe) or "instagram_action" in domain_set:
        triggers.append("external_mutation")
    if _commercial_or_spend_request(probe, domain_set):
        triggers.append("commercial_or_spend")
    if _rights_or_privacy_request(probe):
        triggers.append("rights_or_privacy")
    if _destructive_or_permission_request(probe):
        triggers.append("destructive_or_permission")
    if _physical_print_request(probe):
        triggers.append("physical_print")

    if "external_mutation" in triggers:
        scope = "external_mutation"
    elif "unknown_domain" in triggers:
        scope = "unknown_domain"
    elif "research" in domain_set or _contains_phrase(
        probe, ("read only", "read-only", "inspect", "analyze", "analyse", "research", "latest", "בדוק", "מחקר")
    ):
        scope = "read_only"
    elif "operations" in domain_set:
        scope = "internal_mutation"
    else:
        scope = "local_routine"

    allowed = set((manifest.get("fastPath") or {}).get("fullPreflightTriggers") or [])
    triggers = [item for item in dict.fromkeys(triggers) if item in allowed]
    return scope, triggers


def fast_path_eligible(domains: list[str], scope: str, triggers: list[str], manifest: dict) -> bool:
    cfg = manifest.get("fastPath") or {}
    if cfg.get("status") != "active" or triggers:
        return False
    profiles = cfg.get("domainProfiles") or {}
    domain_set = set(domains)
    if not domain_set or not domain_set.issubset(set(profiles)):
        return False
    return scope in set(cfg.get("eligibleScopes") or [])


def _fast_path_route(
    domains: list[str],
    scope: str,
    text: str,
    manifest: dict,
) -> tuple[list[str], list[str], list[str], list[str]]:
    cfg = manifest["fastPath"]
    authorities = list(cfg.get("baselineAuthorities") or [])
    packs: list[str] = []
    hard_gates: list[str] = []
    for domain in domains:
        profile = (cfg.get("domainProfiles") or {}).get(domain) or {}
        authorities.extend(profile.get("authorities") or [])
        hard_gates.extend(profile.get("hardGates") or [])
        packs.extend(profile.get("packs") or [])

    probe = text.casefold()
    if "production" in domains and scope != "read_only" and _contains_phrase(
        probe,
        ("cad", "dimensions", "verified dimensions", "step", "stl", "3mf", "dxf", "תכנון מכני", "מידות"),
    ):
        hard_gates.append("verified_specs")

    return (
        list(dict.fromkeys(authorities)),
        list(dict.fromkeys(packs)),
        list(dict.fromkeys(hard_gates)),
        required_tools_for_request(text, domains),
    )


def required_tools_for_request(text: str, domains: list[str]) -> list[str]:
    probe = text.casefold()
    tools: list[str] = []
    if _contains_phrase(probe, ("gmail", "email", "e-mail", "ג׳ימייל", "ג'ימייל", "מייל")):
        if _contains_phrase(probe, ("reply", "respond", "תענה", "השב")):
            tools.append("Gmail.reply")
        elif _contains_phrase(probe, ("send", "forward", "שלח", "תשלח", "העבר")):
            tools.append("Gmail.send_message")
        else:
            tools.append("Gmail.search_threads")
    if _contains_phrase(probe, ("google drive", "drive artifact", "דרייב")):
        if _contains_phrase(probe, ("save", "create", "upload", "write", "persist", "שמור", "צור", "העלה", "כתוב")):
            tools.append("Google-drive.create_file")
        else:
            tools.append("Google-drive.search_files")
    if _contains_phrase(probe, ("owner brief", "owner morning brief", "בריף")):
        tools.append("scripts/vfops_loop.py brief")
    if _contains_phrase(probe, ("internal status", "operational status", "סטטוס")) and "operations" in domains:
        tools.append("office/control-plane")
    if "research" in domains:
        tools.append("WebSearch")
    if "production" in domains:
        dcc_routes = (
            ("maya", "creative-craft:maya"),
            ("blender", "creative-craft:blender"),
            ("3ds max", "creative-craft:3dsmax"),
            ("zbrush", "creative-craft:zbrush"),
        )
        for phrase, tool in dcc_routes:
            if _phrase_in(probe, phrase):
                tools.append(tool)
        if _contains_phrase(probe, ("cad", "step", "stl", "3mf", "dxf", "printable", "תכנון", "שרטוט")):
            tools.append("scripts/vf_fabrication_router.py")
        if not tools:
            tools.append("creative-craft:fabrication")
    return list(dict.fromkeys(tools))


def required_skills_for_request(text: str, domains: list[str]) -> list[str]:
    probe = text.casefold()
    skills: list[str] = []
    if "production" in domains:
        if _contains_phrase(probe, ("maya", "blender", "3ds max", "zbrush", "dcc", "3d model", "modeling")):
            skills.append("vf-dcc-modeling-craft")
        if _contains_phrase(probe, ("cad", "step", "stl", "3mf", "dxf", "dimensions", "תכנון", "שרטוט", "מידות")):
            skills.append("vf-cad-design-craft")
    if "research" in domains:
        skills.append("vfresearch")
    return list(dict.fromkeys(skills))


def local_instructions_for_domains(domains: list[str], manifest: dict) -> list[str]:
    cfg = manifest.get("instructionLocality") or {}
    root_guide = cfg.get("rootGuide") or "AGENTS.md"
    guides = [root_guide]
    domain_guides = cfg.get("domainGuides") or {}
    for domain in domains:
        guides.extend(domain_guides.get(domain) or [])
    return list(dict.fromkeys(guides))


def classify(text: str, manifest: dict) -> list[str]:
    probe = text.casefold()
    hits: list[str] = []
    for name, cfg in manifest["domains"].items():
        if any(_hint_matches(probe, hint) for hint in cfg.get("hints", [])):
            hits.append(name)
    # Caption / public-social copy requests are creative by default in VF. Co-route
    # them through the Creative Manifest gate instead of allowing copywriting alone.
    public_copy_phrases = (
        "caption",
        "כיתוב",
        "public-social",
        "visual-copy",
        "social media",
        "social-media",
        "instagram",
        "אינסטגרם",
        "לפיד",
    )
    public_copy_tokens = ("feed",)
    if (
        "copywriting" in hits
        and "creative_publication" not in hits
        and (
            any(_phrase_in(probe, h) for h in public_copy_phrases)
            or any(_token_in(probe, t) for t in public_copy_tokens)
        )
    ):
        hits.append("creative_publication")
    # Instagram Story / create-a-Story production — not narrative "success/customer/user story".
    if "creative_publication" not in hits and _token_in(probe, "story"):
        narrative = any(
            _phrase_in(probe, p)
            for p in ("success story", "customer story", "user story", "case study")
        )
        social_story = any(
            _phrase_in(probe, p)
            for p in ("instagram story", "ig story", "create a story", "make a story", "write a story", "story for the")
        )
        if social_story and not narrative:
            hits.append("creative_publication")
    # Instagram post create/draft/design/prepare → creative prep (not delivery).
    if "creative_publication" not in hits and _instagram_post_prep_request(probe):
        hits.append("creative_publication")
    # Structural Instagram publish detection (verb + destination, intervening words OK).
    if _instagram_publish_request(probe):
        if "instagram_action" not in hits:
            hits.append("instagram_action")
    elif "instagram_action" in hits:
        # No IG destination: drop Instagram delivery route, but keep publication prep.
        hits = [h for h in hits if h != "instagram_action"]
        if "creative_publication" not in hits and _bare_publication_request(probe):
            hits.append("creative_publication")
    elif "creative_publication" not in hits and _bare_publication_request(probe):
        # e.g. "publish this post" never entered instagram_action but is still public prep.
        hits.append("creative_publication")
    # Pure advisory/howto (no action clause) must not authorize creative production
    # or IG actions. Mixed prompts that already carry instagram_action keep it —
    # never strip the strictest action route with a global advisory override.
    if _advisory_only_request(probe) and "instagram_action" not in hits:
        hits = [h for h in hits if h != "creative_publication"]
    return hits or ["general_business"]

def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve VelvetOS project request authority preflight")
    parser.add_argument("--domain", action="append", choices=None)
    parser.add_argument("--text")
    parser.add_argument("--manifest", help="Exact Creative Manifest for creative production evidence")
    parser.add_argument("--content-id")
    parser.add_argument("--phase", choices=("production", "delivery"), help="Use delivery for review handoff; Instagram actions require delivery")
    parser.add_argument(
        "--delivery-approval",
        help="Path to signed velvet.delivery_approval.v1 JSON receipt (or inline JSON)",
    )
    parser.add_argument(
        "--mutation-tool",
        help="Exact Instagram mutation tool id the approval must bind to",
    )
    parser.add_argument(
        "--package-sha256",
        help="Exact package digest the approval must bind to",
    )
    args = parser.parse_args()
    manifest = load_manifest()
    request_text = args.text or ""
    domains = args.domain or classify(request_text, manifest)
    unknown = [d for d in domains if d not in manifest["domains"]]
    if unknown:
        receipt = {
            "request_domain": domains,
            "request_scope": "unknown_domain",
            "preflight_mode": "FULL",
            "full_preflight_triggers": ["unknown_domain"],
            "owner_surface": "true_blocker_only",
            "authority_manifest_version": manifest["schemaVersion"],
            "baseline_authority": "FAIL",
            "local_instructions": local_instructions_for_domains([], manifest),
            "routed_packs": [],
            "required_skills": [],
            "required_sources": [],
            "required_tools": [],
            "hard_gates": [],
            "current_evidence_state": "BLOCKED",
            "project_preflight": "BLOCKED",
            "route_resolution": "BLOCKED",
            "reason": "unknown_domain",
            "domains": unknown,
            "missing_authority_paths": [],
            "authority_conflicts": [f"unknown domain: {d}" for d in unknown],
            "creative_execution_authorized": False,
            "delivery_authorized": False,
        }
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2

    local_instructions = local_instructions_for_domains(domains, manifest)
    local_instruction_missing = [path for path in local_instructions if not (INSTRUCTION_ROOT / path).is_file()]
    request_scope, full_triggers = request_scope_and_triggers(request_text, domains, manifest)
    fast_candidate = fast_path_eligible(domains, request_scope, full_triggers, manifest)
    fast_profile_problems: list[str] = []

    if fast_candidate:
        authorities, packs, hard_gates, required_tools = _fast_path_route(
            domains, request_scope, request_text, manifest
        )
        missing = [path for path in authorities if not _authority_available(path)]
        if missing:
            fast_profile_problems = [
                "fast path authority unavailable: " + path for path in missing
            ]
            full_triggers = list(dict.fromkeys(full_triggers + ["authority_conflict"]))
            fast_candidate = False

    if not fast_candidate:
        authorities = list(manifest["baselineAuthorities"])
        packs = []
        hard_gates = []
        for domain in domains:
            cfg = manifest["domains"][domain]
            authorities.extend(cfg.get("authorities", []))
            packs.extend(cfg.get("packs", []))
            hard_gates.extend(cfg.get("hardGates", []))
        authorities = list(dict.fromkeys(authorities))
        packs = list(dict.fromkeys(packs))
        hard_gates = list(dict.fromkeys(hard_gates))
        required_tools = required_tools_for_request(request_text, domains)
        missing = [path for path in authorities if not _authority_available(path)]
    else:
        authorities = list(dict.fromkeys(authorities))
        packs = list(dict.fromkeys(packs))
        hard_gates = list(dict.fromkeys(hard_gates))
        missing = [path for path in authorities if not _authority_available(path)]

    creative = bool(set(domains) & {"creative_publication", "instagram_action"})
    binding_problems = [] if fast_candidate else project_binding_problems(creative=creative)
    binding_problems = fast_profile_problems + [
        "local instruction unavailable: " + path for path in local_instruction_missing
    ] + binding_problems
    if (missing or binding_problems) and "authority_conflict" not in full_triggers:
        full_triggers = list(dict.fromkeys(full_triggers + ["authority_conflict"]))

    preflight_mode = "FAST_PATH" if fast_candidate else "FULL"
    initial_blocked = bool(missing or binding_problems)
    receipt = {
        "request_domain": domains,
        "request_scope": request_scope,
        "preflight_mode": preflight_mode,
        "full_preflight_triggers": full_triggers,
        "owner_surface": (manifest.get("fastPath") or {}).get("receiptVisibility", "internal_unless_true_blocker"),
        "authority_manifest_version": manifest["schemaVersion"],
        "baseline_authority": "FAIL" if initial_blocked else "PASS",
        "local_instructions": local_instructions,
        "routed_packs": packs,
        "required_skills": required_skills_for_request(request_text, domains),
        "required_sources": authorities,
        "required_tools": required_tools,
        "hard_gates": hard_gates,
        "current_evidence_state": (
            "fast_path_authority_resolved" if fast_candidate and not initial_blocked
            else "authority_paths_resolved"
        ),
        "project_preflight": "BLOCKED" if initial_blocked else "PASS",
        "missing_authority_paths": missing,
        "authority_conflicts": binding_problems,
        "creative_execution_authorized": False,
        "delivery_authorized": False,
    }
    receipt["route_resolution"] = "BLOCKED" if initial_blocked else "PASS"
    if creative:
        from vf_publication_evidence import validate
        phase = args.phase or ("delivery" if "instagram_action" in domains else "production")
        if "instagram_action" in domains and phase != "delivery":
            evidence = {"ok": False, "evidence_state": "BLOCKED", "publishAuthorized": False,
                        "problems": ["Instagram actions require delivery evidence"]}
        else:
            evidence = validate(ROOT, args.manifest or "", args.content_id or "", phase)
        receipt["publication_evidence_phase"] = phase
        receipt["production_evidence"] = evidence
        receipt["required_skills"] = ["velvet-creative-director", "velvet-brand-guardian", "velvet-hebrew-copy"]
        receipt["current_evidence_state"] = evidence["evidence_state"]
        evidence_ok = bool(evidence.get("ok")) and not missing and not binding_problems
        receipt["creative_execution_authorized"] = bool(phase == "production" and evidence_ok)
        # Publication evidence is NECESSARY but NOT SUFFICIENT for delivery.
        if phase == "delivery":
            approval_problems, delivery_auth = _evaluate_delivery_approval(
                args,
                evidence_ok=evidence_ok,
            )
            receipt["delivery_approval"] = {
                "required": True,
                "ok": delivery_auth,
                "problems": approval_problems,
                "advisory_only": True,
                "note": "preflight PASS is not mutation capability; mutation endpoint re-verifies + claims",
            }
            receipt["delivery_authorized"] = bool(delivery_auth)
            receipt["project_preflight"] = "PASS" if delivery_auth else "BLOCKED"
        else:
            receipt["project_preflight"] = "PASS" if evidence_ok else "BLOCKED"
            receipt["delivery_authorized"] = False
    else:
        receipt["evidence_scope"] = (
            "minimal authority + scope routing; action postflight remains authoritative"
            if preflight_mode == "FAST_PATH"
            else "authority path resolution only; no action authorization"
        )
    receipt["owner_surface"] = (manifest.get("fastPath") or {}).get(
        "receiptVisibility", "internal_unless_true_blocker"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 2 if receipt["project_preflight"] == "BLOCKED" else 0


def _evaluate_delivery_approval(args: argparse.Namespace, *, evidence_ok: bool) -> tuple[list[str], bool]:
    """Advisory delivery-approval check. Never grants mutation capability by itself."""
    problems: list[str] = []
    if not evidence_ok:
        problems.append("publication evidence invalid")
    raw = (args.delivery_approval or "").strip()
    if not raw:
        problems.append("signed delivery approval missing")
        return problems, False

    import sys

    packages = ROOT / "packages"
    if str(packages) not in sys.path:
        sys.path.insert(0, str(packages))
    from vfigos.approval.keys_registry import KeyRegistry
    from vfigos.approval.verify import verify_receipt

    try:
        if raw.startswith("{"):
            envelope = json.loads(raw)
        else:
            path = Path(raw)
            envelope = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(f"delivery approval unreadable: {exc}")
        return problems, False

    import os
    reg_path = (os.environ.get("VELVET_DELIVERY_APPROVAL_REGISTRY") or "").strip()
    registry = KeyRegistry.from_path(Path(reg_path)) if reg_path else KeyRegistry.from_path()
    vr = verify_receipt(
        envelope,
        registry=registry,
        expected_mutation_tool=(args.mutation_tool or None),
        expected_content_id=(args.content_id or None),
        expected_package_sha256=(args.package_sha256 or None),
    )
    if not vr.ok:
        problems.extend(vr.problems)
        return problems, False
    if problems:
        return problems, False
    return [], True


if __name__ == "__main__":
    raise SystemExit(main())
