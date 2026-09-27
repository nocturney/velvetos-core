#!/usr/bin/env python3
"""Resolve the active ChatGPT Project bundle from the Project Authority manifest.

Single source of truth: `packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json`
-> `chatgptProjectBundle`. `vf_project_preflight.py` and `vf_publication_evidence.py`
derive their revision/bundle/path/hash constants from here, so a revision bump
is a manifest edit (plus the new bundle files), not a code edit in two scripts.

Fail-closed: a missing field, malformed hash, file that does not exist, or a
path/bundle id that does not carry the declared revision raises
`ProjectBundleError`. The SHA-256 pins stay trust anchors; they just live in
the manifest now instead of being duplicated in code.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REL = Path("packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json")
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


def resolve(root: Path = ROOT, manifest_rel: Path = MANIFEST_REL) -> ProjectBundle:
    path = root / manifest_rel
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - fail closed with context
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
    paths = {name: field(name) for name in ("authority", "assetManifest", "instructions", "productTruthGuide")}
    for name in ("authority", "assetManifest", "instructions"):
        if f"-v{revision}." not in Path(paths[name]).name:
            raise ProjectBundleError(f"chatgptProjectBundle.{name} {paths[name]!r} is not the v{revision} file")
    for name, rel in paths.items():
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ProjectBundleError(f"chatgptProjectBundle.{name} must be repo-relative")
        if not (root / rel).is_file():
            raise ProjectBundleError(f"chatgptProjectBundle.{name} file missing: {rel}")
    hashes = {name: field(name) for name in ("authoritySha256", "assetManifestSha256")}
    for name, value in hashes.items():
        if not HEX64.fullmatch(value):
            raise ProjectBundleError(f"chatgptProjectBundle.{name} is not a lowercase SHA-256")
    return ProjectBundle(
        contract_version=contract,
        revision=revision,
        bundle_id=bundle_id,
        authority=paths["authority"],
        asset_manifest=paths["assetManifest"],
        instructions=paths["instructions"],
        product_truth_guide=paths["productTruthGuide"],
        authority_sha256=hashes["authoritySha256"],
        asset_manifest_sha256=hashes["assetManifestSha256"],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    try:
        bundle = resolve(args.root)
    except ProjectBundleError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, **asdict(bundle)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
