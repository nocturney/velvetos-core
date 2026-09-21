#!/usr/bin/env python3
"""Validate VF Project 6.6.9 review-release evidence for publication staging.

This is an adapter, not a second creative gate. It accepts only a completed
Revision 6.6.9 project workspace whose exact release/reviews remain bound to
the final visual, then optionally binds a deterministic transport derivative
through an explicit transport-QA receipt.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

PROJECT_SCHEMA = 6
PROJECT_REVISION = "6.6.9"
PROJECT_BUNDLE_ID = "VF-PROJECT-6.6.9-NATIVE-PRODUCT-EDIT-ROUTING"
SHA64 = re.compile(r"^[0-9a-f]{64}$", re.I)
FINAL_CHECKS = (
    "source_identity", "critical_details", "negative_spaces",
    "scene_no_synthetic_product", "reference_match", "creative_sufficiency",
    "scene_led_composition", "style_anchor_alignment", "creative_continuity",
    "hebrew_rtl", "copy_facts", "brand_assets", "inset_provenance",
    "mobile_readability", "meaningful_graphics", "not_board_wrapper",
    "headline_hierarchy", "environment_not_raw_fallback",
    "negative_space_has_role", "details_add_information",
)
FALLBACK_MASTER_CHECKS = (
    "source_identity", "mask_coverage", "critical_details", "negative_spaces",
    "scene_no_synthetic_product", "reference_match", "creative_sufficiency",
    "scene_led_composition", "style_anchor_alignment",
)
IDENTITY_CHECKS = (
    "silhouette", "proportions", "parts_and_openings", "surface_identity",
    "color_and_finish", "critical_details",
)
NATIVE_CREATIVE_CHECKS = (
    "scene_and_surface", "hero_prominence", "environment_and_light",
    "surface_contact", "distractions_resolved", "negative_space_for_headline",
    "creative_sufficiency", "not_raw_source_plus_text", "reference_alignment",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe(root: Path, rel: str, label: str) -> Path:
    if not isinstance(rel, str) or not rel.strip():
        raise ValueError(f"{label} path missing")
    p = (root / rel).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes repo root") from exc
    if not p.is_file():
        raise ValueError(f"{label} missing: {rel}")
    return p


def _json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ValueError(f"{label} invalid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")
    return data


def _ref(base: Path, ref: Any, label: str) -> Path:
    if not isinstance(ref, dict):
        raise ValueError(f"{label} reference missing")
    rel = ref.get("path")
    sha = str(ref.get("sha256") or "").lower()
    if not SHA64.fullmatch(sha):
        raise ValueError(f"{label} sha256 missing/invalid")
    p = (base / str(rel)).resolve()
    try:
        p.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes project workspace") from exc
    if not p.is_file():
        raise ValueError(f"{label} missing: {rel}")
    actual = digest(p)
    if actual != sha:
        raise ValueError(f"{label} sha256 mismatch")
    return p


def _pass_checks(review: dict[str, Any], names: tuple[str, ...], label: str) -> None:
    checks = review.get("checks")
    if not isinstance(checks, dict):
        raise ValueError(f"{label} checks missing")
    for name in names:
        item = checks.get(name)
        if not isinstance(item, dict) or item.get("verdict") != "PASS":
            raise ValueError(f"{label} check {name} must PASS")
        notes = item.get("notes")
        if not isinstance(notes, str) or not notes.strip():
            raise ValueError(f"{label} check {name} notes missing")


def _package_digest(visual_sha: str, text_sha: str) -> str:
    rows = [
        {"role": "FINAL_VISUAL", "sha256": visual_sha},
        {"role": "FINAL_TEXT", "sha256": text_sha},
    ]
    body = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _caption(root: Path, caption_ref: str | None, receipt_ref: str | None) -> str:
    if not caption_ref or not receipt_ref:
        raise ValueError("caption_ref and caption_receipt_ref are required")
    caption = _safe(root, caption_ref, "caption")
    receipt_path = _safe(root, receipt_ref, "caption receipt")
    receipt = _json(receipt_path, "caption receipt")
    caption_sha = digest(caption)
    if receipt.get("text_sha256") != caption_sha:
        raise ValueError("caption receipt hash mismatch")
    if receipt.get("visible_text_gate") != "PASS":
        raise ValueError("caption visible-text gate did not PASS")
    lint = receipt.get("lint")
    if not isinstance(lint, dict) or lint.get("status") != "pass":
        raise ValueError("caption lint did not PASS")
    return caption_sha


def _transport(root: Path, final_sha: str, ref: str | None, receipt_ref: str | None) -> tuple[str, list[str]]:
    if not ref and not receipt_ref:
        return final_sha, [final_sha]
    if not ref or not receipt_ref:
        raise ValueError("transport_artifact_ref and transport_qa_ref must be provided together")
    transport = _safe(root, ref, "transport artifact")
    receipt_path = _safe(root, receipt_ref, "transport QA receipt")
    receipt = _json(receipt_path, "transport QA receipt")
    transport_sha = digest(transport)
    if receipt.get("schema") != "velvet.project669.transport_qa.v1":
        raise ValueError("transport QA schema mismatch")
    if receipt.get("source_final_sha256") != final_sha:
        raise ValueError("transport QA is not bound to project final")
    if receipt.get("transport_sha256") != transport_sha:
        raise ValueError("transport QA transport hash mismatch")
    if receipt.get("visual_equivalence") != "PASS":
        raise ValueError("transport visual equivalence did not PASS")
    if receipt.get("metadata_stripped") is not True:
        raise ValueError("transport metadata stripping not proven")
    if receipt.get("reviewer_kind") not in {"ASSISTANT_VISION", "OWNER", "HUMAN_REVIEWER"}:
        raise ValueError("transport reviewer kind missing")
    if receipt.get("opened_transport") is not True:
        raise ValueError("transport artifact was not visually reviewed")
    return transport_sha, [final_sha, transport_sha]


def validate(
    root: Path,
    run_ref: str,
    content_id: str,
    format_name: str,
    package_sha256: str,
    transport_artifact_ref: str | None = None,
    transport_qa_ref: str | None = None,
    caption_ref: str | None = None,
    caption_receipt_ref: str | None = None,
) -> dict[str, Any]:
    problems: list[str] = []
    try:
        if format_name not in {"post", "carousel", "story", "reel"}:
            raise ValueError("unsupported publication format")
        if not SHA64.fullmatch((package_sha256 or "").lower()):
            raise ValueError("package_sha256 must be 64 hex")
        run_path = _safe(root, run_ref, "project run")
        run = _json(run_path, "project run")
        ws = run_path.parent
        if run.get("schema") != PROJECT_SCHEMA:
            raise ValueError("project run schema must be 6")
        if run.get("revision") != PROJECT_REVISION:
            raise ValueError("project run revision must be 6.6.9")
        if run.get("bundle_id") != PROJECT_BUNDLE_ID:
            raise ValueError("project bundle id mismatch")
        if run.get("fixture") is not False:
            raise ValueError("fixture project run cannot authorize publication")

        source_shas: set[str] = set()
        sources = run.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError("project sources missing")
        for idx, row in enumerate(sources):
            if not isinstance(row, dict):
                raise ValueError("project source row invalid")
            _ref(ws, row.get("file"), f"source {idx+1}")
            _ref(ws, row.get("ingest"), f"source ingest {idx+1}")
            source_shas.add(row["file"]["sha256"])

        candidate = run.get("candidate") or {}
        route = candidate.get("route")
        if route not in {"SOURCE_COMPOSITE", "NATIVE_PRODUCT_EDIT"}:
            raise ValueError("unsupported project route")
        _ref(ws, candidate.get("file"), "candidate")
        _ref(ws, candidate.get("mobile"), "candidate mobile")
        proof_path = _ref(ws, candidate.get("proof"), "product proof")
        product_proof = _json(proof_path, "product proof")
        if product_proof.get("publication_authorized") is not False:
            raise ValueError("project proof publication_authorized must remain false")
        if route == "SOURCE_COMPOSITE":
            if product_proof.get("source_pixel_integrity") != "PASS":
                raise ValueError("source composite pixel integrity did not PASS")
        else:
            if product_proof.get("source_pixel_integrity") != "NOT_APPLICABLE_NATIVE_EDIT":
                raise ValueError("native product proof marker mismatch")
            ir_ref = run.get("identity_review")
            cr_ref = run.get("creative_review")
            ir = _json(_ref(ws, ir_ref, "native identity review"), "native identity review")
            cr = _json(_ref(ws, cr_ref, "native creative review"), "native creative review")
            if ir.get("overall") != "PASS" or cr.get("overall") != "PASS":
                raise ValueError("native identity/creative review must PASS")
            _pass_checks(ir, IDENTITY_CHECKS, "native identity")
            _pass_checks(cr, NATIVE_CREATIVE_CHECKS, "native creative")

        master = run.get("master") or {}
        master_path = _ref(ws, master.get("file"), "creative master")
        _ref(ws, master.get("materialization"), "master materialization")
        master_evidence_path = _ref(ws, master.get("evidence"), "master evidence")
        master_evidence = _json(master_evidence_path, "master evidence")
        if master.get("route") != route or master_evidence.get("route") != route:
            raise ValueError("master route binding mismatch")
        if route == "SOURCE_COMPOSITE":
            fallback_ref = (master_evidence.get("reviews") or {}).get("fallback")
            fallback = _json(_ref(ws, fallback_ref, "fallback master review"), "fallback master review")
            _pass_checks(fallback, FALLBACK_MASTER_CHECKS, "fallback master")
            if fallback.get("candidate_sha256") != candidate["file"]["sha256"]:
                raise ValueError("fallback master review candidate mismatch")
            if set(fallback.get("source_sha256") or []) != source_shas:
                raise ValueError("fallback master review source mismatch")

        final = run.get("final") or {}
        final_path = _ref(ws, final.get("file"), "project final")
        mobile_path = _ref(ws, final.get("mobile"), "project final mobile")
        proof_path = _ref(ws, final.get("proof"), "final proof")
        final_proof = _json(proof_path, "final proof")
        _ref(ws, final.get("spec"), "final spec")
        if final_proof.get("copy_lexical_checks") != "PASS":
            raise ValueError("final copy lexical checks did not PASS")
        if (final_proof.get("final") or {}).get("sha256") != final["file"]["sha256"]:
            raise ValueError("final proof final binding mismatch")
        if (final_proof.get("mobile") or {}).get("sha256") != final["mobile"]["sha256"]:
            raise ValueError("final proof mobile binding mismatch")
        if (final_proof.get("compositor_input") or {}).get("sha256") != master["file"]["sha256"]:
            raise ValueError("final compositor is not bound to creative master")

        release_path = _ref(ws, run.get("release"), "release")
        release = _json(release_path, "release")
        if release.get("scope") != "REVIEW_ARTIFACT_ONLY":
            raise ValueError("release scope must be REVIEW_ARTIFACT_ONLY")
        if release.get("review_delivery_authorized") is not True:
            raise ValueError("review release is not authorized")
        if release.get("publication_authorized") is not False:
            raise ValueError("project runner must not self-authorize publication")
        if release.get("final_qa") != "EXACT_FILE_REVIEWER_ATTESTED_PASS":
            raise ValueError("project final QA did not PASS")
        if release.get("source_ingest") != "PASS":
            raise ValueError("project source ingest did not PASS")
        if release.get("route") != route:
            raise ValueError("release route mismatch")
        if (release.get("artifact") or {}).get("sha256") != final["file"]["sha256"]:
            raise ValueError("release artifact mismatch")

        review_path = _ref(ws, release.get("review"), "final review")
        review = _json(review_path, "final review")
        _pass_checks(review, FINAL_CHECKS, "final review")
        if review.get("reviewer_kind") not in {"ASSISTANT_VISION", "OWNER", "HUMAN_REVIEWER"}:
            raise ValueError("final reviewer kind missing")
        if review.get("opened_full_size") is not True or review.get("opened_mobile") is not True:
            raise ValueError("final full/mobile review not attested")
        if review.get("final_sha256") != final["file"]["sha256"]:
            raise ValueError("final review hash mismatch")
        if review.get("mobile_sha256") != final["mobile"]["sha256"]:
            raise ValueError("final mobile review hash mismatch")
        if review.get("master_sha256") != master["file"]["sha256"]:
            raise ValueError("final review master mismatch")
        if set(review.get("source_sha256") or []) != source_shas:
            raise ValueError("final review source mismatch")

        final_sha = digest(final_path)
        if final_sha in source_shas:
            raise ValueError("final visual cannot be a raw source")
        transport_sha, visual_hashes = _transport(
            root, final_sha, transport_artifact_ref, transport_qa_ref
        )
        caption_sha = _caption(root, caption_ref, caption_receipt_ref)
        computed_package = _package_digest(transport_sha, caption_sha)
        if computed_package != package_sha256.lower():
            raise ValueError("exact final package SHA-256 mismatch")
        result = {
            "ok": True,
            "publishAuthorized": True,
            "adapter": "VF_PROJECT_6_6_9_RELEASE",
            "contentId": content_id,
            "format": format_name,
            "projectRun": run_ref,
            "route": route,
            "projectFinalSha256": final_sha,
            "transportSha256": transport_sha,
            "captionSha256": caption_sha,
            "packageSha256": computed_package,
            "visualHashes": visual_hashes,
            "sourceHashes": sorted(source_shas),
            "problems": [],
            "rule": "project review release + exact owner publication approval; runner publication_authorized remains false",
        }
        return result
    except Exception as exc:
        problems.append(str(exc))
        return {
            "ok": False,
            "publishAuthorized": False,
            "adapter": "VF_PROJECT_6_6_9_RELEASE",
            "contentId": content_id,
            "format": format_name,
            "visualHashes": [],
            "problems": problems,
        }
