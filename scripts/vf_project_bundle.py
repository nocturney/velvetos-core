#!/usr/bin/env python3
"""Resolve the active ChatGPT Project bundle from the canonical authority manifest.

This module deliberately avoids hard-coding a Project revision into validators.
Historical bundle files may stay in git, but executable gates resolve only the
bundle declared by packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT_AUTHORITY_MANIFEST = Path("packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json")
CANONICAL_AUTHORITY_FILENAME = "Velvet-Factory-Project-Authority-v6.txt"
AESTHETIC_REFERENCE_KEYS = ("broad_visual", "editorial_layout", "current_direction")
EXPECTED_AESTHETIC_ROLES = {
    "broad_visual": "broad_style_only",
    "editorial_layout": "editorial_layout_and_annotation_style_only",
    "current_direction": "current_owner_approved_direction_style_only_not_product_source",
}
EXPECTED_PRODUCT_TRUTH_GUIDE_ROLE = "text_only_product_truth_fidelity_qa_not_style"


def _json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} cannot be decoded: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _workspace_relative(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} missing")
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"{label} must be workspace-relative")
    return rel


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_project_bundle(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    manifest_rel = PROJECT_AUTHORITY_MANIFEST
    manifest_path = root / manifest_rel
    project_manifest = _json_object(manifest_path, "Project Authority Manifest")
    bundle = project_manifest.get("chatgptProjectBundle")
    if not isinstance(bundle, dict):
        raise ValueError("chatgptProjectBundle missing from Project Authority Manifest")

    contract = bundle.get("contractVersion")
    revision = bundle.get("revision")
    bundle_id = bundle.get("bundleId")
    if not isinstance(contract, int) or not isinstance(revision, str) or not isinstance(bundle_id, str):
        raise ValueError("chatgptProjectBundle identity is incomplete")

    authority_rel = _workspace_relative(bundle.get("authority"), "chatgptProjectBundle.authority")
    assets_rel = _workspace_relative(bundle.get("assetManifest"), "chatgptProjectBundle.assetManifest")
    instructions_rel = _workspace_relative(bundle.get("instructions"), "chatgptProjectBundle.instructions")
    guide_rel = _workspace_relative(bundle.get("productTruthGuide"), "chatgptProjectBundle.productTruthGuide")
    for rel, label in (
        (authority_rel, "Project Authority"),
        (assets_rel, "Project asset manifest"),
        (instructions_rel, "Project Instructions"),
        (guide_rel, "Product Truth guide"),
    ):
        path = root / rel
        if not path.is_file():
            raise ValueError(f"{label} missing: {rel.as_posix()}")

    authority_path = root / authority_rel
    assets_path = root / assets_rel
    instructions_path = root / instructions_rel
    guide_path = root / guide_rel
    authority_text = authority_path.read_text(encoding="utf-8")
    expected_needles = (
        f"Contract version: {contract}",
        f"Revision: {revision}",
        f"Bundle: {bundle_id}",
    )
    if not all(needle in authority_text for needle in expected_needles):
        raise ValueError("Project Authority identity does not match chatgptProjectBundle")

    asset_manifest = _json_object(assets_path, "Project asset manifest")
    identity = (
        asset_manifest.get("contract_version"),
        asset_manifest.get("revision"),
        asset_manifest.get("bundle_id"),
    )
    if identity != (contract, revision, bundle_id):
        raise ValueError("Project asset manifest identity does not match chatgptProjectBundle")

    rows = asset_manifest.get("assets")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Project asset manifest assets must be an array of objects")
    by_filename = {row.get("filename"): row for row in rows if isinstance(row.get("filename"), str)}

    authority_row = by_filename.get(CANONICAL_AUTHORITY_FILENAME)
    if not isinstance(authority_row, dict) or authority_row.get("sha256") != _sha256(authority_path):
        raise ValueError("Project Authority bytes are not bound by the active asset manifest")

    instructions_meta = asset_manifest.get("instructions")
    if not isinstance(instructions_meta, dict) or instructions_meta.get("sha256") != _sha256(instructions_path):
        raise ValueError("Project Instructions bytes do not match the active asset manifest")

    current_refs = asset_manifest.get("current_references")
    if not isinstance(current_refs, dict):
        raise ValueError("current_references missing from active asset manifest")
    aesthetic_rows: list[dict[str, Any]] = []
    aesthetic_hashes: set[str] = set()
    for key in AESTHETIC_REFERENCE_KEYS:
        filename = current_refs.get(key)
        if not isinstance(filename, str) or not filename:
            raise ValueError(f"current_references.{key} missing")
        row = by_filename.get(filename)
        if not isinstance(row, dict):
            raise ValueError(f"active aesthetic reference missing from asset rows: {filename}")
        if row.get("role") != EXPECTED_AESTHETIC_ROLES[key]:
            raise ValueError(f"active aesthetic reference has wrong role: {filename}")
        sha = row.get("sha256")
        if not isinstance(sha, str) or len(sha) != 64:
            raise ValueError(f"active aesthetic reference has invalid SHA-256: {filename}")
        aesthetic_rows.append(row)
        aesthetic_hashes.add(sha)
    if len(aesthetic_hashes) != len(AESTHETIC_REFERENCE_KEYS):
        raise ValueError("active aesthetic reference identities must be distinct")

    truth = asset_manifest.get("product_truth")
    if not isinstance(truth, dict):
        raise ValueError("product_truth block missing from active asset manifest")
    guide_filename = truth.get("guide")
    guide_row = by_filename.get(guide_filename)
    if not isinstance(guide_filename, str) or not isinstance(guide_row, dict):
        raise ValueError("Product Truth guide is not bound by the active asset manifest")
    guide_sha = guide_row.get("sha256")
    if guide_row.get("role") != EXPECTED_PRODUCT_TRUTH_GUIDE_ROLE:
        raise ValueError("Product Truth guide role must remain fidelity-QA-only, not style")
    if not isinstance(guide_sha, str) or guide_sha != _sha256(guide_path):
        raise ValueError("Product Truth guide bytes do not match the active asset manifest")
    if guide_sha in aesthetic_hashes:
        raise ValueError("Product Truth guide must remain separate from aesthetic references")
    if truth.get("visual_conditioning") != "FORBIDDEN":
        raise ValueError("Product Truth visual conditioning must remain FORBIDDEN")

    return {
        "manifest_path": manifest_rel,
        "manifest": project_manifest,
        "bundle": bundle,
        "contract": contract,
        "revision": revision,
        "bundle_id": bundle_id,
        "authority_path": authority_rel,
        "asset_manifest_path": assets_rel,
        "instructions_path": instructions_rel,
        "product_truth_guide_path": guide_rel,
        "authority_sha256": _sha256(authority_path),
        "asset_manifest_sha256": _sha256(assets_path),
        "instructions_sha256": _sha256(instructions_path),
        "product_truth_guide_sha256": guide_sha,
        "asset_manifest": asset_manifest,
        "aesthetic_reference_rows": aesthetic_rows,
        "aesthetic_reference_sha256s": aesthetic_hashes,
    }