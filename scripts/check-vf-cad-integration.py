#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bridge = (ROOT / "scripts" / "vf_cad.py").read_text(encoding="utf-8")
doc = (ROOT / "packages" / "vfprod" / "TEXT-TO-CAD.md").read_text(encoding="utf-8")
skill = (ROOT / "packages" / "vfprod" / "SKILL.md").read_text(encoding="utf-8")
expert = (ROOT / "packages" / "vfprod" / "experts" / "3D-MODEL.md").read_text(encoding="utf-8")

required_bridge = [
    "printer_matrix.json",
    "ORCASLICER_BIN",
    "text-to-cad-profiles",
    '"start_print": False',
    '"upload": False',
    "cadgen.cli",
    "dfam_tool.py",
    "gcode_tool.py",
]
missing = [x for x in required_bridge if x not in bridge]
assert not missing, f"vf_cad bridge missing contracts: {missing}"

for forbidden in ("start_print(", "upload_print(", "printer_ip", "socket.", "requests.post("):
    assert forbidden not in bridge, f"unsafe printer-control surface in bridge: {forbidden}"

assert "TEXT-TO-CAD.md" in skill
assert "CAD פונקציונלי פרמטרי" in expert
assert "printer_matrix.json" in doc
assert "Physical printing remains a separate production-floor action." in doc

print("check-vf-cad-integration: PASS")
