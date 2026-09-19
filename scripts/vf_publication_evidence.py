#!/usr/bin/env python3
"""Validate VF publication evidence in the existing Creative Manifest.

Read-only, offline, no publication. Checks file integrity and required review
receipts, NOT aesthetic correctness, receipt authorship, or provider invocation.
All stage approvals must still be produced by the actual office workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vf_media_integrity import inspect_media

POLICY = "packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json"
AUTHORITY = "packages/velvetos/chatgpt-project/PROJECT-AUTHORITY-v6.4.txt"
ASSETS = "packages/velvetos/chatgpt-project/ASSET-MANIFEST-v6.4.json"
ASSETS_SHA = "2d0d91cf94215e107fc0ccb1a4bb9d4e1a479dceb6c7f25dcf8901e6e5749091"
AUTHORITY_SHA = "b3c2b5a66c395a7e1d60b6cddb532443876e4144f189c4835512ff3283c5112a"
PROJECT_CONTRACT_VERSION = 6
PROJECT_REVISION = "6.4"
PROJECT_BUNDLE_ID = "VF-PROJECT-6.4-AESTHETIC-TRUTH-SEPARATION"
PRODUCT_TRUTH_GUIDE = "packages/velvetos/chatgpt-project/PRODUCT-TRUTH-GUIDE-v1.txt"
REJECTED_PRODUCT_TRUTH_REFERENCE_SHA256 = "17c3a4deeebb566b7566e3e69257c03b666fcc92436c78e824efbccf627e6dc9"
STAGES = ("authority", "source_lock", "product_truth_lock", "reference_decomposition",
          "creative_director", "source_grounded_production", "visible_text",
          "brand_guardian", "exact_final_qa")
AXES = ("product_to_frame", "environment", "light", "depth", "negative_space",
        "hierarchy", "typography", "details", "surfaces", "accent")
CHECKS = ("source_match", "reference_match", "copy_checked", "brand_checked", "final_qa")
HEX = re.compile(r"[0-9a-f]{64}")
EMPTY = {"", "NONE", "N/A", "PENDING", "UNPROVEN", "_", "TODO"}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text_digest_candidates(path: Path) -> set[str]:
    """Canonical text identity plus Git CRLF checkout equivalent."""
    raw = path.read_bytes()
    return {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
    }


def package_digest(assets: list[dict[str, Any]]) -> str:
    """Ordered outputs including caption/overlay text; paths are not identity."""
    rows = [{"role": x["role"], "sha256": x["sha256"]} for x in assets]
    body = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def meaningful(value: Any) -> bool:
    return isinstance(value, str) and value.strip().upper() not in EMPTY and "<" not in value


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _rows(value: Any, label: str, nonempty: bool = True) -> list:
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(f"{label} must be {'a nonempty ' if nonempty else 'an '}array")
    return value


def local_path(root: Path, value: Any) -> Path:
    if not meaningful(value):
        raise ValueError("missing/placeholder evidence path")
    rel = Path(value)
    if rel.is_absolute() or re.match(r"^[A-Za-z]:|^[/\\]|^[A-Za-z]+://", value):
        raise ValueError("evidence paths must be workspace-relative, not URL/absolute paths")
    path = (root / rel).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("evidence path escapes workspace") from exc
    if not path.is_file():
        raise ValueError(f"missing evidence file: {value}")
    if path.stat().st_size == 0:
        raise ValueError(f"empty evidence file: {value}")
    return path


def load_json(path: Path, expected_sha256: str | None = None) -> dict:
    with path.open("rb") as stream:
        raw = stream.read(2 * 1024 * 1024 + 1)
    if expected_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("creative manifest bytes differ from the approval-bound SHA-256")
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("JSON evidence exceeds 2 MiB")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON field: {key}")
            result[key] = value
        return result
    return _object(json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique), str(path))


def verify_ref(root: Path, ref: Any, label: str, denied: set[str]) -> Path:
    obj = _object(ref, label)
    sha = obj.get("sha256")
    if not isinstance(sha, str) or not HEX.fullmatch(sha):
        raise ValueError(f"{label}: invalid SHA-256")
    if sha in denied:
        raise ValueError(f"{label}: REJECTED_FOR_REUSE artifact")
    path = local_path(root, obj.get("path"))
    if digest(path) != sha:
        raise ValueError(f"{label}: file bytes differ from recorded SHA-256")
    return path


def timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("stage timestamp missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed > datetime.now(timezone.utc):
        raise ValueError("stage timestamp must have timezone and cannot be in future")
    return parsed


def validate(root: Path, manifest_ref: str, content_id: str,
             phase: str = "delivery", expected_package: str | None = None, expected_format: str | None = None, expected_manifest_sha256: str | None = None, require_staging: bool = False) -> dict:
    """Fail closed, including malformed input; never update state or send content."""
    try:
        return _validate(root.resolve(), manifest_ref, content_id, phase, expected_package, expected_format, expected_manifest_sha256, require_staging)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
        return {"ok": False, "phase": phase, "problems": [str(exc)],
                "evidence_state": "BLOCKED", "publishAuthorized": False}


def _validate(root, manifest_ref, content_id, phase, expected_package, expected_format, expected_manifest_sha256, require_staging):
    if phase not in {"production", "delivery"}:
        raise ValueError("unknown evidence phase")
    policy = load_json(local_path(root, POLICY))
    route = _object(policy.get("publicationRoute"), "publicationRoute")
    if route.get("version") != 1 or route.get("mode") != "fail_closed":
        raise ValueError("publication route policy missing or unsupported")
    authority = local_path(root, AUTHORITY)
    if AUTHORITY_SHA not in text_digest_candidates(authority):
        raise ValueError(f"Project Authority is not verified revision {PROJECT_REVISION}")
    assets_path = local_path(root, ASSETS)
    if ASSETS_SHA not in text_digest_candidates(assets_path):
        raise ValueError(f"Project asset manifest bytes do not match verified revision {PROJECT_REVISION}")
    asset_manifest = load_json(assets_path)
    expected_identity = (PROJECT_CONTRACT_VERSION, PROJECT_REVISION, PROJECT_BUNDLE_ID)
    actual_identity = (
        asset_manifest.get("contract_version"),
        str(asset_manifest.get("revision")),
        asset_manifest.get("bundle_id"),
    )
    if actual_identity != expected_identity:
        raise ValueError("Project asset manifest revision mismatch")
    asset_rows = _rows(asset_manifest.get("assets"), "asset manifest assets")
    product_truth = _object(asset_manifest.get("product_truth"), "product_truth")
    if product_truth.get("visual_conditioning") != "FORBIDDEN":
        raise ValueError("Product Truth visual conditioning must remain FORBIDDEN")
    guide_filename = product_truth.get("guide")
    if not meaningful(guide_filename):
        raise ValueError("Product Truth guide filename missing")
    guide_rows = [
        row for row in asset_rows
        if row.get("filename") == guide_filename
        and row.get("role") == "text_only_product_truth_fidelity_qa_not_style"
        and row.get("required_for") == "visual_work"
    ]
    if len(guide_rows) != 1:
        raise ValueError("exactly one text-only Product Truth guide identity required")
    guide_sha = guide_rows[0].get("sha256")
    if not isinstance(guide_sha, str) or not HEX.fullmatch(guide_sha):
        raise ValueError("Product Truth guide has invalid SHA-256")
    guide_path = local_path(root, PRODUCT_TRUTH_GUIDE)
    if guide_sha not in text_digest_candidates(guide_path):
        raise ValueError("Product Truth guide bytes do not match the v6.4 asset manifest")
    current_refs = _object(asset_manifest.get("current_references"), "current_references")
    style_names = {name for name in current_refs.values() if meaningful(name)}
    if len(style_names) != 3:
        raise ValueError("exactly three current aesthetic reference filenames required")
    style_rows = [
        row for row in asset_rows
        if row.get("filename") in style_names and row.get("required_for") == "visual_work"
    ]
    if {row.get("filename") for row in style_rows} != style_names:
        raise ValueError("current aesthetic reference files are not fully bound in asset manifest")
    required_refs = {row.get("sha256") for row in style_rows}
    if len(required_refs) != 3 or any(not isinstance(sha, str) or not HEX.fullmatch(sha) for sha in required_refs):
        raise ValueError("all three canonical aesthetic reference identities required")
    denied = set(_rows(route.get("rejectedArtifactSha256"), "rejectedArtifactSha256"))
    if REJECTED_PRODUCT_TRUTH_REFERENCE_SHA256 not in denied:
        raise ValueError("rejected Product Truth teaching-sheet identity is not denied by publication policy")
    manifest = load_json(local_path(root, manifest_ref), expected_manifest_sha256)
    if manifest.get("jobId") != content_id:
        raise ValueError("manifest/content ID mismatch")
    if manifest.get("format") not in {"post", "carousel", "story", "reel"}:
        raise ValueError("manifest format is missing or invalid")
    if expected_format is not None and manifest["format"] != expected_format:
        raise ValueError("manifest format differs from the requested publication format")
    ev = _object(manifest.get("publicationEvidence"), "publicationEvidence")
    if ev.get("version") != 1 or ev.get("policy_sha256") != digest(root / POLICY):
        raise ValueError("missing/stale publication evidence policy binding")
    if ev.get("public_intent") not in {"showcase", "commercial"}:
        raise ValueError("public intent must be selected before production")
    direction = _object(ev.get("direction"), "direction")
    family = direction.get("family_id")
    if not meaningful(family) or direction.get("status") != "LOCKED":
        raise ValueError("direction must have a concrete locked family")
    rejected_families = set(route.get("rejectedDirectionFamilies", []))
    for event in _rows(ev.get("direction_history", []), "direction_history", False):
        _object(event, "direction event")
        if event.get("decision") == "REJECT_DIRECTION":
            rejected_families.add(event.get("family_id"))
    lineage = _rows(direction.get("derived_from_families", []), "direction lineage", False)
    if family in rejected_families or any(x in rejected_families for x in lineage):
        raise ValueError("REJECTED_FOR_REUSE: direction family or parent rejected")
    tools = _rows(ev.get("tools"), "tools")
    for tool in tools:
        if not meaningful(tool) or "canva" in tool.casefold():
            raise ValueError("Canva/vfcanva prohibited in VF publication route")
    sources = _rows(ev.get("sources"), "sources")
    source_shas = set()
    for src in sources:
        source_path = verify_ref(root, src, "source", denied)
        if src.get("role") != "PRODUCT_SOURCE" or src["sha256"] in required_refs:
            raise ValueError("STYLE_ONLY/generated references cannot be product sources")
        inspect_media(source_path, "product source", source=True)
        source_shas.add(src["sha256"])
    refs = _rows(ev.get("references"), "references")
    ref_shas = set()
    for ref in refs:
        verify_ref(root, ref, "reference", denied)
        if ref.get("role") != "STYLE_ONLY":
            raise ValueError("reference role must remain STYLE_ONLY")
        ref_shas.add(ref["sha256"])
    if ref_shas != required_refs:
        raise ValueError("reference identities do not match all three canonical sources")
    decomposition = load_json(verify_ref(root, ev.get("reference_decomposition"), "reference decomposition", denied))
    if set(decomposition.get("reference_sha256", [])) != required_refs:
        raise ValueError("reference decomposition is not bound to current references")
    if any(not meaningful(decomposition.get(axis)) for axis in AXES):
        raise ValueError("reference decomposition has missing/placeholder visual axes")
    protection = _object(ev.get("product_protection"), "product_protection")
    if protection.get("method") not in {"PROTECTED_SOURCE_PIXELS", "SOURCE_MASK_COMPOSITE", "SOURCE_VIDEO_EDIT"}:
        raise ValueError("source protection mechanism required; prompt alone is not proof")
    verify_ref(root, protection.get("evidence"), "product protection evidence", denied)
    if not _rows(protection.get("protected_regions"), "protected_regions"):
        raise ValueError("protected product regions missing")
    steps = _rows(ev.get("stages"), "stages")
    required_stages = STAGES if phase == "delivery" else STAGES[:5]
    if len(steps) != len(required_stages):
        raise ValueError("stage count must match the requested phase exactly")
    if [x.get("name") for x in steps] != list(required_stages):
        raise ValueError("required stages missing or out of order")
    prior = None
    for step in steps[:len(required_stages)]:
        if step.get("status") != "PASS":
            raise ValueError(f"stage {step['name']} is not PASS")
        start, end = timestamp(step.get("started_at")), timestamp(step.get("completed_at"))
        if end < start or (prior and start < prior):
            raise ValueError("stage chronology invalid; later checks cannot excuse earlier omissions")
        prior = end
        stage_shas = set()
        for ref in _rows(step.get("evidence"), "stage evidence"):
            verify_ref(root, ref, f"stage {step['name']}", denied)
            stage_shas.add(ref.get("sha256"))
        if step.get("name") == "product_truth_lock" and guide_sha not in stage_shas:
            raise ValueError("product_truth_lock is not bound to the exact v6.4 Product Truth guide")
    if phase == "production":
        return {"ok": True, "phase": phase, "evidence_state": "INPUT_EVIDENCE_VALIDATED",
                "problems": [], "publishAuthorized": False}
    outputs = _rows(ev.get("outputs"), "outputs")
    if not any(x.get("role") == "FINAL_VISUAL" for x in outputs):
        raise ValueError("no final visual artifact")
    visual_info = {}
    for out in outputs:
        output_path = verify_ref(root, out, "final output", denied)
        if out.get("role") == "FINAL_VISUAL":
            visual_info[out["sha256"]] = inspect_media(output_path, "final visual")
            if require_staging:
                from vf_publish_bridge import (inspect_reviewed_asset, load_config,
                                               verify_image_normalization, verify_video_normalization)
                cfg = load_config()
                inspect_reviewed_asset(output_path, cfg)
                master_ref = out.get("normalization_source")
                master = verify_ref(root, master_ref, "normalization source", denied)
                if visual_info[out["sha256"]]["kind"] == "image":
                    verify_image_normalization(master, master_ref["sha256"], out["sha256"], cfg)
                else:
                    verify_video_normalization(master, master_ref["sha256"], out["sha256"], cfg)
        if out.get("role") not in {"FINAL_VISUAL", "FINAL_TEXT"}:
            raise ValueError("invalid final output role")
        if out["sha256"] in source_shas | ref_shas:
            raise ValueError("raw passthrough/reference is not a finished output")
    text_hashes = {x["sha256"] for x in outputs if x["role"] == "FINAL_TEXT"}
    copy_receipts = _rows(ev.get("copy_receipts", []), "copy receipts", False)
    checked_text = set()
    for receipt_ref in copy_receipts:
        receipt = load_json(verify_ref(root, receipt_ref, "copy lint receipt", denied))
        if receipt.get("visible_text_gate") != "PASS" or (receipt.get("lint") or {}).get("status") != "pass":
            raise ValueError("actual copy lint receipt must pass")
        if receipt.get("surface") not in {"public-social", "visual-microcopy"}:
            raise ValueError("copy receipt has the wrong surface")
        checked_text.add(receipt.get("text_sha256"))
    if checked_text != text_hashes:
        raise ValueError("every exact final text requires its own matching copy lint receipt")
    computed = package_digest(outputs)
    if ev.get("package_sha256") != computed or (expected_package is not None and expected_package != computed):
        raise ValueError("ordered final package differs from recorded/approved package")
    review = load_json(verify_ref(root, ev.get("review"), "exact-final review", denied))
    if review.get("job_id") != content_id or review.get("package_sha256") != computed:
        raise ValueError("review is not bound to this exact job/package")
    if set(review.get("source_sha256", [])) != source_shas or set(review.get("reference_sha256", [])) != ref_shas:
        raise ValueError("review source/reference identities mismatch")
    checks = _object(review.get("checks"), "review checks")
    if any(checks.get(k) != "PASS" for k in CHECKS):
        raise ValueError("source/reference/copy/brand/final review gates must independently pass")
    if review.get("synthetic_subject_change") != "NONE":
        raise ValueError("synthetic product change forbidden")
    if not meaningful(review.get("reviewer")) or not meaningful(review.get("reference_match_observations")):
        raise ValueError("reviewer and concrete reference-match observations required")
    review_time = timestamp(review.get("reviewed_at"))
    if review_time < timestamp(steps[-1]["started_at"]) or review_time > timestamp(steps[-1]["completed_at"]):
        raise ValueError("exact-final review must occur within the final QA stage")
    visuals = [x for x in outputs if x["role"] == "FINAL_VISUAL"]
    views = _rows(review.get("views"), "full/mobile review views")
    if {x.get("artifact_sha256") for x in views} != {x["sha256"] for x in visuals}:
        raise ValueError("every exact final visual requires full/mobile review views")
    for view in views:
        full = verify_ref(root, view.get("full"), "full review view", denied)
        mobile = verify_ref(root, view.get("mobile"), "mobile review view", denied)
        # The delivered artifact determines validation, not an aliased full-view suffix.
        media = visual_info[view["artifact_sha256"]]
        preview = inspect_media(mobile, "mobile review view")
        fw, fh = media["width"], media["height"]
        mw, mh = preview["width"], preview["height"]
        if not (0 < mw < fw and 0 < mh < fh and abs(mw / mh - fw / fh) < 0.02):
            raise ValueError("mobile preview must be smaller and preserve the full image aspect ratio")
        if view["full"]["sha256"] != view["artifact_sha256"]:
            raise ValueError("full review view is not the exact delivered visual")
        if view["mobile"]["sha256"] == view["full"]["sha256"]:
            raise ValueError("mobile review view must be a separate reduced-size preview")
    return {"ok": True, "phase": phase, "problems": [], "packageSha256": computed,
            "artifact_exists": True, "evidence_state": "FILES_AND_REVIEW_BINDINGS_VALIDATED",
            "visualHashes": [x["sha256"] for x in visuals],
            "textHashes": sorted(text_hashes),
            "limitation": "Integrity of submitted evidence is verified; visual judgment and tool/receipt authorship are not independently attested.",
            "publishAuthorized": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--content-id", required=True)
    parser.add_argument("--phase", choices=("production", "delivery"), default="delivery")
    parser.add_argument("--package-sha256")
    args = parser.parse_args()
    result = validate(Path(__file__).resolve().parents[1], args.manifest, args.content_id,
                      args.phase, args.package_sha256)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
