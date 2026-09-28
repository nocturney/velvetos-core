#!/usr/bin/env python3
"""Project bundle resolver: one manifest-driven identity, no revision literals in code."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import vf_project_bundle as vpb  # noqa: E402
import vf_project_preflight as pre  # noqa: E402
import vf_publication_evidence as pub  # noqa: E402


def fail(msg: str) -> None:
    print(f"FAIL project-bundle: {msg}")
    sys.exit(1)


def digests(path: Path) -> set[str]:
    raw = path.read_bytes()
    return {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}


b = vpb.resolve()
# 1. Pins match the real bytes (the pins are trust anchors, not decoration).
if b.authority_sha256 not in digests(ROOT / b.authority):
    fail("authoritySha256 does not match the authority file")
if b.asset_manifest_sha256 not in digests(ROOT / b.asset_manifest):
    fail("assetManifestSha256 does not match the asset manifest file")
assets = json.loads((ROOT / b.asset_manifest).read_text(encoding="utf-8"))
if (assets.get("contract_version"), str(assets.get("revision")), assets.get("bundle_id")) != (b.contract_version, b.revision, b.bundle_id):
    fail("asset manifest identity differs from chatgptProjectBundle")

# 2. Both consumers derive from the resolver.
expect_pre = {"PROJECT_AUTHORITY": Path(b.authority), "PROJECT_ASSET_MANIFEST": Path(b.asset_manifest),
              "PROJECT_INSTRUCTIONS": Path(b.instructions), "PROJECT_CONTRACT_VERSION": b.contract_version,
              "PROJECT_REVISION": b.revision, "PROJECT_BUNDLE_ID": b.bundle_id,
              "PROJECT_ASSET_MANIFEST_SHA256": b.asset_manifest_sha256}
expect_pub = {"AUTHORITY": b.authority, "ASSETS": b.asset_manifest, "ASSETS_SHA": b.asset_manifest_sha256,
              "AUTHORITY_SHA": b.authority_sha256, "PROJECT_CONTRACT_VERSION": b.contract_version,
              "PROJECT_REVISION": b.revision, "PROJECT_BUNDLE_ID": b.bundle_id, "PRODUCT_TRUTH_GUIDE": b.product_truth_guide}
for mod, expect in ((pre, expect_pre), (pub, expect_pub)):
    for name, value in expect.items():
        if getattr(mod, name) != value:
            fail(f"{mod.__name__}.{name} is not resolver-derived")

# 3. No hard-coded bundle revision/pins left in the two consumers.
literal = re.compile(r"-v\d+\.\d+(?:\.\d+)?\.(?:txt|json)|VF-PROJECT-\d|\"\d+\.\d+\.\d+\"")
for rel in ("scripts/vf_project_preflight.py", "scripts/vf_publication_evidence.py"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    hit = literal.search(text)
    if hit:
        fail(f"{rel} hard-codes bundle revision literal {hit.group(0)!r}")
    for pin in (b.authority_sha256, b.asset_manifest_sha256):
        if pin in text:
            fail(f"{rel} duplicates a manifest SHA-256 pin")

# 4. Fail-closed resolver behaviour on a broken manifest.
manifest = json.loads((ROOT / vpb.MANIFEST_REL).read_text(encoding="utf-8"))
cases = {
    "missing bundle": lambda m: m.pop("chatgptProjectBundle"),
    "bad sha": lambda m: m["chatgptProjectBundle"].__setitem__("assetManifestSha256", "abc"),
    "revision/path mismatch": lambda m: m["chatgptProjectBundle"].__setitem__("revision", "9.9.9"),
    "bundle id without revision": lambda m: m["chatgptProjectBundle"].__setitem__("bundleId", "VF-PROJECT-X"),
    "missing file": lambda m: m["chatgptProjectBundle"].__setitem__("instructions", "packages/velvetos/chatgpt-project/PROJECT-INSTRUCTIONS-v" + m["chatgptProjectBundle"]["revision"] + ".missing.txt"),
    "absolute path": lambda m: m["chatgptProjectBundle"].__setitem__("productTruthGuide", "/etc/passwd"),
    "missing hash field": lambda m: m["chatgptProjectBundle"].pop("authoritySha256"),
    "missing reel route": lambda m: m["chatgptProjectBundle"].__setitem__("reelRoute", "packages/velvetos/chatgpt-project/REEL-ROUTE.missing.md"),
}
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    for rel in (b.authority, b.asset_manifest, b.instructions, b.product_truth_guide, b.reel_route):
        (t / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, t / rel)
    (t / vpb.MANIFEST_REL).parent.mkdir(parents=True, exist_ok=True)
    (t / vpb.MANIFEST_REL).write_text(json.dumps(manifest), encoding="utf-8")
    if vpb.resolve(t) != b:
        fail("resolver is not deterministic on a copied tree")
    for name, mutate in cases.items():
        m = copy.deepcopy(manifest)
        mutate(m)
        (t / vpb.MANIFEST_REL).write_text(json.dumps(m), encoding="utf-8")
        try:
            vpb.resolve(t)
        except vpb.ProjectBundleError:
            continue
        fail(f"resolver accepted broken manifest ({name})")

print(f"OK project-bundle revision={b.revision} bundle={b.bundle_id} consumers=2 literals=0 negative_cases={len(cases)}")
