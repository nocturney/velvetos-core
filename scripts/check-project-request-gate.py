#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import hashlib
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "packages/velvetos/PROJECT-REQUEST-GATE.md"
MANIFEST = ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"
CLI = ROOT / "scripts/vf_project_preflight.py"


def fail(msg: str) -> None:
    print(f"FAIL project-request-gate: {msg}", file=sys.stderr)
    raise SystemExit(1)

for path in (GATE, MANIFEST, CLI):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
if manifest.get("status") != "mandatory" or manifest.get("preflightMode") != "fail_closed":
    fail("manifest is not mandatory fail-closed")
if manifest.get("gateDocument") != "packages/velvetos/PROJECT-REQUEST-GATE.md":
    fail("gateDocument mismatch")
required_domains = {
    "creative_publication", "copywriting", "operations", "production",
    "sales_conversion", "finance", "research", "system_engineering", "instagram_action", "general_business"
}
if not required_domains.issubset(set(manifest.get("domains", {}))):
    fail("required domain coverage missing")

project_authority = ROOT / "packages/velvetos/chatgpt-project/PROJECT-AUTHORITY-v6.2.txt"
asset_manifest = ROOT / "packages/velvetos/chatgpt-project/ASSET-MANIFEST-v6.2.json"
visual_enforcement = ROOT / "packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json"
for path in (project_authority, asset_manifest, visual_enforcement):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
authority_text = project_authority.read_text(encoding="utf-8")
if "vfcovers/vfcanva composition route" in authority_text:
    fail("stale vfcanva route remains active in Project Authority")
for needle in ("Canva/vfcanva are forbidden", "creative_execution_authorized: true"):
    if needle not in authority_text:
        fail(f"Project Authority missing {needle}")
asset_data = json.loads(asset_manifest.read_text(encoding="utf-8"))
authority_rows = [x for x in asset_data.get("assets", []) if x.get("filename") == "Velvet-Factory-Project-Authority-v6.txt"]
authority_sha = hashlib.sha256(project_authority.read_bytes()).hexdigest()
if len(authority_rows) != 1 or authority_rows[0].get("sha256") != authority_sha:
    fail("Project Authority bytes are not bound to the 6.2 asset manifest")
route = json.loads(visual_enforcement.read_text(encoding="utf-8")).get("publicationRoute", {})
if not {"canva", "vfcanva"}.issubset({str(x).casefold() for x in route.get("deniedTools", [])}):
    fail("publicationRoute must deny Canva/vfcanva")

# Behavioral regression: even a hash-consistent stale Project Authority must fail closed.
sys.path.insert(0, str(ROOT / "scripts"))
import vf_project_preflight as project_preflight
if project_preflight.project_binding_problems():
    fail("current Project binding is inconsistent: " + "; ".join(project_preflight.project_binding_problems()))
with tempfile.TemporaryDirectory(prefix="vf-project-binding-") as tmp_name:
    tmp = Path(tmp_name)
    for rel in (project_preflight.PROJECT_AUTHORITY, project_preflight.PROJECT_ASSET_MANIFEST,
                project_preflight.VISUAL_ENFORCEMENT, project_preflight.PROJECT_GATE):
        target = tmp / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    stale = tmp / project_preflight.PROJECT_AUTHORITY
    stale.write_text(stale.read_text(encoding="utf-8").replace("Canva/vfcanva are forbidden", "Canva/vfcanva may be used"), encoding="utf-8")
    stale_sha = hashlib.sha256(stale.read_bytes()).hexdigest()
    am = json.loads((tmp / project_preflight.PROJECT_ASSET_MANIFEST).read_text(encoding="utf-8"))
    for row in am["assets"]:
        if row.get("filename") == "Velvet-Factory-Project-Authority-v6.txt":
            row["sha256"] = stale_sha
            row["bytes"] = stale.stat().st_size
    (tmp / project_preflight.PROJECT_ASSET_MANIFEST).write_text(json.dumps(am, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    problems = project_preflight.project_binding_problems(tmp)
    if not any("no-Canva" in problem for problem in problems):
        fail("hash-consistent stale Project Authority did not fail closed")

all_paths = list(manifest.get("baselineAuthorities", []))
for cfg in manifest["domains"].values():
    all_paths.extend(cfg.get("authorities", []))
missing = sorted({p for p in all_paths if not (ROOT / p).is_file()})
if missing:
    fail("missing authority path(s): " + ", ".join(missing))

gate = GATE.read_text(encoding="utf-8")
for needle in ("No substantive work starts", "Project Instructions", "route first", "exact-final"):
    if needle.casefold() not in gate.casefold():
        fail(f"gate document missing {needle}")

for rel in ("AGENTS.md", "instances/velvet-factory/AGENTS.md", "instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc"):
    body = (ROOT / rel).read_text(encoding="utf-8")
    if "PROJECT-REQUEST-GATE.md" not in body or "PROJECT-AUTHORITY-MANIFEST.json" not in body:
        fail(f"{rel} not bound to project request gate")
for sample, expected in (("תכין פוסט לפרסום", "creative_publication"), ("עדכן סטטוס הזמנה", "operations")):
    proc = subprocess.run([sys.executable, str(CLI), "--text", sample], cwd=ROOT, text=True, capture_output=True)
    expected_code = 2 if expected == "creative_publication" else 0
    if proc.returncode != expected_code:
        fail(f"preflight CLI failed for sample {sample}: {proc.stderr or proc.stdout}")
    receipt = json.loads(proc.stdout)
    expected_state = "BLOCKED" if expected == "creative_publication" else "PASS"
    if receipt.get("project_preflight") != expected_state or expected not in receipt.get("request_domain", []):
        fail(f"preflight CLI did not route {sample} to {expected}")
    if expected == "creative_publication" and receipt.get("creative_execution_authorized") is not False:
        fail("creative request without exact production evidence must not authorize creative tools")
    if expected != "creative_publication" and receipt.get("creative_execution_authorized") is not False:
        fail("non-creative request must not accidentally authorize creative tools")

print(f"OK project-request-gate domains={len(manifest['domains'])} authority_paths={len(set(all_paths))} creative_without_evidence=BLOCKED creative_tool_authorization=fail_closed")
