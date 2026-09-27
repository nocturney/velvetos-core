#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry_path = ROOT / "packages" / "vfprod" / "CAD-ENGINE-REGISTRY.json"
schema_path = ROOT / "packages" / "vfprod" / "GEOMETRY-IR.schema.json"
doc_path = ROOT / "packages" / "vfprod" / "CAD-ENGINE-STACK.md"
cli = ROOT / "scripts" / "vf_cad_stack.py"

assert registry_path.is_file(), registry_path
assert schema_path.is_file(), schema_path
assert doc_path.is_file(), doc_path
assert cli.is_file(), cli

registry = json.loads(registry_path.read_text(encoding="utf-8"))
assert registry["schema"] == "velvetos.cad-engines.v1"
assert registry["authority"] == "packages/vfprod/FABRICATION-ROUTER.md"
assert registry["printer_actions_allowed"] is False
assert registry["max_repair_iterations"] == 2

engines = registry["engines"]
assert set(engines) == {"build123d", "cadquery", "jscad", "cad-cae-copilot", "forgent3d"}
assert engines["build123d"]["role"] == "primary"
assert engines["cadquery"]["role"] == "secondary"
assert engines["jscad"]["role"] == "secondary"
assert engines["cad-cae-copilot"]["role"] == "pilot"
assert engines["forgent3d"]["role"] == "pilot"
for row in engines.values():
    assert row["paid_provider_required"] is False
    assert row["printer_control"] is False

assert registry["patterns"]["graph_cad"] == "IR_INSPIRATION_ONLY"
assert registry["patterns"]["multi_agent_cad"] == "BOUNDED_WORKFLOW_PATTERN_ONLY"
assert registry["radar"]["awesome-cad"]["runtime"] is False
assert registry["rejected_runtime"]["cadam"] is True

router = json.loads((ROOT / "packages" / "vfprod" / "FABRICATION-ROUTER.json").read_text(encoding="utf-8"))
assert router["engine_registry"] == "packages/vfprod/CAD-ENGINE-REGISTRY.json"
assert router["engine_stack_cli"] == "scripts/vf_cad_stack.py"

tool_status = json.loads((ROOT / "packages" / "velvetos" / "TOOL-STATUS.json").read_text(encoding="utf-8"))
tts = tool_status["tools"]["text-to-cad"]
assert tts["engine_registry"] == "packages/vfprod/CAD-ENGINE-REGISTRY.json"
assert tts["engine_stack_cli"] == "scripts/vf_cad_stack.py"

links = json.loads((ROOT / "packages" / "vfresearch" / "LINKS.json").read_text(encoding="utf-8"))
awesome = [x for x in links["links"] if x.get("id") == "awesome-cad"]
assert len(awesome) == 1
assert "radar" in awesome[0]["note"].lower()

host = json.loads((ROOT / "packages" / "vfharness" / "state" / "cad-engine-stack-host-acceptance-2026-09-27.json").read_text(encoding="utf-8"))
assert host["printer_actions_allowed"] is False
assert host["paid_provider_calls_performed"] is False
assert all(host["engines"][name]["status"] == "PASS" for name in ("build123d","cadquery","jscad"))
assert host["pilots"]["cad-cae-copilot"]["status"] == "PASS_LOCAL_SMOKE"
assert host["pilots"]["forgent3d"]["status"] == "SOURCE_CLONED_RUNTIME_UNVERIFIED"
assert host["rejected"]["cadam_runtime_installed"] is False

for cost_name in (
    "fabrication-cost-cadquery-2026-09-27.json",
    "fabrication-cost-jscad-2026-09-27.json",
    "fabrication-cost-cad-cae-copilot-2026-09-27.json",
    "fabrication-cost-forgent3d-2026-09-27.json",
):
    cost = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_cost_preflight.py"),
         str(ROOT / "packages" / "vfharness" / "state" / cost_name)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert cost.returncode == 0, cost.stdout + cost.stderr
    assert json.loads(cost.stdout)["status"] == "PASS"

proc = subprocess.run([sys.executable, str(cli), "contract"], cwd=ROOT, text=True, capture_output=True)
assert proc.returncode == 0, proc.stdout + proc.stderr
contract = json.loads(proc.stdout)
assert contract["status"] == "PASS"
assert contract["max_repair_iterations"] == 2

sample = ROOT / "packages" / "vfharness" / "state" / "cad-engine-stack-20260927" / "geometry-ir-sample.json"
proc = subprocess.run([sys.executable, str(cli), "ir-validate", "--input", str(sample)], cwd=ROOT, text=True, capture_output=True)
assert proc.returncode == 0, proc.stdout + proc.stderr
assert json.loads(proc.stdout)["status"] == "PASS"

state = ROOT / "packages" / "vfharness" / "state" / "cad-engine-stack-20260927" / "repair-state-test.json"
if state.exists():
    state.unlink()
for expected in ("REPAIR_ALLOWED", "REPAIR_ALLOWED", "FALLBACK_REQUIRED"):
    proc = subprocess.run([sys.executable, str(cli), "repair-next", "--state", str(state), "--failure", "geometry_check_failed"], cwd=ROOT, text=True, capture_output=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["decision"] == expected, payload
if state.exists():
    state.unlink()

print("check-vf-cad-stack: PASS")
