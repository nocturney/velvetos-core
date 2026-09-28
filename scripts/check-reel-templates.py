#!/usr/bin/env python3
"""CI-safe Reel template, HyperFrames regression and Adobe route checks."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
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
ADOBE = ROOT / "packages/vfom/adobe"
ADOBE_SCHEMA = ADOBE / "REEL-JOB.schema.json"
PS_JSX = ADOBE / "photoshop-product-layer.jsx"
AE_JSX = ADOBE / "build-reel.jsx"
ORCH = ROOT / "scripts/vf_ae_reel.py"
JOB = ROOT / "packages/vfom/jobs/VF-R006"


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
if 'BRAND_TOKENS = "packages/vfbrand/brand-tokens.json"' not in runtime:
    fail("HyperFrames brand tokens must resolve from repo-root packages/...")
if 'new URL("/", document.baseURI)' not in runtime or "fetch(repoAsset(BRAND_TOKENS))" not in runtime:
    fail("HyperFrames runtime must anchor assets at served repo root")
if "new FontFace" not in runtime or "family.file" not in runtime or "document.fonts.ready" not in runtime:
    fail("HyperFrames runtime must load committed token fonts from repo-root paths")
if "../../vfbrand" in runtime or "../../vfbrand" in css:
    fail("HyperFrames must not use ../../vfbrand asset escapes")
if "document.currentScript" in runtime:
    fail("inlined HyperFrames runtime must not depend on document.currentScript")
if "tokens?.logo?.preferred?.overlay" not in runtime:
    fail("runtime must resolve the preferred exact logo from brand-tokens")
if "window.__timelines[compositionId] = tl" not in runtime:
    fail("runtime must register the populated HyperFrames timeline")


for preset in contract["presets"]:
    if preset not in preset_doc:
        fail(f"preset doc missing {preset}")
    if re.search(rf"\b{re.escape(preset)}\s*\(", runtime) is None:
        fail(f"runtime implementation missing {preset}")

declared_by_template = {}
for name in contract["templates"]:
    path_obj = TEMPLATES / name
    if not path_obj.is_file():
        fail(f"template missing: {name}")
    body = path_obj.read_text(encoding="utf-8")
    html = re.search(r"<html\b[^>]*>", body, re.I)
    if not html:
        fail(f"{name} missing html tag")
    if re.search(r'\bdir=["\']rtl["\']', html.group(0), re.I):
        fail(f"{name} must not put dir=rtl on the html tag")
    if 'dir="rtl"' not in body[html.end():]:
        fail(f"{name} must keep explicit RTL on a text container")
    stable_id = name.removesuffix(".html")
    for required in (
        f'id="{stable_id}"', f'data-composition-id="{stable_id}"',
        'data-width="1080"', 'data-height="1920"', 'data-fps="30"',
        '../velvet-reel.css', '../velvet-reel.js',
    ):
        if required not in body:
            fail(f"{name} missing {required}")
    gsap_at = body.find("cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js")
    if gsap_at < 0 or gsap_at > body.find("../velvet-reel.js"):
        fail(f"{name} must load pinned GSAP before ../velvet-reel.js")
    for media_id, var_id in (
        ("hero", "heroImage"), ("inset-image", "insetImage"),
        ("real-motion", "realMotionVideo"), ("audio-track", "audioFile"),
    ):
        tag = re.search(rf'<(?:img|video|audio)\b[^>]*\bid="{media_id}"[^>]*>', body, re.S)
        if tag and f'data-var-src="{var_id}"' not in tag.group(0):
            fail(f"{name} #{media_id} must bind data-var-src=\"{var_id}\"")
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
for needle in (
    "realMotionVideo", "audioFile", 'data-has-audio="true"',
    "HEADLINE_REVEAL", "ACCENT_RULE_WIPE", "CHIP_SEQUENCE", "INSET_POP",
):
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

for sample in sample_paths:
    data = load(sample)
    if set(data) != required:
        fail(f"{sample.name} keys differ from schema")
    if not all(isinstance(data[key], str) for key in required):
        fail(f"{sample.name} all HyperFrames variables must be scalar strings")
    if data["variablesStatus"] != "needs_input" or not data["neededInputs"]:
        fail(f"{sample.name} must fail closed as needs_input")
    if data["heroImage"] or data["realMotionVideo"] or data["audioFile"]:
        fail(f"{sample.name} must not fabricate render inputs")
    if data["cta"] != cta:
        fail(f"{sample.name} CTA drift from brand tokens")
    if data["accentId"] not in accent_map or data["accentHex"].lower() != accent_map[data["accentId"]]:
        fail(f"{sample.name} accent drift from brand tokens")
    if not 3 <= len(data["headline"].split()) <= 7:
        fail(f"{sample.name} headline must be 3-7 words")
    if len(data["subhead"].split()) > 12:
        fail(f"{sample.name} subhead exceeds 12 words")
    expected = caption_rows.get(sample.name)
    if not expected:
        fail(f"{sample.name} has no live-caption hash fixture")
    if data["sourceMediaId"] != expected["sourceMediaId"] or data["sourcePermalink"] != expected["sourcePermalink"]:
        fail(f"{sample.name} source post identity drift")
    digest = hashlib.sha256(data["caption"].encode("utf-8")).hexdigest()
    if digest != expected["captionSha256"]:
        fail(f"{sample.name} exact live caption hash drift")


# Exercise legacy HyperFrames bridge planning only; no render and no network.
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


# Adobe schema / static implementation wiring.
job_schema = load(ADOBE_SCHEMA)
expected_required = {
    "schema", "jobId", "status", "reelType", "reference", "canvas",
    "copy", "assets", "scenes", "audioStrategy", "neededInputs",
    "publicationAuthorized",
}
if set(job_schema.get("required") or []) != expected_required:
    fail("Adobe job schema top-level required fields drift")
props = job_schema.get("properties") or {}
canvas_props = (props.get("canvas") or {}).get("properties") or {}
if (
    (canvas_props.get("width") or {}).get("const"),
    (canvas_props.get("height") or {}).get("const"),
    (canvas_props.get("fps") or {}).get("const"),
) != (1080, 1920, 30):
    fail("Adobe job schema must lock 1080x1920/30fps")
duration = canvas_props.get("durationSeconds") or {}
if duration.get("minimum") != 12 or duration.get("maximum") != 15:
    fail("Adobe job schema duration must be 12-15 seconds")
scene_schema = props.get("scenes") or {}
if scene_schema.get("minItems") != 5 or scene_schema.get("maxItems") != 5:
    fail("Adobe job schema must require five scene angles")
assets_props = (props.get("assets") or {}).get("properties") or {}
if (assets_props.get("headlineWeight") or {}).get("const") != 700:
    fail("Adobe job schema headline must be Rubik 700")
if (assets_props.get("subheadWeight") or {}).get("const") != 600:
    fail("Adobe job schema subhead must be Rubik 600")
if (props.get("publicationAuthorized") or {}).get("const") is not False:
    fail("Adobe job schema must hard-lock publicationAuthorized=false")

ps_jsx = PS_JSX.read_text(encoding="utf-8")
for needle in (
    'stringIDToTypeID("autoCutout")', "selection.smooth", "selection.feather",
    "PNGSaveOptions", '$.getenv("VF_AE_REEL_CONFIG")',
    'productPixelsSource: "scene_selection_only"',
):
    if needle not in ps_jsx:
        fail(f"Photoshop JSX missing {needle}")
if "generativeFill" in ps_jsx:
    fail("Photoshop JSX must not invoke Generative Fill")


ae_jsx = AE_JSX.read_text(encoding="utf-8")
for needle in (
    'addCamera("VF_2_5D_CAMERA"', "ADBE Camera Depth of Field",
    "ADBE Camera Focus Distance", "CC Particle World",
    "ParagraphJustification.RIGHT_JUSTIFY", "ParagraphDirection.RIGHT_TO_LEFT",
    "ADBE Mask Parade", "SAFE_TOP = 150", "SAFE_BOTTOM = 384",
    "SAFE_RIGHT_BUTTON_STRIP = 190", 'resolveFont("Rubik", weight)',
    "scaleValue = layer.threeDLayer", "importFile(cfg.assets.logo)",
    'applyTemplate("Lossless")',
    'renderQueue.items.add(comp)',
):
    if needle not in ae_jsx:
        fail(f"After Effects JSX missing {needle}")

orch = ORCH.read_text(encoding="utf-8")
for needle in (
    r'DEFAULT_RUNTIME = Path(r"D:\Velvet\Runtime\VelvetOS")',
    r'FFMPEG_DIR = Path(r"D:\Velvet\Tools\Shared\ffmpeg\current\bin")',
    'Adobe After Effects 2026', 'Adobe Photoshop 2026',
    'startswith("27.7")', 'startswith("26.3")',
    "AddFontResourceExW", "aerender", "ffprobe",
    "apad=pad_dur", "intentional_silence", "audioStreams",
    "--validate-only", '"publicationAuthorized": False',
    "render-receipt.json",
):
    if needle not in orch:
        fail(f"vf_ae_reel.py missing {needle}")

manifest = load(JOB / "manifest.json")
variables = load(JOB / "variables.json")
storyboard = load(JOB / "storyboard.json")
prep = load(JOB / "prep-status.json")
expected_copy = {
    "headlineLines": ["פרטים קטנים,", "נוכחות גדולה."],
    "subhead": "שלושה מוקדים קטנים שבונים את כל האופי שלו.",
    "icons": ["מודפס בתלת־ממד", "פריט דקורטיבי", "מתאים למדף או לשולחן"],
    "detailLabels": ["המבט שתופס ראשון", "שכבות הנוצות", "מרקם הבסיס"],
    "cta": cta,
    "accentHex": "#a86838",
}
if manifest.get("copy") != expected_copy:
    fail("VF-R006 exact overlay copy drift")
if manifest.get("status") != "needs_input" or prep.get("status") != "needs_input":
    fail("VF-R006 must remain needs_input while scene pairs are pending")
if manifest.get("publicationAuthorized") is not False:
    fail("VF-R006 may not authorize publication")
if variables.get("headlineLines") != expected_copy["headlineLines"]:
    fail("VF-R006 variables headline drift")

if len(manifest.get("scenes") or []) != 5:
    fail("VF-R006 must carry five pending scene slots")
for row in manifest["scenes"]:
    if row["sourcePhoto"] or row["scene"] or row["emptyPlate"] or row["productLayer"]:
        fail("VF-R006 must not fabricate pending source/scene/product-layer paths")
    if any(row["sha256"].values()):
        fail("VF-R006 must not invent source SHA-256 values")
if manifest.get("neededInputs") != prep.get("neededInputs") or not manifest["neededInputs"]:
    fail("VF-R006 neededInputs drift")
if storyboard.get("durationSeconds") != 13.5:
    fail("VF-R006 storyboard duration drift")
safe = storyboard.get("safeZones") or {}
if safe != {"topPx": 150, "bottomFraction": 0.2, "rightButtonStripPx": 190}:
    fail("VF-R006 safe-zone contract drift")

validate = subprocess.run(
    [
        sys.executable, str(ORCH), "--job",
        "packages/vfom/jobs/VF-R006", "--validate-only",
    ],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=False,
)
if validate.returncode != 0:
    fail("vf_ae_reel --validate-only failed: " + (validate.stderr or validate.stdout).strip())
try:
    validate_payload = json.loads(validate.stdout)
except json.JSONDecodeError as exc:
    fail(f"vf_ae_reel --validate-only did not emit JSON: {exc}")
if not validate_payload.get("ok") or validate_payload.get("renderable"):
    fail("VF-R006 validation must pass structurally while remaining non-renderable")

print(
    "OK reel templates "
    f"templates={len(contract['templates'])} presets={len(contract['presets'])} "
    f"samples={len(sample_paths)} rtl=PASS root_assets=PASS adobe=PASS "
    "vf_r006=needs_input turntable=PASS"
)
