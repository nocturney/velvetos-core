#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
router_path = ROOT / "packages" / "vfprod" / "FABRICATION-ROUTER.json"
router = json.loads(router_path.read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "packages" / "velvetos" / "PROJECT-AUTHORITY-MANIFEST.json").read_text(encoding="utf-8"))
tool_status = json.loads((ROOT / "packages" / "velvetos" / "TOOL-STATUS.json").read_text(encoding="utf-8"))
vfprod = (ROOT / "packages" / "vfprod" / "SKILL.md").read_text(encoding="utf-8")
text_to_cad = (ROOT / "packages" / "vfprod" / "TEXT-TO-CAD.md").read_text(encoding="utf-8")
lock = json.loads((ROOT / "skills-lock.json").read_text(encoding="utf-8"))

expected = {
    "cad", "cad-viewer", "dfam-check", "dfm", "dxf", "engineering-drawing",
    "gcode", "sdf", "sendcutsend", "srdf", "step-parts", "urdf",
}
assert set(router["installed_skills"]) == expected
assert set(lock["skills"]) == expected
assert router["excluded_skills"] == ["bambu-labs"]
assert router["upstream_commit"] == "fafa7b057d8f2c3347ff422f0515380123a4b1d4"
assert router["viewer_policy"] == {"host": "127.0.0.1", "external_bind": False}

for name in expected:
    assert (ROOT / ".agents" / "skills" / name / "SKILL.md").is_file(), name
    assert (ROOT / ".grok" / "skills" / name / "SKILL.md").is_file(), name

assert not (ROOT / ".agents" / "skills" / "bambu-labs").exists()
assert not (ROOT / ".grok" / "skills" / "bambu-labs").exists()

hb = router["hard_boundaries"]
for key in (
    "printer_network_control",
    "upload_to_printer",
    "start_print",
    "heating",
    "motion",
    "sendcutsend_order_submission",
    "hidden_dimensions_may_be_invented",
):
    assert hb[key] is False, key

production = manifest["domains"]["production"]
assert "packages/vfprod/FABRICATION-ROUTER.md" in production["authorities"]
assert "packages/vfprod/TEXT-TO-CAD.md" in production["authorities"]
assert "fabrication_tool_route" in production["hardGates"]
assert "no_printer_control" in production["hardGates"]

assert "FABRICATION-ROUTER.md" in vfprod
assert ".agents/skills/<skill>/SKILL.md" in vfprod
assert "bambu-labs" in text_to_cad
assert "excluded" in text_to_cad.lower()

tts = tool_status["tools"]["text-to-cad"]
assert tts["status"] == "active"
assert tts["router"] == "packages/vfprod/FABRICATION-ROUTER.md"
assert tts["print_start"] is False
assert tts["installed_skill_count"] == 12
assert (ROOT / tts["host_evidence"]).is_file()

proc = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "vf_fabrication_router.py"), "verify"],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
assert proc.returncode == 0, proc.stdout + proc.stderr
report = json.loads(proc.stdout)
assert report["status"] == "PASS"
assert report["enabled_count"] == 12

decision_cases = [
    ("תכנן מתאם בקוטר 32 מ״מ עם ארבעה חורים ותכין להדפסה", [], "functional_part_to_print"),
    ("תכנן תושבת למיסב 608ZZ ותכין להדפסה", [], "assembly_with_standard_parts_to_print"),
    ("תמצא לי STEP של מיסב 608ZZ", [], "standard_part_lookup"),
    ("קח את התמונה ותכנן ממנה תושבת", ["part.png"], "photo_or_sketch_to_functional_cad"),
    ("בדוק אם הקובץ צריך תמיכות", ["part.stl"], "additive_printability_review"),
    ("באיזה כיוון הכי נכון להדפיס את החלק", ["part.stl"], "additive_orientation_optimization"),
    ("תכין שרטוט הנדסי PDF עם מידות", ["part.step"], "engineering_drawing_pdf"),
    ("תכין DXF לחיתוך לייזר", ["part.step"], "dxf_profile_or_flat_pattern"),
    ("פתח לי את המודל לבדיקה", ["part.step"], "cad_visual_review"),
    ("תכין את הקובץ להדפסה", ["part.stl"], "slice_and_validate"),
    ("design a printable threaded bracket", [], "functional_part_to_print"),
    ("reconstruct this reference and preserve exact mounting holes", [], "reference_reconstruction"),
    ("make this STL printable", [], "additive_redesign"),
    ("slice for U1 and validate the G-code", [], "slice_and_validate"),
    ("מה מרווח מומלץ לחיבור snap-fit ב-PETG?", [], "advice_calculation"),
]
for request, files, expected_intent in decision_cases:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "vf_fabrication_router.py"),
        "decide",
        "--request",
        request,
    ]
    for file_name in files:
        cmd.extend(["--file", file_name])
    decision = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", capture_output=True)
    assert decision.returncode == 0, decision.stdout + decision.stderr
    payload = json.loads(decision.stdout)
    assert payload["intent"] == expected_intent, (request, payload)

for cost_file in (
    "fabrication-cost-text-to-cad-2026-09-27.json",
    "fabrication-cost-step-parts-2026-09-27.json",
    "fabrication-cost-sendcutsend-2026-09-27.json",
):
    cost_path = ROOT / "packages" / "vfharness" / "state" / cost_file
    assert cost_path.is_file(), cost_path
    cost = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_cost_preflight.py"), str(cost_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert cost.returncode == 0, cost.stdout + cost.stderr
    assert json.loads(cost.stdout)["status"] == "PASS"

print("check-vf-fabrication-router: PASS skills=12 printer-send=disabled costs=PASS")
