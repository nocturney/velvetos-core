#!/usr/bin/env python3
"""Resolve the active ChatGPT Project bundle from the selected instance surface.

The Project Authority manifest stores logical `instance:surface:chatgptProject/*`
references. This resolver maps them through VelvetOS instance resolution, so the
instance owns the distribution bytes while Core retains only the interface and
trust pins.

Fail-closed: Core checkout callers must select an instance explicitly (or via
VELVETOS_INSTANCE_ID). Missing/malformed references, traversal, missing files,
revision mismatches, and invalid SHA-256 pins all raise ProjectBundleError.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from vf_project_distribution import ProjectDistributionError, resolve_distribution

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REL = Path("packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json")
SURFACE_PREFIX = "instance:surface:"
CHATGPT_SURFACE = "chatgptProject"
HEX64 = re.compile(r"[0-9a-f]{64}")
REVISION_RE = re.compile(r"\d+\.\d+(?:\.\d+)?")


class ProjectBundleError(ValueError):
    pass


@dataclass(frozen=True)
class ProjectBundle:
    contract_version: int
    revision: str
    bundle_id: str
    authority: str
    asset_manifest: str
    instructions: str
    product_truth_guide: str
    authority_sha256: str
    asset_manifest_sha256: str


def _safe_relative(value: str, *, label: str) -> Path:
    raw = Path(value)
    if raw.is_absolute() or re.match(r"^[A-Za-z]:", value) or ".." in raw.parts:
        raise ProjectBundleError(f"{label} must be a safe relative path")
    return raw


def resolve_reference(
    root: str | Path,
    reference: str,
    *,
    instance_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Resolve repo-relative or instance-surface references to an existing file."""
    repo = Path(root).resolve()
    ref = str(reference).strip()
    if not ref:
        raise ProjectBundleError("empty project reference")

    if ref.startswith(SURFACE_PREFIX):
        rest = ref[len(SURFACE_PREFIX):]
        if "/" not in rest:
            raise ProjectBundleError(f"malformed instance surface reference: {ref}")
        surface, rel_text = rest.split("/", 1)
        if surface != CHATGPT_SURFACE:
            raise ProjectBundleError(f"unsupported project surface {surface!r}")
        rel = _safe_relative(rel_text, label=ref)
        try:
            base = resolve_distribution(
                repo,
                instance_id=instance_id,
                env=os.environ if env is None else env,
            )
        except ProjectDistributionError as exc:
            raise ProjectBundleError(str(exc)) from exc
        candidate = (base / rel).resolve()
        try:
            candidate.relative_to(base.resolve())
        except ValueError as exc:
            raise ProjectBundleError(f"project surface reference escapes distribution: {ref}") from exc
    else:
        rel = _safe_relative(ref, label=ref)
        candidate = (repo / rel).resolve()
        try:
            candidate.relative_to(repo)
        except ValueError as exc:
            raise ProjectBundleError(f"project reference escapes repository: {ref}") from exc

    if not candidate.is_file():
        raise ProjectBundleError(f"project reference file missing: {ref}")
    return candidate


def resolve(
    root: Path = ROOT,
    manifest_rel: Path = MANIFEST_REL,
    *,
    instance_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> ProjectBundle:
    root = Path(root).resolve()
    path = root / manifest_rel
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ProjectBundleError(f"cannot read {manifest_rel}: {exc}") from exc
    raw = manifest.get("chatgptProjectBundle")
    if not isinstance(raw, dict):
        raise ProjectBundleError("chatgptProjectBundle missing from Project Authority manifest")

    def field(name: str) -> str:
        value = raw.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ProjectBundleError(f"chatgptProjectBundle.{name} missing")
        return value.strip()

    contract = raw.get("contractVersion")
    if not isinstance(contract, int) or isinstance(contract, bool) or contract < 1:
        raise ProjectBundleError("chatgptProjectBundle.contractVersion must be a positive integer")
    revision = field("revision")
    if not REVISION_RE.fullmatch(revision):
        raise ProjectBundleError(f"chatgptProjectBundle.revision {revision!r} is not a revision number")
    bundle_id = field("bundleId")
    if f"-{revision}-" not in bundle_id:
        raise ProjectBundleError(f"bundleId {bundle_id!r} does not carry revision {revision}")

    refs = {name: field(name) for name in ("authority", "assetManifest", "instructions", "productTruthGuide")}
    for name in ("authority", "assetManifest", "instructions"):
        filename = refs[name].replace("\\", "/").rsplit("/", 1)[-1]
        if f"-v{revision}." not in filename:
            raise ProjectBundleError(f"chatgptProjectBundle.{name} {refs[name]!r} is not the v{revision} file")

    resolved: dict[str, str] = {}
    for name, ref in refs.items():
        candidate = resolve_reference(root, ref, instance_id=instance_id, env=env)
        try:
            resolved[name] = candidate.relative_to(root).as_posix()
        except ValueError as exc:
            raise ProjectBundleError(f"resolved project reference is outside repository: {ref}") from exc

    hashes = {name: field(name) for name in ("authoritySha256", "assetManifestSha256")}
    for name, value in hashes.items():
        if not HEX64.fullmatch(value):
            raise ProjectBundleError(f"chatgptProjectBundle.{name} is not a lowercase SHA-256")

    return ProjectBundle(
        contract_version=contract,
        revision=revision,
        bundle_id=bundle_id,
        authority=resolved["authority"],
        asset_manifest=resolved["assetManifest"],
        instructions=resolved["instructions"],
        product_truth_guide=resolved["productTruthGuide"],
        authority_sha256=hashes["authoritySha256"],
        asset_manifest_sha256=hashes["assetManifestSha256"],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--instance-id")
    args = ap.parse_args()
    try:
        bundle = resolve(args.root, instance_id=args.instance_id)
    except ProjectBundleError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, **asdict(bundle)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
