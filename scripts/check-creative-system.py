#!/usr/bin/env python3
"""Validate Velvet creative specialist + manifest architecture. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VFOM = ROOT / "packages" / "vfom"
INSTANCE = ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
CONTENT_SPRINT = ROOT / ".cursor" / "skills" / "vf-content-sprint" / "SKILL.md"
SPECIALISTS = {
    "creativeDirector": ROOT / ".cursor" / "skills" / "vf-creative-director" / "SKILL.md",
    "brandGuardian": ROOT / ".cursor" / "skills" / "vf-brand-guardian" / "SKILL.md",
    "mediaLibrarian": ROOT / ".cursor" / "skills" / "vf-media-librarian" / "SKILL.md",
}


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def must_contain(path: Path, needles: tuple[str, ...]) -> None:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            fail(f"{path.relative_to(ROOT)} missing {needle!r}")


def main() -> None:
    foundry = load_json(VFOM / "FOUNDRY.json")
    if foundry.get("version", 0) < 2:
        fail("FOUNDRY version must include creative-system MVP")
    manifest_policy = foundry.get("creativeManifest") or {}
    if manifest_policy.get("enabled") is not True:
        fail("Creative Manifest must be enabled")
    if manifest_policy.get("notASecondStateMachine") is not True or manifest_policy.get("notAMediaCatalog") is not True:
        fail("Creative Manifest must not become a second state machine/catalog")

    schema = load_json(VFOM / "CREATIVE-MANIFEST.schema.json")
    required = set(schema.get("required") or [])
    needed = {"jobId", "format", "status", "sourceEvidence", "concept", "hook", "shots", "edit", "cover", "qa"}
    if not needed.issubset(required):
        fail(f"Creative Manifest required fields missing {sorted(needed - required)}")
    props = schema.get("properties") or {}
    for name in ("overlays", "feed", "derivativeRefs", "rightsNotes"):
        if name not in props:
            fail(f"Creative Manifest missing {name}")

    must_contain(VFOM / "MOTION-PRESETS.md", ("VELVET_HARD_CUT", "VELVET_PROOF_FREEZE", "VELVET_STRESS_SLOWMO"))
    must_contain(VFOM / "FORMAT-GENOMES.md", ("PROOF_UNDER_PRESSURE", "FAIL_FIX_PROVE", "PROBLEM_TO_PART"))

    must_contain(CONTENT_SPRINT, ("Creative Manifest", "vf-creative-director", "vf-brand-guardian", "vf-media-librarian"))
    must_contain(SPECIALISTS["creativeDirector"], ("first-frame", "shotRequest", "EDL", "Creative Manifest"))
    must_contain(SPECIALISTS["brandGuardian"], ("Brand", "Originality", "feed", "Creative Manifest"))
    must_contain(SPECIALISTS["mediaLibrarian"], ("Media Vault", "Asset Truth", "Claim Truth", "Creative Manifest"))

    for path in SPECIALISTS.values():
        agent = path.parent / "agents" / "openai.yaml"
        if not agent.is_file():
            fail(f"missing {agent.relative_to(ROOT)}")

    instance = load_json(INSTANCE)
    autonomy = instance.get("creativeAutonomy") or {}
    expected = {
        "creativeManifestSchema": "packages/vfom/CREATIVE-MANIFEST.schema.json",
        "motionPresets": "packages/vfom/MOTION-PRESETS.md",
        "formatGenomes": "packages/vfom/FORMAT-GENOMES.md",
    }
    for key, value in expected.items():
        if autonomy.get(key) != value:
            fail(f"creativeAutonomy.{key} must be {value}")
    if autonomy.get("creativeManifestRequired") is not True:
        fail("creativeAutonomy.creativeManifestRequired must be true")

    specialists = autonomy.get("specialists") or {}
    foundry_specialists = foundry.get("specialists") or {}
    expected_specialists = {
        "creativeDirector": ".cursor/skills/vf-creative-director/SKILL.md",
        "brandGuardian": ".cursor/skills/vf-brand-guardian/SKILL.md",
        "mediaLibrarian": ".cursor/skills/vf-media-librarian/SKILL.md",
    }
    for key, value in expected_specialists.items():
        if specialists.get(key) != value or foundry_specialists.get(key) != value:
            fail(f"specialist binding mismatch for {key}")

    print("OK creative-system manifest specialists motion-genomes bound")


if __name__ == "__main__":
    main()
