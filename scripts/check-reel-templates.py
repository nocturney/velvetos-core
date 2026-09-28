#!/usr/bin/env python3
"""CI-safe Reel template/variables/bridge contract checks. No render and no network."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HF = ROOT / "packages/vfom/hyperframes"
TEMPLATES = HF / "templates"
VARIABLES = HF / "variables"
TESTS = HF / "tests"
TOKENS = ROOT / "packages/vfbrand/brand-tokens.json"
CONTRACT = ROOT / "packages/vfom/REEL-ROUTE-CONTRACT.json"
PRESETS = ROOT / "packages/vfom/MOTION-PRESETS.md"
RUNTIME = HF / "velvet-reel.js"
CSS = HF / "velvet-reel.css"
SCHEMA = HF / "REEL-VARIABLES.schema.json"
TURNTABLE = ROOT / "scripts/vf_turntable.py"


def fail(msg: str) -> None:
    print("FAIL reel-templates: " + msg, file=sys.stderr)
    raise SystemExit(1)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


contract = load(CONTRACT)
tokens = load(TOKENS)
schema = load(SCHEMA)
runtime = RUNTIME.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")
preset_doc = PRESETS.read_text(encoding="utf-8")
if contract.get("implementationStatus") != "implemented":
    fail("REEL-ROUTE-CONTRACT must be implemented")
if "brand-tokens.json" not in runtime or "document.fonts.ready" not in runtime:
    fail("runtime must wait for brand tokens and committed fonts")
if "tokens?.logo?.preferred?.overlay" not in runtime:
    fail("runtime must resolve the preferred exact logo from brand-tokens")
if "window.__timelines[compositionId] = tl" not in runtime:
    fail("runtime must register the populated HyperFrames timeline")
if "new URL(BRAND_TOKENS, RUNTIME_URL)" not in runtime or "document.currentScript" not in runtime:
    fail("runtime must resolve brand tokens/repo assets against velvet-reel.js, not the served page URL")

for family in tokens["fonts"]["families"]:
    rel = family["file"].removeprefix("packages/")
    if Path(rel).name not in css or "@font-face" not in css:
        fail(f"committed font not wired by @font-face: {family['family']}")

for preset in contract["presets"]:
    if preset not in preset_doc:
        fail(f"preset doc missing {preset}")
    if re.search(rf"\b{re.escape(preset)}\s*\(", runtime) is None:
        fail(f"runtime implementation missing {preset}")

declared_by_template = {}
for name in contract["templates"]:
    path = TEMPLATES / name
    if not path.is_file():
        fail(f"template missing: {name}")
    body = path.read_text(encoding="utf-8")
    stable_id = name.removesuffix(".html")
    for required in (
        'dir="rtl"', f'id="{stable_id}"', f'data-composition-id="{stable_id}"',
        'data-width="1080"', 'data-height="1920"', 'data-fps="30"',
        '../velvet-reel.css', '../velvet-reel.js',
    ):
        if required not in body:
            fail(f"{name} missing {required}")
    gsap_at = body.find("cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js")
    if gsap_at < 0 or gsap_at > body.find("../velvet-reel.js"):
        fail(f"{name} must load pinned GSAP before ../velvet-reel.js")
    for media_id, var_id in (("hero", "heroImage"), ("inset-image", "insetImage"),
                             ("real-motion", "realMotionVideo"), ("audio-track", "audioFile")):
        tag = re.search(rf'<(?:img|video|audio)\b[^>]*\bid="{media_id}"[^>]*>', body, re.S)
        if tag and f'data-var-src="{var_id}"' not in tag.group(0):
            fail(f"{name} #{media_id} must bind data-var-src=\"{var_id}\" so HyperFrames extracts/mixes it")
    match = re.search(r"data-composition-variables='(\[.*?\])'", body, re.S)
    if not match:
        fail(f"{name} missing declared variables")
    try:
        declarations = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        fail(f"{name} variable declarations invalid JSON: {exc}")
    declared_by_template[name] = {row["id"] for row in declarations}
rich = (TEMPLATES / "rich-still-reel.html").read_text(encoding="utf-8")
duration_match = re.search(r'id="rich-still-reel".*?data-duration="([0-9.]+)"', rich, re.S)
if not duration_match or not 7 <= float(duration_match.group(1)) <= 15:
    fail("rich-still-reel duration must be 7-15 seconds")
for needle in ("realMotionVideo", "audioFile", 'data-has-audio="true"', "HEADLINE_REVEAL",
               "ACCENT_RULE_WIPE", "CHIP_SEQUENCE", "INSET_POP"):
    if needle not in rich:
        fail(f"rich-still-reel missing {needle}")

required = set(schema.get("required") or [])
properties = set((schema.get("properties") or {}).keys())
if not required or required != properties:
    fail("variables schema must make every render variable explicit")
if declared_by_template["rich-still-reel.html"] != required:
    fail("rich-still-reel declared variables differ from REEL-VARIABLES schema")

accent_map = {row["id"]: row["hex"].lower() for row in tokens["accents"]["samples"]}
cta = tokens["reel"]["endCardCta"]
caption_rows = {row["file"]: row for row in load(TESTS / "live-caption-sources.json")["rows"]}
sample_paths = sorted(VARIABLES.glob("*.json"))
if [p.name for p in sample_paths] != [
    "deer-2026-09-23.json", "dragon-2026-09-20.json",
    "octopus-2026-09-27.json", "owl-2026-09-19.json",
]:
    fail("expected exactly four named live-post sample variable files")

for path in sample_paths:
    data = load(path)
    if set(data) != required:
        fail(f"{path.name} keys differ from schema")
    if not all(isinstance(data[key], str) for key in required):
        fail(f"{path.name} all HyperFrames variables must be scalar strings")
    if data["variablesStatus"] != "needs_input" or not data["neededInputs"]:
        fail(f"{path.name} must fail closed as needs_input")
    if data["heroImage"] or data["realMotionVideo"] or data["audioFile"]:
        fail(f"{path.name} must not fabricate render inputs")
    if data["cta"] != cta:
        fail(f"{path.name} CTA drift from brand tokens")
    if data["accentId"] not in accent_map or data["accentHex"].lower() != accent_map[data["accentId"]]:
        fail(f"{path.name} accent drift from brand tokens")
    headline_words = len(data["headline"].split())
    if not 3 <= headline_words <= 7:
        fail(f"{path.name} headline must be 3-7 words")
    if len(data["subhead"].split()) > 12:
        fail(f"{path.name} subhead exceeds 12 words")
    expected = caption_rows.get(path.name)
    if not expected:
        fail(f"{path.name} has no live-caption hash fixture")
    if data["sourceMediaId"] != expected["sourceMediaId"] or data["sourcePermalink"] != expected["sourcePermalink"]:
        fail(f"{path.name} source post identity drift")
    digest = hashlib.sha256(data["caption"].encode("utf-8")).hexdigest()
    if digest != expected["captionSha256"]:
        fail(f"{path.name} exact live caption hash drift")

# Exercise bridge planning only; no HyperFrames binary or render is invoked.
sys.path.insert(0, str(ROOT / "scripts"))
import vf_hyperframes as bridge  # noqa: E402

base_request = {
    "backend": "hyperframes",
    "jobId": "VF-TEMPLATE-SMOKE",
    "projectDir": str(ROOT),
    "composition": "packages/vfom/hyperframes/templates/rich-still-reel.html",
    "stage": "rough",
    "target": "reel_master",
    "format": "mp4",
    "resolution": "portrait",
    "fps": 30,
    "quality": "draft",
    "output": "packages/vfom/hyperframes/tests/out.mp4",
    "audioRequired": True,
}
single = dict(base_request, variablesFile="packages/vfom/hyperframes/variables/owl-2026-09-19.json")
single_req = bridge.validate_request(single)
single_render = bridge.build_commands(single_req)[1]
if "--variables-file" not in single_render or "--batch" in single_render:
    fail("vf_hyperframes --variables-file plan wiring failed")
batch = dict(
    base_request,
    output="packages/vfom/hyperframes/tests/out-{sourceMediaId}.mp4",
    batchFile="packages/vfom/hyperframes/tests/batch-smoke.json",
)
batch_req = bridge.validate_request(batch)
batch_render = bridge.build_commands(batch_req)[1]
if "--batch" not in batch_render or "--batch-fail-fast" not in batch_render or "--strict-variables" not in batch_render:
    fail("vf_hyperframes --batch plan wiring failed")
batch_outputs = bridge.batch_output_paths(batch_req)
if len(batch_outputs) != 2 or len(set(batch_outputs)) != 2:
    fail("vf_hyperframes batch output expansion failed")

turntable = TURNTABLE.read_text(encoding="utf-8")
for needle in (
    "from vf_3d import detect_blender", "threemf_import", "6.0 <= args.duration <= 8.0",
    "frame N+1 is 360 degrees", "no AI product generation", "publicationAuthorized",
):
    if needle not in turntable:
        fail(f"turntable truth/runtime contract missing {needle!r}")

print(
    "OK reel templates "
    f"templates={len(contract['templates'])} presets={len(contract['presets'])} "
    f"samples={len(sample_paths)} rtl=PASS tokens=PASS batch_plan=PASS turntable=PASS"
)
