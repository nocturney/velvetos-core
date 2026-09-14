#!/usr/bin/env python3
"""Fail-closed cold-start binding check for Velvet Factory visual standard."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STD = "packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md"
PROMPT = "packages/vfom/VELVET-VISUAL-SYSTEM-PROMPT.md"
REF = "packages/vfom/reference/velvet-approved-grid-2026-09-14.jpg"
PUBLIC = "https://raw.githubusercontent.com/nocturney/velvetos-core/main/packages/vfom/reference/velvet-approved-grid-2026-09-14.jpg"
ASSET = "MAHVJjCCKQA"
SHA = "707edde3f4d43cffea090bf90ed2418c160db2f8d90d104e4920b44697a014c0"

def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)

def load(rel: str) -> dict:
    path = ROOT / rel
    if not path.is_file(): fail(f"missing {rel}")
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: fail(f"invalid JSON {rel}: {exc}")
    if not isinstance(data, dict): fail(f"{rel} must be object")
    return data

def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file(): fail(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    for rel in (STD, PROMPT, REF):
        if not (ROOT / rel).is_file(): fail(f"missing {rel}")
    dna = load("packages/vfom/VISUAL-DNA.json").get("ownerApprovedVisualStandard") or {}
    for key, expected in {"status":"approved", "document":STD, "portablePrompt":PROMPT, "referenceAsset":REF, "publicReferenceUrl":PUBLIC, "canvaAssetId":ASSET, "artifactSha256":SHA, "coldStartGate":"fail_closed"}.items():
        if dna.get(key) != expected: fail(f"VISUAL-DNA ownerApprovedVisualStandard.{key} mismatch")
    instance = load("instances/velvet-factory/instance/velvet-factory.json")
    autonomy = instance.get("creativeAutonomy") or {}
    bound = autonomy.get("ownerApprovedVisualStandard") or {}
    for key, expected in {"required":True, "status":"approved", "document":STD, "portablePrompt":PROMPT, "referenceAsset":REF, "publicReferenceUrl":PUBLIC, "canvaAssetId":ASSET, "artifactSha256":SHA, "coldStartGate":"fail_closed"}.items():
        if bound.get(key) != expected: fail(f"instance ownerApprovedVisualStandard.{key} mismatch")
    if (autonomy.get("publish") or {}).get("requireOwnerApprovedVisualStandard") is not True:
        fail("publish.requireOwnerApprovedVisualStandard must be true")
    foundry = load("packages/vfom/FOUNDRY.json").get("ownerApprovedVisualStandard") or {}
    if foundry.get("required") is not True or foundry.get("artifactSha256") != SHA:
        fail("FOUNDRY owner-approved visual standard binding mismatch")
    schema = load("packages/vfom/CREATIVE-MANIFEST.schema.json")
    if "visualStandard" not in (schema.get("required") or []): fail("Creative Manifest must require visualStandard")
    vs = (schema.get("properties") or {}).get("visualStandard") or {}
    props = vs.get("properties") or {}
    for key, expected in {"document":STD, "portablePrompt":PROMPT, "referenceAsset":REF, "publicReferenceUrl":PUBLIC, "canvaAssetId":ASSET, "artifactSha256":SHA}.items():
        if (props.get(key) or {}).get("const") != expected: fail(f"Creative Manifest visualStandard.{key} const mismatch")
    surfaces = [
        ".cursor/skills/velvet-creative-director/SKILL.md",
        ".cursor/skills/velvet-brand-guardian/SKILL.md",
        ".cursor/skills/vf-content-sprint/SKILL.md",
        "packages/vfom/VISUAL-OS.md",
        "packages/vfom/CREATIVE-AUTOPILOT.md",
    ]
    for rel in surfaces:
        body = text(rel)
        for needle in ("OWNER-APPROVED-GRID-STANDARD-2026-09-14.md", ASSET):
            if needle not in body: fail(f"{rel} missing {needle}")
    if PUBLIC not in text(STD) or PUBLIC not in text(PROMPT): fail("public visual reference URL missing from canonical docs")
    for path in (ROOT / "packages/vfom/jobs").glob("*/creative-manifest.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        vsb = data.get("visualStandard") or {}
        if vsb.get("gate") != "PASS" or vsb.get("canvaAssetId") != ASSET or vsb.get("artifactSha256") != SHA or vsb.get("coldStart") is not True:
            fail(f"{path.relative_to(ROOT)} missing canonical visualStandard PASS binding")
    print("OK owner-approved visual standard cold-start bootstrap is fail-closed and propagated")

if __name__ == "__main__":
    main()
