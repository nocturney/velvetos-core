#!/usr/bin/env python3
"""Project bundle resolver: one manifest-driven executable identity plus explicit source extensions."""
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

# 2. Both executable consumers derive from the resolver.
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

# 3. No hard-coded bundle revision/pins left in the two executable consumers.
literal = re.compile(r"-v\d+\.\d+(?:\.\d+)?\.(?:txt|json)|VF-PROJECT-\d|\"\d+\.\d+\.\d+\"")
for rel in ("scripts/vf_project_preflight.py", "scripts/vf_publication_evidence.py"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    hit = literal.search(text)
    if hit:
        fail(f"{rel} hard-codes bundle revision literal {hit.group(0)!r}")
    for pin in (b.authority_sha256, b.asset_manifest_sha256):
        if pin in text:
            fail(f"{rel} duplicates a manifest SHA-256 pin")

# 4. LATEST is a projection with explicit states; it must not masquerade an extension as the runtime.
latest_path = ROOT / "packages/velvetos/chatgpt-project/LATEST.json"
latest = json.loads(latest_path.read_text(encoding="utf-8"))
if latest.get("schema") != "velvetos.chatgpt-project.latest.v2":
    fail("LATEST schema is not v2")
if "revision" in latest or "bundleId" in latest:
    fail("LATEST must not expose a single ambiguous top-level revision/bundleId")
creative = latest.get("creativeRuntime") or {}
if (creative.get("revision"), creative.get("bundleId")) != (
    "6.6.9", "VF-PROJECT-6.6.9-NATIVE-PRODUCT-EDIT-ROUTING"
):
    fail("LATEST creativeRuntime must identify the 6.6.9 creative runtime")
if creative.get("repoSynced") is not False:
    fail("LATEST must not claim the 6.6.9 flat runtime is repo-synced without evidence")
extensions = latest.get("extensions") or {}
chat_native = extensions.get("chatNativeEditor") or {}
reel = extensions.get("reel") or {}
if (chat_native.get("revision"), chat_native.get("bundleId")) != (
    "6.6.11", "VF-PROJECT-6.6.11-CHAT-NATIVE-EDITOR-RECOVERY"
):
    fail("LATEST chatNativeEditor extension identity drift")
if (reel.get("revision"), reel.get("bundleId")) != (
    "6.6.10", "VF-PROJECT-6.6.10-REEL-VIDEO-ROUTE"
):
    fail("LATEST reel extension identity drift")
for ext_name, ext in (("chatNativeEditor", chat_native), ("reel", reel)):
    for key in ("instructions", "routeDoc"):
        rel = ext.get(key)
        if not isinstance(rel, str) or not rel:
            fail(f"LATEST {ext_name}.{key} missing")
        path = ROOT / "packages/velvetos/chatgpt-project" / rel
        if not path.is_file():
            fail(f"LATEST {ext_name}.{key} file missing: {rel}")
repo_exec = latest.get("repoExecutableBundle") or {}
if (repo_exec.get("revision"), repo_exec.get("bundleId")) != (b.revision, b.bundle_id):
    fail("LATEST repoExecutableBundle differs from manifest chatgptProjectBundle")
if repo_exec.get("authority") != Path(b.authority).name:
    fail("LATEST repoExecutableBundle authority drift")
if repo_exec.get("assetManifest") != Path(b.asset_manifest).name:
    fail("LATEST repoExecutableBundle asset manifest drift")
if repo_exec.get("instructions") != Path(b.instructions).name:
    fail("LATEST repoExecutableBundle instructions drift")

chat_route = (ROOT / "packages/velvetos/chatgpt-project" / chat_native["routeDoc"]).read_text(encoding="utf-8")
chat_instructions = (ROOT / "packages/velvetos/chatgpt-project" / chat_native["instructions"]).read_text(encoding="utf-8")
for needle in ("CHAT_NATIVE_TERMINAL", "FILE_BACKED_NATIVE_EDIT", "OWNER_REVIEW_CANDIDATE", "תכין פוסט"):
    if needle not in chat_route or needle not in chat_instructions:
        fail(f"chat-native recovery contract missing {needle!r}")

# 5. Fail-closed resolver behaviour on a broken executable manifest.
manifest = json.loads((ROOT / vpb.MANIFEST_REL).read_text(encoding="utf-8"))
cases = {
    "missing bundle": lambda m: m.pop("chatgptProjectBundle"),
    "bad sha": lambda m: m["chatgptProjectBundle"].__setitem__("assetManifestSha256", "abc"),
    "revision/path mismatch": lambda m: m["chatgptProjectBundle"].__setitem__("revision", "9.9.9"),
    "bundle id without revision": lambda m: m["chatgptProjectBundle"].__setitem__("bundleId", "VF-PROJECT-X"),
    "missing file": lambda m: m["chatgptProjectBundle"].__setitem__("instructions", "packages/velvetos/chatgpt-project/PROJECT-INSTRUCTIONS-v" + m["chatgptProjectBundle"]["revision"] + ".missing.txt"),
    "absolute path": lambda m: m["chatgptProjectBundle"].__setitem__("productTruthGuide", "/etc/passwd"),
    "missing hash field": lambda m: m["chatgptProjectBundle"].pop("authoritySha256"),
}
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    for rel in (b.authority, b.asset_manifest, b.instructions, b.product_truth_guide):
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

print(
    f"OK project-bundle executable={b.revision} creative=6.6.9 "
    f"extensions=6.6.10,6.6.11 consumers=2 negative_cases={len(cases)}"
)
